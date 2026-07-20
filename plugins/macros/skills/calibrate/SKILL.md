---
name: calibrate
description: Explicit-request macro. Activate only when the user directly requests this macro; never infer activation from task characteristics. Skill — Iteratively align a mental model or state through purpose-driven passes that move from broad structure to consequential finer distinctions.
---

Honor every skill explicitly activated in the user's request exactly once. If another activated skill is not yet loaded and the host provides a skill-loading mechanism, load it through that mechanism. Do not reload an active skill.

Run a progressive-resolution calibration: align a mental model or state only as precisely as the
user's purpose requires. Calibration may concern intent, understanding, vocabulary, requirements,
observed conditions, beliefs, constraints, or another human or system state.

## Frame

Infer the following from the request and context. Ask only for what cannot safely be inferred:

- **target** — the model or state being aligned;
- **purpose** — what the calibrated model must enable;
- **participants** — whose models or states matter;
- **authority** — whether each claim comes from intent, demonstrated ability, observation,
  inference, or external evidence; and
- **boundary** — what this calibration does not need to resolve.

Start with a compact account of the apparent broad shape and its important unknowns. Invite
correction of the framing before resolving finer distinctions.

## Resolution passes

For each pass:

1. State the current model at its justified resolution, including uncertainty or disagreement.
2. Identify the **resolution frontier**: unresolved distinctions that could change the intended
   explanation, decision, diagnosis, plan, or action.
3. Ask the smallest useful set of independent probes from that frontier, normally one to four.
   Explain ambiguous distinctions with concrete examples. Do not pad the pass or follow branches
   eliminated by prior answers.
4. Incorporate the response while preserving its source and authority. Record corrections,
   contradictions, confidence, and superseded interpretations.
5. Collapse resolved branches. Zoom in only where the purpose now depends on finer resolution.

Match probes to the target:

- For intent or preference, treat the person's answer as normative authority. Evidence may test a
  premise but does not choose their policy.
- For understanding, use explanation, comparison, prediction, application, or diagnosis. Treat
  the inferred level as revisable; self-rated familiarity alone is insufficient.
- For factual or operational state, prefer observable discriminators and targeted read-only
  checks. Keep observation separate from inference.
- For vocabulary, test examples, counterexamples, boundaries, and relationships. Matching labels
  do not establish matching meanings.

Ask the probes and stop the current exchange. Do not answer them for the user. On response, revise
the model before selecting another pass.

## Convergence

Stop when the model is fit for its purpose: the relevant broad structure is shared, no unresolved
distinction would materially change the next step, remaining uncertainty is explicit and bounded,
and consequential claims have appropriate authority or evidence.

Never request fine resolution before the coarse model supports the distinction. Never retain a
coarse model when the purpose depends on finer resolution.

At convergence, present a compact baseline: purpose, current model, consequential distinctions,
remaining uncertainty, and implications. Ask for confirmation when it represents consequential
human intent. Otherwise, continue an already-requested downstream action only when it remains in
scope.

If a pass does not improve resolution, state the competing models, missing discriminator, and the
narrower purpose or new evidence needed to proceed.

## Composition with packet

When packet is also active, calibrate defines the next resolution pass and packet provides its
filesystem boundary:

- On creation, packet the current model, purpose, frontier, exact probes, response locations, and
  incorporation rule.
- On resume, incorporate validated returns, evaluate convergence, and identify the next frontier.
- Follow packet's one-operation-per-activation rule. A later pass requires another explicit packet
  activation.

Without packet, conduct the same passes in conversation. Calibrate alone does not create files or
require configuration.
