---
name: findable
description: Keep project conventions reachable from agent entry points and aligned with actual behavior. Use only when explicitly requested.
disable-model-invocation: true
---

Treat project instructions, commands, and contracts as part of the working interface.

When you add or change a convention, make it reachable from each agent entry point the project uses. A new person or agent should be able to follow a clear path to the relevant instruction, command, or contract. Keep detailed guidance near the work it governs.

When code or configuration changes a command, file format, or workflow, update the guides and contracts that describe the changed behavior in the same change. A change is incomplete if a relevant guide or contract still describes the old behavior.

Before finishing, follow the path from each relevant agent entry point to the affected guidance. Check that the pointers work and the guidance matches current behavior.
