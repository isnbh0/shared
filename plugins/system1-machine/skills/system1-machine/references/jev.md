# Designing for Jev

Jev is TypeSafe's flagship System One model: it takes application state plus typed
questions and returns typed answers with probabilities in place of generated text.

This page covers only the properties that change a design. The API contract — request and
response fields, SDK usage, current limits — lives in the live docs at
https://docs.typesafe.ai/llms.txt, and TypeSafe maintains its own agent skill for writing
the integration. Read those when implementing; do not infer field names from here.

## Three judgment shapes

Pick the shape while designing: it determines what code can do with the answer.

- **Choice** — which of these options. Use when the outcomes are a known closed set.
- **Score** — which of several ordered descriptive levels applies. Use for graded
  judgments you intend to threshold or weight.
- **Noul** — is this true, returned as a probability. Use for a proposition you want as a
  number.

## Two constraints worth designing around

**Questions in one request are evaluated independently.** They all see the same state,
and none can see another's answer. If a design needs judgment B to depend on judgment A's
answer, that dependency costs a deliberate second request.

**Noul answers carry no confidence.** Choice and Score return a probability distribution
and a confidence derived from its shape; Noul returns the probability alone. So a design
that routes on how certain the model is — acting automatically when confident, escalating
when not — needs Choice or Score at that decision point. Keeping Noul there means
deriving your own measure from the probability, or moving the uncertainty gate elsewhere.
