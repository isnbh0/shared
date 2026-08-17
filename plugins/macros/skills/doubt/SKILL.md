---
name: doubt
description: Explicit-request macro. Activate only when the user directly requests this macro; never infer activation from task characteristics. Skill — Spawns an independent subagent to critique recent work with web research. Use when the user wants a second opinion, says "doubt this", or wants to verify code against docs.
---

Honor every skill explicitly activated in the user's request exactly once. If another activated skill is not yet loaded and the host provides a skill-loading mechanism, load it through that mechanism. Do not reload an active skill.

Do NOT re-invoke this skill recursively.
Do NOT re-read these instructions or any other document in a loop.
If you encounter any error or are unsure how to proceed, STOP and tell the user.
Execute the workflow below once, then stop.

## Task

You are orchestrating an independent, research-backed critique of recent work.

## Argument Parsing

Parse the user's request:

- **Empty** → auto-scope (see Scope Resolution below)
- **Any text** → freeform mode (use the text as the critique focus)

## Scope Resolution

Determine what to critique. Use the first match:

1. **Freeform prompt** — if the user's request contains text, use that as the critique focus. Still read relevant files and allow web research.
2. **Staged changes** — `git diff --cached`. If non-empty, this is the scope.
3. **Unstaged changes** — `git diff`. If non-empty, this is the scope.
4. **Last commit** — `git diff HEAD~1`. Use this as the scope.
5. **Conversation context** — if no git changes exist, look at the most recent substantive work in the conversation.
6. **Nothing found** — if none of the above yield a scope, STOP and tell the user: "No changes, commits, or context found to critique. Activate the doubt skill again with a freeform question."

For diff-based scopes: always read touched files in full (not just the diff). The diff shows what changed; the full file shows whether it fits.

Set `${SCOPE}` to a description of what was gathered (the diff content, the file list, or the freeform question).

## Agent Prompt Template

Use this prompt for the subagent. Replace `${SCOPE}` with the resolved scope.

For **diff/code** scope:

```
You are an independent code critic. Your job is to find real problems, not nitpick style.

## Context
${SCOPE}

## Instructions

1. Read the diff and each touched file in full. Understand what the code does and why.
2. Identify concerns: correctness bugs, logic errors, edge cases, security issues, robustness gaps, API misuse, missing error handling at system boundaries.
3. Research: search the web to verify assumptions. Check library docs, API references, known gotchas, and version-specific behavior. Cite your sources with URLs.
4. Recommend: for each concern, explain the concrete fix, but do not modify files.
5. Report: list what you found and recommend, ranked by severity.

## What NOT to do
- Don't flag style, formatting, or naming unless it causes a bug.
- Don't add comments, docstrings, or type annotations.
- Don't refactor working code.
- Don't add error handling for impossible scenarios.
- Don't touch code outside the scope of your critique.

## Output format
Severity-ranked bullet list. For each item:
- **[severity]** One-line description
- What you found → the concrete fix you recommend
- Source: [url] (if you researched it)
```

For **freeform** scope:

```
You are an independent research agent.

## Question
${SCOPE}

## Instructions

1. Read relevant code in the project for context.
2. Research the question on the web. Find authoritative sources.
3. If the research reveals issues in the code, explain the concrete fixes, but do not modify files.
4. Answer the question with evidence. Cite sources with URLs.

## Output format
Direct answer first, then supporting evidence as a bullet list with citations.
```

## Execution

1. Resolve scope.
2. Launch one subagent using the appropriate prompt template.
3. Present the agent's findings to the user as a terse, severity-ranked bullet list.

## Notes

- Launch the critic with read-only access. Do not grant editing or writing tools; applying findings is a separate user-authorized step.
- Web access is optional and is controlled by the host agent/tooling.
- If web access is unavailable, agents still produce useful critique — just without external verification.
