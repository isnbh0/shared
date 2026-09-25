"""Copy link: ⇧⌘C (Ctrl+Shift+C) copies the selected item's URL and announces it in a toast."""

import pytest
from conftest import check_laws
from test_tree_keyboard import MOD, focused_id, state

LINK = "ControlOrMeta+Shift+KeyC"

# The clipboard is stubbed: headless Chromium has no system clipboard to read back.
CLIPBOARD_STUB = """
Object.defineProperty(navigator, "clipboard", { configurable: true, value: {
  writeText: (t) => (window.__copyMode === "reject" ? Promise.reject(new Error("no")) : (window.__copied = t, Promise.resolve())) } });
addEventListener("copy", (e) => { window.__fallback = e.clipboardData.getData("text/plain"); });
"""

LINK_MD = """\
# Links

- 1 One
  - 1.1 One one
- 2 Two
  - 2.1 Two one
- 3 Three
"""


@pytest.fixture
def links(page, open_outline):
    page.add_init_script(CLIPBOARD_STUB)

    def _open(markdown: str = LINK_MD, fragment: str = ""):
        return open_outline(markdown, fragment)

    return _open


def base(page) -> str:
    return page.url.split("#")[0]


def copied(page):
    return page.evaluate("window.__copied")


def toast_says(page, text: str) -> None:
    page.wait_for_function("(t) => document.getElementById('toast').textContent === t", arg=text)


def test_copies_item_url(links):
    page = links()
    page.keyboard.press("ArrowRight")
    page.keyboard.press("ArrowRight")
    assert state(page)["activeId"] == "1.1"
    page.keyboard.press(LINK)
    assert copied(page) == base(page) + "#1.1"
    assert page.is_visible("#toast")
    toast_says(page, "Link copied")
    assert page.is_visible("#toast")
    assert page.evaluate("document.activeElement.id") == "item-1_1"
    check_laws(page)


def test_title_copies_root(links):
    page = links()
    page.keyboard.press("Home")
    assert state(page)["activeId"] == "root"
    page.keyboard.press(LINK)
    url = copied(page)
    assert url == base(page) + "#root"
    page.keyboard.press("ArrowDown")                   # move away, then follow the link
    assert state(page)["activeId"] == "1"
    page.goto(url)
    page.wait_for_function("() => window.tractatus.state().activeId === 'root'")
    check_laws(page)


def test_unlabelled_item(links):
    page = links("# Plain\n\n- 1 One\n- An unlabelled second item\n")
    page.keyboard.press("ArrowDown")
    assert state(page)["activeId"] == "p-2"
    page.keyboard.press(LINK)
    url = copied(page)
    assert url == base(page) + "#p-2"
    page.keyboard.press("ArrowUp")
    page.goto(url)
    page.wait_for_function("() => window.tractatus.state().activeId === 'p-2'")


def test_url_untouched(links):
    page = links()
    before = page.evaluate("[history.length, location.href]")
    for key in ("ArrowDown", "ArrowDown", "ArrowUp"):
        page.keyboard.press(LINK)
        page.keyboard.press(key)
    assert page.evaluate("[history.length, location.href]") == before


def test_existing_hash_replaced(links):
    page = links(fragment="#2")
    assert state(page)["activeId"] == "2"
    page.keyboard.press("ArrowUp")
    assert state(page)["activeId"] == "1"
    page.keyboard.press(LINK)
    assert copied(page) == base(page) + "#1"
    assert "#2" not in copied(page)


def test_toast_non_modal(links):
    page = links()
    page.keyboard.press(LINK)
    page.keyboard.press("ArrowDown")
    assert state(page)["activeId"] == "2"
    assert focused_id(page) == "2"
    toast = page.locator("#toast")
    assert toast.get_attribute("role") == "status"
    assert toast.get_attribute("aria-live") == "polite"
    assert toast.get_attribute("tabindex") is None
    assert page.evaluate("document.getElementById('toast').closest('main, [role=tree]')") is None
    assert page.evaluate("document.querySelectorAll('dialog:modal').length") == 0
    check_laws(page)


def test_toast_hides(links):
    page = links()
    page.keyboard.press(LINK)
    toast_says(page, "Link copied")
    page.wait_for_function("() => document.getElementById('toast').hidden", timeout=3000)
    assert page.evaluate("document.getElementById('toast').textContent") == ""
    assert not page.is_visible("#toast")


def test_fallback(links):
    page = links()
    page.evaluate("window.__copyMode = 'reject'")
    page.keyboard.press(LINK)
    toast_says(page, "Link copied")
    assert page.evaluate("window.__fallback") == base(page) + "#1"
    assert copied(page) is None


def test_copy_fails(links):
    page = links()
    page.evaluate("() => { window.__copyMode = 'reject'; document.execCommand = () => false; }")
    page.keyboard.press(LINK)
    toast_says(page, "Could not copy the link")
    assert page.evaluate("window.__fallback") is None


def test_idle_reselects_first(links):
    page = links()
    page.keyboard.press("Escape")
    assert page.evaluate("window.tractatus.selection().mode") == "idle"
    page.keyboard.press(LINK)
    assert copied(page) is None
    assert page.evaluate("window.tractatus.selection().mode") == "selected"
    assert page.is_hidden("#toast")
    page.keyboard.press(LINK)
    assert copied(page) == base(page) + "#1"


def test_range_copies_focus_end(links):
    page = links()
    page.keyboard.press("Shift+ArrowDown")
    sel = page.evaluate("window.tractatus.selection()")
    assert (sel["anchorId"], sel["activeId"]) == ("1", "2")
    page.keyboard.press(LINK)
    assert copied(page) == base(page) + "#2"
    sel = page.evaluate("window.tractatus.selection()")
    assert (sel["anchorId"], sel["activeId"], sel["selected"]) == ("2", "2", ["2"])
    assert focused_id(page) == "2"
    check_laws(page)


SETTLED_STUB = """() => {
  window.__settle = [];
  window.__shown = [];
  Object.defineProperty(navigator, "clipboard", { configurable: true, value: {
    writeText: (t) => new Promise((resolve, reject) => window.__settle.push({ t, resolve, reject })) } });
  new MutationObserver(() => {
    const t = document.getElementById("toast").textContent;
    if (t !== "") window.__shown.push(t);
  }).observe(document.getElementById("toast"), { childList: true, characterData: true, subtree: true });
}"""


def test_stale_result_dropped(links):
    page = links()
    page.evaluate(SETTLED_STUB)
    page.keyboard.press(LINK)                          # on 1: settled later, successfully
    page.keyboard.press("ArrowDown")
    page.evaluate("document.execCommand = () => false")
    page.keyboard.press(LINK)                          # on 2: rejected, and the fallback fails
    assert page.evaluate("window.__settle.map((s) => s.t)") == [base(page) + "#1", base(page) + "#2"]
    page.evaluate("window.__settle[1].reject(new Error('no'))")
    page.evaluate("window.__settle[0].resolve()")
    toast_says(page, "Could not copy the link")
    page.wait_for_timeout(150)
    assert page.evaluate("document.getElementById('toast').textContent") == "Could not copy the link"
    assert page.evaluate("window.__shown") == ["Could not copy the link"]


def test_toast_timers_reset(links):
    page = links()
    page.keyboard.press(LINK)
    toast_says(page, "Link copied")
    page.wait_for_timeout(1500)
    page.keyboard.press(LINK)
    page.wait_for_timeout(1000)                        # 2500 ms after the first copy
    assert page.is_visible("#toast")
    toast_says(page, "Link copied")


PREVENTED_JS = """() => {
  window.__prevented = [];
  addEventListener("keydown", (e) => {
    if (e.code === "KeyC" && e.shiftKey) window.__prevented.push(e.defaultPrevented);
  });
}"""


def test_devtools_chord_consumed(links):
    page = links()
    page.evaluate(PREVENTED_JS)
    page.keyboard.press(LINK)                          # the tree
    assert copied(page) == base(page) + "#1"
    page.keyboard.press("ArrowDown")
    page.evaluate("() => { window.__copied = undefined; document.activeElement.blur(); }")
    assert page.evaluate("document.activeElement === document.body")
    page.keyboard.press(LINK)                          # <body>
    assert copied(page) == base(page) + "#2"
    page.evaluate("window.__copied = undefined")
    page.focus("#help-button")
    page.keyboard.press(LINK)                          # a page-tools button
    assert copied(page) == base(page) + "#2"
    assert page.evaluate("window.__prevented") == [True, True, True]
    check_laws(page)


def test_plain_copy_unchanged(links):
    page = links()
    page.keyboard.press("ArrowRight")
    page.keyboard.press("ArrowRight")
    assert state(page)["activeId"] == "1.1"
    page.evaluate("""() => { window.__copies = [];
      addEventListener("copy", (e) => window.__copies.push(
        [e.defaultPrevented, e.clipboardData.getData("text/plain")])); }""")
    page.keyboard.press(f"{MOD}+c")
    assert page.evaluate("window.__copies") == [[True, "- 1.1 One one\n"]]
    assert copied(page) is None
    assert page.is_hidden("#toast")
