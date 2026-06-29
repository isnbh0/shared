"""Deterministic scorer for the `spex_write_phased` skill.

Inspects the produced spec directory's structure, README headers, and per-phase
markers. Twelve boolean checks: hard = 1 iff all pass; soft = fraction passed.
"""
from __future__ import annotations

import os
import re
from pathlib import Path

SPEC_DIR_RE = re.compile(r"^\d{6}-\d{6}-")
PHASE_FILE_RE = re.compile(r"^P\d+-.+\.md$")
README_HEADERS = ("Design Principles", "Key Design Decisions",
                  "Phase Summary", "Progress Tracking")
PHASE_MARKERS = ("Goal", "Entry state", "Exit state",
                 "Implementation Checklist", "Required Tests")


def _find_spec_dir(ws: str | None) -> str | None:
    if not ws or not os.path.isdir(ws):
        return None
    for name in sorted(os.listdir(ws)):
        full = os.path.join(ws, name)
        if os.path.isdir(full) and SPEC_DIR_RE.match(name):
            return full
    return None


def _read(path: str | None) -> str:
    if not path:
        return ""
    try:
        return Path(path).read_text(encoding="utf-8")
    except OSError:
        return ""


def score(task: dict, rollout: dict | None) -> dict:
    tid = task["id"]
    ws = rollout.get("workspace_dir") if rollout else None
    checks: dict[str, bool] = {}

    spec_dir = _find_spec_dir(ws)
    checks["timestamped_dir"] = spec_dir is not None

    readme = os.path.join(spec_dir, "README.md") if spec_dir else None
    checks["readme_present"] = bool(readme and os.path.isfile(readme))

    phase_files: list[str] = []
    if spec_dir:
        phase_files = [os.path.join(spec_dir, n) for n in sorted(os.listdir(spec_dir))
                       if PHASE_FILE_RE.match(n)]
    checks["phase_file_present"] = len(phase_files) >= 1

    readme_text = _read(readme) if checks["readme_present"] else ""
    for header in README_HEADERS:
        checks[f"readme_header::{header}"] = header in readme_text

    phase_texts = [_read(p) for p in phase_files]
    for marker in PHASE_MARKERS:
        checks[f"phase_marker::{marker}"] = bool(phase_texts) and all(marker in t for t in phase_texts)

    total = len(checks)               # 1 + 1 + 1 + 4 + 5 = 12
    passed = sum(1 for v in checks.values() if v)
    soft = passed / total
    hard = 1 if all(checks.values()) else 0
    return {"id": tid, "hard": hard, "soft": round(soft, 6)}
