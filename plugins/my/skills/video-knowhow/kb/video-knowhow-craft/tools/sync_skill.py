# /// script
# requires-python = ">=3.13"
# ///
"""Replace a skill's bundled knowledge base with a fresh build of the package.

    uv run tools/sync_skill.py DEST [--commit REV]

Runs package.py (link and term checks must pass, or nothing is written) into a
temporary folder, unzips the package, and replaces the contents of DEST with
the package root's contents. DEST's parent must be a skill folder holding
SKILL.md; anything else is refused so the wrong folder is never wiped.
"""

import argparse
import shutil
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

TOOLS = Path(__file__).resolve().parent
TOP = "video-knowhow-kb"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("dest", type=Path, help="kb folder inside a skill folder (created if missing)")
    parser.add_argument("--commit", default="HEAD", help="revision to package (default: HEAD)")
    opts = parser.parse_args()

    dest = opts.dest.resolve()
    if not (dest.parent / "SKILL.md").is_file():
        sys.exit(f"refusing: {dest.parent} is not a skill folder with SKILL.md")
    if dest.exists() and not dest.is_dir():
        sys.exit(f"refusing: {dest} exists and is not a folder")

    with tempfile.TemporaryDirectory(prefix="video-knowhow-sync-") as tmp:
        out = Path(tmp) / "out"
        out.mkdir()
        build = subprocess.run(
            ["uv", "run", "--quiet", str(TOOLS / "package.py"), str(out), "--commit", opts.commit]
        )
        if build.returncode:
            sys.exit("package.py failed; destination left untouched")
        zips = list(out.glob(f"{TOP}-*.zip"))
        if len(zips) != 1:
            sys.exit(f"expected one package zip, found {len(zips)}")
        extract = Path(tmp) / "extract"
        with zipfile.ZipFile(zips[0]) as archive:
            archive.extractall(extract)
        src = extract / TOP
        if not (src / "README.md").is_file():
            sys.exit(f"package has no {TOP}/README.md")

        dest.mkdir(exist_ok=True)
        for child in dest.iterdir():
            if child.is_dir() and not child.is_symlink():
                shutil.rmtree(child)
            else:
                child.unlink()
        for child in src.iterdir():
            shutil.move(str(child), dest / child.name)

    files = [p for p in dest.rglob("*") if p.is_file()]
    size = sum(p.stat().st_size for p in files)
    print(f"synced {zips[0].name} into {dest}: {len(files)} files, {size:,} bytes")
    return 0


if __name__ == "__main__":
    sys.exit(main())
