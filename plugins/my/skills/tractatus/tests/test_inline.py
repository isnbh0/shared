"""Phase 4: inline grammar (law I) and vetted links (law H)."""

import pytest
from conftest import check_laws
from test_deep_links import hash_of
from test_tree_keyboard import focused_id, state


@pytest.fixture
def fixture_page(open_outline, fake_md):
    return open_outline(fake_md)


def parse(page, source, links=True):
    return page.evaluate(
        "([s, links]) => window.tractatus.parseInline(s, { links })", [source, links]
    )


def text(value):
    return {"type": "text", "value": value}


def types(tokens):
    """Token types, depth-first."""
    out = []
    for t in tokens:
        out.append(t["type"])
        out.extend(types(t.get("children", [])))
    return out


def test_parse_basic_tokens(fixture_page):
    assert parse(fixture_page, "a *b* **c** _d_ `e`") == [
        text("a "),
        {"type": "em", "children": [text("b")]},
        text(" "),
        {"type": "strong", "children": [text("c")]},
        text(" "),
        {"type": "em", "children": [text("d")]},
        text(" "),
        {"type": "code", "value": "e"},
    ]


def test_parse_escapes_and_literals(fixture_page):
    page = fixture_page
    assert parse(page, "\\*x\\*") == [text("*x*")]
    assert parse(page, "snake_case_name") == [text("snake_case_name")]
    assert parse(page, "2 * 3 * 4") == [text("2 * 3 * 4")]


def test_parse_math(fixture_page):
    page = fixture_page
    assert parse(page, "$p \\supset q$") == [{"type": "math", "tex": "p \\supset q"}]
    assert parse(page, "costs $5 and \\$6") == [text("costs $5 and $6")]
    assert "math" not in types(parse(page, "$$x$$"))
    assert "math" not in types(parse(page, "$ x$"))
    assert parse(page, "\\(aRb\\)") == [text("(aRb)")]
    assert parse(page, "$a\\$b$") == [{"type": "math", "tex": "a\\$b"}]


def test_code_and_math_bind_tighter(fixture_page):
    page = fixture_page
    out = parse(page, "$a*b*c$")
    assert out == [{"type": "math", "tex": "a*b*c"}]
    assert parse(page, "*a $b*c$ d*") == [
        {
            "type": "em",
            "children": [text("a "), {"type": "math", "tex": "b*c"}, text(" d")],
        }
    ]
    assert parse(page, "``a`b``") == [{"type": "code", "value": "a`b"}]
    assert parse(page, "`a") == [text("`a")]


def test_parse_links(fixture_page):
    page = fixture_page
    assert parse(page, "[t](https://x.test)") == [
        {"type": "link", "dest": "https://x.test", "children": [text("t")]}
    ]
    assert "link" not in types(parse(page, "[t](a b)"))
    assert "link" not in types(parse(page, "[](#1)"))
    out = parse(page, "[a [b](#2) c](#1)")
    assert len(out) == 1 and out[0]["type"] == "link" and out[0]["dest"] == "#1"
    assert "link" not in types(out[0]["children"])
    assert parse(page, "[t](x\\)y)")[0]["dest"] == "x)y"


ENUMERATION_JS = r"""
() => {
  const { parseInline, escapeInline } = window.tractatus;
  const ALPHABET = ["$", "*", "_", "`", "\\", "[", "]", "(", ")", "a", " "];
  const countA = (s) => s.split("a").length - 1;
  const tokensA = (ts) => ts.reduce((n, t) =>
    n + (t.type === "text" || t.type === "code" ? countA(t.value)
      : t.type === "math" ? countA(t.tex)
      : (t.type === "link" ? countA(t.dest) : 0) + tokensA(t.children)), 0);
  const normal = (ts) => ts.every((t, i) =>
    (t.type !== "text" || (t.value !== "" && ts[i - 1]?.type !== "text")) &&
    (!("children" in t) || (t.children.length > 0 && normal(t.children))));
  const failures = [];
  let count = 0;
  const check = (s) => {
    count += 1;
    for (const links of [true, false]) {
      let why = null;
      try {
        const out = parseInline(s, { links });
        const back = parseInline(escapeInline(s), { links });
        const want = s === "" ? [] : [{ type: "text", value: s }];
        if (tokensA(out) !== countA(s)) why = "lossy";
        else if (!normal(out)) why = "not normal";
        else if (JSON.stringify(back) !== JSON.stringify(want)) why = "escape";
      } catch (e) {
        why = `throws ${e}`;
      }
      if (why !== null && failures.length < 5) failures.push([s, links, why]);
    }
  };
  const walk = (prefix, depth) => {
    check(prefix);
    if (depth === 5) return;
    for (const c of ALPHABET) walk(prefix + c, depth + 1);
  };
  walk("", 0);
  return { count, failures };
}
"""


def test_grammar_enumeration(fixture_page):
    """Law I: total, lossless, normal form, and escaping, over every string up to length 5."""
    result = fixture_page.evaluate(ENUMERATION_JS)
    assert result["count"] == 177_156
    assert result["failures"] == []


def test_escape_inline(fixture_page):
    page = fixture_page
    assert page.evaluate("window.tractatus.escapeInline(\"a*b_[c]$`\\\\\")") == (
        "a\\*b\\_\\[c\\]\\$\\`\\\\"
    )
    assert page.evaluate("window.tractatus.escapeInline('(a)')") == "(a)"


@pytest.mark.parametrize(
    ("dest", "expected"),
    [
        ("javascript:alert(1)", None),
        ("JaVaScRiPt:alert(1)", None),
        ("\u0001javascript:alert(1)", None),
        (" javascript:alert(1)", None),
        ("java\tscript:alert(1)", None),
        ("data:text/html,x", None),
        ("vbscript:x", None),
        ("file:///etc/passwd", None),
        ("//evil.test/x", None),
        ("relative.html", None),
        ("#9.9", None),
        ("#%", None),
        ("https://x.test/a", "https://x.test/a"),
        ("HTTPS://X.test", "https://x.test/"),
        ("mailto:a@b.test", "mailto:a@b.test"),
        ("#5.1", "#5.1"),
        ("#p-5-3", "#p-5-3"),
    ],
)
def test_link_targets(fixture_page, dest, expected):
    """Law H: only http(s), mailto, and fragments naming an item become hrefs."""
    assert fixture_page.evaluate("d => window.tractatus.linkHref(d)", dest) == expected


SWEEP_JS = """
() => {
  const allowed = new Set(["http:", "https:", "mailto:"]);
  const errs = [];
  for (const a of document.querySelectorAll("a")) {
    const href = a.getAttribute("href");
    if (href === null) { errs.push(`no href: ${a.outerHTML}`); continue; }
    if (href.startsWith("#")) {
      let id = null;
      try { id = decodeURIComponent(href.slice(1)); } catch {}
      const hit = id !== null &&
        [...document.querySelectorAll("[data-id]")].some((e) => e.dataset.id === id);
      if (!hit) errs.push(`dangling ${href}`);
    } else {
      let protocol = null;
      try { protocol = new URL(href).protocol; } catch {}
      if (!allowed.has(protocol)) errs.push(`protocol ${protocol}: ${href}`);
    }
    if (a.closest("#outline") && a.getAttribute("tabindex") !== "-1") errs.push(`tab stop: ${href}`);
  }
  return { errs, count: document.querySelectorAll("a").length };
}
"""


def test_link_sweep(fixture_page):
    """Law H over the whole page: every <a> has a vetted href; tree links are not Tab stops."""
    page = fixture_page
    result = page.evaluate(SWEEP_JS)
    assert result["errs"] == []
    assert result["count"] >= 1
    assert "dangerous link" in page.text_content("#item-4_12 .text")
    assert page.locator("#item-4_12 .text a").count() == 0


def test_link_sweep_adversarial(open_outline):
    """Every link form that must not become an <a>, rendered in the tree, intro and title."""
    dests = [
        "javascript:alert(1)",
        "JaVaScRiPt:alert(1)",
        "vbscript:x",
        "data:text/html,x",
        "file:///etc/passwd",
        "//evil.test/x",
        "relative.html",
        "#9.9",
        "#%",
        "java\\)script:x",
    ]
    links = " ".join(f"[bad{i}]({d})" for i, d in enumerate(dests))
    md = f"# [t](https://x.test) {links}\n\nIntro {links} [ok](#1)\n\n- 1 {links} [ok](https://x.test)"
    page = open_outline(md)
    result = page.evaluate(SWEEP_JS)
    assert result["errs"] == []
    assert result["count"] == 2
    assert page.locator("#doc-title a").count() == 0
    assert page.get_attribute(".intro a", "href") == "#1"
    assert page.get_attribute("#outline [role=group] a", "href") == "https://x.test/"


def test_fixture_renders_markup(fixture_page):
    page = fixture_page
    assert page.text_content("#item-1_11 .text em") == "all"
    assert page.text_content("#item-5_11 .text strong") == "all"
    assert page.text_content("#item-5_101 .text code") == "(TTTT)(p, q)"
    assert page.text_content(".intro em") == "Tractatus"


def test_title_plain_text(open_outline):
    page = open_outline("# *My* doc\n\n- 1 x")
    assert page.title() == "My doc"
    assert page.text_content("#doc-title em") == "My"


def test_markup_is_not_html(open_outline):
    page = open_outline("- 1 *<b>x</b>* `<img src=x>` [<i>y</i>](https://x.test)")
    assert page.locator("#outline b, #outline img, #outline i").count() == 0
    assert page.text_content("#item-1 em") == "<b>x</b>"
    assert page.text_content("#item-1 a") == "<i>y</i>"


def test_content_link_zooms(fixture_page):
    """A click on an in-content #id link zooms into its target (Dynalist); the URL is #z=ID."""
    page = fixture_page
    page.click("#item-4 > .row > .toggle")
    page.click("#item-4_1 > .row > .toggle")
    link = "#item-4_11 .text a"
    assert page.get_attribute(link, "href") == "#5.1"
    page.click(link)
    page.wait_for_function("() => window.tractatus.zoom() === '5.1'")
    assert hash_of(page) == "#z=5.1"
    assert focused_id(page) == "5.1"
    check_laws(page)

    # 4.11 is outside 5.1, so go back to the document before clicking the link again.
    page.go_back()
    page.wait_for_function("() => window.tractatus.zoom() === 'root'")
    page.keyboard.press("Home")
    assert focused_id(page) == "root"
    page.click(link)
    page.wait_for_function("() => window.tractatus.zoom() === '5.1'")
    assert hash_of(page) == "#z=5.1"
    assert focused_id(page) == "5.1"
    check_laws(page)


def test_link_press_keeps_focus_off_link(fixture_page):
    """Law D: a press on a tree link never puts DOM focus on the link."""
    page = fixture_page
    page.click("#item-4 > .row > .toggle")
    page.click("#item-4_1 > .row > .toggle")
    page.hover("#item-4_11 .text a")
    page.mouse.down()
    assert page.evaluate("document.activeElement.tagName") != "A"
    check_laws(page)
    page.mouse.up()
    page.wait_for_function("() => document.activeElement.dataset.id === '5.1'")
    check_laws(page)
