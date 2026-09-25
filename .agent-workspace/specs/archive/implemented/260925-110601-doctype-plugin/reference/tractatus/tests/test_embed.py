"""Law E: the content block round-trips any string, in Python and in the browser."""

import io
import sys

import pytest
from conftest import embed, template_text
from hypothesis import given
from hypothesis import strategies as st


@given(st.text())
def test_encode_roundtrip(s):
    encoded = embed.encode(s)
    assert embed.decode(encoded) == s
    assert "<" not in encoded
    assert all(ord(c) >= 0x20 for c in encoded)


@given(st.text())
def test_embed_extract_roundtrip(s):
    t = template_text()
    out = embed.embed(s, t)
    assert embed.extract(out) == s
    m = embed.BLOCK_RE.search(t)
    assert out.startswith(t[: m.start(2)])
    assert out.endswith(t[m.end(2) :])


def test_template_fixed_point():
    t = template_text()
    assert embed.embed(embed.extract(t), t) == t
    assert embed.extract(t).startswith("# Outline")


def test_block_count():
    t = template_text()
    with pytest.raises(ValueError, match="found 0"):
        embed.embed("x", "<p>no block</p>")
    with pytest.raises(ValueError, match="found 2"):
        embed.embed("x", t + t)
    block = embed.BLOCK_RE.search(t).group(2)
    with pytest.raises(ValueError, match="found 0"):
        embed.embed("x", t.replace(block, '"a<b"'))


def test_decode_rejects_non_string():
    for block in ("{}", "1", '"x'):
        with pytest.raises(ValueError):
            embed.decode(block)


def test_cli_file(tmp_path, fake_md, capsysbinary):
    md = tmp_path / "o.md"
    md.write_bytes(fake_md.encode())
    out = tmp_path / "o.html"
    assert embed.main([str(md), "-o", str(out)]) == 0
    assert embed.extract(out.read_bytes().decode()) == fake_md
    capsysbinary.readouterr()
    assert embed.main(["--extract", str(out)]) == 0
    assert capsysbinary.readouterr().out == fake_md.encode()


def test_cli_stdin_bytes(tmp_path, monkeypatch):
    monkeypatch.setattr(sys, "stdin", io.TextIOWrapper(io.BytesIO(b"- 1 x\r\n- 2 y")))
    out = tmp_path / "o.html"
    assert embed.main(["-", "-o", str(out)]) == 0
    assert embed.extract(out.read_bytes().decode()) == "- 1 x\r\n- 2 y"


def test_cli_creates_parents(tmp_path, capsysbinary):
    md = tmp_path / "o.md"
    md.write_text("- 1 x", encoding="utf-8")
    out = tmp_path / "inbox" / "deeper" / "o.html"
    assert embed.main([str(md), "-o", str(out)]) == 0
    assert embed.extract(out.read_bytes().decode()) == "- 1 x"
    # A failed build creates no directories.
    assert embed.main([str(tmp_path / "missing.md"), "-o", str(tmp_path / "none" / "o.html")]) == 1
    assert not (tmp_path / "none").exists()


def test_cli_errors(tmp_path):
    out = tmp_path / "o.html"
    assert embed.main([str(tmp_path / "missing.md"), "-o", str(out)]) == 1
    assert not out.exists()

    md = tmp_path / "o.md"
    md.write_text("- 1 x", encoding="utf-8")
    bad = tmp_path / "bad.html"
    bad.write_text("<p>no block</p>", encoding="utf-8")
    assert embed.main([str(md), "-o", str(out), "--template", str(bad)]) == 1
    assert not out.exists()

    with pytest.raises(SystemExit):
        embed.main([])


CORPUS = [
    "- 1 </script><script>alert(1)</script>",
    "- 1 </SCRIPT >",
    "- 1 <!--<script>",
    "- 1 a\r\n- 2 b\r- 3 c",
    "- 1 nul\u0000here",
    "- 1 line sep para",
    "- 1 literal \\u003c escape",
    "- 1 한국어 텍스트",
    "- 1 emoji 🧭 and ZWJ 👩‍💻",
    "- 1 $$ and \\\\ backslashes \\",
    "",
]


@pytest.mark.parametrize("s", CORPUS)
def test_browser_roundtrip(open_outline, s):
    page = open_outline(s)
    assert page.evaluate("s => window.tractatus.source === s", s) is True
    assert page.evaluate('document.querySelectorAll("script:not([src])").length') == 2


def test_invalid_block_shows_error(page, tmp_path, console_errors):
    t = embed.BLOCK_RE.sub(lambda m: m.group(1) + "{}" + m.group(3), template_text())
    path = tmp_path / "bad.html"
    path.write_text(t, encoding="utf-8", newline="")
    page.goto(path.as_uri())
    page.wait_for_function("() => document.documentElement.dataset.outlineReady === 'error'")
    assert "embed.py" in page.text_content("#status")
    assert page.is_hidden("#outline")
    assert page.evaluate("window.tractatus.source") is None
