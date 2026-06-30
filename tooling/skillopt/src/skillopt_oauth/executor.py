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
import platform
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
    # Targeted signatures of an actual metered-API slip / billing / usage-limit
    # condition. Deliberately narrower than a bare "api key" / "credit" /
    # "billing" match: a model's benign prose (or a JSON usage field like
    # "modelUsage") must not false-positive and abort an otherwise-clean run.
    # Still catches the real warnings a metered fallback or a hit limit emits
    # (including the hermetic stub's auth_warning text).
    r"api[_ -]?key\s+(?:detected|present|set|found|required|invalid|missing)"
    r"|billed?\s+to\s+(?:your\s+)?(?:api|account|credits?)"
    r"|api\s+credits?"
    r"|credit\s+balance"
    r"|insufficient\s+(?:credit|quota|funds|balance)"
    r"|rate[_ -]?limit"
    r"|usage\s+limit"
    r"|too\s+many\s+requests"
    r"|quota\s+(?:exceeded|reached)"
    r"|billing\s+(?:error|issue|required|problem)",
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
    # On macOS there is no .credentials.json: the subscription credential lives
    # in the login Keychain. Consult it before falling back to "api_key"/"none".
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
    item is the subscription signal. We intentionally do an existence/attribute
    lookup only -- NOT ``-g``/``-w`` -- because decrypting the secret can trigger
    a Keychain ACL prompt that would hang a headless run, whereas listing the
    item does not. Best-effort and fail-safe: any error (non-macOS, missing
    ``security``, locked keychain) returns ``None`` so the caller falls through
    rather than crashing the preflight.
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


class OAuthCLIExecutor:
    """Shell out to the OAuthed ``claude`` / ``codex`` CLIs. No API path exists."""

    def __init__(self, *, claude_bin="claude", codex_bin="codex",
                 model_claude=None, model_codex=None, reasoning_effort="high",
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
                workdir: str | None = None, timeout: float = 600.0,
                allow_writes: bool = False) -> "CliResult":
        """Run one non-interactive CLI call and return its :class:`CliResult`.

        ``provider`` is ``"claude"`` or ``"codex"``. The candidate skill, if
        given, is injected as a read-only workspace file before the call.
        ``allow_writes`` widens the CLI's sandbox so the model may create files
        in ``workdir`` (rollouts need this; reflect/judge calls do not).
        """
        if provider not in ("claude", "codex"):
            raise ValueError(f"unknown provider {provider!r}; expected 'claude' or 'codex'")

        self._preflight(provider)
        requested = self.model_claude if provider == "claude" else self.model_codex

        created_tmp: str | None = None
        if workdir is None and skill_path is not None:
            workdir = created_tmp = tempfile.mkdtemp(prefix="skillopt-work-")
        if skill_path is not None and workdir is not None:
            self._inject_skill(workdir, skill_path)

        cmd, stdin_data = self._build_command(provider, prompt, requested, allow_writes)

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
            # Only ever remove the temp dir we allocated -- never a caller-supplied workdir.
            if created_tmp is not None:
                shutil.rmtree(created_tmp, ignore_errors=True)

        reported = self._extract_model(provider, stdout)
        model_asserted = self._assert_model(requested, reported) if exit_code == 0 else None
        auth_billing_warning = bool(_AUTH_BILLING_RE.search(f"{stdout}\n{stderr}"))
        return CliResult(stdout, exit_code, duration, model_asserted, stderr,
                         auth_billing_warning)

    # -- internals --------------------------------------------------------

    def _build_command(self, provider, prompt, requested, allow_writes=False):
        """Return ``(argv, stdin_data)`` for the given provider.

        ``allow_writes`` widens the sandbox so the model may create files in its
        working directory: claude gains ``--permission-mode acceptEdits``; codex
        runs under ``--sandbox workspace-write`` instead of ``read-only``.
        """
        if provider == "claude":
            # Headless subscription path is `claude -p`. NEVER `--bare`: that flag
            # skips OAuth/keychain and *requires* an API key (metered), and is
            # slated to become the `-p` default in a future release -- so pin the
            # CLI version (config) and assert `--bare` is absent from the argv.
            # `--output-format json` makes stdout a single machine-readable result
            # object (so the model that actually ran is recoverable from
            # `modelUsage`) instead of free-form prose. `--permission-mode
            # acceptEdits` is the minimal grant that lets a non-interactive `-p`
            # run create/edit files inside its working directory.
            cmd = [self.claude_bin, "-p", prompt, "--output-format", "json"]
            if allow_writes:
                cmd += ["--permission-mode", "acceptEdits"]
            if requested:
                cmd += ["--model", requested]
            self._guard_no_bare(cmd)
            return cmd, None
        # codex exec: read-only by default; widen to workspace-write only when the
        # call must produce files. `--skip-git-repo-check` keeps `exec` from
        # refusing to run in a non-repo workspace. reasoning effort + model via -c
        # flags (effort omitted when unset); prompt on stdin.
        sandbox = "workspace-write" if allow_writes else "read-only"
        cmd = [self.codex_bin, "exec", "-s", sandbox, "--skip-git-repo-check"]
        if self.reasoning_effort:
            cmd += ["-c", f"model_reasoning_effort={self.reasoning_effort}"]
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
            # Suffix match is intentionally uppercase: the claude/codex CLIs only
            # read the canonical UPPER_CASE_API_KEY names, so a lowercase variant
            # surviving here is inert (it would never flip billing).
            env = {k: v for k, v in os.environ.items()
                   if not (k.endswith("_API_KEY") or k.endswith("_AUTH_TOKEN"))}
            for name in ("ANTHROPIC_API_KEY", "ANTHROPIC_AUTH_TOKEN",
                         "OPENAI_API_KEY", "CODEX_API_KEY"):
                env.pop(name, None)  # belt-and-suspenders past the suffix filter
        else:
            # Opting out forfeits the metered-API safeguard: any *_API_KEY in the
            # parent will reach the child and silently bill metered API even with a
            # valid OAuth session. Leave the default (True) on for billing safety.
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
    def _extract_model(provider: str, stdout: str) -> str | None:
        """Recover the model the CLI actually ran on, if discoverable.

        Order: the explicit ``[[SKILLOPT_MODEL:...]]`` marker first (the hermetic
        stub and any CLI that echoes it), then provider-specific structured
        output. ``claude -p --output-format json`` returns an SDKResultMessage
        whose ``modelUsage`` is keyed by the real model id(s) -- there is no
        top-level ``model`` field -- so the first key is the model that ran.
        ``codex exec`` emits no machine-readable model field, so the ``-m`` pin is
        the contract and we report ``None``.
        """
        marked = OAuthCLIExecutor._extract_model_marker(stdout)
        if marked:
            return marked
        if provider == "claude":
            return OAuthCLIExecutor._model_from_claude_json(stdout)
        return None

    @staticmethod
    def _model_from_claude_json(stdout: str) -> str | None:
        text = (stdout or "").strip()
        if not text:
            return None
        try:
            obj = json.loads(text)
        except ValueError:
            try:
                obj = json.loads(extract_json_object(text))
            except (PatchParseError, ValueError):
                return None
        if not isinstance(obj, dict):
            return None
        usage = obj.get("modelUsage")
        if isinstance(usage, dict) and usage:
            return next(iter(usage))
        model = obj.get("model")
        return model if isinstance(model, str) and model else None

    @staticmethod
    def _model_family(name: str | None) -> str | None:
        """The coarse model family token in ``name`` (e.g. 'opus' in
        'claude-opus-4-8'), or ``None`` if no known family is present."""
        n = (name or "").lower()
        for fam in ("opus", "sonnet", "haiku", "fable", "gpt", "o3", "o4"):
            if fam in n:
                return fam
        return None

    @staticmethod
    def _assert_model(requested: str | None, reported: str | None) -> str | None:
        """Verify the pinned model against what the CLI reported.

        A real CLI reports a concrete id (``claude-opus-4-8``) while the pin may
        be an alias (``opus``); these are treated as a match (same family) and
        the concrete id is preferred. Only a cross-family report -- e.g. pinned
        ``opus`` but ``haiku`` ran (a silent downgrade) -- is a hard error.
        """
        if requested is None:
            return reported
        if reported is None or reported == requested:
            return reported if reported is not None else requested
        rf = OAuthCLIExecutor._model_family(requested)
        pf = OAuthCLIExecutor._model_family(reported)
        if rf and pf and rf == pf:
            return reported
        raise ModelAssertionError(
            f"model assertion failed: pinned {requested!r} but CLI reported {reported!r}"
        )


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
