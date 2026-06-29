"""Frozen-val data loader for the `spex_write_phased` env."""
from __future__ import annotations

from pathlib import Path

from skillopt_oauth.base import SplitDataLoader
from skillopt_oauth.envs import _io


class SpexWritePhasedDataLoader(SplitDataLoader):
    """Loads `spex_write_phased` tasks from ``tasks/spex_write_phased/{train,val}/*.jsonl``.

    Val is read from ``val/`` and stable-sorted by id: FROZEN, never resampled.
    Train resampling is deterministic per seed via ``sample_train_batch``.
    """

    env_name = "spex_write_phased"

    def __init__(self, tasks_dir: str | Path | None = None, *,
                 val_fraction: float = 0.40, split_seed: object = 20260629):
        super().__init__()  # base plumbing only (Phase 1); no required args
        if tasks_dir is None:
            self.tasks_dir = _io.project_root(__file__) / "tasks" / self.env_name
        else:
            self.tasks_dir = Path(tasks_dir)
        self.val_fraction = val_fraction
        self.split_seed = split_seed
        self._train: list[dict] | None = None
        self._val: list[dict] | None = None

    def load(self) -> dict:
        train = self._train
        if train is None:
            train = self._train = _io.read_jsonl_dir(self.tasks_dir / "train")
        val = self._val
        if val is None:
            val = self._val = _io.read_jsonl_dir(self.tasks_dir / "val")
        return {"train": list(train), "val": list(val)}

    def train_split(self) -> list[dict]:
        return self.load()["train"]

    def val_split(self) -> list[dict]:
        return self.load()["val"]

    def sample_train_batch(self, batch_size: int, *, seed: object) -> list[dict]:
        pool = self.train_split()
        ordered = sorted(pool, key=lambda t: _io.hash_rank(seed, t["id"]))
        return ordered[:batch_size]

    @staticmethod
    def deterministic_split(pool: list[dict], *, val_fraction: float,
                            seed: object = 0) -> tuple[list[dict], list[dict]]:
        items = sorted(pool, key=lambda t: t["id"])
        train: list[dict] = []
        val: list[dict] = []
        for t in items:
            (val if _io.hash_bucket(seed, t["id"]) < val_fraction else train).append(t)
        return train, val
