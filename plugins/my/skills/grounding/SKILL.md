---
name: grounding
description: Pursue the foundation you wish the work had started from instead of compromising, and make invalid states impossible to express. Use only when explicitly requested.
disable-model-invocation: true
---

Grounding is a philosophy, not a procedure. Hold to it in whatever you are doing, whether that is planning, building, reviewing, or something else entirely.

## If only

Sometimes the work makes you think: if only we had started by doing it this way. Take that thought as the goal. Move the work to that foundation instead of compromising around it, even if that means an overhaul. The concept hierarchy, the architecture, and work already done are all open to change. Churn and sunk cost are not reasons to keep a design.

An "if only" is a judgment about sound architecture, not a preference. "If only we had used MySQL" does not count unless a real problem rests on it. "If only one state machine owned this, every new case would be easy to add" does. Principles named alongside grounding help decide what sound means here.

## Impossible to express

Handled one "this should happen" at a time, behaviors end up stepping on each other. Instead, derive a small set of deterministic, total laws, and build everything else against them. Every input has a defined outcome under those laws.

These laws are physics, not legislation. A law holds when a contradictory state cannot be constructed: the type does not admit it, the schema has no slot for it, the protocol offers no message that expresses it, or the only constructor establishes the invariant. A validator, lint rule, or review that catches a violation does not make it impossible.

Treat proposed laws as hypotheses. Weigh what a law gives against what enforcing it costs, and reformulate a law that gives bad results or keeps needing exceptions.

Laws in prose are a claim. Where they interact in ways that matter, test the claim with something that can fail: a formal model, property-based tests, exhaustive enumeration, a type that will not compile, or an attempt to construct the forbidden state. A check that cannot fail has grounded nothing. For relational or state-machine laws, Alloy is a strong default; see `references/alloy.md`.
