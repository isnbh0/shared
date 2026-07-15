---
name: askme
description: Explicit-request macro. Activate only when the user directly requests this macro; never infer activation from task characteristics. Skill — Shorthand that tells the agent to ask clarifying questions instead of making decisions on its own
---

Honor every skill explicitly activated in the user's request exactly once. If another activated skill is not yet loaded and the host provides a skill-loading mechanism, load it through that mechanism. Do not reload an active skill.

When you encounter ambiguities or decision points — before starting or mid-task — stop and ask the user to clarify or decide. Do not assume.
