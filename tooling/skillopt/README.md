# SkillOpt-OAuth

A fork of Microsoft SkillOpt that keeps the ML training loop's shape and
semantics intact and routes **every** LLM call (rollout, reflect/optimizer,
judge) through OAuthed `claude` / `codex` CLI **subscription** sessions — never
API keys, never the raw Messages API. Agentic rollouts on a subscription run
roughly 10–50× cheaper than metered API.

## Quick start

```bash
cd tooling/skillopt
uv sync
uv run python -m skillopt_oauth.train --dry-run   # lists envs + prints config
uv run pytest                                      # hermetic; spends nothing

# A real, dual-identity optimization run (needs OAuth claude + codex logins;
# spends real subscription tokens). Watches a deliberately bad skill improve 0 -> 1:
examples/timestamp_optimize/run.sh
```

## Status

Implemented and **self-contained**: the full loop — OAuth executor, bounded
scheduler, variance gate, parallel-propose reflection, write-ahead
checkpoint/resume — runs end to end on real `claude` / `codex` subscriptions, with
126 hermetic tests. Upstream Microsoft SkillOpt is **not** a runtime dependency;
the fork mirrors its algorithm and keeps two dormant seams to delegate to it once
a version is pinned (see [DESIGN §2](docs/DESIGN.md#2-relationship-to-upstream-skillopt)).

## Design principles

1. **Fork, don't reimplement** — mirror SkillOpt's algorithm and wrap upstream at
   the execution seam (self-contained today; see [DESIGN §2](docs/DESIGN.md#2-relationship-to-upstream-skillopt)).
2. **One LLM chokepoint** — every call flows through `OAuthCLIExecutor`; fail
   closed unless a subscription credential is proven, and scrub `*_API_KEY` from
   the child env so a metered fallback is impossible by construction.
3. **Parallel to the algorithm's limit, sequential where the math demands** — fan
   out rollouts, val evals, and minibatch proposals; serialize steps and the gate.
4. **Backpressure is mandatory** — per-provider pools + token-bucket pacing +
   backoff + circuit breaker.
5. **Deterministic-first scoring** — the gate is only meaningful when scoring is
   low-variance; prefer pure-Python scorers over LLM judges.
6. **Variance-aware gating** — accept improvements only beyond the measured noise
   floor.
7. **Resumable by construction** — write-ahead checkpoint after every step.
8. **Hermetic tests** — never call real OAuth/CLIs in tests; drive a stub CLI.

## Learn more

- [`docs/DESIGN.md`](docs/DESIGN.md) — the durable design context: intent,
  constraints (OAuth billing safety, dual identity, backpressure), the
  relationship to upstream SkillOpt, the real-CLI execution contract, the gate
  math, the reflection fidelity compromise, and known risks.
- [`examples/timestamp_optimize/`](examples/timestamp_optimize/README.md) — a
  runnable real optimization run with its captured trajectory.
