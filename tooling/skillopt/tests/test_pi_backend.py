"""The vendored skillopt fork adds a ``pi`` (Earendil) CLI backend. Phase 1 covers the
``pi_chat`` chat surface + the billing guards on the live dispatcher (``skillopt.model``)
without spawning ``pi`` -- the subprocess shim is mocked, so these spend nothing.

Success is derived from the STREAM, not the exit code (pi exits 0 even on runtime failure),
and the ``actual == intended`` guard plus the wrapper-gated permitted-set gate are exercised.
"""
from __future__ import annotations

import json

import pytest

import skillopt.model as M
from skillopt.model import backend_config as BC
from skillopt.model import pi_backend as P
from skillopt.model.backend_config import (
    get_optimizer_backend,
    is_optimizer_chat_backend,
    is_target_chat_backend,
    set_optimizer_backend,
    set_target_backend,
)
from skillopt.model.common import default_model_for_backend, normalize_backend_name


@pytest.fixture(autouse=True)
def _isolate_backend_state():
    """Restore the global optimizer/target backend + deployments so a case can't leak
    into the other suites (the setters mutate module globals + os.environ)."""
    saved_opt_backend = BC.OPTIMIZER_BACKEND
    saved_tgt_backend = BC.TARGET_BACKEND
    saved_opt_dep = P.OPTIMIZER_DEPLOYMENT
    saved_tgt_dep = P.TARGET_DEPLOYMENT
    M.reset_token_tracker()
    yield
    BC.OPTIMIZER_BACKEND = saved_opt_backend
    BC.TARGET_BACKEND = saved_tgt_backend
    P.OPTIMIZER_DEPLOYMENT = saved_opt_dep
    P.TARGET_DEPLOYMENT = saved_tgt_dep
    M.reset_token_tracker()


class _FakeProc:
    """A subprocess.CompletedProcess stand-in for hermetic _run_pi tests."""

    def __init__(self, *, stdout="", stderr="", returncode=0):
        self.stdout = stdout
        self.stderr = stderr
        self.returncode = returncode


def _message_end(text, *, provider="openai-codex", model="gpt-5.5", usage=None):
    """One valid assistant ``message_end`` JSONL line."""
    msg = {
        "type": "message_end",
        "message": {
            "role": "assistant",
            "provider": provider,
            "model": model,
            "content": [{"type": "text", "text": text}],
            "usage": usage or {"input": 70, "output": 3, "cacheRead": 7936,
                               "cacheWrite": 0, "totalTokens": 8009},
        },
    }
    return json.dumps(msg, ensure_ascii=False)


_AGENT_END = json.dumps({"type": "agent_end", "messages": [], "willRetry": False})


@pytest.fixture
def fake_pi(monkeypatch):
    """Replace the pi subprocess helper so no real ``pi`` runs."""
    seen: dict = {"calls": 0}

    def fake_run(*, model, prompt, attachments, structured_output, timeout):
        seen["model"] = model
        seen["prompt"] = prompt
        seen["calls"] += 1
        return ("REWRITTEN", {"prompt_tokens": 10, "completion_tokens": 5, "total_tokens": 15})

    monkeypatch.setattr(P, "_run_pi", fake_run)
    return seen


# -- registration / normalization ------------------------------------------ #


def test_allowlist_accepts_pi_chat_optimizer():
    set_optimizer_backend("pi_chat")
    assert get_optimizer_backend() == "pi_chat"
    assert is_optimizer_chat_backend() is True


def test_pi_normalizes_and_has_default_models():
    assert normalize_backend_name("pi") == "pi_chat"
    assert default_model_for_backend("pi_chat") == "gpt-5.5"
    assert default_model_for_backend("pi_exec") == "gpt-5.5"


def test_pi_exec_is_not_an_optimizer_but_pi_is():
    with pytest.raises(ValueError):
        set_optimizer_backend("pi_exec")
    set_optimizer_backend("pi")  # alias -> pi_chat, must not raise
    assert get_optimizer_backend() == "pi_chat"


def test_pi_chat_is_a_target_chat_backend():
    set_target_backend("pi_chat")
    assert is_target_chat_backend() is True


def test_set_optimizer_deployment_reaches_pi():
    M.set_optimizer_deployment("gpt-5.5")
    assert P.OPTIMIZER_DEPLOYMENT == "gpt-5.5"


# -- dispatch routing + token accounting ----------------------------------- #


def test_chat_optimizer_dispatches_to_pi(fake_pi):
    set_optimizer_backend("pi_chat")
    M.set_optimizer_deployment("gpt-5.5")
    out, usage = M.chat_optimizer(system="You optimize prompts.", user="Improve this skill.")
    assert out == "REWRITTEN"
    assert fake_pi["model"] == "gpt-5.5"
    assert usage["total_tokens"] == 15


def test_chat_optimizer_messages_dispatches_to_pi(fake_pi):
    set_optimizer_backend("pi_chat")
    out, _usage = M.chat_optimizer_messages(messages=[{"role": "user", "content": "hi"}])
    assert out == "REWRITTEN"
    assert fake_pi["calls"] == 1


def test_pi_tokens_not_double_counted(fake_pi):
    # pi_backend shares common.tracker with claude_backend; the merge in get_token_summary
    # must count each pi call once, not twice.
    set_optimizer_backend("pi_chat")
    M.chat_optimizer(system="s", user="u")
    M.chat_optimizer(system="s", user="u")
    summary = M.get_token_summary()
    assert summary["_total"]["calls"] == 2
    assert summary["_total"]["total_tokens"] == 30


def test_claude_chat_optimizer_still_selectable():
    # Regression: the existing dispatch branches are untouched.
    set_optimizer_backend("claude_chat")
    assert get_optimizer_backend() == "claude_chat"


# -- usage mapping + stream parsing ---------------------------------------- #


def test_usage_from_message_uses_pi_total():
    got = P._usage_from_message(
        {"input": 70, "output": 3, "cacheRead": 7936, "cacheWrite": 0, "totalTokens": 8009}
    )
    assert got == {"prompt_tokens": 8006, "completion_tokens": 3, "total_tokens": 8009}


def test_parse_pi_stream_takes_last_assistant_and_sums_usage():
    stream = "\n".join([
        json.dumps({"type": "session", "id": "abc"}),
        _message_end("FIRST", usage={"output": 2, "totalTokens": 10}),
        _message_end("SECOND", usage={"output": 4, "totalTokens": 20}),
        _AGENT_END,
    ])
    parsed = P._parse_pi_stream(stream)
    assert parsed["last_text"] == "SECOND"
    assert parsed["usage"]["total_tokens"] == 30
    assert parsed["usage"]["completion_tokens"] == 6


def test_parse_pi_stream_u2028_safe():
    # A literal U+2028 inside the assistant text must not split the JSON line
    # (str.splitlines() would break here; str.split("\n") does not).
    text = "line-a line-b"
    parsed = P._parse_pi_stream(_message_end(text))
    assert " " in parsed["last_text"]


# -- actual == intended guard ---------------------------------------------- #


def test_guard_provider_passes_intentional_glm_raises_on_fallback():
    parsed = P._parse_pi_stream(_message_end("ok", provider="zai", model="glm-5.2"))
    # Intentional GLM pin: passes.
    P._guard_provider(parsed, "zai", "glm-5.2")
    # openai-codex was pinned but zai served it -> silent fallback -> non-retryable.
    with pytest.raises(P.PiBillingError):
        P._guard_provider(parsed, "openai-codex", "gpt-5.5")


def test_guard_provider_usage_without_provider_refuses():
    stream = json.dumps({
        "type": "message_end",
        "message": {"role": "assistant", "content": [{"type": "text", "text": "hi"}],
                    "usage": {"output": 1, "totalTokens": 5}},
    })
    parsed = P._parse_pi_stream(stream)
    with pytest.raises(P.PiBillingError):
        P._guard_provider(parsed, "openai-codex", "gpt-5.5")


# -- argv invariants (no billing) ------------------------------------------ #


def test_run_pi_argv_invariants(monkeypatch):
    captured: dict = {}

    def fake_run(command, **kwargs):
        captured["cmd"] = list(command)
        return _FakeProc(stdout=_message_end("HELLO"), returncode=0)

    monkeypatch.setattr(P.subprocess, "run", fake_run)
    out, _usage = P._run_pi(model="gpt-5.5", prompt="hi", attachments=[],
                            structured_output=False, timeout=None)
    assert out == "HELLO"
    cmd = captured["cmd"]
    assert "--provider" in cmd and cmd[cmd.index("--provider") + 1] == "openai-codex"
    assert "--model" in cmd
    assert "--no-tools" in cmd
    assert "--no-session" in cmd
    assert "--system-prompt" in cmd
    assert "--api-key" not in cmd  # NEVER passed


def test_run_pi_refuses_image_attachment():
    with pytest.raises(RuntimeError):
        P._run_pi(model="gpt-5.5", prompt="describe", attachments=[{"type": "image", "path": "/x.png"}],
                  structured_output=False, timeout=None)


# -- success from stream, NOT exit code (empirical: pi exit code is unreliable) --- #


def test_run_pi_exit0_but_runtime_error_stream_fails(monkeypatch):
    # pi exits 0 on a missing API key / runtime failure; with no assistant message_end the
    # stream is a FAILURE and _run_pi must raise despite returncode == 0.
    err_line = json.dumps({"type": "error", "message": "no api key configured"})

    def fake_run(command, **kwargs):
        return _FakeProc(stdout=err_line, returncode=0)

    monkeypatch.setattr(P.subprocess, "run", fake_run)
    with pytest.raises(RuntimeError):
        P._run_pi(model="gpt-5.5", prompt="hi", attachments=[],
                  structured_output=False, timeout=None)


def test_run_pi_nonzero_exit_but_valid_stream_succeeds(monkeypatch):
    # Symmetric proof that returncode does NOT gate success: a non-zero exit with a valid
    # assistant message_end (matching the pin) still returns the text.
    def fake_run(command, **kwargs):
        return _FakeProc(stdout=_message_end("STILL-OK"), returncode=1)

    monkeypatch.setattr(P.subprocess, "run", fake_run)
    out, _usage = P._run_pi(model="gpt-5.5", prompt="hi", attachments=[],
                            structured_output=False, timeout=None)
    assert out == "STILL-OK"


# -- wrapper-gated permitted-provider gate --------------------------------- #


def test_assert_allowed_provider_blocks_unopted_metered_when_enforced(monkeypatch):
    monkeypatch.setenv("SKILLOPT_OAUTH_ENFORCE", "1")
    monkeypatch.delenv("PI_ALLOW_METERED", raising=False)
    with pytest.raises(P.PiBillingError):
        P._assert_allowed_provider("zai")  # not opted in


def test_assert_allowed_provider_allows_opted_in_metered(monkeypatch):
    monkeypatch.setenv("SKILLOPT_OAUTH_ENFORCE", "1")
    monkeypatch.setenv("PI_ALLOW_METERED", "zai")
    P._assert_allowed_provider("zai")  # opted in -> no raise


def test_assert_allowed_provider_permissive_without_enforce(monkeypatch):
    monkeypatch.delenv("SKILLOPT_OAUTH_ENFORCE", raising=False)
    monkeypatch.delenv("PI_ALLOW_METERED", raising=False)
    # plain skillopt-train: no gate, any pin is the user's choice.
    P._assert_allowed_provider("zai")


def test_assert_allowed_provider_subscription_always_ok(monkeypatch):
    monkeypatch.setenv("SKILLOPT_OAUTH_ENFORCE", "1")
    monkeypatch.delenv("PI_ALLOW_METERED", raising=False)
    P._assert_allowed_provider("openai-codex")  # built-in subscription set


# -- billing error is non-retryable ---------------------------------------- #


def test_billing_error_is_not_retried(monkeypatch):
    calls: dict = {"n": 0}

    def boom(*, model, prompt, attachments, structured_output, timeout):
        calls["n"] += 1
        raise P.PiBillingError("provider fallback")

    monkeypatch.setattr(P, "_run_pi", boom)
    with pytest.raises(P.PiBillingError):
        P._chat_messages_impl("gpt-5.5", [{"role": "user", "content": "hi"}], 100, 5, "optimizer")
    assert calls["n"] == 1  # fatal on the first attempt, never retried


# ==========================================================================
# Phase 2: pi_exec agentic rollout target.
# ==========================================================================
import os

from skillopt.model import codex_harness as H
from skillopt.model.backend_config import is_target_exec_backend
from skillopt.model.codex_harness import render_skill_md


def test_pi_exec_is_a_target_exec_backend():
    set_target_backend("pi_exec")
    assert is_target_exec_backend() is True
    assert is_target_chat_backend() is False


def test_run_target_exec_dispatches_to_pi_exec(monkeypatch, tmp_path):
    set_target_backend("pi_exec")
    seen: dict = {"calls": 0}

    def fake_run_pi_exec(**kwargs):
        seen["calls"] += 1
        seen["work_dir"] = kwargs["work_dir"]
        return ("ANSWER", "raw")

    monkeypatch.setattr(P, "run_pi_exec", fake_run_pi_exec)
    out, _raw = H.run_target_exec(
        work_dir=str(tmp_path), prompt="solve it", model="gpt-5.5", timeout=60,
    )
    assert out == "ANSWER"
    assert seen["calls"] == 1


def test_pi_exec_stages_external_files_and_emits_no_allow_dir(monkeypatch, tmp_path):
    work_dir = tmp_path / "work"
    work_dir.mkdir()
    ext = tmp_path / "external.txt"
    ext.write_text("payload")
    captured: dict = {}

    def fake_run(command, **kwargs):
        captured["cmd"] = list(command)
        return _FakeProc(stdout=_message_end("DONE"), returncode=0)

    monkeypatch.setattr(P.subprocess, "run", fake_run)
    out, _raw = P._run_pi_cli_exec(
        work_dir=str(work_dir), prompt="task", model="gpt-5.5", timeout=60,
        data_dirs=[str(ext)],
    )
    assert out == "DONE"
    assert "--allow-dir" not in captured["cmd"]  # pi has no dir-mount flag
    assert "--add-dir" not in captured["cmd"]
    # the external file was staged under <work_dir>/_staged/
    assert (work_dir / "_staged" / "external.txt").read_text() == "payload"
    # the /skill: force-execute prefix rides the positional prompt
    assert any(str(tok).startswith("/skill:skillopt-target") for tok in captured["cmd"])
    assert "--skill" in captured["cmd"]


def test_run_pi_exec_sums_multi_turn_usage(monkeypatch, tmp_path):
    work_dir = tmp_path / "work"
    work_dir.mkdir()
    stream = "\n".join([
        _message_end("turn-1 partial", usage={"output": 2, "totalTokens": 10}),
        _message_end("turn-2 final", usage={"output": 4, "totalTokens": 20}),
        _AGENT_END,
    ])

    def fake_run(command, **kwargs):
        return _FakeProc(stdout=stream, returncode=0)

    monkeypatch.setattr(P.subprocess, "run", fake_run)
    out, _raw = P.run_pi_exec(work_dir=str(work_dir), prompt="t", model="gpt-5.5", timeout=60)
    assert out == "turn-2 final"  # last assistant text
    rollout = P.get_token_summary()["rollout"]
    assert rollout["total_tokens"] == 30      # 10 + 20 summed across turns
    assert rollout["completion_tokens"] == 6  # 2 + 4


def test_pi_exec_guard_applies_to_rollout(monkeypatch, tmp_path):
    work_dir = tmp_path / "work"
    work_dir.mkdir()
    # pin resolves to openai-codex (config default) but the stream came from zai -> fallback.
    fallback = _message_end("oops", provider="zai", model="glm-5.2")

    def fake_run(command, **kwargs):
        return _FakeProc(stdout=fallback, returncode=0)

    monkeypatch.setattr(P.subprocess, "run", fake_run)
    with pytest.raises(P.PiBillingError):
        P._run_pi_cli_exec(work_dir=str(work_dir), prompt="t", model="gpt-5.5", timeout=60)


def test_pi_tools_mapping():
    assert P._pi_tools(["Read", "Bash", "Edit"], allow_file_edits=False) == "read,bash,edit"
    got = P._pi_tools(["Read"], allow_file_edits=True)
    assert got.split(",")[0] == "read" and "write" in got and "edit" in got


def test_normalize_pi_exec_prompt_strips_anti_skill_wording():
    dirty = "Read the file. do not call a Skill tool. Then answer."
    assert "do not call a Skill tool" not in P._normalize_pi_exec_prompt(dirty)


def test_render_skill_md_frontmatter_name_is_skillopt_target():
    md = render_skill_md("Dynamic body here.")
    assert 'name: "skillopt-target"' in md
    assert "Dynamic body here." in md


def test_legacy_set_backend_pi_exec_and_name():
    M.set_backend("pi_exec")
    assert BC.get_optimizer_backend() == "pi_chat"
    assert BC.get_target_backend() == "pi_exec"
    assert M.get_backend_name() == "pi"
