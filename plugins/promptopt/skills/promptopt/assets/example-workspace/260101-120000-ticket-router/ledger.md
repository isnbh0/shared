# Candidate Ledger

| Candidate | Parent | Operation | Hypothesis | Train | Val | Prompt Cost | Status |
|---|---|---|---|---:|---:|---|---|
| c001 | baseline | route-description patch | Sparse route descriptions cause lockout misroutes | 2/3 | 2/3 | small increase | rejected |
| c002 | c001 | priority-rule patch | Mixed intents need explicit fallback priority | 3/3 | 3/3 | moderate increase | selected |

## Notes

- c001 improved concrete route descriptions but did not fix mixed-intent cases.
- c002 added a targeted priority rule and met the stated train/val criteria.
