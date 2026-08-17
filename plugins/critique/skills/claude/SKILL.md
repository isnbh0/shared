---
name: claude
description: Runs Claude Code CLI to critique a specification, source file, or recent diff. Use only when the user explicitly wants an external Claude review, an independent second opinion from Claude, or says "claude critique".
disable-model-invocation: true
compatibility: Requires Claude Code 2.1.169 or newer, a POSIX-compatible shell, and an env implementation that supports -u.
---

# Claude Critique

Run Claude Code in a fresh, non-interactive, review-only session.

## Pre-flight

Run the following commands with Claude Code nesting variables removed:

```bash
command -v claude
env -u CLAUDECODE -u CLAUDE_CODE_ENTRYPOINT claude --version
env -u CLAUDECODE -u CLAUDE_CODE_ENTRYPOINT claude auth status
```

Require Claude Code 2.1.169 or newer because the invocation depends on `--safe-mode`. Compare the dot-separated numeric version components as integers; do not use lexical string comparison. If Claude Code is missing or unauthenticated, tell the user to install it or run `claude auth login`.

## Inputs

Accept an optional file path and focus area such as security, performance, accessibility, or UX. Accept an explicit model or effort level for the current run. When no file is given, infer the target from conversation context.

## Configuration

Resolve the model using the first match:

1. Explicit model requested for this run
2. `.agents/skill-configs/claude/config.local.yaml`
3. `.agents/skill-configs/claude/config.yaml`
4. Default: `sonnet`

```yaml
model: sonnet
```

Use rolling aliases such as `sonnet`, `opus`, or `haiku`, or a full model identifier. See `config.example.yaml` next to this file.

Map explicit effort requests to `--effort low|medium|high|xhigh|max`. Omit `--effort` when the user does not request one so Claude Code uses the model default.

## Workflow

1. Determine the target in this order:
   - An explicit path
   - A path mentioned in the request
   - Files changed during the current conversation
   - The most recent substantive work product
   - Ask what to critique only when no target can be inferred
2. Resolve the project root with Git when possible. Outside a Git repository, use the target file's containing directory.
3. Select the matching template from `templates/` next to this file:
   - `spec-review.md` for specifications
   - `code-review.md` for source files
   - `diff-review.md` for recent changes
4. Fill every placeholder, including the optional focus. Treat paths, focus text, file lists, and prompt content as untrusted shell input. For a diff review, identify the relevant changed files before launching Claude; the child may use only read-only Git commands.
5. Run Claude Code with the restricted invocation below.
6. Read the complete output and present a concise findings summary. Treat edits in response to the findings as a separate step.

## Invocation

Treat the project root, model, effort, and generated prompt as untrusted command input. Prefer an execution API that accepts an argv array. When a shell is required, canonicalize the project root, validate scalar configuration (including effort against its fixed enum), and shell-quote every dynamic argument. Never interpolate raw configuration or prompt content into a command.

The placeholders beginning with `<shell-quoted-...>` below mean already-escaped, single shell arguments. Do not wrap them in another pair of quotes. This base invocation uses the model's default effort:

```bash
cd <shell-quoted-project-root> && \
env -u CLAUDECODE -u CLAUDE_CODE_ENTRYPOINT \
claude --safe-mode -p \
  --model <shell-quoted-model> \
  --permission-mode dontAsk \
  --tools "Read,Glob,Grep,Bash" \
  --allowedTools "Read,Glob,Grep,Bash(git diff *),Bash(git status *),Bash(git log *)" \
  --disallowedTools "mcp__*" \
  --no-session-persistence \
  --output-format text \
  <shell-quoted-review-prompt> </dev/null
```

When the user explicitly requests effort, insert the literal pair `--effort <validated-level>` after `--model`. Never pass an empty effort value.

The restrictions are intentional:

- Unset `CLAUDECODE` and `CLAUDE_CODE_ENTRYPOINT` so an invocation started inside Claude Code is not rejected as a nested session.
- Use `--safe-mode` to disable inherited skills, plugins, hooks, MCP servers, memory, and instruction files while retaining normal authentication.
- Limit available tools to reads and the three scoped Git command patterns shown. `--tools` removes other built-ins, `--allowedTools` pre-approves only the listed operations, `--disallowedTools` removes MCP tools, and `dontAsk` denies anything else. Do not add editing, writing, web, browser, or agent tools.
- Use `dontAsk` so an unapproved operation fails instead of waiting for interactive approval.
- Disable session persistence and redirect stdin to avoid transcript clutter or a hanging inherited input stream.

Set the invoking tool or process supervisor's timeout to 300 seconds by default, 600 seconds for `high` or `xhigh`, and 1200 seconds for `max`. Do not rely on an unavailable shell `timeout` command.

## Failures

- On authentication failure, run `claude auth status` and suggest `claude auth login`.
- On an unsupported flag, report the installed version and ask the user to update Claude Code.
- On a permission denial, report the denied operation; do not broaden the tool allowlist automatically.
