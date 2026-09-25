"""Skill instructions and the doctype archive contain the published resources."""

import io
import json
import re
import subprocess
import zipfile

from conftest import REPO, SKILL_DIR, embed

SKILL_MD = SKILL_DIR / "SKILL.md"


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
    assert fields["name"] == "tractatus" == SKILL_DIR.name
    assert fields["description"]
    for name in ("zoomdoc", "tractatus"):
        directory = SKILL_DIR.parent / name
        assert directory.is_dir()
        assert frontmatter((directory / "SKILL.md").read_text(encoding="utf-8"))["name"] == name
        assert (directory / "config.example.yaml").is_file()


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


def test_configuration_and_example():
    text = skill_text()
    assert "config.local.yaml" in text and "config.yaml" in text
    assert "output_dir" in text and "ask" in text
    assert "inbox/" not in text
    assert (SKILL_DIR / "examples/tractatus.md").is_file()
    assert "examples/tractatus.md" in text
    assert "python3" in text and "3.13" in text
    assert "MathJax 3.2.2" in text
    assert "output_dir:" in (SKILL_DIR / "config.example.yaml").read_text(encoding="utf-8")


def test_package_archive(tmp_path):
    manifest = json.loads((SKILL_DIR.parents[1] / ".claude-plugin/plugin.json").read_text())
    assert manifest["name"] == "doctype"
    assert manifest["version"] == "1.0.0"
    subprocess.run(["bash", "scripts/pack-plugin.sh", "doctype", str(tmp_path)], cwd=REPO, check=True, capture_output=True)
    with zipfile.ZipFile(tmp_path / "doctype.zip") as archive:
        names = set(archive.namelist())
    for name in ("zoomdoc", "tractatus"):
        assert f"skills/{name}/SKILL.md" in names
    assert "skills/tractatus/examples/tractatus.md" in names
    assert not any("tests/" in name for name in names)
