# Baseline Results

## Summary

- Train: 1/3 matched expected route.
- Val: 1/3 matched expected route.
- Contract: valid JSON in all recorded outputs.
- Evidence basis: see `decision.md` for the run-level context replay note.
- Main failures: the baseline treats account lockout/suspension as technical
  issues and forces mixed-intent tickets into a single concrete route instead of
  using `needs_review`.
- Raw outputs: `baseline/outputs/train.jsonl` and `baseline/outputs/val.jsonl`.

## Train

| Case | Expected | Actual | Notes |
|---|---|---|---|
| train-refund-001 | billing | billing | Pass |
| train-lockout-001 | account_access | technical | Lockout treated as technical issue |
| train-ambiguous-001 | needs_review | account_access | Mixed intent forced to access route |

## Val

| Case | Expected | Actual | Notes |
|---|---|---|---|
| val-refund-001 | billing | billing | Pass |
| val-lockout-001 | account_access | technical | Suspension treated as technical issue |
| val-ambiguous-001 | needs_review | technical | Multi-issue ticket forced to technical route |
