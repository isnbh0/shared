# /// script
# requires-python = ">=3.13"
# ///
"""Deterministic validator for semantic-zoom documents (see SKILL.md).

Usage: uv run validate.py <doc.html>
Exit 0 = valid; exit 1 = errors (listed on stdout).
"""

import re
import sys
from collections import Counter
from collections.abc import Callable, Iterator
from html.parser import HTMLParser
from pathlib import Path


class Node:
    def __init__(self, tag: str, attrs: list[tuple[str, str | None]], parent: "Node | None") -> None:
        self.tag: str = tag
        self.attrs: dict[str, str | None] = dict(attrs)
        self.parent: Node | None = parent
        self.children: list[Node] = []
        self.text_parts: list[str] = []

    @property
    def classes(self) -> list[str]:
        return (self.attrs.get("class") or "").split()

    def text(self) -> str:
        return "".join(self.text_parts) + "".join(c.text() for c in self.children)

    def walk(self) -> Iterator["Node"]:
        yield self
        for c in self.children:
            yield from c.walk()

    def find_all(self, pred: Callable[["Node"], bool]) -> list["Node"]:
        return [n for n in self.walk() if pred(n)]


VOID: frozenset[str] = frozenset({"meta", "br", "hr", "img", "input", "link"})


class TreeBuilder(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.root: Node = Node("#root", [], None)
        self.cur: Node = self.root

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        node = Node(tag, attrs, self.cur)
        self.cur.children.append(node)
        if tag not in VOID:
            self.cur = node

    def handle_endtag(self, tag: str) -> None:
        n: Node = self.cur
        while n is not self.root and n.tag != tag:
            assert n.parent is not None
            n = n.parent
        if n is not self.root:
            assert n.parent is not None
            self.cur = n.parent

    def handle_data(self, data: str) -> None:
        self.cur.text_parts.append(data)


def tokens(text: str) -> list[str]:
    return re.sub(r"[^\w\s]", " ", text.lower()).split()


def coverage_gate(source_md: str, z3_texts: list[str], err: Callable[[str], None], warn: Callable[[str], None]) -> None:
    """Each substantial source paragraph must be ~contained in some z3's tokens."""
    z3_counters = [Counter(tokens(t)) for t in z3_texts]
    for para in re.split(r"\n\s*\n", source_md):
        para = para.strip()
        ptok = tokens(para)
        if len(ptok) < 8:
            continue
        pcount = Counter(ptok)
        best = max(
            (sum(min(c, z[w]) for w, c in pcount.items()) / len(ptok) for z in z3_counters),
            default=0.0,
        )
        if best < 0.85:
            err(f"source paragraph not covered by any z3 ({best:.0%} best match): {para[:60]!r}...")
    src_len = len(" ".join(tokens(source_md)))
    z3_len = len(" ".join(tokens(" ".join(z3_texts))))
    if src_len and z3_len < 0.6 * src_len:
        warn(f"total z3 text is only {z3_len / src_len:.0%} of the embedded source — z3 may be excerpting")


def validate(html: str) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    err: Callable[[str], None] = errors.append

    # ---- placeholder hygiene (raw text: catches braces anywhere) ----
    if "{{" in html or "}}" in html:
        for m in re.finditer(r"\{\{.{0,50}", html):
            err(f"unfilled placeholder: {m.group(0)!r}...")
    if re.search(r'data-level\s*=\s*(""|\'\')', html):
        err('data-level="" present — renders the section blank; omit the attribute to inherit')

    tb = TreeBuilder()
    tb.feed(html)
    root: Node = tb.root

    def one(scope: Node, desc: str, pred: Callable[[Node], bool]) -> Node | None:
        found = scope.find_all(pred)
        if len(found) != 1:
            err(f"{desc}: expected exactly 1, found {len(found)}")
        return found[0] if found else None

    title = one(root, "<title>", lambda n: n.tag == "title")
    if title is not None and not title.text().strip():
        err("<title> is empty")

    article = one(root, "article#doc", lambda n: n.tag == "article" and n.attrs.get("id") == "doc")
    if article is None:
        return errors, warnings

    header = one(article, "header", lambda n: n.tag == "header")
    if header is not None:
        one(header, "header h1", lambda n: n.tag == "h1")
        one(header, "header .z0", lambda n: "z0" in n.classes)
        one(header, "header .z1", lambda n: "z1" in n.classes)

    sections: list[Node] = article.find_all(lambda n: n.tag == "section")
    if not sections:
        err("no <section> blocks")

    z3_texts: list[str] = []
    for i, s in enumerate(sections, 1):
        where = f"section {i}"
        one(s, f"{where} h2", lambda n: n.tag == "h2")
        z2 = one(s, f"{where} .z2", lambda n: "z2" in n.classes)
        z3 = one(s, f"{where} .z3", lambda n: "z3" in n.classes)
        if z3 is not None:
            z3_texts.append(z3.text())

        # serializer block vocabulary (headings inside a level have no markdown mapping)
        for lvl_name, lvl in (("z2", z2), ("z3", z3)):
            if lvl is None:
                continue
            for b in lvl.find_all(lambda n: n.tag in ("h3", "h4", "h5", "h6")):
                err(f"{where} {lvl_name}: <{b.tag}> unsupported by the markdown serializer (split into sections instead)")

    # ---- coverage gate against the embedded source (skip if absent) ----
    source = root.find_all(
        lambda n: n.tag == "script" and n.attrs.get("type") == "text/markdown" and n.attrs.get("id") == "source"
    )
    if source:
        coverage_gate(source[0].text(), z3_texts, err, warnings.append)

    return errors, warnings


def main() -> None:
    if len(sys.argv) != 2:
        sys.exit("usage: uv run validate.py <doc.html>")
    errors, warnings = validate(Path(sys.argv[1]).read_text())
    for w in warnings:
        print(f"WARNING: {w}")
    for e in errors:
        print(f"ERROR: {e}")
    print(f"{sys.argv[1]}: {'FAIL (' + str(len(errors)) + ' errors)' if errors else 'OK'}")
    sys.exit(1 if errors else 0)


if __name__ == "__main__":
    main()
