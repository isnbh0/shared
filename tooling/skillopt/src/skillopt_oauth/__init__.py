"""SkillOpt-OAuth: a fork of Microsoft SkillOpt that routes every LLM call (rollout,
reflect/optimizer, judge) through OAuthed `claude` / `codex` CLI sessions instead of
metered provider APIs.

STUB STATE (Phase 1): package skeleton with a working config schema and environment
registry. The executor, scheduler, backends, reflect, gate, and checkpoint modules are
signature-only stubs filled in Phases 2-5.
"""
from __future__ import annotations

from .config import Config, load_config
from .registry import list_envs, register_env
from . import envs as _envs  # noqa: F401  (importing registers any benchmark envs)

__version__ = "0.1.0"

__all__ = ["Config", "load_config", "register_env", "list_envs", "__version__"]
