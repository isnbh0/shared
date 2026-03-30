---
name: mapreduce
description: Split a task into parallel chunks, dispatch subagents, and consolidate results
---

Do NOT re-invoke this skill via the Skill tool.
Do NOT re-read these instructions or any other document in a loop.
If you encounter any error or are unsure how to proceed, STOP and tell the user.
Execute the workflow below once, then stop.

## Task

You are orchestrating a **map-reduce** execution of the user's task. Your `$ARGUMENTS` contain the task description from the user.

Your job is to:
1. Analyze the task and determine whether it can be safely parallelized
2. If yes: split into 2+ independent chunks
3. (Optional) Build shared context that all chunks need — terminology, conventions, reference material
4. Dispatch parallel subagents to work on each chunk (map phase)
5. Dispatch a final subagent to consolidate all results (reduce phase)

## Setup

1. Check if `$ARGUMENTS` contains `--workspace <dir>`. If so, use that directory and skip config lookup.
2. Check for config files (first match wins):
   - `.claude/skill-configs/macros/config.local.yaml` (local scope, gitignored)
   - `.claude/skill-configs/macros/config.yaml` (project scope, committed to repo)
3. **If no config found**: STOP and tell the user:
   > "No macros config found. I need a workspace directory to store reports.
   > You can either:
   > 1. Specify a custom path
   > 2. Use the default `.agent-workspace/macros`
   >
   > I'll create `.claude/skill-configs/macros/config.yaml` with your choice.
   > (See `config.example.yaml` in the macros plugin for reference.)"
   Wait for the user's response, then create the config file before continuing.
4. Set `${WORKSPACE_DIR}` to the resolved `workspace_dir`. All paths below use this variable.

## Workflow

### Step 1: Create run directory

```bash
TIMESTAMP=$(date +"%y%m%d-%H%M%S")
RUN_DIR="${WORKSPACE_DIR}/${TIMESTAMP}-descriptive-task-name"
mkdir -p "${RUN_DIR}"
```

Use a kebab-case name that describes the overall task.

### Step 2: Analyze and plan chunks (MAP planning)

Read `$ARGUMENTS` carefully. First, determine whether the task is parallelizable at all.

**Bail out if the task is not safely splittable.** Tell the user and execute the task sequentially instead. Signs a task should NOT be parallelized:
- Work centers on a single file or tightly coupled set of files (e.g., a migration, a lockfile, a shared schema)
- Steps have serial dependencies where each step's output is the next step's input
- The task involves a single logical change that would be incoherent if split (e.g., rename a function and all its call sites)
- Splitting would require multiple chunks to modify the same files

If the task IS parallelizable, determine how to split into **2 or more independent chunks**. Each chunk must be:

- **Self-contained** — completable without knowledge of other chunks' results
- **Non-overlapping** — no two chunks modify the same files or produce conflicting outputs
- **Roughly equal in scope** — balanced workload across subagents

Common splitting strategies:
- **By file/directory**: Different parts of the codebase
- **By concern**: e.g., frontend vs backend vs tests vs docs
- **By subtask**: Independent steps that don't depend on each other
- **By scope**: e.g., different modules, different endpoints, different components

Write a brief plan to the user explaining your chunking strategy before proceeding. If shared context is needed (see Step 3), mention that too.

### Step 3: Build shared context (CONTEXT phase — optional)

**When to use this step**: When chunks need consistent assumptions, shared terminology, or common reference material. Skip this step if chunks are truly independent and don't need alignment.

**Signs you need shared context**:
- Chunks produce user-facing content that must be consistent (tone, terminology, naming)
- Chunks reference the same domain concepts that could be interpreted differently
- The task involves transforming/translating content where style must be uniform
- Multiple chunks will make parallel design decisions that should agree

**What shared context typically includes**:
- **Synopsis/overview** — high-level summary so each chunk understands its place in the whole
- **Glossary/terminology** — agreed-upon terms, translations, naming conventions
- **Style/conventions** — tone, formatting rules, patterns to follow
- **Reference material** — existing code patterns, API shapes, data structures that chunks should conform to

**How to build it**:

1. Investigate the task scope (read relevant files, understand the domain)
2. Write the shared context to `${RUN_DIR}/_context.md`:

```markdown
# Shared Context: {task-name}

## Overview
[What the overall task is trying to accomplish. Enough for any chunk agent to understand the big picture.]

## Glossary / Terminology
[Key terms, naming conventions, translations — anything that must be consistent across chunks.]

## Conventions
[Style rules, formatting patterns, architectural decisions that all chunks must follow.]

## Reference Material
[Pointers to existing files, patterns, or examples that chunks should conform to. Include file paths or inline snippets as needed.]
```

3. Keep it concise — every subagent will read this file, so avoid bloat. Aim for the minimum context needed for consistency. If it exceeds ~200 lines, split into:
   - `_context.md` — core conventions every chunk must read (glossary, style rules, overview)
   - `_reference.md` — supplementary material (full examples, data structures). Only instruct chunks to read this if their assignment specifically needs it.

**Context delivery model**: Subagents read context files from disk. Do NOT paste context file contents into subagent prompts. Instead, instruct each subagent to read `${RUN_DIR}/_context.md` as its first action. You MAY quote 1-2 critical constraints inline (e.g., "all function names must use snake_case") as a guard, but the file is the source of truth.

**Source-of-truth rule**: `_context.md` is authoritative for **decisions and conventions** (naming, style, design choices agreed upon during planning). The **repository** is authoritative for **current code state** (what exists, what imports what, actual implementations). If `_context.md` summarizes or quotes code and the actual repo differs, the repo wins for code facts — but conventions in `_context.md` still govern new work.

**IMPORTANT**: This step runs synchronously before the map phase. Do NOT parallelize context-building with chunk dispatch — the context must be complete before any subagent starts.

### Step 4: Dispatch MAP subagents (parallel)

Launch all chunk subagents **in a single message** using multiple Agent tool calls so they run in parallel.

Each subagent prompt MUST include:

1. **The chunk assignment** — exactly what this subagent is responsible for
2. **The full task context** — enough background so the subagent can work independently
3. **Shared context** (if Step 3 was performed) — instruct the subagent: "Before starting work, read `${RUN_DIR}/_context.md` and follow its conventions." You may quote 1-2 critical constraints inline as a guard, but do NOT paste the full context file into the prompt.
4. **Report instructions** — the subagent MUST write a report file when done:

```
Your report MUST be written to: {RUN_DIR}/chunk-{N}-{chunk-name}.md

The report must include:
## Chunk: {chunk-name}
### What was done
[Detailed description of work performed]
### Files modified
[List of files created/modified/deleted with brief descriptions]
### Key decisions
[Any non-obvious choices made and why]
### Issues or concerns
[Anything the consolidation agent should know about]
### Status
[Complete / Partial / Blocked — and explanation if not complete]
```

5. **Boundary constraints** — what NOT to touch (other chunks' territory)

**IMPORTANT**: All subagents MUST be launched in a single message so they execute in parallel. Do NOT launch them sequentially.

### Step 5: Wait for all MAP subagents to complete

All subagents must finish before proceeding.

During Step 4, you launched N subagents with known report filenames (e.g., `chunk-1-frontend.md`, `chunk-2-backend.md`). Check each expected file individually — do NOT rely on glob matching:

```bash
# Check each expected report by name
test -f "${RUN_DIR}/chunk-1-frontend.md" && echo "chunk-1: OK" || echo "chunk-1: MISSING"
test -f "${RUN_DIR}/chunk-2-backend.md" && echo "chunk-2: OK" || echo "chunk-2: MISSING"
# ... repeat for each expected chunk
```

If any reports are missing, this is NOT a fatal error — proceed to the reduce phase but include the missing chunk names in the reducer's prompt so it can account for gaps.

### Step 6: Dispatch REDUCE subagent

Launch a single subagent to consolidate all chunk results. Its prompt MUST include:

1. **The original task** — full context of what was being accomplished
2. **The chunking strategy** — how work was divided and which chunks were expected
3. **Missing chunks** (if any) — which reports were not found in Step 5
4. **Shared context** (if Step 3 was performed) — instruct the reducer to read `${RUN_DIR}/_context.md` as the authoritative source for conventions and decisions
5. **Report locations** — paths to all chunk reports to read
6. **Consolidation instructions**:

```
You are the consolidation agent for a map-reduce execution.

## Phase 1: Read and understand

1. Read the shared context file (if it exists): {RUN_DIR}/_context.md
2. Read ALL chunk reports: {list each expected report path}
3. Note which chunks reported Complete vs Partial vs Blocked

## Phase 2: Verify integration

If any chunks produced code or file changes:

1. Read the actual modified files (don't just trust the reports — verify the repo state)
2. Check for conflicts:
   - No conflicting modifications to the same files
   - Imports/dependencies are consistent across chunks
   - No duplicated work
   - Naming and style consistent with shared context (if present)
3. If chunks made conflicting decisions, shared context is authoritative for conventions and design choices. If shared context doesn't cover the conflict, prefer the approach that is more consistent with existing code patterns.
4. Fix any integration issues you find

If the project has a test/build/lint command, run it to verify nothing is broken.

## Phase 3: Handle incomplete chunks

For Partial chunks: assess whether the completed portion integrates cleanly. Note what remains.
For Blocked chunks: document the blocker. Do NOT attempt the blocked work unless the blocker is trivially resolvable.
For Missing chunks (report never written): check if the subagent made any file changes anyway (look for uncommitted modifications in that chunk's territory). Document findings.

## Phase 4: Write consolidated report

Write to: {RUN_DIR}/consolidated-report.md

# Consolidated Report: {task-name}
**Date:** YYYY-MM-DD HH:MM:SS
**Chunks:** {N} dispatched, {M} complete, {P} partial/blocked/missing

## Summary
[High-level summary of what was accomplished across all chunks]

## Work Performed
[Combined description organized by logical area, not by chunk]

## Files Modified
[Deduplicated list of all files created/modified/deleted — verified against actual repo state]

## Key Decisions
[Consolidated decisions from all chunks]

## Integration Notes
[Any conflicts found, how they were resolved, and which source of truth was used]

## Verification
[What verification was performed: tests run, builds checked, files inspected]

## Incomplete Work
[What remains from partial/blocked/missing chunks, if any]

## Status
[Overall status: Complete / Partial — with explanation]
```

### Step 7: Report to user

After the reduce subagent completes:

1. Read `${RUN_DIR}/consolidated-report.md`
2. Present a concise summary to the user
3. Note the report location for their reference

If the consolidated report is missing or the reducer failed: tell the user the reduce phase did not complete, point them to the individual chunk reports in `${RUN_DIR}/` for partial results, and report the run as incomplete.

## Anti-patterns to Avoid

**Avoid sequential dispatch**: All map subagents MUST be launched in parallel in a single message. Launching them one-by-one defeats the purpose.

**Avoid overlapping chunks**: If two subagents modify the same file, the last one to finish wins and the other's work is lost. Plan chunks to avoid file conflicts.

**Avoid trivial splits**: Don't split a 5-minute task into 5 chunks. The overhead of coordination should be worth the parallelism. Use 2-3 chunks for moderate tasks, more for larger ones.

**Avoid empty reduce**: Even if chunks seem independent, always run the reduce phase — it catches integration issues and produces the consolidated record.

## Notes

- Reports persist in `${WORKSPACE_DIR}/` for future reference
- Each run gets its own timestamped directory for isolation
- The consolidated report is the authoritative record of what was done
- Chunk reports are retained as detailed backup
