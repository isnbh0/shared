# Phased Implementation Guide

Companion document to [SKILL.md](./SKILL.md) for writing multi-phase specifications.

> **Note:** `${SPECS_DIR}` is resolved during the Setup step in [SKILL.md](./SKILL.md). All paths in this document use that variable.

## When to Use Phased Implementation

Use this pattern when:
- Feature requires multiple independent steps that should each leave the system working
- Architectural changes need backward compatibility preserved at each step
- Work will span multiple sessions with clear handoff points
- Changes touch multiple components that benefit from incremental rollout

**Core principles**:
- Each phase leaves the system in a working, deployable state
- **Context persistence**: All context lives in the spec and codebase, never in conversation memory. Each phase can be implemented by a different agent in a separate session with no prior context.

---

## Phase Design Principles

Every phase must satisfy these seven properties:

| Property | Description |
|----------|-------------|
| **Self-contained** | Completable in one agent session |
| **Context persistence** | All context in spec/codebase; implementable by fresh agent with no prior conversation |
| **Self-consistent** | System works after completion (tests pass, CLI functions) |
| **Backward compatible** | Existing functionality preserved (use optional fields, default values) |
| **Independently committable** | Clear git boundary - one commit per phase |
| **Test-required** | Unit tests for all new code |
| **Workflow-verified** | Reproducible example workflow to verify phase works |

---

## Strict Phase Template

Each phase MUST follow this structure. Omit sections only when user explicitly requests.

```markdown
## Phase N: [Descriptive Title]

**Goal:** [1-2 sentences describing what this phase accomplishes]

**Entry state:** [What must be true before starting - typically "Phase N-1 complete"]
**Exit state:** [What will be true after completion - specific, verifiable outcomes]

### Implementation Checklist

- [ ] [Specific task with file path if applicable]
- [ ] [Another task]
- [ ] Add unit tests (see Required Tests below)
- [ ] Run `[test command]` - all tests pass
- [ ] Run example workflow (see below)
- [ ] Commit: `[commit message following repo conventions]`

### Code

[Complete implementations, not snippets. Include file paths and line context.]

```python
# path/to/file.py - ADD/MODIFY description

class NewFeature:
    """Docstring explaining purpose.

    STUB STATE: [What's implemented now]
    FUTURE: [What will use this in later phases]
    """
    pass
```

### Required Tests

**File:** `tests/path/to/test_file.py` (NEW or UPDATE)

```python
"""Complete test file - not snippets."""

import pytest
from module import Feature

class TestFeature:
    def test_basic_case(self):
        """Test description."""
        assert Feature().works()
```

### Example Workflow

```bash
# Commands to verify this phase works
uv run pytest tests/path/to/test_file.py -v

# Manual verification if applicable
uv run python -c "
from module import Feature
print(Feature().works())
print('Phase N complete')
"

# Confirm existing functionality unbroken
uv run pytest
```
```

---

## Spec-Level Scaffolding

Beyond individual phases, the full spec should include these sections:

### Header

```markdown
# [Feature Name]

**Date:** YYYY-MM-DD HH:MM:SS
**Issue:** One-line problem description
**Priority:** High/Medium/Low
**Status:** Requires Implementation

## Problem Statement

- Current state (what exists now)
- Target state (what should exist)
- Impact (why this matters)
```

### Design Principles

List 5-7 principles guiding implementation decisions:

```markdown
## Design Principles

1. **Principle name** - Brief explanation
2. **Incremental implementation** - Each phase leaves system working
3. **Test-driven phases** - Each phase requires tests before completion
```

### Key Design Decisions

Document significant choices with rationale:

```markdown
## Key Design Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Data format | YAML over JSON | Human-readable, supports comments |
| Interface style | Sync | Parallelism via workers, not async |
| New field defaults | Optional with defaults | Backward compatibility |
```

### Phase Summary Table

Provide overview of all phases:

```markdown
## Phase Summary

| Phase | Description | Tests Required | Backward Compatible |
|-------|-------------|----------------|---------------------|
| 1 | Core domain models | Model creation, serialization | Yes (additive) |
| 2 | Add source_type field | Field presence, parser updates | Yes (default empty) |
| 3 | Entity-aware results | Optional fields, serialization | Yes (optional fields) |
```

### Progress Tracking

```markdown
## Progress Tracking

When starting:
**Status:** In Progress
**Current Phase:** [N]
**Started:** YYYY-MM-DD

When complete:
**Status:** Completed
**Completed:** YYYY-MM-DD
```

### Deferred Features (Optional)

Explicitly list what's out of scope:

```markdown
## Deferred Features

The following are explicitly out of scope for this spec:
1. **Feature X** - Will be addressed in separate spec
2. **Enhancement Y** - Not needed for MVP
```

---

## Stub Annotations

Use consistent annotations to mark incomplete code:

| Annotation | Purpose | Example |
|------------|---------|---------|
| `STUB STATE:` | What's implemented now | `STUB STATE: Interface only, no implementation` |
| `FUTURE:` | What will use/extend this | `FUTURE: Will be used by CLI (Phase 5)` |
| `Limitations:` | Known constraints | `Limitations: Not thread-safe` |

```python
class Repository(ABC):
    """Abstract repository interface.

    STUB STATE: Interface only. No concrete implementation yet.
    FUTURE: FileRepository (Phase 3), SQLite (post-MVP).
    """
```

---

## Advanced Patterns

### Sub-phases for Mid-Course Corrections

When implementation reveals issues with the original plan, use decimal sub-phases:

```markdown
## Phase 3.8: Classification Sub-Model Refactor

**Goal:** Fix architecture issue discovered during Phase 3.7 implementation.

**Why sub-phase:** Design discussions during 3.7 revealed fundamental issues
that require addressing before continuing to Phase 4.
```

### Spec Forking

When architecture changes fundamentally, fork the spec rather than rewriting:

```markdown
# Feature Name v2

**Date:** YYYY-MM-DD
**Forked from:** `${SPECS_DIR}/archive/superseded/YYMMDD-original.md` at Phase 3.7

**Why forked:** [Brief explanation of what changed]

**Completed phases (1-3.7):** Already implemented per original spec.
This document continues from Phase 3.8.
```

Move the original to `${SPECS_DIR}/archive/superseded/`.

### Migration Strategies

For changes that affect existing data or APIs:

```markdown
### Migration Strategy

**Phase 1 (this phase):** Add new structure with backward-compatible migration
- Old format auto-migrates on load via model_validator
- New saves use new format
- Tests updated to use new format

**Phase 2 (future):** Remove deprecated support
- After all data migrated, remove legacy field handling
- Clean up validators
```

---

## Tooling Integration

### TodoWrite for Phase Tracking

At the start of implementing a phase, create todos including wrap-up steps:

```
TodoWrite:
- Implement [feature] according to spec
- Add unit tests for new code
- Run full test suite
- Update spec status to "Completed" with commit hash
- Archive spec to ${SPECS_DIR}/archive/implemented/
- Git add and commit all changes
```

This prevents forgetting wrap-up steps after long implementations.

### Git Commit Patterns

Based on repository conventions:

**Spec creation:**
```bash
git add ${SPECS_DIR}/YYMMDD-HHMMSS-name.md
git commit -m "spec: add specification for [brief description]

Created spec: YYMMDD-HHMMSS-name.md
Status: Requires Implementation"
```

**Spec updates:**
```bash
git commit -m "docs(spec): [what changed]

[Details if needed]"
```

**Phase implementation:**
```bash
git commit -m "feat(scope): [what was implemented]

Implements Phase N of ${SPECS_DIR}/YYMMDD-name.md

- [Change 1]
- [Change 2]
- [Change 3]

All tests pass."
```

**Phase completion marker:**
```bash
git commit -m "docs(spec): mark Phase N as implemented"
```

### Checklist Completion

Update `[ ]` to `[x]` as you complete each item. This provides:
- Visual progress tracking
- Clear record of what was done
- Easy identification of incomplete work

---

## Override Guidelines

When user explicitly requests deviation from this template:

1. **Document the deviation** in the spec with rationale
2. **Maintain the core principle** - each phase must leave system working
3. **Note which sections were modified** and why
4. **Keep phases independently committable** even if structure differs

Example:
```markdown
> **Template Override:** Combining Code and Required Tests sections per user request.
> Rationale: Tests are trivial and inline examples are clearer.
```

---

## Quick Reference

### Writing a phased spec:
1. Create timestamped file in `${SPECS_DIR}/`
2. Add header with status "Requires Implementation"
3. Write Design Principles and Key Design Decisions
4. Define phases following strict template
5. Add Phase Summary table
6. Git commit spec only
7. **STOP** - Don't implement

### Implementing a phased spec:
1. Read entire spec including all phases
2. Create TodoWrite with current phase + wrap-up steps
3. Update spec status to "In Progress"
4. Implement current phase following template exactly
5. Update checklist items to `[x]` as completed
6. Run tests and example workflow
7. Commit implementation with phase reference
8. If more phases remain, repeat from step 2
9. When all phases done: update status, archive spec, final commit
