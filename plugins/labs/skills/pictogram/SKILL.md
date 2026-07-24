---
name: pictogram
description: Creates deterministic SVG action pictograms from natural-language requests by authoring, validating, and compiling a constrained XML pose language. Use when the user wants a pictogram, signage-style figure, or SVG icon of a person or small group performing an action, including actions involving ordinary props.
---

# Creating action pictograms

Translate the requested action into the bundled pictogram DSL, validate it, compile it to SVG, and
save both source and output. The author chooses the action and pose; the canon chooses how that pose
becomes a pictogram.

Require a Rust toolchain with Cargo. If it is unavailable, report the missing prerequisite.

## Resolve configuration

Resolve configuration in this order:

1. An output directory explicitly requested for this run
2. `.agents/skill-configs/pictogram/config.local.yaml`
3. `.agents/skill-configs/pictogram/config.yaml`

Read `config.example.yaml` beside this file for all supported fields. If neither an explicit output
directory nor configuration exists, stop and ask whether to use `.agent-workspace/pictograms` or a
custom directory. Create `.agents/skill-configs/pictogram/config.yaml` with the answer before
continuing.

Set the Cargo target directory from `cargo_target_dir`. If omitted, use
`${workspace_dir}/.cargo-target`. Resolve relative paths from the project root.

## Create the bundle

Create one directory per request:

```text
${workspace_dir}/{YYMMDD-HHMMSS}-{slug}/
├── {slug}.pictogram.xml
└── {slug}.svg
```

Use one timestamp for the bundle. Keep build artifacts outside it.

## Author the source

1. Read `references/dsl.md` and the example relevant to the requested pose. Use
   `references/jumping-jacks.pictogram.xml` as the minimal full example.
2. Express each human as the fixed pose graph. Place meaningful joints explicitly; do not ask a
   solver or the compiler to invent the pose.
3. Treat human actions as a default, not a refusal boundary. For equipment or unusual subjects,
   use `assembly` and its restricted primitives to make a legible approximation. Disclose material
   compromises.
4. Use the standard `aicher-inspired-48-v1` profile. It is a contemporary, invented canon inspired
   by systemic reduction; do not describe it as historically authentic Munich geometry.
5. Declare every controlled deviation reported by the validator. Revise the pose before spending
   expression budget when a nearby grid-aligned construction communicates the same action.
6. Include a concise title and description.

## Validate and compile

Set `SKILL_DIR` to this skill's directory, then run:

```bash
CARGO_TARGET_DIR="${cargo_target_dir}" cargo run --quiet \
  --manifest-path "${SKILL_DIR}/Cargo.toml" -- \
  validate "${bundle}/${slug}.pictogram.xml"

CARGO_TARGET_DIR="${cargo_target_dir}" cargo run --quiet \
  --manifest-path "${SKILL_DIR}/Cargo.toml" -- \
  compile "${bundle}/${slug}.pictogram.xml" "${bundle}/${slug}.svg"

CARGO_TARGET_DIR="${cargo_target_dir}" cargo run --quiet \
  --manifest-path "${SKILL_DIR}/Cargo.toml" -- \
  proof "${bundle}/${slug}.pictogram.xml"
```

Fix validation errors and rerun. Warnings require judgment: improve the silhouette when practical,
otherwise keep the output and report the bounded concern.

The proof rasterizes the compiled geometry at 16, 24, 32, and 48 px and checks for accidental
holes, fragmented features, and closed negative-space gaps.

Default output is a black figure intended for a light field. For output embedded on unknown or
dark backgrounds, compile with `--color-mode current`: the `figure` role emits `currentColor` so
the embedding context's `color` property controls the figure, while `accent` keeps its palette
value.

After compilation, inspect the SVG as an image when the environment supports visual inspection.
Check recognizability at small size, decisive negative spaces, and whether near/far limbs remain
distinguishable. Adjust the DSL source—not the SVG—and recompile.

## Guardrails

- Preserve the normalized 48×48 canvas, canonical widths, palette roles, and layer order.
- Keep authored coordinates integral. Prefer the two-unit grid and core octilinear directions.
- Keep raw SVG, scripts, CSS, transforms, filters, gradients, external resources, and embedded text
  out of DSL source.
- Treat contact and intent metadata as assertions. Do not silently move anatomy to satisfy them.
- Judge silhouettes in monochrome first. Accent color must not be the only thing separating
  masses that the proof reports as fused.

Report the source and SVG paths, the profile, any declared deviations, and any perceptual caveat.
