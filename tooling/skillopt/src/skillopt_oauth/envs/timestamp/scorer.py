"""Deterministic scorer for the `timestamp` skill.

The skill must prefix every newly created top-level file/folder with a
`yymmdd-HHMMSS-` timestamp. Reward is fully programmatic: no LLM judge.
"""
from __future__ import annotations

import os
import re

TS_PREFIX = re.compile(r"^\d{6}-\d{6}-")


def _produced_names(rollout: dict | None) -> list[str]:
    """Top-level names the rollout produced, ignoring dotfiles.

    Prefers an explicit ``produced_names`` list when present; otherwise scans the
    rollout's ``workspace_dir`` (which the adapter creates fresh per task).
    """
    if not rollout:
        return []
    explicit = rollout.get("produced_names")
    if explicit is not None:
        return [n for n in explicit if not str(n).startswith(".")]
    ws = rollout.get("workspace_dir")
    if ws and os.path.isdir(ws):
        return sorted(n for n in os.listdir(ws) if not n.startswith("."))
    return []


def score(task: dict, rollout: dict | None) -> dict:
    """Return ``{"id", "hard", "soft"}`` for a single timestamp rollout.

    hard = 1 iff every produced name matches ``^\\d{6}-\\d{6}-`` and at least
    ``min_artifacts`` (default 1) names were produced. soft = fraction matching.
    """
    tid = task["id"]
    names = _produced_names(rollout)
    if not names:
        return {"id": tid, "hard": 0, "soft": 0.0}
    matched = [n for n in names if TS_PREFIX.match(n)]
    soft = len(matched) / len(names)
    min_artifacts = int(task.get("min_artifacts", 1))
    hard = 1 if (len(matched) == len(names) and len(names) >= min_artifacts) else 0
    return {"id": tid, "hard": hard, "soft": round(soft, 6)}
