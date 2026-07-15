---
name: consensus
description: Run N blind agents on the same job in parallel, then merge findings into consensus/unique/conflicts. Agents report only — no edits for concurrent safety.
---

Honor every skill explicitly activated in the user's request exactly once. If another activated skill is not yet loaded and the host provides a skill-loading mechanism, load it through that mechanism. Do not reload an active skill.

Do NOT re-invoke this skill recursively.
Do NOT re-read these instructions or any other document in a loop.
If you encounter any error or are unsure how to proceed, STOP and tell the user.
Execute the workflow below once, then stop.

## Task

You are dispatching N independent, blind agents to work on the same job in parallel, then merging their findings.

## Argument Parsing

Parse the user's request for a number:

- **Bare number** (`2`, `3`, `4`, `5`) → agent count. Cap at 5.
- **Empty or non-numeric** → STOP and tell the user: "Provide the number of parallel agents (2–5) with the consensus skill."

The job itself comes from the conversation context or from a composed skill.

## Determining the Job

Identify what the agents should work on:

1. If another skill is active in this request (for example, `macros:doubt`), that skill defines the job and prompt template.
2. Otherwise, use the most recent substantive task or request in the conversation.
3. If no job can be determined, STOP and tell the user: "No job found. Activate a task-defining skill with the consensus skill, or provide context first."

## Execution

1. Prepare the agent prompt from the job. Prepend this constraint to each agent's prompt:

   ```
   You are one of ${N} independent agents reviewing the same work.
   Report your findings but do NOT apply fixes.
   List what you would fix and how. Do not modify any files.
   ```

   The no-edits constraint is non-negotiable. Parallel agents writing to the same files will produce conflicts and lost work.

2. Launch all N agents concurrently, batching the dispatch if the host supports it. Each gets the identical prompt. They are blind to each other.

3. After all agents return, **merge** their findings:
   - **Consensus** — issues flagged by 2+ agents. Lead with these.
   - **Unique finds** — issues flagged by only one agent. Present with attribution ("agent 1 noted…", "agent 2 noted…").
   - **Conflicts** — if agents disagree, present both positions.

4. Present one unified, terse list to the user. No per-agent sections.
