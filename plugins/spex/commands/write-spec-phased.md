---
description: Write a phased specification document
---

Do NOT invoke the spex skill via the Skill tool.
Do NOT re-read these instructions or any other document in a loop.
If you encounter any error or are unsure how to proceed, STOP and tell the user.
Execute the workflow below once, then stop.

## Task

You are writing a phased specification document. Your `$ARGUMENTS` contain the context/requirements from the user.

Write the spec, commit it, and STOP. Do not implement. Implementation is handled by a separate agent in a separate session.

## Setup

1. Check if `$ARGUMENTS` contains `--workspace <dir>`. If so, use that directory and skip config lookup.
2. Check for config files (first match wins):
   - `.claude/skill-configs/spex/config.local.yaml` (local scope, gitignored)
   - `.claude/skill-configs/spex/config.yaml` (project scope, committed to repo)
3. **If no config found**: STOP and tell the user:
   > "No spex config found. I need a workspace directory to store spec files.
   > You can either:
   > 1. Specify a custom path
   > 2. Use the default `.agent-workspace/specs`
   >
   > I'll create `.claude/skill-configs/spex/config.yaml` with your choice.
   > (See `config.example.yaml` in the spex plugin for reference.)"
   Wait for the user's response, then create the config file before continuing.
4. Set `${SPECS_DIR}` to the resolved `workspace_dir`. All paths below use this variable.

## Workflow

**Step 1: Create timestamped spec file**

```bash
# Generate timestamp and create spec
TIMESTAMP=$(date +"%y%m%d-%H%M%S")
touch ${SPECS_DIR}/${TIMESTAMP}-descriptive-name.md
```

**File naming**: `{YYMMDD-HHMMSS}-{kebab-case-description}.md`
**Location**: `${SPECS_DIR}/` directory

**Step 2: Investigate thoroughly**

**Before proposing solutions**:

1. **Trace execution**: Use grep/find to follow actual code paths
2. **Verify assumptions**: Check if functionality already exists elsewhere
3. **Confirm the problem**: Ensure issue exists where suspected
4. **Never assume missing**: Always verify before claiming something doesn't exist

**Step 3: Write complete phased spec**

Use the spec template (see below) with these additional required sections for phased specs:

- **Design Principles** section (5-7 guiding principles)
- **Key Design Decisions** table (Decision | Choice | Rationale)
- **Multiple phases** following the strict phase template (see Strict Phase Template below)
- **Phase Summary** table
- **Progress Tracking** section

**Step 4: Git commit and STOP**

```bash
# Add the spec file only
git add ${SPECS_DIR}/${TIMESTAMP}-descriptive-name.md

# Commit with descriptive message
git commit -m "spec: add specification for [brief description]

Created spec: ${TIMESTAMP}-descriptive-name.md
Status: Requires Implementation"
```

**STOP HERE** - Your work is done. Implementation will be handled by a different agent.

## Spec Template

```markdown
# [Component/Feature] - [Brief Issue]

**Date:** YYYY-MM-DD HH:MM:SS
**Issue:** One-line problem description
**Priority:** [High/Medium/Low]
**Status:** Requires Implementation

## Problem Statement

- Current behavior (what's broken)
- Expected behavior (what should happen)
- Impact on users/system

## Root Cause Analysis

- Technical investigation with code examples
- Why the problem exists
- Comparison with working implementations if available

## Technical Approach

- Proposed solution methodology
- High-level implementation strategy
- Rationale for chosen approach

## Implementation Details

- Specific code changes with file paths
- Step-by-step implementation plan
- Testing strategy
- All commands and dependencies needed
```

## Writing Quality Checklist

Before committing, verify:

- [ ] Timestamp formatted correctly (YYMMDD-HHMMSS)
- [ ] File in `${SPECS_DIR}/` directory
- [ ] Status is "Requires Implementation"
- [ ] All required sections present
- [ ] Investigated existing code before proposing changes
- [ ] Problem statement is specific
- [ ] Root cause includes technical investigation
- [ ] Solution fixes only stated problem
- [ ] Implementation details are actionable with full file paths
- [ ] Code examples properly formatted with file:line references
- [ ] No meta-commentary or self-notes
- [ ] Self-contained for fresh agent to implement

Run through the checklist once. If the spec covers the problem, root cause, approach, and implementation details, commit it. Do not iterate.

## When to Use Phased Implementation

Use this pattern when:
- Feature requires multiple independent steps that should each leave the system working
- Architectural changes need backward compatibility preserved at each step
- Work will span multiple sessions with clear handoff points
- Changes touch multiple components that benefit from incremental rollout

**Core principles**:
- Each phase leaves the system in a working, deployable state
- **Context persistence**: All context lives in the spec and codebase, never in conversation memory. Each phase can be implemented by a different agent in a separate session with no prior context.

## Phased Spec Requirements

Your spec must include these sections:

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

Each phase must be:
- **Self-contained** — Completable in one session
- **Self-consistent** — System works after completion (tests pass)
- **Backward compatible** — Existing functionality preserved
- **Independently committable** — One commit per phase
- **Test-required** — Unit tests for new code
- **Workflow-verified** — Reproducible example to verify

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

## Content Guidelines

**Content principles**:
- Write specs as final truth, not drafts
- No meta-commentary or revision history
- Include all context for fresh agent to start work
- Use code examples with file paths and line numbers
- Fix only the stated problem (no scope creep)

**Code examples format**:
```typescript
// src/components/Example.tsx:42
const problematic = () => { /* ... */ };

// Fixed version:
const corrected = () => { /* ... */ };
```

## Common Patterns

### Reference existing code

```markdown
## Root Cause Analysis

The issue occurs in `src/components/Button.tsx:87-92`:

\`\`\`typescript
// Current problematic implementation
const handleClick = () => {
  // Missing validation
  processData(data);
};
\`\`\`

Similar functionality in `src/components/Form.tsx:145` handles this correctly.
```

### Provide complete context

```markdown
## Implementation Details

**Files to modify**:
- `src/components/Button.tsx` - Add validation
- `src/types/index.ts` - Add new type definition

**Dependencies**:
\`\`\`bash
npm install zod
\`\`\`

**Testing**:
\`\`\`bash
npm run dev
# Navigate to http://localhost:5173/test-page
# Click button and verify validation works
\`\`\`
```

### Break down complex changes

```markdown
## Implementation Details

**Step 1: Add type definitions**
\`\`\`typescript
// src/types/validation.ts
export interface ValidationRule { /* ... */ }
\`\`\`

**Step 2: Implement validation logic**
\`\`\`typescript
// src/utils/validator.ts:1
export const validateInput = (/* ... */) => { /* ... */ }
\`\`\`

**Step 3: Integrate into component**
\`\`\`typescript
// src/components/Form.tsx:42
import { validateInput } from '@/utils/validator';
// Apply validation before submission
\`\`\`
```

## Anti-patterns to Avoid

**❌ Vague problem statements**:
"The form doesn't work right"

**✅ Specific problem statements**:
"Form submission in `src/components/ContactForm.tsx:87` allows invalid email formats to pass validation, causing 400 errors from the API"

**❌ Assumed missing functionality**:
"We need to add validation because there is none"

**✅ Verified gaps**:
"Searched codebase with `grep -r 'emailValidation' src/` - validation exists in `auth/` but not in `contact/` forms"

**❌ Scope creep**:
"Fix email validation AND redesign the form UI AND add analytics"

**✅ Focused solution**:
"Add email validation to contact form using existing validation utilities from `src/auth/validators.ts`"

**❌ Writing and implementing in same session**:
Don't create spec and immediately implement it

**✅ Separate sessions**:
Write spec → commit → stop. Later: implement spec → update status → commit

## Directory Structure

```
${SPECS_DIR}/
├── {timestamp}-name.md           # New specs (Status: Requires Implementation)
├── active/                        # In progress (Status: In Progress)
├── archive/
│   ├── implemented/              # Completed (Status: Completed)
│   └── deprecated/               # Obsolete (Status: Deprecated)
└── drafts/                       # Work-in-progress ideas
```

## Quick Reference

### Writing a phased spec:
1. Create timestamped file in `${SPECS_DIR}/`
2. Add header with status "Requires Implementation"
3. Write Design Principles and Key Design Decisions
4. Define phases following strict template
5. Add Phase Summary table
6. Git commit spec only
7. **STOP** - Don't implement

## Notes

- Specs are living documents until archived
- Update specs if requirements change (add timestamped note at top)
- Reference spec filename in commit messages
- Self-contained specs enable any agent to implement independently
- Timestamps ensure chronological ordering and uniqueness
