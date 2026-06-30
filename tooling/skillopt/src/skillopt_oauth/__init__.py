"""skillopt-oauth: make Microsoft SkillOpt safe to run on ``claude`` / ``codex``
subscription CLIs.

A thin launch wrapper (console script ``skillopt-oauth``) around upstream's
``skillopt-train``: it runs a fail-closed OAuth preflight, scrubs every
``*_API_KEY`` / ``*_AUTH_TOKEN`` from the child env so a metered fallback is
impossible by construction, routes upstream at its ``claude_code_exec`` /
``codex_exec`` backends, then ``exec``s upstream. See :mod:`skillopt_oauth.oauth_guard`.
"""
from __future__ import annotations

from .oauth_guard import (
    OAuthPreflightError,
    build_record,
    configure_backends,
    extract_out_root,
    main,
    preflight,
    redact_argv,
    scrub_env,
    write_record,
)

__version__ = "0.3.0"

__all__ = [
    "OAuthPreflightError",
    "build_record",
    "configure_backends",
    "extract_out_root",
    "main",
    "preflight",
    "redact_argv",
    "scrub_env",
    "write_record",
    "__version__",
]
