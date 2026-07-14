---
name: chunked
description: Sequence a task as ordered parts that add up to the whole. Each iteration may read prior iterations' outputs.
argument-hint: "<task>"
---

Honor every skill explicitly activated in the user's request exactly once. If another activated skill is not yet loaded and the host provides a skill-loading mechanism, load it through that mechanism. Do not reload an active skill.

Do NOT re-invoke this skill recursively.
Do NOT re-read these instructions or any other document in a loop.
If you encounter any error or are unsure how to proceed, STOP and tell the user.
Execute the workflow below once, then stop.

## Task

You are running an **ordered partition** of the user's task: a sequence of parts that together cover the whole. Iteration K may read the outputs of iterations 1..K-1 so it can deduplicate against, build on, or react to prior work.

## Determining the task

Identify what to partition:

1. If another skill is active in this request (for example, `skill(macros:mapreduce)`), that skill defines the per-chunk job and prompt template — chunked's role is to slice the scope it operates on.
2. Otherwise, use the most recent substantive task or request in the conversation.
3. If no task can be determined, STOP and tell the user: "No task found. Provide a task description or activate another skill with this one."

## Setup

1. Check for config files (first match wins):
   - `.agents/skill-configs/macros/config.local.yaml` (local scope, gitignored)
   - `.agents/skill-configs/macros/config.yaml` (project scope, committed to repo)
   - Legacy fallback (older installs): `.claude/skill-configs/macros/config.local.yaml`, then `.claude/skill-configs/macros/config.yaml`. If config is found only at a legacy path, use it and offer to move it to the new location.
2. **If no config found**: STOP and tell the user:
   > "No macros config found. I need a workspace directory to store reports.
   > You can either:
   > 1. Specify a custom path
   > 2. Use the default `.agent-workspace/macros`
   >
   > I'll create `.agents/skill-configs/macros/config.yaml` with your choice.
   > (See `config.example.yaml` in the macros plugin for reference.)"
   Wait for the user's response, then create the config file before continuing.
3. Set `${WORKSPACE_DIR}` to the resolved `workspace_dir`. All paths below use this variable.

## Workflow

### Step 1: Create outer run directory

```bash
TIMESTAMP=$(date +"%y%m%d-%H%M%S")
OUTER_RUN_DIR="${WORKSPACE_DIR}/${TIMESTAMP}-chunked-{task-slug}"
mkdir -p "${OUTER_RUN_DIR}"
```

Use a kebab-case `{task-slug}` describing the overall task.

### Step 2: Infer the partition

Read the task once and identify natural ordered boundaries — time windows, scope batches, phases, ranges, regions. Aim for parts that **disjointly cover the whole** and follow an obvious sequence. Require **at least 2 parts**; if the task isn't naturally partitionable into 2+ ordered slices, STOP and tell the user.

Write the partition plan to `${OUTER_RUN_DIR}/_partition.md` as a numbered list. Each entry is a `(slug, scoped sub-task description)` pair:

```markdown
# Partition: {task-slug}

1. **{slug-1}** — {scoped sub-task for iteration 1}
2. **{slug-2}** — {scoped sub-task for iteration 2}
3. **{slug-3}** — {scoped sub-task for iteration 3}
```

Each `{slug-K}` is short kebab-case (used in the chunk directory name). Each scoped sub-task must be a self-contained instruction the iteration-K agent can execute without re-reading the original task description.

Present a one-line summary of the partition to the user before dispatching iteration 1 (e.g., "Partitioning into 3 weekly batches: week-1, week-2, week-3").

### Step 3: Iterate sequentially

For K from 1 to N (where N is the number of partition slices):

1. **Build iteration K's task description** from the K-th partition slice.

2. **Tell iteration K about prior chunks.** Instruct iteration K (in natural language inside its prompt) to first read the contents of `${OUTER_RUN_DIR}/chunk-*/` for all K' < K, and use them to deduplicate against, build on, or react to prior work. Don't mandate a literal sentence — describe the intent and let the synthesizing agent phrase it for the actual prompt.

3. **Composition handoff.** If another orchestrator skill (for example, `skill(macros:mapreduce)`) is active in this request, run its full workflow once per partition slice, with the slice's scoped sub-task as that skill's input. If the composed orchestrator supports a workspace override, direct it to use `${OUTER_RUN_DIR}/chunk-${K}-{slug}` as its workspace so its nested run directory lands inside the chunk's directory and prior chunks remain readable. Complete one iteration's full workflow before starting the next.

   When no orchestrator is composed, dispatch a single subagent for iteration K and tell it to write its outputs under `${OUTER_RUN_DIR}/chunk-${K}-{slug}/`.

4. **Wait for iteration K to complete.** Verify outputs landed at the expected path (`${OUTER_RUN_DIR}/chunk-${K}-{slug}/` exists and is non-empty). If not, halt and tell the user plainly which iteration failed and what was missing.

5. **Do not start iteration K+1 until K is fully complete and verified.**

### Step 4: Final summary

After the last iteration completes, present a terse roll-up to the user: which chunks ran, what each produced, and the paths under `${OUTER_RUN_DIR}/`. No consolidated-report file is written. If the user wants one, they ask.

## Anti-patterns to Avoid

- **Don't parallelize across chunks.** Sequential ordering is the whole point — parallelism belongs *inside* a chunk (via `skill(macros:mapreduce)`), not across them.
- **Don't continue past a failed iteration without user follow-up.** If iteration K fails or produces nothing, halt and tell the user. Do not skip ahead or retry silently.
- **Don't re-partition mid-run.** The partition is fixed in Step 2. If it turns out wrong, halt and tell the user instead of mutating the plan during dispatch.
