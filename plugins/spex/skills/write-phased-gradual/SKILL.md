---
name: write-phased-gradual
description: Write a rolling phased specification that plans only the next useful increment
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

Investigate the request, write and commit the initial frontier of a gradual phased specification,
then stop. Do not choose a concrete first phase or implement application code in the same task.

Use this workflow when later phases should respond to evidence learned from earlier implementation.
Use an up-front phased specification instead when the complete phase plan should be known before
implementation begins.

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
2. Trace the real code paths, verify assumptions, and record the repository baseline without
   selecting the first implementation increment.
3. Write exactly `README.md`, `P1.md`, and `P2.md` using the templates below.
4. Run the quality checks below.
5. Add and commit only the new specification directory, then stop.

## README.md Template

```markdown
# [Feature Name]

**Date:** YYYY-MM-DD HH:MM:SS
**Issue:** [One-line problem]
**Priority:** [High/Medium/Low]
**Planning Mode:** Gradual
**Status:** Requires Phase Concretization
**Current Frontier:** P1
**Next Action:** Concretize P1

## Problem Statement

[Current state, target state, impact, and verified root cause]

## Verified Repository Baseline

- `[repository-relative path]` — [Verified current responsibility or behavior]

## Design Principles

1. **Adaptive planning** — Choose each increment from the repository state left by completed work.
2. **Incremental delivery** — Every concrete phase leaves the system working.
3. **Verified phases** — Every concrete phase has runnable completion checks.

## Durable Decisions and Contracts

| Decision or contract | Current truth | Evidence |
|----------------------|---------------|----------|
| [Item] | [Constraint that later phases must preserve] | `[path or command]` |

## Deferred Work

- [Known work intentionally left for later selection]

## Phase Summary

| Phase | State | Application Commit | Document |
|-------|-------|--------------------|----------|
| P1 | Awaiting concretization | — | [P1.md](./P1.md) |
| P2 | Trailing placeholder | — | [P2.md](./P2.md) |
```

Keep the overview current as the frontier advances. Completed phase rows remain in place and point
to real application commits. `Current Frontier` names the phase eligible for action, and `Next
Action` tells a fresh agent exactly whether to concretize or implement it.

## P1 Concretization Placeholder

```markdown
# Phase 1: Select the Next Increment

**State:** Awaiting concretization

Reinspect the current repository and this specification. Choose the smallest coherent step that
materially advances the stated goal, then rewrite this file in place as a concrete phase using the
contract below.

Base the choice on verified repository state, completed phase results, failures, and newly learned
constraints. Do not rely on conversation-only context. Keep `P2.md` as the trailing placeholder.

Before application work begins, update `README.md` and commit only the concretized specification
changes.
```

## P2 Trailing Placeholder

```markdown
# Phase 2: Reserved

**State:** Trailing placeholder

This file reserves the phase after the current frontier. Do not select or describe its
implementation while the preceding phase remains incomplete.

After the preceding phase is implemented, verified, and committed, reinspect the repository and
rewrite this file in place as the next concrete phase. Add `P3.md` as the new trailing placeholder,
update `README.md`, commit only those specification changes, and stop before implementing Phase 2.
```

Later trailing placeholders use the same instructions with monotonic phase numbers.

## Concrete Phase Contract

When a placeholder becomes the current concrete phase, rewrite it in this form:

```markdown
# Phase N: [Descriptive Title]

**State:** Ready
**Goal:** [Concrete outcome]
**Entry state:** [Verified starting state]
**Exit state:** [Specific, verifiable ending state]

## Relevant Completed Contracts

- [Fact established by a completed phase that this phase must preserve]

## Implementation Checklist

- [ ] [Task with repository-relative file path]
- [ ] Add or update tests described below
- [ ] Run `[headless verification command]`
- [ ] Commit: `[message following repository conventions]`

## Code

[Complete implementation guidance, with repository-relative paths and enough context for a fresh agent.]

## Required Tests

**File:** `tests/path/to/test_file.py` (NEW or UPDATE)

[Complete tests or exact test requirements.]

## Verification

[Runnable headless commands and expected results.]
```

Use judgment to choose the smallest step that materially advances the goal. Each concrete phase
must be independently implementable, leave the system working, define explicit entry and exit
states, and state completed cross-phase contracts as facts.

## Quality Gate

Before committing, verify once:

- The overview identifies `Planning Mode: Gradual` and records the verified baseline, durable
  decisions, deferred work, current frontier, phase links, progress, and exact next action.
- The initial artifact contains only `README.md`, `P1.md`, and `P2.md`; P1 awaits concretization and
  P2 is the trailing placeholder.
- No speculative implementation content appears in either initial placeholder.
- Any concrete phase is independently implementable, with actionable paths, required tests,
  headless verification, and an application commit boundary.
- The spec contains no conversation-only context, author-to-author hedges, or machine-absolute paths.
- Every referenced existing path is tracked: check with `git ls-files` and `git check-ignore -v`.
- Every path the implementation creates is checked against gitignore rules; include an explicit
  un-ignore instruction when required.
- Phase numbers are monotonic, all links resolve, and completed phases reference real application
  commits.
- A fresh agent on a fresh clone can select and implement the next phase using only committed content.
- Only the intended specification files are staged.

If normative material is untracked or ignored, either commit it to a tracked location and update
the references or inline it in the spec. Do not commit a broken reference.

Add and commit only the specification directory using the repository's commit conventions. The
commit message should identify the gradual phased spec and its status. Stop immediately after the
commit; concretization and implementation belong to a separate task.
