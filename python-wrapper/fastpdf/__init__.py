"""
FastPDF - High-performance PDF generation from HTML/CSS/Tailwind templates.

This package provides a fast, Rust-powered PDF rendering engine with
a clean Python API and integrations for Django and FastAPI.

Basic usage::

    from fastpdf import render_pdf, render_pdf_to_file

    # Render to bytes
    pdf_bytes = render_pdf("<h1>Hello World</h1>")

    # Render to file
    render_pdf_to_file("<h1>Hello World</h1>", "output.pdf")

    # With options
    from fastpdf import RenderOptions
    opts = RenderOptions(page_size="Letter", title="My Document")
    pdf_bytes = render_pdf(html, options=opts)

Template rendering::

    from fastpdf import render_pdf_from_template

    pdf_bytes = render_pdf_from_template(
        "invoice.html",
        context={"customer": "Acme Corp", "total": 1234.56},
        template_dir="templates/",
    )
"""

from __future__ import annotations

__version__ = "0.1.0"

from fastpdf.core import (
    FastPdfError,
    PdfDocument,
    PdfEngine,
    RenderOptions,
    batch_render,
    get_version,
    render_pdf,
    render_pdf_from_template,
    render_pdf_to_file,
)

__all__ = [
    "FastPdfError",
    "PdfDocument",
    "PdfEngine",
    "RenderOptions",
    "batch_render",
    "get_version",
    "render_pdf",
    "render_pdf_from_template",
    "render_pdf_to_file",
]
