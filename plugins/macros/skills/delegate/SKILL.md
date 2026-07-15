---
name: delegate
description: Use subagents to save context space and/or parallelize subtasks where possible
---

Honor every skill explicitly activated in the user's request exactly once. If another activated skill is not yet loaded and the host provides a skill-loading mechanism, load it through that mechanism. Do not reload an active skill.

Prefer subagents over doing work inline whenever it would save context space or enable parallelism. Specifically:

- **Parallelize** independent subtasks by launching multiple agents concurrently, batching the dispatch if the host supports it.
- **Offload** research, exploration, and large-file reads to subagents so their raw output stays out of the main context.
- **Keep inline** only work that is trivial, sequential, or requires synthesis you need in-context for the next step.

When briefing a subagent, write a self-contained prompt — it has no memory of this conversation.
