"""EnvAdapter for the `spex_write_phased` env.

Same abstract surface and scoring orchestration as the timestamp adapter,
specialized to produce a phased-spec rollout prompt and to score with the
spec-structure scorer.
"""
from __future__ import annotations

import asyncio
import tempfile
from pathlib import Path

from skillopt_oauth.base import EnvAdapter
from skillopt_oauth.envs.spex_write_phased.dataloader import SpexWritePhasedDataLoader
from skillopt_oauth.envs.spex_write_phased.scorer import score as score_spex
from skillopt_oauth.scheduler import cli_job


class SpexWritePhasedAdapter(EnvAdapter):
    env_name = "spex_write_phased"

    def __init__(self, loader: SpexWritePhasedDataLoader | None = None, *,
                 provider: str = "claude", skill_path: str | None = None):
        super().__init__()  # base plumbing only (Phase 1); no required args
        self.loader = loader or SpexWritePhasedDataLoader()
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
                      workdir_root: str | None = None, timeout: float = 900.0) -> list[dict]:
        """Run rollouts in parallel; one workspace per task.

        Routed through :func:`skillopt_oauth.scheduler.cli_job` so the pool's full
        backoff / retry / circuit-breaker stack and ``CliResult`` classification
        (rate-limit / timeout / auth-billing) apply uniformly (README known-risk #2).
        """
        provider = provider or self.provider
        skill_path = skill_path or self.skill_path
        root = Path(workdir_root) if workdir_root else Path(tempfile.mkdtemp(prefix="spex_roll_"))

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
        if rollouts is None:
            rollouts = asyncio.run(self.rollout(
                tasks, scheduler=scheduler, executor=executor, provider=provider,
                skill_path=skill_path, workdir_root=workdir_root))
        by_id = {r["id"]: r for r in rollouts}
        out: list[dict] = []
        for task in tasks:
            r = by_id.get(task["id"])
            out.append(score_spex(task, r) if r is not None
                       else {"id": task["id"], "hard": 0, "soft": 0.0})
        return out

    def _build_prompt(self, task: dict) -> str:
        return ("Apply the write-phased spec skill for this turn.\n"
                f"Request: {task['prompt']}\n"
                "Produce a timestamped spec directory containing README.md and "
                "PN-*.md phase files in the current working directory.")
