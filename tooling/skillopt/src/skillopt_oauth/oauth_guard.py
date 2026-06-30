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
"""
from __future__ import annotations

import json
import os
import platform
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Callable, Mapping

__all__ = [
    "OAuthPreflightError",
    "PROVIDERS",
    "default_oauth_probe",
    "scrub_env",
    "resolve_target",
    "preflight",
    "configure_backends",
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


class OAuthPreflightError(RuntimeError):
    """Raised when the CLI would NOT resolve to a subscription OAuth credential.

    Failing closed here is the guard against silently running on a metered API: if
    the probe cannot confirm OAuth (or would resolve to an API key), nothing is
    launched.
    """


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
    Returns the verdict (``'oauth'``) on success.
    """
    if provider not in PROVIDERS:
        raise ValueError(f"unknown provider {provider!r}; expected one of {PROVIDERS}")
    verdict = (probe or default_oauth_probe)(provider)
    if verdict != "oauth":
        raise OAuthPreflightError(
            f"{provider} would resolve to a non-subscription credential "
            f"(probe -> {verdict!r}); refusing to launch so the run cannot be "
            f"silently billed to a metered API. Sign in with an OAuth / "
            f"subscription session (claude: `claude /login` or `claude setup-token`; "
            f"codex: ChatGPT auth)."
        )
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


def main(argv: list[str] | None = None, *,
         probe: Callable[[str], str] | None = None,
         exec_fn: Callable[[str, list[str], Mapping[str, str]], object] = os.execvpe,
         ) -> int:
    """Preflight, scrub, route, then ``exec`` upstream ``skillopt-train``.

    All ``argv`` are passed through verbatim to upstream. On success ``exec``
    replaces the process and this never returns; on a preflight or exec failure it
    returns a nonzero exit code. ``probe`` and ``exec_fn`` are injectable for tests.
    """
    args = list(sys.argv[1:] if argv is None else argv)
    provider = resolve_target(args)
    try:
        preflight(provider, probe=probe)
    except OAuthPreflightError as exc:
        print(f"skillopt-oauth: {exc}", file=sys.stderr)
        return 2

    env = scrub_env(os.environ)
    configure_backends(env, provider)

    print(
        f"skillopt-oauth: OAuth preflight OK for {provider!r}; "
        f"TARGET_BACKEND={env['TARGET_BACKEND']}, "
        f"{_EXEC_PATH_VAR[provider]}={env[_EXEC_PATH_VAR[provider]]}; "
        f"scrubbed metered-API keys; exec -> {UPSTREAM_TRAIN}",
        file=sys.stderr,
    )
    try:
        exec_fn(UPSTREAM_TRAIN, [UPSTREAM_TRAIN, *args], env)
    except OSError as exc:
        # exec only returns control on failure (e.g. skillopt-train not on PATH).
        print(
            f"skillopt-oauth: failed to exec {UPSTREAM_TRAIN!r}: {exc}; is upstream "
            f"`skillopt` installed and on PATH?",
            file=sys.stderr,
        )
        return 127
    # A real ``os.execvpe`` never returns here; an injected stub (tests) may.
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
