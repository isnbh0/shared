"""The single LLM chokepoint for SkillOpt-OAuth.

Every rollout, reflect, and judge call in the fork is dispatched through
``OAuthCLIExecutor.run_cli``. It shells out to the OAuthed ``claude`` / ``codex``
CLIs only -- there is deliberately no API or chat code path anywhere in the
package. Before spawning, it scrubs every ``*_API_KEY`` / ``*_AUTH_TOKEN`` out of
the child env and runs a fail-closed OAuth preflight (a subscription credential
is required), never passes ``--bare``, pins and verifies the model id on every
call, surfaces auth/billing warnings, and exposes helpers that recover a strict
edit-op JSON object from free-form CLI stdout.
"""
from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import tempfile
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

__all__ = [
    "CliResult",
    "OAuthCLIExecutor",
    "ExecutorError",
    "ApiKeyForbiddenError",
    "OAuthPreflightError",
    "ModelAssertionError",
    "PatchParseError",
    "PatchSchemaError",
    "default_oauth_probe",
    "extract_json_object",
    "parse_patch_json",
    "validate_patch",
]

# A CLI (and the hermetic stub) echoes the model it actually ran on with this
# marker so the executor can verify pinning offline. Absence is non-fatal
# (real CLIs may not echo); a *contradiction* is a hard error.
_MODEL_MARKER_RE = re.compile(r"\[\[SKILLOPT_MODEL:([^\]]*)\]\]")

# Auth / billing / usage-limit signals scanned out of CLI stdout+stderr. A hit
# means the call may have slipped onto a metered path or hit a limit, so it is
# surfaced as ``CliResult.auth_billing_warning`` and treated as a failure even on
# a clean (exit 0) run.
_AUTH_BILLING_RE = re.compile(
    r"api[ -]?key|rate limit|usage limit|quota|bill(?:ed|ing)|credit",
    re.IGNORECASE,
)

# Edit-op contract for reflect/optimizer patches (spine sections 5 and 7).
_ALLOWED_OPS = {"add", "delete", "replace"}
_REQUIRED_FIELDS: dict[str, tuple[str, ...]] = {
    "add": ("content",),
    "delete": ("target",),
    "replace": ("target", "content"),
}

# Conventional exit code used when a call is killed for exceeding its timeout.
TIMEOUT_EXIT_CODE = 124


class ExecutorError(RuntimeError):
    """Base class for executor failures."""


class ApiKeyForbiddenError(ExecutorError):
    """Retained for back-compat. The blunt parent-env scan that once raised this
    is superseded by child-env scrubbing and the OAuth preflight."""


class OAuthPreflightError(ExecutorError):
    """Raised when the CLI would NOT resolve to a subscription OAuth credential.

    Failing closed here is the guard against silently running on a metered API:
    if the probe cannot confirm OAuth (or would resolve to an API key), no call
    is made.
    """


class ModelAssertionError(ExecutorError):
    """Raised when the CLI reports a model that contradicts the pinned one."""


class PatchParseError(ExecutorError):
    """Raised when no parseable JSON object can be recovered from stdout."""


class PatchSchemaError(ExecutorError):
    """Raised when a parsed object violates the add/delete/replace schema."""


@dataclass
class CliResult:
    """Outcome of one CLI invocation.

    The spine pins the first four fields and their order. ``stderr`` and
    ``auth_billing_warning`` are appended with defaults so the documented
    ``CliResult(stdout, exit_code, duration, model_asserted)`` construction still
    works while the Phase 3 scheduler can inspect stderr and treat
    ``auth_billing_warning`` as a failure signal (auth/billing/usage-limit text
    was detected in stdout+stderr).
    """

    stdout: str
    exit_code: int
    duration: float
    model_asserted: str | None
    stderr: str = ""
    auth_billing_warning: bool = False


def default_oauth_probe(provider: str) -> str:
    """Best-effort resolution of the credential the CLI would actually use.

    Returns ``'oauth'`` (a subscription credential), ``'api_key'`` (a metered
    API key would win), or ``'none'`` (nothing resolvable). This is the default
    strategy; it is injectable via ``OAuthCLIExecutor(oauth_probe=...)`` so tests
    stay fully hermetic and never touch a real keychain / ``auth.json``.
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
    # A real probe would also query the macOS keychain here; absent a confirmed
    # subscription credential, refuse to assume OAuth.
    if os.environ.get("ANTHROPIC_API_KEY"):
        return "api_key"
    return "none"


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


class OAuthCLIExecutor:
    """Shell out to the OAuthed ``claude`` / ``codex`` CLIs. No API path exists."""

    def __init__(self, *, claude_bin="claude", codex_bin="codex",
                 model_claude=None, model_codex=None, reasoning_effort="xhigh",
                 forbid_api_keys=True, require_oauth=True, scrub_child_env=True,
                 oauth_probe=None):
        # The old construction-time parent-env API-key *scan* is intentionally
        # gone: scrubbing the child env (``scrub_child_env``) and the fail-closed
        # OAuth preflight (``require_oauth``) supersede it, and a stray key in the
        # parent is no longer fatal -- it simply never reaches the child.
        # ``forbid_api_keys`` is kept for back-compat with documented call sites
        # and no longer rejects on construction. New params are keyword-only with
        # safe defaults so the spine §10 signature still resolves.
        self.claude_bin = claude_bin
        self.codex_bin = codex_bin
        self.model_claude = model_claude
        self.model_codex = model_codex
        self.reasoning_effort = reasoning_effort
        self.forbid_api_keys = forbid_api_keys
        self.require_oauth = require_oauth
        self.scrub_child_env = scrub_child_env
        self._oauth_probe = oauth_probe
        self._oauth_verified: dict[str, bool] = {}  # memoized preflight verdicts

    # -- public -----------------------------------------------------------

    def run_cli(self, *, provider: str, prompt: str, skill_path: str | None = None,
                workdir: str | None = None, timeout: float = 600.0) -> "CliResult":
        """Run one non-interactive CLI call and return its :class:`CliResult`.

        ``provider`` is ``"claude"`` or ``"codex"``. The candidate skill, if
        given, is injected as a read-only workspace file before the call.
        """
        if provider not in ("claude", "codex"):
            raise ValueError(f"unknown provider {provider!r}; expected 'claude' or 'codex'")

        self._preflight(provider)
        requested = self.model_claude if provider == "claude" else self.model_codex

        created_tmp = False
        if workdir is None and skill_path is not None:
            workdir = tempfile.mkdtemp(prefix="skillopt-work-")
            created_tmp = True
        if skill_path is not None and workdir is not None:
            self._inject_skill(workdir, skill_path)

        cmd, stdin_data = self._build_command(provider, prompt, requested)

        env = self._build_child_env(provider, requested)

        start = time.monotonic()
        try:
            if stdin_data is None:
                proc = subprocess.run(
                    cmd, capture_output=True, text=True, timeout=timeout,
                    cwd=workdir, env=env, stdin=subprocess.DEVNULL,
                )
            else:
                proc = subprocess.run(
                    cmd, input=stdin_data, capture_output=True, text=True,
                    timeout=timeout, cwd=workdir, env=env,
                )
            duration = time.monotonic() - start
            stdout, stderr, exit_code = proc.stdout or "", proc.stderr or "", proc.returncode
        except subprocess.TimeoutExpired as exc:
            duration = time.monotonic() - start
            stdout = exc.stdout if isinstance(exc.stdout, str) else ""
            stderr = exc.stderr if isinstance(exc.stderr, str) else ""
            exit_code = TIMEOUT_EXIT_CODE
        finally:
            if created_tmp:
                shutil.rmtree(workdir, ignore_errors=True)

        reported = self._extract_model_marker(stdout)
        model_asserted = self._assert_model(requested, reported) if exit_code == 0 else None
        auth_billing_warning = bool(_AUTH_BILLING_RE.search(f"{stdout}\n{stderr}"))
        return CliResult(stdout, exit_code, duration, model_asserted, stderr,
                         auth_billing_warning)

    # -- internals --------------------------------------------------------

    def _build_command(self, provider, prompt, requested):
        """Return ``(argv, stdin_data)`` for the given provider."""
        if provider == "claude":
            # Headless subscription path is `claude -p`. NEVER `--bare`: that flag
            # skips OAuth/keychain and *requires* an API key (metered), and is
            # slated to become the `-p` default in a future release -- so pin the
            # CLI version (config) and assert `--bare` is absent from the argv.
            cmd = [self.claude_bin, "-p", prompt]
            if requested:
                cmd += ["--model", requested]
            self._guard_no_bare(cmd)
            return cmd, None
        # codex: read-only sandbox, reasoning effort + model via -c flags, prompt on stdin
        cmd = [self.codex_bin, "exec", "-s", "read-only",
               "-c", f"model_reasoning_effort={self.reasoning_effort}"]
        if requested:
            cmd += ["-c", f"model={requested}"]
        cmd += ["-"]
        return cmd, prompt

    def _preflight(self, provider: str) -> None:
        """Fail closed unless the resolved credential is a subscription OAuth one.

        Runs once per provider (memoized) before the first call. The probe is
        injectable (``oauth_probe``) so tests are hermetic; the default best-effort
        probe inspects the real credential stores. A verdict other than ``'oauth'``
        -- including ``'api_key'`` and ``'none'`` -- raises rather than risk a
        silent metered call.
        """
        if not self.require_oauth or self._oauth_verified.get(provider):
            return
        probe = self._oauth_probe or default_oauth_probe
        verdict = probe(provider)
        if verdict != "oauth":
            raise OAuthPreflightError(
                f"{provider} would resolve to a non-subscription credential "
                f"(probe -> {verdict!r}); refusing to run so the call cannot be "
                f"silently billed to a metered API. Sign in with an OAuth / "
                f"subscription session (e.g. `claude setup-token` or ChatGPT auth)."
            )
        self._oauth_verified[provider] = True

    def _build_child_env(self, provider: str, requested: str | None) -> dict:
        """Construct the child env, stripping anything that could flip the call to a metered API.

        In ``-p`` / ``exec`` mode a stray ``*_API_KEY`` in the parent ALWAYS
        overrides the OAuth session, so scrub every name ending in ``_API_KEY`` /
        ``_AUTH_TOKEN`` (explicitly incl. ANTHROPIC_API_KEY, ANTHROPIC_AUTH_TOKEN,
        OPENAI_API_KEY, CODEX_API_KEY) from the *child* -- the parent is left
        untouched. ``CLAUDE_CODE_OAUTH_TOKEN`` is an OAuth token from
        ``claude setup-token`` (not an API key), so it survives the scrub for
        claude; it is never handed to codex.
        """
        if self.scrub_child_env:
            env = {k: v for k, v in os.environ.items()
                   if not (k.endswith("_API_KEY") or k.endswith("_AUTH_TOKEN"))}
            for name in ("ANTHROPIC_API_KEY", "ANTHROPIC_AUTH_TOKEN",
                         "OPENAI_API_KEY", "CODEX_API_KEY"):
                env.pop(name, None)  # belt-and-suspenders past the suffix filter
        else:
            env = dict(os.environ)
        if provider != "claude":
            env.pop("CLAUDE_CODE_OAUTH_TOKEN", None)
        env["SKILLOPT_MODEL"] = requested or ""
        return env

    @staticmethod
    def _guard_no_bare(cmd: list) -> None:
        """Refuse ``claude --bare``: it bypasses OAuth/keychain and forces a
        metered API key. The executor never constructs it; this guard fails loudly
        if a future change (or a flipped `-p` default) ever sneaks it into argv."""
        if "--bare" in cmd:
            raise ExecutorError(
                "refusing to run `claude --bare`: it bypasses OAuth and forces "
                "metered API billing"
            )

    def _inject_skill(self, workdir, skill_path) -> Path:
        """Write the candidate skill to ``<workdir>/.agents/skills/<target>/SKILL.md``."""
        src = Path(skill_path)
        target = src.resolve().parent.name or "candidate"
        dest_dir = Path(workdir) / ".agents" / "skills" / target
        dest_dir.mkdir(parents=True, exist_ok=True)
        dest = dest_dir / "SKILL.md"
        dest.write_text(src.read_text(encoding="utf-8"), encoding="utf-8")
        return dest

    @staticmethod
    def _extract_model_marker(stdout: str) -> str | None:
        match = _MODEL_MARKER_RE.search(stdout or "")
        if not match:
            return None
        value = match.group(1).strip()
        return value or None

    @staticmethod
    def _assert_model(requested: str | None, reported: str | None) -> str | None:
        """Verify the pinned model against what the CLI reported."""
        if requested is None:
            return reported
        if reported is not None and reported != requested:
            raise ModelAssertionError(
                f"model assertion failed: pinned {requested!r} but CLI reported {reported!r}"
            )
        return requested


# -- structured-output helpers --------------------------------------------


def extract_json_object(text: str) -> str:
    """Return the first balanced top-level ``{...}`` substring from ``text``.

    Tolerant of surrounding prose and Markdown code fences: it brace-matches
    while respecting string literals and escapes.
    """
    start = text.find("{")
    if start == -1:
        raise PatchParseError("no JSON object found in CLI output")
    depth = 0
    in_str = False
    esc = False
    for i in range(start, len(text)):
        ch = text[i]
        if in_str:
            if esc:
                esc = False
            elif ch == "\\":
                esc = True
            elif ch == '"':
                in_str = False
        else:
            if ch == '"':
                in_str = True
            elif ch == "{":
                depth += 1
            elif ch == "}":
                depth -= 1
                if depth == 0:
                    return text[start:i + 1]
    raise PatchParseError("unbalanced JSON object in CLI output")


def validate_patch(obj: object) -> dict:
    """Enforce the add/delete/replace edit-op schema; raise on violation."""
    if not isinstance(obj, dict):
        raise PatchSchemaError("patch must be a JSON object")
    edits = obj.get("edits")
    if not isinstance(edits, list):
        raise PatchSchemaError("patch must contain an 'edits' list")
    for i, edit in enumerate(edits):
        if not isinstance(edit, dict):
            raise PatchSchemaError(f"edit[{i}] must be an object")
        op = edit.get("op")
        if op not in _ALLOWED_OPS:
            raise PatchSchemaError(
                f"edit[{i}] has invalid op {op!r}; allowed: {sorted(_ALLOWED_OPS)}"
            )
        for field in _REQUIRED_FIELDS[op]:
            if not isinstance(edit.get(field), str):
                raise PatchSchemaError(
                    f"edit[{i}] op={op} requires string field {field!r}"
                )
    return obj


def parse_patch_json(stdout: str, *, repair: Callable[[str], str] | None = None,
                     validate: bool = True) -> dict:
    """Extract (and by default schema-validate) an edit-op object from stdout.

    ``repair`` is an optional one-shot hook: if the first attempt fails to parse
    or fails validation and a callable is supplied, it is invoked once with the
    raw stdout and its return value re-parsed. Higher-level retry orchestration
    (e.g. re-prompting the CLI) belongs to the caller; this provides only the
    parse + validate primitives and the single repair seam.
    """
    def _attempt(text: str) -> dict:
        raw = extract_json_object(text)
        try:
            obj = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise PatchParseError(f"invalid JSON in CLI output: {exc}") from exc
        if validate:
            validate_patch(obj)
        return obj

    try:
        return _attempt(stdout)
    except (PatchParseError, PatchSchemaError):
        if repair is None:
            raise
        return _attempt(repair(stdout))
