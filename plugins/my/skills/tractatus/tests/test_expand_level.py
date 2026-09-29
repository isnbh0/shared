"""Expand to level: ⌥⌘1–9 (Ctrl+Alt+1–9) set the expansion below the active item to N levels."""

import random

import pytest
from conftest import LAWS_JS, check_laws
from test_tree_keyboard import KEYS, MOD, click_text, focused_id, state

LEVEL_MD = """\
# Levels

- 1 One
  - 1.1 One one
    - 1.1.1 Three deep
      - 1.1.1.1 Four deep
        - 1.1.1.1.1 Five deep
  - 1.2 One two
    - 1.2.1 One two one
- 2 Two
  - 2.1 Two one
- 3 Three
"""
ALL_PARENTS = ["1", "1.1", "1.1.1", "1.1.1.1", "1.2", "2"]


def LEVEL(n):
    return f"Alt+{MOD}+Digit{n}"


def selection(page):
    return page.evaluate("window.tractatus.selection()")


@pytest.fixture
def levels(open_outline):
    """The level fixture with item 1 selected by a click."""
    page = open_outline(LEVEL_MD)
    click_text(page, "1")
    assert focused_id(page) == "1"
    return page


def test_level_on_item(levels):
    page = levels
    page.keyboard.press(LEVEL(2))
    assert state(page) == {"expanded": ["1", "1.1", "1.2"], "activeId": "1"}
    assert focused_id(page) == "1"
    check_laws(page)


def test_level_one_collapses_below(levels):
    page = levels
    page.keyboard.press(f"{MOD}+Shift+Period")
    assert state(page)["expanded"] == ALL_PARENTS[:5]
    page.keyboard.press(LEVEL(1))
    assert state(page) == {"expanded": ["1"], "activeId": "1"}
    check_laws(page)


def test_level_is_relative(levels):
    page = levels
    page.keyboard.press("ArrowRight")               # expand 1
    page.keyboard.press("ArrowRight")               # to 1.1
    assert state(page) == {"expanded": ["1"], "activeId": "1.1"}
    page.keyboard.press(LEVEL(2))
    assert state(page) == {"expanded": ["1", "1.1", "1.1.1"], "activeId": "1.1"}
    check_laws(page)


def test_level_on_title(levels):
    page = levels
    page.keyboard.press(f"{MOD}+Shift+Period")      # something to collapse under the root
    page.keyboard.press("Home")
    assert state(page)["activeId"] == "root"
    page.keyboard.press(LEVEL(1))
    assert state(page) == {"expanded": [], "activeId": "root"}
    check_laws(page)
    page.keyboard.press(LEVEL(3))
    assert state(page) == {"expanded": ["1", "1.1", "1.2", "2"], "activeId": "root"}
    assert page.get_attribute("#item-root", "aria-expanded") == "true"
    check_laws(page)


def test_outside_subtree_untouched(levels):
    page = levels
    page.keyboard.press("ArrowDown")
    page.keyboard.press("ArrowRight")               # expand 2
    page.keyboard.press("ArrowUp")
    assert state(page) == {"expanded": ["2"], "activeId": "1"}
    page.keyboard.press(LEVEL(1))
    assert state(page) == {"expanded": ["1", "2"], "activeId": "1"}
    check_laws(page)


def test_leaf_noop(levels):
    page = levels
    page.keyboard.press("ArrowDown")
    page.keyboard.press("ArrowDown")
    before = state(page)
    assert before == {"expanded": [], "activeId": "3"}
    page.keyboard.press(LEVEL(4))
    assert state(page) == before
    assert focused_id(page) == "3"
    check_laws(page)


def test_range_collapses(levels):
    page = levels
    page.keyboard.press("Shift+ArrowDown")
    sel = selection(page)
    assert (sel["anchorId"], sel["activeId"]) == ("1", "2")
    page.keyboard.press(LEVEL(2))
    sel = selection(page)
    assert (sel["mode"], sel["anchorId"], sel["activeId"]) == ("selected", "2", "2")
    assert state(page)["expanded"] == ["2"]
    check_laws(page)


def test_idle_first_key_reselects(levels):
    page = levels
    page.keyboard.press("Escape")
    assert selection(page)["mode"] == "idle"
    page.keyboard.press(LEVEL(2))
    assert selection(page)["mode"] == "selected"
    assert state(page) == {"expanded": [], "activeId": "1"}
    check_laws(page)


def platform_script(platform):
    return (
        "Object.defineProperty(navigator, 'userAgentData', "
        f"{{ get: () => ({{ platform: {platform!r} }}) }});"
    )


DISPATCH_JS = """(init) => document.getElementById('item-1').dispatchEvent(
  new KeyboardEvent('keydown', { code: 'Digit2', key: '2', bubbles: true, cancelable: true, ...init }))"""


def test_altgraph_ignored(page, open_outline):
    page.add_init_script(platform_script("Linux"))
    open_outline(LEVEL_MD)
    assert page.evaluate("document.querySelector('#help dt:nth-of-type(19) kbd').textContent") == "Ctrl+Alt+1–9"
    click_text(page, "1")
    before = state(page)
    page.evaluate(DISPATCH_JS, {"altKey": True, "ctrlKey": True, "modifierAltGraph": True})
    assert state(page) == before
    page.evaluate(DISPATCH_JS, {"altKey": True, "ctrlKey": True})
    assert state(page) == {"expanded": ["1", "1.1", "1.2"], "activeId": "1"}
    check_laws(page)


def test_altgraph_allowed_on_apple(page, open_outline):
    page.add_init_script(platform_script("macOS"))
    open_outline(LEVEL_MD)
    click_text(page, "1")
    page.evaluate(
        DISPATCH_JS, {"altKey": True, "metaKey": True, "ctrlKey": False, "modifierAltGraph": True}
    )
    assert state(page) == {"expanded": ["1", "1.1", "1.2"], "activeId": "1"}
    check_laws(page)


def test_routed_from_body(levels):
    page = levels
    page.evaluate("document.activeElement.blur()")
    assert page.evaluate("document.activeElement === document.body")
    page.keyboard.press(LEVEL(2))
    assert state(page) == {"expanded": ["1", "1.1", "1.2"], "activeId": "1"}
    assert focused_id(page) == "1"
    check_laws(page)


LEVEL_KEYS = KEYS + [LEVEL(n) for n in range(1, 10)]


@pytest.mark.parametrize("seed", [1, 2, 3])
def test_laws_after_levels(levels, seed):
    """Laws S and D hold after every step of a random walk that mixes level chords with the
    tree keys."""
    page = levels
    rng = random.Random(seed)
    steps = []
    for n in range(200):
        key = rng.choice(LEVEL_KEYS)
        steps.append(key)
        page.keyboard.press(key)
        errs = page.evaluate(LAWS_JS)
        assert errs == [], f"seed {seed}, step {n}: {errs}\nsteps: {steps}"
