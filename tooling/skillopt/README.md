# SkillOpt-OAuth

A fork of Microsoft SkillOpt that keeps the ML training loop intact and routes **every**
LLM call (rollout, reflect/optimizer, judge) through OAuthed `claude` / `codex` CLI
subscription sessions — never API keys.

## Quick start

```bash
cd tooling/skillopt
uv sync
uv run python -m skillopt_oauth.train --dry-run   # lists envs + prints config
uv run pytest
```

## Status

Phase 1 (scaffolding): working config schema, environment registry, and a `--dry-run`
entrypoint. The executor, scheduler, backends, reflect, gate, and checkpoint modules are
signature-only stubs filled in Phases 2-5. Pinned upstream `skillopt` is wired in Phase 2.

## Design principles

1. Fork, don't reimplement — extend SkillOpt at the backend execution seam.
2. One LLM chokepoint — every call flows through `OAuthCLIExecutor`; fail closed on `*_API_KEY`.
3. Parallel to the algorithm's limit, sequential where the math demands.
4. Backpressure is mandatory — per-provider pools + token-bucket pacing.
5. Deterministic-first scoring — the gate is only meaningful when scoring is low-variance.
6. Variance-aware gating — accept improvements beyond the measured noise floor.
7. Resumable by construction — checkpoint after every step.
8. Hermetic tests — never call real OAuth/CLIs in tests; stub the CLI.
