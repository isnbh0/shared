# /// script
# requires-python = ">=3.13"
# ///
"""Check relative links and heading anchors in the two video know-how KBs.

The package root is the folder that holds video-knowhow-code/ and
video-knowhow-craft/ as siblings: the shelves' parent folder in the author's
repo, video-knowhow-kb/ in the zip. With no arguments, every .md and .html
file in the two KB folders is checked, plus the package's root README.md,
AGENTS.md, ATTRIBUTION.md and CLAUDE.md when present. Arguments narrow the
check to given files or folders.

Markdown links and images are scanned in every .md file; href attributes in
every shipped .html file. (The interactive roundup page embeds its outline
as a JSON string; that outline is the roundup .md beside it, so its links
are scanned there once, not twice.)

Each relative link (and image) falls into one class:

  ok       the target exists with exact case; a .md target has the anchor
  broken   inside the package: missing target, wrong case, a folder, a missing
           anchor, or an unencoded space
  outside  the target leaves the package, or sits in a comparison/ lab the
           package does not ship; expected to be absent from the zip
  media    a local-only binary (.mp4, .jsonl, .sqlite, ...) absent here

The mode follows the root folder's name. In the author's workspace only
broken links make the exit status non-zero; outside links are expected
there, since the workspace holds the unshipped shelves the package describes.
Inside the assembled package (root folder video-knowhow-kb/, as the builder
extracts it) self-containment is policy: every outside link fails the check
and is listed with the group it leaves into, so the builder refuses to ship
a package with links to material it does not carry. Web links are not
fetched.
"""

import argparse
import os
import re
import sys
from collections import Counter
from pathlib import Path
from urllib.parse import unquote

ROOT = Path(__file__).resolve().parents[2]
TOP = "video-knowhow-kb"  # the zip's top folder, mirrored from package.py
KBS = ("video-knowhow-code", "video-knowhow-craft")
ROOT_FILES = ("README.md", "AGENTS.md", "ATTRIBUTION.md", "CLAUDE.md")
MEDIA = {".mp4", ".mov", ".webm", ".mkv", ".wav", ".m4a", ".mp3", ".aac", ".flac", ".jsonl", ".sqlite"}
CLASSES = ("ok", "broken", "outside", "media")
# Package mode: the checker runs inside the assembled package, where nothing
# outside the root exists, so outside links are policy failures. Repo mode:
# the root is the author's workspace, where unshipped shelves really exist.
PACKAGE = ROOT.name == TOP
# Markdown sources whose fragment links target ids in the HTML rendered from them.
RENDERED = {
    "video-knowhow-craft/roundup/motion-production-roundup.md": "motion-production-roundup-no-js.html",
}

LINK = re.compile(
    r"!?\[(?:[^\[\]\\]|\\.|\[[^\]]*\])*\]"
    r"\(\s*(<[^>]*>|[^\s()]*(?:\([^\s()]*\)[^\s()]*)*)(?:\s+(?:\"[^\"]*\"|'[^']*'))?\s*\)"
)
SPACED = re.compile(r"\]\((?!<)([^()\s]+\s+[^()\"']+)\)")
HREF = re.compile(r"\shref\s*=\s*(?:\"([^\"]*)\"|'([^']*)')", re.I)
HEADING = re.compile(r"^(#{1,6})[ \t]+(.*?)(?:[ \t]+#+)?[ \t]*$")
FENCE = re.compile(r"^\s*(```|~~~)")
CODE_SPAN = re.compile(r"(`+)(?:(?!\1).)+?\1")
SCHEME = re.compile(r"^[a-z][a-z0-9+.-]*:", re.I)

_anchors: dict[Path, set[str]] = {}
_listings: dict[Path, set[str]] = {}


def prose_lines(text: str) -> list[str]:
    """Lines with fenced code blanked and inline code removed, numbering kept."""
    out, fence = [], None
    for line in text.split("\n"):
        m = FENCE.match(line)
        if m and (fence is None or m.group(1) == fence):
            fence = None if fence else m.group(1)
            out.append("")
        elif fence:
            out.append("")
        else:
            out.append(CODE_SPAN.sub("", line))
    return out


def slug(text: str) -> str:
    """GitHub-style heading slug."""
    text = re.sub(r"!?\[([^\]]*)\]\([^)]*\)", r"\1", text)
    text = re.sub(r"<[^>]+>", "", text)
    text = re.sub(r"[^\w\- ]", "", text.strip().lower())
    return text.replace(" ", "-")


def anchors(path: Path) -> set[str]:
    if path not in _anchors:
        text = path.read_text(encoding="utf-8")
        seen: Counter[str] = Counter()
        found = set(re.findall(r'<[a-z][^>]*\s(?:name|id)="([^"]+)"', text))
        rel = path.relative_to(ROOT).as_posix() if path.is_relative_to(ROOT) else ""
        if rel in RENDERED and (html := path.parent / RENDERED[rel]).is_file():
            found |= set(re.findall(r'\sid="([^"]+)"', html.read_text(encoding="utf-8")))
        for line in prose_lines(text):
            if m := HEADING.match(line):
                s = slug(m.group(2))
                found.add(s if not seen[s] else f"{s}-{seen[s]}")
                seen[s] += 1
        _anchors[path] = found
    return _anchors[path]


def exists_exact(path: Path) -> bool:
    """True if the path exists with the exact case of every component."""
    if not os.path.lexists(path):
        return False
    current = Path(path.anchor)
    for part in path.parts[1:]:
        if current not in _listings:
            _listings[current] = set(os.listdir(current))
        if part not in _listings[current]:
            return False
        current = current / part
    return True


def inside(path: Path) -> bool:
    if not path.is_relative_to(ROOT):
        return False
    parts = path.relative_to(ROOT).parts
    return not parts or parts[0] in KBS or (len(parts) == 1 and parts[0] in ROOT_FILES)


def lab_absent(path: Path) -> bool:
    """True inside a KB's comparison/ lab that this root does not contain."""
    if not path.is_relative_to(ROOT):
        return False
    parts = path.relative_to(ROOT).parts
    return (
        len(parts) >= 2
        and parts[0] in KBS
        and parts[1] == "comparison"
        and not (ROOT / parts[0] / "comparison").is_dir()
    )


def group(path: Path) -> str:
    if path.is_relative_to(ROOT) and path.relative_to(ROOT).parts:
        return path.relative_to(ROOT).parts[0]
    return "beyond the package root"


def classify(src: Path, target: str) -> tuple[str, str]:
    file_part, _, frag = target.partition("#")
    dest = src if not file_part else Path(os.path.normpath(src.parent / unquote(file_part)))
    if not inside(dest):
        found = dest.exists() and (not frag or dest.suffix != ".md" or unquote(frag) in anchors(dest))
        return "outside", group(dest) + ("" if found else ", unresolved here")
    if lab_absent(dest):
        return "outside", "comparison, unresolved here"
    if not exists_exact(dest):
        if dest.suffix.lower() in MEDIA:
            return "media", "absent here"
        return "broken", "wrong case" if dest.exists() else "missing target"
    if dest.is_dir():
        return "broken", "folder; link a file such as its README.md"
    if frag and dest.suffix == ".md" and unquote(frag) not in anchors(dest):
        return "broken", "missing anchor"
    return "ok", ""


def files(args: list[str]) -> list[Path]:
    starts = [Path(a).resolve() for a in args] or [ROOT / kb for kb in KBS] + [
        ROOT / name for name in ROOT_FILES if (ROOT / name).is_file()
    ]
    found = []
    for start in starts:
        if start.is_file():
            found.append(start)
            continue
        for dirpath, dirnames, filenames in os.walk(start):
            dirnames[:] = sorted(d for d in dirnames if d != "node_modules" and not d.startswith("."))
            found += [Path(dirpath) / f for f in sorted(filenames) if f.endswith((".md", ".html"))]
    return found


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("paths", nargs="*", help="files or folders to check (default: both KBs)")
    parser.add_argument(
        "--list",
        action="append",
        default=[],
        choices=("outside", "media", "all"),
        help="also list links of this class (broken links are always listed)",
    )
    opts = parser.parse_args()
    shown = {"broken"} | ({"outside", "media"} if "all" in opts.list else set(opts.list))
    if PACKAGE:
        shown.add("outside")  # self-containment policy: list every outside link

    counts: Counter[str] = Counter()
    outside_groups: Counter[str] = Counter()
    web = 0
    checked = files(opts.paths)

    def count(cls: str, target: str, note: str, line: int, where) -> None:
        counts[cls] += 1
        if cls == "outside":
            outside_groups[note.removesuffix(", unresolved here")] += 1
            if note.endswith("unresolved here"):
                counts["outside unresolved here"] += 1
        if cls in shown:
            print(f"{cls.upper():8} {where}:{line}  {target}  ({note})")

    for src in checked:
        where = src.relative_to(ROOT) if src.is_relative_to(ROOT) else src
        text = src.read_text(encoding="utf-8")
        if src.suffix.lower() == ".html":
            # Shipped pages: check href attributes. The outline embedded in the
            # interactive roundup page is checked as its own .md file.
            for m in HREF.finditer(text):
                target = (m.group(1) or m.group(2)).strip()
                if not target or target.startswith("#"):
                    continue
                if SCHEME.match(target):
                    web += 1
                    continue
                cls, note = classify(src, target)
                count(cls, target, note, text.count("\n", 0, m.start()) + 1, where)
            continue
        for n, line in enumerate(prose_lines(text), 1):
            hits = [("broken", m.group(1), "unencoded space") for m in SPACED.finditer(line)]
            for m in LINK.finditer(line):
                target = m.group(1).strip("<>")
                if SCHEME.match(target):
                    web += 1
                    continue
                if not target:
                    hits.append(("broken", "()", "empty target"))
                    continue
                cls, note = classify(src, target)
                hits.append((cls, target, note))
            for cls, target, note in hits:
                count(cls, target, note, n, where)

    total = sum(counts[c] for c in CLASSES)
    print(f"\n{len(checked)} files, {total} relative links under {ROOT}")
    for cls in CLASSES:
        extra = ""
        if cls == "outside" and counts[cls]:
            parts = ", ".join(f"{g} {k}" for g, k in outside_groups.most_common())
            extra = f"  ({parts}; {counts['outside unresolved here']} unresolved here)"
            if PACKAGE:
                extra += "  FAIL: links leave the package"
        print(f"  {cls:8} {counts[cls]:5}{extra}")
    print(f"  web links not fetched: {web}")
    return 1 if counts["broken"] or (PACKAGE and counts["outside"]) else 0


if __name__ == "__main__":
    sys.exit(main())
