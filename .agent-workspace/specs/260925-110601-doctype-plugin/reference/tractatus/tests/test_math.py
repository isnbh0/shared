"""Phase 4: MathJax typesetting (laws T and M), with a stub offline and the real MathJax online."""

import base64
import hashlib
import re

import pytest
from conftest import FIXTURES, check_laws, template_text

MATHJAX_URL = "https://cdn.jsdelivr.net/npm/mathjax@3.2.2/es5/tex-chtml.js"
MATHJAX_SRI = "sha384-AHAnt9ZhGeHIrydA1Kp1L7FN+2UosbF7RQg6C+9Is/a7kDpQ1684C2iH2VWil6r4"
CSP = (
    "default-src 'none'; "
    f"script-src 'unsafe-inline' {MATHJAX_URL}; "
    "style-src 'unsafe-inline'; "
    "font-src https://cdn.jsdelivr.net/npm/mathjax@3.2.2/es5/output/chtml/fonts/; "
    "base-uri 'none'; form-action 'none'"
)
STUB = FIXTURES / "mathjax-stub.js"
MATH_STATE = "document.documentElement.dataset.mathState"
LEGAL = [["source", "pending"], ["pending", "typeset"], ["pending", "failed"]]

# Records every data-math change as [old, new]; installed before the page's own scripts run.
RECORD_JS = """
window.__mathTransitions = [];
new MutationObserver((records) => {
  for (const r of records) window.__mathTransitions.push([r.oldValue, r.target.dataset.math]);
}).observe(document, { subtree: true, attributes: true, attributeOldValue: true,
                        attributeFilter: ["data-math"] });
"""

MATH_MD = "- 1 Plain.\n  - 1.1 $p \\supset q$ and $aRb$\n- 2 $x$\n"


def settle(page, timeout=30_000):
    page.wait_for_function(
        f"() => {MATH_STATE} !== undefined && {MATH_STATE} !== 'loading'", timeout=timeout
    )
    return page.evaluate(MATH_STATE)


def spans(page):
    return page.evaluate(
        "[...document.querySelectorAll('.math')].map(s => [s.dataset.tex, s.dataset.math])"
    )


def sri(data: bytes) -> str:
    return "sha384-" + base64.b64encode(hashlib.sha384(data).digest()).decode()


def pin_integrity(value: str):
    """A page transform that swaps the template's MathJax integrity for `value`."""

    def _transform(html: str) -> str:
        assert html.count(MATHJAX_SRI) == 1
        return html.replace(MATHJAX_SRI, value)

    return _transform


def assert_forward_only(page):
    """Law M: every recorded move is source->pending, pending->typeset or pending->failed."""
    moves = page.evaluate("window.__mathTransitions")
    assert moves, "no transitions recorded"
    assert all(m in LEGAL for m in moves), moves


@pytest.fixture
def stub(page, page_transforms):
    """Serve the MathJax stub in `mode`; registered after the law N abort route, so it wins.
    The page's integrity is pinned to the stub unless `integrity` is False."""

    def _stub(mode="ok", integrity=True):
        page.add_init_script(f"window.__stubMode = {mode!r};")
        page.add_init_script(RECORD_JS)
        if integrity:
            page_transforms.append(pin_integrity(sri(STUB.read_bytes())))
        page.route(
            MATHJAX_URL,
            lambda r: r.fulfill(
                path=STUB,
                content_type="text/javascript",
                headers={"Access-Control-Allow-Origin": "*"},   # a file:// page's origin is null
            ),
        )

    return _stub


def test_math_offline_fallback(page, open_outline, fake_md, console_errors):
    page.add_init_script(RECORD_JS)
    page = open_outline(fake_md)
    assert settle(page) == "unavailable"
    assert all(state == "failed" for _, state in spans(page))
    span = page.locator("#item-4_011 .math")
    assert span.get_attribute("data-tex") == "p \\supset q"
    assert span.text_content() == "p \\supset q"
    assert_forward_only(page)
    assert console_errors == []


def test_no_math_no_load(page, open_outline):
    requests = []
    page.on("request", lambda r: requests.append(r.url))
    page = open_outline("- 1 plain")
    assert page.evaluate(MATH_STATE) == "none"
    assert not any("cdn.jsdelivr.net" in u for u in requests)


def test_mathjax_config(stub, open_outline):
    stub("ok")
    page = open_outline(MATH_MD)
    settle(page)
    config = page.evaluate("window.__stubConfig")
    assert config["startup"]["typeset"] is False
    assert config["options"]["enableMenu"] is False
    assert config["options"]["enableAssistiveMml"] is True
    assert sorted(config["tex"]["packages"]["[-]"]) == ["autoload", "noundefined", "require"]
    # Law T: \mmlToken, \ref and \eqref are undefined; base and ams macros built on \mmlToken
    # are restated without any of them.
    macros = config["tex"]["macros"]
    for name in ("mmlToken", "ref", "eqref"):
        assert macros[name] == f"\\{name}Disabled"
    restated = {"bmod", "pmod", "mod", "varliminf", "varlimsup", "varinjlim", "varprojlim"}
    assert set(macros) == {"mmlToken", "ref", "eqref"} | restated
    bodies = [body if isinstance(body, str) else body[0] for body in macros.values()]
    assert not any(re.search(r"\\(mmlToken|ref|eqref)(?![A-Za-z])", body) for body in bodies)


FILTER_JS = """(cases) => {
  const [[filter], ...more] = window.__stubPostFilters;
  const node = ([kind, attrs]) => ({ kind, attributes: attrs && { getExplicit: (n) => attrs[n] } });
  const run = (nodes) => {
    try { filter({ data: { root: { walkTree: (f) => nodes.map(node).forEach(f) } } }); return null; }
    catch (e) { return e.message; }
  };
  return { more: more.length, results: cases.map(run) };
}"""
BLOCKED_ATTRIBUTES = ["href", "class", "id", "style", "fontfamily", "fontweight", "fontstyle", "src", "alt"]


def test_markup_filter(stub, open_outline):
    """Law T, second layer: the TeX post-filter rejects these attributes and mglyph."""
    stub("ok")
    page = open_outline(MATH_MD)
    settle(page)
    harmless = [
        ["mi", {"mathvariant": "normal"}],
        ["mo", {"lspace": "thickmathspace", "stretchy": False}],
        ["mfrac", {"linethickness": "2pt"}],
        ["text", None],
    ]
    cases = [harmless] + [[["mi", {}], ["mi", {name: "x"}]] for name in BLOCKED_ATTRIBUTES]
    cases.append([["mi", {}], ["mglyph", {}]])
    out = page.evaluate(FILTER_JS, cases)
    assert out["more"] == 0
    assert out["results"][0] is None
    for name, message in zip(BLOCKED_ATTRIBUTES, out["results"][1:]):
        assert message == f'math: the "{name}" attribute is not allowed'
    assert out["results"][-1] == "math: mglyph is not allowed"


def test_mathjax_integrity(stub, page, build_page):
    """The MathJax script is pinned by SRI: a body that does not match never runs."""
    assert template_text().count(MATHJAX_SRI) == 1
    stub("ok", integrity=False)
    page.goto(build_page(MATH_MD).as_uri())
    page.wait_for_function("() => document.documentElement.dataset.outlineReady === 'true'")
    assert settle(page) == "unavailable"
    assert page.evaluate("window.__stubConfig") is None
    script = page.locator(f'script[src="{MATHJAX_URL}"]')
    assert script.get_attribute("integrity") == MATHJAX_SRI
    assert script.get_attribute("crossorigin") == "anonymous"


def test_csp(page, build_page):
    """The page may load only MathJax's script and fonts; images and fetches are blocked."""
    t = template_text()
    assert t.index('http-equiv="Content-Security-Policy"') < t.index("<script")
    page.goto(build_page("- 1 plain").as_uri())
    page.wait_for_function("() => document.documentElement.dataset.outlineReady === 'true'")
    assert page.get_attribute('meta[http-equiv="Content-Security-Policy"]', "content") == CSP
    blocked = page.evaluate(
        """() => new Promise((resolve) => {
          addEventListener("securitypolicyviolation", (e) => resolve(e.effectiveDirective), { once: true });
          document.body.append(Object.assign(document.createElement("img"), { src: "https://leak.invalid/x.png" }));
        })"""
    )
    assert blocked == "img-src"


def test_math_stub_ok(stub, open_outline):
    stub("ok")
    page = open_outline(MATH_MD)
    assert settle(page) == "ready"
    assert all(state == "typeset" for _, state in spans(page))
    calls = page.evaluate("window.__stubCalls")
    assert sorted(calls) == ["aRb", "p \\supset q", "x"]
    assert set(calls.values()) == {1}
    page.evaluate("Promise.all([window.tractatus.typeset(), window.tractatus.typeset()])")
    assert page.evaluate("window.__stubCalls") == calls
    assert page.evaluate(MATH_STATE) == "ready"
    # A span that is still `source` is claimed by the first of two same-tick requests only.
    page.evaluate(
        """() => {
          const s = Object.assign(document.createElement("span"), { className: "math", textContent: "late" });
          s.dataset.tex = "late";
          s.dataset.math = "source";
          document.querySelector("#item-1 .para").append(s);
          return Promise.all([window.tractatus.typeset(), window.tractatus.typeset()]);
        }"""
    )
    assert page.evaluate("window.__stubCalls")["late"] == 1
    assert page.get_attribute('.math[data-tex="late"]', "data-math") == "typeset"
    assert page.evaluate(MATH_STATE) == "ready"
    assert_forward_only(page)
    check_laws(page)


@pytest.mark.parametrize("mode", ["reject", "merror"])
def test_math_stub_one_failure(stub, open_outline, mode):
    stub(mode)
    page = open_outline(MATH_MD)
    assert settle(page) == "partial"
    for tex, state in spans(page):
        assert state == ("failed" if tex == "aRb" else "typeset"), tex
    failed = page.locator('.math[data-tex="aRb"]')
    assert failed.text_content() == "aRb"
    assert failed.locator("mjx-merror").count() == 0
    # A failed span is final: another typeset request neither retries nor revives it.
    page.evaluate("window.tractatus.typeset()")
    assert page.evaluate("window.__stubCalls")["aRb"] == 1
    assert failed.get_attribute("data-math") == "failed"
    assert_forward_only(page)


def test_math_stub_stall(stub, page, build_page, console_errors):
    stub("stall")
    path = build_page(MATH_MD)
    html = path.read_text(encoding="utf-8")
    assert html.count('data-math-timeout="15000"') == 1
    path.write_text(html.replace('data-math-timeout="15000"', 'data-math-timeout="200"'), encoding="utf-8")
    page.goto(path.as_uri())
    page.wait_for_function("() => document.documentElement.dataset.outlineReady === 'true'")
    # Law M: spans are claimed synchronously at startup, so later requests find nothing to claim.
    assert page.evaluate(MATH_STATE) == "loading"
    assert all(state == "pending" for _, state in spans(page))
    page.evaluate("window.tractatus.typeset(); window.tractatus.typeset(); null")
    assert settle(page, timeout=3_000) == "unavailable"
    assert all(state == "failed" for _, state in spans(page))
    assert_forward_only(page)


def test_math_stub_no_promise(stub, open_outline):
    stub("nopromise")
    page = open_outline(MATH_MD)
    assert settle(page) == "unavailable"
    assert_forward_only(page)


@pytest.mark.network
def test_math_online(open_outline, fake_md):
    page = open_outline(fake_md)
    assert settle(page) == "ready"
    assert sri(page.request.get(MATHJAX_URL).body()) == MATHJAX_SRI
    page.click("#item-4 > .row > .toggle")
    page.click("#item-4_01 > .row > .toggle")
    container = page.locator('#item-4_011 .math[data-math="typeset"] mjx-container')
    assert container.count() == 1
    assert container.locator("mjx-assistive-mml").count() == 1
    assert page.locator("#outline .math [tabindex]").count() == 0
    check_laws(page)

    # Law D: Tab visits exactly one element inside the tree, the active item.
    page.evaluate("document.activeElement.blur()")
    seen, inside = [], []
    for _ in range(20):
        page.keyboard.press("Tab")
        el = page.evaluate_handle("document.activeElement")
        if any(page.evaluate("([a, b]) => a === b", [el, s]) for s in seen):
            break
        seen.append(el)
        if page.evaluate("e => document.getElementById('outline').contains(e)", el):
            inside.append(page.evaluate("e => e.dataset.id ?? e.tagName", el))
    assert inside == [page.evaluate("window.tractatus.state().activeId")]


TEX_VOCABULARY = [
    "a",  # control
    "\\href{https://x.test}{a}",
    "\\class{c1}{a}",
    "\\style{color:red}{a}",
    "\\cssId{i1}{a}",
    "\\bbox[red]{a}",
    "\\toggle{a}{b}\\endtoggle",
    "\\require{html}\\href{https://x.test}{a}",
    # Harmless extensions ground each removed package on its own (the attribute filter below
    # would also catch \href): no \require, no autoload, and undefined commands are errors.
    "\\require{cancel}\\cancel{a}",
    "\\enclose{circle}{a}",
    "\\xyzzy",
    # Base can set these attributes through \mmlToken, \ref and \eqref, which are undefined.
    '\\mmlToken{mi}[href="https://x.test"]{a}',
    '\\mmlToken{mi}[class="c1"]{a}',
    '\\mmlToken{mi}[id="i1"]{a}',
    '\\mmlToken{mi}[style="color:red"]{a}',
    "\\ref{x}",
    "\\eqref{x}",
    '\\def\\x{\\mmlToken{mi}[href="https://x.test"]{z}}\\x',
]


LEAK = "https://leak.invalid"
# \mmlToken also reaches an mglyph's src (an <img>) and fontfamily, fontweight and fontstyle,
# which CHTML writes unchecked into a style attribute. Each row names LEAK.
TEX_INJECTION = [
    s.replace("LEAK", LEAK)
    for s in [
        '\\mmlToken{mglyph}[src="LEAK/b1.png",width="2em",height="1em",alt="ALT"]{}',
        '\\mmlToken{mi}[fontfamily="serif;position:fixed;inset:0;background:url(LEAK/b2.png);z-index:9"]{x}',
        '\\mmlToken{mi}[fontfamily="serif",fontweight="bold;background:url(LEAK/weight.png)"]{x}',
        '\\mmlToken{mi}[fontfamily="serif",fontstyle="italic;background:url(LEAK/style.png)"]{x}',
        '\\mmlToken{mglyph}[src="LEAK/g.png",fontfamily="serif;background:url(LEAK/gf.png)"]{}',
        '\\let\\x=\\mmlToken \\x{mi}[fontfamily="serif;background:url(LEAK/let.png)"]{x}',
        '\\def\\x{\\mmlToken}\\x{mi}[fontfamily="serif;background:url(LEAK/def.png)"]{x}',
        '\\text{\\(\\mmlToken{mi}[fontfamily="serif;background:url(LEAK/text.png)"]{x}\\)}',
    ]
]
# Base and ams macros built on \mmlToken still typeset.
TEX_KEPT = [
    "a",
    "a \\bmod b",
    "a \\pmod{b}",
    "a \\mod b",
    "\\varliminf_n x",
    "\\varlimsup_n x",
    "\\varinjlim_n x",
    "\\varprojlim_n x",
]


@pytest.mark.network
def test_tex_vocabulary(page, open_outline):
    """Law T: commands that could emit URLs, classes, ids, styles or actions are errors."""
    requests = []
    page.on("request", lambda r: requests.append(r.url))
    rows = TEX_KEPT + TEX_VOCABULARY[1:] + TEX_INJECTION
    page = open_outline("\n".join(f"- ${tex}$" for tex in rows))
    assert settle(page) == "partial"
    states = dict(spans(page))
    assert states == {tex: ("typeset" if tex in TEX_KEPT else "failed") for tex in rows}
    for selector in (
        "#outline [href]",
        "#outline a",
        ".c1",
        "#i1",
        '#outline [style*="red"]',
        "#outline img",
        "#outline [src]",
        f'#outline [style*="{LEAK}"]',
    ):
        assert page.locator(selector).count() == 0, selector
    assert [u for u in requests if u.startswith(LEAK)] == []
    check_laws(page)


# A plain row, then a row whose first line holds math taller than the line (overlines, brackets).
ALIGN_MD = (
    "- 5 Propositions are truth-functions of elementary propositions.\n"
    "- 6 The general form of truth-function is: $[\\overline{p}, \\overline{\\xi}, N(\\overline{\\xi})]$.\n"
)
# Per row: the first line's baseline minus the bullet's centre, and the label's baseline minus
# the first line's. A zero-size inline-block's top is the baseline of the line it sits on.
ALIGN_JS = """(ids) => ids.map((id) => {
  const row = document.querySelector(`#${id} > .row`);
  const baseline = (host) => {
    const m = document.createElement("span");
    m.style.cssText = "display:inline-block;inline-size:0;block-size:0";
    host.prepend(m);
    const y = m.getBoundingClientRect().top;
    m.remove();
    return y;
  };
  const text = baseline(row.querySelector(".para"));
  const t = row.querySelector(".toggle").getBoundingClientRect();
  return [text - (t.top + t.height / 2), baseline(row.querySelector(".label")) - text];
})"""
ALIGN_CASES = [
    pytest.param(width, spacing, id=f"{width}-{'cozy' if spacing else 'default'}")
    for width in (1200, 400)                       # 400: the narrow inline-label layout
    for spacing in (None, {"--lh": "1.2", "--item-gap": "8px"})   # Dynalist large / cozy
]


def assert_math_row_aligned(page, width, spacing):
    page.set_viewport_size({"width": width, "height": 700})
    for prop, value in (spacing or {}).items():
        page.evaluate("([p, v]) => document.documentElement.style.setProperty(p, v)", [prop, value])
    plain, math = page.evaluate(ALIGN_JS, ["item-5", "item-6"])
    assert math == pytest.approx(plain, abs=1), (plain, math)


@pytest.mark.network
@pytest.mark.parametrize("width, spacing", ALIGN_CASES)
def test_math_row_bullet_alignment(open_outline, width, spacing):
    """The bullet and label sit on the first line of a row with tall inline math as on a plain row."""
    page = open_outline(ALIGN_MD)
    assert settle(page) == "ready"
    assert page.locator('#item-6 .math[data-math="typeset"] mjx-container').count() == 1
    assert_math_row_aligned(page, width, spacing)


@pytest.mark.parametrize("width, spacing", ALIGN_CASES)
def test_math_row_bullet_alignment_offline(open_outline, width, spacing):
    page = open_outline(ALIGN_MD)
    assert settle(page) == "unavailable"
    assert spans(page)[0][1] == "failed"
    assert_math_row_aligned(page, width, spacing)
