"""The vendored skillopt fork adds a ``codex_chat`` optimizer backend so the
optimizer (reflect/rewrite) role can run on the codex CLI subscription, the same
way ``claude_chat`` already runs the optimizer on the claude CLI.

These tests verify the wiring on the *live* dispatcher (``skillopt.model``) without
spawning ``codex`` — the subprocess shim is mocked, so they spend nothing.
"""
from __future__ import annotations

import pytest

import skillopt.model as M
from skillopt.model import backend_config as BC
from skillopt.model import codex_backend as C
from skillopt.model.backend_config import (
    get_optimizer_backend,
    is_optimizer_chat_backend,
    set_optimizer_backend,
)
from skillopt.model.common import default_model_for_backend, normalize_backend_name


@pytest.fixture(autouse=True)
def _isolate_backend_state():
    """Restore the global optimizer backend/deployment so a case can't leak into
    the wrapper suite (set_optimizer_backend mutates module globals + os.environ)."""
    saved_backend = BC.OPTIMIZER_BACKEND
    saved_deployment = C.OPTIMIZER_DEPLOYMENT
    M.reset_token_tracker()
    yield
    BC.OPTIMIZER_BACKEND = saved_backend
    C.OPTIMIZER_DEPLOYMENT = saved_deployment
    M.reset_token_tracker()


@pytest.fixture
def fake_codex(monkeypatch):
    """Replace the codex subprocess so no real ``codex exec`` runs."""
    seen: dict = {"calls": 0}

    def fake_run(*, model, prompt, attachments, output_schema, timeout):
        seen["model"] = model
        seen["prompt"] = prompt
        seen["calls"] += 1
        return ("REWRITTEN", {"prompt_tokens": 10, "completion_tokens": 5, "total_tokens": 15})

    monkeypatch.setattr(C, "_run_codex_exec", fake_run)
    return seen


def test_allowlist_accepts_codex_chat():
    # Previously raised ValueError — codex was target-only.
    set_optimizer_backend("codex_chat")
    assert get_optimizer_backend() == "codex_chat"
    assert is_optimizer_chat_backend() is True


def test_codex_chat_normalizes_and_has_default_model():
    assert normalize_backend_name("codex_chat") == "codex_chat"
    assert default_model_for_backend("codex_chat") == "gpt-5.5"


def test_exec_token_stays_target_only():
    # The optimizer token is codex_chat; the exec backend remains target-only.
    with pytest.raises(ValueError):
        set_optimizer_backend("codex_exec")
    with pytest.raises(ValueError):
        set_optimizer_backend("codex")


def test_set_optimizer_deployment_reaches_codex():
    M.set_optimizer_deployment("gpt-5.5")
    assert C.OPTIMIZER_DEPLOYMENT == "gpt-5.5"


def test_chat_optimizer_dispatches_to_codex(fake_codex):
    set_optimizer_backend("codex_chat")
    M.set_optimizer_deployment("gpt-5.5")
    out, usage = M.chat_optimizer(system="You optimize prompts.", user="Improve this skill.")
    assert out == "REWRITTEN"
    assert fake_codex["model"] == "gpt-5.5"
    assert usage["total_tokens"] == 15


def test_chat_optimizer_messages_dispatches_to_codex(fake_codex):
    set_optimizer_backend("codex_chat")
    out, _usage = M.chat_optimizer_messages(messages=[{"role": "user", "content": "hi"}])
    assert out == "REWRITTEN"
    assert fake_codex["calls"] == 1


def test_codex_tokens_not_double_counted(fake_codex):
    # codex_backend shares common.tracker with claude_backend; the merge in
    # get_token_summary must count each codex call once, not twice.
    set_optimizer_backend("codex_chat")
    M.chat_optimizer(system="s", user="u")
    M.chat_optimizer(system="s", user="u")
    summary = M.get_token_summary()
    assert summary["_total"]["calls"] == 2
    assert summary["_total"]["total_tokens"] == 30


def test_claude_chat_optimizer_still_selectable():
    # Regression: the existing dispatch branches are untouched.
    set_optimizer_backend("claude_chat")
    assert get_optimizer_backend() == "claude_chat"
