"""Full one-epoch smoke (produces best_skill.md) and checkpoint-resume reproducibility."""
from __future__ import annotations

import asyncio
import json
import os
import random

from skillopt_oauth.checkpoint import TrainState
from skillopt_oauth.gate import calibrate_sigma_gate
from skillopt_oauth.loop import LoopConfig, LoopDeps, run_epoch, step, train
from conftest import FakeScheduler

INIT = "# skill\nbody line"
MARKER = "MARKER: improved"


def _make_deps(scheduler):
    """Fakes honoring the Phase-2 stub contract: a rollout 'succeeds' only once the
    skill contains MARKER; the proposer adds MARKER exactly once, then proposes nothing."""
    async def rollout_fn(skill_doc, task):
        return {"id": task["id"], "stdout": "GOOD" if MARKER in skill_doc else "BAD"}

    def scorer(task, rollout):
        ok = 1 if "GOOD" in rollout.get("stdout", "") else 0
        return {"id": task["id"], "hard": ok, "soft": float(ok)}

    async def propose_fn(skill_doc, minibatch):
        edits = [] if MARKER in skill_doc else [{"kind": "add", "anchor": "", "text": MARKER}]
        return json.dumps({"edits": edits})

    train_tasks = [{"id": f"tr{i}"} for i in range(4)]
    val_tasks = [{"id": f"va{i}"} for i in range(4)]
    return LoopDeps(scheduler=scheduler, rollout_fn=rollout_fn, scorer=scorer,
                    propose_fn=propose_fn, train_tasks=train_tasks, val_tasks=val_tasks)


def _cfg(out_dir):
    return LoopConfig(batch_size=2, minibatch_size=2, n_samples=3, val_n_samples=3,
                      steps_per_epoch=3, gate_mode="variance", reflection_mode="parallel",
                      rollout_provider="claude", reflect_provider="codex", seed=0,
                      out_dir=str(out_dir))


def test_one_epoch_smoke_produces_best_skill(tmp_path):
    cfg = _cfg(tmp_path)
    deps = _make_deps(FakeScheduler())
    state = asyncio.run(train(cfg, deps, initial_skill=INIT, epochs=1))

    best_path = tmp_path / "best_skill.md"
    assert best_path.exists()
    assert MARKER in best_path.read_text()           # the accepted improvement landed
    assert state.epoch == 1
    assert state.step == cfg.steps_per_epoch
    assert state.best_score == 1.0                   # val went 0 -> 1 and was accepted
    assert (tmp_path / cfg.checkpoint_path).exists()


def test_resume_reproduces_uninterrupted_run(tmp_path):
    # 1) Clean uninterrupted run.
    dir_a = tmp_path / "a"
    clean = asyncio.run(train(_cfg(dir_a), _make_deps(FakeScheduler()),
                              initial_skill=INIT, epochs=1))

    # 2) Interrupted run: drive one step, "crash", then resume to completion.
    dir_b = tmp_path / "b"
    cfg_b = _cfg(dir_b)
    deps_b = _make_deps(FakeScheduler())

    async def partial():
        st = TrainState(skill_doc=INIT, best_skill_doc=INIT)
        st.set_rng(random.Random(cfg_b.seed))
        st.sigma_gate = await calibrate_sigma_gate(
            skill_doc=st.skill_doc, val_tasks=deps_b.val_tasks, n_samples=cfg_b.val_n_samples,
            scheduler=deps_b.scheduler, provider=cfg_b.rollout_provider,
            rollout_fn=deps_b.rollout_fn, scorer=deps_b.scorer, metric=cfg_b.metric)
        await step(st, cfg_b, deps_b, cfg_b.steps_per_epoch)   # one committed step, then crash

    asyncio.run(partial())
    assert (dir_b / cfg_b.checkpoint_path).exists()            # WAL committed mid-epoch

    resumed = asyncio.run(train(cfg_b, deps_b, initial_skill=INIT, epochs=1))

    # 3) Resumed final state matches the uninterrupted run exactly.
    assert resumed.epoch == clean.epoch == 1
    assert resumed.step == clean.step
    assert resumed.skill_doc == clean.skill_doc
    assert resumed.best_score == clean.best_score
    assert resumed.best_skill_doc == clean.best_skill_doc
    assert (dir_b / "best_skill.md").read_text() == (dir_a / "best_skill.md").read_text()
