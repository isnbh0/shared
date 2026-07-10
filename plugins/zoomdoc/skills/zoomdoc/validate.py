# /// script
# requires-python = ">=3.13"
# ///
"""Validate a zoomdoc v3 semantic HTML document.

Usage: uv run validate.py <doc.html>
Exit 0 = valid; exit 1 = errors (listed on stdout).
"""

from __future__ import annotations

import re
import sys
from collections import Counter
from collections.abc import Callable, Iterator
from html.parser import HTMLParser
from pathlib import Path


VOID = frozenset(
    {
        "area",
        "base",
        "br",
        "col",
        "embed",
        "hr",
        "img",
        "input",
        "link",
        "meta",
        "source",
        "track",
        "wbr",
    }
)
HEADINGS = frozenset({"h1", "h2", "h3", "h4", "h5", "h6"})
SECTIONING = frozenset({"article", "aside", "nav", "section"})
NONCONTENT = frozenset({"script", "style", "template"})
LEVEL_ID = re.compile(r"^[a-z][a-z0-9-]*$")
SAFE_NONEXECUTABLE_SCRIPTS = frozenset({"application/json", "application/ld+json"})


class Node:
    def __init__(
        self, tag: str, attrs: list[tuple[str, str | None]], parent: Node | None
    ) -> None:
        self.tag = tag
        self.attrs = dict(attrs)
        self.parent = parent
        self.items: list[str | Node] = []

    @property
    def classes(self) -> list[str]:
        return (self.attrs.get("class") or "").split()

    def children(self) -> list[Node]:
        return [item for item in self.items if isinstance(item, Node)]

    def text(self, *, skip: frozenset[str] = frozenset()) -> str:
        parts: list[str] = []
        for item in self.items:
            if isinstance(item, str):
                parts.append(item)
            elif item.tag not in skip:
                parts.append(item.text(skip=skip))
        return "".join(parts)

    def walk(self) -> Iterator[Node]:
        yield self
        for child in self.children():
            yield from child.walk()

    def find_all(self, pred: Callable[[Node], bool]) -> list[Node]:
        return [node for node in self.walk() if pred(node)]

    def direct(self, pred: Callable[[Node], bool]) -> list[Node]:
        return [node for node in self.children() if pred(node)]


class TreeBuilder(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.root = Node("#root", [], None)
        self.current = self.root

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        node = Node(tag, attrs, self.current)
        self.current.items.append(node)
        if tag not in VOID:
            self.current = node

    def handle_startendtag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        node = Node(tag, attrs, self.current)
        self.current.items.append(node)

    def handle_endtag(self, tag: str) -> None:
        node = self.current
        while node is not self.root and node.tag != tag:
            assert node.parent is not None
            node = node.parent
        if node is not self.root:
            assert node.parent is not None
            self.current = node.parent

    def handle_data(self, data: str) -> None:
        self.current.items.append(data)


def level_tokens(node: Node) -> list[str]:
    return (node.attrs.get("data-zoomdoc-at") or "").split()


def tokens(text: str) -> list[str]:
    return re.sub(r"[^\w\s]", " ", text.lower()).split()


def projection_text(node: Node, level: str) -> str:
    parts: list[str] = []

    def visit(item: str | Node) -> None:
        if isinstance(item, str):
            parts.append(item)
            return
        if item.tag in NONCONTENT:
            return
        if "data-zoomdoc-at" in item.attrs and level not in level_tokens(item):
            return
        for child in item.items:
            visit(child)

    visit(node)
    return " ".join("".join(parts).split())


def coverage_gate(
    source: str,
    finest_text: str,
    err: Callable[[str], None],
    warn: Callable[[str], None],
) -> None:
    """Check strict transcription coverage against the complete finest projection."""
    finest_counter = Counter(tokens(finest_text))
    source_tokens = tokens(source)

    for paragraph in re.split(r"\n\s*\n", source):
        paragraph = paragraph.strip()
        paragraph_tokens = tokens(paragraph)
        if len(paragraph_tokens) < 8:
            continue
        paragraph_counter = Counter(paragraph_tokens)
        overlap = sum(
            min(count, finest_counter[word])
            for word, count in paragraph_counter.items()
        )
        ratio = overlap / len(paragraph_tokens)
        if ratio < 0.85:
            err(
                f"source paragraph insufficiently covered by the finest projection ({ratio:.0%}): {paragraph[:70]!r}..."
            )

    finest_tokens = tokens(finest_text)
    if source_tokens and len(finest_tokens) < 0.6 * len(source_tokens):
        warn(
            f"finest projection contains only {len(finest_tokens) / len(source_tokens):.0%} as many tokens as the source"
        )


def own_section_headings(node: Node) -> list[Node]:
    found: list[Node] = []

    def visit(current: Node) -> None:
        for child in current.children():
            if child.tag in HEADINGS:
                found.append(child)
            if child.tag in SECTIONING:
                continue
            visit(child)

    visit(node)
    return found


def nearest_zoom_unit(node: Node) -> Node | None:
    current = node.parent
    while current is not None:
        if "data-zoomdoc-unit" in current.attrs:
            return current
        current = current.parent
    return None


def validate(html: str) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []
    err = errors.append
    warn = warnings.append

    for match in re.finditer(r"\{\{[A-Z][A-Z0-9_]*\}\}", html):
        err(f"unfilled template placeholder: {match.group(0)!r}")

    tree = TreeBuilder()
    try:
        tree.feed(html)
    except Exception as exc:
        err(f"HTML parser failed: {exc}")
        return errors, warnings
    root = tree.root

    def exactly_one(
        scope: Node, description: str, pred: Callable[[Node], bool]
    ) -> Node | None:
        found = scope.find_all(pred)
        if len(found) != 1:
            err(f"{description}: expected exactly 1, found {len(found)}")
        return found[0] if found else None

    html_node = exactly_one(root, "html element", lambda node: node.tag == "html")
    if html_node is not None and not (html_node.attrs.get("lang") or "").strip():
        err("html element requires a non-empty lang attribute")

    title = exactly_one(root, "title element", lambda node: node.tag == "title")
    if title is not None and not title.text().strip():
        err("title element is empty")

    charset = root.find_all(lambda node: node.tag == "meta" and "charset" in node.attrs)
    if not charset:
        warn("missing meta charset")
    viewport = root.find_all(
        lambda node: node.tag == "meta"
        and (node.attrs.get("name") or "").lower() == "viewport"
    )
    if not viewport:
        warn("missing viewport metadata")

    document = exactly_one(
        root, "zoomdoc root", lambda node: "data-zoomdoc" in node.attrs
    )
    if document is None:
        return errors, warnings
    if document.tag != "article":
        err(f"zoomdoc root must be an article, found <{document.tag}>")

    levels = (document.attrs.get("data-zoomdoc-levels") or "").split()
    if len(levels) < 2:
        err("data-zoomdoc-levels requires at least two ordered level identifiers")
    if len(levels) != len(set(levels)):
        err("data-zoomdoc-levels contains duplicate identifiers")
    for level in levels:
        if not LEVEL_ID.fullmatch(level):
            err(
                f"invalid level identifier {level!r}; use lowercase letters, digits, and hyphens"
            )

    finest = levels[-1] if levels else ""
    initial = document.attrs.get("data-zoomdoc-initial")
    if initial and initial not in levels:
        err(f"data-zoomdoc-initial {initial!r} is not declared in data-zoomdoc-levels")
    if "data-zoomdoc-current" in document.attrs:
        err(
            "data-zoomdoc-current is runtime state and must not appear in the authored document"
        )
    if "data-zoomdoc-at" in document.attrs:
        err("the zoomdoc root cannot be level-controlled")
    for attribute in ("data-zoomdoc-control-label", "data-zoomdoc-detail-label"):
        if (
            attribute in document.attrs
            and not (document.attrs.get(attribute) or "").strip()
        ):
            err(f"{attribute} must not be empty")
    for level in levels:
        attribute = f"data-zoomdoc-label-{level}"
        if (
            attribute in document.attrs
            and not (document.attrs.get(attribute) or "").strip()
        ):
            err(f"{attribute} must not be empty")

    h1s = document.find_all(lambda node: node.tag == "h1")
    if len(h1s) != 1:
        err(f"zoomdoc document requires exactly one h1, found {len(h1s)}")

    all_nodes = list(root.walk())
    ids: dict[str, Node] = {}
    for node in all_nodes:
        node_id = node.attrs.get("id")
        if not node_id:
            continue
        if node_id in ids:
            err(f"duplicate id {node_id!r}")
        ids[node_id] = node

    controlled = document.find_all(lambda node: "data-zoomdoc-at" in node.attrs)
    if not controlled:
        err("zoomdoc contains no data-zoomdoc-at elements")

    for node in controlled:
        declared = level_tokens(node)
        where = f"<{node.tag} data-zoomdoc-at={node.attrs.get('data-zoomdoc-at')!r}>"
        if not declared:
            err(f"{where} declares no levels")
            continue
        if len(declared) != len(set(declared)):
            err(f"{where} contains duplicate level identifiers")
        unknown = [level for level in declared if level not in levels]
        if unknown:
            err(f"{where} uses undeclared levels: {', '.join(unknown)}")

        ancestor = node.parent
        reachable = set(levels)
        while ancestor is not None and ancestor is not document.parent:
            if "data-zoomdoc-at" in ancestor.attrs:
                reachable &= set(level_tokens(ancestor))
            ancestor = ancestor.parent
        unreachable = set(declared) - reachable
        if unreachable:
            err(
                f"{where} declares levels hidden by an ancestor: {', '.join(sorted(unreachable))}"
            )

        hidden = "hidden" in node.attrs
        should_be_hidden = finest not in declared
        if hidden != should_be_hidden:
            expected = "include hidden" if should_be_hidden else "omit hidden"
            err(
                f"{where} must {expected} so the no-JavaScript fallback shows only {finest!r}"
            )

    units = document.find_all(lambda node: "data-zoomdoc-unit" in node.attrs)
    for index, unit in enumerate(units, 1):
        where = f"zoom unit {unit.attrs.get('id') or index!r}"
        if not unit.attrs.get("id"):
            err(f"{where} requires a stable id")
        if "data-zoomdoc-override" in unit.attrs:
            err(
                f"{where}: data-zoomdoc-override is runtime state and must not be authored"
            )

        headers = unit.direct(lambda node: node.tag == "header")
        if len(headers) != 1:
            err(
                f"{where} requires exactly one direct header child, found {len(headers)}"
            )
        elif len(own_section_headings(headers[0])) != 1:
            err(f"{where} header requires exactly one heading")

        contents = unit.direct(lambda node: "data-zoomdoc-unit-content" in node.attrs)
        if len(contents) != 1:
            err(
                f"{where} requires exactly one direct data-zoomdoc-unit-content child, found {len(contents)}"
            )
        elif finest:
            detail_targets = contents[0].find_all(
                lambda node: "data-zoomdoc-at" in node.attrs
                and nearest_zoom_unit(node) is unit
                and finest in level_tokens(node)
                and set(level_tokens(node)) != set(levels)
            )
            if not detail_targets:
                warn(
                    f"{where} has no finest-only detail to reveal; remove data-zoomdoc-unit if local zoom is unnecessary"
                )
            for target in detail_targets:
                if not target.attrs.get("id"):
                    err(
                        f"{where} finest-only <{target.tag}> requires an id for aria-controls"
                    )

    def has_accessible_name(node: Node) -> bool:
        if own_section_headings(node):
            return True
        if (node.attrs.get("aria-label") or "").strip():
            return True
        references = (node.attrs.get("aria-labelledby") or "").split()
        return bool(references) and all(
            reference in ids and ids[reference].text(skip=NONCONTENT).strip()
            for reference in references
        )

    for section in document.find_all(lambda node: node.tag in SECTIONING):
        if section is document:
            continue
        if not has_accessible_name(section):
            warn(
                f"<{section.tag}> without an own heading or accessible name; use a div if it is only a script or style container"
            )

    for image in document.find_all(lambda node: node.tag == "img"):
        if "alt" not in image.attrs:
            err(
                f"img{f'#{image.attrs.get("id")}' if image.attrs.get('id') else ''} requires alt (empty for decorative images)"
            )

    scripts = root.find_all(lambda node: node.tag == "script")
    runtimes = [node for node in scripts if "data-zoomdoc-runtime" in node.attrs]
    if len(runtimes) != 1:
        err(f"expected exactly one data-zoomdoc-runtime script, found {len(runtimes)}")
    for script in scripts:
        if "data-zoomdoc-runtime" in script.attrs:
            continue
        script_type = (script.attrs.get("type") or "").lower()
        if script_type not in SAFE_NONEXECUTABLE_SCRIPTS:
            err(
                f"authored executable script is not allowed (type={script_type or 'text/javascript'!r})"
            )

    sources = root.find_all(lambda node: node.attrs.get("id") == "zoomdoc-source")
    if len(sources) > 1:
        err(f"zoomdoc-source: expected at most 1, found {len(sources)}")
    source = sources[0] if sources else None
    if source is not None and source.tag != "template":
        err("zoomdoc-source must be a template element")

    source_mode = document.attrs.get("data-zoomdoc-source-mode")
    if source_mode and source_mode != "transcription":
        err(
            f"unsupported data-zoomdoc-source-mode {source_mode!r}; omit it or use 'transcription'"
        )
    if source_mode == "transcription":
        if source is None:
            err("transcription mode requires template#zoomdoc-source")
        else:
            source_text = source.text(skip=frozenset({"script", "style"})).strip()
            if not source_text:
                err("template#zoomdoc-source is empty")
            elif finest:
                coverage_gate(source_text, projection_text(document, finest), err, warn)

    return errors, warnings


def main() -> None:
    if len(sys.argv) != 2:
        sys.exit("usage: uv run validate.py <doc.html>")
    path = Path(sys.argv[1])
    errors, warnings = validate(path.read_text(encoding="utf-8"))
    for warning in warnings:
        print(f"WARNING: {warning}")
    for error in errors:
        print(f"ERROR: {error}")
    print(f"{path}: {'FAIL (' + str(len(errors)) + ' errors)' if errors else 'OK'}")
    raise SystemExit(1 if errors else 0)


if __name__ == "__main__":
    main()
