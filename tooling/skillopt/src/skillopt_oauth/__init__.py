"""skillopt-oauth: make Microsoft SkillOpt safe to run on ``claude`` / ``codex``
subscription CLIs.

A thin launch wrapper (console script ``skillopt-oauth``) around upstream's
``skillopt-train``: it runs a fail-closed OAuth preflight, scrubs every
``*_API_KEY`` / ``*_AUTH_TOKEN`` from the child env so a metered fallback is
impossible by construction, routes upstream at its ``claude_code_exec`` /
``codex_exec`` backends, then ``exec``s upstream. See :mod:`skillopt_oauth.oauth_guard`.
"""
from __future__ import annotations

from .oauth_guard import OAuthPreflightError, configure_backends, main, preflight, scrub_env

__version__ = "0.2.0"

__all__ = [
    "OAuthPreflightError",
    "configure_backends",
    "main",
    "preflight",
    "scrub_env",
    "__version__",
]
