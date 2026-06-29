"""Frozen-val data loader for the `timestamp` env."""
from __future__ import annotations

from pathlib import Path

from skillopt_oauth.base import SplitDataLoader
from skillopt_oauth.envs import _io


class TimestampDataLoader(SplitDataLoader):
    """Loads `timestamp` tasks from ``tasks/timestamp/{train,val}/*.jsonl``.

    The val split is read straight from ``val/`` and stable-sorted by id: it is
    FROZEN and never resampled. Train may be resampled per step via
    ``sample_train_batch`` (deterministic for a given seed, different across seeds).
    """

    env_name = "timestamp"

    def __init__(self, tasks_dir: str | Path | None = None, *,
                 val_fraction: float = 0.34, split_seed: object = 20260629):
        super().__init__()  # base plumbing only (Phase 1); no required args
        if tasks_dir is None:
            tasks_dir = _io.project_root(__file__) / "tasks" / self.env_name
        self.tasks_dir = Path(tasks_dir)
        self.val_fraction = val_fraction
        self.split_seed = split_seed
        self._train: list[dict] | None = None
        self._val: list[dict] | None = None

    def load(self) -> dict:
        if self._train is None:
            self._train = _io.read_jsonl_dir(self.tasks_dir / "train")
        if self._val is None:
            self._val = _io.read_jsonl_dir(self.tasks_dir / "val")
        return {"train": list(self._train), "val": list(self._val)}

    def train_split(self) -> list[dict]:
        return self.load()["train"]

    def val_split(self) -> list[dict]:
        # Frozen: identical order and membership on every call.
        return self.load()["val"]

    def sample_train_batch(self, batch_size: int, *, seed: object) -> list[dict]:
        pool = self.train_split()
        ordered = sorted(pool, key=lambda t: _io.hash_rank(seed, t["id"]))
        return ordered[:batch_size]

    @staticmethod
    def deterministic_split(pool: list[dict], *, val_fraction: float,
                            seed: object = 0) -> tuple[list[dict], list[dict]]:
        """Stable sort by id, then hash-bucket each id into train/val.

        Pure and reproducible: the val membership for a given (pool, fraction,
        seed) never changes across calls or processes.
        """
        items = sorted(pool, key=lambda t: t["id"])
        train: list[dict] = []
        val: list[dict] = []
        for t in items:
            (val if _io.hash_bucket(seed, t["id"]) < val_fraction else train).append(t)
        return train, val
