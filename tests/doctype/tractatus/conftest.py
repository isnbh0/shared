"""Test harness for the tractatus template.

Run from the shared repository root:
    uv run --with pytest --with pytest-playwright --with hypothesis \
        pytest tests/doctype/tractatus -q
One-time browser install:
    uv run --with pytest-playwright playwright install chromium webkit
Tests marked `network` are skipped unless TRACTATUS_NETWORK=1. Every other test that uses a
page runs with all non-file requests aborted, whatever the environment says.
Pages run under the template's CSP, which forbids eval: give wait_for_function an arrow
function, since Playwright evaluates a bare expression with eval.
"""

import importlib.util
import os
import re
from pathlib import Path

import pytest
from hypothesis import settings
from hypothesis.configuration import set_hypothesis_home_dir

REPO = Path(__file__).resolve().parents[3]
SKILL_DIR = REPO / "plugins/doctype/skills/tractatus"
TEMPLATE = SKILL_DIR / "template.html"
FIXTURES = Path(__file__).resolve().parent / "fixtures"
NETWORK = os.environ.get("TRACTATUS_NETWORK") == "1"

# No example database; Hypothesis still caches Unicode and constants data, so keep that
# storage in the test directory (gitignored) rather than in the packaged skill.
set_hypothesis_home_dir(Path(__file__).resolve().parent / ".hypothesis")
settings.register_profile("tractatus", database=None)
settings.load_profile("tractatus")

_spec = importlib.util.spec_from_file_location("embed", SKILL_DIR / "embed.py")
embed = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(embed)


def template_text() -> str:
    return TEMPLATE.read_bytes().decode("utf-8")


def pytest_collection_modifyitems(config, items):
    if NETWORK:
        return
    skip = pytest.mark.skip(reason="set TRACTATUS_NETWORK=1")
    for item in items:
        if item.get_closest_marker("network"):
            item.add_marker(skip)


@pytest.fixture(autouse=True)
def _network_mode(request):
    """Law N: a test's network access depends only on its own `network` marker."""
    if "page" in request.fixturenames and request.node.get_closest_marker("network") is None:
        request.getfixturevalue("page").route(re.compile(r"^(?!file:).*"), lambda r: r.abort())


@pytest.fixture
def fake_md() -> str:
    return (FIXTURES / "fake-tractatus.txt").read_bytes().decode("utf-8")


@pytest.fixture
def console_errors(page):
    errors: list[str] = []

    def on_console(m):
        # Deliberately aborted requests (law N) are logged as net::ERR_FAILED.
        if m.type == "error" and "net::ERR_FAILED" not in m.text:
            errors.append(m.text)

    page.on("console", on_console)
    page.on("pageerror", lambda e: errors.append(str(e)))
    yield errors
    assert errors == [], errors


@pytest.fixture
def page_transforms() -> list:
    """Functions applied, in order, to each page that build_page writes."""
    return []


@pytest.fixture
def build_page(tmp_path, page_transforms):
    def _build(markdown: str, name: str = "page.html") -> Path:
        path = tmp_path / name
        html = embed.embed(markdown, template_text())
        for transform in page_transforms:
            html = transform(html)
        path.write_text(html, encoding="utf-8", newline="")
        return path

    return _build


@pytest.fixture
def open_outline(page, build_page, console_errors):
    def _open(markdown: str, fragment: str = ""):
        page.goto(build_page(markdown).as_uri() + fragment)
        page.wait_for_function("() => document.documentElement.dataset.outlineReady === 'true'")
        return page

    return _open


LAWS_JS = (Path(__file__).resolve().parent / "laws.js").read_text(encoding="utf-8")


def check_laws(page) -> None:
    """Laws S and D: the DOM projection agrees with window.tractatus.state()."""
    assert page.evaluate(LAWS_JS) == []
