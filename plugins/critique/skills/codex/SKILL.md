---
name: codex
description: Runs OpenAI Codex CLI to critique a spec or code file. Use when the user wants external AI review, a second opinion, or says "codex critique".
disable-model-invocation: true
compatibility: Requires the Codex CLI and a POSIX-compatible shell for the documented invocation.
---

# Codex Critique

Run OpenAI's Codex CLI to get an independent critique of a file (spec, code, etc.).

## Pre-flight

Run `command -v codex` (or the platform equivalent) to verify that Codex is available.

If codex is not found, tell the user to install and authenticate (`codex login`).

## Usage

Invoke with an optional file path to critique (relative or absolute) and an optional focus area (e.g., "security", "performance", "UX gaps"). To use a specific codex model for this run, say so in the request.

All inputs are optional. When no file is given, infer the target from conversation context.

## Configuration

Config is resolved with the following precedence (first match wins):

1. **Explicit override** — the user asks to use a specific model for this run
2. **Local config** (`.agents/skill-configs/codex/config.local.yaml`) — personal/local scope, gitignored
3. **Project config** (`.agents/skill-configs/codex/config.yaml`) — project scope, committed to repo
4. **Legacy fallback** (`.claude/skill-configs/codex/config.local.yaml`, then `config.yaml`) — older installs
5. **Default** — `gpt-5.6-terra`

```yaml
model: gpt-5.6-terra  # model to use with codex exec
```

Available tiers: `gpt-5.6-sol` (deepest reasoning, most expensive), `gpt-5.6-terra` (balanced), `gpt-5.6-luna` (cheapest).

See `config.example.yaml` in the critique plugin's codex skill for reference.

## Setup

1. If the user explicitly asks to use a specific model, use it and skip config lookup.
2. Check for config files (first match wins):
   - `.agents/skill-configs/codex/config.local.yaml` (local scope, gitignored)
   - `.agents/skill-configs/codex/config.yaml` (project scope, committed to repo)
   - Legacy fallback (older installs): `.claude/skill-configs/codex/config.local.yaml`, then `.claude/skill-configs/codex/config.yaml`. If config is found only at a legacy path, use it and offer to move it to the new location.
3. If no config found, use `gpt-5.6-terra` as the default.
4. Set `${MODEL}` to the resolved model name.

### Reasoning Effort

The user can request higher reasoning effort by saying things like "xhigh", "high effort", "think harder", or "deep review". Map these to the `--config model_reasoning_effort` flag:

| User says | Flag value |
|-----------|-----------|
| (default) | *(omit flag — uses codex default "medium")* |
| "high" | `high` |
| "xhigh", "think hard" | `xhigh` |
| "max", "maximum", "deep review" | `max` |
| "ultra" | `ultra` |

`max` and `ultra` only pay off on `gpt-5.6-sol` — the lower tiers accept them but have less reasoning ceiling to spend. When the user asks for max/ultra and the resolved model is terra or luna, use sol for that run and say so. `ultra` makes codex delegate to subagents; it is the slowest and most expensive setting.

## How It Works

1. **Determine what to critique** — use one of these strategies, in priority order:
   - If the user provided a file path, use it
   - If the user mentions a file by name or path (e.g., `games/foo/bar.js`), use that
   - If changes were made during the current conversation (specs written, code edited, etc.), critique those — use `git diff` against the state before the conversation's changes to identify the affected files and pass them to codex
   - If the user says something like "critique this" or "get a second opinion", look at the most recent substantive work product in the conversation
   - If nothing can be inferred, ask the user what to critique
2. Resolve the working directory (project root)
3. Build a review prompt tailored to the content type — use the templates in the `templates/` directory next to this skill (its base directory):
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
  "<review-prompt>" </dev/null
```

**Flags:**
- `-m ${MODEL}` — the resolved model (default: `gpt-5.6-terra`)
- `-s read-only` — read-only sandbox (no file modifications)
- `-C <dir>` — set working directory so codex can read referenced files
- `--config model_reasoning_effort="<effort>"` — reasoning depth: `medium` (default), `high`, `xhigh`, `max`, or `ultra`. Omit for default. Higher effort = slower but more thorough analysis.

**Stdin redirect (`</dev/null`) is required.** In some host-agent spawn environments, non-TTY stdin can remain open and cause `codex exec` to hang while reading additional input. Redirecting from `/dev/null` gives codex an immediate EOF.

**Timeout:** 300 seconds at default effort, 600 seconds at high/xhigh, 1200 seconds at max/ultra (codex does more reasoning passes; ultra also fans out to subagents)

## After Running

1. Read the full codex output (it may be persisted to a temp file if large)
2. Present findings to the user in a concise summary
3. If the user wants to act on the feedback, proceed with edits as a separate step

## Notes

- If codex errors, check `codex --version` and suggest `codex login` if auth fails
