"""The published zoomdoc skill retains its validator and document model."""

import importlib.util
import subprocess
import sys
from pathlib import Path


REPO = Path(__file__).resolve().parents[2]
SKILL = REPO / "plugins/doctype/skills/zoomdoc"
OLD_LINK = "https://github.com/isnbh0/shared/tree/main/plugins/zoomdoc"
NEW_LINK = "https://github.com/isnbh0/shared/tree/main/plugins/doctype/skills/zoomdoc"


def test_template_links_to_published_skill():
    template = (SKILL / "template.html").read_text(encoding="utf-8")
    assert template.count(NEW_LINK) == 1
    assert OLD_LINK not in template


def test_validator_accepts_semantic_zoom(tmp_path):
    html = """<!doctype html>
<html lang="en"><head><meta charset="utf-8"><title>Example</title></head><body>
<article data-zoomdoc data-zoomdoc-levels="brief full">
  <header><h1>Example</h1></header>
  <p data-zoomdoc-at="brief" hidden>Overview.</p>
  <p data-zoomdoc-at="full">Complete explanation.</p>
</article><script data-zoomdoc-runtime></script>
</body></html>"""
    spec = importlib.util.spec_from_file_location("zoomdoc_validate", SKILL / "validate.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    errors, _warnings = module.validate(html)
    assert errors == []
    page = tmp_path / "zoomdoc.html"
    page.write_text(html, encoding="utf-8")
    result = subprocess.run([sys.executable, str(SKILL / "validate.py"), str(page)], capture_output=True, text=True)
    assert result.returncode == 0, result.stdout + result.stderr
    assert result.stdout.endswith("OK\n")
