"""Phase 5: SKILL.md examples build working pages, and the skill is published to both hosts."""

import io
import os
import re

from conftest import SKILL_DIR, embed

SKILL_MD = SKILL_DIR / "SKILL.md"
MACBOOK = SKILL_DIR.parents[2]


def skill_text() -> str:
    return SKILL_MD.read_text(encoding="utf-8")


def frontmatter(text: str) -> dict[str, str]:
    assert text.startswith("---\n")
    block = text[4 : text.index("\n---\n", 4)]
    fields = {}
    for line in block.splitlines():
        key, sep, value = line.partition(":")
        assert sep, line
        fields[key.strip()] = value.strip()
    return fields


def format_example() -> str:
    section = skill_text().split("\n## Format\n", 1)[1]
    m = re.search(r"^```markdown\n(.*?)^```$", section, re.MULTILINE | re.DOTALL)
    assert m is not None
    return m.group(1)


def heredoc_example() -> str:
    m = re.search(r"<<'EOF'\n(.*?)^\s*EOF$", skill_text(), re.MULTILINE | re.DOTALL)
    assert m is not None
    # The heredoc sits inside an indented list item; strip that indentation as a shell reader would
    # see the text after the list is rendered.
    lines = m.group(1).splitlines(keepends=True)
    indent = min(len(ln) - len(ln.lstrip(" ")) for ln in lines if ln.strip())
    return "".join(ln[indent:] for ln in lines)


def open_page(page, path):
    warnings: list[str] = []
    page.on("console", lambda m: m.type == "warning" and warnings.append(m.text))
    page.goto(path.as_uri())
    page.wait_for_function("() => document.documentElement.dataset.outlineReady === 'true'")
    return warnings


def test_frontmatter():
    fields = frontmatter(skill_text())
    assert fields["name"] == "my-tractatus" == SKILL_DIR.name
    assert fields["description"]


def test_skill_md_uses_embed():
    text = skill_text()
    assert "embed.py" in text
    assert "--extract" in text
    for banned in ("outline-source", "<\\/script", "\\("):
        assert banned not in text, banned


def test_procedure_example_renders(page, console_errors, tmp_path):
    md = tmp_path / "o.md"
    md.write_text(format_example(), encoding="utf-8")
    out = tmp_path / "o.html"
    assert embed.main([str(md), "-o", str(out)]) == 0
    warnings = open_page(page, out)
    assert page.title() == "Title"
    assert page.locator("#item-root > [role=group] > li").count() == 2
    assert warnings == []


def test_procedure_heredoc_example(page, console_errors, tmp_path, monkeypatch):
    body = heredoc_example()
    monkeypatch.setattr("sys.stdin", io.TextIOWrapper(io.BytesIO(body.encode("utf-8"))))
    out = tmp_path / "h.html"
    assert embed.main(["-", "-o", str(out)]) == 0
    assert embed.extract(out.read_text(encoding="utf-8")) == body
    open_page(page, out)
    assert page.title() == "Title"
    assert page.locator("#outline li").count() == 2   # the root and one item


def test_codex_link():
    link = MACBOOK / "agents/skills/my-tractatus"
    assert link.is_symlink()
    assert os.readlink(link) == "../../claude/skills/my-tractatus"
    assert link.resolve() == SKILL_DIR.resolve()


def test_installer_entry():
    lines = (MACBOOK / "install.sh").read_text(encoding="utf-8").splitlines()
    assert '"claude/skills/my-tractatus:$HOME/.claude/skills/my-tractatus"' in [
        ln.strip() for ln in lines
    ]
