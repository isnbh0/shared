"""Hermetic tests for the real-CLI compatibility paths.

These cover the edits that make the OAuth executor / scheduler / training wiring
match the actual ``claude`` and ``codex`` CLIs (structured ``--output-format
json`` output, ``codex exec`` sandboxing, the macOS Keychain OAuth probe, the
narrowed auth/billing detector, and the train-side prompt/config plumbing).

Nothing here spawns a real ``claude`` / ``codex`` CLI or touches real OAuth: the
Keychain probe's ``platform``/``subprocess`` seams are monkeypatched, credential
lookups are pointed at ``tmp_path``, and the scheduler test drives an in-process
recording executor.
"""
from __future__ import annotations

import asyncio
import json
import subprocess

import pytest

from skillopt_oauth import executor, train
from skillopt_oauth.config import Config
from skillopt_oauth.executor import (
    _AUTH_BILLING_RE,
    ModelAssertionError,
    OAuthCLIExecutor,
)
from skillopt_oauth.scheduler import cli_job
from skillopt_oauth.train import EnvConfig, reconcile_loop_config


@pytest.fixture
def ex():
    """A plain executor (default ``reasoning_effort='high'``). No call ever runs."""
    return OAuthCLIExecutor(claude_bin="claude", codex_bin="codex")


# --------------------------------------------------------------------------- #
# _probe_claude_keychain -- macOS-only existence probe, fail-safe to None
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize("returncode,expected", [(0, "oauth"), (1, None), (2, None)])
def test_probe_claude_keychain_returncode(monkeypatch, returncode, expected):
    monkeypatch.setattr(executor.platform, "system", lambda: "Darwin")

    def _fake_run(cmd, *args, **kwargs):
        return subprocess.CompletedProcess(cmd, returncode, "", "")

    monkeypatch.setattr(executor.subprocess, "run", _fake_run)
    assert executor._probe_claude_keychain() == expected


def test_probe_claude_keychain_non_macos_short_circuits(monkeypatch):
    monkeypatch.setattr(executor.platform, "system", lambda: "Linux")

    def _boom(*args, **kwargs):
        raise AssertionError("subprocess.run must not run on non-macOS")

    monkeypatch.setattr(executor.subprocess, "run", _boom)
    assert executor._probe_claude_keychain() is None


def test_probe_claude_keychain_oserror_is_none(monkeypatch):
    monkeypatch.setattr(executor.platform, "system", lambda: "Darwin")

    def _raise(*args, **kwargs):
        raise OSError("no `security` binary here")

    monkeypatch.setattr(executor.subprocess, "run", _raise)
    assert executor._probe_claude_keychain() is None


# --------------------------------------------------------------------------- #
# _probe_claude_oauth -- falls through to the Keychain verdict on macOS
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize("keychain,expected", [("oauth", "oauth"), (None, "none")])
def test_probe_claude_oauth_uses_keychain_verdict(monkeypatch, tmp_path, keychain, expected):
    # No env token, no ~/.claude/.credentials.json (home -> empty tmp_path), no API key.
    monkeypatch.delenv("CLAUDE_CODE_OAUTH_TOKEN", raising=False)
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.setattr(executor.Path, "home", classmethod(lambda cls: tmp_path))
    monkeypatch.setattr(executor, "_probe_claude_keychain", lambda: keychain)
    assert executor._probe_claude_oauth() == expected


# --------------------------------------------------------------------------- #
# _build_command -- structured claude output; codex sandbox + effort flags
# --------------------------------------------------------------------------- #
def test_build_command_claude_read_only(ex):
    cmd, stdin = ex._build_command("claude", "hi", None, False)
    assert cmd == ["claude", "-p", "hi", "--output-format", "json"]
    assert stdin is None
    assert "--bare" not in cmd
    assert "--permission-mode" not in cmd  # no write grant when allow_writes=False


def test_build_command_claude_allow_writes_grants_acceptedits(ex):
    cmd, _ = ex._build_command("claude", "hi", None, True)
    assert "--output-format" in cmd and "json" in cmd
    assert "--bare" not in cmd
    assert "--permission-mode" in cmd
    assert "acceptEdits" in cmd


def test_build_command_codex_read_only(ex):
    cmd, stdin = ex._build_command("codex", "reflect", None, False)
    assert cmd[:4] == ["codex", "exec", "-s", "read-only"]
    assert "--skip-git-repo-check" in cmd
    assert "model_reasoning_effort=high" in " ".join(cmd)
    assert stdin == "reflect"  # codex takes the prompt on stdin


def test_build_command_codex_allow_writes_widens_sandbox(ex):
    cmd, _ = ex._build_command("codex", "reflect", None, True)
    assert "-s" in cmd and "workspace-write" in cmd
    assert "read-only" not in cmd
    assert "--skip-git-repo-check" in cmd


def test_build_command_codex_omits_effort_when_unset():
    ex0 = OAuthCLIExecutor(claude_bin="claude", codex_bin="codex", reasoning_effort="")
    cmd, _ = ex0._build_command("codex", "reflect", None, False)
    assert "model_reasoning_effort" not in " ".join(cmd)


# --------------------------------------------------------------------------- #
# _extract_model -- modelUsage key from claude json; marker wins; codex None
# --------------------------------------------------------------------------- #
CLAUDE_JSON = (
    '{"type":"result","result":"done","total_cost_usd":0.21,'
    '"modelUsage":{"claude-opus-4-8":{"outputTokens":50},'
    '"claude-haiku-4-5-20251001":{"outputTokens":3}}}'
)


def test_extract_model_from_claude_output_format_json(ex):
    assert ex._extract_model("claude", CLAUDE_JSON) == "claude-opus-4-8"


def test_extract_model_explicit_marker_wins_amid_prose(ex):
    assert ex._extract_model("claude", "blah [[SKILLOPT_MODEL:stub-x]] blah") == "stub-x"


def test_extract_model_codex_returns_none(ex):
    assert ex._extract_model("codex", "no marker here") is None


# --------------------------------------------------------------------------- #
# _assert_model -- alias/full-id compatible; cross-family + generic mismatch raise
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize("requested,reported,expected", [
    ("opus", "claude-opus-4-8", "claude-opus-4-8"),
    (None, "claude-opus-4-8", "claude-opus-4-8"),
    ("claude-opus-4-8", None, "claude-opus-4-8"),
])
def test_assert_model_compatible(requested, reported, expected):
    assert OAuthCLIExecutor._assert_model(requested, reported) == expected


@pytest.mark.parametrize("requested,reported", [
    ("opus", "claude-haiku-4-5"),  # cross-family: silent downgrade
    ("model-A", "model-B"),        # generic contradiction
])
def test_assert_model_mismatch_raises(requested, reported):
    with pytest.raises(ModelAssertionError):
        OAuthCLIExecutor._assert_model(requested, reported)


# --------------------------------------------------------------------------- #
# _AUTH_BILLING_RE -- narrow enough to ignore benign prose / JSON usage fields
# --------------------------------------------------------------------------- #
STUB_AUTH_WARNING = (
    "Notice: ANTHROPIC_API_KEY detected; this request will be billed to "
    "your API credits, not your subscription."
)


@pytest.mark.parametrize("text", [
    "I created the file 260630-120000-summary.md in the working directory.",
    '{"modelUsage": {"claude-opus-4-8": {"outputTokens": 50}}}',
])
def test_auth_billing_regex_ignores_benign(text):
    assert _AUTH_BILLING_RE.search(text) is None


@pytest.mark.parametrize("text", [
    STUB_AUTH_WARNING,
    "credit balance is too low",
    "rate limit exceeded",
    "usage limit reached",
    "429 too many requests",
])
def test_auth_billing_regex_matches_real_signals(text):
    assert _AUTH_BILLING_RE.search(text) is not None


# --------------------------------------------------------------------------- #
# scheduler.cli_job -- threads allow_writes (and provider) into run_cli
# --------------------------------------------------------------------------- #
class _CleanResult:
    exit_code = 0
    auth_billing_warning = False
    stdout = ""
    stderr = ""


class _RecordingExecutor:
    """Records the kwargs ``cli_job`` forwards to ``run_cli``."""

    def __init__(self):
        self.kwargs = None
        self.result = _CleanResult()

    def run_cli(self, **kwargs):
        self.kwargs = kwargs
        return self.result


def test_cli_job_passes_allow_writes_through():
    asyncio.run(_cli_job_allow_writes())


async def _cli_job_allow_writes():
    fake = _RecordingExecutor()
    factory = cli_job(fake, provider="claude", prompt="x", allow_writes=True)
    out = await factory()
    assert fake.kwargs["allow_writes"] is True
    assert fake.kwargs["provider"] == "claude"
    # classify_cli_result passes a clean (exit 0, no billing) result straight through.
    assert out is fake.result


# --------------------------------------------------------------------------- #
# train.reconcile_loop_config -- override > env YAML > P1 Config default
# --------------------------------------------------------------------------- #
def _env_config(**over) -> EnvConfig:
    # Values deliberately distinct from both the overrides and the P1 Config
    # defaults (batch_size=40, n_samples=3, claude/codex) so each precedence
    # tier is observable.
    base = dict(
        env="timestamp", initial_skill="skills/timestamp/initial.md",
        tasks_dir="tasks/timestamp", batch_size=7, n_samples=4,
        rollout_provider="claude-env", reflect_provider="codex-env",
    )
    base.update(over)
    return EnvConfig(**base)


def test_reconcile_explicit_overrides_win():
    cfg = reconcile_loop_config(
        Config(), _env_config(), out_dir=".",
        batch_size=1, n_samples=2, val_n_samples=5,
        rollout_provider="x", reflect_provider="y",
    )
    assert cfg.batch_size == 1
    assert cfg.n_samples == 2
    assert cfg.val_n_samples == 5
    assert cfg.rollout_provider == "x"
    assert cfg.reflect_provider == "y"


def test_reconcile_env_yaml_wins_without_overrides():
    cfg = reconcile_loop_config(Config(), _env_config(), out_dir=".")
    assert cfg.batch_size == 7              # env YAML, not P1 default 40
    assert cfg.n_samples == 4               # env YAML, not P1 default 3
    assert cfg.val_n_samples == 4           # defaults to n_samples
    assert cfg.rollout_provider == "claude-env"
    assert cfg.reflect_provider == "codex-env"


# --------------------------------------------------------------------------- #
# train prompt builders + edit-op JSON recovery
# --------------------------------------------------------------------------- #
def test_rollout_prompt_inlines_skill_and_task_and_top_level():
    rp = train._rollout_prompt(
        "PREFIX EVERYTHING", {"prompt": "Create summary.md", "id": "t1"}
    )
    assert "PREFIX EVERYTHING" in rp      # skill text inlined
    assert "Create summary.md" in rp      # task prompt inlined
    assert "TOP LEVEL" in rp              # artifacts at top level for the scorer


def test_reflect_prompt_pins_schema_and_objective():
    fp = train._reflect_prompt(
        "old skill", [{"prompt": "Create a folder backups", "id": "v3"}]
    )
    assert '"edits"' in fp                # the edit-op JSON schema is pinned
    assert "YYMMDD-HHMMSS-" in fp         # the scored objective is stated
    assert "Create a folder backups" in fp  # the minibatch task is referenced


def test_extract_edits_json_from_fenced_reply():
    fenced = (
        "Sure! Here:\n```json\n"
        '{"edits": [{"kind":"add","anchor":"","text":"x"}]}\n```'
    )
    got = train._extract_edits_json(fenced)
    assert json.loads(got)["edits"][0]["kind"] == "add"


def test_extract_edits_json_passthrough_when_no_object():
    raw = "no json object anywhere in this reply"
    assert train._extract_edits_json(raw) == raw
