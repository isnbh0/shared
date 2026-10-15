# /// script
# requires-python = ">=3.13"
# ///
"""Render the package glossary page from its single source.

    uv run tools/glossary.py            # write video-knowhow-code/Glossary.md
    uv run tools/glossary.py --check    # exit 1 if Glossary.md is not the current render

video-knowhow-code/glossary.toml holds every defined term once: the table key is
the canonical name, so a duplicate definition fails to parse. This script writes
the entries alphabetically under letter headings; each entry is a heading, so its
anchor is the GitHub slug of the term and stays stable while the name does. The
roundup's glossary tables read the same file (roundup/render_static.py), and
tools/termcheck.py enforces the retired variants it lists.
"""

import argparse
import re
import sys
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "video-knowhow-code" / "glossary.toml"
OUTPUT = ROOT / "video-knowhow-code" / "Glossary.md"


def slug(text: str) -> str:
    """GitHub-style heading slug, the same rule linkcheck.py applies."""
    text = re.sub(r"[^\w\- ]", "", text.strip().lower())
    return text.replace(" ", "-")


def load(path: Path = SOURCE) -> dict[str, dict]:
    with path.open("rb") as handle:
        data = tomllib.load(handle)
    terms = data.get("terms", {})
    for name, entry in terms.items():
        if not entry.get("definition", "").strip():
            raise ValueError(f"glossary term {name!r} has no definition")
    return terms


def render(terms: dict[str, dict]) -> str:
    names = sorted(terms, key=lambda n: (n.casefold(), n))
    letters: dict[str, list[str]] = {}
    for name in names:
        letters.setdefault(name[0].upper(), []).append(name)
    seen: dict[str, str] = {}
    for anchor, name in [(slug(n), n) for n in names] + [(slug(k), k) for k in letters]:
        if anchor in seen:
            raise ValueError(f"anchor #{anchor} is shared by {seen[anchor]!r} and {name!r}")
        seen[anchor] = name
    lines = [
        "# Glossary",
        "",
        "<!-- Generated from glossary.toml by ../video-knowhow-craft/tools/glossary.py; edit the TOML, not this page. -->",
        "",
        "Every defined term in the package, defined once here. Other pages link to these entries.",
        "",
        " · ".join(f"[{letter}](#{slug(letter)})" for letter in letters),
        "",
    ]
    for letter, group in letters.items():
        lines += [f"## {letter}", ""]
        for name in group:
            entry = terms[name]
            lines += [f"### {name}", "", entry["definition"].strip(), ""]
            see = entry.get("see", [])
            if see:
                links = ", ".join(f"[{s['text']}]({s['href']})" for s in see)
                lines += [f"See {links}.", ""]
    lines += ["[Home](Home.md)", ""]
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--check", action="store_true", help="fail if Glossary.md differs from the render")
    opts = parser.parse_args()
    text = render(load())
    if opts.check:
        current = OUTPUT.read_text(encoding="utf-8") if OUTPUT.is_file() else ""
        if current != text:
            print(f"{OUTPUT.relative_to(ROOT)} is stale; run tools/glossary.py", file=sys.stderr)
            return 1
        print(f"{OUTPUT.relative_to(ROOT)} matches glossary.toml")
        return 0
    OUTPUT.write_text(text, encoding="utf-8")
    print(f"wrote {OUTPUT.relative_to(ROOT)}: {text.count(chr(10) + '### ')} terms")
    return 0


if __name__ == "__main__":
    sys.exit(main())
