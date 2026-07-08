# PromptOpt Brief

## Target Behavior

Improve a support-ticket routing prompt so refund requests route to `billing`,
account lockout requests route to `account_access`, and ambiguous cases route to
`needs_review`.

## Prompt Target

- Feature area: support ticket intake router.
- Prompt location: `app/prompts/ticket_router.md` (provided by the user).
- Runtime path: not executed in this example workspace; outputs represent a
  context-reconstruction example using the captured prompt, input shape, and
  output contract.

## Output Contract

Return JSON only:

```json
{"route":"billing|account_access|technical|needs_review","confidence":0.0,"reason":"short reason"}
```

No markdown, no extra prose, no renamed fields.

## Default Policy

Use `needs_review` when the message has mixed intents, missing context, or no
clear destination.

## Train Cases

See `cases/train.jsonl`.

## Val Cases

See `cases/val.jsonl`.

## Final-Review Cases

See `cases/final-review.jsonl`. These are not used for candidate steering.

## Acceptance Criteria

- Clear refund requests route to `billing`.
- Clear lockout requests route to `account_access`.
- Ambiguous mixed-intent requests route to `needs_review`.
- Output remains valid JSON with the required fields.
- Longer prompts are acceptable only if they improve routing without adding
  avoidable complexity.

## Stop Rule

Stop after two candidate steps or earlier if a candidate meets the acceptance
criteria without regressions.
