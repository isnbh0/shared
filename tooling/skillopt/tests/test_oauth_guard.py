"""Hermetic tests for the OAuth-safety launch wrapper.

Nothing here spawns a real ``claude`` / ``codex`` CLI, execs upstream
``skillopt-train``, or touches a real OAuth session: the probe is injected, the
Keychain ``platform`` / ``subprocess`` seams are monkeypatched, credential lookups
are pointed at ``tmp_path``, and ``exec_fn`` is a recording stub.
"""
from __future__ import annotations

import json
import signal
import subprocess

import pytest

from skillopt_oauth import oauth_guard
from skillopt_oauth.oauth_guard import (
    OAuthPreflightError,
    build_record,
    configure_backends,
    extract_out_root,
    main,
    preflight,
    redact_argv,
    resolve_target,
    scrub_env,
    write_record,
)

# All 8 secret flags enumerated from upstream ``scripts/train.py``.
_SECRET_FLAGS = [
    "--azure_api_key",
    "--azure_openai_api_key",
    "--optimizer_azure_openai_api_key",
    "--target_azure_openai_api_key",
    "--qwen_chat_api_key",
    "--optimizer_qwen_chat_api_key",
    "--target_qwen_chat_api_key",
    "--minimax_api_key",
]


def _read_records(tmp_path):
    """Read the JSONL decision records the autouse fixture redirects into tmp_path."""
    f = tmp_path / "records" / "runs.jsonl"
    if not f.exists():
        return []
    return [json.loads(line) for line in f.read_text().splitlines() if line.strip()]


def _boom_redact(_argv):
    raise RuntimeError("redaction blew up")


class _FakeProc:
    """A subprocess.Popen stand-in for hermetic supervise tests."""

    def __init__(self, *, returncode=0, wait_raises=None, on_wait_signal=None, pid=None):
        self.returncode = returncode
        self._wait_raises = wait_raises
        self._on_wait_signal = on_wait_signal
        self.signals: list[int] = []
        # Default pid=None makes _signal_child skip the os.killpg group path and use
        # send_signal, so the forwarding test is deterministic with no real OS call.
        self.pid = pid

    def send_signal(self, signum):
        self.signals.append(signum)

    def wait(self):
        if self._on_wait_signal is not None:
            # simulate a signal arriving mid-run by invoking the handler the
            # supervisor installed for it.
            handler = signal.getsignal(self._on_wait_signal)
            handler(self._on_wait_signal, None)  # type: ignore[operator]
        if self._wait_raises is not None:
            raise self._wait_raises
        return self.returncode


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
    # ...and the child carries the correlation run_id.
    assert rec.env["SKILLOPT_OAUTH_RUN_ID"]


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


# -- argv redaction (security-critical) ------------------------------------ #


@pytest.mark.parametrize("flag", _SECRET_FLAGS)
def test_redact_known_secret_flag_space_form(flag):
    out = redact_argv([flag, "sk-SECRET", "--config", "x.yaml"])
    assert out == [flag, "<redacted>", "--config", "x.yaml"]


@pytest.mark.parametrize("flag", _SECRET_FLAGS)
def test_redact_known_secret_flag_eq_form(flag):
    out = redact_argv([f"{flag}=sk-SECRET", "--config", "x.yaml"])
    assert out == [f"{flag}=<redacted>", "--config", "x.yaml"]


@pytest.mark.parametrize("argv,expected", [
    # H1: allow_abbrev=True means abbreviations are valid secret passes.
    (["--azure_api_k", "sk-x"], ["--azure_api_k", "<redacted>"]),
    (["--minimax_api", "sk-x"], ["--minimax_api", "<redacted>"]),
    (["--azure_api_k=sk-x"], ["--azure_api_k=<redacted>"]),
])
def test_redact_abbreviations(argv, expected):
    assert redact_argv(argv) == expected


@pytest.mark.parametrize("argv", [
    ["--qwen_chat_max_tokens", "4096"],
    ["--rewrite_max_completion_tokens", "100"],
    ["--claude_code_exec_max_thinking_tokens", "50"],
])
def test_redact_numeric_denylist_left_intact(argv):
    assert redact_argv(argv) == argv


@pytest.mark.parametrize("argv,expected", [
    # forward-compat heuristic for secrets upstream may add later.
    (["--newvendor_api_key", "sk-x"], ["--newvendor_api_key", "<redacted>"]),
    (["--service_access_token", "tok"], ["--service_access_token", "<redacted>"]),
    (["--client_oauth_token", "tok"], ["--client_oauth_token", "<redacted>"]),
    (["--db_password", "hunter2"], ["--db_password", "<redacted>"]),
    (["--vault_secret", "s"], ["--vault_secret", "<redacted>"]),
    (["--gcp_credential", "c"], ["--gcp_credential", "<redacted>"]),
])
def test_redact_heuristic_fallback(argv, expected):
    assert redact_argv(argv) == expected


def test_redact_secret_flag_as_last_token_does_not_crash():
    out = redact_argv(["--config", "x.yaml", "--azure_api_key"])
    assert out == ["--config", "x.yaml", "--azure_api_key"]  # nothing to redact


def test_redact_is_non_mutating():
    live = ["--azure_api_key", "sk-x"]
    out = redact_argv(live)
    assert live == ["--azure_api_key", "sk-x"]  # original verbatim
    assert out == ["--azure_api_key", "<redacted>"]
    assert out is not live


# -- out_root extraction --------------------------------------------------- #


@pytest.mark.parametrize("argv,expected", [
    (["--out_root", "/tmp/foo"], "/tmp/foo"),
    (["--out_root=/tmp/bar"], "/tmp/bar"),
    (["--config", "x.yaml"], None),
    (["--out_root"], None),  # dangling, no value
])
def test_extract_out_root(argv, expected):
    assert extract_out_root(argv) == expected


# -- build_record (pure) --------------------------------------------------- #


def test_build_record_deterministic_and_names_only():
    kw = dict(
        event="handoff", run_id="rid", ts="2026-01-01T00:00:00Z", provider="claude",
        verdict="oauth", probe_name="default_oauth_probe",
        src_env={"PATH": "/bin", "ANTHROPIC_API_KEY": "sk-SECRET"},
        child_env={"PATH": "/bin"},
        routing={"TARGET_BACKEND": "claude_code_exec"},
        argv=["--config", "x.yaml"], resolved_path="/bin/skillopt-train",
        out_root_arg=None, out_root_injected=False,
    )
    r1 = build_record(**kw)
    r2 = build_record(**kw)
    assert r1 == r2  # deterministic given injected ts + run_id
    assert r1["run_id"] == "rid"
    assert r1["ts"] == "2026-01-01T00:00:00Z"
    assert r1["schema_version"] == oauth_guard.SCHEMA_VERSION
    # scrubbed_keys are NAMES only, sorted; never the value.
    assert r1["scrubbed_keys"] == ["ANTHROPIC_API_KEY"]
    assert "sk-SECRET" not in json.dumps(r1)


def test_build_record_verdict_present_on_refused():
    r = build_record(
        event="refused", run_id="r", ts="t", provider="codex", verdict="none",
        probe_name="p", src_env={}, child_env={}, routing={},
        argv=["--config", "x.yaml"], resolved_path=None,
        out_root_arg=None, out_root_injected=False,
    )
    assert r["preflight"]["verdict"] == "none"


def test_build_record_redaction_failure_yields_sentinel(monkeypatch):
    monkeypatch.setattr(oauth_guard, "redact_argv", _boom_redact)
    r = build_record(
        event="handoff", run_id="r", ts="t", provider="claude", verdict="oauth",
        probe_name="p", src_env={}, child_env={}, routing={},
        argv=["--azure_api_key", "sk-SECRET"], resolved_path=None,
        out_root_arg=None, out_root_injected=False,
    )
    assert r["argv_redacted"] == ["<argv-redaction-failed>"]  # never the raw value
    assert "sk-SECRET" not in json.dumps(r)


def test_build_record_extra_fields_merge():
    r = build_record(
        event="completed", run_id="r", ts="t", provider="claude", verdict="oauth",
        probe_name="p", src_env={}, child_env={}, routing={},
        argv=[], resolved_path=None, out_root_arg=None, out_root_injected=False,
        exit_code=0, duration_s=1.5, end_ts="t2",
    )
    assert r["exit_code"] == 0 and r["duration_s"] == 1.5 and r["end_ts"] == "t2"


# -- write_record (the only I/O; fail-soft) -------------------------------- #


def test_write_record_appends_valid_jsonl(tmp_path):
    d = str(tmp_path / "recs")
    write_record({"a": 1}, log_dir=d, enabled=True)
    write_record({"a": 2}, log_dir=d, enabled=True)
    lines = (tmp_path / "recs" / "runs.jsonl").read_text().splitlines()
    assert [json.loads(x) for x in lines] == [{"a": 1}, {"a": 2}]


def test_write_record_disabled_writes_nothing(tmp_path):
    d = str(tmp_path / "recs")
    write_record({"a": 1}, log_dir=d, enabled=False)
    assert not (tmp_path / "recs").exists()


def test_write_record_unwritable_dir_warns_and_returns(tmp_path):
    blocker = tmp_path / "afile"
    blocker.write_text("x")  # a FILE where a dir component is expected
    d = str(blocker / "sub")
    # must not raise -- launch proceeds even if the record can't be written.
    write_record({"a": 1}, log_dir=d, enabled=True)
    assert not (blocker / "sub").exists()


def test_write_record_single_newline_terminated_line(tmp_path):
    d = str(tmp_path / "recs")
    write_record({"a": 1}, log_dir=d, enabled=True)
    content = (tmp_path / "recs" / "runs.jsonl").read_bytes()
    assert content.endswith(b"\n")
    assert content.count(b"\n") == 1  # exactly one os.write of one line


# -- main(): event records ------------------------------------------------- #


def test_main_refused_records_verdict(tmp_path):
    rec = _RecordingExec()
    rc = main(["--config", "x.yaml"], probe=lambda _p: "api_key", exec_fn=rec,
              now=lambda: "t", run_id_fn=lambda: "rid")
    assert rc == 2
    assert rec.called is False  # never handed off
    records = _read_records(tmp_path)
    assert [r["event"] for r in records] == ["refused"]
    assert records[0]["preflight"]["verdict"] == "api_key"
    assert records[0]["scrubbed_keys"] == []  # no scrub on refusal
    assert records[0]["run_id"] == "rid"


def test_main_handoff_record_has_run_id_and_scrub(tmp_path, monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-SECRET")
    rec = _RecordingExec()
    user_args = ["--config", "x.yaml", "--backend", "claude_code_exec"]
    main(user_args, probe=lambda _p: "oauth", exec_fn=rec,
         now=lambda: "t", run_id_fn=lambda: "rid")
    records = _read_records(tmp_path)
    assert [r["event"] for r in records] == ["handoff"]  # exactly one line
    r = records[0]
    assert r["run_id"] == "rid"
    assert "ANTHROPIC_API_KEY" in r["scrubbed_keys"]  # name only
    # live argv passed through verbatim; child env scrubbed + carries run_id.
    assert rec.args == ["skillopt-train", *user_args]
    assert "ANTHROPIC_API_KEY" not in rec.env
    assert rec.env["SKILLOPT_OAUTH_RUN_ID"] == "rid"


def test_main_exec_failure_records_two_lines_same_run_id(tmp_path):
    def _boom_exec(file, args, env):
        raise OSError("skillopt-train not on PATH")

    rc = main(["--config", "x.yaml"], probe=lambda _p: "oauth", exec_fn=_boom_exec,
              now=lambda: "t", run_id_fn=lambda: "rid")
    assert rc == 127
    records = _read_records(tmp_path)
    assert [r["event"] for r in records] == ["handoff", "exec_failed"]
    assert records[0]["run_id"] == records[1]["run_id"] == "rid"
    assert records[1]["error"]  # guard's own OSError text (verified secret-free)


def test_main_dry_run_prints_delta_and_does_not_exec(tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("SKILLOPT_OAUTH_DRY_RUN", "1")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-SECRET")
    rec = _RecordingExec()
    rc = main(["--config", "x.yaml"], probe=lambda _p: "oauth", exec_fn=rec,
              now=lambda: "t", run_id_fn=lambda: "rid")
    assert rc == 0
    assert rec.called is False  # never exec'd
    out = capsys.readouterr().out
    assert "dry-run" in out
    assert "skillopt-train" in out
    assert "ANTHROPIC_API_KEY" in out  # env delta lists the removed name...
    assert "sk-SECRET" not in out      # ...but never the value
    assert [r["event"] for r in _read_records(tmp_path)] == ["dry_run"]


def test_main_dry_run_takes_precedence_over_supervise(tmp_path, monkeypatch):
    monkeypatch.setenv("SKILLOPT_OAUTH_DRY_RUN", "1")
    monkeypatch.setenv("SKILLOPT_OAUTH_SUPERVISE", "1")
    rec = _RecordingExec()
    rc = main(["--config", "x.yaml"], probe=lambda _p: "oauth", exec_fn=rec,
              now=lambda: "t", run_id_fn=lambda: "rid")
    assert rc == 0
    assert [r["event"] for r in _read_records(tmp_path)] == ["dry_run"]


def test_main_out_root_recorded_when_passed(tmp_path):
    rec = _RecordingExec()
    main(["--config", "x.yaml", "--out_root", "/tmp/foo"], probe=lambda _p: "oauth",
         exec_fn=rec, now=lambda: "t", run_id_fn=lambda: "rid")
    up = _read_records(tmp_path)[0]["upstream"]
    assert up["out_root_arg"] == "/tmp/foo"
    assert up["out_root_injected"] is False


def test_main_out_root_null_when_absent(tmp_path):
    rec = _RecordingExec()
    main(["--config", "x.yaml"], probe=lambda _p: "oauth", exec_fn=rec,
         now=lambda: "t", run_id_fn=lambda: "rid")
    up = _read_records(tmp_path)[0]["upstream"]
    assert up["out_root_arg"] is None
    assert up["out_root_injected"] is False


def test_main_out_root_injected_when_opt_in(tmp_path, monkeypatch):
    monkeypatch.setenv("SKILLOPT_OAUTH_INJECT_OUT_ROOT", "1")
    rec = _RecordingExec()
    main(["--config", "x.yaml"], probe=lambda _p: "oauth", exec_fn=rec,
         now=lambda: "t", run_id_fn=lambda: "rid")
    up = _read_records(tmp_path)[0]["upstream"]
    assert up["out_root_injected"] is True
    assert "rid" in up["out_root_arg"]
    # the injected flag also reaches the live argv handed to exec.
    assert rec.args[-2:] == ["--out_root", up["out_root_arg"]]


def test_main_log_disabled_no_file_but_stderr_emits(tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("SKILLOPT_OAUTH_LOG", "0")
    rec = _RecordingExec()
    main(["--config", "x.yaml"], probe=lambda _p: "oauth", exec_fn=rec,
         now=lambda: "t", run_id_fn=lambda: "rid")
    assert _read_records(tmp_path) == []  # file write suppressed
    err = capsys.readouterr().err
    assert "skillopt-oauth:" in err  # the stderr line is the contract -> still emits
    assert "rid" in err


# -- main(): supervise (opt-in completion record) -------------------------- #


def test_supervise_forwards_signal_once_and_returns_code():
    proc = _FakeProc(returncode=0, on_wait_signal=signal.SIGINT)
    rc = oauth_guard._supervise(
        ["skillopt-train"], {},
        run_fn=lambda argv, env: proc,
    )
    assert proc.signals == [signal.SIGINT]  # forwarded exactly once
    assert rc == 0


def test_supervise_returns_signal_aware_exit_code():
    proc = _FakeProc(returncode=-signal.SIGINT)  # child killed by SIGINT
    rc = oauth_guard._supervise(
        ["skillopt-train"], {},
        run_fn=lambda argv, env: proc,
    )
    assert rc == 128 + signal.SIGINT


def test_main_supervise_writes_handoff_then_completed(tmp_path, monkeypatch):
    proc = _FakeProc(returncode=0)
    monkeypatch.setattr(oauth_guard.subprocess, "Popen",
                        lambda argv, **kwargs: proc)
    rec = _RecordingExec()
    rc = main(["--config", "x.yaml", "--backend", "claude_code_exec"],
              probe=lambda _p: "oauth", exec_fn=rec, now=lambda: "t",
              run_id_fn=lambda: "rid", supervise=True)
    assert rc == 0
    assert rec.called is False  # supervised, not exec'd
    records = _read_records(tmp_path)
    assert [r["event"] for r in records] == ["handoff", "completed"]
    assert records[0]["run_id"] == records[1]["run_id"] == "rid"
    completed = records[1]
    assert completed["exit_code"] == 0
    assert completed["duration_s"] >= 0
    assert "end_ts" in completed


def test_main_supervise_handoff_survives_parent_kill(tmp_path, monkeypatch):
    proc = _FakeProc(wait_raises=KeyboardInterrupt())  # parent interrupted mid-run
    monkeypatch.setattr(oauth_guard.subprocess, "Popen",
                        lambda argv, **kwargs: proc)
    with pytest.raises(KeyboardInterrupt):
        main(["--config", "x.yaml"], probe=lambda _p: "oauth", now=lambda: "t",
             run_id_fn=lambda: "rid", supervise=True)
    # the handoff was written BEFORE the spawn, so a kill still leaves a trace.
    assert [r["event"] for r in _read_records(tmp_path)] == ["handoff"]


# -- secret-leak audit: no secret VALUE in any record line or stderr ------- #


def test_no_secret_values_leak_across_all_paths(tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-anthropic-SECRET")
    monkeypatch.setenv("OPENAI_API_KEY", "sk-openai-SECRET")
    cases = [
        (["--config", "x.yaml", "--azure_api_key", "sk-azure-SECRET"], "oauth"),
        (["--azure_api_k", "sk-abbrev-SECRET", "--backend", "claude_code_exec"], "oauth"),
        (["--minimax_api", "sk-mini-SECRET"], "oauth"),
        (["--target_qwen_chat_api_key=sk-eq-SECRET"], "oauth"),
        # bare key=value via upstream's preferred --cfg-options channel (dotted + flat)
        (["--cfg-options", "model.azure_api_key=sk-cfg-SECRET"], "oauth"),
        (["--cfg-options", "optimizer.api_key=sk-cfgflat-SECRET", "--config", "x"], "oauth"),
        # eq directly on the --cfg-options option (single token)
        (["--cfg-options=model.azure_api_key=sk-cfgeq-SECRET"], "oauth"),
        # secret-term flag that also ends in a numeric-denylist suffix
        (["--password_max_tokens", "sk-deny-SECRET"], "oauth"),
        # value that itself starts with -- (only valid via eq form)
        (["--azure_api_key=--sk-dash-SECRET"], "oauth"),
        (["--config", "x.yaml"], "none"),  # refused path
    ]
    for argv, verdict in cases:
        main(argv, probe=lambda _p, v=verdict: v, exec_fn=_RecordingExec(),
             now=lambda: "t", run_id_fn=lambda: "rid")
    # exec_failed path: a PATH-resolved path in the exception must not leak.
    def _boom_exec(file, args, env):
        exc = FileNotFoundError(2, "No such file or directory")
        exc.filename = "/tmp/sk-path-SECRET/skillopt-train"
        raise exc
    main(["--config", "x"], probe=lambda _p: "oauth", exec_fn=_boom_exec,
         now=lambda: "t", run_id_fn=lambda: "rid")
    # pathological env NAME embedding a secret (only names are recorded).
    monkeypatch.setenv("LEAK_sk-name-SECRET_API_KEY", "v")
    main(["--config", "x"], probe=lambda _p: "oauth", exec_fn=_RecordingExec(),
         now=lambda: "t", run_id_fn=lambda: "rid")
    # redaction-failure path: the sentinel must appear, the raw value must not.
    monkeypatch.setattr(oauth_guard, "redact_argv", _boom_redact)
    main(["--azure_api_key", "sk-fail-SECRET"], probe=lambda _p: "oauth",
         exec_fn=_RecordingExec(), now=lambda: "t", run_id_fn=lambda: "rid")

    captured = capsys.readouterr()
    record_text = (tmp_path / "records" / "runs.jsonl").read_text()
    blob = record_text + captured.err + captured.out
    for needle in ("SECRET", "sk-azure", "sk-abbrev", "sk-mini", "sk-eq", "sk-cfg",
                   "sk-cfgflat", "sk-cfgeq", "sk-deny", "sk-dash", "sk-path",
                   "sk-name", "sk-fail", "sk-anthropic", "sk-openai"):
        assert needle not in blob, f"secret leaked: {needle!r}"


# -- redaction: --cfg-options bare key=value + denylist collision ----------- #


@pytest.mark.parametrize("argv,expected", [
    (["--cfg-options", "model.azure_api_key=sk-x"],
     ["--cfg-options", "model.azure_api_key=<redacted>"]),
    (["--cfg-options", "optimizer.api_key=sk-x", "--config", "y"],
     ["--cfg-options", "optimizer.api_key=<redacted>", "--config", "y"]),
    (["--cfg-options", "model.target_qwen_chat_api_key=sk-x"],
     ["--cfg-options", "model.target_qwen_chat_api_key=<redacted>"]),
    # eq directly on the option (single token, valid via argparse nargs="+"):
    # the secret is keyed by the value's own k=v, not by --cfg-options.
    (["--cfg-options=model.azure_api_key=sk-x"],
     ["--cfg-options=model.azure_api_key=<redacted>"]),
])
def test_redact_cfg_options_bare_key_value(argv, expected):
    assert redact_argv(argv) == expected


@pytest.mark.parametrize("argv", [
    ["--cfg-options", "model.qwen_chat_max_tokens=4096"],
    ["--cfg-options", "model.rewrite_max_completion_tokens=100"],
])
def test_redact_cfg_options_numeric_left_intact(argv):
    assert redact_argv(argv) == argv  # bias to over-redact must not hit integers


@pytest.mark.parametrize("argv,expected", [
    # secret term wins over the numeric denylist suffix (forward-compat).
    (["--password_max_tokens", "sk-x"], ["--password_max_tokens", "<redacted>"]),
    (["--credential_completion_tokens", "sk-x"], ["--credential_completion_tokens", "<redacted>"]),
    (["--secret_max_tokens", "sk-x"], ["--secret_max_tokens", "<redacted>"]),
])
def test_redact_secret_term_beats_numeric_denylist(argv, expected):
    assert redact_argv(argv) == expected


def test_redact_adjacent_secret_flags_does_not_leak_trailing_value():
    # The first flag's "value" is itself a flag -> argparse rejects it; we must not
    # consume it and desync, leaving the real trailing value un-redacted.
    out = redact_argv(["--azure_api_key", "--minimax_api_key", "sk-TRAIL"])
    assert out == ["--azure_api_key", "--minimax_api_key", "<redacted>"]


def test_redact_dash_starting_value_via_eq_form():
    # A secret value that itself starts with -- is only valid via the eq form.
    assert redact_argv(["--azure_api_key=--sk-x"]) == ["--azure_api_key=<redacted>"]


# -- resolve_target: abbreviation + target precedence + last-wins ----------- #


@pytest.mark.parametrize("argv,expected", [
    (["--back", "codex_exec"], "codex"),                       # allow_abbrev
    (["--target_back", "codex_exec"], "codex"),
    (["--back=codex_exec"], "codex"),
    (["--backend", "claude_code_exec", "--target_backend", "codex_exec"], "codex"),  # target wins
    (["--backend", "claude_code_exec", "--backend", "codex_exec"], "codex"),         # last wins
    (["--target_backend", "codex_exec", "--target_backend", "claude_code_exec"], "claude"),
])
def test_resolve_target_argparse_faithful(argv, expected):
    assert resolve_target(argv, environ={}) == expected


def test_main_routes_codex_via_abbreviation(tmp_path):
    rec = _RecordingExec()
    main(["--back", "codex_exec"], probe=lambda _p: "oauth", exec_fn=rec,
         now=lambda: "t", run_id_fn=lambda: "rid")
    assert rec.env["TARGET_BACKEND"] == "codex_exec"
    assert _read_records(tmp_path)[0]["provider"] == "codex"


# -- extract_out_root: argparse-faithful ------------------------------------ #


@pytest.mark.parametrize("argv,expected", [
    (["--out_root", "a", "--out_root", "b"], "b"),     # last wins
    (["--out_root", "--config"], None),                # dangling -> no value
    (["--out_ro", "/d"], "/d"),                        # abbreviation
    (["--out_root="], ""),                             # explicit empty
])
def test_extract_out_root_argparse_faithful(argv, expected):
    assert extract_out_root(argv) == expected


# -- build_record hardening ------------------------------------------------- #


def test_build_record_reserved_fields_beat_extra():
    rec = build_record(
        event="completed", run_id="RID", ts="t", provider="claude", verdict="oauth",
        probe_name="p", src_env={}, child_env={}, routing={}, argv=[],
        resolved_path=None, out_root_arg=None, out_root_injected=False,
        schema_version=999, cwd="HACK", exit_code=3,  # extra can't clobber reserved
    )
    assert rec["schema_version"] == oauth_guard.SCHEMA_VERSION
    assert rec["cwd"] != "HACK"
    assert rec["exit_code"] == 3  # genuine event-specific extra still lands


def test_build_record_sanitizes_non_identifier_env_name():
    rec = build_record(
        event="handoff", run_id="r", ts="t", provider="claude", verdict="oauth",
        probe_name="p", src_env={"LEAK_sk-SECRET_API_KEY": "v", "ANTHROPIC_API_KEY": "v"},
        child_env={}, routing={}, argv=[], resolved_path=None,
        out_root_arg=None, out_root_injected=False,
    )
    assert "ANTHROPIC_API_KEY" in rec["scrubbed_keys"]       # canonical name kept
    assert "<non-identifier-key>" in rec["scrubbed_keys"]    # secret-bearing name redacted
    assert "sk-SECRET" not in __import__("json").dumps(rec)


def test_build_record_cwd_failsoft(monkeypatch):
    def _raise():
        raise FileNotFoundError(2, "cwd gone")
    monkeypatch.setattr(oauth_guard.os, "getcwd", _raise)
    rec = build_record(
        event="handoff", run_id="r", ts="t", provider="claude", verdict="oauth",
        probe_name="p", src_env={}, child_env={}, routing={}, argv=[],
        resolved_path=None, out_root_arg=None, out_root_injected=False,
    )
    assert rec["cwd"] is None  # deleted cwd never raises into the record build


def test_default_log_dir_failsoft_falls_back_to_home(monkeypatch):
    monkeypatch.delenv("SKILLOPT_OAUTH_LOG_DIR", raising=False)
    monkeypatch.setattr(oauth_guard.os, "getcwd",
                        lambda: (_ for _ in ()).throw(OSError("cwd gone")))
    monkeypatch.setenv("HOME", "/home/x")
    assert oauth_guard._default_log_dir() == "/home/x/.agent-workspace/skillopt-oauth"


# -- write_record hardening ------------------------------------------------- #


def test_write_record_non_serializable_is_failsoft(tmp_path):
    write_record({"bad": object()}, log_dir=str(tmp_path / "recs"), enabled=True)  # no raise
    assert not (tmp_path / "recs" / "runs.jsonl").exists()


def test_write_record_does_not_follow_symlink(tmp_path):
    d = tmp_path / "recs"
    d.mkdir()
    target = tmp_path / "secret.txt"
    target.write_text("orig")
    (d / "runs.jsonl").symlink_to(target)
    write_record({"a": 1}, log_dir=str(d), enabled=True)  # O_NOFOLLOW -> fail-soft
    assert target.read_text() == "orig"  # never appended through the planted symlink


def test_write_record_tightens_existing_permissive_file(tmp_path):
    import os
    import stat
    d = tmp_path / "recs"
    d.mkdir()
    f = d / "runs.jsonl"
    f.write_text("")
    os.chmod(f, 0o644)
    write_record({"a": 1}, log_dir=str(d), enabled=True)
    assert stat.S_IMODE(os.stat(f).st_mode) == 0o600  # fchmod tightened it


# -- exec_failed / supervise spawn failure: sanitized + symmetric ----------- #


def test_main_exec_failed_sanitizes_exception(tmp_path):
    def _boom_exec(file, args, env):
        exc = FileNotFoundError(2, "No such file or directory")
        exc.filename = "/tmp/sk-PATH-SECRET/skillopt-train"
        raise exc

    rc = main(["--config", "x"], probe=lambda _p: "oauth", exec_fn=_boom_exec,
              now=lambda: "t", run_id_fn=lambda: "rid")
    assert rc == 127
    rec = _read_records(tmp_path)[-1]
    assert rec["event"] == "exec_failed"
    assert rec["error"] == "FileNotFoundError(errno=2)"  # class + errno only
    import json as _json
    assert "sk-PATH-SECRET" not in _json.dumps(rec)


def test_main_supervise_spawn_failure_records_exec_failed(tmp_path, monkeypatch):
    def _boom_popen(argv, **kwargs):
        exc = FileNotFoundError(2, "No such file or directory")
        exc.filename = "/tmp/sk-PATH-SECRET/skillopt-train"
        raise exc

    monkeypatch.setattr(oauth_guard.subprocess, "Popen", _boom_popen)
    rc = main(["--config", "x"], probe=lambda _p: "oauth", now=lambda: "t",
              run_id_fn=lambda: "rid", supervise=True)
    assert rc == 127  # symmetric with the exec path, not a crash
    events = [r["event"] for r in _read_records(tmp_path)]
    assert events == ["handoff", "exec_failed"]


def test_main_launch_proceeds_when_cwd_deleted(tmp_path, monkeypatch):
    monkeypatch.setattr(oauth_guard.os, "getcwd",
                        lambda: (_ for _ in ()).throw(FileNotFoundError(2, "gone")))
    rec = _RecordingExec()
    main(["--config", "x"], probe=lambda _p: "oauth", exec_fn=rec,
         now=lambda: "t", run_id_fn=lambda: "rid")
    assert rec.called is True  # launch proceeds despite a deleted cwd
    assert _read_records(tmp_path)[0]["cwd"] is None


def test_main_dry_run_redaction_failure_still_returns_zero(tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("SKILLOPT_OAUTH_DRY_RUN", "1")
    monkeypatch.setattr(oauth_guard, "redact_argv", _boom_redact)
    rec = _RecordingExec()
    rc = main(["--azure_api_key", "sk-SECRET"], probe=lambda _p: "oauth",
              exec_fn=rec, now=lambda: "t", run_id_fn=lambda: "rid")
    assert rc == 0
    assert rec.called is False
    out = capsys.readouterr().out
    assert "argv-redaction-failed" in out  # sentinel, not the raw value
    assert "sk-SECRET" not in out


# -- supervise signal forwarding: process group + fallback ------------------ #


def test_supervise_forwards_to_process_group(monkeypatch):
    proc = _FakeProc(pid=4321, on_wait_signal=signal.SIGTERM)
    calls: list[tuple[int, int]] = []
    monkeypatch.setattr(oauth_guard.os, "getpgid", lambda pid: pid)
    monkeypatch.setattr(oauth_guard.os, "killpg", lambda pgid, sig: calls.append((pgid, sig)))
    rc = oauth_guard._supervise(["p"], {}, run_fn=lambda *_a: proc)
    assert calls == [(4321, signal.SIGTERM)]  # delivered to the whole group
    assert proc.signals == []                 # killpg path, not the direct-child fallback
    assert rc == 0


def test_supervise_send_signal_fallback_when_no_pgid():
    proc = _FakeProc(pid=None, on_wait_signal=signal.SIGINT)  # no pid -> skip killpg
    oauth_guard._supervise(["p"], {}, run_fn=lambda *_a: proc)
    assert proc.signals == [signal.SIGINT]


def test_supervise_send_signal_fallback_when_getpgid_raises(monkeypatch):
    # Real pid but the group lookup fails (e.g. already-reaped) -> direct-child fallback.
    proc = _FakeProc(pid=4321, on_wait_signal=signal.SIGINT)
    monkeypatch.setattr(oauth_guard.os, "getpgid",
                        lambda pid: (_ for _ in ()).throw(ProcessLookupError()))
    oauth_guard._supervise(["p"], {}, run_fn=lambda *_a: proc)
    assert proc.signals == [signal.SIGINT]


# -- redaction residuals (post-hardening) ----------------------------------- #


def test_redact_normalizes_surrounding_whitespace():
    # a cfg-options key with a space before '=' must still be recognized as secret.
    assert redact_argv(["--cfg-options", "model.azure_api_key =sk-x"]) == \
        ["--cfg-options", "model.azure_api_key =<redacted>"]


@pytest.mark.parametrize("argv", [
    ["--cfg-options", "optimizer=claude_chat"],   # prefix of optimizer_..._api_key
    ["--cfg-options", "target=foo"],              # prefix of target_..._api_key
    ["--cfg-options", "azure=x"],
])
def test_redact_bare_cfg_routing_keys_not_over_redacted(argv):
    # The abbreviation/prefix rule applies only to --flags, not bare cfg keys, so
    # legitimate routing facts stay legible in the audit record.
    assert redact_argv(argv) == argv


@pytest.mark.parametrize("flag", ["--session_key", "--bearer_token", "--anthropic_api_token"])
def test_redact_forward_compat_token_key_suffixes(flag):
    assert redact_argv([flag, "sk-x"]) == [flag, "<redacted>"]


def test_redact_space_form_preserves_following_flag():
    # argparse-consistent: a --prefixed next token is the next option, not a value,
    # so it stays legible (not redacted) in the record. A --starting secret VALUE
    # must use the eq form (covered elsewhere).
    assert redact_argv(["--azure_api_key", "--config", "x.yaml"]) == \
        ["--azure_api_key", "--config", "x.yaml"]


def test_print_dry_run_swallows_broken_pipe(monkeypatch, capsys):
    import builtins

    def _broken(*_a, **_k):
        raise BrokenPipeError("closed stdout")

    monkeypatch.setattr(builtins, "print", _broken)
    # must not raise into the launch path even when stdout is gone.
    oauth_guard._print_dry_run("claude", ["--config", "x"], {}, {})
