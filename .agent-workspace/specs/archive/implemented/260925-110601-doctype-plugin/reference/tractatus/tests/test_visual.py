"""Dynalist visual style: geometry, colours and contrast (law V)."""

import re

import pytest
from conftest import check_laws, template_text

VISUAL_MD = """\
# Visual

Intro note with `code`, $x$ and a [link](https://example.org/).

- 1 Alpha
  - 1.1 Beta has **bold**, *em*, `code`, $a^2$ and a [link](https://example.org/).

    Second paragraph of beta.
  - 1.2 Gamma
    - 1.2.1 Delta
- 2 Epsilon
- 3 Zeta
"""

# Unlabelled, so every row is toggle + text.
BULLET_MD = """\
- Parent one
  - Child leaf
  - Child parent
    - Grandchild
- Leaf two
- Parent three
  - Hidden child
"""

SCHEMES = ["light", "dark"]
BULLET = {"light": "rgb(122, 122, 122)", "dark": "rgb(167, 167, 167)"}
GUIDE = {"light": "rgb(238, 238, 238)", "dark": "rgb(68, 68, 68)"}
ACTIVE = {"light": "rgb(204, 232, 255)", "dark": "rgb(0, 55, 102)"}
PAGE = {"light": "rgb(255, 255, 255)", "dark": "rgb(24, 24, 24)"}
WIDE = {"width": 1280, "height": 720}
NARROW = {"width": 375, "height": 700}   # below 40rem (640px): inline labels
TRANSPARENT = "rgba(0, 0, 0, 0)"

# Default metrics, derived from the template's knobs (text 20px, line height 1.5, item gap 10px,
# indent 30px). test_spacing_panel.py checks that they follow the knobs.
FONT = 20
LINE = FONT * 1.5                  # 30px line box
NOTE_FONT = FONT - 3               # 17px
NOTE_LINE = NOTE_FONT * 1.5        # 25.5px
GAP = 10                           # between consecutive rows
PAD_TOP = GAP                      # row padding above the text: Dynalist's highlight reaches a
PAD_BOTTOM = GAP / 2               # whole gap above the text and half a gap below
PITCH = LINE + GAP                 # 40px between one-line siblings
NOTE_GAP = 0                       # Dynalist: a note starts where its paragraph's line ends
GROUP_GAP = 4                      # Dynalist: extra space after a nested group closes
BULLET_COL = 22
TEXT_GAP = 4                       # Dynalist: the text starts 15px right of the bullet's centre
TEXT_X = BULLET_COL + TEXT_GAP     # 26px: text start inside a row
INDENT = 30                        # a child row starts one indent right of its parent row
GUIDE_X = BULLET_COL / 2 - 1       # 10px: the guide's left edge, under the bullet centre
TITLE_INSET = 6                    # the root row starts this far before the item rows
COLUMN_PAD = 88                    # Dynalist: the title and rows start 88px into the column
LINK_FOCUS = "rgb(0, 138, 255)"

RECT_JS = """sel => {
  const r = document.querySelector(sel).getBoundingClientRect();
  return { left: r.left, right: r.right, top: r.top, bottom: r.bottom, width: r.width, height: r.height };
}"""
STYLE_JS = "([sel, prop]) => getComputedStyle(document.querySelector(sel))[prop]"

# WCAG 2 relative luminance and contrast, with the effective background composited from the
# element and its ancestors. Kept here, not in the template.
CONTRAST_LIB = r"""
  const parse = (c) => {
    const m = c.match(/rgba?\(([^)]+)\)/);
    if (!m) throw new Error(`unparsed colour ${c}`);
    const p = m[1].split(/[\s,/]+/).filter(Boolean).map(Number);
    return { r: p[0], g: p[1], b: p[2], a: p.length > 3 ? p[3] : 1 };
  };
  const over = (top, bottom) => {         // top composited over an opaque bottom
    const a = top.a;
    return { r: top.r * a + bottom.r * (1 - a), g: top.g * a + bottom.g * (1 - a),
             b: top.b * a + bottom.b * (1 - a), a: 1 };
  };
  const lin = (v) => {
    const s = v / 255;
    return s <= 0.04045 ? s / 12.92 : ((s + 0.055) / 1.055) ** 2.4;
  };
  const lum = (c) => 0.2126 * lin(c.r) + 0.7152 * lin(c.g) + 0.0722 * lin(c.b);
  const ratio = (a, b) => {
    const [hi, lo] = [lum(a), lum(b)].sort((x, y) => y - x);
    return (hi + 0.05) / (lo + 0.05);
  };
  // Geometry-aware: an ancestor paints behind the element only if its border box contains the
  // element's centre. A gutter label lies outside its row, so it is painted over the page.
  const background = (el) => {
    const r = el.getBoundingClientRect();
    const cx = r.left + r.width / 2;
    const cy = r.top + r.height / 2;
    const covers = (e) => {
      const b = e.getBoundingClientRect();
      return cx >= b.left && cx <= b.right && cy >= b.top && cy <= b.bottom;
    };
    const layers = [];
    for (let e = el; e; e = e.parentElement) {
      if (!covers(e)) continue;
      const c = parse(getComputedStyle(e).backgroundColor);
      if (c.a > 0) layers.push(c);
      if (c.a >= 1) break;
    }
    let base = layers.at(-1);
    if (!base || base.a < 1) {
      base = parse(getComputedStyle(document.documentElement).backgroundColor);
      if (base.a < 1) base = { r: 255, g: 255, b: 255, a: 1 };
    } else {
      layers.pop();
    }
    return layers.reverse().reduce((acc, c) => over(c, acc), base);
  };
"""

CONTRAST_JS = (
    "(selectors) => {"
    + CONTRAST_LIB
    + r"""
  const out = [];
  for (const sel of selectors) {
    for (const el of document.querySelectorAll(sel)) {
      if (!el.checkVisibility() || el.textContent.trim() === "") continue;
      let fg = parse(getComputedStyle(el).color);
      const bg = background(el);
      if (fg.a < 1) fg = over(fg, bg);
      const active = el.closest('[role="treeitem"]')?.tabIndex === 0;
      out.push({ sel, html: el.outerHTML.slice(0, 120), ratio: ratio(fg, bg), active,
                 bg: `rgb(${[bg.r, bg.g, bg.b].map(Math.round).join(", ")})` });
    }
  }
  return out;
}"""
)

# Law V for graphics: every painted part of every visible bullet (fill, border or ring shadow of
# ::before and ::after) against the row's effective background.
BULLET_CONTRAST_JS = (
    "() => {"
    + CONTRAST_LIB
    + r"""
  const out = [];
  for (const el of document.querySelectorAll("#outline .toggle")) {
    if (!el.checkVisibility()) continue;
    const li = el.closest('[role="treeitem"]');
    const bg = background(el);
    for (const pseudo of ["::before", "::after"]) {
      const s = getComputedStyle(el, pseudo);
      if (s.display === "none") continue;
      const inks = [];
      const fill = parse(s.backgroundColor);
      if (fill.a > 0) inks.push(["background", fill]);
      if (parseFloat(s.borderTopWidth) > 0) inks.push(["border", parse(s.borderTopColor)]);
      if (s.boxShadow !== "none") inks.push(["box-shadow", parse(s.boxShadow)]);
      for (const [kind, c] of inks) {
        const fg = c.a < 1 ? over(c, bg) : c;
        out.push({ id: li.dataset.id, active: li.tabIndex === 0,
                   expanded: li.getAttribute("aria-expanded"), pseudo, kind, ratio: ratio(fg, bg) });
      }
    }
  }
  return out;
}"""
)

PAGE_TEXT = [
    "#doc-title", ".intro p", ".intro code", ".row .para", ".row code", ".row .math",
    ".row a", ".label", ".help-button", ".status", ".empty", "#toast", ".find-count",
]
HELP_TEXT = ["#help h2", "#help dt kbd", "#help dd", "#help button"]


PSEUDO_JS = """([sel, pseudo]) => {
  const s = getComputedStyle(document.querySelector(sel), pseudo);
  return { content: s.content, display: s.display, width: s.width, height: s.height,
           background: s.backgroundColor, borderRadius: s.borderTopLeftRadius,
           borderWidth: s.borderTopWidth, boxShadow: s.boxShadow, translate: s.translate };
}"""


def rect(page, sel):
    return page.evaluate(RECT_JS, sel)


def style(page, sel, prop):
    return page.evaluate(STYLE_JS, [sel, prop])


def open_visual(open_outline, page, scheme="light"):
    page.emulate_media(color_scheme=scheme)
    return open_outline(VISUAL_MD)


def expand_1(page):
    page.focus("#item-1")
    page.keyboard.press("ArrowRight")
    assert page.get_attribute("#item-1", "aria-expanded") == "true"


def settle_math(page):
    page.wait_for_function(
        "() => !['loading', undefined].includes(document.documentElement.dataset.mathState)"
    )


def test_column_and_title(open_outline, page):
    open_visual(open_outline, page)
    viewport = page.viewport_size["width"]
    for sel in ("main", ".page-head"):
        r = rect(page, sel)
        assert r["width"] == min(820, viewport), sel
        assert abs(r["left"] - (viewport - r["right"])) <= 1, sel
    assert style(page, "#doc-title", "fontSize") == "28px"
    assert style(page, "#doc-title", "lineHeight") == "34px"
    assert style(page, "#doc-title", "fontWeight") == "400"
    outline = rect(page, "#outline")
    # The title's text starts where the rows do, as Dynalist's does; the root row's highlight
    # starts TITLE_INSET before it, so its ring clears the text.
    assert abs(rect(page, "#row-root")["left"] - (outline["left"] - TITLE_INSET)) <= 0.5
    assert abs(rect(page, "#row-root")["right"] - outline["right"]) <= 0.5
    assert abs(rect(page, "#doc-title")["left"] - outline["left"]) <= 0.5
    assert abs(rect(page, "#item-1 > .row")["left"] - outline["left"]) <= 0.5
    assert abs(outline["left"] - (rect(page, "main")["left"] + COLUMN_PAD)) <= 0.5


def test_row_metrics(open_outline, page):
    open_visual(open_outline, page)
    rows = page.evaluate(
        "[...document.querySelectorAll('.row:not(.root-row)')].map(r => [r.id,"
        " getComputedStyle(r).lineHeight, getComputedStyle(r.querySelector('.para')).fontSize])"
    )
    assert rows and all(lh == f"{LINE:g}px" and fs == f"{FONT}px" for _, lh, fs in rows), rows
    top = lambda id: rect(page, f"#item-{id} > .row")["top"]  # noqa: E731
    assert abs(top("2") - top("1") - PITCH) <= 0.5
    assert abs(top("3") - top("2") - PITCH) <= 0.5
    # As Dynalist's, the highlight reaches a whole gap above the text and half a gap below; the
    # row above's highlight overlaps the other half.
    row2, text2 = rect(page, "#item-2 > .row"), rect(page, "#item-2 > .row > .text")
    assert abs(text2["top"] - row2["top"] - PAD_TOP) <= 0.5
    assert abs(row2["bottom"] - text2["bottom"] - PAD_BOTTOM) <= 0.5
    assert abs(rect(page, "#item-2 > .row")["height"] - (PAD_TOP + LINE + PAD_BOTTOM)) <= 0.5
    expand_1(page)
    # Parent to first child: the same pitch as between siblings. Last child to next item: the
    # pitch plus the group gap.
    assert abs(top("1_1") - top("1") - PITCH) <= 0.5
    # 1.1 has a note, so measure from 1.2: collapsed and one line tall.
    assert abs(rect(page, "#item-1_2 > .row")["height"] - (PAD_TOP + LINE + PAD_BOTTOM)) <= 0.5
    assert abs(top("2") - top("1_2") - PITCH - GROUP_GAP) <= 0.5
    # Inline code and math do not grow a line box: one-line paragraphs stay --line tall,
    # and 1.1's row is padding + line + note gap + note line + padding.
    heights = page.evaluate(
        "[...document.querySelectorAll('.row .para, .intro p')].filter(e => e.checkVisibility())"
        ".map(e => [e.textContent.slice(0, 20), e.getBoundingClientRect().height])"
    )
    want = [NOTE_LINE, LINE, LINE, NOTE_LINE, LINE, LINE, LINE]
    assert [h for _, h in heights] == want, heights
    want_1_1 = PAD_TOP + LINE + NOTE_GAP + NOTE_LINE + PAD_BOTTOM
    assert abs(rect(page, "#item-1_1 > .row")["height"] - want_1_1) <= 0.5
    check_laws(page)


@pytest.mark.parametrize("scheme", SCHEMES)
def test_indent_and_guides(open_outline, page, scheme):
    open_visual(open_outline, page, scheme)
    expand_1(page)
    page.keyboard.press("ArrowRight")   # 1.1
    page.keyboard.press("ArrowDown")    # 1.2
    page.keyboard.press("ArrowRight")   # expand 1.2
    assert page.get_attribute("#item-1_2", "aria-expanded") == "true"
    left = lambda id: rect(page, f"#item-{id} > .row")["left"]  # noqa: E731
    assert abs(left("1_1") - left("1") - INDENT) <= 0.5
    assert abs(left("1_2_1") - left("1_2") - INDENT) <= 0.5
    # The child's row starts INDENT - TEXT_X right of its parent's text, as Dynalist's does.
    assert abs(left("1_1") - rect(page, "#item-1 > .row > .text")["left"] - (INDENT - TEXT_X)) <= 0.5
    groups = page.evaluate(
        "[...document.querySelectorAll('[role=group]')].map(g => { const s = getComputedStyle(g);"
        " return [s.borderLeftWidth, s.borderLeftStyle, s.borderLeftColor]; })"
    )
    # The root's group is the top level: no guide, no indent.
    assert groups[0][0] == "0px"
    assert style(page, "#item-root > [role=group]", "paddingLeft") == "0px"
    assert groups[1:] == [["1px", "solid", GUIDE[scheme]]] * 2
    for parent in ("1", "1_2"):
        guide = rect(page, f"#item-{parent} > [role=group]")["left"]
        assert abs(guide - left(parent) - GUIDE_X) <= 0.5
    check_laws(page)


@pytest.mark.parametrize("scheme", SCHEMES)
def test_group_gap(open_outline, page, scheme):
    open_visual(open_outline, page, scheme)
    expand_1(page)
    page.keyboard.press("ArrowRight")   # 1.1
    page.keyboard.press("ArrowDown")    # 1.2
    page.keyboard.press("ArrowRight")   # expand 1.2
    assert page.get_attribute("#item-1_2", "aria-expanded") == "true"
    top = lambda id: rect(page, f"#item-{id} > .row > .text")["top"]  # noqa: E731
    group = lambda id: rect(page, f"#item-{id} > [role=group]")  # noqa: E731
    # Siblings and parent to first child keep the pitch; each closing group adds GROUP_GAP.
    assert abs(top("1_2_1") - top("1_2") - PITCH) <= 0.5
    assert abs(top("2") - top("1_2_1") - PITCH - 2 * GROUP_GAP) <= 0.5
    assert abs(top("3") - top("2") - PITCH) <= 0.5
    # A guide starts at its parent's text and ends at its last descendant's row; the outer
    # guide runs GROUP_GAP past the inner one, as Dynalist's does.
    for parent in ("1", "1_2"):
        assert abs(group(parent)["top"] - rect(page, f"#item-{parent} > .row > .text")["bottom"]) <= 0.5
    assert abs(group("1_2")["bottom"] - rect(page, "#item-1_2_1 > .row")["bottom"]) <= 0.5
    assert abs(group("1")["bottom"] - group("1_2")["bottom"] - GROUP_GAP) <= 0.5
    # The gap belongs to the item: the item's box reaches the next item's row.
    assert abs(rect(page, "#item-1")["bottom"] - rect(page, "#item-2 > .row")["top"]
               - PAD_TOP / 2) <= 0.5
    check_laws(page)


@pytest.mark.parametrize("scheme", SCHEMES)
def test_active_row(open_outline, page, scheme):
    open_visual(open_outline, page, scheme)
    page.click("#item-2 > .row > .text")   # mouse focus: the ring shows in selected mode too
    assert page.evaluate("document.activeElement.id") == "item-2"
    assert style(page, "#item-2 > .row", "backgroundColor") == ACTIVE[scheme]
    assert style(page, "#item-2 > .row", "borderRadius") == "0px"
    assert style(page, "#item-2 > .row", "outlineStyle") == "solid"
    assert style(page, "#item-2 > .row", "outlineWidth") == "2px"
    assert style(page, "#item-2 > .row", "outlineColor") == LINK_FOCUS
    assert style(page, "#item-2", "outlineStyle") == "none"
    page.keyboard.press("ArrowDown")       # keyboard focus: the ring follows the active item
    assert page.evaluate("document.activeElement.id") == "item-3"
    assert style(page, "#item-3 > .row", "backgroundColor") == ACTIVE[scheme]
    assert style(page, "#item-3 > .row", "outlineStyle") == "solid"
    assert style(page, "#item-3 > .row", "outlineWidth") == "2px"
    assert style(page, "#item-3 > .row", "outlineColor") == LINK_FOCUS
    assert style(page, "#item-3", "outlineStyle") == "none"
    assert style(page, "#item-2 > .row", "backgroundColor") == TRANSPARENT
    page.hover("#item-1 > .row > .text")
    assert style(page, "#item-1 > .row", "backgroundColor") == TRANSPARENT
    check_laws(page)


def test_notes_code_links(open_outline, page):
    open_visual(open_outline, page)
    expand_1(page)
    first = rect(page, "#item-1_1 .para:nth-child(1)")
    note = "#item-1_1 .para:nth-child(2)"
    assert style(page, note, "fontSize") == f"{NOTE_FONT}px"
    assert style(page, note, "lineHeight") == f"{NOTE_LINE:g}px"
    assert style(page, note, "color") == "rgb(78, 78, 78)"
    assert abs(rect(page, note)["top"] - first["bottom"] - NOTE_GAP) <= 0.5

    code = ".text code"
    assert style(page, code, "fontSize") == f"{FONT - 2}px"
    assert style(page, code, "color") == "rgb(199, 37, 78)"
    assert style(page, code, "backgroundColor") == "rgb(245, 245, 245)"
    assert style(page, code, "borderRadius") == "4px"
    assert style(page, code, "paddingLeft") == "5px"
    assert style(page, code, "paddingRight") == "5px"

    # Offline, MathJax never loads: every span ends "failed" and keeps the fallback styling.
    settle_math(page)
    assert page.evaluate("[...document.querySelectorAll('.math')].map(s => s.dataset.math)") == [
        "failed",
        "failed",
    ]
    math = ".text .math"
    assert style(page, math, "color") == "rgb(34, 34, 34)"
    assert style(page, math, "backgroundColor") == "rgb(245, 245, 245)"
    assert style(page, math, "fontFamily").startswith("Consolas")
    assert style(page, math, "fontSize") == f"{FONT - 2}px"

    assert style(page, ".text a", "color") == style(page, "#item-1_1 .para", "color")
    assert style(page, ".text a", "textDecorationLine") == "underline"
    assert style(page, ".intro", "fontSize") == f"{NOTE_FONT}px"
    assert style(page, ".intro", "color") == "rgb(78, 78, 78)"
    assert style(page, ".intro code", "fontSize") == f"{NOTE_FONT - 2}px"
    assert rect(page, ".intro p")["height"] == NOTE_LINE
    check_laws(page)


@pytest.mark.parametrize("scheme", SCHEMES)
def test_contrast(open_outline, page, scheme):
    open_visual(open_outline, page, scheme)
    assert page.evaluate("matchMedia('(prefers-color-scheme: dark)').matches") == (scheme == "dark")
    expand_1(page)
    page.keyboard.press("ArrowRight")
    assert page.evaluate("window.tractatus.state().activeId") == "1.1"
    settle_math(page)
    # The copy-link toast, shown by hand so the sweep does not race its 2 s timer.
    page.evaluate(
        "() => { const t = document.getElementById('toast'); t.hidden = false; t.textContent = 'Link copied'; }"
    )
    results = page.evaluate(CONTRAST_JS, PAGE_TEXT)
    swept = {r["sel"] for r in results}
    # The active row holds code, a link, math, a note and a label.
    assert {".row .para", ".row code", ".row .math", ".row a", ".label", ".intro code", "#toast"} <= swept
    # The active row's label sits in the gutter, outside the row: it is painted over the page.
    active_labels = [r for r in results if r["sel"] == ".label" and r["active"]]
    assert [r["bg"] for r in active_labels] == [PAGE[scheme]], active_labels
    page.keyboard.press("Shift+Slash")
    assert page.get_attribute("#help", "open") is not None
    help_results = page.evaluate(CONTRAST_JS, HELP_TEXT)
    assert {r["sel"] for r in help_results} == set(HELP_TEXT)
    failures = [
        f"{r['sel']}: {r['ratio']:.2f} {r['html']}"
        for r in results + help_results
        if r["ratio"] < 4.5
    ]
    assert failures == []

    # The find count shows only under a query; "beta" keeps 1.1 shown and active. Esc in the box
    # clears it and returns focus to 1.1.
    page.keyboard.press("Escape")
    page.fill("#find-input", "beta")
    counted = page.evaluate(CONTRAST_JS, PAGE_TEXT)
    assert ".find-count" in {r["sel"] for r in counted}
    assert [f"{r['sel']}: {r['ratio']:.2f}" for r in counted if r["ratio"] < 4.5] == []
    page.press("#find-input", "Escape")
    assert page.evaluate("window.tractatus.state().activeId") == "1.1"

    # Bullet glyphs are graphics: >= 3:1 (law V). Here 1.1, a leaf, is active.
    bullets = page.evaluate(BULLET_CONTRAST_JS)

    # BULLET_MD: the active row is a parent, Parent one, in each of its bullet states.
    open_outline(BULLET_MD)
    toggle = "#item-p-1 > .row > .toggle"
    assert page.evaluate("window.tractatus.state().activeId") == "p-1"
    bullets += page.evaluate(BULLET_CONTRAST_JS)          # ring on --active
    page.hover("#item-p-1 > .row > .text")
    bullets += page.evaluate(BULLET_CONTRAST_JS)          # plus on --active
    page.click(toggle)
    assert page.get_attribute("#item-p-1", "aria-expanded") == "true"
    bullets += page.evaluate(BULLET_CONTRAST_JS)          # minus on --active
    page.hover("#item-p-3 > .row > .text")
    bullets += page.evaluate(BULLET_CONTRAST_JS)          # disc on --active; plus on --bg
    page.mouse.move(0, 0)
    bullets += page.evaluate(BULLET_CONTRAST_JS)
    swept = {(r["active"], r["expanded"], r["pseudo"], r["kind"]) for r in bullets}
    assert {
        (True, None, "::before", "background"),            # 1.1: leaf disc
        (True, "false", "::before", "background"),         # ring's dot, and the plus bar
        (True, "false", "::after", "box-shadow"),          # ring
        (True, "false", "::after", "background"),          # plus's vertical bar
        (True, "true", "::before", "background"),          # minus, then disc
        (False, "false", "::after", "box-shadow"),
        (False, "false", "::after", "background"),
        (False, None, "::before", "background"),
    } <= swept, swept
    failures = [r for r in bullets if r["ratio"] < 3.0]
    assert failures == []

    # Narrow viewport: labels are inline, so the active row's label is painted over --active.
    page.set_viewport_size(NARROW)
    open_outline(VISUAL_MD)
    expand_1(page)
    page.keyboard.press("ArrowRight")
    assert page.evaluate("window.tractatus.state().activeId") == "1.1"
    settle_math(page)
    narrow = page.evaluate(CONTRAST_JS, PAGE_TEXT)
    active_labels = [r for r in narrow if r["sel"] == ".label" and r["active"]]
    assert [r["bg"] for r in active_labels] == [ACTIVE[scheme]], active_labels
    failures = [f"{r['sel']}: {r['ratio']:.2f} {r['html']}" for r in narrow if r["ratio"] < 4.5]
    assert failures == []


FIND_BOX_JS = (
    "() => {"
    + CONTRAST_LIB
    + r"""
  const input = document.getElementById("find-input");
  const text = getComputedStyle(input).color;
  const placeholder = getComputedStyle(input, "::placeholder").color;
  const bg = background(input);
  const on = (c) => { const fg = parse(c); return ratio(fg.a < 1 ? over(fg, bg) : fg, bg); };
  return { text, placeholder, textRatio: on(text), placeholderRatio: on(placeholder) };
}"""
)


@pytest.mark.parametrize("scheme", SCHEMES)
def test_find_box_contrast(open_outline, page, scheme):
    """Law V for the find box: the text sweep reads text nodes, which misses an input's value and
    its placeholder."""
    open_visual(open_outline, page, scheme)
    got = page.evaluate(FIND_BOX_JS)
    assert got["text"] and got["placeholder"], got
    assert got["textRatio"] >= 4.5 and got["placeholderRatio"] >= 4.5, got
    check_laws(page)


def _block_end(css: str, open_brace: int) -> int:
    depth = 0
    for i in range(open_brace, len(css)):
        if css[i] == "{":
            depth += 1
        elif css[i] == "}":
            depth -= 1
            if depth == 0:
                return i + 1
    raise AssertionError("unbalanced braces")


def _cut_block(css: str, opener: str) -> str:
    start = css.index(opener)
    return css[:start] + css[_block_end(css, css.index("{", start)) :]


def test_no_raw_colours_in_components():
    t = template_text()
    css = t[t.index("<style>") : t.index("</style>")]
    css = _cut_block(css, "@layer tokens {")
    start = css.index("@layer base {")
    states = css.index("@layer states {")
    css = css[start : _block_end(css, css.index("{", states))]
    css = _cut_block(css, "@media (forced-colors: active) {")
    assert re.findall(r"#[0-9a-fA-F]{3,8}\b", css) == []
    allowed = re.sub(r"box-shadow:[^;}]*", "", css)
    allowed = re.sub(r"[^{}]*::backdrop\s*\{[^}]*\}", "", allowed)
    assert re.findall(r"\b(?:rgba?|hsla?)\(", allowed) == []


def test_laws_after_restyle(open_outline, page):
    open_visual(open_outline, page)
    check_laws(page)
    expand_1(page)
    check_laws(page)
    page.keyboard.press("ArrowRight")
    page.keyboard.press("ArrowDown")
    page.keyboard.press("ArrowRight")
    check_laws(page)
    page.click("#item-1_2_1 > .row > .text")
    assert page.evaluate("window.tractatus.state().activeId") == "1.2.1"
    check_laws(page)
    page.hover("#item-2 > .row > .text")
    check_laws(page)


# ── Phase 2: Dynalist bullets as the toggle ─────────────────────────────


def pseudo(page, id, which):
    return page.evaluate(PSEUDO_JS, [f"#item-{id} > .row > .toggle", which])


def px(value: str) -> float:
    assert value.endswith("px"), value
    return float(value[:-2])


def size(page, id, which):
    s = pseudo(page, id, which)
    return px(s["width"]), px(s["height"])


def assert_size(actual, want):
    # Chromium keeps layout sizes in 1/64px units: 6.4px computes as 6.39062px.
    assert all(abs(a - w) <= 1 / 64 for a, w in zip(actual, want, strict=True)), (actual, want)


def ring(page, id, colour):
    after = pseudo(page, id, "::after")
    assert after["display"] == "block"
    assert_size((px(after["width"]), px(after["height"])), (12, 12))
    assert after["borderRadius"] == "50%"
    # The 1.5px stroke is an inset shadow; a 1.5px border would be floored to 1px (Chromium).
    assert after["boxShadow"] == f"{colour} 0px 0px 0px 1.5px inset"
    assert after["borderWidth"] == "0px"
    assert_size(size(page, id, "::before"), (6, 6))


def plus(page, id, colour):
    before, after = pseudo(page, id, "::before"), pseudo(page, id, "::after")
    assert_size(size(page, id, "::before"), (10.5, 1.5))
    assert_size(size(page, id, "::after"), (1.5, 10.5))
    for s in (before, after):
        assert s["background"] == colour
        assert s["borderRadius"] == "0px"
        assert s["borderWidth"] == "0px"
    assert after["boxShadow"] == "none"


def minus(page, id, colour):
    assert_size(size(page, id, "::before"), (11, 1.5))
    before = pseudo(page, id, "::before")
    assert before["background"] == colour
    assert before["borderRadius"] == "0px"
    assert pseudo(page, id, "::after")["display"] == "none"


def disc(page, id, colour):
    before = pseudo(page, id, "::before")
    assert_size(size(page, id, "::before"), (6.4, 6.4))
    assert before["borderRadius"] == "50%"
    assert before["background"] == colour
    assert pseudo(page, id, "::after")["display"] == "none"


def open_bullets(open_outline, page, scheme="light"):
    page.emulate_media(color_scheme=scheme)
    return open_outline(BULLET_MD)


def test_bullet_column(open_outline, page):
    open_bullets(open_outline, page)
    page.focus("#item-p-1")
    page.keyboard.press("ArrowRight")          # expand Parent one
    page.keyboard.press("ArrowDown")
    page.keyboard.press("ArrowDown")           # Child parent
    page.keyboard.press("ArrowRight")          # expand it
    assert page.get_attribute("#item-p-1-2", "aria-expanded") == "true"
    rows = page.evaluate(
        """() => [...document.querySelectorAll('[role=treeitem]:not(#item-root)')].filter(li => li.checkVisibility())
        .map(li => { const box = (sel) => { const r = li.querySelector(sel).getBoundingClientRect();
                                           return { left: r.left, top: r.top, width: r.width, height: r.height }; };
          return { id: li.dataset.id, row: box(':scope > .row'), toggle: box(':scope > .row > .toggle'),
                   text: box(':scope > .row > .text'),
                   glyph: li.querySelector(':scope > .row > .toggle').textContent }; })"""
    )
    assert [r["id"] for r in rows] == ["p-1", "p-1-1", "p-1-2", "p-1-2-1", "p-2", "p-3"]
    for r in rows:
        row, toggle, text = r["row"], r["toggle"], r["text"]
        assert abs(toggle["width"] - TEXT_X) <= 0.5, r       # the hit area reaches the text
        assert abs(toggle["height"] - LINE) <= 0.5, r
        assert abs(toggle["left"] - row["left"]) <= 0.5, r
        assert abs(toggle["top"] - (row["top"] + PAD_TOP)) <= 0.5, r
        assert abs(text["left"] - (row["left"] + TEXT_X)) <= 0.5, r
        assert r["glyph"] == "", r
    # The 1px guide (10px margin, then the border) runs under the parent's bullet: the bullet's
    # centre, 11px in, is the guide's right edge, so the guide's centre is 0.5px left of it.
    # The child's bullet column starts one indent in, INDENT - TEXT_X right of the parent's text.
    by_id = {r["id"]: r for r in rows}
    for parent, child in (("p-1", "p-1-1"), ("p-1-2", "p-1-2-1")):
        guide = rect(page, f"#item-{parent} > [role=group]")["left"]
        centre = by_id[parent]["toggle"]["left"] + BULLET_COL / 2
        assert abs(guide + 0.5 - centre) <= 0.5
        child_left = by_id[child]["toggle"]["left"]
        assert abs(child_left - by_id[parent]["toggle"]["left"] - INDENT) <= 0.5
        assert abs(child_left - by_id[parent]["text"]["left"] - (INDENT - TEXT_X)) <= 0.5
    check_laws(page)


@pytest.mark.parametrize("scheme", SCHEMES)
def test_bullet_shapes(open_outline, page, scheme):
    open_bullets(open_outline, page, scheme)
    page.focus("#item-p-1")
    page.keyboard.press("ArrowRight")
    assert page.get_attribute("#item-p-1", "aria-expanded") == "true"
    page.mouse.move(0, 0)
    colour = BULLET[scheme]
    disc(page, "p-1", colour)        # expanded parent
    disc(page, "p-1-1", colour)      # leaf
    disc(page, "p-2", colour)        # leaf
    ring(page, "p-1-2", colour)      # collapsed parent
    ring(page, "p-3", colour)
    before = pseudo(page, "p-3", "::before")
    assert before["background"] == colour
    assert before["borderRadius"] == "50%"
    for id in ("p-1", "p-1-1", "p-1-2", "p-2", "p-3"):
        for which in ("::before", "::after"):
            s = pseudo(page, id, which)
            assert s["content"] == '""', (id, which)
            assert s["translate"] == "-50% -50%", (id, which)
    check_laws(page)


def test_bullet_hover(open_outline, page):
    open_bullets(open_outline, page)
    colour = BULLET["light"]
    page.focus("#item-p-1")
    page.keyboard.press("ArrowRight")
    page.hover("#item-p-3 > .row > .text")
    plus(page, "p-3", colour)
    check_laws(page)
    page.hover("#item-p-1 > .row > .text")
    minus(page, "p-1", colour)
    ring(page, "p-3", colour)                  # no longer hovered
    check_laws(page)
    page.hover("#item-p-2 > .row > .text")
    disc(page, "p-2", colour)                  # leaves do not change
    disc(page, "p-1", colour)
    check_laws(page)
    page.hover("#item-p-3 > .row > .text")
    plus(page, "p-3", colour)
    page.mouse.move(0, 0)
    ring(page, "p-3", colour)
    check_laws(page)


def test_bullet_click_toggles(open_outline, page):
    open_bullets(open_outline, page)
    colour = BULLET["light"]
    assert page.evaluate("window.tractatus.state().activeId") == "p-1"
    page.click("#item-p-3 > .row > .toggle")
    assert page.get_attribute("#item-p-3", "aria-expanded") == "true"
    assert page.is_visible("#item-p-3-1")
    minus(page, "p-3", colour)                 # the mouse is still over the row
    assert page.evaluate("window.tractatus.state().activeId") == "p-3"
    check_laws(page)
    page.click("#item-p-3 > .row > .toggle")
    assert page.get_attribute("#item-p-3", "aria-expanded") == "false"
    plus(page, "p-3", colour)
    assert page.evaluate("window.tractatus.state().activeId") == "p-3"
    check_laws(page)


def test_no_text_glyphs(open_outline, page):
    t = template_text()
    assert "▸" not in t
    assert "•" not in t
    open_bullets(open_outline, page)
    page.focus("#item-p-1")
    page.keyboard.press("ArrowRight")
    glyphs = page.evaluate(
        "[...document.querySelectorAll('#outline *')]"
        ".filter(e => /^[\\s•▸+−]+$/.test(e.textContent)).map(e => e.outerHTML)"
    )
    assert glyphs == []


# ── Phase 3: gutter labels ──────────────────────────────────────────────

# Labels to depth 4. The last label has the example's longest label length, 7 characters
# (examples/tractatus.md has 6.36311 and six others); rendered at 12px in the headless
# Chromium monospace fallback it measures 50.578px wide.
LABEL_MD = """\
# Labels

- 1 One
  - 1.1 One one
    - 1.11 One one one
      - 1.111 Deep
- 2 Two with a longer text that wraps onto a second line in narrow viewports, so the label stays on the first line
- Unlabelled item
- 6.36311 Longest label
"""

LONG_LABEL_MD = """\
# Long labels

- 1 Short
- 1.2345678901 Long
"""

# A zero-size inline-block's top is the baseline of the line it sits on.
ROWS_JS = """() => [...document.querySelectorAll('[role=treeitem]:not(#item-root)')].filter(li => li.checkVisibility())
  .map(li => { const box = (e) => { if (!e) return null; const r = e.getBoundingClientRect();
                                   return { left: r.left, right: r.right, top: r.top, height: r.height }; };
    const baseline = (host, where = "prepend") => {
      if (!host) return null;
      const m = document.createElement("span");
      m.style.cssText = "display:inline-block;inline-size:0;block-size:0";
      host[where](m);
      const y = m.getBoundingClientRect().top;
      m.remove();
      return y;
    };
    const label = li.querySelector(':scope > .row .label');
    const para = li.querySelector(':scope > .row .para');
    return { id: li.dataset.id, active: li.tabIndex === 0,
             row: box(li.querySelector(':scope > .row')),
             label: box(label), labelBase: baseline(label),
             textBase: baseline(label ? label.parentElement : para, label ? "after" : "prepend"),
             text: box(li.querySelector(':scope > .row > .text')) }; })"""


def open_labels(open_outline, page, viewport=WIDE, md=LABEL_MD):
    page.set_viewport_size(viewport)
    return open_outline(md)


def expand_chain(page):
    """Expand 1, 1.1 and 1.11 with ArrowRight down the chain; 1.111 ends active."""
    page.focus("#item-1")
    for _ in range(6):
        page.keyboard.press("ArrowRight")
    assert page.evaluate("window.tractatus.state().activeId") == "1.111"
    assert page.is_visible("#item-1_111")


def rows(page):
    return {r["id"]: r for r in page.evaluate(ROWS_JS)}


def test_gutter_alignment(open_outline, page):
    open_labels(open_outline, page)
    expand_chain(page)
    by_id = rows(page)
    assert list(by_id) == ["1", "1.1", "1.11", "1.111", "2", "p-3", "6.36311"]
    outline = rect(page, "#outline")
    for id, r in by_id.items():
        row, label, text = r["row"], r["label"], r["text"]
        assert abs(text["left"] - (row["left"] + TEXT_X)) <= 0.5, r
        if id == "p-3":
            assert label is None
            continue
        assert abs(label["right"] - (outline["left"] - 8)) <= 0.5, r
        assert abs(r["labelBase"] - r["textBase"]) <= 0.5, r      # on the first line's baseline
        assert row["top"] + PAD_TOP <= label["top"] < row["top"] + PAD_TOP + LINE, r
    assert by_id["6.36311"]["label"]["left"] >= rect(page, "main")["left"]
    check_laws(page)


def test_gutter_label_style(open_outline, page):
    open_labels(open_outline, page)
    assert page.evaluate("window.tractatus.state().activeId") == "1"
    label = "#item-2 > .row .label"
    assert style(page, label, "position") == "absolute"
    assert style(page, label, "fontSize") == "12px"
    assert style(page, label, "lineHeight") == f"{LINE:g}px"
    assert style(page, label, "fontFamily").split(",")[0].strip() == "Consolas"
    assert style(page, label, "color") == "rgb(107, 107, 107)"
    # The active background is the row's only; the gutter label lies outside it.
    assert rect(page, "#item-1 > .row .label")["right"] < rect(page, "#item-1 > .row")["left"]


def test_narrow_labels(open_outline, page):
    open_labels(open_outline, page, NARROW)
    expand_chain(page)
    by_id = rows(page)
    labelled = {id: r for id, r in by_id.items() if r["label"] is not None}
    assert set(labelled) == {"1", "1.1", "1.11", "1.111", "2", "6.36311"}
    # The label is the text's inline prefix: it starts the text column, on its first baseline,
    # and the text wraps under it (the label takes no measure from the lines below).
    for r in labelled.values():
        assert abs(r["text"]["left"] - (r["row"]["left"] + TEXT_X)) <= 0.5, r
        assert abs(r["label"]["left"] - r["text"]["left"]) <= 0.5, r
        assert abs(r["labelBase"] - r["textBase"]) <= 0.5, r
    assert page.evaluate(
        "[...document.querySelectorAll('.label')].every(l => getComputedStyle(l).position === 'static')"
    )
    two = by_id["2"]
    assert two["text"]["height"] >= 2 * LINE, two        # wraps onto more lines than its label
    assert two["row"]["top"] + PAD_TOP <= two["label"]["top"] < two["row"]["top"] + PAD_TOP + LINE, two
    assert style(page, "main", "paddingLeft") == "16px"
    check_laws(page)


def test_accessible_name_unchanged(open_outline, page):
    for viewport in (WIDE, NARROW):
        open_labels(open_outline, page, viewport)
        expand_chain(page)
        name = re.compile(r"^1\.11 One one one")
        assert page.get_by_role("treeitem", name=name).count() == 1, viewport


def test_gutter_grows_for_long_labels(open_outline, page):
    for viewport in ({"width": 700, "height": 600}, WIDE):
        open_labels(open_outline, page, viewport, LONG_LABEL_MD)
        label = rect(page, "#item-1_2345678901 > .row .label")
        outline = rect(page, "#outline")
        assert label["left"] >= 0, (viewport, label)
        assert label["left"] >= rect(page, "main")["left"], (viewport, label)
        assert abs(label["right"] - (outline["left"] - 8)) <= 0.5, (viewport, label)
        assert abs(rect(page, "#doc-title")["left"] - outline["left"]) <= 0.5, viewport
    open_visual(open_outline, page)
    assert style(page, "main", "paddingLeft") == f"{COLUMN_PAD}px"


def test_laws_after_labels(open_outline, page):
    open_labels(open_outline, page)
    check_laws(page)
    expand_chain(page)
    check_laws(page)
    page.click("#item-2 > .row > .text")
    assert page.evaluate("window.tractatus.state().activeId") == "2"
    check_laws(page)
    page.set_viewport_size(NARROW)
    check_laws(page)
    page.keyboard.press("ArrowUp")
    page.keyboard.press("ArrowLeft")
    check_laws(page)
    page.set_viewport_size(WIDE)
    check_laws(page)
