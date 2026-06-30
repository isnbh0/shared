"""Hermetic tests for the OAuth-safety launch wrapper.

Nothing here spawns a real ``claude`` / ``codex`` CLI, execs upstream
``skillopt-train``, or touches a real OAuth session: the probe is injected, the
Keychain ``platform`` / ``subprocess`` seams are monkeypatched, credential lookups
are pointed at ``tmp_path``, and ``exec_fn`` is a recording stub.
"""
from __future__ import annotations

import subprocess

import pytest

from skillopt_oauth import oauth_guard
from skillopt_oauth.oauth_guard import (
    OAuthPreflightError,
    configure_backends,
    main,
    preflight,
    resolve_target,
    scrub_env,
)


# -- env scrub -------------------------------------------------------------- #


def test_scrub_strips_api_keys_and_auth_tokens():
    src = {
        "ANTHROPIC_API_KEY": "sk-anthropic",
        "ANTHROPIC_AUTH_TOKEN": "tok-anthropic",
        "OPENAI_API_KEY": "sk-openai",
        "CODEX_API_KEY": "sk-codex",
        "SOMEVENDOR_API_KEY": "sk-generic",        # generic suffix match
        "SOMEVENDOR_AUTH_TOKEN": "tok-generic",    # generic suffix match
        "PATH": "/usr/bin",                        # unrelated -> kept
        "CLAUDE_CODE_OAUTH_TOKEN": "oauth-tok",    # subscription cred -> kept
    }
    out = scrub_env(src)
    for stripped in ("ANTHROPIC_API_KEY", "ANTHROPIC_AUTH_TOKEN", "OPENAI_API_KEY",
                     "CODEX_API_KEY", "SOMEVENDOR_API_KEY", "SOMEVENDOR_AUTH_TOKEN"):
        assert stripped not in out
    assert out["PATH"] == "/usr/bin"
    assert out["CLAUDE_CODE_OAUTH_TOKEN"] == "oauth-tok"


def test_scrub_does_not_mutate_source():
    src = {"ANTHROPIC_API_KEY": "sk-x", "PATH": "/usr/bin"}
    scrub_env(src)
    assert src["ANTHROPIC_API_KEY"] == "sk-x"  # original untouched


def test_scrub_reads_os_environ_by_default(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-should-be-stripped")
    monkeypatch.setenv("SKILLOPT_OAUTH_MARKER", "kept")
    out = scrub_env()
    assert "ANTHROPIC_API_KEY" not in out
    assert out["SKILLOPT_OAUTH_MARKER"] == "kept"


# -- OAuth preflight (fail closed) ----------------------------------------- #


def test_preflight_passes_with_oauth_probe():
    assert preflight("claude", probe=lambda provider: "oauth") == "oauth"


@pytest.mark.parametrize("verdict", ["api_key", "none"])
@pytest.mark.parametrize("provider", ["claude", "codex"])
def test_preflight_fails_closed_without_oauth(provider, verdict):
    with pytest.raises(OAuthPreflightError):
        preflight(provider, probe=lambda _p: verdict)


def test_preflight_rejects_unknown_provider():
    with pytest.raises(ValueError):
        preflight("bard", probe=lambda _p: "oauth")


# -- backend routing ------------------------------------------------------- #


def test_configure_backends_claude_sets_exec_backend_and_path():
    env: dict[str, str] = {}
    configure_backends(env, "claude", claude_bin="/opt/claude")
    assert env["TARGET_BACKEND"] == "claude_code_exec"
    assert env["OPTIMIZER_BACKEND"] == "claude_chat"
    assert env["CLAUDE_CODE_EXEC_PATH"] == "/opt/claude"


def test_configure_backends_codex_sets_exec_backend_and_path():
    env: dict[str, str] = {}
    configure_backends(env, "codex", codex_bin="/opt/codex")
    assert env["TARGET_BACKEND"] == "codex_exec"
    assert env["OPTIMIZER_BACKEND"] == "openai_chat"
    assert env["CODEX_EXEC_PATH"] == "/opt/codex"


def test_configure_backends_honors_preexisting_exec_path():
    env = {"CLAUDE_CODE_EXEC_PATH": "/custom/claude"}
    configure_backends(env, "claude", claude_bin="/opt/claude")
    assert env["CLAUDE_CODE_EXEC_PATH"] == "/custom/claude"  # user pin wins


def test_configure_backends_falls_back_to_default_bin(monkeypatch):
    # No override + nothing resolvable on PATH -> the plain CLI name.
    monkeypatch.setattr(oauth_guard.shutil, "which", lambda _name: None)
    env: dict[str, str] = {}
    configure_backends(env, "claude")
    assert env["CLAUDE_CODE_EXEC_PATH"] == "claude"


def test_configure_backends_rejects_unknown_provider():
    with pytest.raises(ValueError):
        configure_backends({}, "bard")


# -- target resolution ----------------------------------------------------- #


@pytest.mark.parametrize("argv,expected", [
    (["--backend", "codex_exec"], "codex"),
    (["--backend=claude_code_exec"], "claude"),
    (["--target_backend", "codex_exec"], "codex"),
    (["--target_backend=claude_code_exec"], "claude"),
    (["--config", "x.yaml"], "claude"),  # default when no backend flag
])
def test_resolve_target_from_args(argv, expected):
    assert resolve_target(argv, environ={}) == expected


def test_resolve_target_from_env_when_args_silent():
    assert resolve_target(["--config", "x.yaml"], environ={"SKILLOPT_OAUTH_TARGET": "codex"}) == "codex"


def test_resolve_target_args_beat_env():
    out = resolve_target(["--backend", "claude_code_exec"], environ={"SKILLOPT_OAUTH_TARGET": "codex"})
    assert out == "claude"


# -- main(): preflight -> scrub -> route -> exec --------------------------- #


class _RecordingExec:
    """Stands in for ``os.execvpe``; records the call instead of replacing the process."""

    def __init__(self):
        self.called = False
        self.file = ""
        self.args: list[str] = []
        self.env: dict[str, str] = {}

    def __call__(self, file, args, env):
        self.called = True
        self.file = file
        self.args = list(args)
        self.env = dict(env)


def test_main_execs_upstream_with_passthrough_and_safe_env(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-should-never-reach-child")
    monkeypatch.delenv("CLAUDE_CODE_EXEC_PATH", raising=False)
    rec = _RecordingExec()
    user_args = ["--config", "configs/foo.yaml", "--backend", "claude_code_exec"]

    main(user_args, probe=lambda _p: "oauth", exec_fn=rec)

    assert rec.called is True
    assert rec.file == "skillopt-train"
    # argv passes through verbatim after the program name.
    assert rec.args == ["skillopt-train", *user_args]
    # the scrub closed the metered-billing hole...
    assert "ANTHROPIC_API_KEY" not in rec.env
    # ...and the routing pointed upstream at the OAuth CLI.
    assert rec.env["TARGET_BACKEND"] == "claude_code_exec"
    assert "CLAUDE_CODE_EXEC_PATH" in rec.env


def test_main_fails_closed_without_launching(monkeypatch):
    rec = _RecordingExec()
    rc = main(["--config", "x.yaml"], probe=lambda _p: "none", exec_fn=rec)
    assert rc == 2
    assert rec.called is False  # never handed off to upstream


def test_main_routes_codex_when_selected():
    rec = _RecordingExec()
    main(["--backend", "codex_exec"], probe=lambda _p: "oauth", exec_fn=rec)
    assert rec.env["TARGET_BACKEND"] == "codex_exec"
    assert "CODEX_EXEC_PATH" in rec.env


# -- lifted probe internals: macOS Keychain existence probe ---------------- #


@pytest.mark.parametrize("returncode,expected", [(0, "oauth"), (1, None), (2, None)])
def test_probe_claude_keychain_returncode(monkeypatch, returncode, expected):
    monkeypatch.setattr(oauth_guard.platform, "system", lambda: "Darwin")

    def _fake_run(cmd, *args, **kwargs):
        return subprocess.CompletedProcess(cmd, returncode, "", "")

    monkeypatch.setattr(oauth_guard.subprocess, "run", _fake_run)
    assert oauth_guard._probe_claude_keychain() == expected


def test_probe_claude_keychain_non_macos_short_circuits(monkeypatch):
    monkeypatch.setattr(oauth_guard.platform, "system", lambda: "Linux")

    def _boom(*args, **kwargs):
        raise AssertionError("subprocess.run must not run on non-macOS")

    monkeypatch.setattr(oauth_guard.subprocess, "run", _boom)
    assert oauth_guard._probe_claude_keychain() is None


def test_probe_claude_keychain_oserror_is_none(monkeypatch):
    monkeypatch.setattr(oauth_guard.platform, "system", lambda: "Darwin")

    def _raise(*args, **kwargs):
        raise OSError("no `security` binary here")

    monkeypatch.setattr(oauth_guard.subprocess, "run", _raise)
    assert oauth_guard._probe_claude_keychain() is None


# -- lifted probe internals: claude verdict falls through to Keychain ------- #


@pytest.mark.parametrize("keychain,expected", [("oauth", "oauth"), (None, "none")])
def test_probe_claude_oauth_uses_keychain_verdict(monkeypatch, tmp_path, keychain, expected):
    # No env token, no ~/.claude/.credentials.json (home -> empty tmp_path), no API key.
    monkeypatch.delenv("CLAUDE_CODE_OAUTH_TOKEN", raising=False)
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.setattr(oauth_guard.Path, "home", classmethod(lambda cls: tmp_path))
    monkeypatch.setattr(oauth_guard, "_probe_claude_keychain", lambda: keychain)
    assert oauth_guard._probe_claude_oauth() == expected


# -- lifted probe internals: codex auth.json mode -------------------------- #


@pytest.mark.parametrize("payload,expected", [
    ('{"auth_mode": "chatgpt"}', "oauth"),
    ('{"preferred_auth_method": "chatgpt"}', "oauth"),
    ('{"auth_mode": "apikey"}', "api_key"),
    ('{"OPENAI_API_KEY": "sk-x"}', "api_key"),
    ('{}', "none"),
])
def test_probe_codex_oauth_from_auth_json(monkeypatch, tmp_path, payload, expected):
    (tmp_path / "auth.json").write_text(payload, encoding="utf-8")
    monkeypatch.setenv("CODEX_HOME", str(tmp_path))
    assert oauth_guard._probe_codex_oauth() == expected


def test_probe_codex_oauth_missing_file_is_none(monkeypatch, tmp_path):
    monkeypatch.setenv("CODEX_HOME", str(tmp_path))  # no auth.json written
    assert oauth_guard._probe_codex_oauth() == "none"
