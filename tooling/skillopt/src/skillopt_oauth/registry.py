"""Environment registry for SkillOpt-OAuth (the canonical env-registration API).

STUB STATE: the registry mechanism is COMPLETE as of Phase 1. Zero environments are
registered until Phase 4 imports its env packages — each calls `register_env` at import
time. The registry lives in this dedicated module (NOT in `envs/__init__.py`) because
Phase 4 replaces `envs/__init__.py` to import the env subpackages; keeping the registry
here means that replacement never disturbs it.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class EnvSpec:
    """One registered environment: its adapter + loader classes and default config path."""

    name: str
    adapter_cls: type
    loader_cls: type
    default_config: Optional[str] = None


_ENV_REGISTRY: dict[str, EnvSpec] = {}


def register_env(name: str, *, adapter_cls: type, loader_cls: type,
                 default_config: str | None = None) -> None:
    """Register an environment under `name`. Raises ValueError on a duplicate name."""
    if name in _ENV_REGISTRY:
        raise ValueError(f"environment already registered: {name!r}")
    _ENV_REGISTRY[name] = EnvSpec(name=name, adapter_cls=adapter_cls,
                                  loader_cls=loader_cls, default_config=default_config)


def list_envs() -> list[str]:
    """Return registered environment names in sorted (deterministic) order."""
    return sorted(_ENV_REGISTRY)


def get_env(name: str) -> EnvSpec:
    """Return the `EnvSpec` registered under `name`. Raises KeyError if absent."""
    try:
        return _ENV_REGISTRY[name]
    except KeyError as exc:
        raise KeyError(
            f"no environment registered as {name!r}; known: {list_envs()}"
        ) from exc
