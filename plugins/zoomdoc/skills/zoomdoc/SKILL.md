---
name: zoomdoc
description: Author accessible semantic-zoom HTML documents whose structure and content can vary freely across ordered detail levels. Use when creating a zoomable document, converting or adapting existing material into one, or synthesizing sources into a self-contained HTML document with semantic markup, progressive enhancement, and optional per-section detail controls.
---

# Semantic zoom document

Create one self-contained HTML document whose readers can move between ordered levels of detail. Preserve semantic HTML as the document model; use `data-zoomdoc-*` only as renderer metadata. Keep the finest level complete and readable when JavaScript is unavailable.

Bundled resources:

- `template.html` — accessible renderer and a three-level example. Copy it, replace every `{{…}}` placeholder, and reshape the semantic content as needed.
- `validate.py` — structural, accessibility, progressive-enhancement, and optional source-coverage checks. Run `uv run ${CLAUDE_SKILL_DIR}/validate.py <doc.html>`.

## Core model

Use an `<article data-zoomdoc>` root with these attributes:

- `data-zoomdoc-levels="brief summary full"` — ordered, space-separated level identifiers from coarsest to finest. Define two or more; names and count are document-specific.
- `data-zoomdoc-initial="summary"` — optional JavaScript-on initial level. Omit it to start at the finest level.
- `data-zoomdoc-profile="article"` — optional editorial profile label such as `article`, `reference`, `procedure`, `transcript`, `catalog`, or `freeform`. Profiles guide authoring; the renderer does not impose their ontology.
- `data-zoomdoc-label-<level>="Readable label"` — optional visible, localizable label for each level; otherwise the renderer title-cases its identifier.
- `data-zoomdoc-control-label` and `data-zoomdoc-detail-label` — optional localizable labels for the global level selector and local disclosure buttons.
- `data-zoomdoc-source-mode="transcription"` — optional strict source-fidelity mode; see Source modes.

Place normal semantic HTML inside the article. Add `data-zoomdoc-at` only where visibility changes by level:

```html
<article data-zoomdoc
         data-zoomdoc-levels="brief summary full"
         data-zoomdoc-initial="summary"
         data-zoomdoc-profile="reference">
  <header>
    <h1>Document title</h1>
    <p>Persistent provenance and date.</p>
    <p data-zoomdoc-at="brief" hidden>Brief orientation.</p>
    <div data-zoomdoc-at="summary" hidden>Summary overview.</div>
  </header>

  <main data-zoomdoc-at="summary full">
    <section data-zoomdoc-unit id="installation">
      <header><h2>Installation</h2></header>
      <div data-zoomdoc-unit-content id="installation-content">
        <ol data-zoomdoc-at="summary" hidden>…condensed steps…</ol>
        <div data-zoomdoc-at="full" id="installation-full">…full content, including nested sections…</div>
      </div>
    </section>
  </main>
</article>
```

Follow these rules:

- Treat `data-zoomdoc-at` as a space-separated token list. Show the element at exactly those document levels.
- Leave persistent content unannotated. Titles, headings, metadata, citations, and navigation usually persist.
- Make the last declared level the no-JavaScript fallback. Elements whose `data-zoomdoc-at` includes the last level must not have `hidden`; other controlled elements must have `hidden` in the authored file.
- Use the same element at several levels when its representation does not change, for example `data-zoomdoc-at="summary full"`.
- Nest semantic sections freely. The renderer reacts only to explicit `data-zoomdoc-*` attributes, never to generic `section`, heading, or content tags.

## Semantic HTML and accessibility

Use native HTML before ARIA:

- Build a valid heading hierarchy with `h1`–`h6`. Use `article`, `section`, `nav`, `aside`, `figure`, `figcaption`, `table`, `dl`, `details`, and other elements for their intended meanings.
- Give every meaningful image appropriate `alt`; use `alt=""` for decorative images.
- Put inactive alternatives behind the native `hidden` attribute. Never override `[hidden]` in author CSS and never leave duplicate representations exposed to assistive technology.
- Let the renderer create native radio inputs for the mutually exclusive document level and native disclosure buttons for local full-detail overrides. Do not recreate these controls in authored content.
- Add ARIA only when native HTML does not express the required relationship. Do not add `role="region"` to every section.
- Keep authored scripts out of the document. JSON-LD metadata is allowed; the shipped renderer is the only executable script.

An optional locally zoomable unit uses `data-zoomdoc-unit`, a stable `id`, and one direct child `data-zoomdoc-unit-content`. Give the unit a real heading and stable IDs to its finest-only controlled blocks. The renderer injects a `Full detail` disclosure button outside the heading and connects it to the blocks it actually reveals with `aria-controls` and `aria-expanded`.

## Content freedom

Allow any safe semantic flow content. Do not reduce valid HTML to what a Markdown exporter can represent. Figures, images, nested sections, definition lists, tables, code, math, media, footnotes, callouts, and domain-specific classes may appear in any level.

Add document-specific presentation in `<style data-zoomdoc-theme>` after the shipped style. Prefer the renderer's CSS custom properties and scope selectors beneath `[data-zoomdoc]`. Do not override `hidden` or change the runtime script unless the user explicitly requests custom renderer behavior.

Choose level meanings to fit the material. Examples:

| Profile | Coarse → fine progression |
|---|---|
| article | thesis → abstract → section summaries → full article |
| reference | purpose → topic map → signatures/key facts → full reference |
| procedure | outcome → workflow → executable steps → rationale/examples |
| transcript | takeaway → synopsis → chapter timeline → full transcript |
| catalog | identity → category overview → item cards → complete records |

These are authoring patterns, not schema requirements.

## Source modes

Choose one mode deliberately:

- **Transcription** — preserve essentially all source content. Set `data-zoomdoc-source-mode="transcription"` and embed the plain canonical source in `<template id="zoomdoc-source"><pre>…HTML-escaped source text…</pre></template>`. The validator checks coverage against the complete finest projection across the document; source paragraphs may cross section boundaries.
- **Adaptation** — reorganize, translate, or substantially reshape source material. Omit strict transcription mode; optionally embed the source for provenance.
- **Synthesis** — compose a new document from a conversation or multiple sources. Omit strict transcription mode and cite sources in the document normally.

At coarser levels, preserve factual support from finer levels while allowing connective and organizing language. Do not require literal phrase containment except in transcription mode.

## Authoring workflow

1. Choose a semantic document structure and an ordered level vocabulary appropriate to the material.
2. Author or import the finest representation as valid semantic HTML. Mechanical conversion and scaffolding are allowed; review the result as a document.
3. Add persistent structure and coarser projections. Use prose, lists, tables, diagrams, signatures, timelines, or other forms suited to each unit.
4. Add `data-zoomdoc-at`, initial `hidden` states, and optional zoom-unit markers. Keep renderer metadata separate from content meaning.
5. If transcribing, embed the canonical plain source and resolve every coverage failure against the source.
6. Run the validator until it prints `OK`.
7. Open the file and test every global level and local detail control with keyboard navigation. Check heading order, visible focus, reflow, reduced motion, print behavior, localized control labels, and the JavaScript-disabled finest fallback.

Preserve the bundled renderer as reusable infrastructure, but adapt the semantic document freely.
