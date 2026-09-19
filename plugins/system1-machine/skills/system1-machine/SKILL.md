---
name: system1-machine
description: Design a system around many cheap, low-latency judgments rather than one expensive call, decomposing it into judgments, deterministic operations, and the artifacts between them. Use when architecting around a System One model such as TypeSafe's Jev, or any fast judgment substrate, and the question is what machine to build rather than how to call the API.
---

# System 1 machine

A system-1 judgment is fast, fuzzy, and cheap enough to make thousands of times: is this
relevant, which of these, how strongly. Once judgments stop being scarce, the design
problem is the structure around them.

This skill produces a design; writing the integration is a separate job. When the
substrate is TypeSafe's Jev, `references/jev.md` covers the properties that constrain a
design.

## Decompose the problem

Split the machine three ways, and keep the seams visible in the design:

1. **Judgments** — decisions that need semantic understanding.
2. **Deterministic operations** — filtering, aggregation, routing, weighting, thresholds,
   bookkeeping. These belong to code, and should stay there.
3. **Artifacts** — the durable state between the two, read and produced by each step.

The split is the design: a step that quietly does both is where a machine gets hard to
change, because weights and thresholds end up buried inside a judgment.

## Size the judgments

Ask for what a knowledgeable person decides in a second, given the right context. If a
judgment turns on several independent factors, ask about each one separately and combine
the answers in code.

A judgment that needs deliberation should be decomposed further. A longer prompt will not
rescue it.

## Find the moves cheap judgment unlocks

- **Fan-out** — judge many objects, or one object from many angles, and let code decide
  what mattered. Batching related judgments is usually cheaper and faster than asking
  serially.
- **Speculation** — ask questions whose answers you may not need, when asking costs less
  than the round trip to discover you needed them.
- **Composition** — score several dimensions separately, then combine with weights you
  control.
- **Accumulation** — persist judgments so later decisions can draw on history and not
  only on the current input.
- **Uncertainty as a second axis** — a judgment says what; how certain it is says whether
  to act. Route confident cases automatically, uncertain ones to confirmation, review, or
  a human. Set that boundary per action, by what getting it wrong costs.
- **Audit** — have later judgments check earlier ones.

## Design pressure

Ask, as the design settles:

- What becomes feasible at orders of magnitude more judgments than seems reasonable?
- What can be decided speculatively or precomputed rather than discovered lazily?
- Where can several narrow judgments replace one complicated one?
- What state is worth accumulating across the machine?
- Which decisions should code keep?

## Output

Show what the machine consumes, what it judges, what it computes deterministically, and
what it produces, with the artifacts between steps explicit. When a diagram helps, follow
`references/mermaid.md`.

Name every judgment and identify its inputs before handing the design off.
