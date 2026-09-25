"""Scrolling: a pointer action never scrolls the page; keyboard moves scroll minimally."""

import pytest
from conftest import check_laws
from test_selection import blur, full_selection, selection
from test_tree_keyboard import MOD, css, focused_id, state

SHORT = {"width": 900, "height": 300}


def scroll_y(page):
    return page.evaluate("scrollY")


def to_bottom(page):
    page.evaluate("() => window.scrollTo(0, document.documentElement.scrollHeight)")
    return scroll_y(page)


def row_rect(page, id):
    return page.evaluate(
        "sel => { const r = document.querySelector(sel).getBoundingClientRect();"
        " return { top: r.top, bottom: r.bottom }; }",
        f"#item-{css(id)} > .row",
    )


def off_screen(page, id):
    r = row_rect(page, id)
    return r["bottom"] <= 0 or r["top"] >= page.evaluate("innerHeight")


def press_at(page, selector, modifiers=()):
    """Click the centre of an on-screen element without Playwright's scroll-into-view."""
    box = page.locator(selector).bounding_box()
    assert box is not None and 0 <= box["y"] and box["y"] + box["height"] <= SHORT["height"]
    for m in modifiers:
        page.keyboard.down(m)
    page.mouse.click(box["x"] + box["width"] / 2, box["y"] + box["height"] / 2)
    for m in modifiers:
        page.keyboard.up(m)


def to_middle(page):
    """Scroll to mid-page, so collapsing an on-screen item cannot clamp the scroll position."""
    page.evaluate("() => window.scrollTo(0, document.documentElement.scrollHeight / 2)")
    return scroll_y(page)


def on_screen_parent(page):
    """The last item with a toggle whose row is wholly on screen."""
    return page.evaluate(
        "h => [...document.querySelectorAll('[role=treeitem][aria-expanded]:not(#item-root)')]"
        ".filter(e => { const r = e.querySelector(':scope > .row').getBoundingClientRect();"
        " return e.checkVisibility() && r.top >= 0 && r.bottom <= h; })"
        ".map(e => e.dataset.id).at(-1)",
        SHORT["height"],
    )


@pytest.fixture
def tall(open_outline, fake_md, page):
    """The fixture outline fully expanded in a short viewport, with the range 2–1 (focus end 1)
    selected at the top of the page."""
    page.set_viewport_size(SHORT)
    open_outline(fake_md)
    page.keyboard.press("Home")
    page.keyboard.press(f"{MOD}+Shift+Period")          # on the title: the whole outline
    page.click("#item-1 > .row > .text")
    page.keyboard.press(f"Alt+{MOD}+ArrowDown")
    page.keyboard.press("Shift+ArrowUp")
    assert full_selection(page)["anchorId"] == "2"
    assert page.evaluate("document.documentElement.scrollHeight") > 3 * SHORT["height"]
    return page


def test_bullet_click_selects_its_item_without_scrolling(tall):
    page = tall
    y = to_middle(page)
    assert off_screen(page, "1") and off_screen(page, "2")
    x = on_screen_parent(page)
    assert x not in ("1", "2")
    was_open = x in state(page)["expanded"]
    press_at(page, f"#item-{css(x)} > .row > .toggle")
    assert scroll_y(page) == y
    s = full_selection(page)
    assert (s["mode"], s["anchorId"], s["activeId"], s["selected"][:1]) == ("selected", x, x, [x])
    assert (x in state(page)["expanded"]) != was_open
    assert focused_id(page) == x
    check_laws(page)


def test_idle_bullet_click_selects_without_scrolling(tall):
    page = tall
    page.keyboard.press("Escape")
    page.keyboard.press("Escape")
    assert selection(page)["mode"] == "idle"
    y = to_middle(page)
    x = on_screen_parent(page)
    press_at(page, f"#item-{css(x)} > .row > .toggle")
    assert scroll_y(page) == y
    assert selection(page) == {"mode": "selected", "activeId": x}
    assert focused_id(page) == x
    check_laws(page)


def test_row_clicks_do_not_scroll(tall):
    """A plain click on a row cut off by the viewport edge, and a Shift+click whose range's
    focus end is off-screen, leave the page where it is."""
    page = tall
    y = to_bottom(page) // 2
    page.evaluate("y => window.scrollTo(0, y)", y)
    ids = page.evaluate(
        "h => [...document.querySelectorAll('[role=treeitem]:not(#item-root) > .row')]"
        ".filter(r => { const b = r.getBoundingClientRect(); return b.top < h && b.bottom > h; })"
        ".map(r => r.parentElement.dataset.id)",
        SHORT["height"],
    )
    assert ids, "no row straddles the bottom edge"
    r = row_rect(page, ids[0])
    page.mouse.click(200, (r["top"] + SHORT["height"]) / 2)
    assert scroll_y(page) == y
    assert selection(page) == {"mode": "selected", "activeId": ids[0]}
    check_laws(page)

    page.click("#item-1_11 > .row > .text")              # anchor deep in item 1
    y = to_bottom(page)
    assert off_screen(page, "1")
    press_at(page, "#item-7 > .row > .text", modifiers=["Shift"])
    assert scroll_y(page) == y
    assert full_selection(page)["anchorId"] == "1"
    check_laws(page)


def test_empty_area_click_does_not_scroll(tall):
    page = tall
    blur(page)
    y = to_bottom(page)
    assert off_screen(page, "1")
    page.mouse.click(3, 150)
    assert scroll_y(page) == y
    assert focused_id(page) == "1"
    check_laws(page)


def test_closing_panels_does_not_scroll(tall):
    page = tall
    page.click("#spacing-button")
    y = to_bottom(page)
    page.click("#spacing-close")                          # the panel is fixed: still on screen
    assert scroll_y(page) == y
    page.evaluate("() => window.scrollTo(0, 0)")
    page.click("#spacing-button")
    y = to_bottom(page)
    page.keyboard.press("Escape")
    assert scroll_y(page) == y
    assert off_screen(page, "1")
    page.keyboard.press("Shift+Slash")
    page.keyboard.press("Escape")
    assert page.get_attribute("#help", "open") is None
    assert scroll_y(page) == y
    check_laws(page)


def test_arrow_down_scrolls_minimally(tall):
    page = tall
    page.keyboard.press("Escape")                         # collapse the range to its focus end, 1
    page.evaluate("() => window.scrollTo(0, 0)")
    height = SHORT["height"]
    scrolled = False
    for _ in range(30):
        page.keyboard.press("ArrowDown")
        r = row_rect(page, focused_id(page))
        assert 0 <= r["top"] and r["bottom"] <= height, r
        if scroll_y(page) > 0:
            scrolled = True
            assert height - r["bottom"] < 1                # "nearest": flush with the bottom
            break
    assert scrolled
    check_laws(page)
