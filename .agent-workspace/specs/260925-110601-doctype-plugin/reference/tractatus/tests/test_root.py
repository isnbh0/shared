"""The document title is the tree's root item: selectable, always open, the parent of the top level."""

import pytest
from conftest import check_laws
from test_selection import BG_JS, COPY_JS, COPY_MD, RING_JS, TRANSPARENT, blur, full_selection, mode, sel
from test_tree_keyboard import AXE_URL, MOD, click_text, focused_id, state, visible_ids
from test_visual import ACTIVE, CONTRAST_JS, SCHEMES, TITLE_INSET, rect

TOP_LEVEL = ["1", "2", "3", "4", "5", "6", "7", "p-8"]
TOP_PARENTS = ["1", "2", "3", "4", "5", "6"]


@pytest.fixture
def root(open_outline, fake_md):
    """The fixture page with the root selected by Home."""
    page = open_outline(fake_md)
    page.keyboard.press("Home")
    assert focused_id(page) == "root"
    return page


def all_parents(page):
    return sorted(page.evaluate(
        "[...document.querySelectorAll('[role=treeitem][aria-expanded]:not(#item-root)')].map(e => e.dataset.id)"
    ))


# ── structure and ARIA ──────────────────────────────────


def test_root_structure(open_outline, fake_md):
    page = open_outline(fake_md)
    tops = page.evaluate(
        "[...document.querySelectorAll('#outline > [role=treeitem]')].map(e => e.id)"
    )
    assert tops == ["item-root"]
    assert page.get_attribute("#item-root", "aria-expanded") == "true"
    assert page.get_attribute("#item-root", "aria-labelledby") == "doc-title"
    assert page.get_attribute("#item-root", "aria-describedby") == "intro"
    assert page.locator("#item-root > .row > .toggle").count() == 0
    # A real <h1> stays, inside the root's row; the top level is the root's group.
    assert page.get_by_role("heading", level=1).count() == 1
    assert page.locator("#item-root > .row > h1#doc-title").count() == 1
    assert page.get_by_role("treeitem", name="Tractatus Bibliothecarius", exact=True).count() == 1
    top = page.evaluate(
        "[...document.querySelectorAll('#item-root > [role=group] > [role=treeitem]')].map(e => e.dataset.id)"
    )
    assert top == TOP_LEVEL
    # The page tools are in the header, outside the tree.
    assert page.evaluate(
        "[...document.querySelectorAll('.page-tools button')].every(b =>"
        " b.closest('header') && !document.getElementById('outline').contains(b))"
    )
    # Intro links are tree content: no Tab stops.
    assert page.evaluate(
        "[...document.querySelectorAll('.intro a')].every(a => a.getAttribute('tabindex') === '-1')"
    )
    check_laws(page)


def test_load_keeps_first_item(open_outline, fake_md):
    page = open_outline(fake_md)
    assert state(page) == {"expanded": [], "activeId": "1"}
    assert page.get_attribute("#item-root", "tabindex") == "-1"
    assert page.get_attribute("#item-root", "aria-selected") == "false"
    assert page.evaluate(BG_JS, "root") in TRANSPARENT
    check_laws(page)


def test_root_selected_and_idle(root):
    page = root
    assert page.get_attribute("#item-root", "tabindex") == "0"
    assert page.get_attribute("#item-root", "aria-selected") == "true"
    assert page.evaluate(BG_JS, "root") not in TRANSPARENT
    assert page.evaluate(RING_JS, "root") == "solid"
    check_laws(page)
    page.keyboard.press("Escape")
    assert mode(page) == "idle"
    assert page.get_attribute("#item-root", "aria-selected") == "false"
    assert page.evaluate(BG_JS, "root") in TRANSPARENT
    assert page.evaluate(RING_JS, "root") == "none"
    check_laws(page)
    page.keyboard.press("ArrowDown")                 # resumes on the root without moving
    assert sel(page) == (("root", "root"), ["root"])
    check_laws(page)


# ── keys ────────────────────────────────────────────────


def test_up_and_down(open_outline, fake_md):
    page = open_outline(fake_md)
    page.keyboard.press("ArrowUp")
    assert focused_id(page) == "root"
    page.keyboard.press("ArrowUp")                   # nothing above the root
    assert focused_id(page) == "root"
    page.keyboard.press("ArrowDown")
    assert focused_id(page) == "1"
    page.keyboard.press("End")
    assert focused_id(page) == "p-8"
    page.keyboard.press("Home")
    assert focused_id(page) == "root"
    check_laws(page)


def test_right_and_left(root):
    page = root
    page.keyboard.press("ArrowLeft")                 # the root never collapses
    assert state(page) == {"expanded": [], "activeId": "root"}
    assert page.get_attribute("#item-root", "aria-expanded") == "true"
    page.keyboard.press("ArrowRight")                # always open: to the first child
    assert focused_id(page) == "1"
    assert state(page)["expanded"] == []
    page.keyboard.press("ArrowLeft")                 # a collapsed top-level item: to its parent
    assert focused_id(page) == "root"
    check_laws(page)


def test_toggle_top_level(root):
    page = root
    page.keyboard.press(f"{MOD}+Period")             # none open: open the top level
    assert state(page)["expanded"] == TOP_PARENTS
    assert focused_id(page) == "root"
    check_laws(page)
    page.keyboard.press(f"{MOD}+Period")             # some open: close the top level
    assert state(page)["expanded"] == []
    assert visible_ids(page) == ["root", *TOP_LEVEL]
    check_laws(page)
    # One open top-level item is enough to close; deeper expansion is kept, as for any collapse.
    click_text(page, "2")
    page.keyboard.press("ArrowRight")
    page.keyboard.press("ArrowRight")
    page.keyboard.press("ArrowRight")                # 2.01 expanded
    page.keyboard.press("Home")
    page.keyboard.press(f"{MOD}+Period")
    assert state(page)["expanded"] == ["2.01"]
    assert visible_ids(page) == ["root", *TOP_LEVEL]
    check_laws(page)


def test_toggle_whole_outline(root):
    page = root
    page.keyboard.press(f"{MOD}+Shift+Period")       # nothing open: open everything
    assert state(page)["expanded"] == all_parents(page)
    assert len(visible_ids(page)) == 48
    assert focused_id(page) == "root"
    check_laws(page)
    page.keyboard.press(f"{MOD}+Shift+Period")       # open: close everything
    assert state(page)["expanded"] == []
    assert visible_ids(page) == ["root", *TOP_LEVEL]
    check_laws(page)
    page.keyboard.press("ArrowDown")
    page.keyboard.press("ArrowRight")                # 1 open
    page.keyboard.press("Home")
    page.keyboard.press(f"{MOD}+Shift+Period")       # any open top-level item counts as open
    assert state(page)["expanded"] == []
    check_laws(page)


def test_star_expands_top_level(root):
    page = root
    page.keyboard.press("Shift+Digit8")
    assert state(page)["expanded"] == TOP_PARENTS
    assert focused_id(page) == "root"
    check_laws(page)


def test_sibling_keys_on_root(root):
    page = root
    for key in (f"Alt+{MOD}+ArrowUp", f"Alt+{MOD}+ArrowDown", "Shift+Home", "Shift+End",
                "Shift+ArrowUp", "Shift+ArrowDown"):
        page.keyboard.press(key)
        assert sel(page) == (("root", "root"), ["root"]), key
    check_laws(page)


def test_header_buttons_route_to_root(root):
    page = root
    page.keyboard.press("ArrowDown")
    page.focus("#help-button")
    page.keyboard.press("Home")
    assert focused_id(page) == "root"
    page.focus("#spacing-button")
    page.keyboard.press(f"{MOD}+Period")
    assert state(page)["expanded"] == TOP_PARENTS
    check_laws(page)


# ── ranges ──────────────────────────────────────────────


def test_extend_promotes_to_root(open_outline, fake_md):
    page = open_outline(fake_md)
    page.keyboard.press("Shift+ArrowDown")           # 1..2
    page.keyboard.press("Shift+ArrowUp")
    page.keyboard.press("Shift+ArrowUp")             # past the first top-level item
    assert sel(page) == (("root", "root"), ["root"])
    assert focused_id(page) == "root"
    check_laws(page)
    page.keyboard.press("End")
    page.keyboard.press("Shift+ArrowDown")           # past the last top-level item
    assert sel(page) == (("root", "root"), ["root"])
    check_laws(page)


def test_title_clicks(open_outline, fake_md):
    page = open_outline(fake_md)
    page.keyboard.press("ArrowDown")
    page.keyboard.press("ArrowDown")
    page.click("#doc-title", modifiers=["Shift"])    # from 3: the root holds it
    assert sel(page) == (("root", "root"), ["root"])
    assert page.evaluate("() => getSelection().isCollapsed")
    check_laws(page)
    click_text(page, "2")
    page.click("#item-4 > .row > .text", modifiers=["Shift"])
    assert sel(page)[0] == ("2", "4")
    page.click("#doc-title")                         # a plain click selects the root alone
    assert sel(page) == (("root", "root"), ["root"])
    assert focused_id(page) == "root"
    check_laws(page)
    page.click(".intro p")                           # the root's note is part of its row
    assert focused_id(page) == "root"
    click_text(page, "3")
    page.keyboard.press("Escape")
    page.click("#doc-title")                         # idle: the click selects
    assert sel(page) == (("root", "root"), ["root"])
    assert mode(page) == "selected"
    check_laws(page)


def test_title_text_selection_survives(open_outline, fake_md):
    page = open_outline(fake_md)
    box = page.locator("#doc-title").bounding_box()
    y = box["y"] + box["height"] / 2
    page.mouse.move(box["x"] + 2, y)
    page.mouse.down()
    page.mouse.move(box["x"] + box["width"] * 0.6, y, steps=5)
    page.mouse.up()
    assert len(page.evaluate("() => String(getSelection())")) > 5
    assert page.evaluate("() => getSelection().isCollapsed") is False
    assert page.evaluate(COPY_JS)["prevented"] is False   # a text selection copies natively
    check_laws(page)


# ── copy ────────────────────────────────────────────────

WHOLE_JS = """text => {
  const strip = (n) => ({ label: n.label, text: n.text, children: n.children.map(strip) });
  const doc = (d) => ({ title: d.title, intro: d.intro, items: d.items.map(strip) });
  const copied = window.tractatus.parseOutline(text);
  return { copied: doc(copied), source: doc(window.tractatus.parseOutline(window.tractatus.source)),
           warnings: copied.warnings };
}"""


def copy_root(page):
    page.keyboard.press("Home")
    assert sel(page) == (("root", "root"), ["root"])
    out = page.evaluate(COPY_JS)
    assert out["prevented"]
    return out["text"]


def test_copy_whole_document(open_outline):
    page = open_outline("# Copy *me*\n\nAn intro with a [link](#2).\n\nA second intro paragraph.\n\n" + COPY_MD.split("\n\n", 1)[1])
    text = copy_root(page)
    assert text.startswith("# Copy *me*\n\nAn intro with a [link](#2).\n\nA second intro paragraph.\n\n- 1 First")
    assert text.endswith("- 3 Third\n")
    rt = page.evaluate(WHOLE_JS, text)
    assert rt["copied"] == rt["source"]
    assert rt["warnings"] == []


def test_copy_whole_fixture(open_outline, fake_md):
    """Collapsed items are copied too: the whole fixture round-trips."""
    page = open_outline(fake_md)
    text = copy_root(page)
    assert text.startswith("# Tractatus Bibliothecarius\n\nA synthetic outline")
    rt = page.evaluate(WHOLE_JS, text)
    assert rt["copied"] == rt["source"]


@pytest.mark.parametrize(
    ("md", "want"),
    [
        ("- 1 One\n  - 1.1 Sub\n", "- 1 One\n  - 1.1 Sub\n"),          # no title: no heading
        ("Just an intro.\n\n- 1 One\n", "Just an intro.\n\n- 1 One\n"),
        ("# Only a title\n", "# Only a title\n"),
        ("", ""),
    ],
    ids=["untitled", "intro-only", "title-only", "empty"],
)
def test_copy_whole_edge_cases(open_outline, md, want):
    page = open_outline(md)
    text = copy_root(page)
    assert text == want
    rt = page.evaluate(WHOLE_JS, text)
    assert rt["copied"] == rt["source"]


def test_copy_shortcut_on_root(root):
    page = root
    page.evaluate("""() => { window.__copies = [];
      addEventListener("copy", (e) => window.__copies.push(e.defaultPrevented)); }""")
    page.keyboard.press(f"{MOD}+c")
    assert page.evaluate("window.__copies") == [True]


# ── links ───────────────────────────────────────────────


def test_deep_links_unchanged(open_outline, fake_md):
    page = open_outline(fake_md, "#2.0121")
    assert focused_id(page) == "2.0121"
    assert state(page)["expanded"] == ["2", "2.01", "2.012"]
    check_laws(page)


def test_root_fragment(open_outline, fake_md):
    """#root selects the title, like any item id."""
    page = open_outline(fake_md, "#root")
    assert focused_id(page) == "root"
    assert page.text_content("#status") == ""
    check_laws(page)


def test_empty_document_root(open_outline):
    page = open_outline("# Nothing yet\n\nNo items.\n")
    assert state(page) == {"expanded": [], "activeId": "root"}
    assert page.get_attribute("#item-root", "aria-expanded") is None
    assert page.is_visible(".empty")
    for key in ("ArrowDown", "ArrowRight", f"{MOD}+Period", f"{MOD}+Shift+Period", "Shift+Digit8", "End"):
        page.keyboard.press(key)
        assert state(page) == {"expanded": [], "activeId": "root"}, key
    check_laws(page)


# ── look ────────────────────────────────────────────────


@pytest.mark.parametrize("scheme", SCHEMES)
def test_root_contrast(open_outline, fake_md, page, scheme):
    """Law V on the selected root row: title, intro and intro code and links."""
    page.emulate_media(color_scheme=scheme)
    page = open_outline(fake_md)
    page.keyboard.press("Home")
    assert page.evaluate(BG_JS, "root") == ACTIVE[scheme]
    results = page.evaluate(CONTRAST_JS, ["#doc-title", ".intro p", ".intro code", ".intro a"])
    assert {r["sel"] for r in results} >= {"#doc-title", ".intro p"}
    assert all(r["bg"] == ACTIVE[scheme] for r in results if r["sel"] in ("#doc-title", ".intro p"))
    failures = [f"{r['sel']}: {r['ratio']:.2f}" for r in results if r["ratio"] < 4.5]
    assert failures == []


def test_root_row_geometry(root):
    """The title's text starts where the rows do, as Dynalist's does; the highlight starts
    TITLE_INSET before them, so the ring stays clear of the title."""
    page = root
    row, outline = rect(page, "#row-root"), rect(page, "#outline")
    title = rect(page, "#doc-title")
    one = rect(page, "#item-1 > .row")
    assert abs(row["left"] - (one["left"] - TITLE_INSET)) <= 0.5
    assert abs(row["right"] - one["right"]) <= 0.5
    assert abs(title["left"] - outline["left"]) <= 0.5
    assert title["left"] - row["left"] >= 4                    # the 2px ring is inset 2px
    assert title["top"] - row["top"] >= 4
    assert row["bottom"] <= one["top"]                         # no overlap with the first row
    assert page.evaluate(
        "getComputedStyle(document.getElementById('doc-title')).fontSize"
    ) == "28px"


def test_root_forced_colors(root):
    page = root
    page.emulate_media(forced_colors="active")
    assert page.evaluate(RING_JS, "root") == "solid"
    blur(page)
    assert page.evaluate(RING_JS, "root") == "solid"            # the selection outline
    page.keyboard.press("Escape")
    assert page.evaluate(RING_JS, "root") == "none"


@pytest.mark.network
def test_root_axe(root):
    page = root
    page.add_script_tag(content=page.request.get(AXE_URL).text())
    for scheme in SCHEMES:
        page.emulate_media(color_scheme=scheme)
        page.keyboard.press("Home")
        assert full_selection(page)["selected"] == ["root"]
        for label in ("root selected", "root expanded"):
            result = page.evaluate("async () => (await axe.run(document)).violations")
            serious = [(v["id"], [n["target"] for n in v["nodes"]]) for v in result
                       if v["impact"] in ("serious", "critical")]
            assert serious == [], (scheme, label)
            if label == "root selected":
                page.keyboard.press(f"{MOD}+Shift+Period")
        page.keyboard.press(f"{MOD}+Shift+Period")
        check_laws(page)
