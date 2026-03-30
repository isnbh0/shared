---
name: doubt
description: Spawns independent subagent(s) to critique recent work with web research. Use when the user wants a second opinion, says "doubt this", or wants to verify code against docs.
argument-hint: "[count | --seq N | \"freeform question\"]"
---

Do NOT re-invoke this skill via the Skill tool.
Do NOT re-read these instructions or any other document in a loop.
If you encounter any error or are unsure how to proceed, STOP and tell the user.
Execute the workflow below once, then stop.

## Task

You are orchestrating an independent, research-backed critique of recent work. Your `$ARGUMENTS` control the mode and scope.

## Argument Parsing

Parse `$ARGUMENTS`:

- **Empty** → single agent, auto-scope
- **Bare number** (`2`, `3`) → parallel mode, that many blind agents. Cap at 3.
- **`--seq N`** → sequential mode, N passes. Cap at 3.
- **Quoted string or free text** that isn't a number/flag → freeform mode (single agent).
- If both a number and `--seq` appear, prefer `--seq`.

## Scope Resolution

Determine what to critique. Use the first match:

1. **Freeform prompt** — if `$ARGUMENTS` contains a non-flag string, use that as the critique focus. Still read relevant files and allow web research.
2. **Staged changes** — `git diff --cached`. If non-empty, this is the scope.
3. **Unstaged changes** — `git diff`. If non-empty, this is the scope.
4. **Last commit** — `git diff HEAD~1`. Use this as the scope.
5. **Conversation context** — if no git changes exist, look at the most recent substantive work in the conversation.
6. **Nothing found** — if none of the above yield a scope, STOP and tell the user: "No changes, commits, or context found to critique. Try again with a freeform question, e.g. `/doubt \"your question\"`."

For diff-based scopes: always read touched files in full (not just the diff). The diff shows what changed; the full file shows whether it fits.

Set `${SCOPE}` to a description of what was gathered (the diff content, the file list, or the freeform question).

## Agent Prompt Template

Use this prompt for each subagent. Replace `${SCOPE}` with the resolved scope.

For **diff/code** scope:

```
You are an independent code critic. Your job is to find real problems, not nitpick style.

## Context
${SCOPE}

## Instructions

1. Read the diff and each touched file in full. Understand what the code does and why.
2. Identify concerns: correctness bugs, logic errors, edge cases, security issues, robustness gaps, API misuse, missing error handling at system boundaries.
3. Research: use WebSearch and WebFetch to verify assumptions. Check library docs, API references, known gotchas, and version-specific behavior. Cite your sources with URLs.
4. Fix: for each concern, apply the fix directly using the Edit tool. Own your suggestions — don't just describe, do. (In parallel mode, skip this step — report only.)
5. Report: list what you found and fixed (or would fix), ranked by severity. For anything you flagged but chose not to fix, explain why.

## What NOT to do
- Don't flag style, formatting, or naming unless it causes a bug.
- Don't add comments, docstrings, or type annotations.
- Don't refactor working code.
- Don't add error handling for impossible scenarios.
- Don't touch code outside the scope of your critique.

## Output format
Severity-ranked bullet list. For each item:
- **[severity]** One-line description
- What you found → what you fixed (or why you didn't)
- Source: [url] (if you researched it)
```

For **freeform** scope:

```
You are an independent research agent.

## Question
${SCOPE}

## Instructions

1. Read relevant code in the project for context.
2. Research the question using WebSearch and WebFetch. Find authoritative sources.
3. If the research reveals issues in the code, fix them using the Edit tool.
4. Answer the question with evidence. Cite sources with URLs.

## Output format
Direct answer first, then supporting evidence as a bullet list with citations.
```

## Mode: Single Agent (default)

1. Resolve scope.
2. Launch one subagent with the Agent tool using the appropriate prompt template.
3. Present the agent's findings to the user as a terse, severity-ranked bullet list.

## Mode: Parallel (`/doubt N`)

1. Resolve scope.
2. Launch N agents **in a single message** (parallel tool calls). Each gets the same scope but with this addition to the prompt: **"Report your findings but do NOT apply fixes via the Edit tool. List what you would fix and how."** Parallel agents must not edit files — concurrent edits to the same files will conflict.
3. After all agents return, **merge** their findings:
   - **Consensus** — issues flagged by multiple agents. Lead with these.
   - **Unique finds** — issues flagged by only one agent. Present with attribution ("agent 1 noted…", "agent 2 noted…").
   - **Conflicts** — if agents disagree, present both positions.
4. Present one unified, terse list. No per-agent sections.

## Mode: Sequential (`/doubt --seq N`)

Run N serial passes. Each pass is a **blind, independent critique** of the current code state. The agent critiques AND applies fixes.

For each pass (1 through N):

1. **Resolve scope fresh** — re-run `git diff` or read files as they are now (not cached from a prior pass).
2. **Launch subagent** with the agent prompt template, plus this preamble:
   ```
   This is pass ${PASS_NUMBER} of ${TOTAL_PASSES} in a sequential review.
   You have NO knowledge of prior passes. Review the code as-is with fresh eyes.
   ```
   Do NOT tell the agent what previous passes found. The blind constraint is critical.
3. **After the agent returns** — identify and commit its changes:
   ```bash
   # Discover what the agent changed
   git diff --name-only
   # Stage only those files (never use git add . or git add -A)
   git add <each file from the diff output>
   git commit -m "doubt: pass ${PASS_NUMBER} fixes"
   ```
   If `git diff --name-only` returns nothing, skip the commit and note "pass N: no changes."
4. **Proceed to next pass** on the newly committed code.

After all passes complete, present a summary:
- What each pass found and fixed
- What the final pass flagged as remaining concerns (if any)
- Remind the user they can `git log` to see each pass, `git diff HEAD~N` for the full delta, or revert individual passes

## Notes

- Permission control (whether agents can edit files, access web) is handled at the Claude Code tooling level. This skill assumes full access.
- If WebSearch/WebFetch are unavailable, agents still produce useful critique — just without external verification.
- `/doubt` complements `/critique`. Use `/critique` for a different model's perspective (cross-model reasoning diversity). Use `/doubt` for same-model, research-backed verification.
