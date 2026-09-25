"""Phase 6: the Tractatus converter (law C) and the committed example page."""

import hashlib
import importlib.util
import sys

import pytest
from conftest import SKILL_DIR, check_laws, embed, template_text
from test_deep_links import set_hash

EXAMPLES = SKILL_DIR / "examples"
MATH_STATE = "document.documentElement.dataset.mathState"

_spec = importlib.util.spec_from_file_location("build_tractatus", EXAMPLES / "build_tractatus.py")
bt = importlib.util.module_from_spec(_spec)
sys.modules["build_tractatus"] = bt  # dataclasses resolve string annotations through it
_spec.loader.exec_module(bt)

# Math tokens of each paragraph, in order, as the template's inline grammar reads them.
MATH_TOKENS_JS = """
(paragraphs) => paragraphs.flatMap((p) => {
  const out = [];
  const walk = (tokens) => {
    for (const t of tokens) {
      if (t.type === "math") out.push(t.tex);
      else if (t.children) walk(t.children);
    }
  };
  walk(window.tractatus.parseInline(p));
  return out;
})
"""

# Parsed outline as flat rows: [label, parent label, depth, text], plus top-level count and warnings.
OUTLINE_JS = """
(markdown) => {
  const doc = window.tractatus.parseOutline(markdown);
  const rows = [];
  const walk = (nodes, parent, depth) => {
    for (const n of nodes) {
      rows.push([n.label, parent, depth, n.text]);
      walk(n.children, n.label, depth + 1);
    }
  };
  walk(doc.items, null, 1);
  return { rows, top: doc.items.length, warnings: doc.warnings };
}
"""

SNIPPETS = [
    (r"\emph{all}", ["*all*"]),
    (r"x \emph{ y } z", ["x *y* z"]),
    (r"\emph{a \emph{b} c}", ["*a b c*"]),
    (r"$\emph{x}$", [r"$\textit{x}$"]),
    (r"$\Not{p}$", [r"$\sim p$"]),
    (r"\Not{p}", [r"$\sim p$"]),
    (r"$p \DPtypo{\Implies}{\supset} q$", [r"$p \supset q$"]),
    (r"\DPtypo{teh}{the}", ["the"]),
    (r"\PropERef{5.151}", ["[5.151](#5.151)"]),
    ("``x''", ["“x”"]),
    ("a---b--c", ["a—b–c"]),
    (r"a\footnote{b}", ["a", "Note: b"]),
    ("a\n\nb", ["a", "b"]),
    (r"$a \text{if $b$} c$", [r"$a \text{if }b c$"]),
    (r"\begin{gather*}a\\b\end{gather*}", [r"$\begin{gathered}a\\b\end{gathered}$"]),
    (
        r"before\begin{tabular}{c}x\end{tabular}after",
        ["before", r"$\begin{array}{c}\text{x}\end{array}$", "after"],
    ),
    # The source's \Illustration[width]{file} takes one mandatory argument.
    (r"\Illustration[w]{images/fig_1.png}", [r"*Figure omitted: fig\_1*"]),
    (r"\Illustration{cube}can", ["*Figure omitted: cube*", "can"]),
    ("1. not a list", [r"1\. not a list"]),
    ("- dash", [r"\- dash"]),
    ("a*b_c [d]", [r"a\*b\_c \[d\]"]),
    (r"50\% of \$5", [r"50% of \$5"]),
    (
        r"\begin{tabular}{|c|c|}p & $q$ \\ \hline\end{tabular}",
        [r"$\begin{array}{|c|c|}\text{p} & q \\ \hline\end{array}$"],
    ),
    # Beyond the spec table: adjacent spans merge (`$a$$b$` would not read back as two spans),
    # spaces inside cells and after math-mode control words survive, \[…\] is a math paragraph,
    # text inside \text{} escapes MathJax's text-mode specials, and @{…} column glue is dropped.
    (r"$a'${}$(b)$", [r"$a'(b)$"]),
    (r"$2 \times 2 = 4$", [r"$2 \times 2 = 4$"]),
    (r"a $ p \ $ b $\,$", [r"a $p$ b $\,$"]),
    (
        r"\begin{tabular}{l}if $p$ then\end{tabular}",
        [r"$\begin{array}{l}\text{if }p\text{ then}\end{array}$"],
    ),
    (r"a \[x\] b", ["a", "$x$", "b"]),
    (r"$\text{50\% \$}$", [r"$\text{50% \$}$"]),
    (
        r"\begin{tabular}{@{}c@{~}l@{}}a&b\end{tabular}",
        [r"$\begin{array}{cl}\text{a} & \text{b}\end{array}$"],
    ),
    (r"Thus\\ \smash[t]{``}x", ["Thus “x"]),
    (r"\idEst\ it", ["*i.e.* it"]),
    (r"\[``x\text{''}\]", [r"$\text{“}x\text{”}$"]),
]


@pytest.fixture
def tractatus(open_outline):
    """A page that exposes window.tractatus (no math, so MathJax never loads)."""
    return open_outline("- 1 x")


def md_text() -> str:
    return (EXAMPLES / "tractatus.md").read_bytes().decode("utf-8")


def outline(page):
    return page.evaluate(OUTLINE_JS, md_text())


def test_parent_rule():
    assert bt.parent("2.0121") == "2.012"
    assert bt.parent("2.01") == "2.0"
    assert bt.parent("2.0") == "2"
    assert bt.parent("3.001") == "3.0"
    assert bt.parent("5.101") == "5.1"
    assert bt.parent("4.0031") == "4.003"
    assert bt.parent("7") is None


def test_read_braced():
    assert bt.read_braced("{a{b}c}d", 0) == ("a{b}c", 7)
    assert bt.read_braced(r"{a\}b}", 0)[0] == r"a\}b"
    assert bt.read_braced(r"{a\\}b", 0)[0] == "a\\\\"
    with pytest.raises(bt.ConversionError):
        bt.read_braced("{a{b}", 0)


def test_strip_comments():
    assert bt.strip_comments("a % c\n  b") == "a b"
    assert bt.strip_comments(r"50\% off") == r"50\% off"
    assert bt.strip_comments("a\\\\% c\nb") == "a\\\\b"


def test_extract():
    source = "\n".join(
        [
            r"\PropositionE{9}{pre}",
            r"\begin{document}",
            r"% \PropositionE{8}{commented}",
            r"\PropositionE{1}{one}",
            r"\PropositionE{1.1}",
            r"{one-one}",
            r"\PropositionG{1}{eins}",
            r"\PropositionE{2}{after}",
        ]
    )
    assert bt.extract_propositions(source) == [("1", "one"), ("1.1", "one-one")]


def test_load_source(monkeypatch):
    with pytest.raises(bt.ConversionError):
        bt.load_source(b"not the pinned source")

    def load(data: bytes) -> str:
        monkeypatch.setattr(bt, "SOURCE_SHA256", hashlib.sha256(data).hexdigest())
        return bt.load_source(data)

    # A commented-out declaration (as in the pinned source) does not count.
    assert load("%\\usepackage[latin1]{inputenc}\né".encode()).endswith("é")
    assert load("\\usepackage[latin1]{inputenc}\né".encode("latin-1")).endswith("é")
    with pytest.raises(bt.ConversionError):
        load(b"\\usepackage[cp1252]{inputenc}")


def test_unknown_command_fails():
    with pytest.raises(bt.ConversionError) as e:
        bt.convert("1", r"\unknownmacro{x}")
    assert e.value.number == "1"
    assert "unknownmacro" in e.value.message
    with pytest.raises(bt.ConversionError):
        bt.convert("1", r"\begin{itemize}x\end{itemize}")


@pytest.mark.parametrize("raw", [r"$\footnote{x}$", r"$\PropERef{1}$", "a & b", "$p$2"])
def test_mode_errors(raw):
    with pytest.raises(bt.ConversionError):
        bt.convert("1", raw)


@pytest.mark.parametrize(("raw", "paragraphs"), SNIPPETS)
def test_convert_snippets(raw, paragraphs):
    assert bt.convert("1", raw).paragraphs == paragraphs


def test_math_tokens_survive(tractatus):
    """Law C: the inline grammar reads back exactly the math spans the serializer emitted."""
    for raw, _ in SNIPPETS:
        converted = bt.convert("1", raw)
        assert tractatus.evaluate(MATH_TOKENS_JS, converted.paragraphs) == converted.math, raw


def test_markdown_structure(tractatus):
    doc = outline(tractatus)
    rows = doc["rows"]
    labels = [label for label, _, _, _ in rows]
    groups = {label for label, _, _, text in rows if text == ""}
    assert groups == {"2.0", "3.0", "4.0", "5.0", "6.0"}
    assert len(rows) == 526 + len(groups)
    assert doc["top"] == 7
    assert max(d for _, _, d, _ in rows) == 6
    assert doc["warnings"] == []
    assert None not in labels
    assert len(set(labels)) == len(labels)
    for label, parent_label, _, _ in rows:
        assert bt.parent(label) == parent_label, label


def test_special_content(tractatus):
    text = {label: t for label, _, _, t in outline(tractatus)["rows"]}
    for label in ("4.31", "4.442", "5.101"):
        assert "\\begin{array}" in text[label], label
    assert "*Figure omitted:" in text["5.5423"]
    assert any(p.startswith("Note:") for p in text["1"].split("\n\n"))
    assert "](#" in text["5.151"]


def test_html_is_current():
    html = (EXAMPLES / "tractatus.html").read_bytes().decode("utf-8")
    assert html == embed.embed(md_text(), template_text()), "rerun build_tractatus.py"


def test_no_gutenberg_text():
    for name in ("tractatus.md", "tractatus.html"):
        assert "gutenberg" not in (EXAMPLES / name).read_bytes().decode("utf-8").lower(), name


def test_example_page_smoke(page, console_errors):
    page.goto((EXAMPLES / "tractatus.html").as_uri())
    page.wait_for_function("() => document.documentElement.dataset.outlineReady === 'true'")
    visible = page.evaluate(
        "[...document.querySelectorAll('[role=treeitem]')].filter(li => li.checkVisibility()).length"
    )
    assert visible == 8                                            # the root and 7 items
    page.wait_for_function(f"() => {MATH_STATE} !== 'loading'")
    assert page.evaluate(MATH_STATE) == "unavailable"
    set_hash(page, "#2.0121")
    page.wait_for_function("() => document.activeElement.dataset.id === '2.0121'")
    assert page.evaluate("window.tractatus.state()")["expanded"] == ["2", "2.0", "2.01", "2.012"]
    check_laws(page)


@pytest.mark.network
def test_rebuild_matches(tmp_path, tractatus):
    assert bt.main(["--out-dir", str(tmp_path)]) == 0
    assert (tmp_path / "tractatus.md").read_bytes() == (EXAMPLES / "tractatus.md").read_bytes()
    assert (tmp_path / "tractatus.html").read_bytes() == (EXAMPLES / "tractatus.html").read_bytes()
    props = bt.extract_propositions(bt.load_source(bt._download()))
    for number, raw in props:
        converted = bt.convert(number, raw)
        assert tractatus.evaluate(MATH_TOKENS_JS, converted.paragraphs) == converted.math, number


@pytest.mark.network
def test_example_typesets(page):
    page.goto((EXAMPLES / "tractatus.html").as_uri())
    page.wait_for_function(f"() => {MATH_STATE} !== undefined && {MATH_STATE} !== 'loading'", timeout=180_000)
    states = page.evaluate("[...document.querySelectorAll('.math')].map(s => s.dataset.math)")
    failed = page.evaluate(
        "[...document.querySelectorAll('.math[data-math=\"failed\"]')].map(s => s.dataset.tex)"
    )
    assert failed == []
    assert page.evaluate(MATH_STATE) == "ready"
    assert states and set(states) == {"typeset"}
    # One span per math token of the markdown.
    paragraphs = [p for *_, text in outline(page)["rows"] for p in text.split("\n\n")]
    assert len(states) == len(page.evaluate(MATH_TOKENS_JS, paragraphs))
