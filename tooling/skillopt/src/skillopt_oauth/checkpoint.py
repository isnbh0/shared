"""Write-ahead checkpoint + resume (spine §7, design principle 7).

OAuth sessions and quotas die mid-run, so we persist a complete snapshot after
EVERY step: the current skill doc, step/epoch indices, the data cursor, the RNG
state, the best score + best skill so far, and the result cache. Writes are atomic
(tmp file + fsync + os.replace) so an interrupted write never corrupts the WAL —
on resume the in-flight step is simply recomputed (it left no committed state).
"""
from __future__ import annotations

import json
import os
import random
from dataclasses import asdict, dataclass, field

from .gate import ResultCache


def _rng_to_jsonable(state: tuple) -> list:
    version, internal, gauss = state
    return [version, list(internal), gauss]


def _rng_from_jsonable(blob: list) -> tuple:
    version, internal, gauss = blob
    return (version, tuple(internal), gauss)


@dataclass
class TrainState:
    """The complete, serializable training snapshot."""
    skill_doc: str
    epoch: int = 0
    step: int = 0               # global step counter
    step_in_epoch: int = 0
    data_cursor: int = 0
    best_score: float = float("-inf")
    best_skill_doc: str = ""
    sigma_gate: float = 0.0
    rng_state: list = field(
        default_factory=lambda: _rng_to_jsonable(random.Random(0).getstate()))
    cache: ResultCache = field(default_factory=ResultCache)

    def get_rng(self) -> random.Random:
        r = random.Random()
        r.setstate(_rng_from_jsonable(self.rng_state))
        return r

    def set_rng(self, r: random.Random) -> None:
        self.rng_state = _rng_to_jsonable(r.getstate())

    def to_dict(self) -> dict:
        d = asdict(self)
        d["cache"] = self.cache.to_dict()
        return d

    @classmethod
    def from_dict(cls, d: dict) -> "TrainState":
        d = dict(d)
        cache = ResultCache.from_dict(d.pop("cache", {}))
        st = cls(**d)
        st.cache = cache
        return st


def write_checkpoint(path: str, state: TrainState) -> None:
    """Atomically persist the train state (write tmp, fsync, os.replace)."""
    parent = os.path.dirname(os.path.abspath(path))
    os.makedirs(parent, exist_ok=True)
    tmp = f"{path}.tmp.{os.getpid()}"
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump(state.to_dict(), fh, ensure_ascii=False, indent=2, sort_keys=True)
        fh.flush()
        os.fsync(fh.fileno())
    os.replace(tmp, path)


def resume(path: str) -> TrainState | None:
    """Restore a TrainState from a checkpoint, or None if none exists."""
    if not os.path.exists(path):
        return None
    with open(path, "r", encoding="utf-8") as fh:
        return TrainState.from_dict(json.load(fh))
