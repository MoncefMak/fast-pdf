"""Tests for Django integration (unit tests, no Django required)."""

from __future__ import annotations

import pytest
from unittest.mock import patch, MagicMock


class TestDjangoImport:
    def test_import_module(self):
        """Module should import even without Django installed."""
        try:
            from fastpdf.contrib import django
        except ImportError:
            pytest.skip("django contrib not importable")

    def test_get_default_options(self):
        """Should return defaults when Django not configured."""
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
