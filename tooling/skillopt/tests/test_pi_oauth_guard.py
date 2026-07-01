"""Hermetic tests for the pi branch of the OAuth-safety launch wrapper.

Nothing here spawns a real ``pi`` CLI, execs upstream, or touches a real pi store: the probe /
credential lookups are pointed at ``tmp_path`` and ``exec_fn`` is a recording stub. The autouse
``hermetic_log_dir`` fixture (tests/conftest.py) redirects records into ``tmp_path`` and clears
the pi env-var surface.
"""
from __future__ import annotations

import json

import pytest

from skillopt_oauth import oauth_guard
from skillopt_oauth.oauth_guard import main


class _RecordingExec:
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


def _write_pi_auth(tmp_path, mapping):
    (tmp_path / "auth.json").write_text(json.dumps(mapping), encoding="utf-8")


# -- provider detection + routing dicts ------------------------------------ #


@pytest.mark.parametrize("value,expected", [
    ("pi", "pi"), ("pi_chat", "pi"), ("pi_exec", "pi"),
    ("openai", None),          # no 'pi' false positive
    ("codex_exec", "codex"), ("claude_code_exec", "claude"),
])
def test_provider_of_detects_pi(value, expected):
    assert oauth_guard._provider_of(value) == expected


def test_pi_routing_dicts():
    assert "pi" in oauth_guard.PROVIDERS
    assert oauth_guard._TARGET_BACKEND["pi"] == "pi_exec"
    assert oauth_guard._OPTIMIZER_BACKEND["pi"] == "pi_chat"
    assert oauth_guard._EXEC_PATH_VAR["pi"] == "PI_EXEC_PATH"
    assert oauth_guard._DEFAULT_BIN["pi"] == "pi"


# -- probe dispatch -------------------------------------------------------- #


def test_default_oauth_probe_routes_pi_only(monkeypatch):
    calls: list[str] = []
    monkeypatch.setattr(oauth_guard, "_probe_pi_oauth", lambda: calls.append("pi") or "oauth")
    monkeypatch.setattr(oauth_guard, "_probe_codex_oauth", lambda: calls.append("codex") or "none")
    monkeypatch.setattr(oauth_guard, "_probe_claude_oauth", lambda: calls.append("claude") or "none")
    assert oauth_guard.default_oauth_probe("pi") == "oauth"
    assert calls == ["pi"]  # neither codex nor claude probe ran


# -- _probe_pi_oauth: subscription vs opt-in vs fail-closed ----------------- #


def test_probe_pi_subscription_oauth(monkeypatch, tmp_path):
    monkeypatch.setenv("PI_CODING_AGENT_DIR", str(tmp_path))
    _write_pi_auth(tmp_path, {"openai-codex": {"type": "oauth"}})
    # no deployment pin -> defaults to openai-codex (a subscription provider)
    assert oauth_guard._probe_pi_oauth() == "oauth"


def test_probe_pi_subscription_api_key_refused(monkeypatch, tmp_path):
    monkeypatch.setenv("PI_CODING_AGENT_DIR", str(tmp_path))
    _write_pi_auth(tmp_path, {"openai-codex": {"apiKey": "sk-x"}})
    assert oauth_guard._probe_pi_oauth() == "api_key"


def test_probe_pi_unopted_metered_fails_closed(monkeypatch, tmp_path):
    monkeypatch.setenv("PI_CODING_AGENT_DIR", str(tmp_path))
    monkeypatch.setenv("TARGET_DEPLOYMENT", "zai/glm-5.2")
    _write_pi_auth(tmp_path, {"zai": {"apiKey": "sk-z"}})
    # zai not opted in -> api_key -> preflight will refuse.
    assert oauth_guard._probe_pi_oauth() == "api_key"


def test_probe_pi_opted_in_metered_accepts(monkeypatch, tmp_path):
    monkeypatch.setenv("PI_CODING_AGENT_DIR", str(tmp_path))
    monkeypatch.setenv("TARGET_DEPLOYMENT", "zai/glm-5.2")
    monkeypatch.setenv("PI_ALLOW_METERED", "zai")
    _write_pi_auth(tmp_path, {"zai": {"apiKey": "sk-z"}})
    assert oauth_guard._probe_pi_oauth() == "oauth"  # any usable entry accepted once opted in


def test_probe_pi_opted_in_but_no_entry_is_none(monkeypatch, tmp_path):
    monkeypatch.setenv("PI_CODING_AGENT_DIR", str(tmp_path))
    monkeypatch.setenv("TARGET_DEPLOYMENT", "zai/glm-5.2")
    monkeypatch.setenv("PI_ALLOW_METERED", "zai")
    _write_pi_auth(tmp_path, {})  # nothing for zai
    assert oauth_guard._probe_pi_oauth() == "none"


# -- provider + allowed-metered resolution --------------------------------- #


def test_resolve_pinned_pi_provider_from_deployment(monkeypatch):
    monkeypatch.setenv("TARGET_DEPLOYMENT", "zai/glm-5.2")
    assert oauth_guard._resolve_pinned_pi_provider(argv=[]) == "zai"


def test_resolve_pinned_pi_provider_from_argv_wins(monkeypatch):
    monkeypatch.setenv("TARGET_DEPLOYMENT", "openai-codex/gpt-5.5")
    assert oauth_guard._resolve_pinned_pi_provider(argv=["--target_model", "zai/glm-5.2"]) == "zai"


def test_resolve_pi_allowed_metered_env_override_wins(tmp_path):
    cfg = tmp_path / "c.yaml"
    cfg.write_text("model:\n  pi_allowed_metered_providers: [anthropic]\n")
    got = oauth_guard._resolve_pi_allowed_metered(
        ["--config", str(cfg)], {"PI_ALLOW_METERED": "zai"})
    assert got == {"zai"}  # env override beats config


def test_resolve_pi_allowed_metered_from_config(tmp_path):
    cfg = tmp_path / "c.yaml"
    cfg.write_text("model:\n  pi_allowed_metered_providers: [zai, anthropic]\n")
    got = oauth_guard._resolve_pi_allowed_metered(["--config", str(cfg)], {})
    assert got == {"zai", "anthropic"}


# -- main(): enforce flag + allowed-metered export + opt-in-aware scrub ----- #


def test_main_pi_exports_enforce_flag_and_allow_metered(monkeypatch):
    monkeypatch.setenv("PI_ALLOW_METERED", "zai")
    rec = _RecordingExec()
    main(["--backend", "pi_exec", "--config", "x.yaml"],
         probe=lambda _p: "oauth", exec_fn=rec)
    assert rec.called is True
    assert rec.env["SKILLOPT_OAUTH_ENFORCE"] == "1"
    assert rec.env["PI_ALLOW_METERED"] == "zai"
    assert rec.env["TARGET_BACKEND"] == "pi_exec"
    assert rec.env["OPTIMIZER_BACKEND"] == "pi_chat"
    assert "PI_EXEC_PATH" in rec.env


@pytest.mark.parametrize("anthropic_opted_in", [False, True])
def test_main_pi_scrub_authjson_only(monkeypatch, tmp_path, anthropic_opted_in):
    """Auth.json-only credential model, exercised through the REAL probe (no probe stub).

    Every metered ``*_API_KEY`` env is scrubbed whether or not its provider is opted in -- an
    opted-in provider (here ``zai``) authenticates from pi's ``auth.json`` (the fixture below),
    never from an env key, and the run still proceeds. The only opt-in-sensitive env credential is
    ``ANTHROPIC_OAUTH_TOKEN``: preserved when ``anthropic`` is opted in, popped otherwise.
    """
    monkeypatch.setenv("PI_CODING_AGENT_DIR", str(tmp_path))
    monkeypatch.setenv("PI_ALLOW_METERED", "zai,anthropic" if anthropic_opted_in else "zai")
    monkeypatch.setenv("TARGET_DEPLOYMENT", "zai/glm-5.2")   # pinned provider zai (opted in)
    monkeypatch.setenv("ZAI_API_KEY", "sk-zai")              # metered key -> scrubbed even opted in
    monkeypatch.setenv("OPENAI_API_KEY", "sk-openai")        # not opted in -> scrubbed
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-anthropic")  # metered key -> scrubbed
    monkeypatch.setenv("ANTHROPIC_OAUTH_TOKEN", "tok")       # opt-in-sensitive (kept iff opted in)
    _write_pi_auth(tmp_path, {"zai": {"apiKey": "sk-z"}})    # opted-in zai resolves via auth.json
    rec = _RecordingExec()
    main(["--backend", "pi_exec"], exec_fn=rec)              # REAL probe path (opted-in zai -> oauth)
    assert rec.called is True                                # auth.json entry present -> preflight proceeds
    assert "ZAI_API_KEY" not in rec.env                      # *_API_KEY scrubbed even when opted in
    assert "OPENAI_API_KEY" not in rec.env
    assert "ANTHROPIC_API_KEY" not in rec.env
    if anthropic_opted_in:
        assert rec.env.get("ANTHROPIC_OAUTH_TOKEN") == "tok"  # opted in -> kept
    else:
        assert "ANTHROPIC_OAUTH_TOKEN" not in rec.env          # not opted -> popped


def test_main_pi_preflight_fails_closed_when_probe_refuses(monkeypatch):
    rec = _RecordingExec()
    rc = main(["--backend", "pi_exec"], probe=lambda _p: "api_key", exec_fn=rec,
              now=lambda: "t", run_id_fn=lambda: "rid")
    assert rc == 2
    assert rec.called is False  # never handed off


def test_main_non_pi_run_leaves_enforce_flag_unset(monkeypatch):
    rec = _RecordingExec()
    main(["--backend", "codex_exec"], probe=lambda _p: "oauth", exec_fn=rec)
    assert "SKILLOPT_OAUTH_ENFORCE" not in rec.env  # pi-only signal
