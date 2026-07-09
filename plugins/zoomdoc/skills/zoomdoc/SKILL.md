---
name: zoomdoc
description: Author a semantic-zoom HTML document — a single-file article readable at four zoom levels (thesis / abstract / per-section summaries / full text) with animated word-level morphs between levels. Use when the user asks for a semantic zoom doc, a zoomable article, or to convert existing prose into one.
---

# Semantic zoom document

Bundled in this skill directory:

- **[schema.md](schema.md)** — the authoritative guide. Read it in full before writing anything.
- **`template.html`** — the complete renderer chrome with `{{placeholder}}` content. Copy it to the target location, replace every `{{…}}` slot, add/remove `<section>` blocks. Never edit its `<style>` or `<script>`; author only between `<article>` and `</article>` plus the `<title>`.
- **`validate.py`** — deterministic validator.

## Non-negotiables

- Every derived phrase in a z2 must be wrapped in `<x k="…">` with the same key wrapping its source span in that section's z3.
- Anchoring: nothing in z0–z2 that isn't in z3; z3 is verbatim source text, never regenerated from summaries.

## Verify before delivering

1. `uv run ${CLAUDE_SKILL_DIR}/validate.py <doc.html>` must print `OK` (structure, key bijectivity, no leftover placeholders).
2. Serve the document's directory headless (`uv run python -m http.server <port>` + a headless-playwright script) and check: each section zooms in/out with keyed phrases gliding, the global z0↔z3 ladder works, no console errors or warnings, and copy-as-markdown output contains no `<x` markup.
