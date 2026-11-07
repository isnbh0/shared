---
name: codex-image-gen
description: Generate new images or edit local reference images through an authenticated Codex installation from a shell-capable agent, preserving original files and reporting measured metadata. Use only when explicitly requested.
disable-model-invocation: true
---

# Codex image generation

Use the bundled runner to produce one new image per invocation through Codex's native image tool,
either from a prompt alone or as an edit of up to five local reference images. Requires
`codex`, an authenticated installation with native image generation, and `uv` on macOS or Linux.
This consumes Codex usage. Do not switch to the separately billed image API without agreement.

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

## References

Pass local images with repeated `--reference` options when the result should be derived from them:
modifying, restyling, or combining their content. Codex sends these as an edit request. For a
brand-new image, omit references and describe any inspiration in the prompt.

Infer each reference's role from the request, such as the image to modify or a source of style or
elements, and ask only when roles are unclear. Order the references so the prompt can name them
("the first image", "the second image"), and state what to preserve. References must be readable
PNG, JPEG, or WebP files. Write the result to a new path: a reference cannot be the output or its
metadata, even with `--replace`. When an edit target has transparent pixels, pass `--transparent`
unless the user wants an opaque result; the native tool does not infer it.

## Generate

Supply the prepared prompt as a UTF-8 file or stdin. For example:

```sh
uv run "<skill-root>/scripts/generate.py" \
  --prompt-file /absolute/path/brief.txt \
  --output /absolute/path/assets/teapot.png \
  --reference /absolute/path/assets/source.png \
  --workspace /absolute/path/project \
  --model gpt-6-luna --timeout 300 --transparent
```

Omit `--transparent` for an opaque background. `--prompt-file -` reads stdin. Use `--replace` only
when replacement of that output and its metadata is authorized. The runner refuses occupied output
paths before generating. For a requested batch, launch independent runners in parallel, defaulting
to up to three concurrent jobs unless the user specifies another limit. Give each image a distinct
output path, track each job's result, and await all jobs. Generate only the requested count.
Do not invoke this skill recursively inside the nested session.

Stdout contains one JSON result; progress goes to stderr. Success includes the output and metadata
paths, dimensions, actual format, alpha measurements, SHA-256, source path, and execution thread ID.
Report the saved image and relevant measured properties; keep full provenance in the sidecar.
A requested transparent image with no transparent pixels returns a failure with the saved artifact's metadata.
Results also list the ordered references. `references_verified` is `true` when Codex's event stream
reports the same ordered input hashes, `null` when the stream omits them, and `false` otherwise.
A `false` value returns `constraint_failed`; do not present that image as an edit of the supplied
references.

## Recover

`<output>.imagegen/` holds the prompt, execution instruction, reference snapshots, JSONL events,
stderr, and job state. `<output>.json` is the metadata sidecar. Keep these until the result is
accepted; they may contain private prompt and image content. The runner snapshots references before
starting Codex, so later changes to the originals do not affect the job, and recovery never treats
snapshots as generated images. The recorded prompt is the exact prompt supplied to Codex with
instructions to pass it verbatim; apart from any reported input hashes, the JSONL stream does not
independently expose the native tool's arguments.

After interruption or failure, use the same output path:

```sh
uv run "<skill-root>/scripts/generate.py" --output /absolute/path/assets/teapot.png --recover
```

Recovery never launches Codex. It verifies an already published output or searches only the recorded
thread's generated-image directory, then saves the original bytes. Multiple candidate images are an
error, not a reason to select the newest. If the job is still running, wait for it to finish before
recovering. Do not delete job state to retry automatically: an interrupted request may have consumed
usage or still be completing. Inspect the logs and resolve the cause. If generation never started,
correct the problem and continue within existing authorization. For another generation, ask only
when duplication risk or authorization for additional usage remains unresolved. Start a retry at
a new output path. To intentionally reuse a completed output path, archive its job directory first
and use `--replace` when replacement is authorized.

The source-directory layout is an observed Codex CLI behavior, not a stable API. If it changes,
report the capability/recovery failure and retain the logs; do not search globally for a recent image.
