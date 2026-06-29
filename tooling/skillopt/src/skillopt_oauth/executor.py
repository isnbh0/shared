"""OAuth-CLI executor — the single LLM chokepoint (Phase 2).

STUB STATE: signatures only; constructor and `run_cli` raise NotImplementedError.
FUTURE (Phase 2): `OAuthCLIExecutor.run_cli` shells out to the `claude` / `codex` CLIs
on OAuthed subscription sessions, asserts the pinned model id + reasoning effort, and
parses structured stdout. The constructor FAILS CLOSED when `forbid_api_keys` is set
and any `*_API_KEY` is present in the environment, making silent API fallback
impossible. Rollout, reflect, and judge all route through this one method — no other
code path may call an LLM.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass
class CliResult:
    """Result of a single CLI invocation.

    STUB STATE: shape declared for Phase 2 consumers; no behavior here.
    """

    stdout: str
    exit_code: int
    duration: float
    model_asserted: str


class OAuthCLIExecutor:
    def __init__(
        self,
        *,
        claude_bin: str = "claude",
        codex_bin: str = "codex",
        model_claude: str | None = None,
        model_codex: str | None = None,
        reasoning_effort: str = "xhigh",
        forbid_api_keys: bool = True,
    ) -> None:
        # FUTURE (Phase 2): raise RuntimeError if forbid_api_keys and any *_API_KEY in os.environ.
        raise NotImplementedError("OAuthCLIExecutor is implemented in Phase 2")

    def run_cli(
        self,
        *,
        provider: str,
        prompt: str,
        skill_path: str | None = None,
        workdir: str | None = None,
        timeout: float = 600.0,
    ) -> "CliResult":
        # FUTURE (Phase 2): provider in {"claude","codex"}; shell out; return CliResult(...).
        raise NotImplementedError("OAuthCLIExecutor.run_cli is implemented in Phase 2")
