---
name: system1-machine
description: Design a system around many cheap, low-latency judgments rather than one expensive call, decomposing it into judgments, deterministic operations, and the artifacts between them. Use when architecting around a System One model such as TypeSafe's Jev, or any fast judgment substrate, and the question is what machine to build rather than how to call the API.
---

# System 1 machine

Design the machine, not just the prompt.

A system-1 judgment is fast, fuzzy, and cheap enough to make thousands of times: is this
relevant, which of these, how strongly. Once judgments stop being the scarce thing, the
interesting question is what structure to put around them.

This skill produces a design, not an integration. When the substrate is TypeSafe's Jev,
`references/jev.md` covers the properties that constrain a design.

## Decompose the problem

Separate three things, and keep them separate in the design:

1. **Judgments** — decisions that need semantic understanding.
2. **Deterministic operations** — filtering, aggregation, routing, weighting, thresholds,
   bookkeeping. Code owns these, and should keep owning them.
3. **Artifacts** — the durable state between the two, read and produced by each step.

The split is the design. A step that quietly does both is where machines get hard to
change, because the weights and thresholds end up buried in a judgment.

## Size the judgments

Ask for what a knowledgeable person decides in a second, given the right context. If a
judgment depends on several independent factors, consider asking about each factor
separately and combining them in code.

A judgment that needs deliberation is a signal to decompose further, not to write a
longer prompt.

## Find the moves cheap judgment unlocks

- **Fan-out** — judge many objects, or one object from many angles, and let code decide
  what mattered. Batching related judgments is usually cheaper and faster than asking
  serially.
- **Speculation** — ask questions whose answers you may not need, when asking is cheaper
  than the round trip to find out you needed them.
- **Composition** — score several dimensions separately, then combine with weights you
  control.
- **Accumulation** — persist judgments so later decisions can depend on history rather
  than only the current input.
- **Uncertainty as a second axis** — a judgment says what; how certain it is says whether
  to act. Route confident cases automatically, uncertain ones to confirmation, review, or
  a human. Set that boundary per action, according to what getting it wrong costs.
- **Audit** — have later judgments check earlier ones.

## Design pressure

Worth asking as the design settles:

- What becomes feasible at orders of magnitude more judgments than seems reasonable?
- What can be decided speculatively or precomputed rather than discovered lazily?
- Where can several narrow judgments replace one complicated judgment?
- What state is worth accumulating across the machine?
- Which decisions should code keep?

## Output

Show what the machine consumes, what it judges, what it computes deterministically, and
what it produces, with the artifacts between steps explicit. When a diagram helps, follow
`references/mermaid.md`.

Hand the design off with the judgments named and their inputs identified.
