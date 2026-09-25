---
name: tractatus
description: Write or adapt content as a nested outline of points with optional number labels, then render it as a self-contained, read-only HTML page with collapse, expand, deep links, and keyboard navigation. Use for tractatus format, a navigable outline page, or an existing nested-list markdown outline.
---

# Tractatus

The name comes from Wittgenstein's book. The format works for any subject whose points can form a
parent-child tree: findings, decisions, instructions, explanations, and other structured content.

Produce one HTML file: `embed.py` (next to this file) writes the outline markdown into a copy of
`template.html`. The page works offline from `file://`.

## Procedure

1. Write the outline (format below). If the user supplied markdown, start from it; preserve its
   content unless the requested result or format requires changes.
2. Choose the output path. Use a path the user provided. Otherwise read
   `.agents/skill-configs/tractatus/config.local.yaml`, then `config.yaml`, relative to the
   working project. Use `output_dir` from the first existing file. If neither file exists, ask
   the user for an output directory, save it as `output_dir` in
   `.agents/skill-configs/tractatus/config.yaml`, and use it. Choose a descriptive
   `<kebab-slug>.html` filename inside that directory and create the directory if needed.
3. Build the page with the chosen explicit path:
   ```sh
   uv run "<this skill's directory>/embed.py" - -o "<output_dir>/my-outline.html" <<'EOF'
   # Title
   - 1 The service has two access paths.
   EOF
   ```
   Or pass a markdown file instead of `-`. If uv is unavailable, use `python3` with Python 3.13
   or newer in the same command.
4. Report the path that `embed.py` prints.

Never edit the page's content block by hand. To revise a page, recover its outline with
`uv run "<this skill's directory>/embed.py" --extract page.html > outline.md`, edit the markdown,
and build again.

## Format

```markdown
# Title

Optional intro paragraph.

- 1 The service has two access paths.
  - 1.1 The web page works on phones.
    - 1.11 Its layout adapts to narrow screens.
  - 1.2 The kiosk works without an account.
- 2 Support is available by phone.
```

- Any markdown list marker works; nesting follows indentation.
- Number labels are optional. A unique leading number such as `1.1` or `2.0121` is shown as the
  item's label and becomes its link target (`page.html#1.1`). Duplicate labels receive positional
  link targets and produce a warning. Write `\2024` to start text with a number that is not a label.
- A line with no marker continues the item above it. To start a second paragraph, leave a
  blank line and indent the text under the item.
- Inline: `*em*`, `**strong**`, `` `code` ``, `[text](https://…)`, `[see 2.1](#2.1)` (clicking
  it zooms into 2.1), and math `$p \supset q$`.
  - Backslash-escape markdown characters to keep them literal, especially `\$`.
  - There is no display math, and no tables, code blocks or images inside items.

## Writing the outline

- Give each item one clear point. Use children for details, examples, qualifications, steps, or
  related points.
- Keep the top level short enough to show the document's structure at a glance.
- Choose labels to suit the content, or omit them. The viewer uses indentation for hierarchy and
  displays labels as written; it does not require their numbers to match the hierarchy.
  Wittgenstein's `1.1`, `1.11` scheme is one option: remarks `2.01`, `2.02` can sit under a
  label-only `2.0` item.
- Put each item's main point first. Collapsed views show whole items, so shorter items are easier
  to scan.
- Cross-reference with fragment links (`[1.2](#1.2)`) rather than "see above".

## Reading the page

The page's Help dialog (`?`) lists the keys and gestures.
Useful links to share: `page.html#2.1` opens at item 2.1, and `page.html#z=2.1` opens zoomed into it.

`examples/tractatus.md` is a complete historical example using Wittgenstein's text. Build HTML
from it with `embed.py` and an explicit output path.

The template loads MathJax 3.2.2 from jsDelivr for math and its fonts when online. Offline
pages keep TeX source visible.
