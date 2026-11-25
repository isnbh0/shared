---
name: gemini
description: Runs Google Antigravity CLI to critique a spec, code, or changes. Use when the user explicitly requests a Gemini critique or second opinion.
disable-model-invocation: true
compatibility: Requires an authenticated Antigravity CLI (agy); the example invocation uses a POSIX-compatible shell.
---

# Gemini Critique

Run Google's Antigravity CLI (`agy`) for an independent Gemini critique of a spec, code, or recent changes.

## Pre-flight

Check `command -v agy` and `agy --version`. If unavailable, refer the user to [Google's installation instructions](https://antigravity.google/docs/cli/tutorial). Complete interactive setup, authentication, and workspace trust before a headless run. Run `agy models` to see the models available to the account. Availability and quota depend on the account.

## Usage and configuration

Accept an optional file path and focus area; infer the target from conversation context if possible, otherwise ask. The user can request a particular model for a run.

Resolve the model in this order: explicit user choice; `.agents/skill-configs/gemini/config.local.yaml`; `.agents/skill-configs/gemini/config.yaml`; legacy `.claude/skill-configs/gemini/config.local.yaml`, then `config.yaml`; otherwise `gemini-4-neon-high`. If config exists only at a legacy path, use it and offer to move it. The optional `model` field is an `agy` model name or slug; see `config.example.yaml`. Existing configurations for the former Gemini CLI may name an unavailable model: if rejected, report the error and consult `agy models` rather than silently substituting another model.

## Review

1. Identify the target: an explicit path, a named file, the conversation's changes, or its most recent substantive work product, in that order. Resolve the project root.
2. Build a prompt using the adjacent `templates/spec-review.md`, `templates/code-review.md`, or `templates/diff-review.md`. Include the requested focus. Ask for findings with evidence and explicitly instruct the reviewer not to modify files or execute commands.
3. For a diff review, obtain the relevant diff in the calling agent and include it in the prompt, along with affected paths. The invocation below denies shell commands, so `agy` cannot run `git diff` itself. Ensure the prompt fits the operating system's argument-size limit; if it does not, provide a readable temporary file containing the diff and reference its path.
4. Run `agy` in print mode as below. Read the complete response and stderr; summarize substantiated findings and identify any inaccessible files or denied actions. A zero exit status alone does not prove that the review had all requested access: headless permission requests can be denied while the run continues.
5. Treat acting on the feedback as a separate step.

## Invocation

Use plan mode and session permission rules to restrict the review. The deny rules block file writes, shell commands, and URL access through the corresponding CLI permission resources. They also take precedence over existing allow rules. `--sandbox` adds terminal containment where available, but is not a read-only filesystem sandbox: it applies to terminal commands, permits workspace writes, and has no effect on unsupported hosts. Plan mode is a planning instruction, not an OS security boundary. CLI settings, extensions, and other tools may have effects outside these restrictions; do not represent this as a guarantee of complete isolation. See [permissions](https://antigravity.google/docs/cli-permissions) and [terminal sandbox](https://antigravity.google/docs/sandbox/).

Treat the project root, model, and prompt as untrusted input. Prefer an execution API accepting an argv array. If using a shell, canonicalize the project root, validate the model as a single scalar, and quote each dynamic argument. The placeholders below denote individually shell-quoted arguments:

```bash
cd <shell-quoted-project-root> && \
agy --mode plan --sandbox \
  --settings '{"toolPermission":"request-review","permissions":{"deny":["write_file(*)","command(*)","read_url(*)","execute_url(*)"]}}' \
  --output-format text --print-timeout 300s \
  --model <shell-quoted-model> \
  -p <shell-quoted-review-prompt> </dev/null
```

Do not add `--disable-slash-commands`: in tested `agy` 1.5.16 it disables the `/plan` expansion used by `--mode plan`. Never use `--dangerously-skip-permissions` for a critique. `agy` may persist its own conversation and logs. If a required read is denied or the review times out, report the limitation rather than claiming a complete review.

If the CLI rejects a flag, check its version and current `agy --help`. See [headless mode](https://antigravity.google/docs/cli/headless/) for output, timeouts, and permission behavior.
