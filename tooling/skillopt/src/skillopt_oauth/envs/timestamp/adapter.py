"""EnvAdapter for the `timestamp` env.

Implements the abstract surface (build_train_env / build_eval_env / rollout /
get_task_types). There is no evaluate(); scoring lives in run_batch, which calls
the deterministic scorer. rollout dispatches each task through the Phase-3
Scheduler onto the Phase-2 oauth_cli executor; tests bypass it with canned rollouts.
"""
from __future__ import annotations

import asyncio
import tempfile
from pathlib import Path

from skillopt_oauth.base import EnvAdapter
from skillopt_oauth.envs.timestamp.dataloader import TimestampDataLoader
from skillopt_oauth.envs.timestamp.scorer import score as score_timestamp
from skillopt_oauth.scheduler import cli_job


class TimestampAdapter(EnvAdapter):
    env_name = "timestamp"

    def __init__(self, loader: TimestampDataLoader | None = None, *,
                 provider: str = "claude", skill_path: str | None = None):
        super().__init__()  # base plumbing only (Phase 1); no required args
        self.loader = loader or TimestampDataLoader()
        self.provider = provider
        self.skill_path = skill_path

    # --- abstract surface ---------------------------------------------------
    def build_train_env(self) -> dict:
        return {"env": self.env_name, "split": "train", "tasks": self.loader.train_split()}

    def build_eval_env(self) -> dict:
        return {"env": self.env_name, "split": "val", "tasks": self.loader.val_split()}

    def get_task_types(self) -> list[str]:
        tasks = self.loader.train_split() + self.loader.val_split()
        return sorted({t.get("type", "default") for t in tasks})

    async def rollout(self, tasks: list[dict], *, scheduler, executor,
                      provider: str | None = None, skill_path: str | None = None,
                      workdir_root: str | None = None, timeout: float = 600.0) -> list[dict]:
        """Run rollouts in parallel under the provider pool; one workspace per task.

        Each task is routed through :func:`skillopt_oauth.scheduler.cli_job`, so the
        raw ``CliResult`` passes through ``classify_cli_result`` and the pool's full
        backoff / retry / circuit-breaker stack engages on rate-limit, timeout, and
        auth/billing signals (README known-risk #2). ``cli_job`` is the drop-in for
        ``submit(lambda: asyncio.to_thread(run_cli(...)))``.
        """
        provider = provider or self.provider
        skill_path = skill_path or self.skill_path
        root = Path(workdir_root) if workdir_root else Path(tempfile.mkdtemp(prefix="ts_roll_"))

        async def _one(task: dict) -> dict:
            ws = root / str(task["id"])
            ws.mkdir(parents=True, exist_ok=True)
            prompt = self._build_prompt(task)
            factory = cli_job(executor, provider=provider, prompt=prompt,
                              skill_path=skill_path, workdir=str(ws), timeout=timeout)
            res = await scheduler.submit(provider, factory)
            return {"id": task["id"], "stdout": getattr(res, "stdout", ""),
                    "workspace_dir": str(ws)}

        # Direct await on gather (no create_task wrapper) per Python 3.13.
        return list(await asyncio.gather(*[_one(t) for t in tasks]))

    # --- scoring orchestration (no evaluate(); reward lives here) ------------
    def run_batch(self, tasks: list[dict], *, rollouts: list[dict] | None = None,
                  scheduler=None, executor=None, provider: str | None = None,
                  skill_path: str | None = None, workdir_root: str | None = None) -> list[dict]:
        """Score a batch into ``[{"id","hard","soft"}, ...]``.

        Pass pre-computed ``rollouts`` (hermetic path) or a scheduler+executor to
        produce them. Order follows ``tasks``; a missing rollout scores as a miss.
        """
        if rollouts is None:
            rollouts = asyncio.run(self.rollout(
                tasks, scheduler=scheduler, executor=executor, provider=provider,
                skill_path=skill_path, workdir_root=workdir_root))
        by_id = {r["id"]: r for r in rollouts}
        out: list[dict] = []
        for task in tasks:
            r = by_id.get(task["id"])
            out.append(score_timestamp(task, r) if r is not None
                       else {"id": task["id"], "hard": 0, "soft": 0.0})
        return out

    def _build_prompt(self, task: dict) -> str:
        return ("Apply the timestamp skill for this turn.\n"
                f"Task: {task['prompt']}\n"
                "Create the requested files/folders in the current working directory.")
