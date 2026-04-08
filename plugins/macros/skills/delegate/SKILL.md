---
name: delegate
description: Use subagents to save context space and/or parallelize subtasks where possible
---

If other `/commands` appear in the user's message and you have not already called the Skill tool for them in this conversation, invoke each now. Do not re-invoke any skill that has already been loaded.

Prefer subagents (the Agent tool) over doing work inline whenever it would save context space or enable parallelism. Specifically:

- **Parallelize** independent subtasks by launching multiple agents in a single message.
- **Offload** research, exploration, and large-file reads to subagents so their raw output stays out of the main context.
- **Keep inline** only work that is trivial, sequential, or requires synthesis you need in-context for the next step.

When briefing a subagent, write a self-contained prompt — it has no memory of this conversation.
