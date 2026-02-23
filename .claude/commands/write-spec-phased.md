---
description: Write a phased implementation specification for complex multi-step features
---

You are writing a **phased** technical specification using the spec-workflow skill in WRITING phase.

## Your Task

Based on the requirements and context discussed in the conversation so far:

1. Use the Skill tool to invoke the spec-workflow: `skill: "spec-workflow"`
2. Also read `.claude/skills/spec-workflow/PHASED-IMPLEMENTATION.md` for the phase structure template
3. Follow both documents to create a multi-phase spec where **each phase is independently deployable**

## Phased Spec Requirements

Your spec must include:
- **Design Principles** section (5-7 guiding principles)
- **Key Design Decisions** table (Decision | Choice | Rationale)
- **Multiple phases** following the strict phase template:
  - Goal, Entry/Exit state
  - Implementation Checklist with `[ ]` items
  - Complete Code examples (not snippets)
  - Required Tests (complete test files)
  - Example Workflow (verification commands)
- **Phase Summary** table
- **Progress Tracking** section

## Phase Design Principles

Each phase must be:
- **Self-contained** - Completable in one session
- **Self-consistent** - System works after completion (tests pass)
- **Backward compatible** - Existing functionality preserved
- **Independently committable** - One commit per phase
- **Test-required** - Unit tests for new code
- **Workflow-verified** - Reproducible example to verify

## Important Notes

- The spec-workflow skill handles the base spec writing process
- PHASED-IMPLEMENTATION.md provides the phase structure template
- Gather all necessary context from the conversation before writing
- Do NOT implement the spec - only write it and commit
- The spec should be self-contained for a fresh agent to implement phase by phase
