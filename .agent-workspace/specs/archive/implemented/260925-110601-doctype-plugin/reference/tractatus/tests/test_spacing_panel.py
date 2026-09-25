"""The Spacing panel: reader-set text size, line height, item gap, indent and column width."""

import json

import pytest
from conftest import SKILL_DIR, check_laws
from hypothesis import example, given, settings
from hypothesis import strategies as st
from test_tree_keyboard import MOD, state
from test_visual import (
    BULLET_COL,
    CONTRAST_JS,
    FONT,
    GAP,
    GROUP_GAP,
    GUIDE_X,
    INDENT,
    LINE,
    NOTE_FONT,
    SCHEMES,
    WIDE,
    rect,
    style,
)

KEY = "my-tractatus:spacing"


def row_height(line, gap):
    """A one-line row: a whole gap above the text and half a gap below, as Dynalist's highlight."""
    return gap + line + gap / 2

EXAMPLE = SKILL_DIR / "examples" / "tractatus.html"

# name, storage key, min, max, step, default, shown as
KNOBS = [
    ("Text size", "fontSize", 16, 24, 1, 20, "20 px"),
    ("Line height", "lh", 1.2, 1.9, 0.05, 1.5, "1.50×"),
    ("Item spacing", "itemGap", 2, 28, 1, 10, "10 px"),
    ("Indent", "indent", 18, 56, 1, 30, "30 px"),
    ("Column width", "column", 560, 1200, 20, 820, "820 px"),
]
DEFAULTS = {key: default for _, key, _, _, _, default, _ in KNOBS}
MINS = {key: lo for _, key, lo, *_ in KNOBS}
MAXES = {key: hi for _, key, _, hi, *_ in KNOBS}

SPACING_MD = """\
# Spacing

- 1 Alpha is one long first paragraph that wraps onto several lines at every column width and \
text size the panel allows, so that the leading between its own lines can be measured against \
the gap to the next item below it. It keeps going for a while longer, well past the point where \
even the widest column at the smallest text size has had to break it at least once, and then \
it goes on a little further still, just to be sure of the second line.
- 2 Beta has a note.

  Beta's note is a second paragraph, which the page renders as a Dynalist note under its item.
- 3 Gamma
  - 3.1 Child
    - 3.1.1 Grandchild
- 4 Delta
"""

# Line boxes of an element's text, top to bottom: client rects of its contents, merged per line.
LINES_JS = """sel => {
  const range = document.createRange();
  const lines = [];
  const walker = document.createTreeWalker(document.querySelector(sel), NodeFilter.SHOW_TEXT);
  for (let node = walker.nextNode(); node !== null; node = walker.nextNode()) {
    if (node.parentElement.closest(".gutter")) continue;     // the label is not the text's line
    range.selectNodeContents(node);
    for (const r of range.getClientRects()) {
      if (r.width === 0) continue;
      const line = lines.find((l) => Math.abs(l.top - r.top) < 1);
      if (line) line.bottom = Math.max(line.bottom, r.bottom);
      else lines.push({ top: r.top, bottom: r.bottom });
    }
  }
  return lines.sort((a, b) => a.top - b.top);
}"""

SET_JS = """([id, v]) => {
  const input = document.getElementById(id);
  input.value = String(v);
  input.dispatchEvent(new Event("input", { bubbles: true }));
}"""

PANEL_TEXT = [
    "#spacing h2",
    "#spacing label",
    "#spacing output",
    "#spacing .panel-button",
    "#spacing .spacing-ref",
    "#spacing .spacing-note",
    "#spacing .status",
    "#spacing-button",
]


def slider(page, name):
    return page.get_by_role("slider", name=name, exact=True)


def set_knob(page, key, value):
    page.evaluate(SET_JS, [f"spacing-{key}", value])


def set_knobs(page, values):
    for key, v in values.items():
        set_knob(page, key, v)


def output(page, key):
    return page.text_content(f"output[for=spacing-{key}]")


def stored(page):
    raw = page.evaluate(f"localStorage.getItem({json.dumps(KEY)})")
    return None if raw is None else json.loads(raw)


def open_panel(page):
    page.click("#spacing-button")
    assert page.get_attribute("#spacing", "open") is not None


def top(page, id):
    return rect(page, f"#item-{id} > .row")["top"]


def left(page, id):
    return rect(page, f"#item-{id} > .row")["left"]


@pytest.fixture
def panel(open_outline, page):
    page.set_viewport_size(WIDE)
    open_outline(SPACING_MD)
    page.focus("#item-3")
    page.keyboard.press("ArrowRight")        # expand 3
    page.keyboard.press("ArrowRight")        # 3.1
    page.keyboard.press("ArrowRight")        # expand 3.1
    assert state(page) == {"expanded": ["3", "3.1"], "activeId": "3.1"}
    open_panel(page)
    return page


def test_opens_non_modal(panel):
    page = panel
    assert page.get_attribute("#spacing-button", "aria-expanded") == "true"
    assert page.evaluate("document.getElementById('spacing').matches(':modal')") is False
    assert page.evaluate("document.activeElement.id") == "spacing-fontSize"
    # The outline stays visible, uninert and live behind the panel.
    assert page.evaluate("document.querySelector('[inert]')") is None
    assert page.is_visible("#item-3_1_1")
    page.click("#item-2 > .row > .text")
    assert state(page)["activeId"] == "2"
    assert page.get_attribute("#spacing", "open") is not None
    check_laws(page)


def test_labels_outputs_defaults(panel):
    page = panel
    for name, key, lo, hi, step, default, shown in KNOBS:
        s = slider(page, name)
        assert s.count() == 1, name
        assert s.get_attribute("id") == f"spacing-{key}"
        assert [s.get_attribute(a) for a in ("min", "max", "step")] == [str(lo), str(hi), str(step)]
        assert float(s.input_value()) == default, name
        assert output(page, key) == shown, name
    assert slider(page, "Line height").get_attribute("aria-valuetext") == "1.50 times the text size"
    assert slider(page, "Item spacing").get_attribute("aria-valuetext") == "10 pixels"
    assert page.text_content("#spacing-storage") == "Saved in this browser"
    assert "Dynalist large / cozy" in page.text_content("#spacing .spacing-ref")


def test_targets_and_focus(panel):
    page = panel
    sizes = page.evaluate(
        "[...document.querySelectorAll('#spacing button, #spacing input, .page-tools button')]"
        ".filter(e => e.checkVisibility()).map(e => { const r = e.getBoundingClientRect(); return [e.id || e.textContent, r.width, r.height]; })"
    )
    assert len(sizes) == 5 + 2 + 3
    assert all(w >= 24 and h >= 24 for _, w, h in sizes), sizes
    page.keyboard.press("Tab")
    assert page.evaluate("document.activeElement.id") == "spacing-lh"
    assert style(page, "#spacing-lh", "outlineStyle") == "solid"


def test_keyboard_changes_geometry(panel):
    page = panel
    slider(page, "Text size").press("ArrowRight")
    assert output(page, "fontSize") == "21 px"
    assert style(page, "#item-1 .para", "fontSize") == "21px"
    assert style(page, "#item-1 > .row", "lineHeight") == f"{21 * 1.5:g}px"
    assert style(page, "#item-2 .para + .para", "fontSize") == "18px"
    slider(page, "Text size").press("Home")
    assert output(page, "fontSize") == "16 px"
    set_knob(page, "fontSize", FONT)

    slider(page, "Line height").press("End")
    assert output(page, "lh") == "1.90×"
    assert slider(page, "Line height").get_attribute("aria-valuetext") == "1.90 times the text size"
    line = FONT * 1.9
    assert abs(rect(page, "#item-4 .para")["height"] - line) <= 0.5
    toggle = rect(page, "#item-4 > .row > .toggle")
    assert abs(toggle["height"] - line) <= 0.5
    assert abs(rect(page, "#item-4 > .row")["height"] - row_height(line, GAP)) <= 0.5
    note = page.evaluate(LINES_JS, "#item-2 .para + .para")          # wraps: line pitch
    assert abs(note[1]["top"] - note[0]["top"] - NOTE_FONT * 1.9) <= 0.5
    slider(page, "Line height").press("ArrowLeft")
    assert output(page, "lh") == "1.85×"
    set_knob(page, "lh", 1.5)

    slider(page, "Item spacing").press("ArrowRight")
    assert output(page, "itemGap") == "11 px"
    # Two groups close between 3.1.1 and 4: the fixed group gap twice, whatever the item gap.
    assert abs(top(page, "4") - top(page, "3_1_1") - (LINE + 11 + 2 * GROUP_GAP)) <= 0.5
    assert abs(top(page, "3_1") - top(page, "3") - (LINE + 11)) <= 0.5

    slider(page, "Indent").fill("44")
    assert output(page, "indent") == "44 px"
    assert abs(left(page, "3_1") - left(page, "3") - 44) <= 0.5
    assert abs(left(page, "3_1_1") - left(page, "3_1") - 44) <= 0.5
    guide = rect(page, "#item-3 > [role=group]")["left"]
    assert abs(guide - left(page, "3") - GUIDE_X) <= 0.5
    assert abs(guide + 0.5 - (left(page, "3") + BULLET_COL / 2)) <= 0.5

    slider(page, "Column width").press("ArrowRight")
    assert output(page, "column") == "840 px"
    assert rect(page, "main")["width"] == 840
    set_knob(page, "column", 1000)
    assert rect(page, "main")["width"] == 1000
    assert rect(page, ".page-head")["width"] == 1000
    assert stored(page) == {**DEFAULTS, "itemGap": 11, "indent": 44, "column": 1000}
    check_laws(page)


def test_ladder(panel):
    """Rows sit farther apart than the lines inside a row, and a note is nearer its own item."""
    page = panel

    @settings(max_examples=25, deadline=None)
    @given(
        font=st.integers(16, 24),
        lh=st.integers(0, 14).map(lambda n: round(1.2 + 0.05 * n, 2)),
        gap=st.integers(2, 28),
        indent=st.integers(18, 56),
        column=st.integers(0, 32).map(lambda n: 560 + 20 * n),
    )
    # Glyphs sit 0px under the line top and 1.75px over its bottom: found by hypothesis.
    @example(font=19, lh=1.25, gap=2, indent=18, column=560)
    def check(font, lh, gap, indent, column):
        values = {"fontSize": font, "lh": lh, "itemGap": gap, "indent": indent, "column": column}
        set_knobs(page, values)
        alpha = page.evaluate(LINES_JS, "#item-1 .para")
        assert len(alpha) >= 2, values
        within = alpha[1]["top"] - alpha[0]["bottom"]
        beta, note = page.evaluate(LINES_JS, "#item-2 .para"), page.evaluate(LINES_JS, "#item-2 .para + .para")
        between = beta[0]["top"] - alpha[-1]["bottom"]
        assert between > within, values
        assert abs(between - within - gap) <= 0.5, values
        gamma = page.evaluate(LINES_JS, "#item-3 .para")
        to_note = note[0]["top"] - beta[-1]["bottom"]
        to_next = gamma[0]["top"] - note[-1]["bottom"]
        assert to_note < to_next, (values, to_note, to_next)

    check()
    check_laws(page)


def test_reset(panel):
    page = panel
    set_knobs(page, MAXES)
    assert stored(page) == MAXES
    assert page.evaluate("document.documentElement.style.length") > 0
    page.click("#spacing-reset")
    page.wait_for_function(
        "() => document.getElementById('spacing-status').textContent === 'Spacing reset to defaults'"
    )
    for name, key, *_, default, shown in KNOBS:
        assert float(slider(page, name).input_value()) == default
        assert output(page, key) == shown
    assert stored(page) is None
    # Only --label-chars is left on :root.
    # Only layout properties (the label gutter, the tree's depth, the header's height) are left.
    assert sorted(page.evaluate("[...document.documentElement.style]")) == ["--depth", "--head-block", "--label-chars"]
    # Rows overlap by half a gap: the pitch is a row's height less GAP / 2.
    assert abs(top(page, "2") - top(page, "1") - rect(page, "#item-1 > .row")["height"] + GAP / 2) <= 0.5
    assert abs(rect(page, "#item-4 > .row")["height"] - row_height(LINE, GAP)) <= 0.5
    assert abs(left(page, "3_1") - left(page, "3") - INDENT) <= 0.5
    # A change clears the announcement; a second reset announces again.
    set_knob(page, "itemGap", 12)
    assert page.text_content("#spacing-status") == ""
    page.click("#spacing-reset")
    page.wait_for_function(
        "() => document.getElementById('spacing-status').textContent === 'Spacing reset to defaults'"
    )
    check_laws(page)


def test_persists_across_reload(panel):
    page = panel
    values = {"fontSize": 17, "lh": 1.65, "itemGap": 16, "indent": 40, "column": 700}
    set_knobs(page, values)
    assert stored(page) == values
    page.reload()
    page.wait_for_function("() => document.documentElement.dataset.outlineReady === 'true'")
    assert page.get_attribute("#spacing", "open") is None
    assert style(page, "#item-1 > .row", "lineHeight") == f"{17 * 1.65:g}px"
    assert rect(page, "main")["width"] == 700
    open_panel(page)
    assert output(page, "lh") == "1.65×"
    assert output(page, "column") == "700 px"
    assert float(slider(page, "Indent").input_value()) == 40


@pytest.mark.parametrize(
    ("raw", "want"),
    [
        ("not json{", DEFAULTS),
        ("null", DEFAULTS),
        ("[1, 2]", DEFAULTS),
        ('"a string"', DEFAULTS),
        (
            json.dumps({"fontSize": 99, "lh": 0.1, "itemGap": -5, "indent": "40", "column": 1e9}),
            {**DEFAULTS, "fontSize": 24, "lh": 1.2, "itemGap": 2, "column": 1200},
        ),
        (json.dumps({"lh": 1.5333, "column": 833, "extra": 1}), {**DEFAULTS, "lh": 1.55, "column": 840}),
    ],
)
def test_garbage_storage(open_outline, page, raw, want):
    open_outline(SPACING_MD)
    page.evaluate("([k, v]) => localStorage.setItem(k, v)", [KEY, raw])
    page.reload()
    page.wait_for_function("() => document.documentElement.dataset.outlineReady === 'true'")
    open_panel(page)
    got = {key: float(slider(page, name).input_value()) for name, key, *_ in KNOBS}
    assert got == want
    assert style(page, "main", "maxWidth") == f"{want['column']}px"
    check_laws(page)


def test_storage_unavailable(open_outline, page):
    page.add_init_script(
        "Object.defineProperty(window, 'localStorage', { get() {"
        " throw new DOMException('The operation is insecure.', 'SecurityError'); } });"
    )
    open_outline(SPACING_MD)
    open_panel(page)
    assert page.text_content("#spacing-storage") == "Not saved (storage unavailable)"
    set_knob(page, "itemGap", 20)
    assert abs(rect(page, "#item-4 > .row")["height"] - row_height(LINE, 20)) <= 0.5
    assert page.text_content("#spacing-storage") == "Not saved (storage unavailable)"
    check_laws(page)


def test_keyboard_isolation(panel):
    page = panel
    before = state(page)
    s = slider(page, "Item spacing")
    for key in ("ArrowRight", "ArrowUp", "ArrowDown", "ArrowLeft", "ArrowLeft", "End", "Home"):
        s.press(key)
        assert state(page) == before, key
        assert page.evaluate("document.activeElement.id") == "spacing-itemGap"
    assert output(page, "itemGap") == "2 px"
    for target in ("#spacing-itemGap", "#spacing-close", "#spacing-reset"):
        page.focus(target)
        page.keyboard.press("Shift+Slash")
        assert page.get_attribute("#help", "open") is None, target
    page.keyboard.press(f"{MOD}+Period")
    page.keyboard.press("Shift+Digit8")
    assert state(page) == before
    check_laws(page)


def test_closing(panel):
    page = panel
    page.keyboard.press("Escape")
    assert page.get_attribute("#spacing", "open") is None
    assert page.evaluate("document.activeElement.id") == "spacing-button"
    assert page.get_attribute("#spacing-button", "aria-expanded") == "false"
    open_panel(page)
    page.click("#spacing-close")
    assert page.get_attribute("#spacing", "open") is None
    assert page.evaluate("document.activeElement.id") == "spacing-button"
    open_panel(page)
    page.click("#spacing-button")            # the trigger toggles
    assert page.get_attribute("#spacing", "open") is None
    # Escape from the keyboard, after a slider change, still returns to the trigger.
    page.keyboard.press("Enter")
    assert page.evaluate("document.activeElement.id") == "spacing-fontSize"
    page.keyboard.press("ArrowRight")
    page.keyboard.press("Escape")
    assert page.evaluate("document.activeElement.id") == "spacing-button"
    assert state(page)["activeId"] == "3.1"
    check_laws(page)


def test_header_clear_of_title(open_outline, page):
    """The tools sit above the title at every column width; a long title wraps in the column."""
    page.set_viewport_size(WIDE)
    open_outline("# Tractatus Logico-Philosophicus and a Few Words More\n\nAn intro note.\n\n- 1 One\n")
    head = rect(page, ".page-head")["height"]
    open_panel(page)
    for column in (820, 560):
        set_knob(page, "column", column)
        title, tools, root = rect(page, "#doc-title"), rect(page, ".page-tools"), rect(page, "#row-root")
        assert root["top"] >= tools["bottom"], (column, tools, root)
        # Like Dynalist's icons, the tools end past the rows, 8px inside the column's edge.
        assert abs(tools["right"] - (rect(page, "main")["right"] - 8)) <= 0.5, column
        assert title["right"] <= root["right"], column
        assert rect(page, ".intro")["top"] >= title["bottom"], column
        assert rect(page, ".page-head")["height"] == head, column
    assert title["height"] > 34, "the long title wraps at the narrowest column"


def expand_all(page, top_level):
    page.focus("#item-1")
    for _ in range(top_level):
        page.keyboard.press(f"{MOD}+Shift+Period")
        page.keyboard.press(f"Alt+{MOD}+ArrowDown")


def test_reflow_320(page, console_errors):
    """WCAG 1.4.10: no sideways scroll at 320px, deepest nesting, every knob at its maximum."""
    page.set_viewport_size({"width": 320, "height": 640})
    page.goto(EXAMPLE.as_uri())
    page.wait_for_function("() => document.documentElement.dataset.outlineReady === 'true'")
    open_panel(page)
    set_knobs(page, MAXES)
    page.keyboard.press("Escape")
    expand_all(page, 7)
    depths = page.evaluate(
        "[...document.querySelectorAll('[role=treeitem]')].map(li => {"
        " let d = 0; for (let e = li; e; e = e.parentElement.closest('[role=treeitem]')) d += 1;"
        " return [d, li.checkVisibility()]; })"
    )
    deepest = max(d for d, _ in depths)
    assert deepest >= 5
    assert all(shown for _, shown in depths), "every item is expanded into view"
    assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")
    # Law M3: the indent step shrinks so the deepest text keeps a 16ch measure.
    narrow = page.evaluate(
        "(() => { const texts = [...document.querySelectorAll('.row .text')].filter((t) => t.checkVisibility());"
        " return texts.flatMap((t) => { const probe = document.createElement('span');"
        " probe.textContent = '0'.repeat(16); probe.style.cssText = 'position:absolute;white-space:nowrap';"
        " t.append(probe); const ch16 = probe.getBoundingClientRect().width; probe.remove();"
        " const w = t.getBoundingClientRect().width;"
        " return w >= ch16 - 0.5 ? [] : [[t.closest('li').dataset.id, w, ch16]]; }); })()"
    )
    assert narrow == []
    open_panel(page)
    assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")
    panel = rect(page, "#spacing")
    assert panel["left"] >= 0 and panel["right"] <= 320
    check_laws(page)


@pytest.mark.parametrize("scheme", SCHEMES)
def test_panel_contrast(panel, scheme):
    page = panel
    page.emulate_media(color_scheme=scheme)
    page.click("#spacing-reset")
    page.wait_for_function("() => document.getElementById('spacing-status').textContent !== ''")
    results = page.evaluate(CONTRAST_JS, PANEL_TEXT)
    assert {r["sel"] for r in results} == set(PANEL_TEXT)
    failures = [f"{r['sel']}: {r['ratio']:.2f} on {r['bg']}" for r in results if r["ratio"] < 4.5]
    assert failures == []
    # Retuned, not inverted: dark raises the surface above the page.
    bg = style(page, "#spacing", "backgroundColor")
    assert bg == {"light": "rgb(255, 255, 255)", "dark": "rgb(36, 36, 36)"}[scheme]
