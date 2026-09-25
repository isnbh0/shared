"""Phase 1 static render: a fully expanded semantic nested list."""

from conftest import TEMPLATE


def test_title_and_intro(open_outline, fake_md):
    page = open_outline(fake_md)
    assert page.text_content("h1") == "Tractatus Bibliothecarius"
    assert page.title() == "Tractatus Bibliothecarius"
    assert page.locator(".intro p").count() == 2


def test_all_items_rendered(open_outline, fake_md):
    page = open_outline(fake_md)
    assert page.locator("#outline li").count() == 48            # 47 items and the root
    assert page.text_content("#item-2_01231 .label") == "2.01231"
    item = page.locator('li[data-id="p-5-3"]')
    assert item.count() == 1
    assert item.locator(".label").count() == 0


def test_text_is_escaped(open_outline):
    page = open_outline("- 1 <img src=x onerror=alert(1)>")
    assert page.locator("#outline img").count() == 0
    assert "<img" in page.text_content("#outline .text")


def test_empty_document(open_outline):
    page = open_outline("")
    assert page.is_visible(".empty")
    assert page.is_visible("#doc-title")                           # the root alone
    assert page.locator("#outline [role=treeitem]").count() == 1
    assert page.locator("#outline [role=group]").count() == 0
    assert page.is_hidden(".intro")
    assert page.title() == "Outline"


def test_template_sample_renders(page, console_errors):
    page.goto(TEMPLATE.as_uri())
    page.wait_for_function("() => document.documentElement.dataset.outlineReady === 'true'")
    assert page.locator("#outline li").count() == 4


def test_semantic_landmarks(open_outline, fake_md):
    page = open_outline(fake_md)
    for tag in ("header", "main", "h1"):
        assert page.locator(tag).count() == 1
    assert page.locator('html[lang="en"]').count() == 1
