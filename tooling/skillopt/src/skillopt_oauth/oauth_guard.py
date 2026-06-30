"""Make Microsoft SkillOpt safe to run on ``claude`` / ``codex`` subscription CLIs.

Upstream SkillOpt ships the ``claude_code_exec`` / ``codex_exec`` target backends,
but every exec site spawns the CLI with **no env scrub and no OAuth preflight**
(``skillopt/model/claude_backend.py``, ``codex_backend.py``, ``codex_harness.py``).
Because upstream's ``subprocess.run`` inherits the parent env, a stray
``ANTHROPIC_API_KEY`` / ``OPENAI_API_KEY`` silently flips the call onto the metered
provider API even with a valid subscription session -- the billing footgun.

This module is a thin launch wrapper (console script ``skillopt-oauth``) that,
before handing off to upstream's ``skillopt-train``, does the three things upstream
omits, then ``exec``s upstream:

1. **Fail-closed OAuth preflight** -- confirm a subscription credential for the
   provider in use (claude: env ``CLAUDE_CODE_OAUTH_TOKEN`` / macOS Keychain
   ``Claude Code-credentials`` / ``~/.claude/.credentials.json``; codex:
   ``~/.codex/auth.json`` ``auth_mode == "chatgpt"``). Refuse to launch otherwise.
2. **Env scrub** -- strip every ``*_API_KEY`` / ``*_AUTH_TOKEN`` from the
   environment the child inherits, so a metered fallback is impossible by
   construction. Fixing *our* process env fixes upstream's footgun without
   patching upstream.
3. **Route both legs onto the CLI** -- point ``CLAUDE_CODE_EXEC_PATH`` /
   ``CODEX_EXEC_PATH`` at the OAuth CLI, and inject an explicit
   ``--optimizer_backend`` so the optimizer/reflect leg rides the subscription CLI
   too. Upstream's ``--backend`` macro otherwise defaults the optimizer to the
   metered ``openai_chat``, and env is inert for upstream's selection -- so the
   argv flag is what actually keeps the whole loop on the subscription.

Then ``os.execvpe`` upstream's ``skillopt-train`` (console script
``scripts.train:main``), passing through all user args.

The training loop, gate, reflect, checkpoint, scheduler, scorers, and demo envs are
upstream's responsibility; this wrapper owns only the preflight, scrub, and routing
above.

**Records & observability.** The wrapper is the only thing that knows *which*
credential it proved, *which* metered keys it neutralized, and *where* it routed --
a security/billing-audit fact nobody downstream captures. So per invocation it
leaves a secret-safe, queryable record of its own decision (JSONL, append-only,
joined on ``run_id``) plus a structured stderr log line, keyed by a generated
``run_id`` that is also exported into the child for output correlation. Records and
logging are **fail-soft**: any I/O error warns to stderr and the launch proceeds.
All control is env-vars only (see the module-level constants below); the arg
namespace stays a pure passthrough to upstream's ``skillopt-train``.
"""
from __future__ import annotations

import json
import logging
import os
import platform
import re
import shlex
import shutil
import signal
import subprocess
import sys
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Mapping

__all__ = [
    "OAuthPreflightError",
    "PROVIDERS",
    "KNOWN_SECRET_FLAGS",
    "SCHEMA_VERSION",
    "default_oauth_probe",
    "scrub_env",
    "resolve_target",
    "preflight",
    "configure_backends",
    "redact_argv",
    "extract_out_root",
    "extract_optimizer_backend",
    "build_record",
    "write_record",
    "main",
]

# Upstream's training entry point (``[project.scripts] skillopt-train = scripts.train:main``).
UPSTREAM_TRAIN = "skillopt-train"

PROVIDERS = ("claude", "codex")

# Provider -> upstream target (rollout) backend that spawns the OAuth CLI.
_TARGET_BACKEND = {"claude": "claude_code_exec", "codex": "codex_exec"}

# Provider -> the optimizer/reflect backend that rides the SAME OAuth CLI as the
# target, so the full optimize loop runs on the subscription. ``claude_chat`` shells
# ``claude -p`` and ``codex_chat`` shells ``codex exec`` -- both keyless. Upstream's
# ``--backend`` macro otherwise defaults the optimizer to the metered ``openai_chat``
# (``scripts/train.py``), and env is inert for upstream's selection, so the wrapper
# makes this real by injecting an explicit ``--optimizer_backend`` argv flag (see
# ``main``). ``codex_chat`` needs the vendored fork's optimizer allowlist + dispatcher
# (``vendor/skillopt``); ``claude_chat`` already works against stock upstream.
_OPTIMIZER_BACKEND = {"claude": "claude_chat", "codex": "codex_chat"}

# Provider -> the env var upstream reads for the CLI binary path.
_EXEC_PATH_VAR = {"claude": "CLAUDE_CODE_EXEC_PATH", "codex": "CODEX_EXEC_PATH"}

# Provider -> default CLI binary name on PATH.
_DEFAULT_BIN = {"claude": "claude", "codex": "codex"}

# Env var that lets a user pin which provider to guard/route when it cannot be
# inferred from the passthrough args.
_TARGET_ENV = "SKILLOPT_OAUTH_TARGET"

# Env var that overrides which optimizer backend the wrapper injects (default: the
# per-provider value in ``_OPTIMIZER_BACKEND``). A backend name forces that optimizer;
# ``off``/``none``/empty disables the injection entirely, letting upstream/config
# decide (the scrub still backstops billing). Never a CLI flag -- env-only surface.
_OPTIMIZER_ENV = "SKILLOPT_OAUTH_OPTIMIZER"

# -- observability env-var surface (all optional) ---------------------------
_LOG_DIR_ENV = "SKILLOPT_OAUTH_LOG_DIR"       # record dir; default .agent-workspace/skillopt-oauth
_LOG_ENV = "SKILLOPT_OAUTH_LOG"               # 0|off disables the file write
_LOG_LEVEL_ENV = "SKILLOPT_OAUTH_LOG_LEVEL"   # default INFO; refusal logs at ERROR
_DRY_RUN_ENV = "SKILLOPT_OAUTH_DRY_RUN"       # 1 -> record dry_run, print, no exec
_SUPERVISE_ENV = "SKILLOPT_OAUTH_SUPERVISE"   # 1 -> supervise (completion record)
_INJECT_OUT_ROOT_ENV = "SKILLOPT_OAUTH_INJECT_OUT_ROOT"  # 1 -> inject --out_root
_RUN_ID_ENV = "SKILLOPT_OAUTH_RUN_ID"         # exported into the child, not read

# Record filename under the log dir.
_RECORD_FILE = "runs.jsonl"

# Logger name (a named logger -> stderr; never basicConfig, never stdout).
_LOGGER_NAME = "skillopt-oauth"

# Bumped when the record shape changes; readers key off this.
SCHEMA_VERSION = 2


class OAuthPreflightError(RuntimeError):
    """Raised when the CLI would NOT resolve to a subscription OAuth credential.

    Failing closed here is the guard against silently running on a metered API: if
    the probe cannot confirm OAuth (or would resolve to an API key), nothing is
    launched. ``verdict`` carries the probe result that triggered the refusal so
    ``main`` can record it without re-probing the keychain (which risks a second
    ACL prompt).
    """

    verdict: str | None = None


# -- OAuth probes -----------------------------------------------------------


def default_oauth_probe(provider: str) -> str:
    """Best-effort resolution of the credential the CLI would actually use.

    Returns ``'oauth'`` (a subscription credential), ``'api_key'`` (a metered API
    key would win), or ``'none'`` (nothing resolvable). Injectable via
    ``preflight(probe=...)`` / ``main(probe=...)`` so tests stay hermetic and never
    touch a real keychain / ``auth.json``.
    """
    return _probe_claude_oauth() if provider == "claude" else _probe_codex_oauth()


def _probe_claude_oauth() -> str:
    # A `claude setup-token` OAuth token is an explicit subscription credential.
    if os.environ.get("CLAUDE_CODE_OAUTH_TOKEN"):
        return "oauth"
    cred = Path.home() / ".claude" / ".credentials.json"
    try:
        data = json.loads(cred.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        data = None
    if isinstance(data, dict):
        oauth = data.get("claudeAiOauth") or data.get("oauth") or {}
        if isinstance(oauth, dict) and oauth.get("subscriptionType"):
            return "oauth"
        if data.get("apiKey") or data.get("ANTHROPIC_API_KEY"):
            return "api_key"
    # On macOS there is no .credentials.json: the subscription credential lives in
    # the login Keychain. Consult it before falling back to "api_key"/"none".
    if _probe_claude_keychain() == "oauth":
        return "oauth"
    if os.environ.get("ANTHROPIC_API_KEY"):
        return "api_key"
    return "none"


def _probe_claude_keychain() -> str | None:
    """Return ``'oauth'`` iff the macOS login Keychain holds a Claude Code OAuth
    credential, else ``None``.

    Claude Code stores a subscription (``/login`` OAuth) credential under the
    generic-password service ``"Claude Code-credentials"``; an API-key login uses
    the distinct service ``"Claude Code"``. So the mere *presence* of the former
    item is the subscription signal. We do an existence/attribute lookup only --
    NOT ``-g``/``-w`` -- because decrypting the secret can trigger a Keychain ACL
    prompt that would hang a headless run, whereas listing the item does not.
    Best-effort and fail-safe: any error (non-macOS, missing ``security``, locked
    keychain) returns ``None`` so the caller falls through rather than crashing.
    """
    if platform.system() != "Darwin":
        return None
    cmd = ["security", "find-generic-password", "-s", "Claude Code-credentials"]
    account = os.environ.get("USER")
    if account:
        cmd += ["-a", account]
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
    except (OSError, subprocess.SubprocessError):
        return None
    return "oauth" if proc.returncode == 0 else None


def _probe_codex_oauth() -> str:
    home = os.environ.get("CODEX_HOME") or str(Path.home() / ".codex")
    auth = Path(home) / "auth.json"
    try:
        data = json.loads(auth.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return "none"
    mode = data.get("auth_mode") or data.get("preferred_auth_method")
    if mode == "chatgpt":
        return "oauth"
    if data.get("OPENAI_API_KEY") or mode in ("apikey", "api_key"):
        return "api_key"
    return "none"


# -- the three guard steps --------------------------------------------------


def scrub_env(environ: Mapping[str, str] | None = None) -> dict[str, str]:
    """Return a copy of ``environ`` with every metered-API credential removed.

    In ``-p`` / ``exec`` mode a stray ``*_API_KEY`` in the parent ALWAYS overrides
    the OAuth session, so strip every name ending in ``_API_KEY`` / ``_AUTH_TOKEN``
    (explicitly incl. ANTHROPIC_API_KEY, ANTHROPIC_AUTH_TOKEN, OPENAI_API_KEY,
    CODEX_API_KEY). ``CLAUDE_CODE_OAUTH_TOKEN`` is an OAuth token from
    ``claude setup-token`` (not an API key) and ends in neither suffix, so it
    survives. The suffix match is intentionally uppercase: the CLIs only read the
    canonical ``UPPER_CASE_API_KEY`` names, so a lowercase variant surviving here
    is inert.
    """
    src = os.environ if environ is None else environ
    env = {k: v for k, v in src.items()
           if not (k.endswith("_API_KEY") or k.endswith("_AUTH_TOKEN"))}
    for name in ("ANTHROPIC_API_KEY", "ANTHROPIC_AUTH_TOKEN",
                 "OPENAI_API_KEY", "CODEX_API_KEY"):
        env.pop(name, None)  # belt-and-suspenders past the suffix filter
    return env


def resolve_target(argv: list[str], environ: Mapping[str, str] | None = None) -> str:
    """Decide which provider to guard and route: ``'claude'`` or ``'codex'``.

    Precedence: an explicit backend in the passthrough args
    (``--backend`` / ``--target_backend``, ``--flag value`` or ``--flag=value``) >
    the ``SKILLOPT_OAUTH_TARGET`` env var > the default (``'claude'``). Any value
    mentioning ``codex`` selects codex; any value mentioning ``claude`` selects
    claude.

    The arg parse mirrors upstream's argparse so the guard preflights the provider
    that will actually run: ``--target_backend`` is authoritative over ``--backend``
    (it is the rollout backend that spawns the CLI), the **last** occurrence wins,
    and ``allow_abbrev`` abbreviations (e.g. ``--back codex_exec``) are recognized.
    """
    src = os.environ if environ is None else environ
    inferred = _target_from_args(argv)
    if inferred:
        return inferred
    env_target = (src.get(_TARGET_ENV) or "").strip().lower()
    if env_target in PROVIDERS:
        return env_target
    return "claude"


# Long options upstream reads to pick the rollout backend.
_BACKEND_FLAG = "--backend"
_TARGET_BACKEND_FLAG = "--target_backend"


def _backend_selector_kind(flag: str) -> str | None:
    """Return ``'target'`` / ``'backend'`` if ``flag`` is the ``--target_backend`` /
    ``--backend`` option or an unambiguous abbreviation of it, else ``None``.

    Upstream's parser has ``allow_abbrev=True``, so any non-empty prefix of a long
    option resolves to it; we mirror that here. ``--target_backend`` is checked first
    because it is authoritative for the rollout. The value still has to mention a
    provider to count (see ``_provider_of``), so over-matching an ambiguous prefix is
    harmless.
    """
    if len(flag) <= 2 or not flag.startswith("--"):
        return None
    if _TARGET_BACKEND_FLAG.startswith(flag):
        return "target"
    if _BACKEND_FLAG.startswith(flag):
        return "backend"
    return None


def _provider_of(value: str) -> str | None:
    low = (value or "").strip().lower()
    if "codex" in low:
        return "codex"
    if "claude" in low:
        return "claude"
    return None


def _target_from_args(argv: list[str]) -> str | None:
    target_vals: list[str] = []
    backend_vals: list[str] = []
    i = 0
    n = len(argv)
    while i < n:
        flag, eq, val = argv[i].partition("=")
        kind = _backend_selector_kind(flag)
        if kind:
            if eq:
                value = val
            elif i + 1 < n:
                value = argv[i + 1]
                i += 1  # consume the space-form value
            else:
                value = ""
            (target_vals if kind == "target" else backend_vals).append(value)
        i += 1
    # target_backend wins over backend; within each, last occurrence wins.
    for value in reversed(target_vals):
        provider = _provider_of(value)
        if provider:
            return provider
    for value in reversed(backend_vals):
        provider = _provider_of(value)
        if provider:
            return provider
    return None


def preflight(provider: str, *, probe: Callable[[str], str] | None = None) -> str:
    """Fail closed unless the resolved credential is a subscription OAuth one.

    The probe is injectable (hermetic tests); the default best-effort probe
    inspects the real credential stores. A verdict other than ``'oauth'`` -- incl.
    ``'api_key'`` and ``'none'`` -- raises rather than risk a silent metered call.
    The raised ``OAuthPreflightError`` carries the failing ``verdict`` so the caller
    can record it without re-probing. Returns the verdict (``'oauth'``) on success.
    """
    if provider not in PROVIDERS:
        raise ValueError(f"unknown provider {provider!r}; expected one of {PROVIDERS}")
    verdict = (probe or default_oauth_probe)(provider)
    if verdict != "oauth":
        err = OAuthPreflightError(
            f"{provider} would resolve to a non-subscription credential "
            f"(probe -> {verdict!r}); refusing to launch so the run cannot be "
            f"silently billed to a metered API. Sign in with an OAuth / "
            f"subscription session (claude: `claude /login` or `claude setup-token`; "
            f"codex: ChatGPT auth)."
        )
        err.verdict = verdict
        raise err
    return verdict


def configure_backends(env: dict[str, str], provider: str, *,
                       claude_bin: str | None = None,
                       codex_bin: str | None = None) -> dict[str, str]:
    """Point upstream's backend selection at the OAuth CLI for ``provider``.

    Sets ``TARGET_BACKEND`` (the rollout path that spawns the CLI), the paired
    ``OPTIMIZER_BACKEND``, and the provider's ``*_EXEC_PATH`` to the resolved CLI
    binary. A pre-existing exec-path value in ``env`` is honored (the user pinned
    it). Mutates and returns ``env``.
    """
    if provider not in PROVIDERS:
        raise ValueError(f"unknown provider {provider!r}; expected one of {PROVIDERS}")
    env["TARGET_BACKEND"] = _TARGET_BACKEND[provider]
    env["OPTIMIZER_BACKEND"] = _OPTIMIZER_BACKEND[provider]
    path_var = _EXEC_PATH_VAR[provider]
    if not env.get(path_var):
        override = claude_bin if provider == "claude" else codex_bin
        binary = override or _DEFAULT_BIN[provider]
        env[path_var] = shutil.which(binary) or binary
    return env


# -- argv redaction (security-critical; bias to over-redact) ----------------

# Known secret flags, enumerated from upstream ``scripts/train.py``. Suffix-only
# matching leaks because upstream's parser has ``allow_abbrev=True`` (``--azure_api_k
# sk-...`` is a valid secret pass), so these anchor exact + prefix matching.
KNOWN_SECRET_FLAGS = (
    "--azure_api_key",
    "--azure_openai_api_key",
    "--optimizer_azure_openai_api_key",
    "--target_azure_openai_api_key",
    "--qwen_chat_api_key",
    "--optimizer_qwen_chat_api_key",
    "--target_qwen_chat_api_key",
    "--minimax_api_key",
)
_KNOWN_SECRET_NAMES = frozenset(f.lstrip("-").lower() for f in KNOWN_SECRET_FLAGS)

# Sentinel substituted for a redacted value; also the whole-field fallback if
# redaction itself raises (never let a raw value through as the fallback).
_REDACTED = "<redacted>"
_REDACTION_FAILED = ["<argv-redaction-failed>"]


def _normalize_flag(flag: str) -> str:
    # Strip surrounding whitespace too: a cfg-options token like
    # ``model.azure_api_key =sk`` must still resolve to the secret key.
    return flag.strip().lstrip("-").lower()


def _is_secret_flag(norm: str, *, allow_prefix: bool = True) -> bool:
    """Decide whether a normalized flag/config-key name names a secret value.

    Security-biased -- when uncertain, redact. Order matters:
    1. exact known secret flag;
    2. prefix of any known secret flag (catches ``allow_abbrev`` abbreviations like
       ``azure_api_k``) -- only when ``allow_prefix`` (i.e. the token is a ``--`` flag,
       where argparse abbreviation applies). Bare ``--cfg-options`` keys are full config
       paths, never abbreviated, so the prefix rule is skipped for them -- otherwise a
       routing key like ``optimizer`` (a prefix of ``optimizer_..._api_key``) would be
       redacted out of the audit record;
    3. positive secret signals (``*_api_key``, contains ``secret``/``password``/
       ``credential``, ``*_auth_token``/``access_token``/``oauth_token``, ``*_token``/
       ``*_key``) -- these win over the numeric denylist, so e.g.
       ``--password_max_tokens`` is still redacted;
    4. numeric denylist (``*_max_tokens`` / ``*_completion_tokens`` /
       ``*_thinking_tokens``) is explicitly NOT secret -- it keeps the legitimate
       integer-valued flags out of the record verbatim;
    5. otherwise not secret.

    ``norm`` may be a flag name (``azure_api_key``) or a dotted/flat config key from
    ``--cfg-options`` (``model.azure_api_key``); the suffix/substring rules handle both.
    """
    if not norm:
        return False
    if norm in _KNOWN_SECRET_NAMES:
        return True
    if allow_prefix and any(known.startswith(norm) for known in _KNOWN_SECRET_NAMES):
        return True
    if norm.endswith("_api_key") or norm.endswith(".api_key") or norm == "api_key":
        return True
    if "secret" in norm or "password" in norm or "credential" in norm:
        return True
    if (norm.endswith("_auth_token") or norm.endswith("access_token")
            or norm.endswith("oauth_token")):
        return True
    if (norm.endswith("_max_tokens") or norm.endswith("_completion_tokens")
            or norm.endswith("_thinking_tokens")):
        return False
    # Forward-compat: any remaining ``*_token`` / ``*_key`` name is treated as a
    # secret (the numeric ``*_tokens`` flags are already excluded above).
    if norm.endswith("_token") or norm.endswith("_key"):
        return True
    return False


def redact_argv(argv: list[str]) -> list[str]:
    """Return a copy of ``argv`` with every secret *value* replaced by a sentinel.

    Covers three shapes, biased to over-redact:
    - ``--secret_flag value`` (space form);
    - ``--secret_flag=value`` (eq form);
    - bare ``key=value`` tokens with **no** ``--`` prefix -- upstream's preferred
      override channel ``--cfg-options`` (``allow_abbrev``, ``nargs="+"``) takes bare
      ``section.key=value`` tokens, and every metered secret is a real config path
      (``model.azure_api_key=...`` etc.), so those must be redacted too.

    Operates on a copy: the live ``argv`` handed to exec/supervise is verbatim and
    untouched. In the space form a ``--``-prefixed next token is treated as another
    option, not this flag's value (mirroring argparse, which rejects option-like
    values) -- so a secret value that itself starts with ``--`` must use the eq form,
    which is handled, and two adjacent secret flags no longer desync the value skip.
    """
    out = list(argv)
    n = len(out)
    i = 0
    while i < n:
        tok = out[i]
        if not isinstance(tok, str):
            i += 1
            continue
        if "=" in tok:
            key, _, val = tok.partition("=")
            # Abbreviation (prefix) matching applies only to ``--`` flags, where
            # argparse allow_abbrev does; a bare ``key=value`` cfg token is a full
            # config path and is matched exactly + by suffix only.
            if _is_secret_flag(_normalize_flag(key), allow_prefix=key.startswith("--")):
                out[i] = f"{key}={_REDACTED}"
            elif "=" in val:
                # ``--cfg-options=section.key=value`` (eq directly on the option):
                # the secret is keyed by the value's own ``k=v`` (a bare cfg key).
                subkey = val.partition("=")[0]
                if _is_secret_flag(_normalize_flag(subkey), allow_prefix=False):
                    out[i] = f"{key}={subkey}={_REDACTED}"
        elif tok.startswith("--") and _is_secret_flag(_normalize_flag(tok)):
            nxt = out[i + 1] if i + 1 < n else None
            if isinstance(nxt, str) and not nxt.startswith("--"):
                out[i + 1] = _REDACTED
                i += 1  # skip the value we just neutralized
        i += 1
    return out


def _redact_argv_safe(argv: list[str]) -> list[str]:
    """``redact_argv`` that never raises: on any failure returns the sentinel field
    (never a raw value), so a record build / dry-run print can't crash or leak."""
    try:
        return redact_argv(argv)
    except Exception:
        return list(_REDACTION_FAILED)


_OUT_ROOT_FLAG = "--out_root"


def extract_out_root(argv: list[str]) -> str | None:
    """Return the effective ``--out_root`` value from ``argv``, else ``None``.

    Mirrors upstream argparse: recognizes ``allow_abbrev`` abbreviations (any
    non-empty prefix of ``--out_root``, e.g. ``--out_ro``), the **last** occurrence
    wins, and a dangling flag whose following token is itself an option (or which is
    the last token) has no value (``None``). Keeping this argparse-faithful matters
    because a wrong/None result drives the opt-in ``--out_root`` injection decision.
    """
    result: str | None = None
    i = 0
    n = len(argv)
    while i < n:
        flag, eq, val = argv[i].partition("=")
        if len(flag) > 2 and _OUT_ROOT_FLAG.startswith(flag):
            if eq:
                result = val
            elif i + 1 < n and not argv[i + 1].startswith("--"):
                result = argv[i + 1]
                i += 1
            else:
                result = None  # dangling: argparse would reject / no value
        i += 1
    return result


_OPTIMIZER_BACKEND_FLAG = "--optimizer_backend"


def extract_optimizer_backend(argv: list[str]) -> str | None:
    """Return the user's explicit ``--optimizer_backend`` value from ``argv``, else None.

    Argparse-faithful, identical mechanics to ``extract_out_root``: ``allow_abbrev``
    prefixes (any non-empty prefix of ``--optimizer_backend``, e.g. ``--optimizer_b``),
    space + ``=`` forms, last-occurrence-wins, dangling/option-valued -> None. A prefix
    like ``--optimizer_m`` belongs to ``--optimizer_model`` -- it is NOT a prefix of
    ``--optimizer_backend`` -- so it is correctly ignored.
    """
    result: str | None = None
    i = 0
    n = len(argv)
    while i < n:
        flag, eq, val = argv[i].partition("=")
        if len(flag) > 2 and _OPTIMIZER_BACKEND_FLAG.startswith(flag):
            if eq:
                result = val
            elif i + 1 < n and not argv[i + 1].startswith("--"):
                result = argv[i + 1]
                i += 1
            else:
                result = None
        i += 1
    return result


def _resolve_optimizer_backend(argv: list[str], provider: str,
                               environ: Mapping[str, str]) -> tuple[str | None, bool]:
    """Return ``(optimizer_backend, injected)`` the run will actually use.

    Precedence: an explicit ``--optimizer_backend`` on argv wins and is never
    re-injected; else ``SKILLOPT_OAUTH_OPTIMIZER`` (a backend name -> inject it;
    ``off``/``none``/``0``/empty -> no injection, let upstream/config decide -- the
    scrub backstops billing); else the per-provider default from ``_OPTIMIZER_BACKEND``
    -> inject it. Injection is what actually selects the optimizer, since upstream
    reads CLI args/config, never env, for backend selection.
    """
    user = extract_optimizer_backend(argv)
    if user is not None:
        return user, False
    raw = environ.get(_OPTIMIZER_ENV)
    if raw is None:
        return _OPTIMIZER_BACKEND[provider], True
    val = raw.strip()
    if val.lower() in ("", "off", "none", "0", "false", "no"):
        return None, False
    return val, True


# -- record construction (pure, no I/O) -------------------------------------


def _wrapper_version() -> str:
    # Lazy import keeps __init__ the single source of truth without a circular
    # import at module load (oauth_guard is imported *by* __init__).
    try:
        from skillopt_oauth import __version__
        return __version__
    except Exception:
        return "unknown"


def _safe_cwd() -> str | None:
    """``os.getcwd()`` but fail-soft: ``None`` if the cwd was removed (so a deleted
    working directory can never raise into the launch path)."""
    try:
        return os.getcwd()
    except OSError:
        return None


# A canonical env var name (what a shell can assign). A scrubbed *value* is never
# recorded, but a pathological *name* could itself embed a secret (e.g.
# ``LEAK_sk-...-SECRET_API_KEY`` via ``env``), so any name that isn't a plain
# identifier is replaced before it reaches a record.
_ENV_NAME_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
_NON_IDENTIFIER_KEY = "<non-identifier-key>"


def _sanitize_env_name(name: str) -> str:
    return name if _ENV_NAME_RE.match(name) else _NON_IDENTIFIER_KEY


def build_record(*, event: str, run_id: str, ts: str, provider: str,
                 verdict: str | None, probe_name: str,
                 src_env: Mapping[str, str], child_env: Mapping[str, str],
                 routing: dict, argv: list[str], resolved_path: str | None,
                 out_root_arg: str | None, out_root_injected: bool,
                 preflight_providers: list[str] | None = None,
                 preflight_verdicts: Mapping[str, str | None] | None = None,
                 **extra) -> dict:
    """Build one record dict for ``event``. Non-secret by construction: only env
    *names* (sanitized; never values), a redacted argv copy, and routing/preflight
    metadata. Deterministic given ``ts`` + ``run_id``.

    ``extra`` adds event-specific fields (``exit_code``/``duration_s``/``end_ts`` on
    ``completed``; ``error`` on ``exec_failed``) but can never clobber a reserved
    field -- the reserved keys are written last.
    """
    argv_redacted = _redact_argv_safe(argv)
    scrubbed_keys = sorted({_sanitize_env_name(n) for n in (set(src_env) - set(child_env))})
    preflight_info: dict[str, Any] = {"verdict": verdict, "probe_name": probe_name}
    if preflight_providers is not None:
        preflight_info["providers"] = list(preflight_providers)
    if preflight_verdicts is not None:
        preflight_info["verdicts"] = dict(preflight_verdicts)
    return {
        **extra,
        "schema_version": SCHEMA_VERSION,
        "run_id": run_id,
        "ts": ts,
        "event": event,
        "wrapper_version": _wrapper_version(),
        "provider": provider,
        "preflight": preflight_info,
        "scrubbed_keys": scrubbed_keys,
        "routing": routing,
        "upstream": {
            "entry": UPSTREAM_TRAIN,
            "resolved_path": resolved_path,
            "out_root_arg": out_root_arg,
            "out_root_injected": out_root_injected,
        },
        "argv_redacted": argv_redacted,
        "cwd": _safe_cwd(),
        "pid": os.getpid(),
    }


# -- record persistence + structured logging (the only I/O; all fail-soft) --


def _get_logger() -> logging.Logger:
    """Return the named ``skillopt-oauth`` logger wired to stderr.

    Idempotent: attaches exactly one handler (never ``basicConfig``, never stdout)
    and refreshes its stream to the current ``sys.stderr`` each call so test capture
    works. Level comes from ``SKILLOPT_OAUTH_LOG_LEVEL`` (default INFO).
    """
    logger = logging.getLogger(_LOGGER_NAME)
    logger.propagate = False
    handler = None
    for h in logger.handlers:
        if getattr(h, "_skillopt_oauth", False):
            handler = h
            break
    if handler is None:
        handler = logging.StreamHandler()
        handler._skillopt_oauth = True  # type: ignore[attr-defined]
        handler.setFormatter(logging.Formatter("skillopt-oauth: %(message)s"))
        logger.addHandler(handler)
    handler.stream = sys.stderr  # type: ignore[attr-defined]  # refresh so pytest capsys captures it
    level_name = (os.environ.get(_LOG_LEVEL_ENV) or "INFO").strip().upper()
    logger.setLevel(getattr(logging, level_name, logging.INFO))
    return logger


def write_record(record: dict, *, log_dir: str, enabled: bool) -> None:
    """Append ``record`` as one JSONL line to ``<log_dir>/runs.jsonl``.

    Fail-soft: when ``enabled`` is False this is a no-op; on any error -- I/O
    (``OSError``) or a non-serializable record (``TypeError``/``ValueError``) -- it
    warns to stderr and returns so the launch proceeds. The line is appended to an
    ``O_APPEND`` fd (each ``write(2)`` is atomically positioned at EOF) opened
    ``O_NOFOLLOW`` (never append through a planted symlink) and ``fchmod`` 0o600
    (tighten a pre-existing world-readable file past the umask), and ``os.write`` is
    looped so a short write (near-full disk) can't truncate the line.
    """
    if not enabled:
        return
    try:
        data = (json.dumps(record, separators=(",", ":")) + "\n").encode("utf-8")
        os.makedirs(log_dir, exist_ok=True)
        path = os.path.join(log_dir, _RECORD_FILE)
        flags = os.O_WRONLY | os.O_CREAT | os.O_APPEND | getattr(os, "O_NOFOLLOW", 0)
        fd = os.open(path, flags, 0o600)
        try:
            try:
                os.fchmod(fd, 0o600)  # tighten an existing permissive file
            except OSError:
                pass
            written = 0
            while written < len(data):
                written += os.write(fd, data[written:])
        finally:
            os.close(fd)
    except (OSError, TypeError, ValueError) as exc:
        try:
            _get_logger().warning("could not write record to %s: %s",
                                  log_dir, exc.__class__.__name__)
        except Exception:
            pass
        return


def _emit_event(*, level: int, message: str, record: dict,
                log_dir: str, log_enabled: bool) -> None:
    """Emit the stderr log line (the contract) and the JSONL record (fail-soft
    add-on). Both are fully guarded so neither can raise into the launch path."""
    try:
        _get_logger().log(level, message)
    except Exception:
        pass
    try:
        write_record(record, log_dir=log_dir, enabled=log_enabled)
    except Exception:
        pass


# -- opt-in supervise (completion record) -----------------------------------


def _default_runner(argv: list[str], env: Mapping[str, str]):
    # Inherit parent stdio (claude `-p` / codex `exec` are non-interactive -> no
    # PTY needed). `start_new_session=True` isolates the child into its own process
    # group so a terminal-generated SIGINT/SIGTERM does NOT reach it directly; this
    # wrapper is then the sole signal source, which is the guard against a
    # double-hit (terminal group-delivery + our forward).
    return subprocess.Popen(argv, env=dict(env), start_new_session=True)


_FORWARD_SIGNALS = tuple(
    getattr(signal, name) for name in ("SIGINT", "SIGTERM", "SIGHUP", "SIGQUIT")
    if hasattr(signal, name)
)


def _signal_child(proc: Any, signum: int) -> None:
    """Forward ``signum`` to the child's whole process group, then the child alone.

    The child is spawned ``start_new_session=True`` (its own session/group), so it
    is shielded from terminal-delivered signals and we are its sole signal source;
    delivering to the *group* (``killpg``) also reaches grandchildren -- the actual
    ``claude`` / ``codex`` CLI that upstream spawns -- so a Ctrl-C tears the whole
    tree down instead of orphaning a metered run. Falls back to the direct child if
    the group lookup fails (and is a no-op for an already-dead child).
    """
    pid = getattr(proc, "pid", None)
    if isinstance(pid, int) and pid > 0:
        try:
            os.killpg(os.getpgid(pid), signum)
            return
        except (ProcessLookupError, PermissionError, OSError):
            pass
    try:
        proc.send_signal(signum)
    except (ProcessLookupError, OSError):
        pass


def _supervise(argv: list[str], env: Mapping[str, str], *,
               run_fn: Callable[[list[str], Mapping[str, str]], object] | None = None) -> int:
    """Spawn the child, forward signals to its group, wait, return a signal-aware code.

    Opt-in path. The child inherits stdio; SIGINT/SIGTERM/SIGHUP/SIGQUIT are
    forwarded to its process group while we wait. Returns the child's exit code, or
    ``128+signo`` if it was killed by a signal. ``run_fn`` is injectable for
    hermetic tests. A spawn-time ``OSError`` propagates (handlers restored first) so
    ``main`` can record ``exec_failed`` symmetrically with the exec path.

    Handlers are installed *before* the spawn so a signal landing in the
    spawn-to-install window can't take the default disposition (kill the parent,
    orphan the child); such a signal is buffered and re-delivered once the child exists.
    """
    pending: list[int] = []
    proc_holder: list[Any] = [None]

    def _forward(signum, *_):
        proc = proc_holder[0]
        if proc is None:
            pending.append(signum)  # arrived during the spawn window; flush below
            return
        _signal_child(proc, signum)

    installed: list[tuple[int, Any]] = []
    for sig in _FORWARD_SIGNALS:
        try:
            installed.append((sig, signal.signal(sig, _forward)))
        except (ValueError, OSError, RuntimeError):
            pass  # not in main thread / unsupported signal -> best-effort
    proc: Any = None
    try:
        proc = (run_fn or _default_runner)(argv, env)
        proc_holder[0] = proc
        for signum in pending:  # re-deliver any signal caught mid-spawn
            _signal_child(proc, signum)
        proc.wait()
    finally:
        for sig, prev in installed:
            try:
                signal.signal(sig, prev)
            except (ValueError, OSError, RuntimeError):
                pass
    rc = proc.returncode
    if rc is None:
        return 0
    return 128 + (-rc) if rc < 0 else rc


# -- env-derived config (the env-var surface) -------------------------------


def _truthy(value: str | None) -> bool:
    return (value or "").strip().lower() in ("1", "true", "yes", "on")


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _default_log_dir() -> str:
    override = os.environ.get(_LOG_DIR_ENV)
    if override:
        return override
    # cwd-relative, matching the repo's .agent-workspace/<tool>/ convention
    # (gitignored at root) and symmetric with upstream's cwd-relative outputs/.
    # Fail-soft on a deleted cwd: fall back to $HOME (or ".") so resolving the log
    # dir can never raise into the launch path.
    base = _safe_cwd() or os.environ.get("HOME") or "."
    return os.path.join(base, ".agent-workspace", "skillopt-oauth")


def _log_enabled() -> bool:
    return (os.environ.get(_LOG_ENV) or "").strip().lower() not in ("0", "off", "false", "no")


def _probe_name(probe: Callable[[str], str] | None) -> str:
    fn = probe or default_oauth_probe
    return getattr(fn, "__name__", repr(fn))


def _safe_exc(exc: BaseException) -> str:
    """A secret-free summary of a launch ``OSError``: exception class + ``errno``
    only. The raw ``str(exc)`` / ``filename`` of an ``os.execvpe`` / ``Popen``
    failure embeds the PATH-resolved absolute path of the binary, which can carry an
    env-derived value -- so it is never recorded or logged."""
    return f"{exc.__class__.__name__}(errno={getattr(exc, 'errno', None)})"


def _print_dry_run(provider: str, argv: list[str],
                   src_env: Mapping[str, str], child_env: Mapping[str, str]) -> None:
    """Print the would-be launch to stdout: redacted argv + env delta (names only).

    Uses the same secret-safe redaction and env-name sanitization as the record,
    and ``shlex.join`` so an arg with spaces/newlines can't forge log-looking output.
    """
    removed = sorted({_sanitize_env_name(n) for n in (set(src_env) - set(child_env))})
    added = sorted({_sanitize_env_name(n) for n in (set(child_env) - set(src_env))})
    try:
        print("skillopt-oauth dry-run (no exec):")
        print(f"  provider:    {provider}")
        print(f"  would exec:  {UPSTREAM_TRAIN} {shlex.join(_redact_argv_safe(argv))}")
        print(f"  env removed: {removed}")
        print(f"  env added:   {added}")
    except OSError:
        # a closed/broken stdout (e.g. `... | head -c0`) must not raise into the
        # launch path -- the dry-run print is best-effort like every other emit.
        pass


# -- main: preflight -> scrub -> route -> record -> exec/supervise -----------


def main(argv: list[str] | None = None, *,
         probe: Callable[[str], str] | None = None,
         exec_fn: Callable[[str, list[str], Mapping[str, str]], object] = os.execvpe,
         now: Callable[[], str] | None = None,
         run_id_fn: Callable[[], str] | None = None,
         log_dir: str | None = None,
         supervise: bool | None = None,
         ) -> int:
    """Preflight, scrub, route, record the decision, then ``exec`` (or supervise)
    upstream ``skillopt-train``.

    All ``argv`` are passed through verbatim to upstream. Each decision point
    writes one structured record (and a matching stderr log line) keyed by a
    generated ``run_id`` that is also exported into the child env for output
    correlation. On success ``exec`` replaces the process and this never returns;
    a preflight failure returns 2, an exec failure 127. Records/logging are
    fail-soft and can never raise into the launch path. The keyword seams (``probe``,
    ``exec_fn``, ``now``, ``run_id_fn``, ``log_dir``, ``supervise``) are injectable
    for tests with safe production defaults.
    """
    args = list(sys.argv[1:] if argv is None else argv)

    clock = now or _utc_now_iso
    make_run_id = run_id_fn or (lambda: uuid.uuid4().hex)
    ldir = log_dir if log_dir is not None else _default_log_dir()
    log_enabled = _log_enabled()
    do_supervise = _truthy(os.environ.get(_SUPERVISE_ENV)) if supervise is None else supervise
    dry_run = _truthy(os.environ.get(_DRY_RUN_ENV))

    provider = resolve_target(args)
    optimizer_backend, optimizer_injected = _resolve_optimizer_backend(args, provider, os.environ)
    optimizer_provider = _provider_of(optimizer_backend) if optimizer_backend else None
    preflight_providers = [provider]
    if optimizer_provider and optimizer_provider != provider:
        preflight_providers.append(optimizer_provider)
    run_id = make_run_id()
    ts = clock()
    probe_name = _probe_name(probe)
    resolved_path = shutil.which(UPSTREAM_TRAIN)
    src_env = dict(os.environ)

    # 1) Preflight EVERY provider the run will touch (target + a hybrid optimizer
    #    leg on a different CLI), failing closed on the first that can't prove OAuth
    #    so the subscription guarantee covers the optimizer leg too. For codex/codex
    #    and claude/claude this is a single provider -- identical to before.
    verdicts: dict[str, str] = {}
    for prov in preflight_providers:
        try:
            verdicts[prov] = preflight(prov, probe=probe)
        except OAuthPreflightError as exc:
            record = build_record(
                event="refused", run_id=run_id, ts=ts, provider=prov,
                verdict=getattr(exc, "verdict", None), probe_name=probe_name,
                src_env=src_env, child_env=src_env,  # no scrub happened
                routing={"TARGET_BACKEND": None, "OPTIMIZER_BACKEND": None,
                         "exec_path_var": _EXEC_PATH_VAR.get(prov), "exec_path": None,
                         "target_provider": provider,
                         "optimizer_backend_arg": optimizer_backend,
                         "optimizer_injected": optimizer_injected,
                         "optimizer_provider": optimizer_provider},
                argv=args, resolved_path=resolved_path,
                out_root_arg=extract_out_root(args), out_root_injected=False,
                preflight_providers=preflight_providers,
                preflight_verdicts={**verdicts, prov: getattr(exc, "verdict", None)},
            )
            _emit_event(level=logging.ERROR, message=str(exc), record=record,
                        log_dir=ldir, log_enabled=log_enabled)
            return 2
    verdict = verdicts[provider]  # target verdict drives the back-compat singular field

    # 2) Scrub + route. The child env is what exec/supervise will inherit.
    child_env = scrub_env(src_env)
    configure_backends(child_env, provider)
    child_env[_RUN_ID_ENV] = run_id  # free, non-intrusive output-correlation hook

    routing = {
        "TARGET_BACKEND": child_env["TARGET_BACKEND"],
        "OPTIMIZER_BACKEND": child_env["OPTIMIZER_BACKEND"],
        "exec_path_var": _EXEC_PATH_VAR[provider],
        "exec_path": child_env[_EXEC_PATH_VAR[provider]],
        "optimizer_backend_arg": optimizer_backend,  # what the optimizer leg will run (or None)
        "optimizer_injected": optimizer_injected,    # did the wrapper add --optimizer_backend
        "optimizer_provider": optimizer_provider,    # claude / codex / None
    }

    # 3) Inject the optimizer backend so upstream actually selects it. Upstream's
    #    --backend macro defaults the optimizer to the metered openai_chat and reads
    #    no env for selection, so this argv flag is what keeps the optimizer leg on
    #    the subscription CLI. Mirror the --out_root injection; out_root stays last.
    if optimizer_injected and optimizer_backend:
        args = [*args, _OPTIMIZER_BACKEND_FLAG, optimizer_backend]

    # 4) Optional --out_root injection (off by default; it relocates upstream's
    #    documented default output dir, a passthrough intrusion).
    out_root_arg = extract_out_root(args)
    out_root_injected = False
    if out_root_arg is None and _truthy(os.environ.get(_INJECT_OUT_ROOT_ENV)):
        out_root_arg = os.path.join(ldir, "runs", run_id)
        args = [*args, "--out_root", out_root_arg]
        out_root_injected = True

    def _record(event: str, **extra) -> dict:
        return build_record(
            event=event, run_id=run_id, ts=ts, provider=provider,
            verdict=verdict, probe_name=probe_name,
            src_env=src_env, child_env=child_env, routing=routing,
            argv=args, resolved_path=resolved_path,
            out_root_arg=out_root_arg, out_root_injected=out_root_injected,
            preflight_providers=preflight_providers, preflight_verdicts=verdicts,
            **extra)

    # 5) Dry-run: record + print the would-be launch, never exec. Takes
    #    precedence over supervise.
    if dry_run:
        _emit_event(
            level=logging.INFO,
            message=(f"dry-run for {provider!r}; run_id={run_id}; would exec "
                     f"{UPSTREAM_TRAIN} (no launch)"),
            record=_record("dry_run"), log_dir=ldir, log_enabled=log_enabled)
        _print_dry_run(provider, args, src_env, child_env)
        return 0

    # 6) Handoff: record BEFORE exec/supervise so a kill still leaves a trace.
    _emit_event(
        level=logging.INFO,
        message=(f"OAuth preflight OK for {provider!r}; "
                 f"TARGET_BACKEND={routing['TARGET_BACKEND']}, "
                 f"{routing['exec_path_var']}={routing['exec_path']}; "
                 f"scrubbed metered-API keys; run_id={run_id}; "
                 f"{'supervise' if do_supervise else 'exec'} -> {UPSTREAM_TRAIN}"),
        record=_record("handoff"), log_dir=ldir, log_enabled=log_enabled)

    full_argv = [UPSTREAM_TRAIN, *args]

    def _emit_exec_failed(exc: OSError) -> int:
        # exec/spawn only returns control on failure (e.g. skillopt-train not on
        # PATH). Record a sanitized summary -- never str(exc), which embeds a
        # PATH-resolved absolute path.
        _emit_event(
            level=logging.ERROR,
            message=(f"failed to launch {UPSTREAM_TRAIN!r}: {_safe_exc(exc)}; is "
                     f"upstream `skillopt` installed and on PATH?"),
            record=_record("exec_failed", error=_safe_exc(exc)),
            log_dir=ldir, log_enabled=log_enabled)
        return 127

    # 7a) Supervise (opt-in): run to completion and record exit code + duration.
    #     A spawn-time OSError is surfaced the same way as the exec path (symmetric
    #     exec_failed record + rc 127) instead of crashing with a traceback.
    if do_supervise:
        start = time.monotonic()
        try:
            rc = _supervise(full_argv, child_env)
        except OSError as exc:
            return _emit_exec_failed(exc)
        duration_s = round(time.monotonic() - start, 6)
        _emit_event(
            level=logging.INFO,
            message=(f"completed run_id={run_id}; exit_code={rc}; "
                     f"duration_s={duration_s}"),
            record=_record("completed", exit_code=rc, duration_s=duration_s,
                           end_ts=clock()),
            log_dir=ldir, log_enabled=log_enabled)
        return rc

    # 7b) Default: exec upstream (replaces this process; never returns on success).
    try:
        exec_fn(UPSTREAM_TRAIN, full_argv, child_env)
    except OSError as exc:
        return _emit_exec_failed(exc)
    # A real ``os.execvpe`` never returns here; an injected stub (tests) may.
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
