"""Phase 2: state, projection, keyboard (laws S and D)."""

import random
import re

import pytest
from conftest import LAWS_JS, check_laws

MOD = "ControlOrMeta"
# Playwright sends "Shift+8" as key "8"; "Shift+Digit8" sends key "*", as a US keyboard does.
AXE_URL = "https://cdn.jsdelivr.net/npm/axe-core@4.10.2/axe.min.js"
HELP_STRINGS = [
    "Previous item",
    "Next item",
    "Expand, or go to first child",
    "Collapse, or go to parent",
    "First item: the title",
    "Last item",
    "Expand all siblings; on the title, the top level",
    "Expand/collapse; on the title, the top level",
    "Expand/collapse all descendants; on the title, the whole outline",
    "Previous sibling",
    "Next sibling",
    "Select the previous item too; past the first, its parent",
    "Select the next item too; past the last, its parent",
    "Select to the first sibling",
    "Select to the last sibling",
    "Select from the selected item to here",
    "Copy the selected items as a markdown list; the title copies the whole document",
    "Clear the filter, then the selection; any arrow key selects again",
    "Expand to that many levels below the selected item; on the title, the whole outline",
    "Copy a link to the selected item; the title links to the whole document",
    "Zoom in: show the selected item as the page",
    "Zoom out one level",
    "On a bullet: zoom in",
    "On a link to an item: zoom into it",
    "Find: filter the outline; in the box, press again for the browser's find",
    "While finding: keep the selected item and clear the filter",
    "Show this help",
]
VISIBLE_JS = (
    "[...document.querySelectorAll('[role=treeitem]')]"
    ".filter(e => e.checkVisibility()).map(e => e.dataset.id)"
)
VISIBLE_PARENTS_JS = (   # items with a toggle: the root has none
    "[...document.querySelectorAll('[role=treeitem][aria-expanded]:not(#item-root)')]"
    ".filter(e => e.checkVisibility()).map(e => e.dataset.id)"
)


def focused_id(page):
    return page.evaluate("document.activeElement.dataset.id")


def css(id):
    return id.replace(".", "_")


def state(page):
    return page.evaluate("window.tractatus.state()")


def visible_ids(page):
    return page.evaluate(VISIBLE_JS)


def text_sel(id):
    """The clickable text of an item's row: the title for the root."""
    return "#doc-title" if id == "root" else f"#item-{css(id)} > .row > .text"


def click_text(page, id):
    # At the start of the text: a centre click could land on an item link, which zooms.
    page.click(text_sel(id), position={"x": 4, "y": 4})


def click_toggle(page, id):
    page.click(f"#item-{css(id)} > .row > .toggle")


@pytest.fixture
def tree(open_outline, fake_md):
    """The fixture page with item 1 focused by a click."""
    page = open_outline(fake_md)
    click_text(page, "1")
    assert focused_id(page) == "1"
    return page


def open_2_011(page):
    """Expand 2 and 2.01, then focus 2.011, by keyboard."""
    click_text(page, "2")
    for _ in range(4):
        page.keyboard.press("ArrowRight")
    assert state(page)["expanded"] == ["2", "2.01"]
    assert focused_id(page) == "2.011"


def test_tree_roles(tree):
    page = tree
    assert page.locator("#outline[role=tree]").count() == 1
    assert page.locator("[role=treeitem]").count() == 48          # 47 items and the root
    groups = page.evaluate(
        "[...document.querySelectorAll('[role=group]')]"
        ".map(g => g.parentElement.getAttribute('role'))"
    )
    assert groups and all(r == "treeitem" for r in groups)
    assert page.get_by_role("treeitem", name=re.compile("^2 What is shelved")).count() == 1
    check_laws(page)


def test_initial_state(open_outline, fake_md):
    page = open_outline(fake_md)
    assert state(page) == {"expanded": [], "activeId": "1"}
    assert visible_ids(page) == ["root", "1", "2", "3", "4", "5", "6", "7", "p-8"]
    assert page.get_attribute("#item-1", "aria-expanded") == "false"
    # The collapsed ring is the toggle's ::after; the text bullet and count pill are gone.
    ring = "getComputedStyle(document.querySelector('#item-1 > .row > .toggle'), '::after').display"
    assert page.evaluate(ring) == "block"
    assert page.evaluate("document.querySelectorAll('#outline .bullet, #outline .count').length") == 0
    check_laws(page)


def test_arrow_navigation(tree):
    page = tree
    page.keyboard.press("ArrowDown")
    page.keyboard.press("ArrowDown")
    assert focused_id(page) == "3"
    page.keyboard.press("End")
    assert focused_id(page) == "p-8"
    page.keyboard.press("Home")
    assert focused_id(page) == "root"
    page.keyboard.press("ArrowUp")
    assert focused_id(page) == "root"
    page.keyboard.press("ArrowDown")
    assert focused_id(page) == "1"
    check_laws(page)


def test_right_left(tree):
    page = tree
    page.keyboard.press("ArrowRight")
    assert state(page)["expanded"] == ["1"]
    assert focused_id(page) == "1"
    assert page.is_visible("#item-1_1")
    page.keyboard.press("ArrowRight")
    assert focused_id(page) == "1.1"
    check_laws(page)
    page.keyboard.press("ArrowLeft")
    assert focused_id(page) == "1"
    assert state(page)["expanded"] == ["1"]
    page.keyboard.press("ArrowLeft")
    assert state(page)["expanded"] == []
    assert focused_id(page) == "1"
    check_laws(page)


def test_toggle_chords(tree):
    page = tree
    click_text(page, "2")
    page.keyboard.press(f"{MOD}+Period")
    assert state(page)["expanded"] == ["2"]
    page.keyboard.press(f"{MOD}+Shift+Period")
    assert state(page)["expanded"] == []
    page.keyboard.press(f"{MOD}+Shift+Period")
    assert state(page)["expanded"] == sorted(
        ["2", "2.01", "2.012", "2.0123", "2.02", "2.1"]
    )
    assert page.is_visible("#item-2_01231")
    assert focused_id(page) == "2"
    check_laws(page)


def test_expand_siblings(tree):
    page = tree
    page.keyboard.press("Shift+Digit8")
    assert state(page)["expanded"] == ["1", "2", "3", "4", "5", "6"]
    assert focused_id(page) == "1"
    check_laws(page)


def test_sibling_jump(tree):
    page = tree
    open_2_011(page)
    page.keyboard.press(f"Alt+{MOD}+ArrowDown")
    assert focused_id(page) == "2.012"
    page.keyboard.press("ArrowRight")
    assert "2.012" in state(page)["expanded"]
    assert focused_id(page) == "2.012"
    page.keyboard.press(f"Alt+{MOD}+ArrowDown")
    assert focused_id(page) == "2.013"
    page.keyboard.press(f"Alt+{MOD}+ArrowUp")
    assert focused_id(page) == "2.012"
    page.keyboard.press(f"Alt+{MOD}+ArrowDown")
    page.keyboard.press(f"Alt+{MOD}+ArrowDown")
    assert focused_id(page) == "2.013"
    check_laws(page)


def test_mouse_toggle(tree):
    """A bullet click selects and focuses its item as well as toggling it."""
    page = tree
    click_toggle(page, "4")
    assert "4" in state(page)["expanded"]
    assert state(page)["activeId"] == "4"
    assert focused_id(page) == "4"
    check_laws(page)
    click_toggle(page, "4")
    assert "4" not in state(page)["expanded"]
    click_text(page, "7")
    assert state(page)["activeId"] == "7"
    assert focused_id(page) == "7"
    check_laws(page)


def test_collapse_moves_active(tree):
    page = tree
    open_2_011(page)
    click_toggle(page, "2")
    assert state(page)["activeId"] == "2"
    assert page.get_attribute("#item-2", "tabindex") == "0"
    assert focused_id(page) == "2"
    check_laws(page)


def test_help_dialog(tree):
    page = tree
    page.keyboard.press("Shift+Slash")
    assert page.get_attribute("#help", "open") is not None
    assert page.locator("#help .keys dd").all_text_contents() == HELP_STRINGS
    assert page.locator("#help .keys dt").count() == len(HELP_STRINGS)
    # Expand to level: one row whose single key names the whole digit range.
    level = HELP_STRINGS.index(
        "Expand to that many levels below the selected item; on the title, the whole outline"
    )
    kbds = page.locator("#help .keys dt").nth(level).locator("kbd").all_text_contents()
    is_apple = page.evaluate(
        "/mac|iphone|ipad/i.test(navigator.userAgentData?.platform ?? navigator.platform)"
    )
    assert kbds == ["⌥⌘1–9" if is_apple else "Ctrl+Alt+1–9"]
    page.keyboard.press("Escape")
    assert page.get_attribute("#help", "open") is None
    assert focused_id(page) == "1"
    page.click("#help-button")
    assert page.get_attribute("#help", "open") is not None
    page.keyboard.press("Escape")
    assert page.get_attribute("#help", "open") is None
    check_laws(page)


def test_roving_tabindex(tree):
    page = tree
    page.keyboard.press("ArrowDown")
    page.keyboard.press("ArrowDown")
    assert page.evaluate(
        "[...document.querySelectorAll('[tabindex=\"0\"]')].map(e => e.id)"
    ) == ["item-3"]
    page.keyboard.press("Tab")
    assert page.evaluate(
        "!document.getElementById('outline').contains(document.activeElement)"
    )
    check_laws(page)


def test_active_highlight(tree):
    page = tree
    page.keyboard.press("ArrowDown")
    page.keyboard.press("ArrowDown")
    bg = "sel => getComputedStyle(document.querySelector(sel)).backgroundColor"
    transparent = ("rgba(0, 0, 0, 0)", "transparent")
    assert page.evaluate(bg, "#item-3 > .row") not in transparent
    assert page.evaluate(bg, "#item-2 > .row") in transparent
    page.click("#help-button")
    assert page.evaluate(bg, "#item-3 > .row") not in transparent
    page.keyboard.press("Escape")
    check_laws(page)
    page.keyboard.press("Escape")                   # idle: nothing highlighted
    assert page.evaluate(bg, "#item-3 > .row") in transparent
    check_laws(page)
    page.keyboard.press("ArrowDown")                # selects again, without moving
    assert page.evaluate(bg, "#item-3 > .row") not in transparent
    assert focused_id(page) == "3"
    check_laws(page)


def test_empty_tree(open_outline):
    page = open_outline("")
    assert state(page) == {"expanded": [], "activeId": "root"}
    check_laws(page)


KEYS = [
    "ArrowUp",
    "ArrowDown",
    "ArrowLeft",
    "ArrowRight",
    "Home",
    "End",
    "Shift+Digit8",
    f"{MOD}+Period",
    f"{MOD}+Shift+Period",
    f"Alt+{MOD}+ArrowUp",
    f"Alt+{MOD}+ArrowDown",
    "Escape",
    "Shift+ArrowUp",
    "Shift+ArrowDown",
    "Shift+ArrowUp",
    "Shift+ArrowDown",
    "Shift+Home",
    "Shift+End",
]


@pytest.mark.parametrize("seed", [1, 2, 3])
def test_laws_random(tree, seed):
    """Laws S and D hold after every step of a random command sequence, which also lands on
    the root (Home, ArrowUp, a title click, promotion past the top level)."""
    page = tree
    rng = random.Random(seed)
    steps = []
    on_root = 0
    for n in range(300):
        kind = rng.choice(["key", "key", "toggle", "row", "shift-row"])
        if kind == "key":
            key = rng.choice(KEYS)
            steps.append(f"press {key}")
            page.keyboard.press(key)
        elif kind == "toggle":
            parents = page.evaluate(VISIBLE_PARENTS_JS)
            id = rng.choice(parents)
            steps.append(f"toggle {id}")
            click_toggle(page, id)
            sel = page.evaluate("window.tractatus.selection()")
            assert (sel["mode"], sel["anchorId"], sel["activeId"]) == ("selected", id, id), steps
        elif kind == "row":
            id = rng.choice(visible_ids(page))
            steps.append(f"row {id}")
            click_text(page, id)
        else:
            id = rng.choice(visible_ids(page))
            steps.append(f"shift-row {id}")
            page.click(text_sel(id), modifiers=["Shift"])
        errs = page.evaluate(LAWS_JS)
        assert errs == [], f"seed {seed}, step {n}: {errs}\nsteps: {steps}"
        on_root += state(page)["activeId"] == "root"
    assert on_root > 0, "the walk never reached the root"


@pytest.mark.network
def test_axe(tree):
    page = tree
    axe_source = page.request.get(AXE_URL).text()

    def serious():
        result = page.evaluate("async () => (await axe.run(document)).violations")
        return [
            (v["id"], v["impact"], [n["target"] for n in v["nodes"]])
            for v in result
            if v["impact"] in ("serious", "critical")
        ]

    def passes(scheme):
        # Inline: the page's CSP admits no script URL but MathJax's.
        page.add_script_tag(content=axe_source)
        assert serious() == [], f"{scheme}: collapsed on load"
        click_text(page, "1")
        for _ in range(8):
            page.keyboard.press(f"{MOD}+Shift+Period")
            page.keyboard.press(f"Alt+{MOD}+ArrowDown")
        assert len(visible_ids(page)) == 48
        check_laws(page)
        assert serious() == [], f"{scheme}: fully expanded"
        page.click("#help-button")
        assert serious() == [], f"{scheme}: help dialog open"
        page.keyboard.press("Escape")
        check_laws(page)
        page.click("#spacing-button")
        assert page.get_attribute("#spacing", "open") is not None
        assert serious() == [], f"{scheme}: spacing panel open"
        page.keyboard.press("Escape")
        assert page.get_attribute("#spacing", "open") is None
        check_laws(page)

    passes("light")
    page.emulate_media(color_scheme="dark")
    before = state(page)
    page.reload()
    page.wait_for_function("() => document.documentElement.dataset.outlineReady === 'true'")
    assert page.evaluate("matchMedia('(prefers-color-scheme: dark)').matches")
    assert state(page) == before   # the stored view is restored
    page.evaluate("localStorage.clear()")
    page.reload()
    page.wait_for_function("() => document.documentElement.dataset.outlineReady === 'true'")
    assert state(page) == {"expanded": [], "activeId": "1"}
    passes("dark")


def test_pointer_focus_follows_state(tree):
    """A press on a group's padding focuses the enclosing treeitem, which then becomes active."""
    page = tree
    page.keyboard.press("ArrowRight")
    page.keyboard.press("ArrowRight")
    assert focused_id(page) == "1.1"
    page.click("#item-1 > [role=group]", position={"x": 4, "y": 4})
    assert state(page)["activeId"] == "1"
    assert focused_id(page) == "1"
    check_laws(page)
