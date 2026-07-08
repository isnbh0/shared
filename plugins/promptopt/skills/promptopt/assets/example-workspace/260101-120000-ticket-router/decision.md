# Decision Record

## Target

Improve support-ticket routing for refund, account lockout, and mixed-intent
messages.

## Case Manifest

- Train: 3 cases.
- Val: 3 cases.
- Final-review: 1 case, not used for candidate steering.

## Baseline Summary

- Train: 1/3.
- Val: 1/3.
- Main failure: mixed-intent and account-access cases were forced into the wrong
  concrete route.

## Execution Mode

Artifact-only/context reconstruction.

## Reproduced Context

- Captured prompt.
- Case input shape.
- JSON output contract.
- These artifacts are sufficient to faithfully replay the LLM-call context for
  this routing prompt example.

## Fidelity Gaps

- The real application runtime path was not executed, so full app integration
  behavior still needs validation outside this run.

## Candidate Summary

- c001 improved account-access routing but still failed mixed-intent fallback.
- c002 preserved c001's gains and added an explicit mixed-intent priority rule.

## Recommendation

Recommend `c002` for human review before any source-editing task applies it.

## Why c002 Was Selected

- Train improved from 1/3 to 3/3.
- Val improved from 1/3 to 3/3.
- Output contract remained valid JSON.
- The prompt grew moderately, but the added rule directly addresses the observed
  failure mode.

## Val Exposure

Val results were used in selection. The final-review case was not used for
candidate steering.

## Risks

- The selected prompt should be run against the final-review case and normal app
  validation before source changes are made.

## If The User Applies This

Start a separate source-editing task that copies the selected candidate into the
real prompt target, then run the application's normal validation.
