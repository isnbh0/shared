---
name: principles
description: Apply working principles for building projects to implementation, design, and review. Use only when explicitly requested.
disable-model-invocation: true
---

Read `references/principles.md` in this skill's own directory in full before applying this skill. It is a coherent statement of working judgment about development, architecture, design, verification, and upkeep. The current task, project stage, and user instructions decide which principles apply; do not turn the outline into a mandatory checklist.

When implementing or designing, let the relevant principles shape the work itself. Carry ordinary implementation choices forward within the authorized scope. Ask when purpose or policy remains undecided. Keep verification proportionate to what the change can affect, and distinguish what was established from what remains uncertain.

When reviewing, connect concrete findings to the affected behavior and propose a repair or next action. Use proposition numbers when they help locate the reasoning. Do not report hypothetical violations merely to cover every principle, or make changes beyond the user's requested review scope.

Apply these principles directly. Related skills such as grounding, aspects, findable, tightloop, and simple-now provide focused treatments, but are not dependencies and are not activated by this skill. A principle about independent review does not require a review panel or authorize delegation on its own.

If the reference cannot be read, say so and do not claim to have applied it.

The reference is generated from the principles project in the author's my-sandbox repository. Its header records the source revision. Maintain the prose at that source and refresh the bundled copy with its `export_skill.py`; edits to the bundled reference are overwritten by the next export. Applying the skill requires only the bundled file, not the source checkout or its tools.
