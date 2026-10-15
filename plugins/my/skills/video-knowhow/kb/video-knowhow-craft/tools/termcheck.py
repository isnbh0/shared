# /// script
# requires-python = ">=3.13"
# ///
"""Check shipped prose against the package glossary.

    uv run tools/termcheck.py              # whole package: retired variants, unused terms, stale page
    uv run tools/termcheck.py FILE...      # retired variants in the given files only

The glossary (video-knowhow-code/glossary.toml) lists, per term, the retired
variants that must not appear in shipped prose. This script scans the markdown
the package ships: both shelves, minus each comparison/ lab, the code shelf's
lintable-video-system-prelim.md and the roundup's review/ folder (the same
selection as package.py), plus the package's root README.md and AGENTS.md when
present and the package templates in tools/. In a git checkout the files that
could ship count: tracked files and untracked files Git does not ignore, minus
the code shelf's TIL.md, a private scratch file.

Exempt from the scan: fenced code, inline code, HTML comments, link targets,
bare URLs, and quoted source text: in sources/excerpts/, passages in double
quotes and blockquote lines. Elsewhere a double-quoted passage is exempt only
when its exact text is listed under [allow] quoted in glossary.toml. A glossary
entry with quoted_ok = true (a spelling rule such as dialog/dialogue) also lets
its variants stand inside double quotes on any page, since quoted sources keep
their own spelling. An inline-code span whose whole content is listed under a
term's retired_code still counts as a hit.

Evidence labels (law 5) form a closed grammar. The code shelf's Editorial notes
("Reading a claim") states it for readers: heads, qualifiers, and shape. The
enforcement detail below lives only here. A bold span whose text ends in a
colon inside the bold is an evidence label, and it must read exactly
**HEAD:** or **HEAD (qualifier):**, where HEAD is Checked, Reported,
Interpretation, Untested idea, or Source status: supported|partly|practice|open,
and the qualifier is one of that head's entries in QUALIFIERS. A bold span that
starts with one of those heads must match the same grammar. Structural lead-ins
put the colon outside the bold (**Fonts**:) or end in a period (**Fonts.**). A
paragraph or list item that starts with a head, or with a retired label word
(Case values, External support, Observed in trace, Inferred, Holds by
construction, Practice), plus an optional parenthetical and a colon outside bold
is an unbolded label and fails too. Prose bold is ** only: __bold__, <b> and
<strong> fail, and so does a ** left open at the end of a line (a bold span
that crosses a line break). A colon inside bold is the ASCII colon: a bold span
holding a colon written as an HTML entity (&#58;, &#x3a;, &colon;) or as a
look-alike character (U+2236, U+FF1A, U+FE55, U+A789) fails. sources/excerpts/
is exempt from this check.

Shipped prose holds no gendered third-person pronouns: he, him, his, she, her,
hers, himself, herself, as whole words in any case. Name the person (John) or
recast the sentence. The same exemptions apply: code, link targets, URLs, and
quoted text in sources/excerpts/.

Residual: a label written with its colon outside the bold (**Seen in frames**:)
reads the same as a structural lead-in, so the check cannot tell them apart.

A whole-package run also fails when a glossary term is used nowhere outside the
glossary (the Glossary page and the roundup's glossary rows do not count as
use), and when Glossary.md is not the current render of glossary.toml. Every
hit is printed as file:line; the exit status is non-zero on any finding.
"""

import argparse
import importlib.util
import os
import re
import subprocess
import sys
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TOOLS = Path(__file__).resolve().parent
KBS = ("video-knowhow-code", "video-knowhow-craft")
GLOSSARY_TOML = ROOT / "video-knowhow-code" / "glossary.toml"
GLOSSARY_PAGE = Path("video-knowhow-code/Glossary.md")
ROOT_FILES = ("README.md", "AGENTS.md", "ATTRIBUTION.md")
EXCLUDED = (
    "video-knowhow-code/lintable-video-system-prelim.md",
    "video-knowhow-code/TIL.md",
)
EXCLUDED_DIRS = ("video-knowhow-craft/roundup/review/",)

FENCE = re.compile(r"^\s*(```|~~~)")
CODE_SPAN = re.compile(r"(`+)((?:(?!\1).)+?)\1")
COMMENT = re.compile(r"<!--.*?-->", re.S)
LINK_TARGET = re.compile(r"(\]\()(<[^>]*>|[^\s()]*(?:\([^\s()]*\)[^\s()]*)*)((?:\s+\"[^\"]*\")?\))")
URL = re.compile(r"<?https?://[^\s>)]+>?")
QUOTED = re.compile(r"\"[^\"\n]*\"|“[^”\n]*”")
BOLD = re.compile(r"\*\*(?=\S)(.+?)(?<=\S)\*\*")
LABEL_HEADS = r"Checked|Reported|Interpretation|Untested idea|Source status"
LABEL_HEAD = re.compile(rf"^(?:{LABEL_HEADS})\b")
LABEL = re.compile(
    r"^(Checked|Reported|Interpretation|Untested idea"
    r"|Source status: (?:supported|partly|practice|open))(?: \(([^()]+)\))?:$"
)
QUALIFIERS = {
    "Checked": ("SLASH_MY", "AX DAY reconstruction", "both productions", "one machine"),
    "Reported": ("SLASH_MY", "AX DAY reconstruction", "chatlog", "commit", "run notes",
                 "recorded revision", "comparison-run record"),
    "Interpretation": ("SLASH_MY", "AX DAY reconstruction"),
    "Untested idea": (),
    "Source status": ("secondary", "vendor", "product review", "one example"),
}
BOLD_ANY = re.compile(r"\*\*.+?\*\*")  # pairs, even around blanked inline code
OTHER_BOLD = re.compile(r"(?<!\w)__(?=\S).+?(?<=\S)__(?!\w)|</?(?:b|strong)\b[^>]*>", re.I)
PLAIN_LABEL = re.compile(
    rf"^\s*(?:[-*+]\s+|\d+\.\s+)?((?:{LABEL_HEADS}|Case values|External support|Observed in trace"
    r"|Inferred(?: lesson)?|Holds by construction|Practice)(?: \([^()]*\))?:)"
)
COLON_LOOKALIKE = re.compile(r"&#0*58;|&#x0*3a;|&colon;|[\u2236\uff1a\ufe55\ua789]", re.I)
PRONOUN = re.compile(r"(?<![^\W_])(?:he|him|his|she|her|hers|himself|herself)(?![^\W_])", re.I)
ROUNDUP_GLOSSARY = re.compile(r"\*\*(?:Global|Section|Subsection) glossary\.\*\*")


def compile_variant(variant: str) -> re.Pattern[str]:
    if variant.startswith("re:"):
        return re.compile(variant[3:])
    return re.compile(r"(?<!\w)" + re.escape(variant) + r"(?!\w)", re.I)


Retired = list[tuple[re.Pattern[str], str, bool]]


def load() -> tuple[dict, Retired, dict[str, str], re.Pattern[str] | None]:
    with GLOSSARY_TOML.open("rb") as handle:
        data = tomllib.load(handle)
    terms = data.get("terms", {})
    retired: Retired = []
    code: dict[str, str] = {}
    for group in ("terms", "plain"):
        for name, entry in data.get(group, {}).items():
            for variant in entry.get("retired", []):
                retired.append((compile_variant(variant), name, entry.get("quoted_ok", False)))
            for span in entry.get("retired_code", []):
                code[span] = name
    allowed: list[str] = data.get("allow", {}).get("quoted", [])
    alts = "|".join(re.escape(s) for s in sorted(allowed, key=len, reverse=True))
    allow = re.compile(rf"\"(?:{alts})\"|“(?:{alts})”") if allowed else None
    return terms, retired, code, allow


def candidates() -> set[str] | None:
    """Paths (relative to ROOT) that could ship: tracked plus untracked, unignored files.

    None outside a git checkout."""
    result = subprocess.run(
        ["git", "-C", str(ROOT), "ls-files", "-z", "--cached", "--others", "--exclude-standard",
         "--", *KBS, *ROOT_FILES],
        capture_output=True,
        text=True,
    )
    if result.returncode:
        return None
    return {p for p in result.stdout.split("\0") if p}


def shipped() -> list[Path]:
    found = []
    for kb in KBS:
        for dirpath, dirnames, filenames in os.walk(ROOT / kb):
            rel_dir = Path(dirpath).relative_to(ROOT).as_posix() + "/"
            dirnames[:] = sorted(
                d
                for d in dirnames
                if d not in ("comparison", "node_modules")
                and not d.startswith(".")
                and not (rel_dir + d + "/").startswith(EXCLUDED_DIRS)
            )
            for name in sorted(filenames):
                rel = rel_dir + name
                if (name.endswith(".md") or name.endswith(".md.tmpl")) and rel not in EXCLUDED:
                    found.append(ROOT / rel)
    found += [ROOT / name for name in ROOT_FILES if (ROOT / name).is_file()]
    git = candidates()
    if git is not None:
        found = [p for p in found if p.relative_to(ROOT).as_posix() in git]
    return found


def prose(
    path: Path, code: dict[str, str], allow: re.Pattern[str] | None
) -> tuple[list[str], list[tuple[int, str, str]]]:
    """Lines with exempt text blanked (numbering kept), plus retired inline-code hits."""
    text = COMMENT.sub(lambda m: "\n" * m.group(0).count("\n"), path.read_text(encoding="utf-8"))
    excerpt = "sources/excerpts/" in path.as_posix()
    lines, hits, fence = [], [], None
    for n, line in enumerate(text.split("\n"), 1):
        m = FENCE.match(line)
        if m and (fence is None or m.group(1) == fence):
            fence = None if fence else m.group(1)
            lines.append("")
            continue
        if fence or (excerpt and line.lstrip().startswith(">")):
            lines.append("")
            continue
        for span in CODE_SPAN.finditer(line):
            if span.group(2).strip() in code:
                hits.append((n, f"`{span.group(2).strip()}`", code[span.group(2).strip()]))
        line = CODE_SPAN.sub(" ", line)
        line = LINK_TARGET.sub(r"\1\3", line)
        line = URL.sub(" ", line)
        if excerpt:
            line = QUOTED.sub(" ", line)
        elif allow is not None:
            line = allow.sub(" ", line)
        lines.append(line)
    return lines, hits


def label_ok(text: str) -> bool:
    m = LABEL.match(text)
    if m is None:
        return False
    head = "Source status" if m.group(1).startswith("Source status") else m.group(1)
    return m.group(2) is None or m.group(2) in QUALIFIERS[head]


def bad_labels(line: str) -> list[str]:
    """Bold spans that break the evidence-label grammar, unbolded label lead-ins, and
    bold written other than as one-line ** spans (law 5)."""
    bad = [
        f"**{m.group(1)}**"
        for m in BOLD.finditer(line)
        if (m.group(1).endswith(":") or LABEL_HEAD.match(m.group(1))) and not label_ok(m.group(1))
    ]
    bad += [
        f"{m.group(0)} (entity or look-alike colon in bold)"
        for m in BOLD_ANY.finditer(line)
        if COLON_LOOKALIKE.search(m.group(0))
    ]
    bad += [f"{m.group(0)} (bold other than **)" for m in OTHER_BOLD.finditer(line)]
    if "**" in BOLD_ANY.sub(" ", line):
        bad.append("** (bold left open across a line break)")
    plain = PLAIN_LABEL.match(line)
    return bad + ([f"{plain.group(1)} (not bold)"] if plain else [])


def usage_forms(name: str, entry: dict) -> list[re.Pattern[str]]:
    forms = entry.get("forms") or [re.sub(r"\s*\(.*?\)", "", name)]
    return [re.compile(r"(?<!\w)" + re.escape(f) + r"(?:s|es)?(?!\w)", re.I) for f in forms]


def glossary_page_current() -> bool:
    spec = importlib.util.spec_from_file_location("glossary_render", TOOLS / "glossary.py")
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load {TOOLS / 'glossary.py'}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    page = ROOT / GLOSSARY_PAGE
    return page.is_file() and page.read_text(encoding="utf-8") == module.render(module.load(GLOSSARY_TOML))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("paths", nargs="*", help="check only these files (skips the whole-package checks)")
    opts = parser.parse_args()
    try:
        terms, retired, code, allow = load()
    except tomllib.TOMLDecodeError as error:
        print(f"{GLOSSARY_TOML.relative_to(ROOT)}: {error}", file=sys.stderr)
        return 2
    files = [Path(p).resolve() for p in opts.paths] if opts.paths else shipped()

    hits = labels = pronouns = 0
    used = {name: 0 for name in terms}
    forms = {name: usage_forms(name, entry) for name, entry in terms.items()}
    for path in files:
        rel = path.relative_to(ROOT).as_posix() if path.is_relative_to(ROOT) else str(path)
        lines, code_hits = prose(path, code, allow)
        for n, found, term in code_hits:
            print(f"{rel}:{n}: {found} -> {term}")
            hits += 1
        for n, line in enumerate(lines, 1):
            unquoted = QUOTED.sub(lambda m: " " * len(m.group(0)), line)
            for pattern, term, quoted_ok in retired:
                for m in pattern.finditer(unquoted if quoted_ok else line):
                    print(f"{rel}:{n}: {m.group(0)!r} -> {term}   | {line.strip()[:140]}")
                    hits += 1
            if "sources/excerpts/" not in rel:
                for label in bad_labels(line):
                    print(f"{rel}:{n}: {label} -> evidence-label grammar   | {line.strip()[:140]}")
                    labels += 1
            for m in PRONOUN.finditer(line):
                print(f"{rel}:{n}: {m.group(0)!r} -> gendered pronoun   | {line.strip()[:140]}")
                pronouns += 1
            if rel != GLOSSARY_PAGE.as_posix() and not ROUNDUP_GLOSSARY.search(line):
                for name, patterns in forms.items():
                    if not used[name] and any(p.search(line) for p in patterns):
                        used[name] = 1

    problems = hits + labels + pronouns
    print(f"\n{len(files)} files, {len(retired)} retired variants: {hits} hits")
    print(f"evidence-label grammar: {labels} bad labels")
    print(f"gendered pronouns: {pronouns} hits")
    if not opts.paths:
        unused = sorted(name for name, count in used.items() if not count)
        for name in unused:
            print(f"UNUSED   {name}: defined in glossary.toml, used nowhere outside the glossary")
        print(f"{len(terms)} glossary terms: {len(unused)} unused")
        problems += len(unused)
        if not glossary_page_current():
            print(f"STALE    {GLOSSARY_PAGE}: not the current render; run tools/glossary.py")
            problems += 1
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
