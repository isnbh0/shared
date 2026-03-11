---
description: Implement an existing specification
---

Do NOT invoke the spex skill via the Skill tool.
Do NOT re-read these instructions or any other document in a loop.
If you encounter any error or are unsure how to proceed, STOP and tell the user.
Execute the workflow below once, then stop.

## Task

You are implementing an existing specification. Your `$ARGUMENTS` contain the spec file path (if provided by the user).

Implement according to the spec. Do not write new specs in this session.

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

**Step 1: Read the spec**

If a spec file path was provided in `$ARGUMENTS`, use that path directly.

Otherwise, find the latest non-future spec automatically:

```bash
python3 -c "
import os
import re
import sys
from datetime import datetime

specs_dir = sys.argv[1]
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
" "${SPECS_DIR}"
```

The script outputs the filename of the latest spec. Construct the full path as `${SPECS_DIR}/{filename}` and read it completely.

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
5. **Archive spec to ${SPECS_DIR}/archive/implemented/**
6. **Git commit all changes**

Example:
```
TodoWrite:
- Implement feature X according to spec
- Run tests to verify requirements
- Update spec status to "Completed" with commit hash
- Archive spec to ${SPECS_DIR}/archive/implemented/
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
git mv ${SPECS_DIR}/{spec}.md ${SPECS_DIR}/active/{spec}.md
git add ${SPECS_DIR}/active/{spec}.md
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
mkdir -p ${SPECS_DIR}/archive/implemented
git mv ${SPECS_DIR}/active/{spec}.md ${SPECS_DIR}/archive/implemented/{spec}.md
git add ${SPECS_DIR}/archive/implemented/{spec}.md
# OR if not in active/
git mv ${SPECS_DIR}/{spec}.md ${SPECS_DIR}/archive/implemented/{spec}.md
git add ${SPECS_DIR}/archive/implemented/{spec}.md
```

**Step 8: Git add and commit everything**

```bash
# Add all changes (implementation + updated spec)
git add [files-you-modified]
git add ${SPECS_DIR}/archive/implemented/{spec}.md  # or wherever spec is

# Commit with reference to spec
git commit -m "feat: implement [feature name]

Implements spec: {timestamp}-name.md
- [Brief description of changes]
- [Another change]

Status: Completed"
```

## Implementation Quality Checklist

Before committing, verify:

- [ ] **All todos marked as completed**
- [ ] All spec requirements implemented
- [ ] Code follows best practices
- [ ] Tests pass / manual testing complete
- [ ] Spec status updated to "Completed"
- [ ] Spec includes commit hashes
- [ ] Spec includes completion date
- [ ] Spec archived to `${SPECS_DIR}/archive/implemented/`
- [ ] All files added to git (implementation + spec)
- [ ] Commit message references spec file
- [ ] No uncommitted changes remain

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

### Implementing a spec:
1. Read spec completely
2. **Create TodoWrite list with all steps including wrap-up**
3. Update status to "In Progress"
4. Implement according to spec + best practices
5. Test thoroughly
6. Update spec status to "Completed" with commits and date
7. Archive spec to `${SPECS_DIR}/archive/implemented/`
8. `git add [all-files] && git commit`
9. Done

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

## Notes

- Specs are living documents until archived
- Update specs if requirements change (add timestamped note at top)
- Reference spec filename in commit messages
- Self-contained specs enable any agent to implement independently
- Timestamps ensure chronological ordering and uniqueness
