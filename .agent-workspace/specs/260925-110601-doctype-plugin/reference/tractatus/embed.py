# /// script
# requires-python = ">=3.13"
# dependencies = []
# ///
"""Write an outline into a copy of the my-tractatus template.

    uv run embed.py OUTLINE.md -o PAGE.html [--template TEMPLATE.html]
    uv run embed.py - -o PAGE.html          # outline from stdin
    uv run embed.py --extract PAGE.html     # print the embedded outline
"""

import argparse
import json
import re
import sys
from pathlib import Path

TEMPLATE = Path(__file__).resolve().with_name("template.html")
BLOCK_RE = re.compile(r'(<script type="application/json" id="outline-source">)([^<]*)(</script>)')


def encode(markdown: str) -> str:
    """A JSON string literal with no '<' and no raw control characters."""
    return json.dumps(markdown, ensure_ascii=False).replace("<", "\\u003c")


def decode(block: str) -> str:
    value = json.loads(block)
    if not isinstance(value, str):
        raise ValueError("outline-source block is not a JSON string")
    return value


def _block(page: str) -> re.Match[str]:
    matches = list(BLOCK_RE.finditer(page))
    if len(matches) != 1:
        raise ValueError(f"expected exactly one outline-source block, found {len(matches)}")
    return matches[0]


def embed(markdown: str, page: str) -> str:
    m = _block(page)
    return page[: m.start(2)] + encode(markdown) + page[m.end(2) :]


def extract(page: str) -> str:
    return decode(_block(page).group(2))


def _read(path: str) -> str:
    data = sys.stdin.buffer.read() if path == "-" else Path(path).read_bytes()
    return data.decode("utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("outline", nargs="?", help="outline markdown file, or - for stdin")
    parser.add_argument("-o", "--output", help="page to write")
    parser.add_argument("--template", default=str(TEMPLATE))
    parser.add_argument("--extract", metavar="PAGE", help="print the outline embedded in PAGE")
    args = parser.parse_args(argv)
    if args.extract and (args.outline or args.output):
        parser.error("--extract takes no other arguments")
    if not args.extract and not (args.outline and args.output):
        parser.error("OUTLINE and -o PAGE are required")
    try:
        if args.extract:
            sys.stdout.buffer.write(extract(_read(args.extract)).encode("utf-8"))
            return 0
        page = embed(_read(args.outline), _read(args.template))
        output = Path(args.output)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(page, encoding="utf-8", newline="")
    except (OSError, UnicodeDecodeError, ValueError) as e:
        print(f"embed.py: {e}", file=sys.stderr)
        return 1
    print(args.output)
    return 0


if __name__ == "__main__":
    sys.exit(main())
