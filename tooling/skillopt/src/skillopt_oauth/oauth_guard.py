"""Make Microsoft SkillOpt safe to run on ``claude`` / ``codex`` subscription CLIs.

Upstream SkillOpt ships the ``claude_code_exec`` / ``codex_exec`` target backends,
but every exec site spawns the CLI with **no env scrub and no OAuth preflight**
(``skillopt/model/claude_backend.py``, ``codex_backend.py``, ``codex_harness.py``).
Because upstream's ``subprocess.run`` inherits the parent env, a stray
``ANTHROPIC_API_KEY`` / ``OPENAI_API_KEY`` silently flips the call onto the metered
provider API even with a valid subscription session -- the billing footgun.

This module is the surviving artifact of the retired SkillOpt fork: a thin launch
wrapper (console script ``skillopt-oauth``) that, before handing off to upstream's
``skillopt-train``, does the three things upstream omits, then ``exec``s upstream:

1. **Fail-closed OAuth preflight** -- confirm a subscription credential for the
   provider in use (claude: env ``CLAUDE_CODE_OAUTH_TOKEN`` / macOS Keychain
   ``Claude Code-credentials`` / ``~/.claude/.credentials.json``; codex:
   ``~/.codex/auth.json`` ``auth_mode == "chatgpt"``). Refuse to launch otherwise.
2. **Env scrub** -- strip every ``*_API_KEY`` / ``*_AUTH_TOKEN`` from the
   environment the child inherits, so a metered fallback is impossible by
   construction. Fixing *our* process env fixes upstream's footgun without
   patching upstream.
3. **Route to the CLI backends** -- point ``TARGET_BACKEND`` / ``OPTIMIZER_BACKEND``
   and ``CLAUDE_CODE_EXEC_PATH`` / ``CODEX_EXEC_PATH`` at the OAuth CLIs.

Then ``os.execvpe`` upstream's ``skillopt-train`` (console script
``scripts.train:main``), passing through all user args.

The probes and the scrub are lifted verbatim from the fork's tested executor; the
rest of the fork (its own loop, gate, reflect, checkpoint, scheduler, scorers, and
demo envs) is upstream's job now and was deleted.

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
    "build_record",
    "write_record",
    "main",
]

# Upstream's training entry point (``[project.scripts] skillopt-train = scripts.train:main``).
UPSTREAM_TRAIN = "skillopt-train"

PROVIDERS = ("claude", "codex")

# Provider -> upstream target (rollout) backend that spawns the OAuth CLI.
_TARGET_BACKEND = {"claude": "claude_code_exec", "codex": "codex_exec"}

# Provider -> the chat backend upstream pairs the optimizer/reflect path with
# (mirrors ``scripts/train.py`` setdefault logic). Upstream restricts the
# optimizer to chat backends, so reflect cannot itself route through an OAuth CLI;
# once the API keys are scrubbed this path fails *closed* (loudly) rather than
# silently billing -- which is the safety property we want.
_OPTIMIZER_BACKEND = {"claude": "claude_chat", "codex": "openai_chat"}

# Provider -> the env var upstream reads for the CLI binary path.
_EXEC_PATH_VAR = {"claude": "CLAUDE_CODE_EXEC_PATH", "codex": "CODEX_EXEC_PATH"}

# Provider -> default CLI binary name on PATH.
_DEFAULT_BIN = {"claude": "claude", "codex": "codex"}

# Env var that lets a user pin which provider to guard/route when it cannot be
# inferred from the passthrough args.
_TARGET_ENV = "SKILLOPT_OAUTH_TARGET"

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
SCHEMA_VERSION = 1


class OAuthPreflightError(RuntimeError):
    """Raised when the CLI would NOT resolve to a subscription OAuth credential.

    Failing closed here is the guard against silently running on a metered API: if
    the probe cannot confirm OAuth (or would resolve to an API key), nothing is
    launched. ``verdict`` carries the probe result that triggered the refusal so
    ``main`` can record it without re-probing the keychain (which risks a second
    ACL prompt).
    """

    verdict: str | None = None


# -- OAuth probes (lifted verbatim from the fork's executor) ----------------


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
    """
    src = os.environ if environ is None else environ
    inferred = _target_from_args(argv)
    if inferred:
        return inferred
    env_target = (src.get(_TARGET_ENV) or "").strip().lower()
    if env_target in PROVIDERS:
        return env_target
    return "claude"


def _target_from_args(argv: list[str]) -> str | None:
    flags = {"--backend", "--target_backend"}
    values: list[str] = []
    for i, tok in enumerate(argv):
        if "=" in tok:
            flag, _, val = tok.partition("=")
            if flag in flags:
                values.append(val)
        elif tok in flags and i + 1 < len(argv):
            values.append(argv[i + 1])
    for val in values:
        low = val.strip().lower()
        if "codex" in low:
            return "codex"
        if "claude" in low:
            return "claude"
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
    return flag.lstrip("-").lower()


def _is_secret_flag(norm: str) -> bool:
    """Decide whether a normalized flag name names a secret value (over-redact).

    Order matters and is security-biased -- when uncertain, redact:
    1. exact known secret flag; 2. prefix of any known secret flag (catches
    ``allow_abbrev`` abbreviations like ``azure_api_k``); 3. numeric denylist
    (``*_max_tokens`` / ``*_completion_tokens`` / ``*_thinking_tokens``) is
    explicitly NOT secret -- it guards the heuristic below from false positives;
    4. forward-compat heuristic for flags upstream may add later.
    """
    if not norm:
        return False
    if norm in _KNOWN_SECRET_NAMES:
        return True
    if any(known.startswith(norm) for known in _KNOWN_SECRET_NAMES):
        return True
    if (norm.endswith("_max_tokens") or norm.endswith("_completion_tokens")
            or norm.endswith("_thinking_tokens")):
        return False
    if norm.endswith("_api_key"):
        return True
    if "secret" in norm or "password" in norm or "credential" in norm:
        return True
    if (norm.endswith("_auth_token") or norm.endswith("access_token")
            or norm.endswith("oauth_token")):
        return True
    return False


def redact_argv(argv: list[str]) -> list[str]:
    """Return a copy of ``argv`` with every secret-flag *value* replaced.

    Handles both ``--flag value`` and ``--flag=value``. Operates on a copy: the
    live ``argv`` handed to exec/supervise is verbatim and untouched. Biased to
    over-redact -- it only ever affects the record copy, never the live launch.
    """
    out = list(argv)
    n = len(out)
    i = 0
    while i < n:
        tok = out[i]
        if isinstance(tok, str) and tok.startswith("--") and "=" in tok:
            flag = tok.partition("=")[0]
            if _is_secret_flag(_normalize_flag(flag)):
                out[i] = f"{flag}={_REDACTED}"
        elif isinstance(tok, str) and tok.startswith("--"):
            if _is_secret_flag(_normalize_flag(tok)) and i + 1 < n:
                out[i + 1] = _REDACTED
                i += 1  # skip the value we just neutralized
        i += 1
    return out


def extract_out_root(argv: list[str]) -> str | None:
    """Return the ``--out_root`` value from ``argv`` (either form), else ``None``."""
    for i, tok in enumerate(argv):
        if tok == "--out_root" and i + 1 < len(argv):
            return argv[i + 1]
        if tok.startswith("--out_root="):
            return tok.partition("=")[2]
    return None


# -- record construction (pure, no I/O) -------------------------------------


def _wrapper_version() -> str:
    # Lazy import keeps __init__ the single source of truth without a circular
    # import at module load (oauth_guard is imported *by* __init__).
    try:
        from skillopt_oauth import __version__
        return __version__
    except Exception:
        return "unknown"


def build_record(*, event: str, run_id: str, ts: str, provider: str,
                 verdict: str | None, probe_name: str,
                 src_env: Mapping[str, str], child_env: Mapping[str, str],
                 routing: dict, argv: list[str], resolved_path: str | None,
                 out_root_arg: str | None, out_root_injected: bool,
                 **extra) -> dict:
    """Build one record dict for ``event``. All fields are non-secret by
    construction: only env *names* (never values), a redacted argv copy, and
    routing/preflight metadata. Deterministic given ``ts`` + ``run_id``.
    """
    try:
        argv_redacted = redact_argv(argv)
    except Exception:
        argv_redacted = list(_REDACTION_FAILED)
    scrubbed_keys = sorted(set(src_env) - set(child_env))
    record = {
        "schema_version": SCHEMA_VERSION,
        "run_id": run_id,
        "ts": ts,
        "event": event,
        "wrapper_version": _wrapper_version(),
        "provider": provider,
        "preflight": {"verdict": verdict, "probe_name": probe_name},
        "scrubbed_keys": scrubbed_keys,
        "routing": routing,
        "upstream": {
            "entry": UPSTREAM_TRAIN,
            "resolved_path": resolved_path,
            "out_root_arg": out_root_arg,
            "out_root_injected": out_root_injected,
        },
        "argv_redacted": argv_redacted,
        "cwd": os.getcwd(),
        "pid": os.getpid(),
    }
    record.update(extra)
    return record


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

    Fail-soft: when ``enabled`` is False this is a no-op; on any ``OSError`` it
    warns once to stderr and returns so the launch proceeds. The line is written
    with a single ``os.write`` to an ``O_APPEND`` fd (POSIX append atomicity) at
    mode ``0o600``.
    """
    if not enabled:
        return
    try:
        line = json.dumps(record, separators=(",", ":")) + "\n"
        os.makedirs(log_dir, exist_ok=True)
        path = os.path.join(log_dir, _RECORD_FILE)
        fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o600)
        try:
            os.write(fd, line.encode("utf-8"))
        finally:
            os.close(fd)
    except OSError as exc:
        try:
            _get_logger().warning("could not write record to %s: %s", log_dir, exc)
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


def _default_runner(prog: str, argv: list[str], env: Mapping[str, str]):
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


def _supervise(prog: str, argv: list[str], env: Mapping[str, str], *,
               run_fn: Callable[[str, list[str], Mapping[str, str]], object] | None = None) -> int:
    """Spawn the child, forward signals to it, wait, return a signal-aware code.

    Opt-in path. The child inherits stdio; SIGINT/SIGTERM/SIGHUP/SIGQUIT are
    forwarded to it while we wait. Returns the child's exit code, or ``128+signo``
    if it was killed by a signal. ``run_fn`` is injectable for hermetic tests.
    """
    proc: Any = (run_fn or _default_runner)(prog, argv, env)

    def _forward(signum, _frame):
        try:
            proc.send_signal(signum)
        except (ProcessLookupError, OSError):
            pass

    installed: list[tuple[int, Any]] = []
    for sig in _FORWARD_SIGNALS:
        try:
            installed.append((sig, signal.signal(sig, _forward)))
        except (ValueError, OSError, RuntimeError):
            pass  # not in main thread / unsupported signal -> best-effort
    try:
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
    return os.path.join(os.getcwd(), ".agent-workspace", "skillopt-oauth")


def _log_enabled() -> bool:
    return (os.environ.get(_LOG_ENV) or "").strip().lower() not in ("0", "off", "false", "no")


def _probe_name(probe: Callable[[str], str] | None) -> str:
    fn = probe or default_oauth_probe
    return getattr(fn, "__name__", repr(fn))


def _print_dry_run(provider: str, argv: list[str],
                   src_env: Mapping[str, str], child_env: Mapping[str, str]) -> None:
    """Print the would-be launch to stdout: redacted argv + env delta (names only)."""
    removed = sorted(set(src_env) - set(child_env))
    added = sorted(set(child_env) - set(src_env))
    print("skillopt-oauth dry-run (no exec):")
    print(f"  provider:    {provider}")
    print(f"  would exec:  {UPSTREAM_TRAIN} {' '.join(redact_argv(argv))}")
    print(f"  env removed: {removed}")
    print(f"  env added:   {added}")


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
    run_id = make_run_id()
    ts = clock()
    probe_name = _probe_name(probe)
    resolved_path = shutil.which(UPSTREAM_TRAIN)
    src_env = dict(os.environ)

    # 1) Preflight (fail closed). On refusal, record the verdict and return 2.
    try:
        verdict = preflight(provider, probe=probe)
    except OAuthPreflightError as exc:
        record = build_record(
            event="refused", run_id=run_id, ts=ts, provider=provider,
            verdict=getattr(exc, "verdict", None), probe_name=probe_name,
            src_env=src_env, child_env=src_env,  # no scrub happened
            routing={"TARGET_BACKEND": None, "OPTIMIZER_BACKEND": None,
                     "exec_path_var": _EXEC_PATH_VAR[provider], "exec_path": None},
            argv=args, resolved_path=resolved_path,
            out_root_arg=extract_out_root(args), out_root_injected=False,
        )
        _emit_event(level=logging.ERROR, message=str(exc), record=record,
                    log_dir=ldir, log_enabled=log_enabled)
        return 2

    # 2) Scrub + route. The child env is what exec/supervise will inherit.
    child_env = scrub_env(src_env)
    configure_backends(child_env, provider)
    child_env[_RUN_ID_ENV] = run_id  # free, non-intrusive output-correlation hook

    routing = {
        "TARGET_BACKEND": child_env["TARGET_BACKEND"],
        "OPTIMIZER_BACKEND": child_env["OPTIMIZER_BACKEND"],
        "exec_path_var": _EXEC_PATH_VAR[provider],
        "exec_path": child_env[_EXEC_PATH_VAR[provider]],
    }

    # 3) Optional --out_root injection (off by default; it relocates upstream's
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
            **extra)

    # 4) Dry-run: record + print the would-be launch, never exec. Takes
    #    precedence over supervise.
    if dry_run:
        _emit_event(
            level=logging.INFO,
            message=(f"dry-run for {provider!r}; run_id={run_id}; would exec "
                     f"{UPSTREAM_TRAIN} (no launch)"),
            record=_record("dry_run"), log_dir=ldir, log_enabled=log_enabled)
        _print_dry_run(provider, args, src_env, child_env)
        return 0

    # 5) Handoff: record BEFORE exec/supervise so a kill still leaves a trace.
    _emit_event(
        level=logging.INFO,
        message=(f"OAuth preflight OK for {provider!r}; "
                 f"TARGET_BACKEND={routing['TARGET_BACKEND']}, "
                 f"{routing['exec_path_var']}={routing['exec_path']}; "
                 f"scrubbed metered-API keys; run_id={run_id}; "
                 f"{'supervise' if do_supervise else 'exec'} -> {UPSTREAM_TRAIN}"),
        record=_record("handoff"), log_dir=ldir, log_enabled=log_enabled)

    full_argv = [UPSTREAM_TRAIN, *args]

    # 6a) Supervise (opt-in): run to completion and record exit code + duration.
    if do_supervise:
        start = time.monotonic()
        rc = _supervise(UPSTREAM_TRAIN, full_argv, child_env)
        duration_s = round(time.monotonic() - start, 6)
        _emit_event(
            level=logging.INFO,
            message=(f"completed run_id={run_id}; exit_code={rc}; "
                     f"duration_s={duration_s}"),
            record=_record("completed", exit_code=rc, duration_s=duration_s,
                           end_ts=clock()),
            log_dir=ldir, log_enabled=log_enabled)
        return rc

    # 6b) Default: exec upstream (replaces this process; never returns on success).
    try:
        exec_fn(UPSTREAM_TRAIN, full_argv, child_env)
    except OSError as exc:
        # exec only returns control on failure (e.g. skillopt-train not on PATH).
        _emit_event(
            level=logging.ERROR,
            message=(f"failed to exec {UPSTREAM_TRAIN!r}: {exc}; is upstream "
                     f"`skillopt` installed and on PATH?"),
            record=_record("exec_failed", error=str(exc)),
            log_dir=ldir, log_enabled=log_enabled)
        return 127
    # A real ``os.execvpe`` never returns here; an injected stub (tests) may.
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
