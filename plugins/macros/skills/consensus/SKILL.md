---
name: consensus
description: Run N blind agents on the same job in parallel, then merge findings into consensus/unique/conflicts. Agents report only — no edits for concurrent safety.
argument-hint: "<count>"
---

Do NOT re-invoke this skill via the Skill tool.
Do NOT re-read these instructions or any other document in a loop.
If you encounter any error or are unsure how to proceed, STOP and tell the user.
Execute the workflow below once, then stop.

## Task

You are dispatching N independent, blind agents to work on the same job in parallel, then merging their findings.

## Argument Parsing

Parse `$ARGUMENTS` for a number:

- **Bare number** (`2`, `3`, `4`, `5`) → agent count. Cap at 5.
- **Empty or non-numeric** → STOP and tell the user: "Usage: `/consensus <count>`. Provide the number of parallel agents (2–5)."

The job itself comes from the conversation context or from a composed skill.

## Determining the Job

Identify what the agents should work on:

1. If another skill is active in this invocation (e.g., `/doubt /consensus 3`), that skill defines the job and prompt template.
2. Otherwise, use the most recent substantive task or request in the conversation.
3. If no job can be determined, STOP and tell the user: "No job found. Compose with a skill (e.g., `/doubt /consensus 3`) or provide context first."

## Execution

1. Prepare the agent prompt from the job. Prepend this constraint to each agent's prompt:

   ```
   You are one of ${N} independent agents reviewing the same work.
   Report your findings but do NOT apply fixes via the Edit tool.
   List what you would fix and how. Do not modify any files.
   ```

   The no-edits constraint is non-negotiable. Parallel agents writing to the same files will produce conflicts and lost work.

2. Launch all N agents **in a single message** (parallel tool calls). Each gets the identical prompt. They are blind to each other.

3. After all agents return, **merge** their findings:
   - **Consensus** — issues flagged by 2+ agents. Lead with these.
   - **Unique finds** — issues flagged by only one agent. Present with attribution ("agent 1 noted…", "agent 2 noted…").
   - **Conflicts** — if agents disagree, present both positions.

4. Present one unified, terse list to the user. No per-agent sections.
