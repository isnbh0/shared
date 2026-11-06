---
name: codex-image-gen
description: Generate new images through an authenticated Codex installation from a shell-capable agent, preserving original files and reporting measured metadata. Use only when explicitly requested.
disable-model-invocation: true
---

# Codex image generation

Use the bundled runner to generate one new image through Codex's native image tool. Requires
`codex`, an authenticated installation with native image generation, and `uv` on macOS or Linux.
This consumes Codex usage. Do not switch to the separately billed image API without agreement.
Editing and reference-image composition are outside this skill's current interface.

## Prepare

Turn the user's brief into a useful prompt while preserving their constraints. Include composition,
aspect ratio, and desired appearance; do not promise exact pixel dimensions or a backend quality
setting. Luna is the orchestrating agent, not the image model. Any later resizing or cropping is a
separate, clearly identified derivative; preserve the original.

Use explicit user choices first. Otherwise read the first existing project config:
`.agents/skill-configs/codex-image-gen/config.local.yaml`, then
`.agents/skill-configs/codex-image-gen/config.yaml`. See [config.example.yaml](config.example.yaml)
for all fields. Resolve relative config paths against the project root; pass absolute paths to
the runner. The runner does not read YAML.

An explicit output path wins. Otherwise use the configured `output_dir` and a descriptive `.png`
filename. If neither is available, ask for an output directory and save it as `output_dir` in the
project config. An explicit output path needs no setup question. Default `workspace` to the project
root, `model` to `gpt-6-luna`, and `timeout` to 300 seconds. The nested Codex process retains the
installation's configured execution permissions; the runner does not bypass approvals or sandboxing.

## Generate

Save the prepared prompt to a UTF-8 file, then run:

```sh
uv run "<skill-root>/scripts/generate.py" \
  --prompt-file /absolute/path/brief.txt \
  --output /absolute/path/assets/teapot.png \
  --workspace /absolute/path/project \
  --model gpt-6-luna --timeout 300 --transparent
```

Omit `--transparent` for an opaque background. `--prompt-file -` reads stdin. Use `--replace` only
when replacement of that output and its metadata is authorized. The runner refuses occupied output
paths before generating. For a requested batch, use one distinct output per image, sequentially
(concurrency one); never generate more than the requested count. Do not invoke this skill recursively
inside the nested session.

Stdout contains one JSON result; progress goes to stderr. Success includes the output and metadata
paths, dimensions, actual format, alpha measurements, SHA-256, source path, and execution thread ID.
Report those measured results rather than the nested agent's claims. A requested transparent image
with no transparent pixels returns a failure with the saved artifact's metadata.

## Recover

`<output>.imagegen/` holds the prompt, execution instruction, JSONL events, stderr, and job state.
`<output>.json` is the metadata sidecar. Keep these until the result is accepted; they may contain
private prompt content. The recorded prompt is the exact prompt supplied to Codex with instructions
to pass it verbatim; the JSONL stream does not independently expose the native tool's arguments.

After interruption or failure, use the same output path:

```sh
uv run "<skill-root>/scripts/generate.py" --output /absolute/path/assets/teapot.png --recover
```

Recovery never launches Codex. It verifies an already published output or searches only the recorded
thread's generated-image directory, then saves the original bytes. Multiple candidate images are an
error, not a reason to select the newest. If the job is still running, wait for it to finish before
recovering. Do not delete job state to retry automatically: an interrupted request may have consumed
usage or still be completing. Inspect the logs, resolve the cause, and obtain an explicit retry
decision before starting another job at a new output path. To intentionally reuse a completed output
path, archive its job directory first and authorize replacement.

The source-directory layout is an observed Codex CLI behavior, not a stable API. If it changes,
report the capability/recovery failure and retain the logs; do not search globally for a recent image.
