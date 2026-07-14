---
name: timeless
description: Shorthand that tells the agent to avoid time estimates — hours, days, calendar dates, or size buckets that map to time. Describe complexity and scope instead.
---

Honor every skill explicitly activated in the user's request exactly once. If another activated skill is not yet loaded and the host provides a skill-loading mechanism, load it through that mechanism. Do not reload an active skill.

Do not include time estimates anywhere in your output — chat, commits, plans, spec docs, PR descriptions. This covers:

- Effort hours/days ("takes an hour", "half a day", "a few days of work")
- Calendar phrasing ("this week", "by Friday", "in a few days")
- Size buckets that map to time ("small/medium/large", "XS/S/M/L")

Base estimates assume human coding speed and don't account for LLM-assisted generation, so any time anchor is fundamentally wrong.

Describe the work along these dimensions instead:

- Complexity: trivial, nontrivial, substantial
- Concrete scope: files touched, systems involved, concepts required
- Risk and unknowns: what's uncertain, what needs verification
- Ordering and dependencies: what must happen before what
