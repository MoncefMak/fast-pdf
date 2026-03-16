"""Tests for FastAPI integration (unit tests)."""

from __future__ import annotations

import asyncio
import pytest
from unittest.mock import patch, MagicMock


class TestFastapiImport:
    def test_import_module(self):
        try:
            from fastpdf.contrib import fastapi
        except ImportError:
            pytest.skip("fastapi contrib not importable")

    def test_import_fails_without_starlette(self):
        """Should raise ImportError with install hint when starlette missing."""
        import sys

        saved_starlette = {}
        for key in list(sys.modules):
            if key.startswith("starlette"):
                saved_starlette[key] = sys.modules.pop(key)
        # Also remove the cached contrib module
        sys.modules.pop("fastpdf.contrib.fastapi", None)

        # Block starlette import
        import builtins
        original_import = builtins.__import__

        def blocked_import(name, *args, **kwargs):
            if name.startswith("starlette"):
                raise ImportError("No module named 'starlette'")
            return original_import(name, *args, **kwargs)

        builtins.__import__ = blocked_import
        try:
            with pytest.raises(ImportError, match="pip install ferropdf\\[fastapi\\]"):
                import importlib
                importlib.import_module("fastpdf.contrib.fastapi")
        finally:
            builtins.__import__ = original_import
            sys.modules.update(saved_starlette)
            sys.modules.pop("fastpdf.contrib.fastapi", None)


class TestPdfResponse:
    @patch("fastpdf.contrib.fastapi.render_pdf")
    def test_returns_pdf_media_type(self, mock_render):
        mock_render.return_value = b"%PDF-1.4 fake"
        from fastpdf.contrib.fastapi import PdfResponse

        resp = PdfResponse("<h1>Test</h1>", filename="test.pdf")
        assert resp.media_type == "application/pdf"
        assert resp.body == b"%PDF-1.4 fake"

    @patch("fastpdf.contrib.fastapi.render_pdf")
    def test_content_disposition_inline_by_default(self, mock_render):
        mock_render.return_value = b"%PDF-1.4 fake"
        from fastpdf.contrib.fastapi import PdfResponse

        resp = PdfResponse("<h1>Test</h1>", filename="test.pdf")
        assert "inline" in resp.headers.get("content-disposition", "")

    @patch("fastpdf.contrib.fastapi.render_pdf")
    def test_content_disposition_attachment(self, mock_render):
        mock_render.return_value = b"%PDF-1.4 fake"
        from fastpdf.contrib.fastapi import PdfResponse

        resp = PdfResponse("<h1>Test</h1>", filename="test.pdf", inline=False)
        assert "attachment" in resp.headers.get("content-disposition", "")

    @patch("fastpdf.contrib.fastapi.render_pdf")
    def test_status_code(self, mock_render):
        mock_render.return_value = b"%PDF-1.4 fake"
        from fastpdf.contrib.fastapi import PdfResponse

        resp = PdfResponse("<h1>Test</h1>", status_code=201)
        assert resp.status_code == 201


class TestStreamingPdfResponse:
    @patch("fastpdf.contrib.fastapi.render_pdf")
    def test_returns_pdf_media_type(self, mock_render):
        mock_render.return_value = b"%PDF-1.4 fake"
        from fastpdf.contrib.fastapi import StreamingPdfResponse

        resp = StreamingPdfResponse("<h1>Test</h1>", filename="test.pdf")
        assert resp.media_type == "application/pdf"

    @patch("fastpdf.contrib.fastapi.render_pdf")
    def test_has_content_length(self, mock_render):
        mock_render.return_value = b"%PDF-1.4 fake"
        from fastpdf.contrib.fastapi import StreamingPdfResponse

        resp = StreamingPdfResponse("<h1>Test</h1>", filename="test.pdf")
        assert resp.headers.get("content-length") == str(len(b"%PDF-1.4 fake"))


class TestRenderPdfAsync:
    @patch("fastpdf.contrib.fastapi.render_pdf")
    def test_render_pdf_async_returns_bytes(self, mock_render):
        mock_render.return_value = b"%PDF-1.4 fake"
        from fastpdf.contrib.fastapi import render_pdf_async

        result = asyncio.get_event_loop().run_until_complete(
            render_pdf_async("<h1>Test</h1>")
        )
        assert isinstance(result, bytes)
        assert result == b"%PDF-1.4 fake"

    @patch("fastpdf.contrib.fastapi.render_pdf")
    def test_render_pdf_async_is_non_blocking(self, mock_render):
        """Verify render_pdf_async runs in executor (non-blocking)."""
        import time
        call_threads = []

        def slow_render(html, **kwargs):
            import threading
            call_threads.append(threading.current_thread().name)
            return b"%PDF-1.4 fake"

        mock_render.side_effect = slow_render
        from fastpdf.contrib.fastapi import render_pdf_async

        asyncio.get_event_loop().run_until_complete(
            render_pdf_async("<h1>Test</h1>")
        )
        # The render should have run in a thread pool worker, not the main thread
        assert len(call_threads) == 1
        assert "ferropdf-worker" in call_threads[0] or "ThreadPool" in call_threads[0]
