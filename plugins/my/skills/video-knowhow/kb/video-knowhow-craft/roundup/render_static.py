# /// script
# requires-python = ">=3.13"
# dependencies = ["markdown-it-py>=3,<5"]
# ///
"""Render the Markdown roundup's two HTML views from their sources.

    uv run roundup/render_static.py

The roundup's glossary items name their terms as links into the package
Glossary; the definitions themselves live once, in
video-knowhow-code/glossary.toml. This script writes:

- motion-production-roundup-no-js.html: native HTML, each glossary item
  rendered as a table whose rows are the linked terms and their glossary.toml
  definitions, and term uses linked to those rows;
- motion-production-roundup.html: the interactive outline, whose embedded
  copy of the Markdown (the outline-source block) is refreshed from the source.
"""

import html
import json
import re
import tomllib
from pathlib import Path

from markdown_it import MarkdownIt

DIRECTORY = Path(__file__).resolve().parent
SOURCE = DIRECTORY / "motion-production-roundup.md"
OUTPUT = DIRECTORY / "motion-production-roundup-no-js.html"
INTERACTIVE = DIRECTORY / "motion-production-roundup.html"
GLOSSARY = DIRECTORY.parents[1] / "video-knowhow-code" / "glossary.toml"
INLINE = MarkdownIt("commonmark", {"html": False})
# A glossary item lists its terms after "Terms:" as links to Glossary.md#<slug>.
TERMS = re.compile(r"\s*Terms:\s*(.*)$")
TERM_LINK = re.compile(r"\[([^\]]+)\]\([^)#]*Glossary\.md#([^)]+)\)")
# Current preferences, layered over roundup.css after it. Delete this constant's text (or set it
# to "") to return the page to the base look.
PREFERENCES_CSS = """
/* Current preferences, layered over the base design; delete this block to return to the base look. */
.eyebrow { display: none; }
.number { font-family: system-ui, sans-serif; font-variant-numeric: tabular-nums; }
code { font-family: inherit; font-variant-numeric: tabular-nums; }
"""
EMBED = re.compile(r'(<script type="application/json" id="outline-source">)([^<]*)(</script>)')


def slug(text: str) -> str:
    """GitHub-style heading slug, as tools/glossary.py writes the Glossary anchors."""
    return re.sub(r"[^\w\- ]", "", text.strip().lower()).replace(" ", "-")


def load_glossary() -> dict[str, str]:
    """Glossary anchor -> definition, from the single source."""
    with GLOSSARY.open("rb") as handle:
        terms = tomllib.load(handle)["terms"]
    return {slug(name): entry["definition"].strip() for name, entry in terms.items()}


DEFINITIONS = load_glossary()


def split_terms(content: str) -> tuple[str, str]:
    """(leading text, the "Terms:" link list) of a glossary item."""
    match = TERMS.search(content)
    return (content[: match.start()], match[1]) if match else (content, "")


def definitions(content: str) -> list[tuple[str, str]]:
    entries = []
    for term, anchor in TERM_LINK.findall(split_terms(content)[1]):
        if anchor not in DEFINITIONS:
            raise ValueError(f"roundup glossary links #{anchor}, which glossary.toml does not define")
        entries.append((term, DEFINITIONS[anchor]))
    return entries


def term_id(label: str, term: str) -> str:
    return f"term-{label}-{re.sub(r'[^a-z0-9]+', '-', term.lower()).strip('-')}"


def render() -> str:
    text = SOURCE.read_text(encoding="utf-8")
    title, remainder = text.split("\n", 1)
    title = title.removeprefix("# ")
    preamble, outline = remainder.split("\n- ", 1)
    paragraphs = preamble.strip().split("\n\n")
    roots: list[dict] = []
    stack: list[tuple[int, dict]] = []
    glossaries = {"root": paragraphs[0]}
    for line in ("- " + outline).splitlines():
        if not line.strip():
            continue
        match = re.fullmatch(r"( *)- (\d+(?:\.\d+)*) (.+)", line)
        if match is None:
            raise ValueError(f"Unsupported outline line: {line}")
        indent, label, content = match.groups()
        node = {"label": label, "content": content, "children": []}
        if label.endswith(".0"):
            glossaries[label] = content
        while stack and stack[-1][0] >= len(indent):
            stack.pop()
        siblings = stack[-1][1]["children"] if stack else roots
        siblings.append(node)
        stack.append((len(indent), node))

    def glossary_scope(label: str) -> dict[str, str]:
        content = glossaries[label]
        imported = {}
        for reference in re.findall(r"\]\(#([^)]*)\)", content):
            if reference in glossaries and reference != label:
                imported.update(glossary_scope(reference))
        imported.update({term: term_id(label, term) for term, _ in definitions(content)})
        return imported

    global_scope = glossary_scope("root")

    def highlighted_text(tokens, idx, options, env):
        value = tokens[idx].content
        # Existing links and code keep their own meaning and never gain nested anchors.
        inside_link = sum(
            token.nesting for token in tokens[:idx] if token.type in {"link_open", "link_close"}
        )
        scope = env.get("terms", {})
        if inside_link or not scope:
            return html.escape(value)
        terms = sorted(scope, key=len, reverse=True)
        pattern = re.compile(r"(?<!\w)(" + "|".join(map(re.escape, terms)) + r")(s?)(?!\w)", re.I)
        lookup = {term.lower(): target for term, target in scope.items()}
        pieces = []
        cursor = 0
        for match in pattern.finditer(value):
            pieces.append(html.escape(value[cursor : match.start()]))
            target = lookup[match[1].lower()]
            pieces.append(
                f'<a class="glossary-term" href="#{target}"><strong>'
                f'{html.escape(match[0])}</strong></a>'
            )
            cursor = match.end()
        pieces.append(html.escape(value[cursor:]))
        return "".join(pieces)

    INLINE.renderer.rules["text"] = highlighted_text

    def inline(content: str, scope=None) -> str:
        return INLINE.renderInline(content, {"terms": scope or {}})

    def glossary(label: str, content: str, caption: str) -> str:
        entries = definitions(content)
        leading = split_terms(content)[0]
        leading = re.sub(r"^\*\*(?:Global|Section|Subsection) glossary\.\*\*\s*", "", leading)
        rows = []
        if leading.strip():
            rows.append(f'<tr><th scope="row">Shared terms</th><td>{inline(leading)}</td></tr>')
        for term, definition in entries:
            anchor = term_id(label, term)
            rows.append(
                f'<tr><th scope="row"><dfn id="{anchor}">{html.escape(term)}</dfn></th>'
                f'<td>{inline(definition, global_scope | glossary_scope(label))}</td></tr>'
            )
        return (
            f'<div class="glossary"><table><caption>{html.escape(caption)}</caption>'
            '<colgroup><col class="term-column"><col></colgroup>'
            '<thead><tr><th scope="col">Term</th><th scope="col">Meaning here</th></tr></thead>'
            f'<tbody>{"".join(rows)}</tbody></table></div>'
        )

    def item(node: dict, scope: dict, depth: int = 0) -> str:
        label, content = node["label"], node["content"]
        if node["children"]:
            scope = scope | glossary_scope(node["children"][0]["label"])
            children = "\n".join(item(child, scope, depth + 1) for child in node["children"])
            level = min(depth + 2, 6)
            return (
                f'<li><section aria-labelledby="heading-{label}"><details id="{label}" open>'
                f'<summary><h{level} id="heading-{label}"><span class="number">{label}</span> '
                f'{inline(content, scope)}</h{level}></summary>'
                f'<ol>{children}</ol></details></section></li>'
            )
        if label.endswith(".0"):
            caption = f'{label} · {"Section" if depth == 1 else "Subsection"} glossary'
            return f'<li id="{label}">{glossary(label, content, caption)}</li>'
        return (
            f'<li id="{label}"><p><span class="number">{label}</span> '
            f'{inline(content, scope)}</p></li>'
        )

    navigation = []
    for node in roots:
        children = "".join(
            f'<li><a href="#{child["label"]}"><span>{child["label"]}</span> '
            f'{inline(child["content"])}</a></li>'
            for child in node["children"] if child["children"]
        )
        navigation.append(
            f'<li><a class="nav-section" href="#{node["label"]}">{node["label"]}. '
            f'{inline(node["content"])}</a><ul>{children}</ul></li>'
        )
    body = "\n".join(item(node, global_scope) for node in roots)
    intro = "\n".join(f'<p>{inline(paragraph, global_scope)}</p>' for paragraph in paragraphs[1:])
    css = (DIRECTORY / "roundup.css").read_text(encoding="utf-8")
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="color-scheme" content="light dark">
<meta http-equiv="Content-Security-Policy" content="default-src 'none'; style-src 'unsafe-inline'; script-src 'none'; base-uri 'none'; form-action 'none'">
<title>{html.escape(title)}</title>
<style>{css}{PREFERENCES_CSS}</style>
</head>
<body>
<a class="skip-link" href="#content">Skip to the outline</a>
<div class="document">
<header id="root">
<p class="eyebrow">Motion production · A numbered field guide</p>
<h1>{html.escape(title)}</h1>
{glossary('root', paragraphs[0], 'Global glossary')}
{intro}
</header>
<main id="content" aria-label="Numbered outline"><ol class="outline">{body}</ol></main>
<footer><a href="motion-production-roundup.md">Markdown source</a> · <a href="#root">Back to the glossary</a></footer>
</div>
<nav id="section-nav" popover="auto" aria-labelledby="nav-title">
<div class="nav-heading"><h2 id="nav-title">Jump to a section</h2>
<button type="button" popovertarget="section-nav" popovertargetaction="hide" aria-label="Close navigation">Close</button></div>
<ul>{''.join(navigation)}</ul>
</nav>
<button class="nav-toggle" type="button" popovertarget="section-nav" aria-label="Toggle section navigation">
<span aria-hidden="true">☰</span> Sections</button>
</body>
</html>
"""


def embed() -> None:
    """Refresh the interactive page's embedded Markdown (the encoding tractatus embed.py uses)."""
    page = INTERACTIVE.read_text(encoding="utf-8")
    encoded = json.dumps(SOURCE.read_text(encoding="utf-8"), ensure_ascii=False).replace("<", "\\u003c")
    updated, count = EMBED.subn(lambda m: m[1] + encoded + m[3], page)
    if count != 1:
        raise ValueError(f"{INTERACTIVE.name}: expected one outline-source block, found {count}")
    INTERACTIVE.write_text(updated, encoding="utf-8")


if __name__ == "__main__":
    OUTPUT.write_text(render(), encoding="utf-8")
    print(OUTPUT)
    embed()
    print(INTERACTIVE)
