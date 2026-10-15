# /// script
# requires-python = ">=3.13"
# ///
"""Build the self-contained video know-how zip from a commit of the source repository.

    uv run tools/package.py OUT_DIR [--commit REV]
    uv run tools/package.py --dry-run [--commit REV]

`git archive` of REV (default HEAD) supplies video-knowhow-code/ and
video-knowhow-craft/ under a top folder video-knowhow-kb/. Four exclusions
keep the package to what it can stand on: each shelf's comparison/ lab (the
comparison-run records stay in the repository; the case pages carry their
findings), the code shelf's lintable-video-system-prelim.md
(superseded first-pass notes on a lintable video system), and the craft
shelf's roundup/review/ (authoring-round visual QA for the roundup page), and
the code shelf's sixteen/ (a separate project that is not part of the
package). Everything else that lives in the repository is represented
in prose: the SLASH_MY production source, the reference shelves, the chatlog
trace, and rendered media. The root README.md, AGENTS.md and ATTRIBUTION.md
come from the templates beside this script in REV, stamped with the commit;
CLAUDE.md imports AGENTS.md. The zip is extracted to a temporary folder and
the linkcheck.py inside it is run there in package mode: self-containment is
policy, so the check fails if any relative link in a shipped .md or .html
file is broken or leaves the package root. The termcheck.py inside it then
checks the shipped prose against the package glossary: a retired term
variant, a glossary term used nowhere, or a stale Glossary.md fails it. Only
if both checks pass is the zip written to OUT_DIR/video-knowhow-kb-<sha>.zip; an existing file is never
overwritten. --dry-run builds and checks without writing anything.
"""

import argparse
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

TOOLS = Path(__file__).resolve().parent
TOP = "video-knowhow-kb"
KBS = ("video-knowhow-code", "video-knowhow-craft")
TEMPLATES = {
    "README.md": "package-README.md.tmpl",
    "AGENTS.md": "package-AGENTS.md.tmpl",
    "ATTRIBUTION.md": "package-ATTRIBUTION.md.tmpl",
}
CLAUDE = "@AGENTS.md\n"


def git(*args: str, cwd: Path = TOOLS) -> str:
    result = subprocess.run(["git", "-C", str(cwd), *args], capture_output=True, text=True)
    if result.returncode:
        sys.exit(f"git {args[0]} failed: {result.stderr.strip()}")
    return result.stdout


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("out_dir", nargs="?", type=Path, help="existing folder to write the zip into")
    parser.add_argument("--commit", default="HEAD", help="revision to package (default: HEAD)")
    parser.add_argument("--dry-run", action="store_true", help="build and check, write nothing")
    opts = parser.parse_args()
    if not opts.dry_run and opts.out_dir is None:
        parser.error("give OUT_DIR, or --dry-run")

    sha = git("rev-parse", "--verify", f"{opts.commit}^{{commit}}").strip()
    short = sha[:8]
    date = git("show", "-s", "--format=%cs", sha).strip()
    root = Path(git("rev-parse", "--show-toplevel").strip()).resolve()
    prefix = TOOLS.parent.parent.relative_to(root).as_posix()  # the folder that holds both shelves
    tools_rel = TOOLS.relative_to(root).as_posix()

    dest = None
    if not opts.dry_run:
        if not opts.out_dir.is_dir():
            sys.exit(f"{opts.out_dir} is not an existing folder")
        dest = opts.out_dir.resolve() / f"{TOP}-{short}.zip"
        if dest.exists():
            sys.exit(f"refusing to overwrite {dest}")

    generated = {name: git("show", f"{sha}:{tools_rel}/{template}") for name, template in TEMPLATES.items()}
    generated = {
        name: text.replace("{{commit}}", sha).replace("{{date}}", date) for name, text in generated.items()
    }
    generated["CLAUDE.md"] = CLAUDE

    with tempfile.TemporaryDirectory(prefix="video-knowhow-kb-") as tmp:
        tmp_zip = Path(tmp) / f"{TOP}-{short}.zip"
        virtual = [f"--add-virtual-file={TOP}/{name}:{text}" for name, text in generated.items()]
        git(
            "archive",
            "--format=zip",
            f"--prefix={TOP}/",
            f"--mtime={git('show', '-s', '--format=%cI', sha).strip()}",
            *virtual,
            "-o",
            str(tmp_zip),
            f"{sha}:{prefix}",
            *KBS,
            # the experiment lab stays in the source repository
            *(f":(exclude){kb}/comparison" for kb in KBS),
            # superseded first-pass scratch on a lintable video system
            ":(exclude)video-knowhow-code/lintable-video-system-prelim.md",
            # authoring-round visual QA for the roundup page
            ":(exclude)video-knowhow-craft/roundup/review",
            # a separate project, not part of the package
            ":(exclude)video-knowhow-code/sixteen",
            cwd=root,
        )
        extract = Path(tmp) / "extract"
        with zipfile.ZipFile(tmp_zip) as archive:
            names = archive.namelist()
            archive.extractall(extract)
        missing = [name for name in generated if f"{TOP}/{name}" not in names]
        if missing:
            sys.exit(f"git archive placed {', '.join(missing)} outside {TOP}/")
        files = [n for n in names if not n.endswith("/")]
        size = tmp_zip.stat().st_size
        print(f"built {tmp_zip.name} from {sha} ({date}): {len(files)} files, {size:,} bytes", flush=True)

        checker = extract / TOP / "video-knowhow-craft" / "tools" / "linkcheck.py"
        if not checker.is_file():
            sys.exit(f"{sha[:8]} has no {tools_rel}/linkcheck.py; package a later commit")
        check = subprocess.run(["uv", "run", "--quiet", str(checker)], cwd=extract / TOP)
        if check.returncode:
            sys.exit("link check failed inside the package; no zip written")

        terms = extract / TOP / "video-knowhow-craft" / "tools" / "termcheck.py"
        if not terms.is_file():
            sys.exit(f"{sha[:8]} has no {tools_rel}/termcheck.py; package a later commit")
        check = subprocess.run(["uv", "run", "--quiet", str(terms)], cwd=extract / TOP)
        if check.returncode:
            sys.exit("term check failed inside the package; no zip written")

        if dest is None:
            print("dry run: link and term checks passed; no zip written")
            return 0
        with tmp_zip.open("rb") as src, dest.open("xb") as out:
            out.write(src.read())
    print(f"wrote {dest}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
