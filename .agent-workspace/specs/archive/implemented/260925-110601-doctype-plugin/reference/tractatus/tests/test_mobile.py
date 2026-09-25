"""Phones and touch screens: laws M1-M7, in Chromium and WebKit under device emulation.

M1 reflow: nothing scrolls sideways from 320px up; only wide math and the crumb trail scroll
    themselves. M2 no overprint: labels and bullets sit on the first line's baseline. M3 minimum
    measure: every row keeps 16ch of text at 320px. M4 targets: 24px everywhere, 44px under a
    coarse pointer, measured by hit testing. M5 registry: one KEYMAP lists keys, touch help and
    the ⋯ menu. M6 no hover-only controls, pinch zoom kept, 16px inputs. M7 zoom is history.
"""

import re

import pytest
from conftest import FIXTURES, LAWS_JS, NETWORK, SKILL_DIR, embed, template_text
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

ENGINES = ["chromium", "webkit"]
# name: (Playwright device, overrides)
DEVICES = {
    "w320": ("iPhone SE", {"viewport": {"width": 320, "height": 568}}),
    "ip15": ("iPhone 15 Pro", {}),
    "pixel7": ("Pixel 7", {}),
    "land": ("iPhone 15 Pro landscape", {"viewport": {"width": 734, "height": 343}}),
    "ipad": ("iPad Mini", {}),
    "desk": (None, {"viewport": {"width": 1280, "height": 800}}),
}
TOUCH = ["w320", "ip15", "pixel7"]
DEEPEST = ".".join(["1"] * 13)
WIDTHS = list(range(320, 1401, 20))
LANDSCAPES = [(568, 320), (734, 343), (844, 390)]
SCROLLERS = ".math.wide, #crumbs ol"   # the only elements allowed to overflow: they scroll


# ── harness ───────────────────────────────────────────────
@pytest.fixture(scope="session")
def docs(tmp_path_factory):
    """The example and the stress outline, built from the current template."""
    out = tmp_path_factory.mktemp("mobile")
    paths = {}
    for name, md in [("example", SKILL_DIR / "examples" / "tractatus.md"), ("stress", FIXTURES / "stress.md")]:
        path = out / f"{name}.html"
        path.write_text(embed.embed(md.read_text(encoding="utf-8"), template_text()), encoding="utf-8", newline="")
        paths[name] = path
    return paths


@pytest.fixture(scope="module", params=ENGINES)
def engine(request, playwright):
    browser = getattr(playwright, request.param).launch()
    yield browser
    browser.close()


def settle(page):
    page.wait_for_function("() => document.documentElement.dataset.outlineReady === 'true'")
    page.wait_for_function(
        "() => !document.querySelector('.math') || !['loading', undefined].includes(document.documentElement.dataset.mathState)",
        timeout=30_000,
    )
    frames(page)


def frames(page, n=2):
    page.evaluate(f"() => new Promise((ok) => {{ let n = {n}; const f = () => (--n ? requestAnimationFrame(f) : ok()); requestAnimationFrame(f); }})")


@pytest.fixture
def phone(engine, playwright, docs, request):
    """open(doc, device, fragment): a page in a fresh emulated context. Law N as in conftest."""
    network = request.node.get_closest_marker("network") is not None
    contexts, errors = [], []

    def _open(doc="example", device="ip15", fragment="", init=(), **over):
        name, base = DEVICES[device]
        options = dict(playwright.devices[name]) if name else {}
        options.pop("default_browser_type", None)
        options.update(base)
        options.update(over)
        context = engine.new_context(**options)
        contexts.append(context)
        if not network:
            context.route(re.compile(r"^(?!file:).*"), lambda r: r.abort())
        context.set_default_timeout(5000)
        page = context.new_page()
        for script in init:
            page.add_init_script(script)
        page.on("pageerror", lambda e: errors.append(str(e)))
        page.on("console", lambda m: m.type == "error" and "ERR_FAILED" not in m.text
                and "Failed to load resource" not in m.text and errors.append(m.text))
        page.goto(docs[doc].as_uri() + fragment)
        settle(page)
        return page

    yield _open
    for context in contexts:
        context.close()
    assert errors == []


def laws(page):
    assert page.evaluate(LAWS_JS) == []


def css_id(id):
    return "#item-" + id.replace(".", "_")


def state(page):
    return page.evaluate("window.tractatus.state()")


def mode(page):
    return page.evaluate("window.tractatus.selection().mode")


def expand_all(page):
    """⋯ › Expand all on the page: every item open."""
    if mode(page) == "selected":                 # nothing selected: the menu acts on the page
        page.focus('[role=treeitem][tabindex="0"]')
        page.keyboard.press("Escape")
        assert mode(page) == "idle"
    tap(page, "#actions-button")
    tap(page, '#actions [data-command="toggleSubtree"]')
    frames(page)
    assert page.evaluate("[...document.querySelectorAll('[role=treeitem][aria-expanded=false]')].every((li) => !li.checkVisibility())")


def tap(page, selector, **kw):
    """A tap where the device has touch, else a click."""
    loc = page.locator(selector).first
    if page.evaluate("matchMedia('(any-pointer: coarse)').matches"):
        loc.tap(**kw)
    else:
        loc.click(**kw)
    frames(page, 1)


def deepest_parent(page):
    return page.evaluate("""() => { let best = null, depth = -1;
      for (const li of document.querySelectorAll('[role=treeitem]')) {
        let d = 0; for (let e = li; e; e = e.parentElement.closest('[role=treeitem]')) d += 1;
        if (d > depth) { depth = d; best = li; } }
      return best.parentElement.closest('[role=treeitem]').dataset.id; }""")


OVERFLOW_JS = """(scrollers) => {
  const vw = document.documentElement.clientWidth;
  const bad = [];
  if (document.documentElement.scrollWidth > vw) bad.push(`page scrollWidth ${document.documentElement.scrollWidth} > ${vw}`);
  for (const el of document.querySelectorAll('body *')) {
    const r = el.getBoundingClientRect();
    if (r.width === 0 || r.height === 0) continue;
    const s = el.closest(scrollers);
    if (s !== null && s !== el) continue;          // clipped by its own scroller
    if (el.parentElement.closest('mjx-assistive-mml')) continue;   // MathJax's 1px clipped copy for screen readers
    if (s === el && !['auto', 'scroll'].includes(getComputedStyle(el).overflowX)) bad.push(`scroller ${el.className} overflow-x ${getComputedStyle(el).overflowX}`);
    if (r.right > vw + 0.5 || r.left < -0.5)
      bad.push(`${el.tagName.toLowerCase()}#${el.id}.${el.className} [${Math.round(r.left)}, ${Math.round(r.right)}] > ${vw}`);
  }
  return bad.slice(0, 8);
}"""


def overflow(page):
    return page.evaluate(OVERFLOW_JS, SCROLLERS)


def sweep(page, sizes):
    failures = {}
    for w, h in sizes:
        page.set_viewport_size({"width": w, "height": h})
        frames(page)
        bad = overflow(page)
        if bad:
            failures[f"{w}x{h}"] = bad
    return failures


# ── M1 reflow ─────────────────────────────────────────────
def reflow(phone, doc, view, pointer):
    page = phone(doc, "ip15" if pointer == "coarse" else "desk")
    if view != "collapsed":
        expand_all(page)
    if view == "zoomed":
        page.evaluate("(id) => { location.hash = 'z=' + id; }", deepest_parent(page))
        frames(page)
        assert page.evaluate("window.tractatus.zoom()") != "root"
    sizes = [(w, 800) for w in WIDTHS] + LANDSCAPES
    assert sweep(page, sizes) == {}
    laws(page)


@pytest.mark.parametrize("pointer", ["fine", "coarse"])
@pytest.mark.parametrize("view", ["collapsed", "expanded", "zoomed"])
@pytest.mark.parametrize("doc", ["example", "stress"])
def test_m1_reflow(phone, doc, view, pointer):
    reflow(phone, doc, view, pointer)


@pytest.mark.network
@pytest.mark.parametrize("pointer", ["fine", "coarse"])
@pytest.mark.parametrize("doc", ["example", "stress"])
def test_m1_reflow_typeset(phone, doc, pointer):
    """With real MathJax, math wider than its line scrolls by itself."""
    reflow(phone, doc, "expanded", pointer)
    page = phone(doc, "w320")
    expand_all(page)
    assert page.evaluate("document.documentElement.dataset.mathState") == "ready"
    assert page.locator(".math.wide").count() >= 1
    assert page.evaluate("[...document.querySelectorAll('.math.wide')].every((m) => m.tabIndex === -1)")


def test_m1_zoomed_text(phone):
    """Browser text zoom (a larger root font) reflows too: every knob at its maximum."""
    page = phone("stress", "w320")
    page.evaluate("""for (const [k, v] of [['--font-size', '24px'], ['--lh', '1.9'], ['--item-gap', '28px'],
      ['--indent', '56px'], ['--column', '1200px']]) document.documentElement.style.setProperty(k, v)""")
    expand_all(page)
    assert sweep(page, [(320, 568), (360, 640), (568, 320)]) == {}


def test_m1_head_crumbs_scroll(phone):
    page = phone("stress", "w320", fragment="#z=" + DEEPEST)
    ol = page.evaluate("(() => { const ol = document.querySelector('#crumbs ol'); const r = ol.getBoundingClientRect();"
                       " return { sw: ol.scrollWidth, cw: ol.clientWidth, left: ol.scrollLeft, right: r.right }; })()")
    assert ol["sw"] > ol["cw"], "a deep trail overflows its line"
    assert ol["right"] <= 320
    assert ol["left"] >= ol["sw"] - ol["cw"] - 1, "the trail starts scrolled to its nearest crumb"


# ── M2 no overprint ───────────────────────────────────────
ALIGN_JS = """() => [...document.querySelectorAll('[role=treeitem]:not(#item-root)')].filter((li) => li.checkVisibility()).map((li) => {
  const row = li.querySelector(':scope > .row'), toggle = row.querySelector(':scope > .toggle');
  const para = row.querySelector('.para'), label = row.querySelector('.label');
  const line = parseFloat(getComputedStyle(row).lineHeight);
  const t = toggle.getBoundingClientRect(), p = para.getBoundingClientRect();
  const bulletY = t.top + parseFloat(getComputedStyle(toggle).paddingTop) + line / 2;
  const bulletX = t.left + parseFloat(getComputedStyle(toggle).paddingLeft) + parseFloat(getComputedStyle(row).getPropertyValue('--bullet-col') || 22) / 2;
  const base = (host, where) => { const m = document.createElement('span');
    m.style.cssText = 'display:inline-block;inline-size:0;block-size:0'; host[where](m);
    const y = m.getBoundingClientRect().top; m.remove(); return y; };
  const out = { id: li.dataset.id, line, bulletY, bulletX, paraTop: p.top };
  if (label) {
    const l = label.getBoundingClientRect();
    out.label = { left: l.left, right: l.right, top: l.top, bottom: l.bottom };
    out.labelBase = base(label, 'prepend');
    out.textBase = base(label.parentElement, 'after');
    // The first glyphs after the label on its line.
    const walker = document.createTreeWalker(para, NodeFilter.SHOW_TEXT);
    for (let n; (n = walker.nextNode());) {
      if (n.parentElement.closest('.gutter') || !n.data.trim()) continue;
      const r = document.createRange(); r.selectNodeContents(n); const g = r.getClientRects()[0];
      out.glyph = { left: g.left, top: g.top };
      // The first word after the label: one piece (the label's space is a break, not glue).
      const word = n.data.match(/^\s*(\S+)/);
      if (word) { r.setStart(n, word[0].length - word[1].length); r.setEnd(n, word[0].length);
        out.wordLines = new Set([...r.getClientRects()].map((q) => Math.round(q.top))).size; }
      break;
    }
  }
  return out; })"""


@pytest.mark.parametrize("device", ["w320", "ip15", "land", "desk"])
@pytest.mark.parametrize("doc", ["example", "stress"])
def test_m2_no_overprint(phone, doc, device):
    page = phone(doc, device)
    expand_all(page)
    rows = page.evaluate(ALIGN_JS)
    bullets = [(r["bulletX"], r["bulletY"]) for r in rows]
    labelled = 0
    for r in rows:
        # The bullet centres on the first line box.
        assert abs(r["bulletY"] - (r["paraTop"] + r["line"] / 2)) <= 1, r
        if "label" not in r:
            continue
        labelled += 1
        l = r["label"]
        assert abs(r["labelBase"] - r["textBase"]) <= 1, r
        assert r["paraTop"] < r["labelBase"] < r["paraTop"] + r["line"], r     # on the first line
        if "glyph" in r and abs(r["glyph"]["top"] - l["top"]) < r["line"] / 2:
            assert l["right"] <= r["glyph"]["left"] + 0.5, r     # the label ends before its text
        assert r.get("wordLines", 1) == 1, r
        for x, y in bullets:                                      # no label covers a bullet
            assert not (l["left"] - 3 < x < l["right"] + 3 and l["top"] - 3 < y < l["bottom"] + 3), (r["id"], x, y)
    assert labelled >= 10
    assert "-10em" not in template_text()


# ── M3 minimum measure ────────────────────────────────────
MEASURE_JS = """() => [...document.querySelectorAll('.row .text')].filter((t) => t.checkVisibility()).flatMap((t) => {
  const probe = document.createElement('span'); probe.textContent = '0'.repeat(16);
  probe.style.cssText = 'position:absolute;white-space:nowrap'; t.append(probe);
  const ch16 = probe.getBoundingClientRect().width; probe.remove();
  const w = t.getBoundingClientRect().width;
  const label = t.querySelector('.label')?.getBoundingClientRect();
  const bad = [];
  if (w < ch16 - 0.5) bad.push([t.closest('li').dataset.id, 'measure', w, ch16]);
  if (label && label.width > w + 0.5) bad.push([t.closest('li').dataset.id, 'label', label.width, w]);
  return bad; })"""


@pytest.mark.parametrize("device", ["w320", "land"])
@pytest.mark.parametrize("doc", ["example", "stress"])
def test_m3_measure(phone, doc, device):
    page = phone(doc, device)
    expand_all(page)
    depth = page.evaluate("Math.max(...[...document.querySelectorAll('[role=treeitem]')].map((li) => {"
                          " let d = 0; for (let e = li; e; e = e.parentElement.closest('[role=treeitem]')) d += 1; return d; }))")
    assert depth >= (14 if doc == "stress" else 5)
    assert page.evaluate(MEASURE_JS) == []


def test_m3_accessible_name(phone):
    """The label stays in the item's accessible name, on a phone as on a desktop."""
    page = phone("stress", "w320", fragment="#" + DEEPEST)
    item = page.get_by_role("treeitem", name=re.compile("^" + re.escape(DEEPEST) + " Level 13"))
    assert item.count() == 1
    assert item.get_attribute("data-id") == DEEPEST


# ── M4 targets ────────────────────────────────────────────
HIT_JS = """([selector, size, anchor]) => {
const inView = (el, r) => {
  // Wholly visible: inside the viewport and every clipping ancestor, and not under the sticky header.
  if (r.top < 0 || r.left < 0 || r.bottom > innerHeight || r.right > innerWidth) return false;
  for (let a = el.parentElement; a; a = a.parentElement) {
    const cs = getComputedStyle(a);
    if (cs.overflowX === 'visible' && cs.overflowY === 'visible') continue;
    const c = a.getBoundingClientRect();
    if (r.top < c.top - 0.5 || r.left < c.left - 0.5 || r.bottom > c.bottom + 0.5 || r.right > c.right + 0.5) return false;
  }
  const head = document.querySelector('.page-head');
  if (!el.closest('.page-head, dialog') && getComputedStyle(head).position === 'sticky' && r.top < head.getBoundingClientRect().bottom) return false;
  if (!el.closest('dialog') && [...document.querySelectorAll('dialog[open]')].some((d) => { const c = d.getBoundingClientRect();
    return r.bottom > c.top && r.top < c.bottom && r.right > c.left && r.left < c.right; })) return false;
  return true;
};
  // For each target: is there a size×size square around its anchor point (the bullet centre
  // for a toggle, else the box centre) in which every sampled point hits the target itself?
  const out = [];
  for (const el of document.querySelectorAll(selector)) {
    if (!el.checkVisibility()) continue;
    const r = el.getBoundingClientRect();
    if (!inView(el, r)) continue;
    let ax = r.left + r.width / 2, ay = r.top + r.height / 2;
    if (el.classList.contains('toggle')) {
      const cs = getComputedStyle(el), row = getComputedStyle(el.parentElement);
      ax = r.left + parseFloat(cs.paddingLeft) + parseFloat(row.getPropertyValue('--bullet-col')) / 2;
      ay = r.top + parseFloat(cs.paddingTop) + parseFloat(row.lineHeight) / 2;
    }
    const step = 2, n = Math.round(size / step);
    const hits = (x, y) => { const e = document.elementFromPoint(x, y); return e !== null && (e === el || el.contains(e)); };
    const grid = [];   // grid[i][j]: the point (ax + (i - n) * step, ay + (j - n) * step)
    for (let i = 0; i <= 2 * n; i++) { grid.push([]); for (let j = 0; j <= 2 * n; j++) grid[i].push(hits(ax + (i - n) * step, ay + (j - n) * step)); }
    let ok = false;
    for (let i0 = 0; i0 <= n && !ok; i0++) for (let j0 = 0; j0 <= n && !ok; j0++) {
      let all = true;
      for (let i = i0; i <= i0 + n - 1 && all; i++) for (let j = j0; j <= j0 + n - 1 && all; j++) all = grid[i][j];
      ok = all;
    }
    if (!ok) out.push([el.id || el.closest('[data-id]')?.dataset.id || el.textContent.trim().slice(0, 20), el.className, Math.round(r.width), Math.round(r.height)]);
  }
  return out;
}"""

HEAD = "#find-input, .page-tools button, #up-button, #crumbs a"
OVERLAP_JS = """(selector) => {
  // Each target's visible box: its rect clipped by its scrolling ancestors (a crumb scrolled
  // under the Up button is not there to tap).
  const clip = (e) => { let r = e.getBoundingClientRect(); r = { left: r.left, top: r.top, right: r.right, bottom: r.bottom };
    for (let a = e.parentElement; a; a = a.parentElement) { const cs = getComputedStyle(a);
      if (cs.overflowX === 'visible' && cs.overflowY === 'visible') continue;
      const c = a.getBoundingClientRect();
      r = { left: Math.max(r.left, c.left), top: Math.max(r.top, c.top), right: Math.min(r.right, c.right), bottom: Math.min(r.bottom, c.bottom) }; }
    return r; };
  const els = [...document.querySelectorAll(selector)].filter((e) => e.checkVisibility());
  const rs = els.map(clip);
  const bad = [];
  for (let i = 0; i < rs.length; i++) for (let j = i + 1; j < rs.length; j++) {
    const a = rs[i], b = rs[j];
    const w = Math.min(a.right, b.right) - Math.max(a.left, b.left), h = Math.min(a.bottom, b.bottom) - Math.max(a.top, b.top);
    if (w > 0.5 && h > 0.5 && !els[i].contains(els[j]) && !els[j].contains(els[i])) bad.push([els[i].id || els[i].className, els[j].id || els[j].className, w, h]);
  }
  return bad; }"""
STEAL_JS = """() => {
const inView = (el, r) => {
  // Wholly visible: inside the viewport and every clipping ancestor, and not under the sticky header.
  if (r.top < 0 || r.left < 0 || r.bottom > innerHeight || r.right > innerWidth) return false;
  for (let a = el.parentElement; a; a = a.parentElement) {
    const cs = getComputedStyle(a);
    if (cs.overflowX === 'visible' && cs.overflowY === 'visible') continue;
    const c = a.getBoundingClientRect();
    if (r.top < c.top - 0.5 || r.left < c.left - 0.5 || r.bottom > c.bottom + 0.5 || r.right > c.right + 0.5) return false;
  }
  const head = document.querySelector('.page-head');
  if (!el.closest('.page-head, dialog') && getComputedStyle(head).position === 'sticky' && r.top < head.getBoundingClientRect().bottom) return false;
  if (!el.closest('dialog') && [...document.querySelectorAll('dialog[open]')].some((d) => { const c = d.getBoundingClientRect();
    return r.bottom > c.top && r.top < c.bottom && r.right > c.left && r.left < c.right; })) return false;
  return true;
};
  // Each bullet's centre, and each link's centre, hits that bullet or link: no slop steals it.
  const bad = [];
  for (const t of document.querySelectorAll('#outline .toggle')) {
    if (!t.checkVisibility()) continue;
    const r = t.getBoundingClientRect(), cs = getComputedStyle(t), row = getComputedStyle(t.parentElement);
    const x = r.left + parseFloat(cs.paddingLeft) + parseFloat(row.getPropertyValue('--bullet-col')) / 2;
    const y = r.top + parseFloat(cs.paddingTop) + parseFloat(row.lineHeight) / 2;
    if (!inView(t, r)) continue;
    const e = document.elementFromPoint(x, y);
    if (e?.closest('.toggle') !== t) bad.push(['bullet', t.closest('[data-id]').dataset.id, e?.className]);
  }
  for (const a of document.querySelectorAll('#outline a')) {
    for (const r of a.getClientRects()) {
      const x = r.left + r.width / 2, y = r.top + r.height / 2;
      if (!inView(a, r)) continue;
      const e = document.elementFromPoint(x, y);
      if (e?.closest('a') !== a) bad.push(['link', a.textContent.slice(0, 20), e?.className]);
    }
  }
  return bad; }"""


def hit_failures(page, size):
    failures = []
    failures += page.evaluate(HIT_JS, [HEAD, size, "centre"])
    failures += page.evaluate(HIT_JS, ["#outline .toggle", size, "bullet"])
    return failures


@pytest.mark.parametrize("device", TOUCH + ["ipad"])
def test_m4_targets_coarse(phone, device):
    page = phone("stress", device, fragment="#z=1.1.1")   # a crumb trail: Up and crumb links
    assert page.evaluate("matchMedia('(any-pointer: coarse)').matches")
    expand_all(page)
    assert hit_failures(page, 44) == []
    assert page.evaluate(OVERLAP_JS, HEAD) == []
    assert page.evaluate(OVERLAP_JS, "#outline .toggle") == []
    assert page.evaluate(STEAL_JS) == []
    page.evaluate("scrollTo(0, 400)")
    assert page.evaluate(STEAL_JS) == []
    # The sheets' controls.
    tap(page, "#actions-button")
    assert page.evaluate(HIT_JS, ["#actions button", 44, "centre"]) == []
    tap(page, "#spacing-button")
    assert page.evaluate(HIT_JS, ["#spacing button, #spacing input", 44, "centre"]) == []
    tap(page, "#spacing-close")
    tap(page, "#help-button")
    assert page.evaluate(HIT_JS, ["#help button", 44, "centre"]) == []


def test_m4_targets_fine(phone):
    page = phone("stress", "desk", fragment="#z=1.1.1")
    assert not page.evaluate("matchMedia('(any-pointer: coarse)').matches")
    expand_all(page)
    assert hit_failures(page, 24) == []
    assert page.evaluate(STEAL_JS) == []
    page.click("#actions-button")
    assert page.evaluate(HIT_JS, ["#actions button", 24, "centre"]) == []


# ── M5 registry ───────────────────────────────────────────
SHARE_STUB = "navigator.share = (data) => { window.__shared = data; return Promise.resolve(); };"
CLIPBOARD_STUB = """Object.defineProperty(navigator, "clipboard", { configurable: true, value: {
  writeText: (t) => { window.__copied = t; return Promise.resolve(); } } });"""


def commands(page):
    return {c["command"]: c for c in page.evaluate("window.tractatus.commands()")}


def test_m5_registry(phone):
    page = phone("example", "ip15", init=[SHARE_STUB])
    cmds = commands(page)
    for name, c in cmds.items():
        if c["touch"] is False:
            assert name in {"extendUp", "extendDown", "extendFirst", "extendLast", "selectTo"}, name
            assert c["reason"], name
        else:
            assert c["gesture"], f"{name} has no touch gesture and no reason"
    # Help lists every chord and every gesture; the menu lists every menu entry.
    tap(page, "#help-button")
    keys = page.locator("#help .keys dd").all_text_contents()
    touch = page.locator("#help .touch dt").all_text_contents()
    assert set(touch) == {c["gesture"] for c in cmds.values() if c["gesture"]}
    assert len(keys) == sum(1 for c in cmds.values() if c["keys"])
    page.keyboard.press("Escape")
    tap(page, "#actions-button")
    shown = page.eval_on_selector_all("#actions [data-command]", "(bs) => [...new Set(bs.map((b) => b.dataset.command))]")
    menu = {n for n, c in cmds.items() if c["menu"]}
    assert set(shown) == menu - {"accept"}, "accept only shows while finding"


def open_menu_run(page, command):
    tap(page, "#actions-button")
    tap(page, f'#actions button[data-command="{command}"]')


def select(page, id):
    tap(page, f"{css_id(id)} > .row .text", position={"x": 60, "y": 10})
    assert state(page)["activeId"] == id


def tap_bullet(page, id):
    tap(page, f"{css_id(id)} > .row > .toggle")


# One scenario per touch command: the gesture the help lists, then what it must do.
def g_select(page):
    select(page, "2")
    assert mode(page) == "selected"


def g_bullet(page):
    tap_bullet(page, "1")
    assert "1" in state(page)["expanded"] and state(page)["activeId"] == "1"
    tap_bullet(page, "1")
    assert "1" not in state(page)["expanded"]


def g_first(page):
    tap(page, "#doc-title")
    assert state(page)["activeId"] == "root"


def g_menu(command, check, prepare=lambda p: select(p, "1")):
    def run(page):
        prepare(page)
        open_menu_run(page, command)
        frames(page)
        assert check(page), command
    return run


def g_expand_level(page):
    select(page, "1")
    tap(page, "#actions-button")
    tap(page, '#actions button[data-step="1"]')
    tap(page, '#actions button[data-step="1"]')
    assert page.text_content("#actions .level output") == "3"
    assert page.is_visible(css_id("1.11"))
    assert page.is_visible("#actions"), "the stepper keeps the menu open"


def g_zoom_out(page):
    page.evaluate("location.hash = 'z=1.1'")
    frames(page)
    tap(page, "#up-button")
    assert page.evaluate("window.tractatus.zoom()") == "1"
    page.go_back()
    frames(page)
    assert page.evaluate("window.tractatus.zoom()") == "1.1"
    tap(page, '#crumbs a[data-id="root"], #crumbs li:first-child a')
    assert page.evaluate("window.tractatus.zoom()") == "root"


def g_link(page):
    page.evaluate("location.hash = 'z=5.3'")      # 5.31 links to 4.31
    frames(page)
    tap_bullet(page, "5.31") if not page.is_visible('#outline a[href="#4.31"]') else None
    page.locator('#outline a[href="#4.31"]').tap()
    frames(page)
    assert page.evaluate("window.tractatus.zoom()") == "4.31"


def g_find(page):
    tap(page, "#find-input")
    page.keyboard.type("logic")
    frames(page)
    assert page.evaluate("window.tractatus.find().matches.length") > 0
    open_menu_run(page, "escape")
    assert page.evaluate("window.tractatus.find().query") == ""


def g_accept(page):
    tap(page, "#find-input")
    page.keyboard.type("logic")
    frames(page)
    first = page.evaluate("window.tractatus.find().matches[0]")
    select(page, first)
    open_menu_run(page, "accept")
    assert page.evaluate("window.tractatus.find().query") == ""
    assert state(page)["activeId"] == first


def g_help(page):
    tap(page, "#help-button")
    assert page.evaluate("document.getElementById('help').open")
    page.keyboard.press("Escape")
    open_menu_run(page, "help")
    assert page.evaluate("document.getElementById('help').open")


def expanded(page, id):
    return id in state(page)["expanded"]


TAPS = {
    "prev": g_select, "next": g_select, "last": g_select, "prevSibling": g_select, "nextSibling": g_select,
    "first": g_first,
    "right": g_bullet, "left": g_bullet,
    "toggle": g_menu("toggle", lambda p: expanded(p, "1")),
    "toggleSubtree": g_menu("toggleSubtree", lambda p: expanded(p, "1") and expanded(p, "1.1")),
    "expandSiblings": g_menu("expandSiblings", lambda p: all(expanded(p, i) for i in ["1", "2", "3"])),
    "expandLevel": g_expand_level,
    "copyLink": g_menu("copyLink", lambda p: p.evaluate("window.__copied").endswith("#1")),
    "share": g_menu("share", lambda p: p.evaluate("window.__shared.url").endswith("#1")),
    "copy": g_menu("copy", lambda p: p.evaluate("window.__copied").startswith("- 1 ")),
    "escape": g_menu("escape", lambda p: mode(p) == "idle"),
    "zoomIn": g_menu("zoomIn", lambda p: p.evaluate("window.tractatus.zoom()") == "1"),
    "zoomClick": g_menu("zoomIn", lambda p: p.evaluate("window.tractatus.zoom()") == "1"),
    "zoomOut": g_zoom_out,
    "linkClick": g_link,
    "find": g_find,
    "accept": g_accept,
    "help": g_help,
}


def test_m5_every_touch_command_is_tested(phone):
    page = phone("example", "ip15", init=[SHARE_STUB])
    assert set(TAPS) == {n for n, c in commands(page).items() if c["touch"] is not False}


@pytest.mark.parametrize("command", sorted(TAPS))
def test_m5_tap(phone, command):
    page = phone("example", "ip15", init=[SHARE_STUB, CLIPBOARD_STUB])
    result = TAPS[command](page)
    assert result is None
    laws(page)


# ── M6 touch hygiene ──────────────────────────────────────
HOVER_JS = """() => {
  const bad = [];
  const walk = (rules, gated) => { for (const r of rules) {
    if (r instanceof CSSMediaRule) walk(r.cssRules, gated || /hover:\\s*hover/.test(r.conditionText));
    else if (r.cssRules) walk(r.cssRules, gated);
    if (r.selectorText && r.selectorText.includes(':hover') && !gated) bad.push(r.selectorText);
  } };
  for (const s of document.styleSheets) walk(s.cssRules, false);
  return bad; }"""


def test_m6_touch_hygiene(phone):
    page = phone("example", "ip15")
    assert page.evaluate("matchMedia('(hover: none)').matches")
    assert page.evaluate(HOVER_JS) == []
    assert page.locator("[title]").count() == 0, "no tooltip-only information"
    meta = page.get_attribute('meta[name="viewport"]', "content")
    assert "user-scalable" not in meta and "maximum-scale" not in meta
    expand_all(page)
    locked = page.evaluate("[...document.querySelectorAll('main *, .page-head *')].filter((e) =>"
                           " !['auto', 'manipulation'].includes(getComputedStyle(e).touchAction)).map((e) => e.className)")
    assert locked == []
    tap(page, "#spacing-button")
    sizes = page.evaluate("[...document.querySelectorAll('input:not([type=range]), select, textarea')].map((e) => parseFloat(getComputedStyle(e).fontSize))")
    assert sizes and min(sizes) >= 16, "iOS zooms into a text field under 16px"


# ── M7 zoom is history ────────────────────────────────────
def test_m7_zoom_history(phone):
    page = phone("example", "ip15")
    select(page, "2")
    before = page.evaluate("history.length")
    open_menu_run(page, "zoomIn")
    assert page.evaluate("window.tractatus.zoom()") == "2"
    assert page.evaluate("location.hash") == "#z=2"
    assert page.evaluate("history.length") == before + 1
    page.go_back()
    frames(page)
    assert page.evaluate("window.tractatus.zoom()") == "root"
    page.go_forward()
    frames(page)
    assert page.evaluate("window.tractatus.zoom()") == "2"
    page.reload()
    settle(page)
    assert page.evaluate("[window.tractatus.zoom(), location.hash]") == ["2", "#z=2"]


# ── sheets, help, start, header ───────────────────────────
def sheet_rect(page, id):
    return page.evaluate(f"(() => {{ const r = document.getElementById('{id}').getBoundingClientRect(); return {{ top: r.top, bottom: r.bottom, left: r.left, right: r.right }}; }})()")


@pytest.mark.parametrize("device", ["w320", "ip15", "land", "ipad"])
def test_sheets_touch(phone, device):
    page = phone("example", device)
    vw, vh = page.evaluate("[innerWidth, innerHeight]")
    tap(page, "#actions-button")
    assert page.get_attribute("#actions-button", "aria-expanded") == "true"
    assert page.evaluate("document.activeElement.id") == "actions", "a touch reader starts at the top of the sheet"
    r = sheet_rect(page, "actions")
    assert abs(r["bottom"] - vh) <= 1 and r["top"] >= 0 and r["left"] >= 0 and r["right"] <= vw, r
    tap(page, "#spacing-button")
    assert page.evaluate("[document.getElementById('actions').open, document.getElementById('spacing').open]") == [False, True]
    assert page.get_attribute("#actions-button", "aria-expanded") == "false"
    r = sheet_rect(page, "spacing")
    assert abs(r["bottom"] - vh) <= 1 and r["top"] >= vh / 2 - 1, r
    # A tap outside closes a bottom sheet.
    page.touchscreen.tap(vw / 2, 20)
    frames(page)
    assert not page.evaluate("document.getElementById('spacing').open")
    # Escape closes and returns focus to the button.
    tap(page, "#actions-button")
    page.keyboard.press("Escape")
    assert page.evaluate("[document.getElementById('actions').open, document.activeElement.id]") == [False, "actions-button"]
    laws(page)


def test_sheets_desktop(phone):
    page = phone("example", "desk")
    page.click("#spacing-button")
    page.click(f"{css_id('2')} > .row .text", position={"x": 40, "y": 10})
    assert page.evaluate("document.getElementById('spacing').open"), "with a mouse the panel stays beside the outline"
    page.click("#actions-button")
    assert page.evaluate("document.getElementById('spacing').open") is False
    menu, button = sheet_rect(page, "actions"), page.locator("#actions-button").bounding_box()
    assert abs(menu["top"] - (button["y"] + button["height"] + 4)) <= 1, "the menu drops from its button"
    assert page.evaluate("document.activeElement.closest('#actions') !== null"), "a keyboard reader starts on its first item"
    page.click(f"{css_id('2')} > .row .text", position={"x": 40, "y": 10})
    assert not page.evaluate("document.getElementById('actions').open")


@pytest.mark.parametrize("device", ["w320", "ip15", "land"])
def test_help_touch(phone, device):
    page = phone("example", device)
    page.evaluate("scrollTo(0, 600)")
    tap(page, "#help-button")
    help = page.evaluate("""(() => { const d = document.getElementById('help'), r = d.getBoundingClientRect(),
      t = d.querySelector('.help-touch').getBoundingClientRect(), k = d.querySelector('.help-keys').getBoundingClientRect(),
      h = document.getElementById('help-title').getBoundingClientRect();
      return { open: d.open, top: r.top, bottom: r.bottom, scroll: d.scrollTop + d.querySelector('.help-body').scrollTop,
               touchFirst: t.top < k.top, title: h.top }; })()""")
    vh = page.evaluate("innerHeight")
    assert help["open"] and help["scroll"] == 0 and help["touchFirst"], help
    assert 0 <= help["title"] and help["bottom"] <= vh, help
    page.touchscreen.tap(5, vh - 5 if help["bottom"] < vh - 10 else 5)
    frames(page)
    assert not page.evaluate("document.getElementById('help').open"), "a tap on the backdrop closes help"


def test_start_mode(phone):
    assert mode(phone("example", "ip15")) == "idle", "a touch page opens with no selection ring"
    page = phone("example", "ip15")
    assert page.locator('[aria-selected="true"]').count() == 0
    assert mode(phone("example", "desk")) == "selected"


def test_start_mode_stored_zoom(phone, docs):
    """Found by the touch walk: a touch page reopened on a stored zoom starts idle in the DOM too."""
    page = phone("stress", "ip15")
    select(page, "2")
    open_menu_run(page, "zoomIn")
    laws(page)
    page.goto(docs["stress"].as_uri())
    settle(page)
    assert page.evaluate("[window.tractatus.zoom(), window.tractatus.selection().mode]") == ["2", "idle"]
    laws(page)


@pytest.mark.parametrize("device", ["w320", "ip15", "ipad"])
def test_sticky_head(phone, device):
    page = phone("stress", device, fragment="#z=1")
    expand_all(page)
    page.evaluate("scrollTo(0, 800)")
    frames(page)
    head = page.evaluate("(() => { const r = document.querySelector('.page-head').getBoundingClientRect();"
                         " return { top: r.top, height: r.height,"
                         " block: getComputedStyle(document.documentElement).getPropertyValue('--head-block') }; })()")
    assert abs(head["top"]) <= 0.5
    assert head["block"] == f"{-(-head['height'] // 1):.0f}px"
    assert page.is_visible("#up-button")
    # A selected item scrolls into view below the header.
    page.evaluate("scrollTo(0, 0)")
    page.evaluate(f"location.hash = '{DEEPEST}'")
    frames(page, 3)
    top = page.evaluate(f"document.querySelector('{css_id(DEEPEST)} > .row').getBoundingClientRect().top")
    assert top >= head["height"] - 1


def test_head_static_landscape(phone):
    """A short landscape screen keeps its height for the outline: the header scrolls away."""
    page = phone("example", "land", viewport={"width": 734, "height": 343})
    assert page.evaluate("getComputedStyle(document.querySelector('.page-head')).position") == "static"
    assert page.evaluate("getComputedStyle(document.documentElement).getPropertyValue('--head-block')") == "0px"


# ── random touch walk ─────────────────────────────────────
WALK = {   # action: what a finger lands on
    "row": "#outline .row .text", "bullet": "#outline .toggle", "menu": "#actions [data-command]",
    "more": "#actions-button", "up": "#up-button", "crumb": "#crumbs a", "spacing": "#spacing-button",
    "step": "#spacing .step", "help": "#help-button", "title": "#doc-title", "link": '#outline a[href^="#"]',
}
MARK_JS = """([sel, k]) => {
  document.querySelectorAll('[data-walk]').forEach((e) => e.removeAttribute('data-walk'));
  const all = [...document.querySelectorAll(sel)].filter((e) => e.checkVisibility() && !e.disabled);
  if (!all.length) return false;
  all[k % all.length].dataset.walk = '1';
  return true; }"""


@pytest.fixture
def walk_page(phone):
    """One page for every example of the walk (Hypothesis runs them inside one test call)."""
    return phone("stress", "ip15", init=[STAY])


# A tap on a web link would leave the page; the walk stays on the outline.
STAY = """addEventListener("click", (e) => { const a = e.target.closest?.("a[href]");
  if (a && !a.getAttribute("href").startsWith("#")) e.preventDefault(); }, true);"""


@settings(max_examples=10, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(walk=st.lists(st.tuples(st.sampled_from([*WALK, "back"]), st.integers(0, 999)), min_size=1, max_size=10))
def test_touch_walk(walk_page, walk):
    """Laws S and D and M1 hold after every tap, from any reachable state."""
    page = walk_page
    page.evaluate("localStorage.clear()")             # a fresh reader: no stored view
    page.goto(page.url.split("#")[0])
    settle(page)
    page.evaluate("localStorage.clear()")
    vw = page.evaluate("innerWidth")
    for action, k in walk:
        if page.evaluate("document.getElementById('help').open"):
            page.keyboard.press("Escape")
        if action == "back":
            if page.evaluate("location.hash") == "":
                continue            # the walk's first entry: Back would leave the page
            page.go_back()
            if not page.url.startswith("file:"):
                page.go_forward()
            settle(page)
        elif page.evaluate(MARK_JS, [WALK[action], k]):
            target = page.locator("[data-walk]").first
            try:
                target.scroll_into_view_if_needed(timeout=1000)
                target.tap(timeout=1000)
            except Exception:   # under an open sheet: a real finger lands on the sheet instead
                continue
        frames(page)
        laws(page)
        assert page.evaluate("document.documentElement.scrollWidth") <= vw, (action, k)
