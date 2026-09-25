"""Selected and idle modes: the active item stays selected until Escape."""

import pytest
from conftest import check_laws
from test_tree_keyboard import AXE_URL, MOD, click_text, click_toggle, focused_id, state, tree  # noqa: F401
from test_visual import (
    ACTIVE,
    BULLET_CONTRAST_JS,
    CONTRAST_JS,
    NARROW,
    PAGE_TEXT,
    SCHEMES,
    WIDE,
    expand_1,
    open_visual,
    settle_math,
)

RING_JS = "id => getComputedStyle(document.querySelector(`#item-${id} > .row`)).outlineStyle"
BG_JS = "id => getComputedStyle(document.querySelector(`#item-${id} > .row`)).backgroundColor"
TRANSPARENT = ("rgba(0, 0, 0, 0)", "transparent")


def full_selection(page):
    return page.evaluate("window.tractatus.selection()")


def selection(page):
    """Mode and active item only."""
    s = full_selection(page)
    return {"mode": s["mode"], "activeId": s["activeId"]}


def mode(page):
    return selection(page)["mode"]


def aria_selected(page):
    return page.evaluate(
        "() => [...document.querySelectorAll('[role=treeitem][aria-selected=true]')]"
        ".map(e => e.dataset.id)"
    )


def blur(page):
    page.evaluate("() => document.activeElement.blur()")
    assert page.evaluate("document.activeElement === document.body")


def test_loads_selected(open_outline, fake_md):
    page = open_outline(fake_md)
    assert mode(page) == "selected"
    assert page.get_attribute("#outline", "data-mode") == "selected"
    assert aria_selected(page) == ["1"]
    assert page.evaluate(BG_JS, "1") not in TRANSPARENT
    check_laws(page)


def test_body_keys_reach_the_tree(open_outline, fake_md):
    """With focus on <body>, navigation keys drive the tree from the active item."""
    page = open_outline(fake_md)
    page.keyboard.press("ArrowDown")
    assert focused_id(page) == "2"
    assert page.evaluate(RING_JS, "2") == "solid"
    blur(page)
    page.keyboard.press("ArrowDown")
    assert focused_id(page) == "3"
    check_laws(page)


def test_margin_click_keeps_focus(tree):
    page = tree
    page.keyboard.press("ArrowDown")
    blur(page)
    page.mouse.click(3, 3)
    assert focused_id(page) == "2"
    assert page.evaluate(RING_JS, "2") == "solid"
    page.click(".page-head", position={"x": 4, "y": 4})    # the header, clear of its buttons
    assert focused_id(page) == "2"
    check_laws(page)


def test_escape_idles_and_arrow_resumes(tree):
    page = tree
    page.keyboard.press("ArrowDown")
    page.keyboard.press("Escape")
    assert selection(page) == {"mode": "idle", "activeId": "2"}
    assert page.get_attribute("#outline", "data-mode") == "idle"
    assert aria_selected(page) == []
    assert page.evaluate(BG_JS, "2") in TRANSPARENT
    assert page.evaluate(RING_JS, "2") == "none"
    assert page.get_attribute("#item-2", "tabindex") == "0"
    check_laws(page)
    page.keyboard.press("Escape")               # idle stays idle
    assert mode(page) == "idle"
    page.keyboard.press("ArrowDown")            # resumes where it was, without moving
    assert selection(page) == {"mode": "selected", "activeId": "2"}
    assert page.evaluate(RING_JS, "2") == "solid"
    check_laws(page)
    page.keyboard.press("ArrowDown")
    assert focused_id(page) == "3"
    check_laws(page)


def test_idle_resumes_from_body(tree):
    """A key on <body> in idle also resumes without moving."""
    page = tree
    page.keyboard.press("Escape")
    blur(page)
    page.keyboard.press("End")
    assert selection(page) == {"mode": "selected", "activeId": "1"}
    assert focused_id(page) == "1"
    check_laws(page)


def test_idle_click_selects_clicked(tree):
    page = tree
    page.keyboard.press("Escape")
    click_text(page, "3")
    assert selection(page) == {"mode": "selected", "activeId": "3"}
    check_laws(page)
    page.keyboard.press("Escape")
    click_text(page, "3")                       # clicking the remembered item selects it too
    assert selection(page) == {"mode": "selected", "activeId": "3"}
    check_laws(page)


def test_idle_toggle_click_selects_its_item(tree):
    page = tree
    page.keyboard.press("Escape")
    click_toggle(page, "2")
    assert state(page)["expanded"] == ["2"]
    assert selection(page) == {"mode": "selected", "activeId": "2"}
    assert focused_id(page) == "2"
    check_laws(page)


def test_idle_tab_in_selects(tree):
    """Tabbing into the tree in idle selects again, so keyboard focus is never invisible."""
    page = tree
    page.keyboard.press("Escape")
    page.focus("#help-button")                  # the header comes just before the tree
    page.keyboard.press("Tab")
    assert focused_id(page) == "1"
    assert mode(page) == "selected"
    check_laws(page)


def test_text_selection_survives(tree):
    """Dragging across text selects it; focus returns to the tree without clearing it."""
    page = tree
    box = page.locator("#item-2 > .row > .text").bounding_box()
    y = box["y"] + 8
    page.mouse.move(box["x"] + 2, y)
    page.mouse.down()
    page.mouse.move(box["x"] + box["width"] * 0.6, y, steps=5)
    page.mouse.up()
    text = page.evaluate("() => String(getSelection())")
    assert len(text) > 5
    assert page.evaluate("() => getSelection().isCollapsed") is False
    check_laws(page)


def test_dialogs_own_escape(tree):
    page = tree
    page.keyboard.press("Shift+Slash")
    assert page.get_attribute("#help", "open") is not None
    page.keyboard.press("Escape")               # closes help; the item stays selected
    assert page.get_attribute("#help", "open") is None
    assert selection(page) == {"mode": "selected", "activeId": "1"}
    page.click("#spacing-button")
    page.focus("#spacing-close")
    page.keyboard.press("ArrowDown")            # not routed to the tree
    assert state(page)["activeId"] == "1"
    page.locator("#spacing").click(position={"x": 4, "y": 4})    # a press inside the panel
    assert page.evaluate("document.getElementById('spacing').contains(document.activeElement)")
    page.keyboard.press("Escape")               # closes the panel; the item stays selected
    assert page.get_attribute("#spacing", "open") is None
    assert mode(page) == "selected"
    check_laws(page)


def test_forced_colors(tree):
    """In forced colours the selected row is outlined, and idle shows nothing."""
    page = tree
    page.emulate_media(forced_colors="active")
    page.keyboard.press("ArrowDown")
    assert page.evaluate(RING_JS, "2") == "solid"
    blur(page)                                  # unfocused, the selection outline still shows
    assert page.evaluate(RING_JS, "2") == "solid"
    page.keyboard.press("ArrowUp")
    page.keyboard.press("Escape")
    assert page.evaluate(RING_JS, "1") == "none"
    assert page.evaluate(RING_JS, "2") == "none"


# ── multi-selection ─────────────────────────────────────


def sel(page):
    """(anchor, focus end) and the sorted selected ids."""
    s = full_selection(page)
    return (s["anchorId"], s["activeId"]), sorted(s["selected"])


def subtree(page, *ids):
    """Ids of the items `ids` and all their descendants, from the DOM."""
    return sorted(
        page.evaluate(
            """ids => ids.flatMap(id => {
              const li = document.getElementById(`item-${id.replaceAll('.', '_')}`);
              return [id, ...[...li.querySelectorAll('[role=treeitem]')].map(e => e.dataset.id)];
            })""",
            list(ids),
        )
    )


def open_1_11(page):
    """Expand 1 and 1.1, then make 1.11 active, by keyboard."""
    for _ in range(4):
        page.keyboard.press("ArrowRight")
    assert focused_id(page) == "1.11"


def test_shift_arrows_extend_and_shrink(tree):
    page = tree
    page.keyboard.press("Shift+ArrowDown")
    assert sel(page) == (("1", "2"), subtree(page, "1", "2"))
    assert focused_id(page) == "2"                   # the focus end is active
    assert page.get_attribute("#item-2", "tabindex") == "0"
    assert page.get_attribute("#item-1_11", "aria-selected") == "true"   # hidden, still selected
    check_laws(page)
    page.keyboard.press("Shift+ArrowDown")
    assert sel(page) == (("1", "3"), subtree(page, "1", "2", "3"))
    page.keyboard.press("Shift+ArrowUp")
    page.keyboard.press("Shift+ArrowUp")             # back to the anchor: a single selection
    assert sel(page) == (("1", "1"), ["1"])
    check_laws(page)
    page.keyboard.press("Shift+ArrowUp")             # past the first top-level item: the root
    assert sel(page) == (("root", "root"), ["root"])
    page.keyboard.press("Shift+ArrowUp")             # nothing holds the root
    assert sel(page) == (("root", "root"), ["root"])
    check_laws(page)
    page.keyboard.press("End")
    page.keyboard.press("Shift+ArrowUp")             # extends upward from a new anchor
    last = focused_id(page)
    assert sel(page)[0][0] != last
    check_laws(page)


def test_extend_promotes_to_parent(tree):
    page = tree
    open_1_11(page)
    page.keyboard.press("Shift+ArrowDown")
    page.keyboard.press("Shift+ArrowDown")
    assert sel(page) == (("1.11", "1.13"), ["1.11", "1.12", "1.13"])
    check_laws(page)
    page.keyboard.press("Shift+ArrowDown")           # past the last sibling: the parent
    assert sel(page) == (("1.1", "1.1"), ["1.1"])
    assert focused_id(page) == "1.1"
    check_laws(page)
    page.keyboard.press("Shift+ArrowDown")           # now among 1.1's siblings
    assert sel(page) == (("1.1", "1.2"), subtree(page, "1.1", "1.2"))
    page.keyboard.press("Shift+ArrowDown")
    assert sel(page) == (("1", "1"), ["1"])
    page.keyboard.press("Shift+ArrowDown")
    assert sel(page) == (("1", "2"), subtree(page, "1", "2"))
    check_laws(page)
    page.keyboard.press("Shift+ArrowUp")             # shrinks, never demotes
    assert sel(page) == (("1", "1"), ["1"])
    assert focused_id(page) == "1"
    page.keyboard.press("Shift+ArrowUp")             # past the first top-level item: the root
    assert sel(page) == (("root", "root"), ["root"])
    check_laws(page)


def test_extend_up_promotes(tree):
    page = tree
    open_1_11(page)
    page.keyboard.press("Shift+ArrowUp")
    assert sel(page) == (("1.1", "1.1"), ["1.1"])
    page.keyboard.press("Shift+ArrowUp")
    assert sel(page) == (("1", "1"), ["1"])
    check_laws(page)


def test_shift_home_end(tree):
    page = tree
    open_1_11(page)
    page.keyboard.press("ArrowDown")                 # 1.12
    page.keyboard.press("Shift+End")
    assert sel(page) == (("1.12", "1.13"), ["1.12", "1.13"])
    page.keyboard.press("Shift+Home")
    assert sel(page) == (("1.12", "1.11"), ["1.11", "1.12"])
    assert focused_id(page) == "1.11"
    page.keyboard.press("Shift+Home")                # already first: nothing
    assert sel(page) == (("1.12", "1.11"), ["1.11", "1.12"])
    check_laws(page)


def test_plain_arrows_collapse_from_focus_end(tree):
    page = tree
    page.keyboard.press("Shift+ArrowDown")
    page.keyboard.press("Shift+ArrowDown")           # 1..3, focus end 3
    page.keyboard.press("ArrowDown")
    assert sel(page) == (("4", "4"), ["4"])
    page.keyboard.press("Shift+ArrowUp")
    page.keyboard.press("Shift+ArrowUp")             # 2..4, focus end 2
    page.keyboard.press("ArrowUp")
    assert sel(page) == (("1", "1"), ["1"])
    check_laws(page)
    page.keyboard.press("Shift+ArrowDown")
    page.keyboard.press("Home")                      # to the root, from a range
    assert sel(page) == (("root", "root"), ["root"])
    page.keyboard.press("ArrowDown")
    page.keyboard.press("ArrowDown")
    page.keyboard.press("Shift+ArrowUp")             # 2..1, focus end 1
    page.keyboard.press(f"Alt+{MOD}+ArrowUp")        # a key that does nothing still collapses
    assert sel(page) == (("1", "1"), ["1"])
    page.keyboard.press("Shift+ArrowDown")
    page.keyboard.press("ArrowUp")                   # focus end 2, up to 1
    assert sel(page) == (("1", "1"), ["1"])
    check_laws(page)


def test_escape_collapses_then_idles(tree):
    page = tree
    page.keyboard.press("Shift+ArrowDown")
    page.keyboard.press("Shift+ArrowDown")
    page.keyboard.press("Escape")
    assert sel(page) == (("3", "3"), ["3"])
    assert mode(page) == "selected"
    check_laws(page)
    page.keyboard.press("Escape")
    assert mode(page) == "idle"
    assert sel(page) == (("3", "3"), [])
    check_laws(page)
    page.keyboard.press("Shift+ArrowDown")           # resumes, single, without moving
    assert sel(page) == (("3", "3"), ["3"])
    check_laws(page)


def test_clicks(tree):
    page = tree
    page.keyboard.press("Shift+ArrowDown")
    click_text(page, "3")                            # a plain click collapses to it
    assert sel(page) == (("3", "3"), ["3"])
    page.click("#item-1 > .row > .text", modifiers=["Shift"])
    assert sel(page) == (("3", "1"), subtree(page, "1", "2", "3"))
    assert focused_id(page) == "1"
    assert page.evaluate("() => getSelection().isCollapsed")   # no text was selected
    check_laws(page)
    open_1_11(page)                                  # plain keys collapse; 1.11 is active
    page.click("#item-1_13 > .row > .text", modifiers=["Shift"])
    assert sel(page) == (("1.11", "1.13"), ["1.11", "1.12", "1.13"])
    page.keyboard.press("ArrowDown")
    page.keyboard.press("ArrowRight")
    page.keyboard.press("ArrowRight")                # 1.21
    assert focused_id(page) == "1.21"
    click_text(page, "1.11")
    page.click("#item-1_21 > .row > .text", modifiers=["Shift"])   # cousins: their parents
    assert sel(page) == (("1.1", "1.2"), subtree(page, "1.1", "1.2"))
    check_laws(page)
    page.click("#item-1 > .row > .text", modifiers=["Shift"])      # an ancestor of the anchor
    assert sel(page) == (("1", "1"), ["1"])
    click_text(page, "1.1")
    page.click("#item-1_12 > .row > .text", modifiers=["Shift"])   # a descendant of the anchor
    assert sel(page) == (("1.1", "1.1"), ["1.1"])
    click_text(page, "2")
    page.keyboard.press("Escape")
    page.click("#item-4 > .row > .text", modifiers=["Shift"])      # idle: from the remembered item
    assert sel(page) == (("2", "4"), subtree(page, "2", "3", "4"))
    assert mode(page) == "selected"
    check_laws(page)


def test_left_and_collapse_in_a_range(tree):
    page = tree
    open_1_11(page)
    page.keyboard.press("Shift+ArrowDown")
    page.keyboard.press("Shift+ArrowDown")
    page.keyboard.press("ArrowLeft")                 # collapse to 1.13, then go to its parent
    assert sel(page) == (("1.1", "1.1"), ["1.1"])
    check_laws(page)
    page.keyboard.press("ArrowRight")
    page.keyboard.press("Shift+ArrowDown")
    page.keyboard.press("Shift+ArrowDown")
    assert sel(page)[0] == ("1.11", "1.13")
    click_toggle(page, "2")                          # elsewhere: selects 2 alone
    assert sel(page)[0] == ("2", "2")
    assert focused_id(page) == "2"
    check_laws(page)
    click_toggle(page, "2")
    click_text(page, "1.11")
    page.keyboard.press("Shift+ArrowDown")
    click_toggle(page, "1.1")                        # the range's parent: selects and collapses it
    assert sel(page) == (("1.1", "1.1"), ["1.1"])
    assert "1.1" not in state(page)["expanded"]
    assert focused_id(page) == "1.1"
    check_laws(page)
    page.keyboard.press("Shift+ArrowDown")
    page.keyboard.press(f"{MOD}+Period")             # collapses the range, then toggles 1.2
    assert sel(page) == (("1.2", "1.2"), ["1.2"])
    assert "1.2" in state(page)["expanded"]
    check_laws(page)


# ── copy ────────────────────────────────────────────────

COPY_JS = """() => {
  const data = new DataTransfer();
  const e = new ClipboardEvent("copy", { clipboardData: data, bubbles: true, cancelable: true });
  document.activeElement.dispatchEvent(e);
  return { text: data.getData("text/plain"), prevented: e.defaultPrevented };
}"""

# Parse the copied text back and compare it with the selected items' subtrees.
ROUNDTRIP_JS = """text => {
  const strip = (n) => ({ label: n.label, text: n.text, children: n.children.map(strip) });
  const parsed = window.tractatus.parseOutline(text);
  const whole = window.tractatus.parseOutline(window.tractatus.source);
  const find = (nodes, id) => {
    for (const n of nodes) { if (n.id === id) return n; const f = find(n.children, id); if (f) return f; }
    return null;
  };
  const on = (li) => li?.getAttribute("aria-selected") === "true";
  const roots = [...document.querySelectorAll('[role=treeitem][aria-selected=true]')]
    .filter((li) => !on(li.parentElement.closest('[role=treeitem]'))).map((li) => li.dataset.id);
  return { copied: parsed.items.map(strip), expected: roots.map((id) => strip(find(whole.items, id))),
           warnings: parsed.warnings };
}"""

COPY_MD = """\
# Copy

- 1 First has **bold**, `code` and a [link](https://example.org/).

  A note on first, with *em*.
  - 1.1 Child
    - 1.1.1 Grandchild
  - \\2024 was a year, unlabelled.
- 2 Second
- 3 Third
"""


def copy(page):
    return page.evaluate(COPY_JS)


def test_copy_single_item(open_outline):
    page = open_outline(COPY_MD)
    out = copy(page)
    assert out["prevented"]
    assert out["text"] == (
        "- 1 First has **bold**, `code` and a [link](https://example.org/).\n"
        "\n"
        "  A note on first, with *em*.\n"
        "  - 1.1 Child\n"
        "    - 1.1.1 Grandchild\n"
        "  - \\2024 was a year, unlabelled.\n"
    )
    rt = page.evaluate(ROUNDTRIP_JS, out["text"])
    assert rt["copied"] == rt["expected"]
    assert rt["warnings"] == []


def test_copy_sibling_range(open_outline):
    page = open_outline(COPY_MD)
    page.keyboard.press("ArrowRight")
    page.keyboard.press("ArrowRight")                # 1.1
    page.keyboard.press("Shift+ArrowDown")
    out = copy(page)
    assert out["text"] == "- 1.1 Child\n  - 1.1.1 Grandchild\n- \\2024 was a year, unlabelled.\n"
    page.keyboard.press("Shift+ArrowDown")           # promoted to 1
    page.keyboard.press("Shift+ArrowDown")           # 1..2
    out = copy(page)
    assert out["text"].startswith("- 1 First")
    assert out["text"].endswith("- 2 Second\n")
    rt = page.evaluate(ROUNDTRIP_JS, out["text"])
    assert [n["label"] for n in rt["copied"]] == ["1", "2"]
    assert rt["copied"] == rt["expected"]


def test_copy_promoted_range(tree):
    """A range promoted twice copies whole top-level subtrees, nested from column 0."""
    page = tree
    open_1_11(page)
    for _ in range(6):                               # 1.11..1.13, 1.1, 1.1..1.2, 1, 1..2
        page.keyboard.press("Shift+ArrowDown")
    assert sel(page)[0] == ("1", "2")
    out = copy(page)
    assert out["prevented"]
    lines = out["text"].splitlines()
    assert lines[0].startswith("- 1 The library is everything")
    assert "  - 1.1 The library is the totality of volumes, not of pages." in lines
    assert "    - 1.12 For the totality of volumes determines what is shelved, and also what is lent out." in lines
    assert any(line.startswith("- 2 What is shelved") for line in lines)
    assert any(line.startswith("        - 2.01231 ") for line in lines)   # collapsed, still copied
    assert not any(line.startswith("- 3") for line in lines)
    rt = page.evaluate(ROUNDTRIP_JS, out["text"])
    assert rt["copied"] == rt["expected"]


def test_copy_leaves_text_selection_and_idle_alone(tree):
    page = tree
    box = page.locator("#item-2 > .row > .text").bounding_box()
    page.mouse.move(box["x"] + 2, box["y"] + 8)
    page.mouse.down()
    page.mouse.move(box["x"] + box["width"] * 0.6, box["y"] + 8, steps=5)
    page.mouse.up()
    assert copy(page)["prevented"] is False          # native copy of the dragged text
    click_text(page, "3")
    page.keyboard.press("Escape")
    assert copy(page)["prevented"] is False          # idle: nothing selected to copy
    page.keyboard.press("ArrowDown")
    assert copy(page)["prevented"] is True


def test_copy_shortcut_fires(tree):
    """The real shortcut reaches the handler (headless Chromium fires copy for ⌘C/Ctrl+C)."""
    page = tree
    page.evaluate("""() => { window.__copies = [];
      addEventListener("copy", (e) => window.__copies.push(e.defaultPrevented)); }""")
    page.keyboard.press(f"{MOD}+c")
    assert page.evaluate("window.__copies") == [True]


# ── isolation, contrast, accessibility ──────────────────


def test_spacing_panel_isolation(tree):
    page = tree
    page.keyboard.press("Shift+ArrowDown")
    before = full_selection(page)
    page.click("#spacing-button")
    page.focus("#spacing-itemGap")
    for key in ("Shift+ArrowDown", "Shift+ArrowUp", "Shift+End", "Escape"):
        if page.get_attribute("#spacing", "open") is None:
            break
        page.keyboard.press(key)
        assert full_selection(page) == before, key
    assert page.get_attribute("#spacing", "open") is None   # Escape closed the panel only
    assert full_selection(page) == before
    check_laws(page)


def promoted_visual_range(page):
    """VISUAL_MD with 1 and 1.2 expanded and the range promoted to 1..2."""
    expand_1(page)
    page.keyboard.press("ArrowRight")                # 1.1
    page.keyboard.press("ArrowDown")
    page.keyboard.press("ArrowRight")                # expand 1.2
    page.keyboard.press("ArrowUp")                   # 1.1
    for _ in range(3):                               # 1.1..1.2, 1, 1..2
        page.keyboard.press("Shift+ArrowDown")
    assert sel(page) == (("1", "2"), ["1", "1.1", "1.2", "1.2.1", "2"])
    settle_math(page)


@pytest.mark.parametrize("scheme", SCHEMES)
@pytest.mark.parametrize("viewport", [WIDE, NARROW], ids=["wide", "narrow"])
def test_range_contrast(open_outline, page, scheme, viewport):
    """Law V holds on every highlighted row of a promoted range."""
    page.set_viewport_size(viewport)
    open_visual(open_outline, page, scheme)
    promoted_visual_range(page)
    results = page.evaluate(CONTRAST_JS, PAGE_TEXT)
    on_active = {r["sel"] for r in results if r["bg"] == ACTIVE[scheme]}
    assert {".row .para", ".row a"} <= on_active
    # Code and math paint their own background; the only row holding them, 1.1, is selected.
    assert {".row code", ".row .math"} <= {r["sel"] for r in results}
    if viewport is NARROW:
        assert ".label" in on_active                 # inline labels sit on the highlight
    failures = [f"{r['sel']}: {r['ratio']:.2f} {r['html']}" for r in results if r["ratio"] < 4.5]
    assert failures == []
    bullets = page.evaluate(BULLET_CONTRAST_JS)
    assert [r for r in bullets if r["ratio"] < 3.0] == []
    check_laws(page)


@pytest.mark.network
def test_range_axe(open_outline, page):
    open_visual(open_outline, page)
    promoted_visual_range(page)
    page.add_script_tag(content=page.request.get(AXE_URL).text())
    for scheme in SCHEMES:
        page.emulate_media(color_scheme=scheme)
        result = page.evaluate("async () => (await axe.run(document)).violations")
        serious = [(v["id"], [n["target"] for n in v["nodes"]]) for v in result
                   if v["impact"] in ("serious", "critical")]
        assert serious == [], scheme


def test_range_fills_subtree_block(tree):
    """A range paints each selected subtree as one block; a single selection only its row."""
    page = tree
    li_bg = "id => getComputedStyle(document.getElementById(`item-${id}`)).backgroundColor"
    page.keyboard.press("ArrowRight")                # expand 1: a single selection
    assert page.evaluate(li_bg, "1") in TRANSPARENT
    assert page.evaluate(BG_JS, "1_1") in TRANSPARENT
    page.keyboard.press("Shift+ArrowDown")           # 1..2
    assert page.evaluate(li_bg, "1") not in TRANSPARENT
    assert page.evaluate(BG_JS, "1_1") not in TRANSPARENT
    page.keyboard.press("Escape")
    assert page.evaluate(li_bg, "1") in TRANSPARENT
    check_laws(page)
