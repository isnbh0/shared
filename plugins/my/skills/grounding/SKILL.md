---
name: grounding
description: Derive the laws a system resolves by, make contradicting states impossible, and reopen whatever it takes to get there. Use only when explicitly requested.
disable-model-invocation: true
---

Grounding is a direction rather than a procedure. It applies wherever a system's behavior is being decided: a spec, a schema, a protocol, a refactor, a design argument. Build up from foundations instead of layering requirements onto the current design. What matters most decides the architecture, and the concept hierarchy, the architecture, and past decisions are all open if that is what it takes.

It carries three separate concerns. All three apply unless the user narrows them.

## Laws, not rules

Handled one "this should happen" at a time, behaviors end up stepping on each other. Instead, derive a small set of deterministic, total laws before adding cases, and build everything else against them. Every input must have a defined outcome under those laws.

These laws are physics, not legislation. A law holds when a contradictory state cannot be constructed: the type does not admit it, the schema has no slot for it, the protocol offers no message that expresses it, or the only constructor establishes the invariant. A validator, lint rule, or review that catches a violation does not make it unrepresentable. Close that gap by changing what the system can express.

State the laws plainly, including the obvious ones. Treat proposed invariants as hypotheses derived from the user’s task. Check both the intended benefit and the cost of enforcing them before making them structural. For layout, distinguish stable interface anchors from content that needs to reflow. When a law gives bad results or keeps needing exceptions, reformulate it rather than patching around it.

## Maximal valid change

The antithesis of minimum viable change. Ask what the ideal shape is. What would an engineer say *in an ideal world, this would have happened first*? What missing foundation would give us a whole class of behavior for free, instead of verifying each path by hand? Then go there, whatever the churn: refactor, re-architect, migrate data, rewrite call sites, discard work, or replace a platform kept only for sunk cost. Diff size is not evidence against a change.

Work out the ideal change even if it goes beyond what the user asked for. If it does, describe it and ask whether to do it.

## Grounding the laws

Laws stated in prose are a claim, not a fact. Once there are several and they interact, intuition stops being reliable about two things: whether they are mutually consistent, and whether the states meant to be unreachable actually are. Where the interactions are load-bearing or non-obvious, ground the claim in something that can fail.

Formal modeling is the prominent default when laws are structural — a small model of the states and relations, with the invariants asserted and the bad states checked for reachability. Offer Alloy when the laws are relational or state-machine shaped and worth the modeling cost; say so plainly when they are not. Before running it, read `references/alloy.md` (in this skill's own directory) for the command and how to read its verdicts.

Formal modeling is one case of the general concern, not the whole of it. Property-based tests, exhaustive enumeration over a bounded space, a type-level encoding that fails to compile when violated, a decision table checked for totality and overlap, or a deliberate attempt to construct the forbidden state and observe it being impossible — any of these grounds a law. Pick the cheapest one that could actually falsify the claim. A check that cannot fail has grounded nothing. Passing a check establishes only the claim it measures; judge whether the resulting system serves the user’s task. For visual work, this includes reading the rendered result for spacing, readability, and density.
