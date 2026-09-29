"""Phase 5 (QoL): find as a filter (law Q, law D amended)."""

import random

import pytest
from conftest import LAWS_JS, check_laws
from test_deep_links import set_hash
from test_tree_keyboard import KEYS, MOD, VISIBLE_PARENTS_JS, click_text, click_toggle, focused_id, state, visible_ids
from test_visual import CONTRAST_LIB
from test_zoom import IN, OUT, zoom

FIND = "ControlOrMeta+f"

# The committed parity fixture (SPEC/tools/parity-fixture.md): positional ids, notes, a wrapped item.
FIXTURE = """\
# Tractatus Logico-Philosophicus

Translated by C. K. Ogden, 1922.

- The world is everything that is the case.

  The decimal figures as numbers of the separate propositions indicate the logical importance of the propositions.
  - The world is the totality of facts, not of things.
    - The world is determined by the facts, and by these being all the facts.
    - For the totality of facts determines both what is the case, and also all that is not the case.
    - The facts in logical space are the world.
  - The world divides into facts.
    - Any one can either be the case or not be the case, and everything else remain the same.
- What is the case, the fact, is the existence of atomic facts.
  - An atomic fact is a combination of objects (entities, things).
    - It is essential to a thing that it can be a constituent part of an atomic fact.
    - In logic nothing is accidental: if a thing can occur in an atomic fact the possibility of that atomic fact must already be prejudged in the thing.
      - It would, so to speak, appear as an accident, when to a thing that could exist alone on its own account, subsequently a state of affairs could be made to fit.

        If things can occur in atomic facts, this possibility must already lie in them.
    - Every thing is, as it were, in a space of possible atomic facts.
      - A spatial object must lie in infinite space.
  - The object is simple.
    - Objects form the substance of the world. Therefore they cannot be compound.
- The logical picture of the facts is the thought.
"""
FACTS_SHOWN = [
    "p-1", "p-1-1", "p-1-1-1", "p-1-1-2", "p-1-1-3", "p-1-2", "p-2", "p-2-1", "p-2-1-2",
    "p-2-1-2-1", "p-2-1-3", "p-3",
]
FACTS_MATCHES = [
    "p-1-1", "p-1-1-1", "p-1-1-2", "p-1-1-3", "p-1-2", "p-2", "p-2-1-2-1", "p-2-1-3", "p-3",
]

# Records whether each find chord's keydown was prevented, after every listener has run.
RECORD_JS = """() => {
  window.__prevented = [];
  addEventListener("keydown", (e) => {
    if (e.key.toLowerCase() === "f" && (e.metaKey || e.ctrlKey)) window.__prevented.push(e.defaultPrevented);
  });
}"""


def find(page):
    return page.evaluate("window.tractatus.find()")


def hidden_ids(page):
    return page.evaluate(
        "[...document.querySelectorAll('[role=treeitem]')].filter((li) => li.hidden).map((li) => li.dataset.id)"
    )


def all_ids(page):
    return page.evaluate("[...document.querySelectorAll('[role=treeitem]')].map((li) => li.dataset.id)")


def box(page):
    return page.evaluate(
        "() => ({ value: document.getElementById('find-input').value,"
        " count: document.getElementById('find-count').textContent })"
    )


def active_element_id(page):
    return page.evaluate("document.activeElement.id")


@pytest.fixture
def outline(open_outline):
    """The parity fixture with the title focused by a click."""
    page = open_outline(FIXTURE)
    click_text(page, "root")
    assert focused_id(page) == "root"
    return page


def type_query(page, text):
    page.fill("#find-input", text)


def test_focus_box(outline):
    page = outline
    page.evaluate(RECORD_JS)
    page.keyboard.press(FIND)
    assert active_element_id(page) == "find-input"
    assert page.evaluate("window.__prevented") == [True]
    check_laws(page)


def test_filter_shown(outline):
    page = outline
    click_toggle(page, "p-2")
    before = state(page)["expanded"]
    type_query(page, "facts")
    f = find(page)
    assert f["shown"] == FACTS_SHOWN
    assert f["matches"] == FACTS_MATCHES
    assert set(hidden_ids(page)) == set(all_ids(page)) - set(FACTS_SHOWN) - {"root"}
    assert visible_ids(page) == ["root", *FACTS_SHOWN]
    assert state(page)["expanded"] == before == ["p-2"]
    check_laws(page)


def test_notes_and_terms(outline):
    page = outline
    type_query(page, "atomic possibility")
    assert find(page)["matches"] == ["p-2-1-2", "p-2-1-2-1"]
    check_laws(page)


def test_case_insensitive(outline):
    page = outline
    type_query(page, "FACTS")
    assert find(page)["shown"] == FACTS_SHOWN
    check_laws(page)


def test_count_announced(outline):
    page = outline
    assert page.get_attribute("#find-count", "aria-live") == "polite"
    assert box(page)["count"] == ""
    type_query(page, "facts")
    assert box(page)["count"] == f"{len(FACTS_MATCHES)} matches"
    type_query(page, "zzz")
    assert box(page)["count"] == "No matches"
    type_query(page, "totality of facts, not")
    assert box(page)["count"] == "1 match"
    check_laws(page)


def moves_into_results(page, key):
    type_query(page, "facts")
    page.keyboard.press(key)
    assert focused_id(page) == state(page)["activeId"] == FACTS_MATCHES[0]
    assert find(page)["query"] == "facts"
    check_laws(page)


def test_enter_moves_into_results(outline):
    moves_into_results(outline, "Enter")


def test_down_moves_into_results(outline):
    moves_into_results(outline, "ArrowDown")


def test_navigation_skips_hidden(outline):
    page = outline
    type_query(page, "facts")
    page.keyboard.press("Enter")
    walked = [state(page)["activeId"]]
    for _ in range(len(FACTS_SHOWN) + 2):
        page.keyboard.press("ArrowDown")
        walked.append(state(page)["activeId"])
    assert walked == FACTS_SHOWN[1:] + ["p-3"] * 4
    check_laws(page)


def test_sibling_step_skips_hidden(outline):
    page = outline
    type_query(page, "facts")
    click_text(page, "p-2-1-2")
    assert state(page)["activeId"] == "p-2-1-2"
    page.keyboard.press(f"Alt+{MOD}+ArrowDown")
    assert state(page)["activeId"] == "p-2-1-3"
    page.keyboard.press(f"Alt+{MOD}+ArrowUp")
    assert state(page)["activeId"] == "p-2-1-2"
    page.keyboard.press(f"Alt+{MOD}+ArrowUp")
    assert state(page)["activeId"] == "p-2-1-2"
    check_laws(page)


def test_bullet_click_while_filtering(outline):
    page = outline
    click_toggle(page, "p-2")
    type_query(page, "facts")
    click_toggle(page, "p-2-1")
    assert state(page) == {"expanded": ["p-2"], "activeId": "p-2-1"}
    assert find(page)["shown"] == FACTS_SHOWN
    check_laws(page)
    page.keyboard.press("Escape")
    assert find(page)["query"] == ""
    assert state(page)["expanded"] == ["p-2"]
    check_laws(page)


def test_url_reveal_clears_query(outline):
    page = outline
    type_query(page, "facts")
    assert "p-2-1-1" not in find(page)["shown"]
    set_hash(page, "#p-2-1-1")
    assert find(page)["query"] == ""
    assert box(page) == {"value": "", "count": ""}
    assert state(page)["activeId"] == "p-2-1-1"
    assert page.locator("#item-p-2-1-1").is_visible()
    check_laws(page)


def test_escape_in_box_restores(outline):
    page = outline
    click_toggle(page, "p-2")
    page.keyboard.press("Home")
    assert state(page) == {"expanded": ["p-2"], "activeId": "root"}
    type_query(page, "facts")
    page.keyboard.press("Escape")
    assert find(page)["query"] == ""
    assert box(page) == {"value": "", "count": ""}
    assert state(page)["expanded"] == ["p-2"]
    assert hidden_ids(page) == []
    assert focused_id(page) == state(page)["activeId"] == "root"
    check_laws(page)


def test_escape_in_tree_restores(outline):
    page = outline
    click_toggle(page, "p-2")
    type_query(page, "facts")
    click_text(page, "p-2-1-3")
    assert state(page)["activeId"] == "p-2-1-3"
    page.keyboard.press("Escape")
    assert find(page)["query"] == ""
    assert state(page) == {"expanded": ["p-2"], "activeId": "p-2-1"}
    assert page.evaluate("window.tractatus.selection().mode") == "selected"
    page.keyboard.press("Escape")
    assert page.evaluate("window.tractatus.selection().mode") == "idle"
    check_laws(page)


def test_enter_in_tree_accepts(outline):
    page = outline
    type_query(page, "facts")
    click_text(page, "p-2-1-2-1")
    page.keyboard.press("Enter")
    assert find(page)["query"] == ""
    assert box(page)["value"] == ""
    st = state(page)
    assert st["activeId"] == "p-2-1-2-1"
    assert {"p-2", "p-2-1", "p-2-1-2"} <= set(st["expanded"])
    assert page.locator("#item-p-2-1-2-1").is_visible()
    check_laws(page)


def test_expansion_keys_noop(outline):
    page = outline
    type_query(page, "facts")
    click_text(page, "p-2-1")
    before, shown = state(page), find(page)["shown"]
    for key in (f"{MOD}+Period", f"{MOD}+Shift+Period", "Shift+Digit8", f"Alt+{MOD}+Digit2"):
        page.keyboard.press(key)
        assert state(page) == before, key
        assert find(page)["shown"] == shown, key
    check_laws(page)


def test_native_find_second_press(outline):
    page = outline
    page.keyboard.press(FIND)
    assert active_element_id(page) == "find-input"
    page.evaluate(RECORD_JS)
    page.keyboard.press(FIND)
    assert page.evaluate("window.__prevented") == [False]
    assert active_element_id(page) == "find-input"
    check_laws(page)


def test_find_in_dialog_untouched(outline):
    page = outline
    page.keyboard.press("Shift+Slash")
    assert page.get_attribute("#help", "open") is not None
    page.evaluate(RECORD_JS)
    page.keyboard.press(FIND)
    assert page.evaluate("document.getElementById('help').contains(document.activeElement)")
    assert page.evaluate("window.__prevented") == [False]
    page.keyboard.press("Escape")
    check_laws(page)


def highlight_texts(page):
    return page.evaluate(
        "() => { const h = CSS.highlights.get('find'); return h ? [...h].map((r) => r.toString()) : null; }"
    )


def test_highlights(outline):
    page = outline
    type_query(page, "facts")
    # Every occurrence lies in an item (the title and intro hold none), and every item holding
    # one is a match.
    title, intro = FIXTURE.split("\n\n")[:2]
    assert "facts" not in (title + intro).lower()
    expected = FIXTURE.lower().count("facts")
    texts = highlight_texts(page)
    assert len(texts) == expected == page.evaluate("CSS.highlights.get('find').size")
    assert {t.lower() for t in texts} == {"facts"}
    type_query(page, "")
    assert highlight_texts(page) is None
    check_laws(page)


def test_highlight_stable_on_navigation(outline):
    page = outline
    type_query(page, "facts")
    page.keyboard.press("ArrowDown")
    page.evaluate("window.__h = CSS.highlights.get('find')")
    page.keyboard.press("ArrowDown")
    page.keyboard.press("ArrowDown")
    assert page.evaluate("CSS.highlights.get('find') === window.__h")
    type_query(page, "facts world")
    assert page.evaluate("CSS.highlights.get('find') instanceof Highlight")
    assert page.evaluate("CSS.highlights.get('find') !== window.__h")
    check_laws(page)


def test_highlight_unicode(open_outline):
    page = open_outline("# U\n\n- İstanbul facts\n- 𝔸 facts 𝔸\n- other\n")
    type_query(page, "facts")
    assert find(page)["matches"] == ["p-1", "p-2"]
    assert visible_ids(page) == ["root", "p-1", "p-2"]
    texts = highlight_texts(page)
    assert texts and {t.lower() for t in texts} == {"facts"}, texts
    check_laws(page)


def test_ime_composition(outline):
    page = outline
    type_query(page, "fa")
    for key in ("Enter", "ArrowDown", "Escape"):
        prevented = page.evaluate(
            "key => { const e = new KeyboardEvent('keydown', { key, isComposing: true, bubbles: true,"
            " cancelable: true }); document.getElementById('find-input').dispatchEvent(e);"
            " return e.defaultPrevented; }",
            key,
        )
        assert not prevented, key
        assert active_element_id(page) == "find-input", key
        assert find(page)["query"] == "fa", key
    check_laws(page)


def test_find_box_focus_ring(outline):
    page = outline
    page.keyboard.press(FIND)
    assert page.evaluate("getComputedStyle(document.getElementById('find-input')).outlineStyle") == "solid"
    check_laws(page)


HIGHLIGHT_CONTRAST_JS = (
    "() => {"
    + CONTRAST_LIB
    + r"""
  const probe = document.createElement("div");
  document.body.append(probe);
  probe.style.backgroundColor = "var(--match)";
  const out = {};
  for (const token of ["--fg", "--note"]) {
    probe.style.color = `var(${token})`;
    const s = getComputedStyle(probe);
    out[token] = ratio(parse(s.color), parse(s.backgroundColor));
  }
  probe.remove();
  return out;
}"""
)


@pytest.mark.parametrize("scheme", ["light", "dark"])
def test_highlight_contrast(open_outline, page, scheme):
    page.emulate_media(color_scheme=scheme)
    open_outline(FIXTURE)
    ratios = page.evaluate(HIGHLIGHT_CONTRAST_JS)
    assert set(ratios) == {"--fg", "--note"}
    assert all(r >= 4.5 for r in ratios.values()), ratios
    check_laws(page)


def test_no_matches(outline):
    page = outline
    type_query(page, "zzz")
    assert find(page) == {"query": "zzz", "matches": [], "shown": []}
    assert visible_ids(page) == ["root"]
    assert state(page)["activeId"] == "root"
    page.keyboard.press("Enter")
    assert active_element_id(page) == "find-input"
    assert state(page)["activeId"] == "root"
    check_laws(page)


def test_accept_without_filter(outline):
    page = outline
    click_text(page, "p-1")
    before = (state(page), page.evaluate("window.tractatus.selection()"))
    page.keyboard.press("Enter")
    assert (state(page), page.evaluate("window.tractatus.selection()")) == before
    check_laws(page)


LONG = "x" * 76


@pytest.mark.parametrize("width", [320, 560])
def test_head_narrow(open_outline, page, width):
    page.set_viewport_size({"width": width, "height": 700})
    items = "".join(f"    - item {n}\n" for n in range(12))
    open_outline(f"# {LONG}\n\n- 1 {LONG}\n  - 1 {LONG}\n{items}", "#z=p-1-1")
    assert zoom(page) == "p-1-1"
    type_query(page, "item")
    assert box(page)["count"] == "12 matches"
    assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")
    boxes = page.evaluate(
        "() => [...document.querySelectorAll('#find-input, #find-count, #crumbs a, .page-tools button')]"
        ".map((e) => { const r = e.getBoundingClientRect();"
        " return { id: e.id || e.textContent, l: r.left, r: r.right, t: r.top, b: r.bottom }; })"
    )
    assert len(boxes) == 2 + 2 + 3, boxes
    kind = {"find-input": "find", "find-count": "count", "actions-button": "tools", "spacing-button": "tools", "help-button": "tools"}
    rows = {k: [b for b in boxes if kind.get(b["id"], "crumbs") == k] for k in ("tools", "find", "count", "crumbs")}
    # The crumbs scroll sideways in their own line; the rest of the header fits the viewport.
    for b in rows["tools"] + rows["find"] + rows["count"]:
        assert 0 <= b["l"] and b["r"] <= width, b
    solid = rows["tools"] + rows["find"] + rows["crumbs"]
    for i, a in enumerate(solid):
        for b in solid[i + 1 :]:
            overlap = a["l"] < b["r"] and b["l"] < a["r"] and a["t"] < b["b"] and b["t"] < a["b"]
            assert not overlap, (a, b)
    # The count sits inside the box's end, clear of the typed text's room.
    (field,), (count,) = rows["find"], rows["count"]
    assert field["l"] <= count["l"] and count["r"] <= field["r"] and field["t"] <= count["t"] and count["b"] <= field["b"]
    # One row for the box and the tools, then the crumbs directly above the title.
    top_row = rows["tools"] + rows["find"]
    assert max(b["t"] for b in top_row) < min(b["b"] for b in top_row)
    assert min(b["t"] for b in rows["crumbs"]) >= max(b["b"] for b in top_row)
    check_laws(page)


def test_zoom_scope(open_outline):
    page = open_outline(FIXTURE, "#z=p-2")
    type_query(page, "facts")
    f = find(page)
    assert f["matches"] == ["p-2-1-2-1", "p-2-1-3"]
    assert all(id.startswith("p-2-") for id in f["shown"])
    assert f["shown"] == ["p-2-1", "p-2-1-2", "p-2-1-2-1", "p-2-1-3"]
    assert box(page)["count"] == "2 matches"
    check_laws(page)


def assert_cleared(page):
    assert find(page)["query"] == ""
    assert box(page) == {"value": "", "count": ""}
    assert hidden_ids(page) == []
    assert page.evaluate("CSS.highlights.get('find')") is None
    check_laws(page)


def test_zoom_change_clears(open_outline):
    page = open_outline(FIXTURE, "#z=p-2")
    type_query(page, "facts")
    page.keyboard.press("Enter")
    page.keyboard.press(OUT)
    assert zoom(page) == "root"
    assert_cleared(page)

    type_query(page, "facts")
    page.keyboard.press("Enter")
    assert state(page)["activeId"] == "p-1-1"
    page.keyboard.press(IN)
    assert zoom(page) == "p-1-1"
    assert_cleared(page)

    type_query(page, "facts")
    assert find(page)["query"] == "facts"
    page.go_back()
    page.wait_for_function("() => window.tractatus.zoom() === 'root'")
    assert_cleared(page)


def test_state_and_url_untouched(outline):
    page = outline
    before = page.evaluate("[history.length, location.href, Object.keys(window.tractatus.state())]")
    type_query(page, "facts")
    page.keyboard.press("Enter")
    page.keyboard.press("ArrowDown")
    page.keyboard.press("Escape")
    type_query(page, "world")
    type_query(page, "")
    after = page.evaluate("[history.length, location.href, Object.keys(window.tractatus.state())]")
    assert after == before
    check_laws(page)


@pytest.mark.parametrize("seed", [1, 2, 3])
def test_laws_random_while_filtering(outline, seed):
    """Laws Q, S and D hold after every step of a random walk that types queries into the box."""
    page = outline
    rng = random.Random(seed)
    steps = []
    filtered = 0
    for n in range(200):
        kind = rng.choice(["key", "key", "key", "toggle", "row", "type"])
        if kind == "key":
            key = rng.choice([*KEYS, "Enter", FIND])
            steps.append(f"press {key}")
            page.keyboard.press(key)
        elif kind == "toggle":
            parents = page.evaluate(VISIBLE_PARENTS_JS)
            if not parents:
                continue
            id = rng.choice(parents)
            steps.append(f"toggle {id}")
            click_toggle(page, id)
        elif kind == "row":
            id = rng.choice(visible_ids(page))
            steps.append(f"row {id}")
            click_text(page, id)
        else:
            query = rng.choice(["facts", "world", "zzz", ""])
            steps.append(f"type {query!r}")
            type_query(page, query)
        errs = page.evaluate(LAWS_JS)
        assert errs == [], f"seed {seed}, step {n}: {errs}\nsteps: {steps}"
        filtered += find(page)["query"] != ""
    assert filtered > 0, "the walk never filtered"


def test_typing_keeps_mode(outline):
    """Typing filters without selecting: an idle page stays idle (compare.py's search state)."""
    page = outline
    page.keyboard.press("Escape")
    assert page.evaluate("window.tractatus.selection().mode") == "idle"
    page.keyboard.press(FIND)
    page.keyboard.type("facts")
    assert find(page)["query"] == "facts"
    assert page.evaluate("window.tractatus.selection()")["selected"] == []
    check_laws(page)
