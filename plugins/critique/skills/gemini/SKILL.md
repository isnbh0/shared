---
name: gemini
description: Runs Google Gemini CLI to critique a spec or code file. Use when the user wants external AI review, a second opinion, or says "gemini critique".
argument-hint: "[file-path] [focus] [--model <model>]"
disable-model-invocation: true
---

# Gemini Critique

Run Google's Gemini CLI to get an independent critique of a file (spec, code, etc.).

## Pre-flight

Verify gemini is available: !`which gemini`

If gemini is not found, tell the user to install it:

```bash
npm install -g @anthropic-ai/gemini-cli  # or see https://github.com/anthropics/gemini-cli
```

## Usage

```
/critique:gemini $ARGUMENTS
```

- `$0` — optional file path to critique (relative or absolute)
- `$1` — optional focus area (e.g., "security", "performance", "UX gaps")
- `--model <model>` — override the gemini model for this invocation

All arguments are optional. When no file is given, infer the target from conversation context.

## Configuration

Config is resolved with the following precedence (first match wins):

1. **CLI flag** (`--model`) — one-off override
2. **Local config** (`.claude/skill-configs/gemini/config.local.yaml`) — personal/local scope, gitignored
3. **Project config** (`.claude/skill-configs/gemini/config.yaml`) — project scope, committed to repo
4. **Default** — `gemini-3.1-pro-preview`

```yaml
model: gemini-3.1-pro-preview  # model to use with gemini CLI
```

See `config.example.yaml` in the critique plugin's gemini skill for reference.

## Setup

1. Check if `$ARGUMENTS` contains `--model <model>`. If so, use that model and skip config lookup.
2. Check for config files (first match wins):
   - `.claude/skill-configs/gemini/config.local.yaml` (local scope, gitignored)
   - `.claude/skill-configs/gemini/config.yaml` (project scope, committed to repo)
3. If no config found, use `gemini-3.1-pro-preview` as the default.
4. Set `${MODEL}` to the resolved model name.

## How It Works

1. **Determine what to critique** — use one of these strategies, in priority order:
   - If `$0` is provided, use it as the file path
   - If the user mentions a file by name or path (e.g., `@games/foo/bar.js`), use that
   - If changes were made during the current conversation (specs written, code edited, etc.), critique those — use `git diff` against the state before the conversation's changes to identify the affected files and pass them to gemini
   - If the user says something like "critique this" or "get a second opinion", look at the most recent substantive work product in the conversation
   - If nothing can be inferred, ask the user what to critique
2. Resolve the working directory (project root)
3. Build a review prompt tailored to the content type — use the templates in `${CLAUDE_SKILL_DIR}/templates/`:
   - `spec-review.md` — for specification files
   - `code-review.md` — for source code files
   - `diff-review.md` — for reviewing recent changes
4. Run `gemini` non-interactively in sandbox mode
5. Present the findings to the user

## Invocation

```bash
cd <project-root> && \
SEATBELT_PROFILE=permissive-closed gemini \
  -s \
  -m ${MODEL} \
  -o text \
  "<review-prompt>"
```

**Flags:**
- `-m ${MODEL}` — the resolved model (default: `gemini-3.1-pro-preview`)
- `-s` — enable sandbox mode
- `-o text` — output as plain text
- `SEATBELT_PROFILE=permissive-closed` — restricts file writes and blocks network access

**Safety note:** The `--sandbox` flag combined with `SEATBELT_PROFILE=permissive-closed` restricts writes and blocks network, but is not as granular as Codex's `-s read-only`. The gemini process can still read all files in the project directory.

**Timeout:** 300 seconds

## After Running

1. Read the full gemini output (it may be persisted to a temp file if large)
2. Present findings to the user in a concise summary
3. If the user wants to act on the feedback, proceed with edits as a separate step

## Notes

- If gemini errors, check `gemini --version` and verify authentication
- Unlike the codex backend, gemini does not support reasoning effort levels
- Must `cd` to project root before running — gemini has no `-C` equivalent
