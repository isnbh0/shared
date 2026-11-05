---
name: grounding
description: Pursue the foundation you wish the work had started from instead of compromising, and make invalid states impossible to express. Use only when explicitly requested.
disable-model-invocation: true
---

Grounding is a philosophy, not a procedure. Hold to it in whatever you are doing, whether that is planning, building, reviewing, or something else entirely.

## If only

Ask what foundation you wish the work had started from. When the work makes you think "if only we had started by doing it this way", take that thought as the goal. Aim for that foundation instead of compromising around it, even if that means an overhaul. The concept hierarchy, the architecture, and work already done are all open to change. Churn and sunk cost are not reasons to keep a design. Real forward costs, such as migrating live data or breaking a public API, shape the path to the foundation, not the goal.

An "if only" is a judgment about sound architecture, not a preference. Sound architecture gives data, behavior, and constraints clear owners, so the system stays easy to change and add to. "If only we had used MySQL" does not count unless a real problem rests on it. "If only one state machine owned this, every new case would be easy to add" does.

## Impossible to express

Handled one "this should happen" at a time, behaviors end up stepping on each other. Instead, derive a small set of deterministic, total laws, and build everything else against them. Deterministic is meant loosely: every input has a defined outcome or a defined set of allowed outcomes.

These laws are physics, not legislation. A law holds when a contradictory state cannot be constructed: the type does not admit it, the schema has no slot for it, the protocol offers no message that expresses it, or the only constructor establishes the invariant. A validator, lint rule, or review that catches a violation after the state exists does not make it impossible.

The system owns its definitions. Translate outside data into those definitions at the boundary. Anything may arrive, and its outcome may be rejection, but only valid states exist inside. When a rule cannot be made physical here, such as one spanning systems this one does not own, call it a checked rule and name the gap.

Treat proposed laws as hypotheses while designing and as physics once enforced. Weigh what a law gives against what enforcing it costs, and reformulate a law that gives bad results or keeps needing exceptions.

Laws in prose are a claim. Where they interact in ways that matter, test the claim with something that can fail: a formal model, property-based tests, exhaustive enumeration, a type that rejects the forbidden construction, or an attempt to construct the forbidden state. A check that cannot fail has grounded nothing. A formal model shows whether the laws fit together, not whether the code can reach the bad state; for that, test the code itself. For relational or state-machine laws, Alloy is a strong default; see `references/alloy.md`.
