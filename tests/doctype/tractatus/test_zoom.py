"""Phase 4 (QoL): zoom and breadcrumbs (laws Z and F)."""

import random

import pytest
from conftest import LAWS_JS, check_laws
from test_deep_links import hash_of, set_hash
from test_math import settle
from test_selection import COPY_JS
from test_tree_keyboard import AXE_URL, KEYS, MOD, VISIBLE_PARENTS_JS, css, focused_id, state, visible_ids
from test_visual import CONTRAST_JS

IN = f"{MOD}+BracketRight"
OUT = f"{MOD}+BracketLeft"

ZOOM_MD = """\
# Zoom

Intro with [1.1](#1.1).

- 1 One
  - 1.1 One one
    - 1.1.1 Leaf a
    - 1.1.2 Leaf b

      n
  - 1.2 One two, see [2.1](#2.1)
- 2 Two
  - 2.1 Two one

    [self](#2.1)
"""


def zoom(page):
    return page.evaluate("window.tractatus.zoom()")


def crumbs(page):
    return page.locator("#crumbs a").all_text_contents()


def selection(page):
    return page.evaluate("window.tractatus.selection()")


def history_length(page):
    return page.evaluate("history.length")


def wait_zoom(page, id):
    page.wait_for_function("id => window.tractatus.zoom() === id", arg=id)


@pytest.fixture
def zpage(open_outline):
    """The zoom fixture at the document root, item 1 focused."""
    return open_outline(ZOOM_MD)


def test_zoom_in_out(zpage):
    page = zpage
    page.keyboard.press("ArrowRight")
    page.keyboard.press("ArrowRight")
    assert state(page)["activeId"] == "1.1"
    page.keyboard.press(IN)
    assert zoom(page) == "1.1"
    assert page.get_attribute("#item-root", "data-id") == "1.1"
    assert page.text_content("#doc-title") == "1.1 One one"
    assert visible_ids(page) == ["1.1", "1.1.1", "1.1.2"]
    assert state(page)["activeId"] == "1.1"
    assert hash_of(page) == "#z=1.1"
    assert crumbs(page) == ["Zoom", "1 One"]
    assert page.title().startswith("1.1 One one")
    check_laws(page)

    page.keyboard.press(OUT)
    assert zoom(page) == "1"
    assert state(page)["activeId"] == "1.1"
    assert hash_of(page) == "#z=1"
    check_laws(page)

    page.keyboard.press(OUT)
    assert zoom(page) == "root"
    assert hash_of(page) == ""
    assert page.locator("#crumbs").is_hidden()
    assert page.title() == "Zoom"
    check_laws(page)


def test_state_shape_unchanged(zpage):
    page = zpage
    page.keyboard.press(IN)
    assert zoom(page) == "1"
    assert set(state(page)) == {"expanded", "activeId"}
    check_laws(page)


def test_history_back_forward(zpage):
    page = zpage
    start = history_length(page)
    page.keyboard.press(IN)
    page.keyboard.press("ArrowDown")
    assert state(page)["activeId"] == "1.1"
    page.keyboard.press(IN)
    assert zoom(page) == "1.1"
    assert history_length(page) == start + 2
    page.go_back()
    wait_zoom(page, "1")
    check_laws(page)
    page.go_back()
    wait_zoom(page, "root")
    check_laws(page)
    page.go_forward()
    wait_zoom(page, "1")
    assert history_length(page) == start + 2
    check_laws(page)


def test_deep_link_zoom(open_outline):
    page = open_outline(ZOOM_MD, "#z=1.1")
    assert zoom(page) == "1.1"
    assert state(page)["activeId"] == "1.1.1"
    assert focused_id(page) == "1.1.1"
    assert page.text_content("#status") == ""
    check_laws(page)


def test_zoom_root_link(open_outline):
    page = open_outline(ZOOM_MD, "#z=root")
    assert zoom(page) == "root"
    assert page.text_content("#status") == ""
    check_laws(page)


def test_unknown_zoom(open_outline, page):
    open_outline(ZOOM_MD, "#z=9")
    assert page.text_content("#status") == "No item “9” in this outline."
    assert zoom(page) == "root"
    check_laws(page)
    page.goto("about:blank")
    open_outline(ZOOM_MD, "#z=%E0%A4%A")
    assert page.text_content("#status") == "No item “z=%E0%A4%A” in this outline."
    assert zoom(page) == "root"
    check_laws(page)


def test_zoom_under_collapsed_ancestors(open_outline):
    page = open_outline(ZOOM_MD, "#z=1.1")
    page.keyboard.press("Home")
    assert zoom(page) == "1.1"
    assert state(page) == {"expanded": [], "activeId": "1.1"}
    check_laws(page)


def test_zoom_commands_noop(zpage):
    page = zpage
    page.keyboard.press("Home")
    before = (state(page), history_length(page), page.url)
    page.keyboard.press(OUT)
    assert (state(page), history_length(page), page.url) == before
    assert zoom(page) == "root"

    page.keyboard.press("ArrowDown")
    page.keyboard.press(IN)
    page.keyboard.press("Home")
    assert state(page)["activeId"] == "1"
    before = (state(page), history_length(page), page.url)
    page.keyboard.press(IN)
    assert (state(page), history_length(page), page.url) == before
    assert zoom(page) == "1"
    check_laws(page)


def test_back_to_base_keeps_view(zpage):
    page = zpage
    page.set_viewport_size({"width": 800, "height": 200})
    set_hash(page, "#1")
    assert state(page)["activeId"] == "1"
    page.keyboard.press("ArrowDown")
    assert state(page)["activeId"] == "2"
    page.evaluate("window.scrollTo(0, document.documentElement.scrollHeight)")
    y = page.evaluate("window.scrollY")
    assert y > 0
    page.go_back()
    page.wait_for_function("() => location.hash === ''")
    page.wait_for_timeout(100)
    assert zoom(page) == "root"
    assert state(page)["activeId"] == "2"
    assert page.evaluate("window.scrollY") == y
    check_laws(page)


def test_url_id_unzooms(open_outline):
    page = open_outline(ZOOM_MD, "#z=2")
    set_hash(page, "#1.1.2")
    assert zoom(page) == "root"
    assert state(page)["activeId"] == "1.1.2"
    assert {"1", "1.1"} <= set(state(page)["expanded"])
    assert page.locator("#crumbs").is_hidden()
    check_laws(page)


def expand_1(page):
    page.click("#item-1 > .row > .toggle")
    assert page.get_attribute("#item-1", "aria-expanded") == "true"


LINK_21 = "#item-1_2 .text a"


def test_item_link_zooms(zpage):
    page = zpage
    expand_1(page)
    start = history_length(page)
    page.click(LINK_21)
    assert zoom(page) == "2.1"
    assert state(page)["activeId"] == "2.1"
    assert focused_id(page) == "2.1"
    assert hash_of(page) == "#z=2.1"
    assert history_length(page) == start + 1
    assert page.text_content("#status") == ""
    check_laws(page)
    page.go_back()
    wait_zoom(page, "root")
    assert hash_of(page) == ""
    check_laws(page)


def test_item_link_after_url_reveal(open_outline):
    page = open_outline(ZOOM_MD, "#2.1")
    assert state(page)["activeId"] == "2.1"
    expand_1(page)
    page.click(LINK_21)
    assert zoom(page) == "2.1"
    assert hash_of(page) == "#z=2.1"
    check_laws(page)


def test_intro_link_zooms(zpage):
    page = zpage
    page.click("#intro a")
    assert zoom(page) == "1.1"
    assert page.text_content("#doc-title") == "1.1 One one"
    check_laws(page)


def test_item_link_to_current_zoom(open_outline):
    page = open_outline(ZOOM_MD, "#z=2.1")
    assert page.text_content("#intro") == "self"
    start = history_length(page)
    page.click("#intro a")
    assert zoom(page) == "2.1"
    assert state(page)["activeId"] == "2.1"
    assert history_length(page) == start
    check_laws(page)


def test_item_link_modified_click(zpage):
    page = zpage
    expand_1(page)
    page.on("popup", lambda p: p.close())
    page.context.on("page", lambda p: p.close() if p != page else None)
    page.evaluate(
        "() => { window.__prevented = null;"
        " addEventListener('click', (e) => { window.__prevented = e.defaultPrevented; }); }"
    )
    page.click(LINK_21, modifiers=["ControlOrMeta"])
    assert page.evaluate("window.__prevented") is False
    assert zoom(page) == "root"
    check_laws(page)


def test_displayed_root_keys(open_outline):
    page = open_outline(ZOOM_MD, "#z=1")
    page.keyboard.press("Home")
    assert state(page) == {"expanded": [], "activeId": "1"}
    page.keyboard.press("ArrowLeft")
    assert state(page) == {"expanded": [], "activeId": "1"}
    page.keyboard.press(f"{MOD}+Period")
    assert state(page) == {"expanded": ["1.1"], "activeId": "1"}
    page.keyboard.press("Shift+ArrowUp")
    assert state(page) == {"expanded": ["1.1"], "activeId": "1"}
    assert selection(page)["anchorId"] == "1"
    page.keyboard.press("ArrowDown")
    assert state(page)["activeId"] == "1.1"
    page.keyboard.press("ArrowUp")
    assert state(page)["activeId"] == "1"
    page.keyboard.press("Escape")
    assert selection(page)["mode"] == "idle"
    assert zoom(page) == "1"
    check_laws(page)


def test_range_clamped(open_outline):
    page = open_outline(ZOOM_MD, "#z=1")
    assert state(page)["activeId"] == "1"      # the current active item is the zoomed one
    page.keyboard.press("ArrowDown")
    assert state(page)["activeId"] == "1.1"
    page.keyboard.press("Shift+ArrowDown")
    sel = selection(page)
    assert (sel["anchorId"], sel["activeId"]) == ("1.1", "1.2")
    check_laws(page)
    page.keyboard.press("Shift+ArrowDown")
    sel = selection(page)
    assert (sel["anchorId"], sel["activeId"]) == ("1", "1")
    check_laws(page)


def test_expansion_survives_zoom(zpage):
    page = zpage
    page.click("#item-2 > .row > .toggle")
    page.click("#item-1 > .row > .text", position={"x": 4, "y": 4})
    assert state(page)["activeId"] == "1"
    page.keyboard.press(IN)
    assert zoom(page) == "1"
    assert "2" in state(page)["expanded"]
    page.keyboard.press(OUT)
    assert zoom(page) == "root"
    assert "2" in state(page)["expanded"]
    assert "2.1" in visible_ids(page)
    check_laws(page)


def test_copy_on_zoom_root(open_outline):
    page = open_outline(ZOOM_MD, "#z=1.1")
    page.keyboard.press("Home")
    out = page.evaluate(COPY_JS)
    assert out["prevented"]
    assert out["text"].startswith("- 1.1 One one\n")
    assert "1.1.2 Leaf b" in out["text"]
    assert "One two" not in out["text"]
    check_laws(page)


def test_bullet_clicks(zpage):
    page = zpage
    page.keyboard.press("Escape")
    assert selection(page)["mode"] == "idle"
    y = page.evaluate("window.scrollY")
    page.click("#item-1 > .row > .toggle")
    assert state(page) == {"expanded": ["1"], "activeId": "1"}
    assert selection(page)["mode"] == "selected"
    assert zoom(page) == "root"
    assert page.evaluate("window.scrollY") == y
    check_laws(page)
    page.click("#item-1_1 > .row > .toggle", modifiers=["ControlOrMeta"])
    assert zoom(page) == "1.1"
    assert state(page) == {"expanded": ["1"], "activeId": "1.1"}
    assert hash_of(page) == "#z=1.1"
    check_laws(page)


def shift_tab_to(page, selector, browser_name):
    for _ in range(10):
        page.keyboard.press("Alt+Shift+Tab" if browser_name == "webkit" else "Shift+Tab")
        if page.evaluate("s => document.activeElement === document.querySelector(s)", selector):
            return
    raise AssertionError(f"Shift+Tab never reached {selector}")


def test_crumb_navigation(zpage, browser_name):
    page = zpage
    page.keyboard.press(IN)
    page.keyboard.press("ArrowDown")
    page.keyboard.press(IN)
    assert zoom(page) == "1.1"
    assert crumbs(page) == ["Zoom", "1 One"]
    shift_tab_to(page, "#crumbs li:first-child a", browser_name)
    page.keyboard.press("Enter")
    assert zoom(page) == "root"
    assert state(page)["activeId"] == "1"
    assert focused_id(page) == "1"
    assert hash_of(page) == ""
    check_laws(page)


def test_crumb_focus_ring(open_outline, browser_name):
    page = open_outline(ZOOM_MD, "#z=1.1")
    shift_tab_to(page, "#crumbs li:last-child a", browser_name)
    style = page.evaluate(
        "() => { const s = getComputedStyle(document.activeElement);"
        " return [s.outlineStyle, s.outlineColor]; }"
    )
    ring = page.evaluate(
        "() => { const d = document.createElement('div');"
        " d.style.color = 'var(--link-focus)'; document.body.append(d);"
        " const c = getComputedStyle(d).color; d.remove(); return c; }"
    )
    assert style == ["solid", ring]
    check_laws(page)


def test_zoomed_title_links(open_outline):
    page = open_outline(ZOOM_MD, "#z=1.2")
    link = '#doc-title a[href="#2.1"]'
    assert page.get_attribute(link, "tabindex") == "-1"
    for _ in range(8):
        page.keyboard.press("Tab")
        assert not page.evaluate("s => document.activeElement === document.querySelector(s)", link)
    page.click(link)
    assert zoom(page) == "2.1"
    check_laws(page)


LONG = "word " * 15


def test_head_narrow(open_outline, page):
    page.set_viewport_size({"width": 320, "height": 600})
    md = f"# {LONG}title\n\n- 1 {LONG}\n  - 1.1 {LONG}\n    - 1.1.1 {LONG}\n"
    open_outline(md, "#z=1.1.1")
    assert zoom(page) == "1.1.1"
    assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")
    boxes = page.evaluate(
        "() => [...document.querySelectorAll('#crumbs a, .page-tools button')].map((e) => {"
        " const r = e.getBoundingClientRect();"
        " return { tool: e.tagName === 'BUTTON', l: r.left, r: r.right, t: r.top, b: r.bottom }; })"
    )
    width = page.evaluate("innerWidth")
    crumbs = [b for b in boxes if not b["tool"]]
    assert len(crumbs) == 3
    # The crumbs are one line that scrolls sideways inside the viewport, scrolled to its end: the
    # nearest ancestor is in full view, and Up (zoom out one level) is always in reach.
    line = page.evaluate("(() => { const r = document.querySelector('#crumbs ol').getBoundingClientRect();"
                         " return { l: r.left, r: r.right, t: r.top, b: r.bottom }; })()")
    assert 0 <= line["l"] and line["r"] <= width, line
    assert line["l"] - 0.5 <= crumbs[-1]["l"] and crumbs[-1]["r"] <= line["r"] + 0.5, (line, crumbs[-1])
    assert page.evaluate("(() => { const o = document.querySelector('#crumbs ol');"
                         " return getComputedStyle(o).overflowX === 'auto' && o.scrollWidth > o.clientWidth; })()")
    up = page.locator("#up-button")
    assert up.is_visible()
    tools = [b for b in boxes if b["tool"]]
    for b in tools:
        assert 0 <= b["l"] and b["r"] <= width, b
    for c in crumbs:
        for t in tools:
            overlap = c["l"] < t["r"] and t["l"] < c["r"] and c["t"] < t["b"] and t["t"] < c["b"]
            assert not overlap, (c, t)
    up.click()
    assert zoom(page) == "1.1"
    check_laws(page)


@pytest.mark.parametrize("scheme", ["light", "dark"])
def test_crumb_contrast(open_outline, page, scheme):
    page.emulate_media(color_scheme=scheme)
    open_outline(ZOOM_MD, "#z=1.1")
    results = page.evaluate(CONTRAST_JS, ["#crumbs a"])
    assert len(results) == 2
    assert all(r["ratio"] >= 4.5 for r in results), results
    check_laws(page)


def test_crumb_separator_not_announced(open_outline):
    page = open_outline(ZOOM_MD, "#z=1.1")
    snapshot = page.locator("#crumbs").aria_snapshot()
    assert "Zoom" in snapshot and "1 One" in snapshot
    assert ">" not in snapshot
    check_laws(page)


@pytest.mark.network
def test_math_under_zoom(open_outline):
    page = open_outline("# M\n\n- 1 One $x$\n  - 1.1 Sub $y$\n- 2 Two\n")
    assert settle(page) == "ready"
    page.keyboard.press(IN)
    assert zoom(page) == "1"
    assert settle(page) == "ready"
    page.wait_for_function(
        "() => document.querySelector('#doc-title .math')?.dataset.math === 'typeset'"
    )
    assert page.locator('#item-1_1 .math[data-math="typeset"]').count() == 1
    check_laws(page)


@pytest.mark.network
def test_axe_zoomed(open_outline, page):
    for scheme in ["light", "dark"]:
        page.emulate_media(color_scheme=scheme)
        open_outline(ZOOM_MD, "#z=1.1")
        page.add_script_tag(content=page.request.get(AXE_URL).text())
        result = page.evaluate("async () => (await axe.run(document)).violations")
        serious = [
            (v["id"], [n["target"] for n in v["nodes"]])
            for v in result
            if v["impact"] in ("serious", "critical")
        ]
        assert serious == [], scheme
        check_laws(page)
        page.goto("about:blank")


def text_sel_zoomed(page, id):
    return "#doc-title" if id == zoom(page) else f"#item-{css(id)} > .row > .text"


@pytest.mark.parametrize("seed", [1, 2, 3])
def test_laws_random_with_zoom(open_outline, seed):
    """Laws S, D and Z hold after every step of a random walk that zooms in, out and back."""
    page = open_outline(ZOOM_MD)
    rng = random.Random(seed)
    steps = []
    depth = 0       # history entries behind the current one that belong to this page
    zoomed = 0
    for n in range(200):
        kind = rng.choice(["key", "key", "zoom", "zoom", "back", "toggle", "row"])
        if kind == "key":
            key = rng.choice(KEYS)
            steps.append(f"press {key}")
            page.keyboard.press(key)
        elif kind == "zoom":
            key = rng.choice([IN, OUT])
            steps.append(f"press {key}")
            before = page.url
            page.keyboard.press(key)
            depth += page.url != before
        elif kind == "back":
            if depth == 0:
                continue
            steps.append("back")
            page.go_back()
            depth -= 1
            page.wait_for_function(
                "() => { const h = location.hash;"
                " const want = h.startsWith('#z=') ? decodeURIComponent(h.slice(3)) : 'root';"
                " return window.tractatus.zoom() === want; }"
            )
        elif kind == "toggle":
            parents = page.evaluate(VISIBLE_PARENTS_JS)
            if not parents:
                continue
            id = rng.choice(parents)
            steps.append(f"toggle {id}")
            page.click(f"#item-{css(id)} > .row > .toggle")
        else:
            id = rng.choice(visible_ids(page))
            steps.append(f"row {id}")
            page.click(text_sel_zoomed(page, id), position={"x": 4, "y": 4})
        errs = page.evaluate(LAWS_JS)
        assert errs == [], f"seed {seed}, step {n}: {errs}\nsteps: {steps}"
        zoomed += zoom(page) != "root"
    assert zoomed > 0, "the walk never zoomed"
