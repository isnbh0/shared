# /// script
# requires-python = ">=3.13"
# ///
"""Deterministic validator for semantic-zoom documents (see schema.md).

Usage: uv run validate.py <doc.html>
Exit 0 = valid; exit 1 = errors (listed on stdout).
"""

import re
import sys
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


def validate(html: str) -> list[str]:
    errors: list[str] = []
    err: Callable[[str], None] = errors.append

    # ---- placeholder hygiene (raw text: catches braces anywhere) ----
    if "{{" in html or "}}" in html:
        for m in re.finditer(r"\{\{.{0,50}", html):
            err(f"unfilled placeholder: {m.group(0)!r}...")
    if "s1-example" in html:
        err("sample key 's1-example' left in document")
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
        return errors
    if article.attrs.get("data-doc-level") != "2":
        err('article data-doc-level must ship as "2" (zoom bar aria-pressed is hardcoded to it)')

    header = one(article, "header", lambda n: n.tag == "header")
    if header is not None:
        one(header, "header h1", lambda n: n.tag == "h1")
        one(header, "header .z0", lambda n: "z0" in n.classes)
        one(header, "header .z1", lambda n: "z1" in n.classes)

    sections: list[Node] = article.find_all(lambda n: n.tag == "section")
    if not sections:
        err("no <section> blocks")

    seen_keys: dict[str, int] = {}  # key -> section index (document uniqueness)
    for i, s in enumerate(sections, 1):
        where = f"section {i}"
        one(s, f"{where} h2", lambda n: n.tag == "h2")
        one(s, f"{where} .sec-head", lambda n: "sec-head" in n.classes)
        one(s, f"{where} .sec-zoom button", lambda n: n.tag == "button" and "sec-zoom" in n.classes)
        one(s, f"{where} .sec-copy button", lambda n: n.tag == "button" and "sec-copy" in n.classes)
        z2 = one(s, f"{where} .z2", lambda n: "z2" in n.classes)
        z3 = one(s, f"{where} .z3", lambda n: "z3" in n.classes)
        if z2 is None or z3 is None:
            continue

        # serializer block vocabulary
        for lvl_name, lvl in (("z2", z2), ("z3", z3)):
            for b in lvl.find_all(lambda n: n.tag in ("ol", "blockquote", "pre", "h3", "h4")):
                err(f"{where} {lvl_name}: <{b.tag}> unsupported by the markdown serializer (use p/ul/table)")

        # provenance keys: bijective per section, non-empty, no nesting
        def keys_of(lvl: Node, lvl_name: str) -> dict[str, int]:
            out: dict[str, int] = {}
            for x in lvl.find_all(lambda n: n.tag == "x"):
                k = x.attrs.get("k")
                if not k:
                    err(f"{where} {lvl_name}: <x> without k attribute")
                    continue
                if not x.text().strip():
                    err(f"{where} {lvl_name}: <x k={k!r}> wraps no text")
                if x.find_all(lambda n: n.tag == "x") != [x]:
                    err(f"{where} {lvl_name}: <x k={k!r}> contains a nested <x>")
                out[k] = out.get(k, 0) + 1
            return out

        k2, k3 = keys_of(z2, "z2"), keys_of(z3, "z3")
        for k in {**k2, **k3}:
            if k2.get(k, 0) != 1 or k3.get(k, 0) != 1:
                err(
                    f"{where}: key {k!r} must appear exactly once in z2 and once in z3 "
                    f"(found z2={k2.get(k, 0)}, z3={k3.get(k, 0)})"
                )
            prev = seen_keys.get(k)
            if prev is not None and prev != i:
                err(f"key {k!r} reused across sections {prev} and {i} — keys are document-unique")
            seen_keys[k] = i

    return errors


def main() -> None:
    if len(sys.argv) != 2:
        sys.exit("usage: uv run validate.py <doc.html>")
    errors = validate(Path(sys.argv[1]).read_text())
    for e in errors:
        print(f"ERROR: {e}")
    print(f"{sys.argv[1]}: {'FAIL (' + str(len(errors)) + ' errors)' if errors else 'OK'}")
    sys.exit(1 if errors else 0)


if __name__ == "__main__":
    main()
