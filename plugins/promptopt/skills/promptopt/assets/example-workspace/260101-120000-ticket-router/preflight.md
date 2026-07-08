# Preflight

## Provided By User

- Target behavior: improve support-ticket routing for refunds, lockouts, and
  ambiguous mixed intents.
- Prompt target: `app/prompts/ticket_router.md`.
- Output contract: JSON object with `route`, `confidence`, and `reason`.
- Default policy: route unclear cases to `needs_review`.
- Train cases: provided in `cases/train.jsonl`.
- Val cases: provided in `cases/val.jsonl`.
- Acceptance criteria: defined in `brief.md`.
- Stop rule: at most two candidate steps.

## Optional Inputs

- Final-review cases: provided in `cases/final-review.jsonl`.
- Prompt cost preference: prefer smaller or simpler equivalent prompts.

## Checked

- Context replay inputs are available: captured prompt, case input shape, and
  JSON output contract.
- Full app runtime validation is outside this example run.
- No source files are edited by this run.
- Candidate prompts are stored only in this workspace.

## Missing

- None for this example run.
