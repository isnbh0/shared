---
name: implement
description: Implement an existing specification
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
product choice not resolved by the request, specification, or repository, or no
defensible safe path remains after diagnosis.

## Task

You are implementing an existing specification. The user's request may include the spec file path.

Implement according to the spec. Do not write a replacement spec in this session. Updating an
existing gradual spec as its frontier advances is part of implementation.

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
   > (See `config.example.yaml` beside this skill for reference.)"
   Wait for the user's response, then create the config file before continuing.
4. Set `${SPECS_DIR}` to the resolved `workspace_dir`. All paths below use this variable.

## Workflow

**Step 1: Read the spec**

If the user provided a spec file path, use it directly.

Otherwise, find the latest non-future spec automatically:

```bash
python3 -c "
import os
import re
import sys
from datetime import datetime

specs_dir = sys.argv[1]
now = datetime.now()
pattern = re.compile(r'^(\d{6})-(\d{6})-(.*)')

valid_specs = []
for entry in os.listdir(specs_dir):
    full_path = os.path.join(specs_dir, entry)
    if not (os.path.isfile(full_path) or os.path.isdir(full_path)):
        continue
    match = pattern.match(entry)
    if match:
        date_part, time_part, _ = match.groups()
        year = int('20' + date_part[0:2])
        month = int(date_part[2:4])
        day = int(date_part[4:6])
        hour = int(time_part[0:2])
        minute = int(time_part[2:4])
        second = int(time_part[4:6])
        try:
            spec_dt = datetime(year, month, day, hour, minute, second)
            if spec_dt <= now:
                valid_specs.append((spec_dt, entry))
        except ValueError:
            continue

if valid_specs:
    latest = sorted(valid_specs, key=lambda x: x[0], reverse=True)[0]
    print(latest[1])
" "${SPECS_DIR}"
```

The script outputs the name of the latest spec (file or directory). Construct the full path as `${SPECS_DIR}/{name}`.

**Reading the spec** depends on whether it's a file or directory:

- **File** (single-phase spec): Read the `.md` file directly.
- **Directory** (phased spec): Read `{dir}/README.md` for the overview, then read every phase
  document it links in numeric order.

Understand:
- Problem statement
- Root cause
- Technical approach
- All implementation details
- Testing requirements

If a directory spec's overview contains `**Planning Mode:** Gradual`, follow the gradual workflow
below instead of Steps 2–8. Specifications without that exact field continue through the existing
workflow unchanged.

## Gradual Phased Specifications

A gradual implementation run handles exactly one concrete application phase, advances the
specification frontier in a separate commit, and stops. It does not continue into the next phase.

### Valid Resting States

Read the overview and all phase files in numeric order. Confirm that they match one of these states:

- **Initial:** the current frontier awaits concretization and the next phase is the trailing
  placeholder.
- **Ready:** earlier phases are complete, the current frontier is concrete and ready, and the next
  phase is the trailing placeholder.
- **Terminal:** every concrete phase is complete, there is no placeholder, and the spec is ready to
  archive.

If an explicitly selected spec is already terminal but not archived, archive it in a
specification-only commit and stop. No application work remains.

Before implementation, stop and repair the specification in a specification-only commit if phase
numbers are not monotonic, links do not resolve, a completed phase lacks a real application commit,
more than one concrete pending phase exists, or the nonterminal spec does not have exactly one
trailing placeholder.

### Concretize the Current Frontier

If the current frontier has `State: Awaiting concretization`:

1. Reinspect the repository and verify the overview's baseline against its current state.
2. Choose the smallest coherent step that materially advances the overall goal.
3. Rewrite the current phase in place using its concrete phase contract. Include a concrete outcome,
   verified entry state, repository-relative paths, completed-phase contracts, complete
   implementation guidance, exact tests, headless verification, and an application commit boundary.
4. Keep the following phase unchanged as the trailing placeholder.
5. Set the phase to `State: In Progress`. Update the overview's phase summary, set its status to `In
   Progress`, retain the current frontier, refresh the verified baseline, durable decisions, and
   deferred work, and set the next action to implement the current phase.

Do not introduce speculative content for later phases. Run the gradual quality gate, stage only the
specification directory, commit the concretization, and then continue with the concrete phase.

If the current frontier is already `State: Ready`, use it as written. Before application changes,
mark that phase and the overview `In Progress`, stage only the specification directory, and commit
that status change. When concretization and the status transition happen together, use one
specification-only commit.

### Implement One Phase

1. Track the concrete phase's implementation tasks, verification, application commit, and frontier
   update.
2. Implement only the current concrete phase.
3. Run every required test and verification command. Interactive verification is allowed only when
   the user explicitly authorized it.
4. Stage only application and test files; exclude the specification directory.
5. Commit the working application with the phase reference, following repository conventions.
6. Record the resulting application commit hash for the specification update.

The application commit must exist before the phase is marked complete. Do not combine application
changes with concretization, rollover, or archival changes.

### Complete or Advance

After the application commit, reinspect the repository and decide from evidence whether the overall
goal is complete.

If the goal is complete:

1. Mark the current phase and its checklist complete and record its application commit.
2. Remove the unused trailing placeholder.
3. Update the overview to `Status: Completed`, clear the current frontier, record the completion
   date, and make the next action `None — specification complete`.
4. Move the entire specification directory to `${SPECS_DIR}/archive/implemented/`.
5. Run the gradual quality gate, stage only the specification changes, commit them, and stop.

If more work remains:

1. Mark the current phase and its checklist complete and record its application commit.
2. Reinspect the repository and rewrite the existing trailing placeholder in place as the next
   concrete phase. Its choice must respond to the state left by the completed application commit.
3. Set the promoted phase to `State: Ready`. Add `P(N+2).md` with `State: Trailing placeholder` and
   no speculative implementation content.
4. Update the overview's verified baseline, durable decisions and contracts, deferred work, phase
   summary, links, and progress. Set the current frontier to the promoted phase, the status to
   `Requires Implementation`, and the next action to implement that phase.
5. Confirm that the spec now has completed phases, exactly one concrete ready phase, and exactly one
   trailing placeholder.
6. Run the gradual quality gate, stage only the specification changes, commit them, and stop before
   implementing the new frontier.

### Gradual Quality Gate

Before every gradual specification commit, verify:

- Every referenced existing path is tracked and available to a fresh agent; proposed paths are
  compatible with ignore rules.
- Any current concrete phase is independently implementable and contains exact tests and headless
  verification commands.
- No speculative implementation content appears in the trailing placeholder.
- Completed phase commits exist and are application commits for the recorded work.
- Phase numbers are monotonic, links resolve, and the overview agrees with the phase files.
- Only the intended specification files are staged.

**Step 2: Create implementation todo list**

**RECOMMENDED**: If your agent has a task/todo facility, use it to track ALL steps, including wrap-up (otherwise keep the checklist inline). This prevents forgetting to update/archive the spec after long implementations.

Create todos for:
1. Implementation tasks (from spec's Implementation Details)
2. Testing/verification
3. **Update spec status to "Completed"**
4. **Add commit hash to spec**
5. **Archive spec to ${SPECS_DIR}/archive/implemented/**
6. **Git commit all changes**

Example:
```
Track these steps:
- Implement feature X according to spec
- Run tests to verify requirements
- Update spec status to "Completed" with commit hash
- Archive spec to ${SPECS_DIR}/archive/implemented/
- Git add and commit all changes (code + spec)
```

**Step 3: Update spec status to "In Progress"**

Edit the spec's status field (in the `.md` file for single-phase specs, or in `README.md` for directory specs):

```markdown
**Status:** In Progress
**Started:** YYYY-MM-DD
```

Optional: Move to active directory

```bash
# Single-phase spec (file)
git mv ${SPECS_DIR}/{spec}.md ${SPECS_DIR}/active/{spec}.md

# Phased spec (directory)
git mv ${SPECS_DIR}/{spec}/ ${SPECS_DIR}/active/{spec}/
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

Edit the spec's status field (the `.md` file for single-phase specs, or `README.md` for directory specs):

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

# Single-phase spec (file)
git mv ${SPECS_DIR}/{spec}.md ${SPECS_DIR}/archive/implemented/{spec}.md
# OR from active/
git mv ${SPECS_DIR}/active/{spec}.md ${SPECS_DIR}/archive/implemented/{spec}.md

# Phased spec (directory)
git mv ${SPECS_DIR}/{spec}/ ${SPECS_DIR}/archive/implemented/{spec}/
# OR from active/
git mv ${SPECS_DIR}/active/{spec}/ ${SPECS_DIR}/archive/implemented/{spec}/
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
├── {timestamp}-name.md            # Single-phase specs (flat file)
├── {timestamp}-name/              # Phased specs (directory)
│   ├── README.md                  #   Overview, principles, decisions, progress
│   ├── P1-{name}.md              #   Phase 1 detail
│   ├── P2-{name}.md              #   Phase 2 detail
│   └── ...
├── active/                        # In progress (Status: In Progress)
├── archive/
│   ├── implemented/              # Completed (Status: Completed)
│   └── deprecated/               # Obsolete (Status: Deprecated)
└── drafts/                       # Work-in-progress ideas
```

## Quick Reference

### Implementing a spec:
1. Read spec completely
2. **Track a checklist with all steps including wrap-up**
3. Update status to "In Progress"
4. Implement according to spec + best practices
5. Test thoroughly
6. Update spec status to "Completed" with commits and date
7. Archive spec to `${SPECS_DIR}/archive/implemented/`
8. `git add [all-files] && git commit`
9. Done

### Implementing a phased spec (directory):
1. Read `README.md` for overview, then read each `PN-*.md` for phase details
2. Track a checklist with current phase + wrap-up steps
3. Update status in `README.md` to "In Progress"
4. Implement current phase following its `PN-*.md` file exactly
5. Update checklist items to `[x]` in the phase file as completed
6. Run tests and example workflow
7. Commit implementation with phase reference
8. If more phases remain, repeat from step 2
9. When all phases done: update `README.md` status, `git mv` entire directory to archive, final commit

## Notes

- Specs are living documents until archived
- Update specs if requirements change (add timestamped note at top)
- Reference spec filename in commit messages
- Self-contained specs enable any agent to implement independently
- Timestamps ensure chronological ordering and uniqueness
