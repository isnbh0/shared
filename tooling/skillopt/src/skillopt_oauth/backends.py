"""The ``oauth_cli`` backend: rollout, reflect, and judge funnel into the executor.

There is no chat / API backend anywhere in the fork. Each of the three call
types is a thin wrapper over :meth:`OAuthCLIExecutor.run_cli`, except the judge,
which prefers a deterministic Python scorer and only touches the CLI when it is
forced (spine section 5).
"""
from __future__ import annotations

import json
from typing import Callable

from .executor import (
    CliResult,
    ExecutorError,
    OAuthCLIExecutor,
    extract_json_object,
    parse_patch_json,
)

__all__ = [
    "BACKEND_NAME",
    "register_oauth_cli_backend",
    "get_backend",
    "build_executor",
    "run_rollout",
    "run_reflect",
    "run_judge",
]

BACKEND_NAME = "oauth_cli"

# Module-local fallback table; an external registry is used when one is passed.
_BACKENDS: dict[str, Callable[..., OAuthCLIExecutor]] = {}


def build_executor(**kwargs) -> OAuthCLIExecutor:
    """Construct an :class:`OAuthCLIExecutor` (the only backend factory)."""
    return OAuthCLIExecutor(**kwargs)


def _register_into(registry, name, factory) -> None:
    register = getattr(registry, "register", None)
    if callable(register):
        register(name, factory)
    else:
        registry[name] = factory


def register_oauth_cli_backend(registry=None, **executor_defaults):
    """Register the ``oauth_cli`` backend factory.

    Integrates with the Phase 1 registry when ``registry`` is supplied (either an
    object exposing ``.register(name, factory)`` or a mapping); always records the
    factory in the module-local table so tests and Phase 3 can resolve it.
    """
    def factory(**overrides) -> OAuthCLIExecutor:
        return OAuthCLIExecutor(**{**executor_defaults, **overrides})

    _BACKENDS[BACKEND_NAME] = factory
    if registry is not None:
        _register_into(registry, BACKEND_NAME, factory)
    return factory


def get_backend(name: str = BACKEND_NAME) -> Callable[..., OAuthCLIExecutor]:
    return _BACKENDS[name]


def run_rollout(executor: OAuthCLIExecutor, *, prompt: str, skill_path: str | None = None,
                provider: str = "claude", workdir: str | None = None,
                timeout: float = 600.0) -> CliResult:
    """Run one rollout of the candidate skill through the CLI.

    Returns the raw :class:`CliResult` (non-raising, like the executor). The
    Phase 3 loop must treat ``result.auth_billing_warning`` as a failure signal
    -- a rollout that slipped onto a metered path must not be scored or rewarded.
    """
    return executor.run_cli(provider=provider, prompt=prompt, skill_path=skill_path,
                            workdir=workdir, timeout=timeout)


def run_reflect(executor: OAuthCLIExecutor, *, prompt: str, skill_path: str | None = None,
                provider: str = "codex", workdir: str | None = None, timeout: float = 600.0,
                repair: Callable[[str], str] | None = None) -> dict:
    """Run the optimizer/reflect call and return a schema-valid edit-op patch."""
    result = executor.run_cli(provider=provider, prompt=prompt, skill_path=skill_path,
                              workdir=workdir, timeout=timeout)
    if result.exit_code != 0 or result.auth_billing_warning:
        raise ExecutorError(
            f"reflect call failed (exit {result.exit_code}, "
            f"auth_billing_warning={result.auth_billing_warning}): "
            f"{result.stderr.strip()}"
        )
    return parse_patch_json(result.stdout, repair=repair)


def run_judge(executor: OAuthCLIExecutor, *, task: dict, rollout: dict,
              scorer: Callable[[dict, dict], dict] | None = None, force_llm: bool = False,
              prompt: str | None = None, provider: str = "codex",
              skill_path: str | None = None, workdir: str | None = None,
              timeout: float = 600.0) -> dict:
    """Score a rollout, preferring the deterministic scorer.

    ``rollout`` is the full rollout record (``{"id", "stdout", "workspace_dir", ...}``);
    deterministic scorers (Phase 4) inspect its workspace, so the canonical scorer
    signature is ``score(task, rollout)``. When a ``scorer`` is available and
    ``force_llm`` is False it is used and no CLI call is made. Otherwise the rubric
    ``prompt`` is sent through the CLI and a ``{"hard": .., "soft": ..}`` object is
    parsed from stdout.
    """
    if scorer is not None and not force_llm:
        return scorer(task, rollout)
    if prompt is None:
        raise ValueError("run_judge requires a rubric 'prompt' when calling the CLI")
    result = executor.run_cli(provider=provider, prompt=prompt, skill_path=skill_path,
                              workdir=workdir, timeout=timeout)
    if result.exit_code != 0 or result.auth_billing_warning:
        raise ExecutorError(
            f"judge call failed (exit {result.exit_code}, "
            f"auth_billing_warning={result.auth_billing_warning}): "
            f"{result.stderr.strip()}"
        )
    return _parse_judge_score(result.stdout, task["id"])


def _parse_judge_score(stdout: str, task_id) -> dict:
    obj = json.loads(extract_json_object(stdout))
    hard = 1 if int(obj.get("hard", 0)) else 0
    soft = float(obj.get("soft", hard))
    return {"id": task_id, "hard": hard, "soft": max(0.0, min(1.0, soft))}
