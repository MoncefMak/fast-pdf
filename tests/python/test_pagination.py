"""Tests de pagination, headers et footers."""
import pytest

try:
    from fastpdf import render_pdf, RenderOptions
    HAS_ENGINE = True
except ImportError:
    HAS_ENGINE = False

pytestmark = pytest.mark.skipif(not HAS_ENGINE, reason="Rust engine not built")


def test_single_page_renders():
    result = render_pdf("<h1>Hello</h1><p>Content</p>")
    assert result[:4] == b"%PDF"


def test_multipage_document():
    paragraph = "<p>" + "Lorem ipsum dolor sit amet. " * 30 + "</p>"
    html = f"<div>{''.join([paragraph] * 10)}</div>"
    result = render_pdf(html)
    assert result[:4] == b"%PDF"
    assert len(result) > 5000


def test_page_break_before():
    html = """
    <div>Page 1 content</div>
    <div style="page-break-before: always">Page 2 content</div>
    """
    result = render_pdf(html)
    assert result[:4] == b"%PDF"


def test_header_html_option():
    html = "<h1>Document avec header</h1>" + "<p>Content</p>" * 50
    opts = RenderOptions(
        header_html="<div style='text-align:right'>Page {{page_number}}</div>"
    )
    result = render_pdf(html, options=opts)
    assert result[:4] == b"%PDF"


def test_footer_html_option():
    html = "<h1>Document avec footer</h1>" + "<p>Content</p>" * 50
    opts = RenderOptions(
        footer_html="<div style='text-align:center'>{{page_number}} / {{total_pages}}</div>"
    )
    result = render_pdf(html, options=opts)
    assert result[:4] == b"%PDF"


def test_header_and_footer_together():
    html = "<h1>Rapport</h1>" + "<p>Paragraphe contenu.</p>" * 100
    opts = RenderOptions(
        header_html="<div>Mon Entreprise — Rapport Annuel</div>",
        footer_html="<div style='text-align:center'>Page {{page_number}} sur {{total_pages}}</div>",
        margin_top=25.0,
        margin_bottom=25.0,
    )
    result = render_pdf(html, options=opts)
    assert result[:4] == b"%PDF"
