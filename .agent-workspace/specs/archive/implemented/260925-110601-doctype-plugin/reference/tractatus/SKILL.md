---
name: my-tractatus
description: Write content as a numbered nested outline ("tractatus format") and render it as one self-contained, read-only outline viewer HTML page with collapse, expand, deep links, and keyboard navigation. Use when the user asks for tractatus format, a navigable outline page, or to render an existing nested-list markdown outline.
---

# my-tractatus

Produce one HTML file: `embed.py` (next to this file) writes the outline markdown into a copy of
`template.html`. The page works offline from `file://`.

## Procedure

1. Write the outline (format below). If the user supplied markdown, use it as is.
2. Build the page. The output path is the user's path, or `inbox/<kebab-slug>.html` under the
   current working directory.
   ```sh
   uv run "<this skill's directory>/embed.py" - -o inbox/my-outline.html <<'EOF'
   # Title
   - 1 First proposition.
   EOF
   ```
   Or pass a markdown file instead of `-`.
3. Report the path that `embed.py` prints.

Never edit the page's content block by hand. To revise a page, recover its outline with
`uv run "<this skill's directory>/embed.py" --extract page.html > outline.md`, edit the markdown,
and build again.

## Format

```markdown
# Title

Optional intro paragraph.

- 1 First proposition.
  - 1.1 A comment on 1.
    - 1.11 A comment on 1.1.
  - 1.2 Another comment on 1.
- 2 Second proposition.
```

- Any markdown list marker works; nesting follows indentation.
- A leading number such as `1.1` or `2.0121` is shown as the item's label and becomes its
  link target (`page.html#1.1`). Write `\2024` to start text with a number that is not a label.
- A line with no marker continues the item above it. To start a second paragraph, leave a
  blank line and indent the text under the item.
- Inline: `*em*`, `**strong**`, `` `code` ``, `[text](https://…)`, `[see 2.1](#2.1)` (clicking
  it zooms into 2.1), and math `$p \supset q$`.
  - Backslash-escape markdown characters to keep them literal, especially `\$`.
  - There is no display math, and no tables, code blocks or images inside items.

## Authoring in tractatus format

- One claim per item. Its children explain, support or qualify that claim, and nothing else.
- Keep the top level short (3–9 items). Someone who reads only the top level should get the
  whole argument.
- Labelling is your call: `1`, `1.1`, `1.1.1`, Wittgenstein's `1.1`, `1.11`, or none. The viewer
  shows labels as written and never checks them. Adapt Wittgenstein's scheme as it suits you;
  for example, remarks `2.01`, `2.02` can sit under a label-only `2.0` item.
- Put the most important statement in each item's first sentence. Collapsed views show
  whole items, so shorter items are easier to scan.
- Cross-reference with fragment links (`[1.2](#1.2)`) rather than "see above".

## Reading the page

The page's Help dialog (`?`) lists the keys and gestures; no need to explain them to the reader.
Useful links to share: `page.html#2.1` opens at item 2.1, and `page.html#z=2.1` opens zoomed into it.

`examples/tractatus.md` is a complete example (built as `examples/tractatus.html`).

## Changing the template

Tests for `template.html` live in `tests/`.
