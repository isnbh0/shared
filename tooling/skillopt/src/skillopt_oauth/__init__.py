"""SkillOpt Guard: run Microsoft SkillOpt through local agent CLIs with routing
and credential preflight.

A thin launch wrapper (console script ``skillopt-oauth``) around upstream's
``skillopt-train``: it runs a fail-closed OAuth preflight, scrubs every
``*_API_KEY`` / ``*_AUTH_TOKEN`` from the child env so a metered fallback is
impossible by construction, routes upstream at its local CLI backends, then
``exec``s upstream. See :mod:`skillopt_oauth.oauth_guard`.
"""
from __future__ import annotations

from .oauth_guard import (
    OAuthPreflightError,
    build_record,
    configure_backends,
    extract_optimizer_backend,
    extract_out_root,
    main,
    preflight,
    redact_argv,
    scrub_env,
    write_record,
)

__version__ = "0.4.0"

__all__ = [
    "OAuthPreflightError",
    "build_record",
    "configure_backends",
    "extract_optimizer_backend",
    "extract_out_root",
    "main",
    "preflight",
    "redact_argv",
    "scrub_env",
    "write_record",
    "__version__",
]
