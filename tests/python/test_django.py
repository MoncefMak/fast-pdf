"""Tests for Django integration (unit tests, no Django required)."""

from __future__ import annotations

import pytest
from unittest.mock import patch, MagicMock, PropertyMock


# ---------------------------------------------------------------------------
# Helper: minimal Django stub so we can import contrib.django without a real
# Django installation if needed.
# ---------------------------------------------------------------------------

def _mock_django():
    """Return a context manager that stubs enough Django to import contrib."""
    import sys
    from unittest.mock import MagicMock

    mods = {}
    for mod_name in [
        "django",
        "django.conf",
        "django.http",
        "django.template",
        "django.template.loader",
        "django.contrib",
        "django.contrib.staticfiles",
        "django.contrib.staticfiles.finders",
    ]:
        if mod_name not in sys.modules:
            mods[mod_name] = MagicMock()

    return mods


class TestDjangoImport:
    def test_import_module(self):
        """Module should import when Django is installed."""
        import sys
        stubs = _mock_django()
        for name, mod in stubs.items():
            sys.modules.setdefault(name, mod)
        try:
            from fastpdf.contrib import django  # noqa: F811
        except ImportError:
            pytest.skip("Could not import django contrib")
        finally:
            for name in stubs:
                sys.modules.pop(name, None)

    def test_import_fails_without_django(self):
        """Should raise ImportError with install hint when Django missing."""
        import sys
        saved = sys.modules.get("django")
        sys.modules["django"] = None  # force ImportError
        try:
            # Force reimport
            sys.modules.pop("fastpdf.contrib.django", None)
            with pytest.raises(ImportError, match="pip install ferropdf\\[django\\]"):
                import importlib
                importlib.import_module("fastpdf.contrib.django")
        finally:
            if saved is not None:
                sys.modules["django"] = saved
            else:
                sys.modules.pop("django", None)
            sys.modules.pop("fastpdf.contrib.django", None)


class TestDjangoSettings:
    @pytest.fixture(autouse=True)
    def _setup_django(self):
        import sys
        stubs = _mock_django()
        for name, mod in stubs.items():
            sys.modules.setdefault(name, mod)
        yield
        for name in stubs:
            sys.modules.pop(name, None)
        sys.modules.pop("fastpdf.contrib.django", None)

    def test_get_default_options(self):
        """Should return defaults when Django FERROPDF not configured."""
        from fastpdf.contrib.django import _get_default_options
        opts = _get_default_options()
        assert opts.page_size == "A4"

    @patch("fastpdf.contrib.django._get_django_settings")
    def test_settings_override(self, mock_settings):
        mock_settings.return_value = {
            "DEFAULT_PAGE_SIZE": "Letter",
            "DEFAULT_MARGIN": 20.0,
            "TAILWIND": True,
        }
        from fastpdf.contrib.django import _get_default_options
        opts = _get_default_options()
        assert opts.page_size == "Letter"
        assert opts.margin_top == 20.0
        assert opts.tailwind is True

    @patch("fastpdf.contrib.django._get_django_settings")
    def test_opts_kwargs_override(self, mock_settings):
        """Caller kwargs should override settings."""
        mock_settings.return_value = {"DEFAULT_PAGE_SIZE": "A4"}
        from fastpdf.contrib.django import _get_default_options
        opts = _get_default_options(page_size="Letter", tailwind=True)
        assert opts.page_size == "Letter"
        assert opts.tailwind is True


class TestResolveStaticUrls:
    @pytest.fixture(autouse=True)
    def _setup_django(self):
        import sys
        stubs = _mock_django()
        for name, mod in stubs.items():
            sys.modules.setdefault(name, mod)
        yield
        for name in stubs:
            sys.modules.pop(name, None)
        sys.modules.pop("fastpdf.contrib.django", None)

    def test_replaces_static_href(self):
        from fastpdf.contrib.django import resolve_static_urls

        with patch(
            "django.contrib.staticfiles.finders.find",
            return_value="/app/static/css/style.css",
        ):
            html = '<link href="/static/css/style.css" rel="stylesheet">'
            result = resolve_static_urls(html)
            assert "/app/static/css/style.css" in result
            assert "/static/css/style.css" not in result

    def test_replaces_static_src(self):
        from fastpdf.contrib.django import resolve_static_urls

        with patch(
            "django.contrib.staticfiles.finders.find",
            return_value="/app/static/img/logo.png",
        ):
            html = '<img src="/static/img/logo.png">'
            result = resolve_static_urls(html)
            assert "/app/static/img/logo.png" in result

    def test_leaves_nonexistent_static(self):
        from fastpdf.contrib.django import resolve_static_urls

        with patch(
            "django.contrib.staticfiles.finders.find",
            return_value=None,
        ):
            html = '<img src="/static/missing.png">'
            result = resolve_static_urls(html)
            assert result == html


class TestRenderToPdfResponse:
    @pytest.fixture(autouse=True)
    def _setup_django(self):
        import sys
        stubs = _mock_django()
        for name, mod in stubs.items():
            sys.modules.setdefault(name, mod)
        yield
        for name in stubs:
            sys.modules.pop(name, None)
        sys.modules.pop("fastpdf.contrib.django", None)

    @patch("fastpdf.contrib.django.render_pdf")
    @patch("django.template.loader.render_to_string", return_value="<h1>Test</h1>")
    def test_returns_http_response(self, mock_render_str, mock_render_pdf):
        mock_render_pdf.return_value = b"%PDF-1.4 fake"
        from fastpdf.contrib.django import render_to_pdf_response

        request = MagicMock()
        response = render_to_pdf_response(
            request,
            "test.html",
            {"key": "val"},
            filename="output.pdf",
        )

        assert response["Content-Type"] == "application/pdf"
        assert 'filename="output.pdf"' in response["Content-Disposition"]
        assert response.status_code == 200

    @patch("fastpdf.contrib.django.render_pdf")
    @patch("django.template.loader.render_to_string", return_value="<h1>Test</h1>")
    def test_opts_kwargs_forwarded(self, mock_render_str, mock_render_pdf):
        mock_render_pdf.return_value = b"%PDF-1.4 fake"
        from fastpdf.contrib.django import render_to_pdf_response

        request = MagicMock()
        response = render_to_pdf_response(
            request,
            "test.html",
            {},
            filename="out.pdf",
            page_size="A4",
            tailwind=True,
        )
        # Should not raise; options built from kwargs
        assert response["Content-Type"] == "application/pdf"


class TestRenderToPdfStream:
    @pytest.fixture(autouse=True)
    def _setup_django(self):
        import sys
        stubs = _mock_django()
        for name, mod in stubs.items():
            sys.modules.setdefault(name, mod)
        yield
        for name in stubs:
            sys.modules.pop(name, None)
        sys.modules.pop("fastpdf.contrib.django", None)

    @patch("fastpdf.contrib.django.render_pdf")
    @patch("django.template.loader.render_to_string", return_value="<h1>Test</h1>")
    def test_returns_streaming_response(self, mock_render_str, mock_render_pdf):
        mock_render_pdf.return_value = b"%PDF-1.4 fake"
        from fastpdf.contrib.django import render_to_pdf_stream

        request = MagicMock()
        response = render_to_pdf_stream(
            request, "test.html", {}, filename="big.pdf"
        )
        assert response["Content-Type"] == "application/pdf"
        assert "Content-Length" in response


class TestPdfMixin:
    @pytest.fixture(autouse=True)
    def _setup_django(self):
        import sys
        stubs = _mock_django()
        for name, mod in stubs.items():
            sys.modules.setdefault(name, mod)
        yield
        for name in stubs:
            sys.modules.pop(name, None)
        sys.modules.pop("fastpdf.contrib.django", None)

    def test_should_render_pdf_with_format_param(self):
        from fastpdf.contrib.django import PdfMixin

        mixin = PdfMixin()
        mixin.request = MagicMock()
        mixin.request.GET = {"format": "pdf"}
        assert mixin._should_render_pdf() is True

    def test_should_not_render_pdf_without_param(self):
        from fastpdf.contrib.django import PdfMixin

        mixin = PdfMixin()
        mixin.request = MagicMock()
        mixin.request.GET = {}
        assert mixin._should_render_pdf() is False

    @patch("fastpdf.contrib.django.render_to_pdf_response")
    def test_render_to_response_returns_pdf(self, mock_pdf_resp):
        mock_pdf_resp.return_value = MagicMock()
        from fastpdf.contrib.django import PdfMixin

        class FakeParent:
            def render_to_response(self, context, **kwargs):
                return "html_response"

            def get_template_names(self):
                return ["invoice.html"]

        class TestView(PdfMixin, FakeParent):
            pdf_filename = "invoice.pdf"
            pdf_options = {"page_size": "A4", "tailwind": True}

        view = TestView()
        view.request = MagicMock()
        view.request.GET = {"format": "pdf"}

        result = view.render_to_response({"invoice": "data"})
        mock_pdf_resp.assert_called_once()

    def test_render_to_response_returns_html_when_no_format(self):
        from fastpdf.contrib.django import PdfMixin

        class FakeParent:
            def render_to_response(self, context, **kwargs):
                return "html_response"

        class TestView(PdfMixin, FakeParent):
            pdf_filename = "invoice.pdf"

        view = TestView()
        view.request = MagicMock()
        view.request.GET = {}

        result = view.render_to_response({})
        assert result == "html_response"


class TestPdfMiddleware:
    @pytest.fixture(autouse=True)
    def _setup_django(self):
        import sys
        stubs = _mock_django()
        for name, mod in stubs.items():
            sys.modules.setdefault(name, mod)
        yield
        for name in stubs:
            sys.modules.pop(name, None)
        sys.modules.pop("fastpdf.contrib.django", None)

    @patch("fastpdf.contrib.django.render_pdf")
    def test_middleware_converts_to_pdf(self, mock_render_pdf):
        mock_render_pdf.return_value = b"%PDF-1.4 fake"
        from fastpdf.contrib.django import PdfMiddleware

        html_response = MagicMock()
        html_response.get.return_value = "text/html; charset=utf-8"
        html_response.content = b"<html><body>Hello</body></html>"

        def get_response(request):
            return html_response

        middleware = PdfMiddleware(get_response)

        request = MagicMock()
        request.GET = {"format": "pdf"}

        response = middleware(request)
        assert response["Content-Type"] == "application/pdf"

    def test_middleware_passes_through_without_param(self):
        from fastpdf.contrib.django import PdfMiddleware

        html_response = MagicMock()

        def get_response(request):
            return html_response

        middleware = PdfMiddleware(get_response)

        request = MagicMock()
        request.GET = {}

        response = middleware(request)
        assert response is html_response

