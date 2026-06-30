"""Training entrypoint for SkillOpt-OAuth.

This module is the wiring spine: it reconciles the three config namespaces the fork
accumulated across phases, builds the Phase-2 executor + Phase-3 scheduler, derives
the rollout/reflect callables (routed through ``cli_job`` for uniform resilience),
and drives the Phase-5 loop (``loop.train``) to completion.

CONFIG RECONCILIATION (README known-risk #1 + the P4 note)
---------------------------------------------------------
Three name spaces describe the same run and must be unified here:

  * P1 ``Config`` (config.py, FLAT)        — lr, lr_schedule, n_samples, *_pool, ...
  * P4 env YAML  (configs/<env>/...,NESTED) — rollout.n_samples, train.split_seed,
                                              loader.val_fraction, providers.{rollout,
                                              reflect}, gate.mode, rollout.timeout, ...
  * P5 ``LoopConfig`` (loop.py)            — lr0, lr_kind, val_n_samples, steps_per_epoch,
                                              metric, seed, out_dir, checkpoint_path, model

The single canonical internal shape is P5 ``LoopConfig`` (what the loop consumes) plus
an ``EnvConfig`` carrying the env-specific knobs (paths, providers, timeouts) the loop
does not. ``reconcile_loop_config`` performs the mapping; the precedence is

    explicit override  >  P4 env YAML  >  P1 Config default

so a value present in the env YAML wins over the flat P1 default, and a CLI/keyword
override wins over both. The full field-by-field mapping:

  P5 LoopConfig field   <- source (P4 YAML path  | P1 Config field)         | default
  --------------------    ----------------------------------------------------------
  batch_size            <- train.batch_size      | batch_size                | 40
  minibatch_size        <- (n/a)                 | minibatch_size            | 8
  n_samples             <- rollout.n_samples     | n_samples                 | 3
  val_n_samples         <- rollout.n_samples     | n_samples                 | 3
  steps_per_epoch       <- (n/a)                 | (n/a)                     | 5  (override)
  lr0                   <- (n/a)                 | lr                        | 4
  min_lr                <- (n/a)                 | min_lr                    | 2
  lr_kind               <- (n/a)                 | lr_schedule               | cosine
  gate_mode             <- gate.mode             | gate_mode                 | variance
  reflection_mode       <- (n/a)                 | reflection_mode           | parallel
  metric                <- (n/a)                 | (n/a)                     | mixed
  rollout_provider      <- providers.rollout     | rollout_provider          | claude
  reflect_provider      <- providers.reflect     | reflect_provider          | codex
  model                 <- (n/a)                 | model_claude (or 'claude')| claude
  seed                  <- train.split_seed      | (n/a)                     | 0
  out_dir               <- (n/a)                 | (n/a)                     | .  (override)
  checkpoint_path       <- (n/a)                 | (n/a)                     | checkpoint.json

Env-only knobs that do NOT land in LoopConfig (they wire the executor/scheduler/loader):
  rollout.timeout -> per-call CLI timeout; loader.val_fraction + train.split_seed ->
  dataloader split; providers.* -> scheduler pools; reasoning_effort -> executor.
"""
from __future__ import annotations

import argparse
import asyncio
import importlib
import shutil
import sys
import tempfile
from dataclasses import asdict, dataclass, field, replace
from pathlib import Path
from typing import Any, Awaitable, Callable

import yaml

from .checkpoint import TrainState
from .config import Config, load_config
from .envs import _io
from .loop import LoopConfig, LoopDeps, train as run_loop
from .registry import get_env, list_envs  # registration triggered by package __init__
from .scheduler import ProviderPool, Scheduler, cli_job


# --------------------------------------------------------------------------- #
# P4 env YAML -> a typed, flat-enough EnvConfig (the nested keys, parsed once)
# --------------------------------------------------------------------------- #
@dataclass
class EnvConfig:
    """The subset of a P4 env YAML the wiring needs, with the nested keys resolved."""
    env: str
    initial_skill: str                 # path, relative to project root
    tasks_dir: str
    rollout_provider: str = "claude"   # providers.rollout
    reflect_provider: str = "codex"    # providers.reflect
    reasoning_effort: str = "high"     # codex model_reasoning_effort (minimal|low|medium|high)
    n_samples: int = 3                 # rollout.n_samples
    rollout_timeout: float = 600.0     # rollout.timeout
    batch_size: int = 40               # train.batch_size
    split_seed: int = 0                # train.split_seed
    val_fraction: float = 0.34         # loader.val_fraction
    gate_mode: str = "variance"        # gate.mode
    raw: dict = field(default_factory=dict)


def load_env_config(env_name: str, *, configs_dir: str | Path | None = None) -> EnvConfig:
    """Load and flatten ``configs/<env>/default.yaml`` (or the registry default_config)."""
    root = _io.project_root()
    if configs_dir is not None:
        path = Path(configs_dir) / env_name / "default.yaml"
    else:
        spec = get_env(env_name)
        rel = spec.default_config or f"configs/{env_name}/default.yaml"
        path = root / rel
    with Path(path).open("r", encoding="utf-8") as fh:
        data = yaml.safe_load(fh) or {}
    if not isinstance(data, dict):
        raise ValueError(f"env config root must be a mapping: {path}")

    providers = data.get("providers") or {}
    rollout = data.get("rollout") or {}
    trn = data.get("train") or {}
    loader = data.get("loader") or {}
    gate = data.get("gate") or {}
    return EnvConfig(
        env=str(data.get("env", env_name)),
        initial_skill=str(data.get("initial_skill", f"skills/{env_name}/initial.md")),
        tasks_dir=str(data.get("tasks_dir", f"tasks/{env_name}")),
        rollout_provider=str(providers.get("rollout", "claude")),
        reflect_provider=str(providers.get("reflect", "codex")),
        reasoning_effort=str(data.get("reasoning_effort", "high")),
        n_samples=int(rollout.get("n_samples", 3)),
        rollout_timeout=float(rollout.get("timeout", 600.0)),
        batch_size=int(trn.get("batch_size", 40)),
        split_seed=int(trn.get("split_seed", 0)),
        val_fraction=float(loader.get("val_fraction", 0.34)),
        gate_mode=str(gate.get("mode", "variance")),
        raw=data,
    )


# --------------------------------------------------------------------------- #
# The reconciliation: (P1 Config, P4 EnvConfig, overrides) -> P5 LoopConfig
# --------------------------------------------------------------------------- #
def reconcile_loop_config(base: Config, env: EnvConfig, *, out_dir: str,
                          steps_per_epoch: int = 5, checkpoint_path: str = "checkpoint.json",
                          seed: int | None = None, batch_size: int | None = None,
                          n_samples: int | None = None, val_n_samples: int | None = None,
                          rollout_provider: str | None = None,
                          reflect_provider: str | None = None) -> LoopConfig:
    """Fold the flat P1 ``Config`` and the nested P4 ``EnvConfig`` into one ``LoopConfig``.

    Precedence: explicit override > P4 env YAML > P1 Config default. See the module
    docstring for the full field-by-field mapping table. The keyword overrides
    (batch_size / n_samples / val_n_samples / rollout_provider / reflect_provider)
    sit at the top of that precedence so a CLI flag can shrink a run or re-route a
    provider without editing the committed env YAML.
    """
    n_eff = n_samples if n_samples is not None else env.n_samples
    return LoopConfig(
        batch_size=batch_size if batch_size is not None else env.batch_size,
        minibatch_size=base.minibatch_size,
        n_samples=n_eff,
        val_n_samples=val_n_samples if val_n_samples is not None else n_eff,
        steps_per_epoch=steps_per_epoch,
        lr0=base.lr,
        min_lr=base.min_lr,
        lr_kind=base.lr_schedule,
        gate_mode=env.gate_mode or base.gate_mode,
        reflection_mode=base.reflection_mode,
        metric="mixed",
        rollout_provider=rollout_provider or env.rollout_provider or base.rollout_provider,
        reflect_provider=reflect_provider or env.reflect_provider or base.reflect_provider,
        model=base.model_claude or "claude",
        seed=int(seed if seed is not None else env.split_seed),
        out_dir=out_dir,
        checkpoint_path=checkpoint_path,
    )


# --------------------------------------------------------------------------- #
# Phase-2 executor + Phase-3 scheduler builders
# --------------------------------------------------------------------------- #
def build_executor(base: Config, env: EnvConfig, *, stub_bin: str | None = None,
                   fake_oauth: bool = False):
    """Construct the single OAuth-CLI chokepoint (Phase 2).

    ``stub_bin`` (hermetic smoke) points BOTH provider binaries at the stub CLI;
    ``fake_oauth`` injects a probe that always resolves to ``'oauth'`` so the
    fail-closed preflight passes offline (this machine has no OAuth creds).
    """
    from .executor import OAuthCLIExecutor

    claude_bin = stub_bin if stub_bin is not None else "claude"
    codex_bin = stub_bin if stub_bin is not None else "codex"
    probe: Callable[[str], str] | None = (lambda provider: "oauth") if fake_oauth else None
    return OAuthCLIExecutor(
        claude_bin=claude_bin, codex_bin=codex_bin,
        model_claude=base.model_claude, model_codex=base.model_codex,
        reasoning_effort=env.reasoning_effort or base.reasoning_effort,
        forbid_api_keys=base.forbid_api_keys, oauth_probe=probe,
    )


def build_scheduler(base: Config, providers: list[str]) -> Scheduler:
    """One bounded Phase-3 ``ProviderPool`` per distinct provider (one OAuth identity)."""
    pools: dict[str, ProviderPool] = {}
    for name in dict.fromkeys(providers):  # dedup, preserve order
        size = base.codex_pool if name == "codex" else base.claude_pool
        pools[name] = ProviderPool(
            name, size, base.rate_per_min, base.max_retries,
            per_call_timeout=base.per_call_timeout,
            circuit_breaker_threshold=base.circuit_breaker_threshold,
            circuit_reset_timeout=base.circuit_reset_timeout,
        )
    return Scheduler(pools)


# --------------------------------------------------------------------------- #
# rollout_fn / propose_fn — the only callables the loop dispatches; both route
# their CLI call through cli_job so classify_cli_result + the pool's backoff /
# retry / circuit-breaker engage uniformly (README known-risk #2, P5 note #5).
# --------------------------------------------------------------------------- #
def _rollout_prompt(skill_doc: str, task: dict) -> str:
    """The instruction sent to the rollout CLI.

    The candidate skill is INLINED (real ``claude`` does not auto-load a workspace
    ``.agents/skills/`` dir, so the doc must reach the model in the prompt), and the
    model is told to create the task's artifacts at the TOP LEVEL of its working
    directory so the deterministic scorer can grade their names.
    """
    return (
        "You are an automated file-creation agent. Apply the following skill "
        "exactly when naming anything you create.\n"
        "=== SKILL ===\n"
        f"{skill_doc.strip()}\n"
        "=== END SKILL ===\n\n"
        f"Task: {task.get('prompt', '')}\n\n"
        "Create the requested file(s) and/or folder(s) directly at the TOP LEVEL "
        "of your current working directory. Do not nest them inside a new "
        "subfolder, and do not create any extra files. Apply the skill's naming "
        "rules to every name you create. Do not ask questions; just create them "
        "and stop."
    )


def _reflect_prompt(skill_doc: str, minibatch: list[dict]) -> str:
    """The instruction sent to the reflect CLI: improve the skill, return edit ops.

    States the reward signal explicitly (the deterministic scorer's prefix rule)
    and pins the exact ``{kind, anchor, text}`` edit-op JSON the reflect parser
    (``reflect.parse_edit_ops``) consumes. The edit engine (``reflect.apply_edits``)
    is LINE-BASED -- an op's ``anchor`` is matched only within a single existing
    line -- so we tell the model that and steer it to an anchor-free ``add``
    (append), which always applies regardless of how the skill is wrapped.
    """
    examples = "\n".join(
        f"  - {m.get('prompt') or m.get('id') or ''}" for m in minibatch
    ) or "  (none)"
    return (
        "You are improving the SKILL document an automated agent reads before it "
        "creates files for a task. The agent's output is scored programmatically: "
        "a task scores 1.0 only if EVERY top-level file or folder it creates has a "
        "name beginning with a YYMMDD-HHMMSS- timestamp prefix (six digits, dash, "
        "six digits, dash), e.g. 260630-142210-summary.md; otherwise it scores 0. "
        "The current skill does NOT achieve this.\n\n"
        "Current SKILL:\n=== SKILL ===\n"
        f"{skill_doc.strip()}\n=== END SKILL ===\n\n"
        "Recent tasks the agent attempted:\n"
        f"{examples}\n\n"
        "Propose edits so the agent RELIABLY prefixes every new file AND folder "
        "name with that exact YYMMDD-HHMMSS- timestamp.\n\n"
        "Edits are applied by a LINE-BASED engine: each edit's \"anchor\" must be a "
        "substring of a SINGLE existing line (it can NOT span multiple lines). "
        "STRONGLY PREFER one \"add\" edit with an empty anchor -- it appends your "
        "\"text\" as a new final line -- and make that text an assertive, "
        "self-contained rule that OVERRIDES any earlier naming guidance (state the "
        "exact YYMMDD-HHMMSS- format and that it applies to every file and folder). "
        "Respond with ONLY a JSON object (no prose, no code fence) of the form:\n"
        '{"edits": [{"kind": "add", "anchor": "", "text": "<rule to append>"}]}\n'
        'where "kind" is "add" (append "text" as a new line; anchor ""), "replace" '
        '(replace the first line containing the single-line "anchor" with "text"), '
        'or "delete" (remove the first line containing the single-line "anchor"). '
        "Output the JSON object and nothing else."
    )


def _extract_edits_json(raw: str) -> str:
    """Recover the edit-op JSON object from a CLI's (possibly prose/fenced) stdout.

    Returns the bare ``{...}`` substring when found, else the raw text -- the
    downstream parser then yields zero edits (a no-op step) rather than crashing.
    """
    from .executor import PatchParseError, extract_json_object
    try:
        return extract_json_object(raw)
    except (PatchParseError, ValueError):
        return raw


def make_rollout_fn(executor, env: EnvConfig, cfg: LoopConfig):
    """Build ``rollout_fn(skill_doc, task) -> {id, stdout, workspace_dir}``.

    The loop fans this out through the scheduler pool; inside, the candidate skill
    is materialized to a file, injected into a fresh per-rollout workspace, and the
    CLI call goes through ``cli_job`` (so a rate-limit / timeout / auth-billing
    signal is classified and the wrapping pool retries or fails closed).
    ``allow_writes=True`` widens the rollout CLI's sandbox so the model can create
    the task's files in the workspace the scorer then scans.
    """
    async def rollout_fn(skill_doc: str, task: dict) -> dict:
        base_dir = tempfile.mkdtemp(prefix="skillopt_roll_")
        skill_dir = Path(base_dir) / env.env
        skill_dir.mkdir(parents=True, exist_ok=True)
        skill_file = skill_dir / "SKILL.md"
        skill_file.write_text(skill_doc, encoding="utf-8")
        ws = Path(base_dir) / "ws"
        ws.mkdir(parents=True, exist_ok=True)
        prompt = _rollout_prompt(skill_doc, task)
        factory = cli_job(executor, provider=cfg.rollout_provider, prompt=prompt,
                          skill_path=str(skill_file), workdir=str(ws),
                          timeout=env.rollout_timeout, allow_writes=True)
        res = await factory()
        return {"id": task["id"], "stdout": getattr(res, "stdout", ""),
                "workspace_dir": str(ws)}

    return rollout_fn


def make_propose_fn(executor, env: EnvConfig, cfg: LoopConfig):
    """Build ``propose_fn(skill_doc, minibatch) -> edit-op JSON``, routed via cli_job.

    The proposer is the OAuth CLI on the reflect identity. It runs in an isolated,
    empty workspace under the read-only sandbox so it never scans the surrounding
    repo, and its stdout is reduced to the bare edit-op JSON object for the reflect
    parser (real CLI output may wrap the JSON in prose or a code fence).
    """
    async def propose_fn(skill_doc: str, minibatch: list[dict]) -> str:
        prompt = _reflect_prompt(skill_doc, minibatch)
        reflect_ws = tempfile.mkdtemp(prefix="skillopt_reflect_")
        try:
            factory = cli_job(executor, provider=cfg.reflect_provider, prompt=prompt,
                              workdir=reflect_ws, timeout=env.rollout_timeout)
            res = await factory()
        finally:
            shutil.rmtree(reflect_ws, ignore_errors=True)
        return _extract_edits_json(getattr(res, "stdout", ""))

    return propose_fn


# --------------------------------------------------------------------------- #
# End-to-end drive
# --------------------------------------------------------------------------- #
async def run_training(base: Config, env: EnvConfig, *, out_dir: str, epochs: int = 1,
                       steps_per_epoch: int = 5, checkpoint_path: str = "checkpoint.json",
                       stub_bin: str | None = None, fake_oauth: bool = False,
                       batch_size: int | None = None, n_samples: int | None = None,
                       val_n_samples: int | None = None, initial_skill: str | None = None,
                       rollout_provider: str | None = None,
                       reflect_provider: str | None = None,
                       reasoning_effort: str | None = None) -> TrainState:
    """Reconcile config, build the executor/scheduler/deps, and run the loop.

    The optional keyword overrides (also exposed as CLI flags) take precedence over
    the env YAML so a run can be shrunk, re-routed to other providers, or pointed
    at a different initial skill without editing committed config.
    """
    if reasoning_effort is not None:
        env = replace(env, reasoning_effort=reasoning_effort)
    cfg = reconcile_loop_config(
        base, env, out_dir=out_dir, steps_per_epoch=steps_per_epoch,
        checkpoint_path=checkpoint_path, batch_size=batch_size, n_samples=n_samples,
        val_n_samples=val_n_samples, rollout_provider=rollout_provider,
        reflect_provider=reflect_provider,
    )

    executor = build_executor(base, env, stub_bin=stub_bin, fake_oauth=fake_oauth)
    scheduler = build_scheduler(base, [cfg.rollout_provider, cfg.reflect_provider])

    spec = get_env(env.env)
    loader = spec.loader_cls(val_fraction=env.val_fraction, split_seed=env.split_seed)
    scorer = importlib.import_module(f"skillopt_oauth.envs.{env.env}.scorer").score

    deps = LoopDeps(
        scheduler=scheduler,
        rollout_fn=make_rollout_fn(executor, env, cfg),
        scorer=scorer,
        propose_fn=make_propose_fn(executor, env, cfg),
        train_tasks=loader.train_split(),
        val_tasks=loader.val_split(),
    )

    if initial_skill:
        initial_path = Path(initial_skill)
        if not initial_path.is_absolute():
            initial_path = _io.project_root() / initial_path
    else:
        initial_path = _io.project_root() / env.initial_skill
    initial_skill_text = Path(initial_path).read_text(encoding="utf-8")
    try:
        return await run_loop(cfg, deps, initial_skill=initial_skill_text, epochs=epochs)
    finally:
        await scheduler.aclose()


# --------------------------------------------------------------------------- #
# CLI
# --------------------------------------------------------------------------- #
def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="skillopt-oauth",
        description="OAuth-CLI fork of Microsoft SkillOpt.",
    )
    parser.add_argument("--config", default=None,
                        help="path to a flat P1 YAML config; defaults used when omitted")
    parser.add_argument("--dry-run", action="store_true",
                        help="list registered environments and the loaded config, then exit")
    parser.add_argument("--env", default=None, choices=list_envs() or None,
                        help="environment to train (loads its P4 configs/<env>/default.yaml)")
    parser.add_argument("--epochs", type=int, default=1, help="number of epochs to run")
    parser.add_argument("--steps-per-epoch", type=int, default=5,
                        help="gated steps per epoch")
    parser.add_argument("--out-dir", default=".",
                        help="run directory for the checkpoint WAL + best_skill.md")
    parser.add_argument("--checkpoint", default="checkpoint.json",
                        help="checkpoint filename inside --out-dir")
    # Run-shaping overrides (precedence over the env YAML); omit to use the YAML.
    parser.add_argument("--batch-size", type=int, default=None,
                        help="override train.batch_size (rollout tasks per step)")
    parser.add_argument("--n-samples", type=int, default=None,
                        help="override rollout.n_samples (samples per task; rollout + val)")
    parser.add_argument("--val-n-samples", type=int, default=None,
                        help="override validation samples per task (defaults to --n-samples)")
    parser.add_argument("--initial-skill", default=None,
                        help="override the initial skill doc path (absolute or repo-relative)")
    parser.add_argument("--rollout-provider", default=None,
                        help="override providers.rollout (e.g. claude)")
    parser.add_argument("--reflect-provider", default=None,
                        help="override providers.reflect (e.g. codex)")
    parser.add_argument("--reasoning-effort", default=None,
                        help="override codex model_reasoning_effort (minimal|low|medium|high)")
    # Hermetic smoke knobs (offline): point both CLIs at the stub + fake the OAuth probe.
    parser.add_argument("--stub", default=None,
                        help="hermetic: use this stub CLI as both claude_bin and codex_bin")
    parser.add_argument("--fake-oauth", action="store_true",
                        help="hermetic: inject an OAuth probe that always resolves to 'oauth'")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    config = load_config(args.config) if args.config else Config()

    if args.dry_run:
        envs = list_envs()
        print("SkillOpt-OAuth dry run")
        print(f"registered environments ({len(envs)}): {envs}")
        print("config:")
        for key, value in asdict(config).items():
            print(f"  {key} = {value!r}")
        return 0

    if not args.env:
        parser.error("training requires --env (or use --dry-run); known: " + str(list_envs()))
        return 2  # unreachable: parser.error() exits with status 2

    env = load_env_config(args.env)
    state = asyncio.run(run_training(
        config, env, out_dir=args.out_dir, epochs=args.epochs,
        steps_per_epoch=args.steps_per_epoch, checkpoint_path=args.checkpoint,
        stub_bin=args.stub, fake_oauth=args.fake_oauth,
        batch_size=args.batch_size, n_samples=args.n_samples,
        val_n_samples=args.val_n_samples, initial_skill=args.initial_skill,
        rollout_provider=args.rollout_provider, reflect_provider=args.reflect_provider,
        reasoning_effort=args.reasoning_effort,
    ))
    print(f"done: env={env.env} epoch={state.epoch} step={state.step} "
          f"best_score={state.best_score}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
