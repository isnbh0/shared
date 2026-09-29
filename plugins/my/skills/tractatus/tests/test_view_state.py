"""Per-document view state: expansion and the active item survive a reload, per document."""

import json
from urllib.parse import urlparse

import pytest
from conftest import check_laws
from test_spacing_panel import KEY as SPACING_KEY
from test_spacing_panel import open_panel, set_knob
from test_tree_keyboard import state

PREFIX = "my-tractatus:view:"
INDEX = "my-tractatus:view-index"
READY = "() => document.documentElement.dataset.outlineReady === 'true'"
DEFAULT = {"expanded": [], "activeId": "1"}

VIEW_MD = """\
# View

- 1 One
  - 1.1 One one
    - 1.1.1 Leaf
  - 1.2 One two
- 2 Two
  - 2.1 Two one
- 3 Three
"""

STORED_JS = f"""() => Object.fromEntries(Object.keys(localStorage)
  .filter((k) => k.startsWith({json.dumps(PREFIX)}))
  .map((k) => [k.slice({len(PREFIX)}), JSON.parse(localStorage.getItem(k))]))"""


def fnv1a32hex(text: str) -> str:
    h = 0x811C9DC5
    for byte in text.encode("utf-8"):
        h = ((h ^ byte) * 0x01000193) & 0xFFFFFFFF
    return f"{h:08x}"


def view_hash(path, title: str) -> str:
    """The page's key hash: location.pathname is the percent-encoded path of the file URL."""
    return fnv1a32hex(urlparse(path.as_uri()).path + "\n" + title)


def stored(page) -> dict:
    """Every view record, by hash."""
    return page.evaluate(STORED_JS)


def index(page):
    raw = page.evaluate(f"localStorage.getItem({json.dumps(INDEX)})")
    return None if raw is None else json.loads(raw)


def go(page, url):
    page.goto(url)
    page.wait_for_function(READY)
    return page


def reload(page):
    page.reload()
    page.wait_for_function(READY)


def reopen(page, url):
    """A new document load: a goto that only changes the fragment would not rerun main."""
    page.goto("about:blank")
    return go(page, url)


def pagehide(page):
    page.evaluate("dispatchEvent(new Event('pagehide'))")


def seed(page, items: dict[str, str]):
    """Writes raw localStorage values before the first file:// page's scripts run, once."""
    page.add_init_script(
        "(() => { if (location.protocol !== 'file:' || sessionStorage.getItem('seeded')) return;"
        " sessionStorage.setItem('seeded', '1');"
        f" for (const [k, v] of Object.entries({json.dumps(items)})) localStorage.setItem(k, v); }})();"
    )


def record(expanded, active_id, zoom_id="root") -> str:
    return json.dumps({"v": 1, "expanded": expanded, "activeId": active_id, "zoomId": zoom_id})


@pytest.fixture
def view(build_page, page, console_errors):
    """The VIEW_MD page (not yet opened) and its view hash."""
    path = build_page(VIEW_MD)
    return path, view_hash(path, "View")


def expand_to_leaf(page):
    """Expand 1 and 1.1 and select 1.1.1, by keyboard."""
    for _ in range(4):
        page.keyboard.press("ArrowRight")


def test_restores_after_reload(view, page):
    path, h = view
    go(page, path.as_uri())
    expand_to_leaf(page)
    want = {"expanded": ["1", "1.1"], "activeId": "1.1.1"}
    assert state(page) == want
    reload(page)
    assert state(page) == want
    assert page.evaluate("document.activeElement.id") == "item-1_1_1"
    check_laws(page)
    # The record's format and key (the hash computed independently here).
    got = stored(page)
    assert list(got) == [h]
    assert sorted(got[h]["expanded"]) == ["1", "1.1"]
    assert {k: v for k, v in got[h].items() if k != "expanded"} == {"v": 1, "activeId": "1.1.1", "zoomId": "root"}
    assert index(page) == [h]


def test_default_is_not_stored(view, page):
    path, h = view
    go(page, path.as_uri())
    page.keyboard.press("ArrowDown")
    page.wait_for_timeout(450)                  # past the debounce: the record is written
    assert stored(page)[h]["activeId"] == "2"
    page.keyboard.press("ArrowUp")              # back to the default view: the record goes
    reload(page)
    assert stored(page) == {}
    assert index(page) == []
    assert state(page) == DEFAULT


def test_plain_load_writes_nothing(view, page):
    path, h = view
    seed(page, {PREFIX + h: record(["1"], "1.2")})
    page.add_init_script(
        "window.__sets = []; const set = Storage.prototype.setItem;"
        " Storage.prototype.setItem = function (k, v) { window.__sets.push(k); return set.call(this, k, v); };"
    )
    go(page, path.as_uri())
    assert state(page) == {"expanded": ["1"], "activeId": "1.2"}
    page.wait_for_timeout(450)
    pagehide(page)
    sets = page.evaluate("window.__sets")
    assert [k for k in sets if k.startswith("my-tractatus:view")] == []
    check_laws(page)


def test_debounce_and_pagehide(view, page):
    path, h = view
    go(page, path.as_uri())
    page.keyboard.press("ArrowRight")
    assert stored(page) == {}                   # debounced: not yet written
    pagehide(page)                              # flushed synchronously
    got = stored(page)
    assert list(got) == [h]
    assert got[h]["expanded"] == ["1"]
    page.wait_for_timeout(450)                  # the flushed save is not repeated
    assert index(page) == [h]


def test_visibility_hidden_flushes(view, page):
    path, h = view
    go(page, path.as_uri())
    page.keyboard.press("ArrowRight")
    page.evaluate(
        "Object.defineProperty(document, 'visibilityState', { value: 'hidden', configurable: true });"
        " document.dispatchEvent(new Event('visibilitychange'))"
    )
    assert stored(page)[h]["expanded"] == ["1"]


def select_2_expanded(page):
    page.keyboard.press("ArrowDown")
    page.keyboard.press("ArrowRight")
    assert state(page) == {"expanded": ["2"], "activeId": "2"}


def test_fragment_wins(view, page):
    path, _ = view
    go(page, path.as_uri())
    select_2_expanded(page)
    reopen(page, path.as_uri() + "#1.1.1")
    assert state(page) == {"expanded": ["1", "1.1", "2"], "activeId": "1.1.1"}
    assert page.evaluate("document.activeElement.id") == "item-1_1_1"
    check_laws(page)


def test_unknown_fragment_keeps_stored(view, page):
    path, _ = view
    go(page, path.as_uri())
    select_2_expanded(page)
    reopen(page, path.as_uri() + "#9.9")
    assert state(page) == {"expanded": ["2"], "activeId": "2"}
    assert page.text_content("#status") == "No item “9.9” in this outline."
    check_laws(page)


def test_zoom_restored(view, page):
    path, h = view
    go(page, path.as_uri())
    page.keyboard.press("ArrowRight")
    page.keyboard.press("ArrowRight")
    page.keyboard.press("ControlOrMeta+BracketRight")
    assert page.evaluate("window.tractatus.zoom()") == "1.1"
    pagehide(page)
    assert stored(page)[h]["zoomId"] == "1.1"
    page.add_init_script("window.__length = history.length")
    reopen(page, path.as_uri())
    assert page.evaluate("window.tractatus.zoom()") == "1.1"
    assert page.evaluate("location.hash") == "#z=1.1"
    assert page.evaluate("history.length") == page.evaluate("window.__length")
    assert state(page) == {"expanded": ["1"], "activeId": "1.1"}
    check_laws(page)


def test_hash_beats_stored_zoom(view, page):
    path, h = view
    seed(page, {PREFIX + h: record(["1"], "1.1", "1.1")})
    go(page, path.as_uri() + "#2")
    assert page.evaluate("window.tractatus.zoom()") == "root"
    assert state(page)["activeId"] == "2"
    check_laws(page)


def test_unknown_hash_keeps_stored_zoom(view, page):
    path, h = view
    seed(page, {PREFIX + h: record(["1"], "1.1", "1.1")})
    go(page, path.as_uri() + "#9.9")
    assert page.evaluate("window.tractatus.zoom()") == "1.1"
    assert page.text_content("#status") == "No item “9.9” in this outline."
    assert page.evaluate("location.hash") == "#9.9"
    check_laws(page)


def test_restored_zoom_writes_nothing(view, page):
    """A zoom restored on load is what storage already holds: nothing is written."""
    path, h = view
    seed(page, {PREFIX + h: record(["1"], "1.1", "1.1")})
    page.add_init_script(
        "window.__sets = []; const set = Storage.prototype.setItem;"
        " Storage.prototype.setItem = function (k, v) { window.__sets.push(k); return set.call(this, k, v); };"
    )
    go(page, path.as_uri())
    assert page.evaluate("window.tractatus.zoom()") == "1.1"
    page.wait_for_timeout(450)
    pagehide(page)
    assert [k for k in page.evaluate("window.__sets") if k.startswith("my-tractatus:view")] == []
    check_laws(page)


def test_per_document(build_page, page, console_errors):
    a = build_page(VIEW_MD, "a.html")
    b = build_page(VIEW_MD.replace("# View", "# Other").replace("Three", "Drei"), "b.html")
    go(page, a.as_uri())
    select_2_expanded(page)
    reopen(page, b.as_uri())
    assert state(page) == DEFAULT
    reopen(page, a.as_uri())
    assert state(page) == {"expanded": ["2"], "activeId": "2"}


def test_same_path_new_title(view, page, build_page):
    path, _ = view
    go(page, path.as_uri())
    select_2_expanded(page)
    build_page(VIEW_MD.replace("# View", "# Renamed"))   # the same page.html, another document
    reload(page)
    assert state(page) == DEFAULT


@pytest.mark.parametrize(
    ("expanded", "active", "want"),
    [
        (["9", "x.y"], "9.9", DEFAULT),                                       # unknown ids
        (["1", "1.1.1", "3"], "1.2", {"expanded": ["1"], "activeId": "1.2"}),  # leaves
        (["1"], "1.1.1", {"expanded": ["1"], "activeId": "1.1"}),              # hidden active
        (["root", "2"], "2.1", {"expanded": ["2"], "activeId": "2.1"}),        # the root
    ],
    ids=["unknown", "leaf", "collapsed-active", "root"],
)
def test_stale_ids(view, page, expanded, active, want):
    path, h = view
    seed(page, {PREFIX + h: record(expanded, active)})
    go(page, path.as_uri())
    assert state(page) == want
    check_laws(page)


@pytest.mark.parametrize(
    ("raw", "want"),
    [
        ("not json{", DEFAULT),
        ("null", DEFAULT),
        ("[]", DEFAULT),
        ('{"v":2,"expanded":["1"],"activeId":"1.1"}', DEFAULT),
        ('{"v":1,"expanded":"1"}', DEFAULT),
        ('{"v":1,"expanded":[1,null,"1"],"activeId":7}', {"expanded": ["1"], "activeId": "1"}),
    ],
    ids=["not-json", "null", "array", "v2", "expanded-string", "mixed-types"],
)
def test_garbage_records(view, page, raw, want):
    path, h = view
    seed(page, {PREFIX + h: raw})
    go(page, path.as_uri())
    assert state(page) == want
    check_laws(page)


def test_storage_unavailable(view, page):
    path, _ = view
    page.add_init_script(
        "Object.defineProperty(window, 'localStorage', { get() {"
        " throw new DOMException('The operation is insecure.', 'SecurityError'); } });"
    )
    go(page, path.as_uri())
    expand_to_leaf(page)
    page.wait_for_timeout(450)
    reload(page)
    assert state(page) == DEFAULT
    check_laws(page)


def test_quota(view, page):
    path, _ = view
    page.add_init_script(
        "const set = Storage.prototype.setItem;"
        " Storage.prototype.setItem = function (k, v) {"
        "  if (String(k).startsWith('my-tractatus:view'))"
        "   throw new DOMException('The quota has been exceeded.', 'QuotaExceededError');"
        "  return set.call(this, k, v); };"
    )
    go(page, path.as_uri())
    expand_to_leaf(page)
    page.wait_for_timeout(450)
    assert state(page) == {"expanded": ["1", "1.1"], "activeId": "1.1.1"}
    reload(page)
    assert state(page) == DEFAULT
    page.keyboard.press("ArrowRight")
    assert state(page) == {"expanded": ["1"], "activeId": "1"}
    check_laws(page)


FAKES = [f"fake{i:04d}" for i in range(50)]


def seed_fakes(page, h, listed):
    items = {PREFIX + f: record(["1"], "1.1") for f in FAKES}
    items[INDEX] = json.dumps(listed)
    seed(page, items)


def test_lru_limit(view, page):
    path, h = view
    seed_fakes(page, h, FAKES)
    go(page, path.as_uri())
    page.keyboard.press("ArrowRight")
    pagehide(page)
    got = index(page)
    assert got == FAKES[1:] + [h]
    assert set(stored(page)) == set(got)


def test_index_reconciled(view, page):
    path, h = view
    listed = [FAKES[45], "ghost000", *FAKES[40:], 7]   # a duplicate, a missing record, a non-string
    seed_fakes(page, h, listed)
    go(page, path.as_uri())
    page.keyboard.press("ArrowRight")
    pagehide(page)
    got = index(page)
    assert len(got) == 50 and len(set(got)) == 50
    assert got[-1] == h
    assert got[-11:-1] == FAKES[40:]                      # listed order kept, last occurrence wins
    assert "ghost000" not in got
    assert set(stored(page)) == set(got)                  # exactly 50 records, all indexed


def test_spacing_key_unchanged(view, page):
    path, h = view
    go(page, path.as_uri())
    open_panel(page)
    set_knob(page, "itemGap", 20)
    page.keyboard.press("Escape")
    page.keyboard.press("ArrowRight")
    pagehide(page)
    spacing = json.loads(page.evaluate(f"localStorage.getItem({json.dumps(SPACING_KEY)})"))
    assert spacing == {"fontSize": 20, "lh": 1.5, "itemGap": 20, "indent": 30, "column": 820}
    assert stored(page)[h]["expanded"] == ["1"]
    keys = page.evaluate("Object.keys(localStorage).sort()")
    assert keys == sorted([SPACING_KEY, INDEX, PREFIX + h])
