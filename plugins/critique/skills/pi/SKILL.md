---
name: pi
description: Runs the pi coding-agent CLI to critique a specification, source file, or recent diff using whichever model provider pi has configured. Use only when the user explicitly wants an external pi review, an independent second opinion through pi, or says "pi critique".
disable-model-invocation: true
compatibility: Requires the pi CLI (npm @earendil-works/pi-coding-agent) and a POSIX-compatible shell.
---

# Pi Critique

Run pi in a fresh, non-interactive, read-only session. Pi is a multi-provider adapter, so this skill reaches whatever models pi has wired locally.

## Pre-flight

```bash
command -v pi
pi --version
```

If pi is missing, tell the user to install it with `npm install -g @earendil-works/pi-coding-agent`.

After resolving the model (see Configuration), and only when a model was resolved, verify credentials:

```bash
pi auth check --model <shell-quoted-provider/model>
```

When no model was resolved, skip this check. Pi's auth subcommands require a provider or model argument, and the run itself reports credential problems in its output.

## Inputs

Accept an optional file path and focus area such as security, performance, accessibility, or UX. Accept an explicit model or thinking level for the current run. When no file is given, infer the target from conversation context.

## Configuration

Resolve the model using the first match:

1. Explicit model requested for this run
2. `.agents/skill-configs/pi/config.local.yaml`
3. `.agents/skill-configs/pi/config.yaml`
4. None: omit the model flag entirely so pi uses its own configured default

```yaml
model: openai-codex/gpt-5.6-terra
```

Use pi's `provider/model` form. Run `pi --list-models` to see what is available. See `config.example.yaml` next to this file. Some providers reached through pi bill per token rather than against a subscription; do not switch providers on the user's behalf.

Map explicit thinking requests such as "high", "xhigh", "max", or "think harder" to `--thinking low|medium|high|xhigh|max`. Omit `--thinking` when the user does not request one so pi's configured default applies.

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
4. Fill every placeholder, including the optional focus. Treat paths, focus text, file lists, diff text, and prompt content as untrusted shell input. For a diff review, run the read-only Git diff yourself before launching pi and embed the output in the `<diff>` placeholder. The child has no shell and cannot run Git.
5. Run pi with the restricted invocation below.
6. Read the complete output and present a concise findings summary. Treat edits in response to the findings as a separate step.

## Invocation

Treat the project root, model, thinking level, and generated prompt as untrusted command input. Prefer an execution API that accepts an argv array. When a shell is required, canonicalize the project root, validate scalar configuration (including the thinking level against its fixed enum), and shell-quote every dynamic argument. Never interpolate raw configuration or prompt content into a command.

The placeholders beginning with `<shell-quoted-...>` below mean already-escaped, single shell arguments. Do not wrap them in another pair of quotes. This base invocation uses pi's default model and thinking level:

```bash
cd <shell-quoted-project-root> && \
pi -p \
  --no-session --no-skills --no-extensions --no-prompt-templates \
  --no-context-files --no-approve \
  --tools read,grep,find,ls \
  --mode text \
  <shell-quoted-review-prompt> </dev/null
```

When a model was resolved, insert the literal pair `--model <shell-quoted-provider/model>` after `-p`. When the user explicitly requests thinking, insert `--thinking <validated-level>`. Never pass an empty value for either.

The restrictions are intentional:

- Pi has no read-only sandbox and cannot scope `bash` to specific commands, so `bash` is excluded. `--tools` limits the child to the four read-only builtins. Do not add `bash`, `edit`, `write`, or any extension tool.
- `--no-skills`, `--no-extensions`, and `--no-prompt-templates` disable inherited skills, extensions, and installed packages such as subagents or web access. `--no-context-files` skips AGENTS.md and CLAUDE.md. `--no-approve` ignores project-local trust. Authentication is untouched.
- `--no-session` avoids writing a transcript.
- Pi has no working-directory flag, so `cd` to the project root first.
- The stdin redirect is required. Pi performs a blocking stdin read at startup in some spawn environments and hangs with no output when stdin is inherited.

Set the invoking tool or process supervisor's timeout to 300 seconds by default, 600 seconds for `high` or `xhigh`, and 1200 seconds for `max`. Do not rely on an unavailable shell `timeout` command.

## Failures

Pi's exit code is unreliable. It exits 0 on runtime errors such as a missing credential or usage limit, and only exits non-zero on argument-parse errors. Judge success from the output: empty output, or output that begins with an error line, is a failure regardless of exit status.

- On a credential or usage-limit error, run `pi auth check --model <provider/model>` for the model in use and report the result. Do not retry with a different provider.
- On an unknown flag, report the installed version and ask the user to update pi with `pi update self`.
- On a missing-tool complaint in the output, report it; do not broaden the tool list automatically.
