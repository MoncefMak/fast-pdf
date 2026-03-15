"""
FastPDF FastAPI Integration
===========================

Provides response helpers for generating PDFs in FastAPI applications.

Quick start::

    from fastapi import FastAPI
    from fastpdf.contrib.fastapi import PdfResponse, render_pdf_response

    app = FastAPI()

    @app.get("/invoice/{invoice_id}")
    async def get_invoice(invoice_id: int):
        html = f"<h1>Invoice #{invoice_id}</h1><p>Amount: $100.00</p>"
        return PdfResponse(html, filename="invoice.pdf")

Template rendering::

    from fastpdf.contrib.fastapi import render_template_to_pdf_response

    @app.get("/report")
    async def get_report():
        return render_template_to_pdf_response(
            "report.html",
            context={"title": "Monthly Report", "data": get_data()},
            template_dir="templates/",
            filename="report.pdf",
        )
"""

from __future__ import annotations

import asyncio
from concurrent.futures import ThreadPoolExecutor
from typing import Any, Dict, List, Optional, Sequence, Union

from starlette.responses import Response

from fastpdf.core import (
    PdfDocument,
    PdfEngine,
    RenderOptions,
    render_pdf,
    render_pdf_from_template,
)


# Dedicated thread pool for PDF rendering — avoids saturating the asyncio default pool
_pdf_executor = ThreadPoolExecutor(
    max_workers=4,
    thread_name_prefix="ferropdf-worker"
)
# Legacy alias for backwards compatibility
_executor = _pdf_executor


class PdfResponse(Response):
    """FastAPI/Starlette response that renders HTML to PDF.

    Example::

        @app.get("/doc")
        async def get_doc():
            return PdfResponse(
                "<h1>Hello</h1>",
                filename="hello.pdf",
            )
    """

    media_type = "application/pdf"

    def __init__(
        self,
        html: str,
        *,
        css: Optional[str] = None,
        options: Optional[RenderOptions] = None,
        filename: Optional[str] = None,
        inline: bool = False,
        status_code: int = 200,
        headers: Optional[Dict[str, str]] = None,
    ):
        pdf_bytes = render_pdf(html, css=css, options=options)

        resp_headers = dict(headers or {})
        if filename:
            disposition = "inline" if inline else "attachment"
            resp_headers["Content-Disposition"] = (
                f'{disposition}; filename="{filename}"'
            )

        super().__init__(
            content=pdf_bytes,
            status_code=status_code,
            headers=resp_headers,
            media_type=self.media_type,
        )


class StreamingPdfResponse(Response):
    """PDF response that can be used with larger documents.

    Currently renders fully and returns. Future versions may support
    true streaming as the Rust engine adds streaming support.
    """

    media_type = "application/pdf"

    def __init__(
        self,
        html: str,
        *,
        css: Optional[str] = None,
        options: Optional[RenderOptions] = None,
        filename: Optional[str] = None,
        status_code: int = 200,
        headers: Optional[Dict[str, str]] = None,
    ):
        pdf_bytes = render_pdf(html, css=css, options=options)

        resp_headers = dict(headers or {})
        if filename:
            resp_headers["Content-Disposition"] = (
                f'attachment; filename="{filename}"'
            )
        resp_headers["Content-Length"] = str(len(pdf_bytes))

        super().__init__(
            content=pdf_bytes,
            status_code=status_code,
            headers=resp_headers,
            media_type=self.media_type,
        )


async def render_pdf_async(
    html: str,
    *,
    css: Optional[str] = None,
    options: Optional[RenderOptions] = None,
) -> bytes:
    """Render HTML to PDF bytes asynchronously.

    Runs the CPU-bound Rust rendering in a thread pool to avoid blocking
    the async event loop.

    Parameters
    ----------
    html : str
        HTML content.
    css : str or None
        Additional CSS.
    options : RenderOptions or None
        Rendering options.

    Returns
    -------
    bytes
        Raw PDF content.
    """
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(
        _pdf_executor,
        lambda: render_pdf(html, css=css, options=options),
    )


async def batch_render_async(
    items: Sequence[Dict[str, Any]],
    *,
    options: Optional[RenderOptions] = None,
) -> List[bytes]:
    """Render multiple HTML documents to PDF asynchronously.

    Uses the Rust engine's parallel batch rendering via a thread pool.
    """
    from fastpdf.core import batch_render as sync_batch_render

    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(
        _executor,
        lambda: sync_batch_render(items, options=options),
    )


def render_pdf_response(
    html: str,
    *,
    css: Optional[str] = None,
    options: Optional[RenderOptions] = None,
    filename: Optional[str] = None,
    inline: bool = False,
    status_code: int = 200,
) -> Response:
    """Convenience function to render HTML and return a Starlette Response.

    Parameters
    ----------
    html : str
        HTML content.
    css : str or None
        Additional CSS.
    options : RenderOptions or None
        Rendering options.
    filename : str or None
        Download filename.
    inline : bool
        Display inline in browser.
    status_code : int
        HTTP status code.

    Returns
    -------
    Response
        Starlette response with PDF content.
    """
    pdf_bytes = render_pdf(html, css=css, options=options)

    headers = {}
    if filename:
        disposition = "inline" if inline else "attachment"
        headers["Content-Disposition"] = f'{disposition}; filename="{filename}"'

    return Response(
        content=pdf_bytes,
        status_code=status_code,
        headers=headers,
        media_type="application/pdf",
    )


def render_template_to_pdf_response(
    template_name: str,
    *,
    context: Optional[Dict[str, Any]] = None,
    template_dir: Optional[str] = None,
    css: Optional[str] = None,
    options: Optional[RenderOptions] = None,
    filename: Optional[str] = None,
    inline: bool = False,
    status_code: int = 200,
) -> Response:
    """Render a Jinja2 template to a PDF response.

    Parameters
    ----------
    template_name : str
        Template filename.
    context : dict or None
        Template variables.
    template_dir : str or None
        Directory containing templates.
    css : str or None
        Additional CSS.
    options : RenderOptions or None
        Rendering options.
    filename : str or None
        Download filename.
    inline : bool
        Display inline in browser.
    status_code : int
        HTTP status code.
    """
    pdf_bytes = render_pdf_from_template(
        template_name,
        context=context,
        template_dir=template_dir,
        css=css,
        options=options,
    )

    headers = {}
    if filename:
        disposition = "inline" if inline else "attachment"
        headers["Content-Disposition"] = f'{disposition}; filename="{filename}"'

    return Response(
        content=pdf_bytes,
        status_code=status_code,
        headers=headers,
        media_type="application/pdf",
    )
