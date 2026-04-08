---
name: seq
description: Run N serial blind passes on the same job with commits between. Each pass works on the current code state with fresh eyes. Requires a clean worktree.
argument-hint: "<count>"
---

If other `/commands` appear in the user's message and you have not already called the Skill tool for them in this conversation, invoke each now. Do not re-invoke any skill that has already been loaded.

Do NOT re-invoke this skill via the Skill tool.
Do NOT re-read these instructions or any other document in a loop.
If you encounter any error or are unsure how to proceed, STOP and tell the user.
Execute the workflow below once, then stop.

## Task

You are running N serial, blind, independent passes on the same job. Each pass reviews and modifies the current code state, then its changes are committed before the next pass begins.

## Argument Parsing

Parse `$ARGUMENTS` for a number:

- **Bare number** (`2`, `3`, `4`, `5`) → pass count. Cap at 5.
- **Empty or non-numeric** → STOP and tell the user: "Usage: `/seq <count>`. Provide the number of serial passes (2–5)."

The job itself comes from the conversation context or from a composed skill.

## Pre-flight: Clean Worktree Check

Before anything else, verify the worktree is clean:

```bash
git diff --name-only
git diff --cached --name-only
```

If either command produces output, STOP and tell the user:

> "Working tree is dirty. `/seq` commits after each pass and needs a clean starting point. Please commit or stash your changes first, then retry."

Do not attempt to filter or work around dirty files.

## Determining the Job

Identify what the agents should work on:

1. If another skill is active in this invocation (e.g., `/doubt /seq 3`), that skill defines the job and prompt template.
2. Otherwise, use the most recent substantive task or request in the conversation.
3. If no job can be determined, STOP and tell the user: "No job found. Compose with a skill (e.g., `/doubt /seq 3`) or provide context first."

## Execution

1. Capture the base reference:
   ```bash
   BASE_SHA=$(git rev-parse HEAD)
   ```

2. For each pass (1 through N):

   a. **Resolve scope fresh** — run `git diff ${BASE_SHA}` to get the cumulative diff from the original state. Read touched files as they are now.

   b. **Launch subagent** with the job prompt, plus this preamble:
      ```
      This is pass ${PASS_NUMBER} of ${TOTAL_PASSES} in a sequential review.
      You have NO knowledge of prior passes. Review the code as-is with fresh eyes.
      ```
      Do NOT tell the agent what previous passes found. The blind constraint is critical.

   c. **After the agent returns** — identify and commit its changes:
      ```bash
      # Discover what the agent changed
      git diff --name-only
      # Stage only those files (never use git add . or git add -A)
      git add <each file from the diff output>
      git commit -m "seq: pass ${PASS_NUMBER} fixes"
      ```
      If `git diff --name-only` returns nothing, skip the commit and note "pass N: no changes."

   d. **Proceed to next pass** on the newly committed code.

3. After all passes complete, present a summary:
   - What each pass found and fixed
   - What the final pass flagged as remaining concerns (if any)
   - Remind the user they can `git log` to see each pass, `git diff HEAD~N` for the full delta, or revert individual passes
