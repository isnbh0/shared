"""Pure, deterministic helpers shared by benchmark environments.

No LLM, no CLI, no randomness: every function is a pure function of its inputs
and the on-disk task files, so scorers and loaders stay reproducible.
"""
from __future__ import annotations

import glob
import hashlib
import json
from pathlib import Path


def project_root(start: str | None = None) -> Path:
    """Ascend from ``start`` (or this file) until a ``pyproject.toml`` is found.

    Falls back to the package layout root (``tooling/skillopt/``) if none is found.
    """
    here = Path(start or __file__).resolve()
    for parent in [here, *here.parents]:
        if (parent / "pyproject.toml").exists():
            return parent
    return Path(__file__).resolve().parents[3]


def read_jsonl_dir(directory: str | Path) -> list[dict]:
    """Read every ``*.jsonl`` file in ``directory`` and return rows stable-sorted by id.

    Blank lines and lines beginning with ``#`` (e.g. a path header) are skipped.
    """
    rows: list[dict] = []
    for fp in sorted(glob.glob(str(Path(directory) / "*.jsonl"))):
        with open(fp, "r", encoding="utf-8") as fh:
            for line in fh:
                s = line.strip()
                if not s or s.startswith("#"):
                    continue
                rows.append(json.loads(s))
    rows.sort(key=lambda t: t["id"])
    return rows


def hash_rank(seed: object, key: str) -> int:
    """Stable, process-independent integer rank for ``key`` under ``seed``."""
    return int(hashlib.sha256(f"{seed}:{key}".encode("utf-8")).hexdigest(), 16)


def hash_bucket(seed: object, key: str, buckets: int = 10000) -> float:
    """Stable bucket in ``[0, 1)`` for ``key`` under ``seed``."""
    return (hash_rank(seed, key) % buckets) / buckets
