"""The copied zoomdoc skill retains its validator and document model."""

import importlib.util
import subprocess
import sys
from pathlib import Path


REPO = Path(__file__).resolve().parents[2]
SOURCE = REPO / "plugins/zoomdoc/skills/zoomdoc"
MOVED = REPO / "plugins/doctype/skills/zoomdoc"
OLD_LINK = "https://github.com/isnbh0/shared/tree/main/plugins/zoomdoc"
NEW_LINK = "https://github.com/isnbh0/shared/tree/main/plugins/doctype/skills/zoomdoc"


def test_copied_files_match():
    for name in ("SKILL.md", "config.example.yaml", "validate.py"):
        assert (MOVED / name).read_bytes() == (SOURCE / name).read_bytes()
    old = (SOURCE / "template.html").read_text(encoding="utf-8")
    new = (MOVED / "template.html").read_text(encoding="utf-8")
    assert old.count(OLD_LINK) == 1
    assert new == old.replace(OLD_LINK, NEW_LINK)


def test_validator_accepts_semantic_zoom(tmp_path):
    html = """<!doctype html>
<html lang="en"><head><meta charset="utf-8"><title>Example</title></head><body>
<article data-zoomdoc data-zoomdoc-levels="brief full">
  <header><h1>Example</h1></header>
  <p data-zoomdoc-at="brief" hidden>Overview.</p>
  <p data-zoomdoc-at="full">Complete explanation.</p>
</article><script data-zoomdoc-runtime></script>
</body></html>"""
    spec = importlib.util.spec_from_file_location("zoomdoc_validate", MOVED / "validate.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    errors, _warnings = module.validate(html)
    assert errors == []
    page = tmp_path / "zoomdoc.html"
    page.write_text(html, encoding="utf-8")
    result = subprocess.run([sys.executable, str(MOVED / "validate.py"), str(page)], capture_output=True, text=True)
    assert result.returncode == 0, result.stdout + result.stderr
    assert result.stdout.endswith("OK\n")
