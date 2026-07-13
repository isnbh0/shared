---
name: write
description: Write a specification document
---

Do NOT re-invoke this skill recursively.
Do NOT re-read these instructions or any other document in a loop.
If you encounter any error or are unsure how to proceed, STOP and tell the user.
Execute the workflow below once, then stop.

## Task

You are writing a specification document. The user's request contains the context/requirements for the spec.

Write the spec, commit it, and STOP. Do not implement. Implementation is handled by a separate agent in a separate session.

## Setup

1. If the user explicitly asks to override the workspace location, use the directory they specify and skip config lookup.
2. Check for config files (first match wins):
   - `.agents/skill-configs/spex/config.local.yaml` (local scope, gitignored)
   - `.agents/skill-configs/spex/config.yaml` (project scope, committed to repo)
   - Legacy fallback (older installs): `.agent-workspace/spex/config.local.yaml`, `.agent-workspace/spex/config.yaml`, then `.claude/skill-configs/spex/config.local.yaml`, `.claude/skill-configs/spex/config.yaml`. If config is found only at a legacy path, use it and offer to move it to the new location.
3. **If no config found**: STOP and tell the user:
   > "No spex config found. I need a workspace directory to store spec files.
   > You can either:
   > 1. Specify a custom path
   > 2. Use the default `.agent-workspace/specs`
   >
   > I'll create `.agents/skill-configs/spex/config.yaml` with your choice.
   > (If you use the local scope, add `.agents/skill-configs/spex/config.local.yaml` to .gitignore.)
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

**Clone test:** before committing, re-read the spec as a stranger on a
fresh clone — only `git ls-files` content exists. Grep the spec dir for
references to untracked/ignored paths, absolute user paths, and
conversation phrasing. Anything that fails resolves in one of two ways:
commit the referenced material to a tracked location, or rewrite the
reference. Committing a spec whose sources are gitignored is a silent
failure. (The Writing Quality Checklist is the itemized form of this
gate.)

```bash
# Add the spec file only
git add ${SPECS_DIR}/${TIMESTAMP}-descriptive-name.md

# Commit with descriptive message
git commit -m "spec: add specification for [brief description]

Created spec: ${TIMESTAMP}-descriptive-name.md
Status: Requires Implementation"
```

**STOP HERE** - Your work is done. Implementation will be handled by a different agent.

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
- [ ] Committed-visibility check: every path the spec references as
      already-existing resolves within the committed tree
      (`git ls-files` / `git check-ignore -v <path>`). If normative
      source material is untracked or gitignored, stop and ask the
      user: commit it to a tracked location (updating references) or
      inline it — never reference it in place. (This is the mechanical
      form of the Clone test in Step 4.)
- [ ] No machine-absolute paths (`/Users/...`, `/home/...`, `$HOME`
      literals). Use repo-relative paths or
      `cd "$(git rev-parse --show-toplevel)"` in workflows.
- [ ] No conversation references ("the user chose", "as discussed",
      "ratified with the user"). Record decisions as dated facts:
      "Ratified 2026-07-12."
- [ ] Gitignore-trap check: `git check-ignore` every path the spec
      instructs the implementer to CREATE; where a tracked ignore
      pattern would swallow it, the spec must carry an explicit
      un-ignore instruction (e.g. `!/bin/`).

Run through the checklist once. If the spec covers the problem, root cause, approach, and implementation details, commit it. Do not iterate.

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

1. Create timestamped file in `${SPECS_DIR}/`
2. Investigate thoroughly
3. Write complete spec with "Status: Requires Implementation"
4. `git add ${SPECS_DIR}/{spec}.md && git commit`
5. **STOP** - Don't implement

## Notes

- Specs are living documents until archived
- Update specs if requirements change (add timestamped note at top)
- Reference spec filename in commit messages
- Self-contained specs enable any agent to implement independently
- Timestamps ensure chronological ordering and uniqueness
