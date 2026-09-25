"""Law P and the fixture's expected shape, through window.tractatus.parseOutline."""

import pytest


@pytest.fixture
def parse(open_outline, fake_md):
    page = open_outline(fake_md)
    return lambda md: page.evaluate("md => window.tractatus.parseOutline(md)", md)


@pytest.fixture
def doc(parse, fake_md):
    return parse(fake_md)


def walk(items, parents=()):
    for node in items:
        yield node, parents
        yield from walk(node["children"], (*parents, node))


def find(doc, label):
    return next((node, parents) for node, parents in walk(doc["items"]) if node["label"] == label)


def test_fixture_shape(doc):
    assert doc["title"] == "Tractatus Bibliothecarius"
    assert len(doc["intro"]) == 2
    assert len(doc["items"]) == 8
    assert sum(1 for _ in walk(doc["items"])) == 47
    assert [n["label"] for n in doc["items"]] == ["1", "2", "3", "4", "5", "6", "7", None]
    assert doc["warnings"] == []


def test_nesting_by_relative_indent(doc):
    node, parents = find(doc, "2.01231")
    assert len(parents) + 1 == 5
    assert [p["label"] for p in parents] == ["2", "2.01", "2.012", "2.0123"]

    three, _ = find(doc, "3")
    assert [c["label"] for c in three["children"]] == ["3.001", "3.01", "3.1"]
    assert [c["label"] for c in three["children"][2]["children"]] == ["3.11", "3.12"]

    _, parents = find(doc, "4.011")
    assert parents[-1]["label"] == "4.01"


def test_label_split(doc):
    node, _ = find(doc, "1.1")
    assert node["text"] == "The library is the totality of volumes, not of pages."
    three, _ = find(doc, "3")
    assert three["children"][0]["label"] == "3.001"


def test_escaped_label(doc):
    last = doc["items"][-1]
    assert last["label"] is None
    assert last["text"] == "2024 is not a label, because it is escaped."


def test_label_only_item(parse):
    doc = parse("- 2 Facts.\n  - 2.0\n    - 2.01 An atomic fact.")
    group = doc["items"][0]["children"][0]
    assert (group["label"], group["text"], group["id"]) == ("2.0", "", "2.0")
    assert group["children"][0]["label"] == "2.01"


def test_positional_ids(doc):
    unlabeled = [node["id"] for node, _ in walk(doc["items"]) if node["label"] is None]
    assert unlabeled == ["p-5-3", "p-5-3-1", "p-8"]


def test_lazy_and_paragraph_continuation(doc):
    node, _ = find(doc, "1.12")
    assert node["text"] == "For the totality of volumes determines what is shelved, and also what is lent out."
    node, _ = find(doc, "6.54")
    assert node["text"] == (
        "My call numbers are elucidatory in this way: he who understands me finally "
        "recognizes them as senseless. Lazy continuation of 6.54 at a shallower indent."
        "\n\nA second paragraph of 6.54."
    )


def test_duplicate_labels_fall_back(parse):
    doc = parse("- 1 a\n- 1 b")
    assert [n["id"] for n in doc["items"]] == ["p-1", "p-2"]
    assert [n["label"] for n in doc["items"]] == ["1", "1"]
    assert len([w for w in doc["warnings"] if "duplicate label" in w]) == 1


def test_unindented_paragraph_warns(parse):
    doc = parse("- 1 a\n\nloose")
    assert doc["items"][0]["text"].split("\n\n") == ["a", "loose"]
    assert len(doc["warnings"]) == 1


def test_blank_and_empty(parse):
    doc = parse("")
    assert doc["items"] == []
    assert doc["title"] is None
    doc = parse("- ")
    assert len(doc["items"]) == 1
    assert doc["items"][0]["text"] == ""


TOTALITY_JS = """
seed => {
  function mulberry32(a) {
    return function () {
      a |= 0; a = (a + 0x6d2b79f5) | 0;
      let t = Math.imul(a ^ (a >>> 15), 1 | a);
      t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
      return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
    };
  }
  const rand = mulberry32(seed);
  const pick = (xs) => xs[Math.floor(rand() * xs.length)];
  const countA = (s) => (s.match(/a/g) ?? []).length;
  const failures = [];
  for (let n = 0; n < 500 && failures.length < 3; n++) {
    const lines = [];
    const count = Math.floor(rand() * 12);
    for (let i = 0; i < count; i++) {
      if (rand() < 0.15) { lines.push(""); continue; }
      lines.push(pick(["", "  ", "    "]) + pick(["- ", "* ", "1. ", "3) ", ""]) +
                 pick(["", "1 ", "2.01 ", "\\\\3 "]) + pick(["a", "a b", ""]));
    }
    if (rand() < 0.2) lines.unshift("# a");
    const md = lines.join(rand() < 0.5 ? "\\n" : "\\r\\n");
    let doc;
    try {
      doc = window.tractatus.parseOutline(md);
    } catch (e) {
      failures.push({ md, error: String(e) });
      continue;
    }
    const ids = [];
    let texts = (doc.title ?? "") + doc.intro.join("");
    const visit = (nodes) => { for (const node of nodes) { ids.push(node.id); texts += node.text; visit(node.children); } };
    visit(doc.items);
    if (!ids.every((id) => typeof id === "string" && id !== "")) failures.push({ md, error: "bad id" });
    else if (new Set(ids).size !== ids.length) failures.push({ md, error: "duplicate ids" });
    else if (countA(md) !== countA(texts)) failures.push({ md, error: "lost text" });
  }
  return failures;
}
"""


@pytest.mark.parametrize("seed", [1, 2, 3])
def test_parse_totality(open_outline, fake_md, seed):
    page = open_outline(fake_md)
    assert page.evaluate(TOTALITY_JS, seed) == []
