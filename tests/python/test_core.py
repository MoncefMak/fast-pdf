"""Tests for the Python wrapper API (unit tests, no Rust engine required)."""

from __future__ import annotations

import pytest
from unittest.mock import patch, MagicMock

from fastpdf.core import (
    RenderOptions,
    PdfDocument,
    PdfEngine,
    FastPdfError,
    RenderError,
    TemplateError,
    ConfigError,
    PAGE_SIZES,
)


# ---------------------------------------------------------------------------
# RenderOptions
# ---------------------------------------------------------------------------

class TestRenderOptions:
    def test_defaults(self):
        opts = RenderOptions()
        assert opts.page_size == "A4"
        assert opts.orientation == "portrait"
        assert opts.margin_top == 10.0
        assert opts.margin_right == 10.0
        assert opts.margin_bottom == 10.0
        assert opts.margin_left == 10.0
        assert opts.title is None
        assert opts.author is None
        assert opts.tailwind is False
        assert opts.base_path is None
        assert opts.header_html is None
        assert opts.footer_html is None

    def test_custom_values(self):
        opts = RenderOptions(
            page_size="Letter",
            orientation="landscape",
            margin_top=25.0,
            title="Test",
            author="Author",
            tailwind=True,
        )
        assert opts.page_size == "Letter"
        assert opts.orientation == "landscape"
        assert opts.margin_top == 25.0
        assert opts.title == "Test"
        assert opts.author == "Author"
        assert opts.tailwind is True

    def test_tuple_page_size(self):
        opts = RenderOptions(page_size=(100.0, 200.0))
        assert opts.page_size == (100.0, 200.0)


class TestPageSizes:
    def test_a4(self):
        assert PAGE_SIZES["A4"] == (210.0, 297.0)

    def test_letter(self):
        assert PAGE_SIZES["Letter"] == (215.9, 279.4)

    def test_all_sizes_are_tuples(self):
        for name, size in PAGE_SIZES.items():
            assert isinstance(size, tuple)
            assert len(size) == 2
            assert size[0] > 0 and size[1] > 0


# ---------------------------------------------------------------------------
# PdfDocument
# ---------------------------------------------------------------------------

class TestPdfDocument:
    def test_creation(self):
        doc = PdfDocument(b"%PDF-1.4 fake", page_count=3, title="Test")
        assert doc.page_count == 3
        assert doc.title == "Test"
        assert doc.to_bytes() == b"%PDF-1.4 fake"

    def test_len(self):
        data = b"x" * 1024
        doc = PdfDocument(data)
        assert len(doc) == 1024

    def test_repr(self):
        doc = PdfDocument(b"x" * 2048, page_count=2, title="Doc")
        r = repr(doc)
        assert "pages=2" in r
        assert "Doc" in r

    def test_save(self, tmp_path):
        doc = PdfDocument(b"%PDF-1.4 test content")
        path = tmp_path / "test.pdf"
        doc.save(path)
        assert path.read_bytes() == b"%PDF-1.4 test content"

    def test_save_creates_directories(self, tmp_path):
        doc = PdfDocument(b"data")
        path = tmp_path / "deep" / "nested" / "dir" / "test.pdf"
        doc.save(path)
        assert path.exists()


# ---------------------------------------------------------------------------
# Exceptions
# ---------------------------------------------------------------------------

class TestExceptions:
    def test_hierarchy(self):
        assert issubclass(RenderError, FastPdfError)
        assert issubclass(TemplateError, FastPdfError)
        assert issubclass(ConfigError, FastPdfError)
        assert issubclass(FastPdfError, Exception)


# ---------------------------------------------------------------------------
# Utilities
# ---------------------------------------------------------------------------

class TestUtils:
    def test_css_string(self):
        from fastpdf.utils import css_string

        result = css_string({
            "body": {"font-size": "12pt", "color": "#333"},
            "h1": {"color": "blue"},
        })
        assert "body" in result
        assert "font-size: 12pt" in result
        assert "h1" in result

    def test_minify_html(self):
        from fastpdf.utils import minify_html

        html = "  <h1>  Hello  </h1>  <p>  World  </p>  "
        result = minify_html(html)
        assert ">  <" not in result  # whitespace between tags removed
        assert "<h1>" in result

    def test_inline_images_skips_urls(self):
        from fastpdf.utils import inline_images

        html = '<img src="https://example.com/img.png">'
        result = inline_images(html)
        assert result == html  # unchanged

    def test_inline_images_skips_data_uri(self):
        from fastpdf.utils import inline_images

        html = '<img src="data:image/png;base64,abc">'
        result = inline_images(html)
        assert result == html


# ---------------------------------------------------------------------------
# Module-level functions (with mocked engine)
# ---------------------------------------------------------------------------

class TestModuleFunctions:
    @patch("fastpdf.core._ENGINE_AVAILABLE", False)
    def test_render_pdf_without_engine(self):
        from fastpdf.core import render_pdf
        with pytest.raises(FastPdfError, match="not available"):
            render_pdf("<h1>Test</h1>")

    @patch("fastpdf.core._ENGINE_AVAILABLE", False)
    def test_get_version_without_engine(self):
        from fastpdf.core import get_version
        version = get_version()
        assert "unavailable" in version

    @patch("fastpdf.core._ENGINE_AVAILABLE", False)
    def test_engine_creation_without_engine(self):
        with pytest.raises(FastPdfError, match="not available"):
            PdfEngine()
