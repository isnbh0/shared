"""Base classes consumed by the Phase 4 envs: `EnvAdapter` + `SplitDataLoader`.

Prefer the upstream SkillOpt base classes when the pinned `skillopt` package is
importable; otherwise fall back to local abstract definitions with the SAME surface so
the fork's envs and the hermetic test suite work offline without upstream installed.
The fork's surface is the contract: `build_train_env` / `build_eval_env` / `rollout` /
`get_task_types` (there is intentionally NO `evaluate()`; deterministic scoring lives in
each env's scorer + `run_batch`, Phase 4).
"""
from __future__ import annotations

from abc import ABC, abstractmethod

try:  # prefer upstream when the pinned dependency is installed (Phase 2 pins it)
    from skillopt.envs import EnvAdapter, SplitDataLoader  # type: ignore
except Exception:  # hermetic fallback: no upstream installed (tests, Phase 1)

    class EnvAdapter(ABC):
        """Abstract environment adapter (fork surface; no `evaluate()`)."""

        env_name: str = ""

        @abstractmethod
        def build_train_env(self) -> dict: ...

        @abstractmethod
        def build_eval_env(self) -> dict: ...

        @abstractmethod
        async def rollout(self, tasks: list[dict], **kwargs) -> list[dict]: ...

        @abstractmethod
        def get_task_types(self) -> list[str]: ...

    class SplitDataLoader(ABC):
        """Abstract split loader: train/val splits with a FROZEN val split."""

        env_name: str = ""

        @abstractmethod
        def train_split(self) -> list[dict]: ...

        @abstractmethod
        def val_split(self) -> list[dict]: ...


__all__ = ["EnvAdapter", "SplitDataLoader"]
