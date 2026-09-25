"""The shipped Markdown renders as a navigable page."""

from conftest import SKILL_DIR, embed, template_text


def test_example_page(page, console_errors, tmp_path):
    markdown = (SKILL_DIR / "examples/tractatus.md").read_text(encoding="utf-8")
    path = tmp_path / "example.html"
    path.write_text(embed.embed(markdown, template_text()), encoding="utf-8")
    page.goto(path.as_uri())
    page.wait_for_function("() => document.documentElement.dataset.outlineReady === 'true'")
    assert page.title()
    assert page.locator("#item-root > [role=group] > li").count() >= 2
    page.goto(path.as_uri() + "#1")
    page.wait_for_function("() => document.documentElement.dataset.outlineReady === 'true'")
    assert page.evaluate("location.hash") == "#1"
    assert page.locator("#item-1").count() == 1
