---
name: gemini
description: Runs Google Gemini CLI to critique a spec or code file. Use when the user wants external AI review, a second opinion, or says "gemini critique".
disable-model-invocation: true
compatibility: The documented sandbox invocation requires the Gemini CLI, macOS Seatbelt, and a POSIX-compatible shell.
---

# Gemini Critique

Run Google's Gemini CLI to get an independent critique of a file (spec, code, etc.).

## Pre-flight

Run `command -v gemini` (or the platform equivalent) to verify that Gemini is available.

If gemini is not found, tell the user to install it:

```bash
npm install -g @google/gemini-cli  # or see https://github.com/google-gemini/gemini-cli
```

## Usage

Invoke with an optional file path to critique (relative or absolute) and an optional focus area (e.g., "security", "performance", "UX gaps"). To use a specific gemini model for this run, say so in the request.

All inputs are optional. When no file is given, infer the target from conversation context.

## Configuration

Config is resolved with the following precedence (first match wins):

1. **Explicit override** — the user asks to use a specific model for this run
2. **Local config** (`.agents/skill-configs/gemini/config.local.yaml`) — personal/local scope, gitignored
3. **Project config** (`.agents/skill-configs/gemini/config.yaml`) — project scope, committed to repo
4. **Legacy fallback** (`.claude/skill-configs/gemini/config.local.yaml`, then `config.yaml`) — older installs
5. **Default** — `gemini-3.1-pro-preview`

```yaml
model: gemini-3.1-pro-preview  # model to use with gemini CLI
```

See `config.example.yaml` in the critique plugin's gemini skill for reference.

## Setup

1. If the user explicitly asks to use a specific model, use it and skip config lookup.
2. Check for config files (first match wins):
   - `.agents/skill-configs/gemini/config.local.yaml` (local scope, gitignored)
   - `.agents/skill-configs/gemini/config.yaml` (project scope, committed to repo)
   - Legacy fallback (older installs): `.claude/skill-configs/gemini/config.local.yaml`, then `.claude/skill-configs/gemini/config.yaml`. If config is found only at a legacy path, use it and offer to move it to the new location.
3. If no config found, use `gemini-3.1-pro-preview` as the default.
4. Set `${MODEL}` to the resolved model name.

## How It Works

1. **Determine what to critique** — use one of these strategies, in priority order:
   - If the user provided a file path, use it
   - If the user mentions a file by name or path (e.g., `games/foo/bar.js`), use that
   - If changes were made during the current conversation (specs written, code edited, etc.), critique those — use `git diff` against the state before the conversation's changes to identify the affected files and pass them to gemini
   - If the user says something like "critique this" or "get a second opinion", look at the most recent substantive work product in the conversation
   - If nothing can be inferred, ask the user what to critique
2. Resolve the working directory (project root)
3. Build a review prompt tailored to the content type — use the templates in the `templates/` directory next to this skill (its base directory):
   - `spec-review.md` — for specification files
   - `code-review.md` — for source code files
   - `diff-review.md` — for reviewing recent changes
4. Run `gemini` non-interactively in sandbox mode
5. Present the findings to the user

## Invocation

The following read-only sandbox command is specific to macOS. On another platform, use that platform's supported Gemini sandbox with equivalent write and network restrictions.

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
