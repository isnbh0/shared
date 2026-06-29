#!/usr/bin/env python3
"""Hermetic stub CLI emulating the non-interactive ``claude -p`` / ``codex exec`` contract.

It serves as both ``claude_bin`` and ``codex_bin``: claude is invoked as
``stub_cli.py -p <prompt> [--model M]`` and codex as
``stub_cli.py exec -s read-only -c model_reasoning_effort=... [-c model=M] -``
with the prompt on stdin. Behaviour is selected by ``STUB_MODE``:

    rollout    -> canned rollout text, exit 0   (the default)
    patch      -> canned add/delete/replace patch JSON in a fenced block, exit 0
    rate_limit -> usage/rate-limit message on stderr, nonzero exit
    fail       -> generic error on stderr, nonzero exit
    slow       -> sleep STUB_DELAY seconds, then behave like ``rollout``
    auth_warning -> rollout text on stdout + an auth/billing notice on stderr, exit 0
    env_echo   -> print the *_API_KEY / *_AUTH_TOKEN names visible to the child, exit 0
    flaky      -> emit a 429 for the first STUB_FAIL_TIMES calls (tracked in
                  STUB_COUNTER_FILE), then fall through to ``ok`` -- exercises the
                  scheduler's rate-limit backoff/retry across subprocess attempts

Every successful response ends with a model marker line
``[[SKILLOPT_MODEL:<model>]]`` where ``<model>`` is ``STUB_MODEL_OVERRIDE`` if
set, else ``SKILLOPT_MODEL`` (exported by the executor), else ``stub-model``.
This file defines the base contract; later phases may add modes.
"""
import os
import sys
import time

CANNED_ROLLOUT = "stub rollout: 260629-233554-result canned rollout output"

CANNED_PATCH = """Here is the proposed edit:
```json
{
  "rationale": "tighten the wording",
  "edits": [
    {"op": "replace", "target": "Do the thing.", "content": "Do the thing precisely."},
    {"op": "add", "after": "Do the thing precisely.", "content": "Then stop."},
    {"op": "delete", "target": "obsolete line"}
  ]
}
```"""


def _maybe_flaky() -> None:
    """Emit a rate-limit signal for the first STUB_FAIL_TIMES calls, then succeed.

    State is kept in STUB_COUNTER_FILE so successive subprocess invocations of
    the same logical job (scheduler retries) progress fail -> fail -> ok. On the
    success call it rewrites STUB_MODE to "ok" and returns so the normal ok
    dispatch emits the standard model-pinned rollout payload. Keep flaky tests on
    the claude provider: this early-exit runs before codex stdin is drained.
    """
    if os.environ.get("STUB_MODE") != "flaky":
        return
    counter_file = os.environ.get("STUB_COUNTER_FILE")
    fail_times = int(os.environ.get("STUB_FAIL_TIMES", "1"))
    seen = 0
    if counter_file and os.path.exists(counter_file):
        try:
            seen = int((open(counter_file).read().strip() or "0"))
        except ValueError:
            seen = 0
    if seen < fail_times:
        if counter_file:
            open(counter_file, "w").write(str(seen + 1))
        sys.stdout.write("HTTP 429 rate limit exceeded\n")
        sys.exit(1)
    os.environ["STUB_MODE"] = "ok"  # fall through to the standard success path


def detect_provider(argv):
    if "exec" in argv:
        return "codex"
    if "-p" in argv:
        return "claude"
    return "unknown"


def model_marker():
    model = (os.environ.get("STUB_MODEL_OVERRIDE")
             or os.environ.get("SKILLOPT_MODEL")
             or "stub-model")
    return f"[[SKILLOPT_MODEL:{model}]]"


def main():
    _maybe_flaky()  # Phase 3: rate-limit-then-succeed for the retry integration test
    argv = sys.argv[1:]
    provider = detect_provider(argv)

    # codex receives the prompt on stdin; drain it so the parent's pipe closes.
    if provider == "codex":
        try:
            sys.stdin.read()
        except Exception:
            pass

    mode = os.environ.get("STUB_MODE", "rollout")
    if mode == "slow":
        time.sleep(float(os.environ.get("STUB_DELAY", "2.0")))
        mode = "rollout"

    if mode == "rate_limit":
        sys.stderr.write("Error: 429 rate limit exceeded -- usage limit reached. Retry later.\n")
        return int(os.environ.get("STUB_EXIT_CODE", "1"))
    if mode == "fail":
        sys.stderr.write("Error: stub generic failure.\n")
        return int(os.environ.get("STUB_EXIT_CODE", "2"))
    if mode == "auth_warning":
        sys.stderr.write(
            "Notice: ANTHROPIC_API_KEY detected; this request will be billed to "
            "your API credits, not your subscription.\n"
        )
        print(f"PROVIDER:{provider}")
        print(CANNED_ROLLOUT)
        print(model_marker())
        return 0
    if mode == "env_echo":
        leaked = sorted(k for k in os.environ
                        if k.endswith("_API_KEY") or k.endswith("_AUTH_TOKEN"))
        print(f"PROVIDER:{provider}")
        print("LEAKED_KEYS:" + ",".join(leaked))
        print(model_marker())
        return 0

    print(f"PROVIDER:{provider}")
    print(CANNED_PATCH if mode == "patch" else CANNED_ROLLOUT)
    print(model_marker())
    return 0


if __name__ == "__main__":
    sys.exit(main())
