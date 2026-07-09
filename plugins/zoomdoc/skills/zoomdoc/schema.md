# Semantic zoom document schema

A single HTML file holds every zoom level of one article. Zoom is a view, not an edit: the finest level (zN) is the ground-truth text; every coarser level is a derived projection of it.

## Files

`template.html` and `validate.py` sit alongside this guide in the skill directory.

- `template.html` — the complete renderer (CSS + JS chrome: zoom bar, per-section zoom, word-morph animation, copy-as-markdown) with `{{placeholder}}` content. To produce a new document, copy it, replace every `{{…}}` slot, and add/remove `<section>` blocks. **Never edit the `<style>` or `<script>`** — all authoring happens between `<article>` and `</article>` (plus the `<title>`). Everything in `{{…}}` — braces included — is an instruction to replace or delete, and sample keys like `s1-example` are placeholders too; no braces or sample keys may survive into the finished document. `{{TITLE}}` appears in both `<title>` and `<h1>` — fill it identically.
- `validate.py` — deterministic validator; run it as SKILL.md's checklist shows (`uv run ${CLAUDE_SKILL_DIR}/validate.py <doc.html>`).

## Generating a document (LLM workflow)

1. Write the z3 sections first — verbatim source text, one `<section>` each.
2. Derive z2 per section (3–5 bullets), reusing z3's surface wording wherever possible. While writing each bullet, wrap each derived phrase in `<x k="…">` **and immediately wrap its source span in that section's z3 with the same key**. Emit the annotation at derivation time; do not try to recover it afterwards.
3. Derive z1 (one paragraph) and z0 (one sentence) from the z2 layer. These are document-scoped and unannotated.
4. Run `uv run ${CLAUDE_SKILL_DIR}/validate.py <doc.html>` — it deterministically checks structure, key bijectivity/nesting/uniqueness, leftover placeholders, and serializer block vocabulary; it must print `OK`. Then self-check the one thing it can't: every claim/number in z0–z2 exists in z3.

## Levels

Fixed four-level ladder for articles. Fewer levels beat a continuous dial — each level must be *qualitatively* different, not just shorter.

| Level | Name     | Content contract                                          | Scope    |
|-------|----------|-----------------------------------------------------------|----------|
| z0    | Thesis   | One sentence. The claim the whole document exists to make. | document |
| z1    | Abstract | One paragraph (3–6 sentences). Thesis + key evidence + implication. | document |
| z2    | Summary  | 3–5 bullet points **per section**, key numbers retained.  | section  |
| z3    | Full     | The complete original text.                                | section  |

z0/z1 are document-scoped (shown instead of the body). z2/z3 are section-scoped (each section renders at its own level).

## Markup convention

```html
<article id="doc" data-doc-level="2">
  <header>
    <h1>…title…</h1>
    <p class="meta">…provenance line…</p>
    <p class="z0">…thesis sentence…</p>
    <p class="z1">…abstract paragraph…</p>
  </header>

  <!-- omit data-level entirely to inherit the doc level; the CSS gates on
       :not([data-level]), so data-level="" would render the section blank -->
  <section>
    <div class="sec-head"><h2>…numbered section heading…</h2><div class="sec-controls"><button class="sec-zoom"></button><button class="copy-md sec-copy" aria-label="Copy this section as Markdown"></button></div></div>
    <div class="z2"><ul>…summary bullets…</ul></div>
    <div class="z3">…full original text…</div>
  </section>
  …
</article>
```

Structural requirements the script depends on (violating any throws or silently hides content):

- The header needs exactly one `h1`, `.z0`, and `.z1`; every section needs exactly one `h2`, `.z2`, `.z3`, and the full `sec-head`/`sec-controls` block shown above — new sections must be complete copies of that skeleton, not bare `h2` + divs.
- Number section headings manually (`1. …`, `2. …`); the copy-as-markdown output bakes them in.
- Keep the shipped default `data-doc-level="2"` — the zoom bar's `aria-pressed` state is hardcoded to match it.
- z2/z3 block vocabulary: `p`, `ul` (nested ok), and `table` only — the markdown serializer handles nothing else (`ol`, `blockquote`, `pre` would silently corrupt copied output).

Rendering rules (all doable in CSS off the two attributes):

1. Doc at z0/z1 → show header thesis/abstract, hide all sections.
2. Doc at z2/z3 → show sections; each section shows its `.z2` **or** `.z3`, per its effective level.
3. Effective section level = `data-level` if set, else `data-doc-level`. Per-section zoom overrides global; changing the global level clears per-section overrides.

## Provenance annotations (generator contract)

Morph matching is by explicit provenance keys, not string similarity. The generator that writes a coarser level wraps each derived phrase in `<x k="key">` and wraps its source span in the finer level with the same key:

```html
<!-- z3 -->  ... comes from <x k="s1-scale">Stanford SCALE</x> [S4]: of <x k="s1-corpus">818 papers</x> ...
<!-- z2 -->  <x k="s1-corpus">Of 818 papers</x> ... survive <x k="s1-scale">Stanford SCALE's</x> screen ...
```

- Keys are document-unique short slugs (`s3-guardrails`). Within a section, a key must appear **exactly once in z2 and exactly once in z3** — morphs run both directions, so the pairing must be bijective per section; a one-sided key degrades to a fade plus a console warning. Never nest one `<x>` inside another (words would be claimed by both keys); nesting `<x>` inside `<strong>`/`<em>` (or vice versa) is fine. This is the anchoring rule made machine-checkable.
- Keys only drive the **per-section z2↔z3 morph**. The document-level z0↔z1 and z1↔z2 transitions carry no keys (z1/z0 are unannotated — don't annotate them), so with `GLOBAL_LCS` off they render as fades; see the switch below.
- **Phrase-provenance** (coarse phrase reuses fine phrasing): words inside the keyed pair glide 1:1.
- **Meaning-provenance** (paraphrase): same mechanism — the renderer aligns whatever words match within the keyed pair (LCS, then order-free); leftovers fade in. If *nothing* matches (pure paraphrase), every target word flies from the source span's location, so the paraphrase visibly materializes out of its source. Because matching is key-scoped, homophones and repeated words can never cross-match.
- Unannotated text does not glide — it crossfades.

### The `GLOBAL_LCS` switch

`const GLOBAL_LCS = false;` in the template's script is the renderer's fuzzy-fallback matcher for **unannotated** text. When on, any adjacent-level transition also matches unkeyed words by whole-block LCS, then an order-free second pass over substantial leftovers (4+ chars or numeric); matched words glide, the rest fade. Keyed pairs are excluded from this fuzzy pass (their tokens are blanked first), so keys always win and homophones can't cross-match.

What it affects:

- **z0↔z1 and z1↔z2 (doc-level)**: these transitions run through the same word-morph engine but carry no keys, so `GLOBAL_LCS` is their *only* possible source of motion. Off (shipped default): they are pure crossfades. On: words shared between the thesis/abstract/summaries glide — e.g. z1→z2 flies the abstract's words out into the section summaries that reuse them.
- **z2↔z3 (per-section)**: keyed phrases glide either way; the flag only adds fuzzy gliding for the text *outside* keyed pairs.

It ships off deliberately: with keys as the only source of motion, a missing annotation shows up immediately as a dead (non-gliding) phrase instead of being papered over by fuzzy matching. Flipping it on is a rendering choice, not an authoring one — it never substitutes for the key bijectivity contract. (Remember the flag lives inside `<script>`, which authors must never edit; treat it as a renderer constant unless the user explicitly asks for the fuzzy behavior.)

## Authoring rules

- **Hand-write everything.** All content — sections, summaries, `<x>` wrappers — is written directly by the author (human or LLM), never emitted by a generation script. Choosing what each key spans is a semantic decision per phrase; programmatic wrapping produces wrong keys that pass validation. Scripts are for validation only.
- **Anchoring**: every claim and number in z0–z2 must exist in z3. Coarse levels select and compress; they never introduce.
- z2 keeps the load-bearing specifics (effect sizes, dates, names) — it's a working level, not a teaser.
- **Morph-friendliness**: reuse z3's surface phrasing in z2 wherever possible (extractive over paraphrased). Within a keyed pair, words match after normalization (case, punctuation, possessives — "SCALE's" glides to "SCALE"), so exact copying isn't required, but heavy paraphrase leaves little to glide.
- z3 is stored verbatim; never regenerate it from a summary.
- Levels are authored per document (by hand or by LLM), then frozen into the file. No runtime generation.
