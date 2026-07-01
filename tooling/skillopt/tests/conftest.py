"""Shared fixtures keeping the OAuth-guard tests hermetic.

The guard now writes a JSONL decision record per ``main()`` invocation. Left to its
default the record lands in a cwd-relative ``.agent-workspace/skillopt-oauth/`` --
i.e. inside the repo. The autouse fixture below redirects every test's record dir
into ``tmp_path`` and clears the observability env-var surface, restoring the
"spends nothing / touches nothing in the tree" property the suite relies on.
"""
from __future__ import annotations

import pytest

# The env vars the guard reads for observability/control. Cleared per test so a
# stray value in the developer's shell can't leak into a case that doesn't set it.
_OBSERVABILITY_ENV = (
    "SKILLOPT_OAUTH_LOG",
    "SKILLOPT_OAUTH_LOG_LEVEL",
    "SKILLOPT_OAUTH_DRY_RUN",
    "SKILLOPT_OAUTH_SUPERVISE",
    "SKILLOPT_OAUTH_INJECT_OUT_ROOT",
    "SKILLOPT_OAUTH_RUN_ID",
    "SKILLOPT_OAUTH_OPTIMIZER",
    "SKILLOPT_OAUTH_TARGET",
    "SKILLOPT_OAUTH_ENFORCE",
    "PI_ALLOW_METERED",
    "PI_CODING_AGENT_DIR",
    "TARGET_DEPLOYMENT",
    "OPTIMIZER_DEPLOYMENT",
    "PI_EXEC_PROVIDER",
    "PI_PROVIDER",
)


@pytest.fixture(autouse=True)
def hermetic_log_dir(tmp_path, monkeypatch):
    """Point record writes at ``tmp_path`` and clear the observability env vars."""
    monkeypatch.setenv("SKILLOPT_OAUTH_LOG_DIR", str(tmp_path / "records"))
    for var in _OBSERVABILITY_ENV:
        monkeypatch.delenv(var, raising=False)
    yield
