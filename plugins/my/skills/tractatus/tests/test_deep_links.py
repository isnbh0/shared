"""Phase 3: deep links and initial focus (law F)."""

from conftest import check_laws
from test_tree_keyboard import MOD, focused_id, state, visible_ids

TOP_LEVEL = ["1", "2", "3", "4", "5", "6", "7", "p-8"]


def hash_of(page):
    return page.evaluate("location.hash")


def set_hash(page, fragment):
    """Navigate the fragment as a reader would (the test, not the viewer, writes location).

    Resolves after the viewer's own hashchange listener, which was registered first.
    """
    page.evaluate(
        "f => new Promise(done => {"
        " addEventListener('hashchange', done, { once: true }); location.hash = f; })",
        fragment,
    )


def test_initial_focus(open_outline, fake_md):
    page = open_outline(fake_md)
    assert page.evaluate("document.activeElement.id") == "item-1"
    page.keyboard.press("ArrowDown")
    assert focused_id(page) == "2"
    assert page.evaluate("window.scrollY") == 0
    check_laws(page)


def test_deep_link_reveals(open_outline, fake_md):
    page = open_outline(fake_md, "#2.0121")
    assert focused_id(page) == "2.0121"
    assert page.get_attribute("#item-2_0121", "tabindex") == "0"
    assert state(page)["expanded"] == ["2", "2.01", "2.012"]
    assert page.get_attribute("#item-2_0123", "aria-expanded") == "false"
    assert set(TOP_LEVEL) <= set(visible_ids(page))
    assert page.get_attribute("#item-1", "aria-expanded") == "false"
    assert hash_of(page) == "#2.0121"
    assert page.text_content("#status") == ""
    check_laws(page)


def test_deep_link_scrolls_into_view(open_outline, fake_md, page):
    page.set_viewport_size({"width": 800, "height": 300})
    page = open_outline(fake_md, "#6.54")
    assert focused_id(page) == "6.54"
    box = page.evaluate(
        "(() => { const r = document.querySelector('#item-6_54 > .row').getBoundingClientRect();"
        " return [r.top, r.bottom, innerHeight]; })()"
    )
    top, bottom, height = box
    assert 0 <= top and bottom <= height
    assert page.evaluate("window.scrollY") > 0
    check_laws(page)


def test_deep_link_positional(open_outline, fake_md):
    page = open_outline(fake_md, "#p-5-3")
    assert "5" in state(page)["expanded"]
    assert focused_id(page) == "p-5-3"
    text = page.evaluate("document.activeElement.querySelector(':scope > .row > .text').textContent")
    assert text.startswith("Unnumbered aside")
    check_laws(page)


def test_hashchange_reveals(open_outline, fake_md):
    page = open_outline(fake_md)
    set_hash(page, "#4.011")
    page.wait_for_function("() => document.activeElement.dataset.id === '4.011'")
    assert focused_id(page) == "4.011"
    assert {"4", "4.01"} <= set(state(page)["expanded"])
    check_laws(page)


def test_reveal_keeps_expansion(open_outline, fake_md):
    page = open_outline(fake_md)
    page.keyboard.press("ArrowRight")
    assert state(page)["expanded"] == ["1"]
    set_hash(page, "#3.11")
    page.wait_for_function("() => document.activeElement.dataset.id === '3.11'")
    assert state(page)["expanded"] == ["1", "3", "3.1"]
    check_laws(page)


def test_back_forward(open_outline, fake_md):
    page = open_outline(fake_md)
    set_hash(page, "#1.1")
    page.wait_for_function("() => document.activeElement.dataset.id === '1.1'")
    set_hash(page, "#3.11")
    page.wait_for_function("() => document.activeElement.dataset.id === '3.11'")
    page.go_back()
    page.wait_for_function("() => document.activeElement.dataset.id === '1.1'")
    assert hash_of(page) == "#1.1"
    page.go_forward()
    page.wait_for_function("() => document.activeElement.dataset.id === '3.11'")
    assert hash_of(page) == "#3.11"
    check_laws(page)


def test_focus_does_not_touch_url(open_outline, fake_md):
    page = open_outline(fake_md, "#2")
    before = page.evaluate("history.length")
    assert focused_id(page) == "2"
    for _ in range(3):
        page.keyboard.press("ArrowDown")
    page.keyboard.press(f"{MOD}+Period")
    page.click("#item-1 > .row")
    assert focused_id(page) == "1"
    assert hash_of(page) == "#2"
    assert page.evaluate("history.length") == before
    check_laws(page)


def test_history_only_for_zoom(open_outline, fake_md):
    """Law F (amended): only a zoom writes history, and a zoom's entry is always #z=ID."""
    page = open_outline(fake_md)
    before = (page.evaluate("history.length"), page.url)
    page.keyboard.press("ArrowDown")
    page.keyboard.press("ArrowRight")
    page.keyboard.press(f"{MOD}+Period")
    page.keyboard.press("Escape")
    assert (page.evaluate("history.length"), page.url) == before
    page.keyboard.press("ArrowDown")
    active = state(page)["activeId"]
    page.keyboard.press(f"{MOD}+BracketRight")
    assert page.evaluate("history.length") == before[0] + 1
    assert hash_of(page) == f"#z={active}"
    check_laws(page)

    page.keyboard.press(f"{MOD}+BracketLeft")        # unzoomed, so the stored view is too
    page.goto("about:blank")
    page = open_outline(fake_md)
    page.click("#item-4 > .row > .toggle")
    page.click("#item-4_1 > .row > .toggle")
    length = page.evaluate("history.length")
    page.click("#item-4_11 .text a")
    assert page.evaluate("history.length") == length + 1
    assert hash_of(page) == "#z=5.1"
    page.go_back()
    page.wait_for_function("() => window.tractatus.zoom() === 'root'")
    assert hash_of(page) == ""
    check_laws(page)


def test_empty_fragment_after_load_keeps_place(open_outline, fake_md):
    page = open_outline(fake_md, "#2.0121")
    before = state(page)
    page.keyboard.press("ArrowDown")
    after_key = state(page)
    set_hash(page, "#")
    assert hash_of(page) == ""
    assert before != after_key
    assert state(page) == after_key
    assert focused_id(page) == after_key["activeId"]
    check_laws(page)


def test_unknown_fragment(open_outline, fake_md):
    page = open_outline(fake_md, "#9.9")
    assert "No item “9.9”" in page.text_content("#status")
    assert focused_id(page) == "1"
    assert visible_ids(page) == ["root", *TOP_LEVEL]
    check_laws(page)


def test_unknown_then_known_clears_status(open_outline, fake_md):
    page = open_outline(fake_md)
    set_hash(page, "#9.9")
    assert "No item “9.9”" in page.text_content("#status")
    assert state(page) == {"expanded": [], "activeId": "1"}
    set_hash(page, "#1.11")
    page.wait_for_function("() => document.activeElement.dataset.id === '1.11'")
    assert page.text_content("#status") == ""
    check_laws(page)


def test_malformed_fragment(open_outline, fake_md, console_errors):
    page = open_outline(fake_md, "#%E0%A4%A")
    assert "No item “%E0%A4%A”" in page.text_content("#status")
    assert focused_id(page) == "1"
    assert console_errors == []
    check_laws(page)


def test_encoded_fragment(open_outline, fake_md):
    page = open_outline(fake_md, "#2%2E01")
    assert focused_id(page) == "2.01"
    check_laws(page)


def test_empty_document_fragment(open_outline, console_errors):
    page = open_outline("", "#1")
    assert "No item “1”" in page.text_content("#status")
    assert console_errors == []
    check_laws(page)
