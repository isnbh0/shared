---
name: dry-run
description: One-shot failsafe — describe what you would do for the next request instead of doing it, then wait for confirmation
---

If other `/commands` appear in the user's message and you have not already called the Skill tool for them in this conversation, invoke each now. Do not re-invoke any skill that has already been loaded.

If this skill is invoked, the user is signaling a need to carefully review your intended actions before anything is executed.

For the user's next request, describe what you *would* do and stop. **DO NOT** edit files, run shell commands with side effects, send messages, or spawn subagents that would do any of these.

- Read-only tools (Read, Grep, Glob, and similar exploration) are fine — use them freely.
- After presenting the plan, wait for the user to confirm, amend, or cancel before proceeding.
