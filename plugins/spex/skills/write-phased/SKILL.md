---
name: write-phased
description: Write a phased specification document
---

Do not re-invoke this skill recursively or reread instructions in a loop.
Treat failed tool calls, patch-context mismatches, test failures, and command
mistakes as recoverable unless they reveal a genuine blocker. Inspect the
current state, correct the cause, and continue. Retrying or adapting a failed
operation within this workflow is allowed; do not restart from the beginning.
If a patch no longer matches, reread the affected file and regenerate a smaller
patch against its current contents.
Stop only when progress requires missing configuration or authority,
unavailable external state, destructive or irreversible action, a material
product choice not resolved by the request or repository, or no defensible safe
path remains after diagnosis.

## Task

Investigate the request, write and commit a phased specification, then stop. Do not implement it in the same task.

## Setup

Resolve `workspace_dir` in this order:

1. Explicit user override
2. `.agents/skill-configs/spex/config.local.yaml`
3. `.agents/skill-configs/spex/config.yaml`
4. Legacy `.agent-workspace/spex/config.local.yaml`, `.agent-workspace/spex/config.yaml`, `.claude/skill-configs/spex/config.local.yaml`, then `.claude/skill-configs/spex/config.yaml`

If config exists only at a legacy path, use it and offer to move it. If none exists, stop and ask the user to choose a workspace directory or `.agent-workspace/specs`; then create the selected `.agents/skill-configs/spex/` config. See `config.example.yaml` beside this file.

Set `${SPECS_DIR}` to the resolved value.

## Workflow

1. Create `${SPECS_DIR}/{YYMMDD-HHMMSS}-{kebab-case-description}/` using the current local time.
2. Trace the real code paths, verify assumptions, and confirm the problem before proposing changes.
3. Write `README.md` plus one `PN-{name}.md` per phase.
4. Run the quality checks below.
5. Add and commit the entire spec directory, then stop.

## README.md Template

```markdown
# [Feature Name]

**Date:** YYYY-MM-DD HH:MM:SS
**Issue:** [One-line problem]
**Priority:** [High/Medium/Low]
**Status:** Requires Implementation

## Problem Statement

[Current state, target state, impact, and verified root cause]

## Design Principles

1. **[Principle]** — [Explanation]
2. **Incremental delivery** — Every phase leaves the system working.
3. **Verified phases** — Every phase has runnable completion checks.

## Key Design Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| [Decision] | [Choice] | [Rationale] |

## Deferred Features

- [Explicitly out-of-scope item and reason]

## Phase Summary

| Phase | Name | Tests Required | Backward Compatible |
|-------|------|----------------|---------------------|
| 1 | [Title] | [Tests] | Yes |

## Phase Documents

1. [P1-{name}.md](./P1-{name}.md) — [Description]

## Progress Tracking

| Phase | Commit | Status |
|-------|--------|--------|
| 1 | — | Pending |
```

## Phase Template

```markdown
## Phase N: [Descriptive Title]

**Goal:** [Concrete outcome]
**Entry state:** [Required starting state]
**Exit state:** [Specific, verifiable ending state]

### Implementation Checklist

- [ ] [Task with repository-relative file path]
- [ ] Add or update tests described below
- [ ] Run `[verification command]`
- [ ] Commit: `[message following repository conventions]`

### Code

[Complete implementation guidance, with repository-relative paths and enough context for a fresh agent.]

### Required Tests

**File:** `tests/path/to/test_file.py` (NEW or UPDATE)

[Complete tests or exact test requirements.]

### Example Workflow

[Runnable commands and expected results.]
```

Each phase must be independently implementable, leave the system working, define explicit entry and exit states, and state cross-phase contracts as facts in every affected phase.

## Quality Gate

Before committing, verify once:

- The overview records the verified root cause, scope, decisions, deferred work, phase links, and progress table.
- Every phase has actionable paths, required tests, runnable verification, and a commit boundary.
- The spec contains no conversation-only context, author-to-author hedges, or machine-absolute paths.
- Every referenced existing path is tracked: check with `git ls-files` and `git check-ignore -v`.
- Every path the implementation creates is checked against gitignore rules; include an explicit un-ignore instruction when required.
- A fresh agent on a fresh clone can implement each phase using only committed content.

If normative material is untracked or ignored, either commit it to a tracked location and update the references or inline it in the spec. Do not commit a broken reference.

Add and commit only the spec directory using the repository's commit conventions. The commit message should identify the phased spec and its status. Stop immediately after the commit; implementation belongs to a separate task.
