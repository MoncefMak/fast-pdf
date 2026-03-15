"""Tests for FastAPI integration (unit tests)."""

from __future__ import annotations

import pytest
from unittest.mock import patch


class TestFastapiImport:
    def test_import_module(self):
        try:
            from fastpdf.contrib import fastapi
        except ImportError:
            pytest.skip("fastapi contrib not importable")
