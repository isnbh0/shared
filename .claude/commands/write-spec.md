---
description: Write a specification based on requirements from the conversation
---

You are writing a technical specification using the spec-workflow skill in WRITING phase.

## Your Task

Based on the requirements and context discussed in the conversation so far:

1. Use the Skill tool to invoke the spec-workflow: `skill: "spec-workflow"`
2. The skill will expand and provide instructions for the WRITING phase
3. Follow the spec-workflow instructions to:
   - Investigate the codebase thoroughly
   - Create a timestamped spec file in `agent-workspace/specs/`
   - Write a complete specification with all required sections
   - Git add and commit the spec file
   - STOP - Do not implement

## Important Notes

- The spec-workflow skill handles the entire spec writing process
- You should let the skill orchestrate the work
- Gather all necessary context from the conversation before writing
- Do NOT implement the spec - only write it and commit
- The spec should be self-contained for a fresh agent to implement later
