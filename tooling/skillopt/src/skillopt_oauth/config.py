"""Configuration schema and loader for SkillOpt-OAuth.

STUB STATE: COMPLETE — this module is fully functional as of Phase 1.
FUTURE: Phases 3 and 5 add consumers of these fields (scheduler pools, gate
thresholds, reflection mode). New fields may be appended with defaults to stay
backward compatible; no schema rewrite is anticipated.
"""
from __future__ import annotations

from dataclasses import dataclass, fields
from pathlib import Path
from typing import Optional

import yaml


@dataclass
class Config:
    """Run configuration. Defaults mirror stock SkillOpt and the design spine."""

    # --- ML core (mirrors stock SkillOpt) ---
    batch_size: int = 40
    minibatch_size: int = 8
    lr: int = 4
    min_lr: int = 2
    lr_schedule: str = "cosine"          # "cosine" | "linear" | "constant"
    slow_update_samples: int = 20

    # --- OAuth scheduler (Phase 3) ---
    claude_pool: int = 6
    codex_pool: int = 6
    rate_per_min: float = 60.0           # token-bucket req/min, below the provider cap
    per_call_timeout: float = 600.0      # per-call CLI timeout (seconds)
    max_retries: int = 5                 # bounded retry budget per job
    circuit_breaker_threshold: int = 5   # consecutive failures before the breaker opens
    circuit_reset_timeout: float = 30.0  # seconds before a half-open probe

    # --- provider routing (dual identity; spine §4) ---
    rollout_provider: str = "claude"     # rollouts + validation evals billed here
    reflect_provider: str = "codex"      # reflect/judge billed to the second identity

    # --- gate + reflection (Phase 5) ---
    gate_mode: str = "variance"          # "variance" | "strict"
    reflection_mode: str = "parallel"    # "parallel" | "sequential"
    n_samples: int = 3

    # --- model pinning (Phase 2) ---
    model_claude: Optional[str] = None
    model_codex: Optional[str] = None
    reasoning_effort: str = "xhigh"

    # --- safety ---
    forbid_api_keys: bool = True


def _known_field_names() -> set[str]:
    return {f.name for f in fields(Config)}


def load_config(path: str | Path) -> Config:
    """Load a YAML config file into a `Config`, filling unspecified keys with defaults.

    An empty (or body-less) YAML file yields all defaults. Unknown top-level keys are
    ignored so env-specific YAML (added in Phase 4, e.g. task paths) may carry extra
    sections without breaking the loader. A non-mapping root is an error.
    """
    path = Path(path)
    with path.open("r", encoding="utf-8") as fh:
        data = yaml.safe_load(fh) or {}
    if not isinstance(data, dict):
        raise ValueError(
            f"config root must be a mapping, got {type(data).__name__}: {path}"
        )
    known = _known_field_names()
    kwargs = {key: value for key, value in data.items() if key in known}
    return Config(**kwargs)
