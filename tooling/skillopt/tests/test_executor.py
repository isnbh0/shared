"""Hermetic tests for the OAuth-CLI executor and the oauth_cli backend.

All CLI calls are routed to ``tests/fixtures/stub_cli.py``; nothing here touches
a real OAuth session or the network.
"""
import shutil
from pathlib import Path

import pytest

from skillopt_oauth import backends
from skillopt_oauth.executor import (
    CliResult,
    ExecutorError,
    ModelAssertionError,
    OAuthCLIExecutor,
    OAuthPreflightError,
    PatchParseError,
    PatchSchemaError,
    parse_patch_json,
    validate_patch,
)

MODEL_CLAUDE = "claude-opus-stub"
MODEL_CODEX = "gpt-codex-stub"


@pytest.fixture
def stub(tmp_path):
    """Copy the stub CLI into a temp dir and mark it executable."""
    src = Path(__file__).parent / "fixtures" / "stub_cli.py"
    dest = tmp_path / "stub_cli.py"
    shutil.copy(src, dest)
    dest.chmod(0o755)
    return dest


@pytest.fixture
def executor(stub):
    return OAuthCLIExecutor(
        claude_bin=str(stub), codex_bin=str(stub),
        model_claude=MODEL_CLAUDE, model_codex=MODEL_CODEX,
        reasoning_effort="high", forbid_api_keys=False,  # back-compat: accepted, no-op
        oauth_probe=lambda provider: "oauth",            # hermetic preflight
    )


@pytest.fixture
def candidate_skill(tmp_path):
    skill = tmp_path / "timestamp" / "initial.md"
    skill.parent.mkdir(parents=True)
    skill.write_text("# Candidate skill\nDo the thing.\n", encoding="utf-8")
    return skill


# -- child-env scrubbing --------------------------------------------------


def test_child_env_scrubs_api_keys_from_the_stub(stub, monkeypatch):
    # A stray key in the *parent* must never reach the child process.
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-should-never-reach-child")
    monkeypatch.setenv("ANTHROPIC_AUTH_TOKEN", "tok-should-never-reach-child")
    monkeypatch.setenv("OPENAI_API_KEY", "sk-openai-should-never-reach-child")
    monkeypatch.setenv("STUB_MODE", "env_echo")
    ex = OAuthCLIExecutor(claude_bin=str(stub), codex_bin=str(stub),
                          oauth_probe=lambda provider: "oauth")
    result = ex.run_cli(provider="claude", prompt="run")
    leaked = next(l for l in result.stdout.splitlines() if l.startswith("LEAKED_KEYS:"))
    assert "ANTHROPIC_API_KEY" not in leaked
    assert "ANTHROPIC_AUTH_TOKEN" not in leaked
    assert "OPENAI_API_KEY" not in leaked


def test_child_env_passes_oauth_token_for_claude_only(stub, monkeypatch):
    monkeypatch.setenv("CLAUDE_CODE_OAUTH_TOKEN", "oauth-tok")
    ex = OAuthCLIExecutor(claude_bin=str(stub), codex_bin=str(stub),
                          oauth_probe=lambda provider: "oauth")
    assert ex._build_child_env("claude", "m").get("CLAUDE_CODE_OAUTH_TOKEN") == "oauth-tok"
    assert "CLAUDE_CODE_OAUTH_TOKEN" not in ex._build_child_env("codex", "m")


# -- OAuth preflight ------------------------------------------------------


def test_preflight_passes_with_oauth_probe(stub, monkeypatch):
    monkeypatch.setenv("STUB_MODE", "rollout")
    ex = OAuthCLIExecutor(claude_bin=str(stub), codex_bin=str(stub),
                          model_claude=MODEL_CLAUDE,
                          oauth_probe=lambda provider: "oauth")
    assert ex.run_cli(provider="claude", prompt="run").exit_code == 0


@pytest.mark.parametrize("verdict", ["api_key", "none"])
def test_preflight_fails_closed_without_oauth(stub, verdict):
    ex = OAuthCLIExecutor(claude_bin=str(stub), codex_bin=str(stub),
                          oauth_probe=lambda provider: verdict)
    with pytest.raises(OAuthPreflightError):
        ex.run_cli(provider="claude", prompt="run")


def test_preflight_skipped_when_not_required(stub, monkeypatch):
    monkeypatch.setenv("STUB_MODE", "rollout")
    ex = OAuthCLIExecutor(claude_bin=str(stub), codex_bin=str(stub),
                          require_oauth=False, oauth_probe=lambda provider: "api_key")
    assert ex.run_cli(provider="claude", prompt="run").exit_code == 0


# -- --bare guard ---------------------------------------------------------


def test_build_command_never_includes_bare(executor):
    cmd, _ = executor._build_command("claude", "do it", MODEL_CLAUDE)
    assert "--bare" not in cmd


def test_guard_no_bare_raises(executor):
    with pytest.raises(ExecutorError):
        executor._guard_no_bare([executor.claude_bin, "-p", "x", "--bare"])


# -- auth / billing warning detection -------------------------------------


def test_auth_billing_warning_detected_on_clean_exit(executor, monkeypatch):
    monkeypatch.setenv("STUB_MODE", "auth_warning")
    result = executor.run_cli(provider="claude", prompt="run")
    assert result.exit_code == 0
    assert result.auth_billing_warning is True


def test_clean_run_has_no_auth_billing_warning(executor, monkeypatch):
    monkeypatch.setenv("STUB_MODE", "rollout")
    assert executor.run_cli(provider="claude", prompt="run").auth_billing_warning is False


# -- routing to the stub for both providers -------------------------------


@pytest.mark.parametrize("provider,expected_model", [
    ("claude", MODEL_CLAUDE),
    ("codex", MODEL_CODEX),
])
def test_run_cli_routes_to_stub(executor, monkeypatch, provider, expected_model):
    monkeypatch.setenv("STUB_MODE", "rollout")
    result = executor.run_cli(provider=provider, prompt="run the candidate")
    assert isinstance(result, CliResult)
    assert result.exit_code == 0
    assert f"PROVIDER:{provider}" in result.stdout
    assert "canned rollout output" in result.stdout
    assert result.model_asserted == expected_model
    assert result.duration >= 0.0


def test_run_cli_rejects_unknown_provider(executor):
    with pytest.raises(ValueError):
        executor.run_cli(provider="bard", prompt="x")


# -- model assertion ------------------------------------------------------


def test_model_assertion_mismatch_raises(executor, monkeypatch):
    monkeypatch.setenv("STUB_MODE", "rollout")
    monkeypatch.setenv("STUB_MODEL_OVERRIDE", "some-other-model")
    with pytest.raises(RuntimeError) as excinfo:
        executor.run_cli(provider="claude", prompt="run")
    assert isinstance(excinfo.value, ModelAssertionError)


def test_model_assertion_skipped_when_unpinned(stub, monkeypatch):
    monkeypatch.setenv("STUB_MODE", "rollout")
    unpinned = OAuthCLIExecutor(claude_bin=str(stub), codex_bin=str(stub),
                                forbid_api_keys=False,
                                oauth_probe=lambda provider: "oauth")
    result = unpinned.run_cli(provider="claude", prompt="run")
    # No model pinned -> the executor records whatever the CLI reported.
    assert result.model_asserted == "stub-model"


# -- skill injection ------------------------------------------------------


def test_skill_injection_writes_workspace_file(executor, monkeypatch, tmp_path, candidate_skill):
    monkeypatch.setenv("STUB_MODE", "rollout")
    work = tmp_path / "work"
    work.mkdir()
    executor.run_cli(provider="claude", prompt="run", skill_path=str(candidate_skill),
                     workdir=str(work))
    injected = work / ".agents" / "skills" / "timestamp" / "SKILL.md"
    assert injected.exists()
    assert "Do the thing." in injected.read_text(encoding="utf-8")


# -- timeout is non-raising ----------------------------------------------


def test_timeout_returns_nonzero_without_raising(executor, monkeypatch):
    monkeypatch.setenv("STUB_MODE", "slow")
    monkeypatch.setenv("STUB_DELAY", "5")
    result = executor.run_cli(provider="claude", prompt="run", timeout=0.5)
    assert result.exit_code == 124
    assert result.model_asserted is None


# -- structured-output helpers -------------------------------------------


GOOD_PROSE = (
    "Sure, here is the patch you asked for.\n"
    '{"edits": [{"op": "replace", "target": "a", "content": "b"}]}\n'
    "Hope that helps!"
)

GOOD_FENCED = (
    "```json\n"
    '{"edits": [{"op": "add", "content": "new line"}]}\n'
    "```\n"
)


def test_parse_patch_json_from_prose():
    obj = parse_patch_json(GOOD_PROSE)
    assert obj["edits"][0]["op"] == "replace"


def test_parse_patch_json_from_fenced_block():
    obj = parse_patch_json(GOOD_FENCED)
    assert obj["edits"][0]["content"] == "new line"


def test_parse_patch_json_malformed_raises():
    with pytest.raises(PatchParseError):
        parse_patch_json("no json anywhere in this output")


def test_parse_patch_json_repair_hook_on_missing_json():
    repaired = '{"edits": [{"op": "delete", "target": "x"}]}'
    obj = parse_patch_json("garbage with no object", repair=lambda _stdout: repaired)
    assert obj["edits"][0]["op"] == "delete"


def test_parse_patch_json_repair_hook_on_bad_schema():
    bad = '{"edits": [{"op": "frobnicate"}]}'
    good = '{"edits": [{"op": "add", "content": "ok"}]}'
    obj = parse_patch_json(bad, repair=lambda _stdout: good)
    assert obj["edits"][0]["op"] == "add"


def test_validate_patch_rejects_bad_op():
    with pytest.raises(PatchSchemaError):
        validate_patch({"edits": [{"op": "frobnicate"}]})


def test_validate_patch_rejects_missing_field():
    with pytest.raises(PatchSchemaError):
        validate_patch({"edits": [{"op": "replace", "target": "a"}]})  # no content


def test_validate_patch_rejects_non_object():
    with pytest.raises(PatchSchemaError):
        validate_patch(["not", "a", "dict"])


# -- backend wiring -------------------------------------------------------


def test_register_oauth_cli_backend_factory(stub):
    backends.register_oauth_cli_backend(claude_bin=str(stub), codex_bin=str(stub),
                                        forbid_api_keys=False)
    factory = backends.get_backend()
    ex = factory()
    assert isinstance(ex, OAuthCLIExecutor)
    assert ex.claude_bin == str(stub)


def test_register_oauth_cli_backend_into_registry(stub):
    registry = {}
    backends.register_oauth_cli_backend(registry=registry, forbid_api_keys=False)
    assert backends.BACKEND_NAME in registry


def test_run_rollout_funnels_to_executor(executor, monkeypatch):
    monkeypatch.setenv("STUB_MODE", "rollout")
    result = backends.run_rollout(executor, prompt="run", provider="claude")
    assert result.exit_code == 0
    assert "canned rollout output" in result.stdout


def test_run_reflect_returns_validated_patch(executor, monkeypatch):
    monkeypatch.setenv("STUB_MODE", "patch")
    patch = backends.run_reflect(executor, prompt="reflect", provider="codex")
    ops = [e["op"] for e in patch["edits"]]
    assert ops == ["replace", "add", "delete"]


class _SpyExecutor:
    """Executor stand-in that records whether the CLI was invoked."""

    def __init__(self, result=None):
        self.calls = 0
        self._result = result

    def run_cli(self, **kwargs):
        self.calls += 1
        if self._result is None:
            raise AssertionError("run_cli must not be called when a scorer is available")
        return self._result


def test_run_judge_prefers_deterministic_scorer():
    spy = _SpyExecutor()  # raises if run_cli is called
    task = {"id": "t1"}

    def scorer(t, _rollout):
        return {"id": t["id"], "hard": 1, "soft": 1.0}

    out = backends.run_judge(spy, task=task, rollout={"id": "t1", "stdout": "anything"},
                             scorer=scorer)
    assert out == {"id": "t1", "hard": 1, "soft": 1.0}
    assert spy.calls == 0


def test_run_judge_calls_cli_when_forced():
    canned = CliResult('{"hard": 1, "soft": 0.9}', 0, 0.0, "m")
    spy = _SpyExecutor(result=canned)
    out = backends.run_judge(spy, task={"id": "t2"}, rollout={"id": "t2", "stdout": "x"},
                             scorer=lambda *_: {}, force_llm=True, prompt="rubric")
    assert out == {"id": "t2", "hard": 1, "soft": 0.9}
    assert spy.calls == 1
