---
name: dry-run
description: One-shot failsafe — describe what you would do for the current request instead of doing it, then wait for confirmation
---

Honor every skill explicitly activated in the user's request exactly once. If another activated skill is not yet loaded and the host provides a skill-loading mechanism, load it through that mechanism. Do not reload an active skill.

If this skill is invoked, the user is signaling a need to carefully review your intended actions before anything is executed.

For the request that activated this skill, describe what you *would* do and stop. **DO NOT** edit files, run shell commands with side effects, send messages, or spawn subagents that would do any of these.

- Read-only inspection is fine — use it freely.
- After presenting the plan, wait for the user to confirm, amend, or cancel before proceeding.
