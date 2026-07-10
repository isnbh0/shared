---
name: zoomdoc
description: Author a semantic-zoom HTML document — a single file readable at four zoom levels (thesis / abstract / per-section summaries / full text). Use when the user asks for a semantic zoom doc or zoomable article, to convert existing prose into one, or to summarize or synthesize content (a conversation, multiple sources) into one.
---

# Semantic zoom document

A single HTML file holds every zoom level of one document. Zoom is a view, not an edit: z3 is the ground-truth text; every coarser level is a derived projection of it. The format is unopinionated about content: it can render an existing text, summarize a conversation, or synthesize multiple sources.

Bundled in this skill directory:

- **`template.html`** — the complete renderer (CSS + JS chrome) with `{{placeholder}}` content. Copy it to the target location, replace every `{{…}}` slot, add/remove `<section>` blocks. **Never edit its `<style>` or `<script>`** — author only between `<article>` and `</article>` plus the `<title>` (and the optional embedded source block). Everything in `{{…}}` — braces included — is an instruction to replace or delete. `{{TITLE}}` appears in both `<title>` and `<h1>` — fill it identically.
- **`validate.py`** — deterministic validator: `uv run ${CLAUDE_SKILL_DIR}/validate.py <doc.html>`.

## Levels

Fixed four-level ladder. Each level must be *qualitatively* different, not just shorter.

| Level | Name     | Content contract                                          | Scope    |
|-------|----------|-----------------------------------------------------------|----------|
| z0    | Thesis   | One sentence. The claim the whole document exists to make. | document |
| z1    | Abstract | One paragraph (3–6 sentences). Thesis + key evidence + implication. | document |
| z2    | Summary  | 3–5 bullet points **per section**, key numbers retained.  | section  |
| z3    | Full     | The document's full text (the complete original, when rendering an existing source). | section  |

z0/z1 are document-scoped (shown instead of the body). z2/z3 are section-scoped (each section renders at its own level).

## Markup convention

The authored surface is only content — the zoom bar, per-section buttons, and section heading numbers are injected by the template's script at load. With JS disabled the document reads complete at z3.

```html
<article id="doc">
  <header>
    <h1>…title…</h1>
    <p class="meta">…one-line meta: what this is, sources, date…</p>
    <p class="z0">…thesis sentence…</p>
    <p class="z1">…abstract paragraph…</p>
  </header>

  <section>
    <h2>…section heading, unnumbered…</h2>
    <div class="z2"><ul>…summary bullets…</ul></div>
    <div class="z3">…full text…</div>
  </section>
  …
</article>
```

- The header needs exactly one `h1`, `.z0`, and `.z1`; every section needs exactly one `h2`, `.z2`, and `.z3`.
- Block vocabulary in z2/z3: standard prose blocks — `p`, `ul`/`ol` (nested ok), `table`, `blockquote`, `pre`/`code`. No headings inside a level (`h3`+) — split into sections instead.
- Inline vocabulary: `strong`/`em`, `a` (copied as `[text](href)`), `code`.
- Never set `data-level` on a section in the authored file (and never `data-level=""` — it renders the section blank); it is runtime state for per-section zoom.

**Embedded source**: when the document renders an existing source, embed the source markdown (HTML-escaped) in a `<script type="text/markdown" id="source">…</script>` block before the template's `<script>`. The file becomes self-contained and the validator's coverage gate runs against it. Synthesized content (a report, a conversation summary) has no source — omit the block.

## Authoring order (non-negotiable)

Draft **z3 first**, then z2 from z3, then z1 from the z2 layer, then z0 from z1 — strictly bottom-up. Never draft a coarser level before the finer one exists, and never regenerate a finer level from a coarser one. Delegating individual passes (e.g. per-section z2 summarization for a long document) is permitted; the order is not.

1. **z3** — the full text, one `<section>` each. When rendering an existing source, the complete source text placed verbatim (fixing extraction artifacts like PDF line-wraps is cleanup, not editing) — never a curated excerpt. When synthesizing, z3 is the fullest telling.
2. **z2** — 3–5 bullets per section, derived from that section's z3. Keep the load-bearing specifics (effect sizes, dates, names) — it's a working level, not a teaser.
3. **z1** — one paragraph derived from the z2 layer.
4. **z0** — one sentence derived from z1.

**Anchoring**: nothing in z0–z2 that isn't in z3. Coarse levels select and compress; they never introduce.

**Hand-write the HTML.** All content is written directly by the author, never emitted by a generation script — what each level keeps is a semantic judgment per phrase. Scripts are for validation only.

## Verify before delivering

1. `uv run ${CLAUDE_SKILL_DIR}/validate.py <doc.html>` must print `OK` (structure, placeholders, block vocabulary — and the source-coverage gate when a source block is embedded).
2. If the document renders an existing source: reread the source top to bottom and confirm everything meant to be carried lands in some section's z3, and list anything intentionally dropped. The coverage gate catches wholesale excerpting; only a check grounded in the source catches the rest. (Skip for synthesized content.)
3. Open the rendered document and read it once at z3 as a reader would — excerpted text, mangled hyphenation, and wrap artifacts are obvious there and invisible to every automated check. Check the zoom ladder works and copy-as-markdown output is clean markdown.
