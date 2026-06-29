"""Outer training loop: rollouts -> score -> reflect -> gate -> checkpoint.

Steps and epochs are sequential (each step needs the gated skill); rollouts, val
evals, and minibatch proposals fan out through the Phase-3 scheduler. The loop owns
datasets, the LR (edit-budget) schedule, the gate, checkpoints, and best_skill.md;
it makes ZERO LLM calls itself (spine §1, §3) — every call is dispatched to a
provider pool via injected `rollout_fn` / `propose_fn` callables.
"""
from __future__ import annotations

import math
import os
import random
from dataclasses import dataclass
from typing import Awaitable, Callable

from . import gate as gatemod
from . import reflect as reflectmod
from .checkpoint import TrainState, resume, write_checkpoint
from .gate import (Scheduler, evaluate_val, calibrate_sigma_gate, fanout,
                   gate_accept, mean_metric, rebaseline)


# --------------------------------------------------------------------------- #
# LR (edit-budget) schedule — mirrors upstream's decay shape for the clamp.
# If upstream exposes its schedule, the loop should defer to it; this local
# implementation keeps the budget deterministic and dependency-free for tests.
# --------------------------------------------------------------------------- #
def lr_at(step: int, total_steps: int, *, lr0: int = 4, min_lr: int = 2,
          kind: str = "cosine") -> int:
    """Edit budget for a step, an int in [min_lr, lr0] decaying over the epoch."""
    if total_steps <= 1 or step <= 0:
        f = 1.0
    elif step >= total_steps - 1:
        f = 0.0
    else:
        t = step / (total_steps - 1)
        if kind == "constant":
            f = 1.0
        elif kind == "linear":
            f = 1.0 - t
        else:  # cosine
            f = 0.5 * (1.0 + math.cos(math.pi * t))
    return int(round(min_lr + (lr0 - min_lr) * f))


# --------------------------------------------------------------------------- #
# Config + dependency wiring (maps onto the Phase-1 config schema)
# --------------------------------------------------------------------------- #
@dataclass
class LoopConfig:
    batch_size: int = 40
    minibatch_size: int = 8
    n_samples: int = 3            # rollout self-consistency on train
    val_n_samples: int = 3        # rollout self-consistency on val
    steps_per_epoch: int = 5
    lr0: int = 4
    min_lr: int = 2
    lr_kind: str = "cosine"
    gate_mode: str = "variance"          # {variance, strict, paired}
    reflection_mode: str = "parallel"    # {parallel, sequential}
    metric: str = "mixed"                # {hard, soft, mixed}
    rollout_provider: str = "claude"
    reflect_provider: str = "codex"
    model: str = "claude"
    seed: int = 0
    out_dir: str = "."
    checkpoint_path: str = "checkpoint.json"


@dataclass
class LoopDeps:
    scheduler: Scheduler
    rollout_fn: Callable[[str, dict], Awaitable[dict]]  # (skill_doc, task) -> rollout dict
    scorer: Callable[[dict, dict], dict]                # (task, rollout) -> {id, hard, soft}
    propose_fn: Callable[[str, list[dict]], Awaitable[str]]  # (skill, minibatch) -> raw patch
    train_tasks: list[dict]
    val_tasks: list[dict]
    repair_fn: Callable[[str, str], Awaitable[str]] | None = None


# --------------------------------------------------------------------------- #
# Batch sampling (deterministic per-epoch permutation; val never resampled)
# --------------------------------------------------------------------------- #
def _sample_batch(state: TrainState, cfg: LoopConfig, train_tasks: list[dict]) -> list[dict]:
    n = len(train_tasks)
    if n == 0:
        return []
    perm = list(range(n))
    random.Random(cfg.seed ^ (state.epoch + 1)).shuffle(perm)
    count = min(cfg.batch_size, n)
    idxs = [perm[(state.data_cursor + k) % n] for k in range(count)]
    return [train_tasks[i] for i in idxs]


async def _run_batch_rollouts(skill_doc: str, batch: list[dict],
                              deps: LoopDeps, cfg: LoopConfig) -> list[dict]:
    """Fan out batch rollouts (n_samples each) and score them to self-consistent recs."""
    factories: list[Callable[[], Awaitable]] = []
    spans: list[tuple[dict, int, int]] = []
    for task in batch:
        start = len(factories)
        for _ in range(cfg.n_samples):
            factories.append(lambda s=skill_doc, t=task: deps.rollout_fn(s, t))
        spans.append((task, start, start + cfg.n_samples))
    rollouts = await fanout(deps.scheduler, cfg.rollout_provider, factories)
    scored: list[dict] = []
    for task, start, end in spans:
        samples = [deps.scorer(task, rollouts[j]) for j in range(start, end)]
        rec = gatemod.aggregate_samples(task["id"], samples)
        # Carry a representative transcript + the task for the reflector's minibatch.
        scored.append(dict(rec, stdout=rollouts[start].get("stdout", ""), task=task))
    return scored


def _emit_best_skill(cfg: LoopConfig, doc: str) -> None:
    """Atomically write best_skill.md on improvement."""
    os.makedirs(cfg.out_dir, exist_ok=True)
    path = os.path.join(cfg.out_dir, "best_skill.md")
    tmp = f"{path}.tmp.{os.getpid()}"
    with open(tmp, "w", encoding="utf-8") as fh:
        fh.write(doc)
    os.replace(tmp, path)


# --------------------------------------------------------------------------- #
# One step: sample -> rollout -> score -> reflect -> gate -> checkpoint
# --------------------------------------------------------------------------- #
async def step(state: TrainState, cfg: LoopConfig, deps: LoopDeps,
               total_steps: int) -> dict:
    lr = lr_at(state.step_in_epoch, total_steps, lr0=cfg.lr0, min_lr=cfg.min_lr,
               kind=cfg.lr_kind)

    batch = _sample_batch(state, cfg, deps.train_tasks)
    scored = await _run_batch_rollouts(state.skill_doc, batch, deps, cfg)

    reflect_res = await reflectmod.run_reflection(
        skill_doc=state.skill_doc, scored_rollouts=scored, lr=lr,
        scheduler=deps.scheduler, provider=cfg.reflect_provider,
        minibatch_size=cfg.minibatch_size, propose_fn=deps.propose_fn,
        repair_fn=deps.repair_fn, reflection_mode=cfg.reflection_mode)
    candidate = reflect_res.candidate_doc

    # Gate critical section (sequential barrier): re-baseline prior under current
    # model, eval candidate on the frozen val split, decide beyond the noise floor.
    val_old = await rebaseline(
        prior_skill_doc=state.skill_doc, val_tasks=deps.val_tasks,
        n_samples=cfg.val_n_samples, scheduler=deps.scheduler,
        provider=cfg.rollout_provider, rollout_fn=deps.rollout_fn,
        scorer=deps.scorer, cache=state.cache, model=cfg.model)
    val_new = await evaluate_val(
        skill_doc=candidate, val_tasks=deps.val_tasks, n_samples=cfg.val_n_samples,
        scheduler=deps.scheduler, provider=cfg.rollout_provider,
        rollout_fn=deps.rollout_fn, scorer=deps.scorer, cache=state.cache, model=cfg.model)

    accepted = gate_accept(val_old, val_new, metric=cfg.metric,
                           sigma_gate=state.sigma_gate,
                           M=max(1, len(deps.val_tasks)), mode=cfg.gate_mode)

    score_new = mean_metric(val_new, cfg.metric)
    if accepted:
        state.skill_doc = candidate
        if score_new > state.best_score:
            state.best_score = score_new
            state.best_skill_doc = candidate
            _emit_best_skill(cfg, candidate)

    # Advance cursors + persist RNG, then write-ahead checkpoint.
    state.step += 1
    state.step_in_epoch += 1
    state.data_cursor += len(batch)
    write_checkpoint(os.path.join(cfg.out_dir, cfg.checkpoint_path), state)

    return {"step": state.step, "lr": lr, "accepted": accepted,
            "applied_ops": len(reflect_res.applied_ops),
            "score_old": mean_metric(val_old, cfg.metric), "score_new": score_new}


# --------------------------------------------------------------------------- #
# One epoch: A/A-calibrate sigma_gate, then steps_per_epoch gated steps
# --------------------------------------------------------------------------- #
async def run_epoch(state: TrainState, cfg: LoopConfig, deps: LoopDeps) -> TrainState:
    total_steps = cfg.steps_per_epoch
    state.sigma_gate = await calibrate_sigma_gate(
        skill_doc=state.skill_doc, val_tasks=deps.val_tasks, n_samples=cfg.val_n_samples,
        scheduler=deps.scheduler, provider=cfg.rollout_provider, rollout_fn=deps.rollout_fn,
        scorer=deps.scorer, metric=cfg.metric, model=cfg.model)
    if state.best_skill_doc == "":
        state.best_skill_doc = state.skill_doc
    while state.step_in_epoch < total_steps:
        await step(state, cfg, deps, total_steps)
    state.epoch += 1
    state.step_in_epoch = 0
    state.data_cursor = 0
    write_checkpoint(os.path.join(cfg.out_dir, cfg.checkpoint_path), state)
    return state


async def train(cfg: LoopConfig, deps: LoopDeps, *, initial_skill: str,
                epochs: int = 1) -> TrainState:
    """Resume if a checkpoint exists, else start fresh; run until epoch == `epochs`.

    A completed run resumes to a no-op; a run interrupted mid-epoch resumes from
    the last committed step and finishes the epoch — deterministically reproducing
    the uninterrupted result.
    """
    ckpt_path = os.path.join(cfg.out_dir, cfg.checkpoint_path)
    state = resume(ckpt_path)
    if state is None:
        state = TrainState(skill_doc=initial_skill, best_skill_doc=initial_skill)
        state.set_rng(random.Random(cfg.seed))
    while state.epoch < epochs:
        await run_epoch(state, cfg, deps)
    return state
