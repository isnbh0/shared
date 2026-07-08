# Candidate c002 Rationale

Hypothesis: the missing behavior is not only better route descriptions; the
prompt needs an explicit priority rule for mixed intents.

Expected improvement:

- Preserve c001 gains on refund and account-access cases.
- Route mixed-intent cases to `needs_review`.

Expected risk:

- Slight prompt growth.
- The prompt may overuse `needs_review` if the mixed-intent rule is too broad.

Prompt cost:

- Moderate increase. The added text is targeted at the observed failure mode.
