---
name: Spec Workflow (Write & Implement)
description: Two-phase workflow for technical specifications - WRITING phase creates and commits specs then stops; IMPLEMENTATION phase follows specs, updates status, and commits all changes. Different agents handle each phase.
argument-hint: "<write|write-phased|implement> [args...]"
disable-model-invocation: true
---

# Spec Workflow: Writing and Implementation

## Overview

This skill supports a **two-phase workflow** where specification writing and implementation are handled by different agents:

1. **WRITING PHASE**: Create spec, commit it, STOP
2. **IMPLEMENTATION PHASE**: Follow spec, implement, update status, commit everything

**CRITICAL**: These are separate tasks. Never write AND implement in the same session.

> **For phased implementations**: When a feature requires multiple independent phases
> (each leaving the system working), see [PHASED-IMPLEMENTATION.md](./PHASED-IMPLEMENTATION.md).

---

## Mode Dispatch

Read the first word of `$ARGUMENTS` to determine the mode:

| First word | Mode | Action |
|------------|------|--------|
| `write` | Write spec | Follow **Phase 1: Writing Specifications** below. Remaining args are context/requirements. |
| `write-phased` | Write phased spec | Follow **Phase 1** + the **Phased Spec Requirements** subsection. Remaining args are context/requirements. |
| `implement` | Implement spec | Follow **Phase 2: Implementing Specifications** below. Remaining args = spec file path (if provided). |
| _(empty or unrecognized)_ | Help | Show usage: `/spec-workflow <write\|write-phased\|implement> [args...]` and briefly describe each mode. |

After dispatching, follow the corresponding phase section below.

---

## Phase 1: Writing Specifications

**When to use**: User requests a spec to be written, or you need to document a bug/feature/system change.

**Your responsibilities**:
- ✅ Investigate and write the spec
- ✅ Git add and commit the spec file
- ✅ STOP - Do not implement

**You must NOT**:
- ❌ Implement the spec
- ❌ Write any code beyond the spec itself
- ❌ Update the spec status to "In Progress" or "Completed"

### Writing Workflow

**Step 1: Create timestamped spec file**

```bash
# Generate timestamp and create spec
TIMESTAMP=$(date +"%y%m%d-%H%M%S")
touch agent-workspace/specs/${TIMESTAMP}-descriptive-name.md
```

**File naming**: `{YYMMDD-HHMMSS}-{kebab-case-description}.md`
**Location**: `agent-workspace/specs/` directory

**Step 2: Investigate thoroughly**

**Before proposing solutions**:

1. **Trace execution**: Use grep/find to follow actual code paths
2. **Verify assumptions**: Check if functionality already exists elsewhere
3. **Confirm the problem**: Ensure issue exists where suspected
4. **Never assume missing**: Always verify before claiming something doesn't exist

**Step 3: Write complete spec**

Use this template:

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

**Step 4: Git commit and STOP**

```bash
# Add the spec file only
git add agent-workspace/specs/${TIMESTAMP}-descriptive-name.md

# Commit with descriptive message
git commit -m "spec: add specification for [brief description]

Created spec: ${TIMESTAMP}-descriptive-name.md
Status: Requires Implementation"
```

**STOP HERE** - Your work is done. Implementation will be handled by a different agent.

### Writing Quality Checklist

Before committing, verify:

- [ ] Timestamp formatted correctly (YYMMDD-HHMMSS)
- [ ] File in `agent-workspace/specs/` directory
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

### Phased Spec Requirements (write-phased mode)

When in `write-phased` mode, your spec must also include these sections (see [PHASED-IMPLEMENTATION.md](./PHASED-IMPLEMENTATION.md) for full templates):

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

---

## Phase 2: Implementing Specifications

**When to use**: User requests implementation of an existing spec.

**Your responsibilities**:
- ✅ Read and understand the spec completely
- ✅ Implement according to the spec
- ✅ Follow all usual best practices
- ✅ Update spec status with commits
- ✅ Git add and commit all changes (spec + implementation)

**You must NOT**:
- ❌ Deviate from the spec without justification
- ❌ Skip updating the spec status
- ❌ Leave uncommitted changes

### Implementation Workflow

**Step 1: Read the spec**

If a spec file path was provided in `$ARGUMENTS` (after the `implement` keyword), use that path directly.

Otherwise, find the latest non-future spec automatically:

```bash
python3 -c "
import os
import re
from datetime import datetime

specs_dir = 'agent-workspace/specs'
now = datetime.now()
pattern = re.compile(r'^(\d{6})-(\d{6})-.*\.md$')

valid_specs = []
for filename in os.listdir(specs_dir):
    match = pattern.match(filename)
    if match:
        date_part, time_part = match.groups()
        year = int('20' + date_part[0:2])
        month = int(date_part[2:4])
        day = int(date_part[4:6])
        hour = int(time_part[0:2])
        minute = int(time_part[2:4])
        second = int(time_part[4:6])
        try:
            spec_dt = datetime(year, month, day, hour, minute, second)
            if spec_dt <= now:
                valid_specs.append((spec_dt, filename))
        except ValueError:
            continue

if valid_specs:
    latest = sorted(valid_specs, key=lambda x: x[0], reverse=True)[0]
    print(latest[1])
"
```

The script outputs the filename of the latest spec. Construct the full path as `agent-workspace/specs/{filename}` and read it completely.

Understand:
- Problem statement
- Root cause
- Technical approach
- All implementation details
- Testing requirements

**Step 2: Create implementation todo list**

**RECOMMENDED**: Use TodoWrite to create a todo list with ALL steps, including wrap-up. This prevents forgetting to update/archive the spec after long implementations.

Create todos for:
1. Implementation tasks (from spec's Implementation Details)
2. Testing/verification
3. **Update spec status to "Completed"**
4. **Add commit hash to spec**
5. **Archive spec to agent-workspace/specs/archive/implemented/**
6. **Git commit all changes**

Example:
```
TodoWrite:
- Implement feature X according to spec
- Run tests to verify requirements
- Update spec status to "Completed" with commit hash
- Archive spec to agent-workspace/specs/archive/implemented/
- Git add and commit all changes (code + spec)
```

**Step 3: Update spec status to "In Progress"**

Edit the spec file:

```markdown
**Status:** In Progress
**Started:** YYYY-MM-DD
```

Optional: Move to active directory

```bash
git mv agent-workspace/specs/{spec}.md agent-workspace/specs/active/{spec}.md
git add agent-workspace/specs/active/{spec}.md
```

**Step 4: Implement according to spec**

Follow the implementation details exactly:
- Make all code changes specified
- Install any required dependencies
- Follow the step-by-step plan
- Test as specified in the spec
- **Mark todos as completed as you finish each step**

**Follow all usual best practices**:
- Write clean, maintainable code
- Add appropriate error handling
- Include comments where helpful
- Ensure type safety
- Test thoroughly

**Step 5: Verify requirements**

```bash
# Test the implementation
npm run dev  # or appropriate test command

# Verify all spec requirements met
# Check each item in Implementation Details section
```

**Step 6: Update spec status to "Completed"**

Edit the spec file:

```markdown
**Status:** Completed
**Implementation:**
- Commit: {hash} - {message}
- Commit: {hash} - {message}
**Completed:** YYYY-MM-DD
```

**Step 7: Archive the spec**

```bash
# Move to implemented archive
mkdir -p agent-workspace/specs/archive/implemented
git mv agent-workspace/specs/active/{spec}.md agent-workspace/specs/archive/implemented/{spec}.md
git add agent-workspace/specs/archive/implemented/{spec}.md
# OR if not in active/
git mv agent-workspace/specs/{spec}.md agent-workspace/specs/archive/implemented/{spec}.md
git add agent-workspace/specs/archive/implemented/{spec}.md
```

**Step 8: Git add and commit everything**

```bash
# Add all changes (implementation + updated spec)
git add [files-you-modified]
git add agent-workspace/specs/archive/implemented/{spec}.md  # or wherever spec is

# Commit with reference to spec
git commit -m "feat: implement [feature name]

Implements spec: {timestamp}-name.md
- [Brief description of changes]
- [Another change]

Status: Completed"
```

### Implementation Quality Checklist

Before committing, verify:

- [ ] **All todos marked as completed**
- [ ] All spec requirements implemented
- [ ] Code follows best practices
- [ ] Tests pass / manual testing complete
- [ ] Spec status updated to "Completed"
- [ ] Spec includes commit hashes
- [ ] Spec includes completion date
- [ ] Spec archived to `agent-workspace/specs/archive/implemented/`
- [ ] All files added to git (implementation + spec)
- [ ] Commit message references spec file
- [ ] No uncommitted changes remain

---

## Directory Structure

```
agent-workspace/specs/
├── {timestamp}-name.md           # New specs (Status: Requires Implementation)
├── active/                        # In progress (Status: In Progress)
├── archive/
│   ├── implemented/              # Completed (Status: Completed)
│   └── deprecated/               # Obsolete (Status: Deprecated)
└── drafts/                       # Work-in-progress ideas
```

---

## Content Guidelines

**Content principles** (apply to both phases):
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

---

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

---

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

---

## Status Field Reference

### During Writing Phase

```markdown
**Status:** Requires Implementation
```

### During Implementation Phase

**Starting work**:
```markdown
**Status:** In Progress
**Started:** YYYY-MM-DD
```

**When complete**:
```markdown
**Status:** Completed
**Implementation:**
- Commit: abc123 - feat: implement feature X
- Commit: def456 - fix: handle edge case in feature X
**Completed:** YYYY-MM-DD
```

**If deprecated**:
```markdown
**Status:** Deprecated
**Reason:** [Brief explanation]
**Superseded By:** [Link to replacement]
**Deprecated:** YYYY-MM-DD
```

---

## Quick Reference

### I'm WRITING a spec:
1. Create timestamped file in `agent-workspace/specs/`
2. Investigate thoroughly
3. Write complete spec with "Status: Requires Implementation"
4. `git add agent-workspace/specs/{spec}.md && git commit`
5. **STOP** - Don't implement

### I'm IMPLEMENTING a spec:
1. Read spec completely
2. **Create TodoWrite list with all steps including wrap-up**
3. Update status to "In Progress"
4. Implement according to spec + best practices
5. Test thoroughly
6. Update spec status to "Completed" with commits and date
7. Archive spec to `agent-workspace/specs/archive/implemented/`
8. `git add [all-files] && git commit`
9. Done

---

## Notes

- Specs are living documents until archived
- Update specs if requirements change (add timestamped note at top)
- Reference spec filename in commit messages
- Self-contained specs enable any agent to implement independently
- Timestamps ensure chronological ordering and uniqueness
- The two-phase approach ensures specs are reviewed before implementation
- Different agents bring fresh perspectives to implementation
