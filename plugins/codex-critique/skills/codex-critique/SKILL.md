---
name: codex-critique
description: Runs OpenAI Codex CLI (GPT 5.4) to critique a spec or code file. Use when the user wants external AI review, a second opinion, or says "codex critique".
---

# Codex Critique

Run OpenAI's Codex CLI with GPT 5.4 to get an independent critique of a file (spec, code, etc.).

## Usage

```
/codex-critique [file-path] [focus]
```

- `file-path` — optional. The file to critique (relative or absolute)
- `focus` — optional focus area (e.g., "security", "performance", "UX gaps")

All arguments are optional. When no file is given, infer the target from conversation context.

### Reasoning Effort

The user can request higher reasoning effort by saying things like "xhigh", "high effort", "think harder", or "deep review". Map these to the `--config model_reasoning_effort` flag:

| User says | Flag value |
|-----------|-----------|
| (default) | *(omit flag — uses codex default "medium")* |
| "high" | `high` |
| "xhigh", "maximum", "think hard" | `xhigh` |

## How It Works

1. **Determine what to critique** — use one of these strategies, in priority order:
   - If a file path is provided as an argument, use it
   - If the user mentions a file by name or path (e.g., `@games/foo/bar.js`), use that
   - If changes were made during the current conversation (specs written, code edited, etc.), critique those — use `git diff` against the state before the conversation's changes to identify the affected files and pass them to codex
   - If the user says something like "critique this" or "get a second opinion", look at the most recent substantive work product in the conversation
   - If nothing can be inferred, ask the user what to critique
2. Resolve the working directory (project root)
3. Build a review prompt tailored to the content type (spec, code, diff)
4. Run `codex exec` non-interactively with read-only sandbox
5. Present the findings to the user

## Invocation

```bash
codex exec \
  -m gpt-5.4 \
  -s read-only \
  -C <project-root> \
  --config model_reasoning_effort="<effort>" \
  "<review-prompt>"
```

**Flags:**
- `-m gpt-5.4` — use GPT 5.4 model
- `-s read-only` — read-only sandbox (no file modifications)
- `-C <dir>` — set working directory so codex can read referenced files
- `--config model_reasoning_effort="<effort>"` — reasoning depth: `medium` (default), `high`, or `xhigh`. Omit for default. Higher effort = slower but more thorough analysis.

**Timeout:** 300 seconds at default effort, 600 seconds at high/xhigh (codex does more reasoning passes)

## Prompt Templates

### For specs

```
You are a senior engineer reviewing a technical specification.
Read the file <path> and also read the source files it references.
Then provide a thorough critique:
- Identify gaps, potential bugs, race conditions
- Flag missing edge cases or error handling
- Suggest alternative approaches where relevant
- Note accessibility or performance concerns
Be specific and constructive. Reference file paths and line numbers.
{focus ? "Focus especially on: <focus>" : ""}
```

### For code files

```
You are a senior engineer performing a code review.
Read the file <path> and any files it imports/references.
Provide a thorough review:
- Identify bugs, edge cases, and potential issues
- Flag security concerns (injection, XSS, etc.)
- Note performance issues or unnecessary complexity
- Suggest improvements, but keep scope to the file under review
Be specific and constructive. Reference line numbers.
{focus ? "Focus especially on: <focus>" : ""}
```

### For diffs (recent changes)

When critiquing recent changes rather than a single file, pass the diff content and tell codex which files to read for full context:

```
You are a senior engineer reviewing a set of recent code changes.
The following files were modified: <file-list>.
Read each modified file in full to understand the context, then review the changes critically:
- Identify bugs, edge cases, and regressions introduced by the changes
- Flag anything that looks incomplete or inconsistent with existing patterns
- Note if any changes need tests, docs, or migration steps
Be specific and constructive. Reference file paths and line numbers.
{focus ? "Focus especially on: <focus>" : ""}
```

## After Running

1. Read the full codex output (it may be persisted to a temp file if large)
2. Present findings to the user in a concise summary
3. If the user wants to act on the feedback, proceed with edits as a separate step

## Notes

- Codex CLI must be installed and authenticated (`codex login`)
- The ChatGPT-tier account does not support `o3` — use `gpt-5.4` as the default model
- If codex errors, check `codex --version` and suggest `codex login` if auth fails
