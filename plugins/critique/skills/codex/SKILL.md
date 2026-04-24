---
name: codex
description: Runs OpenAI Codex CLI to critique a spec or code file. Use when the user wants external AI review, a second opinion, or says "codex critique".
argument-hint: "[file-path] [focus] [--model <model>]"
disable-model-invocation: true
---

# Codex Critique

Run OpenAI's Codex CLI to get an independent critique of a file (spec, code, etc.).

## Pre-flight

Verify codex is available: !`which codex`

If codex is not found, tell the user to install and authenticate (`codex login`).

## Usage

```
/critique:codex $ARGUMENTS
```

- `$0` — optional file path to critique (relative or absolute)
- `$1` — optional focus area (e.g., "security", "performance", "UX gaps")
- `--model <model>` — override the codex model for this invocation

All arguments are optional. When no file is given, infer the target from conversation context.

## Configuration

Config is resolved with the following precedence (first match wins):

1. **CLI flag** (`--model`) — one-off override
2. **Local config** (`.claude/skill-configs/codex/config.local.yaml`) — personal/local scope, gitignored
3. **Project config** (`.claude/skill-configs/codex/config.yaml`) — project scope, committed to repo
4. **Default** — `gpt-5.5`

```yaml
model: gpt-5.5  # model to use with codex exec
```

See `config.example.yaml` in the critique plugin's codex skill for reference.

## Setup

1. Check if `$ARGUMENTS` contains `--model <model>`. If so, use that model and skip config lookup.
2. Check for config files (first match wins):
   - `.claude/skill-configs/codex/config.local.yaml` (local scope, gitignored)
   - `.claude/skill-configs/codex/config.yaml` (project scope, committed to repo)
3. If no config found, use `gpt-5.5` as the default.
4. Set `${MODEL}` to the resolved model name.

### Reasoning Effort

The user can request higher reasoning effort by saying things like "xhigh", "high effort", "think harder", or "deep review". Map these to the `--config model_reasoning_effort` flag:

| User says | Flag value |
|-----------|-----------|
| (default) | *(omit flag — uses codex default "medium")* |
| "high" | `high` |
| "xhigh", "maximum", "think hard" | `xhigh` |

## How It Works

1. **Determine what to critique** — use one of these strategies, in priority order:
   - If `$0` is provided, use it as the file path
   - If the user mentions a file by name or path (e.g., `@games/foo/bar.js`), use that
   - If changes were made during the current conversation (specs written, code edited, etc.), critique those — use `git diff` against the state before the conversation's changes to identify the affected files and pass them to codex
   - If the user says something like "critique this" or "get a second opinion", look at the most recent substantive work product in the conversation
   - If nothing can be inferred, ask the user what to critique
2. Resolve the working directory (project root)
3. Build a review prompt tailored to the content type — use the templates in `${CLAUDE_SKILL_DIR}/templates/`:
   - `spec-review.md` — for specification files
   - `code-review.md` — for source code files
   - `diff-review.md` — for reviewing recent changes
4. Run `codex exec` non-interactively with read-only sandbox
5. Present the findings to the user

## Invocation

```bash
codex exec \
  -m ${MODEL} \
  -s read-only \
  -C <project-root> \
  --config model_reasoning_effort="<effort>" \
  "<review-prompt>"
```

**Flags:**
- `-m ${MODEL}` — the resolved model (default: `gpt-5.5`)
- `-s read-only` — read-only sandbox (no file modifications)
- `-C <dir>` — set working directory so codex can read referenced files
- `--config model_reasoning_effort="<effort>"` — reasoning depth: `medium` (default), `high`, or `xhigh`. Omit for default. Higher effort = slower but more thorough analysis.

**Timeout:** 300 seconds at default effort, 600 seconds at high/xhigh (codex does more reasoning passes)

## After Running

1. Read the full codex output (it may be persisted to a temp file if large)
2. Present findings to the user in a concise summary
3. If the user wants to act on the feedback, proceed with edits as a separate step

## Notes

- If codex errors, check `codex --version` and suggest `codex login` if auth fails
