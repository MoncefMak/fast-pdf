"""
FastPDF Django Integration
==========================

Provides helpers for generating PDFs in Django views using Django templates.

Setup
-----

Add ``"fastpdf.contrib.django"`` to ``INSTALLED_APPS`` (optional, for
management commands and template tag support).

Quick start::

    from fastpdf.contrib.django import render_to_pdf_response

    def invoice_view(request, invoice_id):
        invoice = get_object_or_404(Invoice, pk=invoice_id)
        context = {"invoice": invoice, "items": invoice.items.all()}
        return render_to_pdf_response(
            request,
            "invoices/invoice.html",
            context,
            filename="invoice.pdf",
        )

Settings
--------

Configure in ``settings.py``::

    FASTPDF = {
        "DEFAULT_PAGE_SIZE": "A4",
        "DEFAULT_ORIENTATION": "portrait",
        "DEFAULT_MARGIN": 10.0,
        "TAILWIND": False,
        "BASE_PATH": None,  # defaults to STATIC_ROOT
    }
"""

from __future__ import annotations

from typing import Any, Dict, Optional, Union

from fastpdf.core import PdfDocument, PdfEngine, RenderOptions, FastPdfError


def _get_django_settings() -> dict:
    """Load FastPDF settings from Django settings.FASTPDF."""
    try:
        from django.conf import settings

        return getattr(settings, "FASTPDF", {})
    except Exception:
        return {}


def _get_default_options() -> RenderOptions:
    """Build RenderOptions from Django settings."""
    conf = _get_django_settings()
    opts = RenderOptions()
    if "DEFAULT_PAGE_SIZE" in conf:
        opts.page_size = conf["DEFAULT_PAGE_SIZE"]
    if "DEFAULT_ORIENTATION" in conf:
        opts.orientation = conf["DEFAULT_ORIENTATION"]
    if "DEFAULT_MARGIN" in conf:
        m = conf["DEFAULT_MARGIN"]
        opts.margin_top = m
        opts.margin_right = m
        opts.margin_bottom = m
        opts.margin_left = m
    if "TAILWIND" in conf:
        opts.tailwind = conf["TAILWIND"]
    if "BASE_PATH" in conf:
        opts.base_path = conf["BASE_PATH"]
    else:
        try:
            from django.conf import settings as django_settings

            static_root = getattr(django_settings, "STATIC_ROOT", None)
            if static_root:
                opts.base_path = str(static_root)
        except Exception:
            pass
    return opts


def render_to_pdf(
    template_name: str,
    context: Optional[Dict[str, Any]] = None,
    *,
    request=None,
    options: Optional[RenderOptions] = None,
    using: Optional[str] = None,
) -> PdfDocument:
    """Render a Django template to a PdfDocument.

    Parameters
    ----------
    template_name : str
        Django template name (resolved through template loaders).
    context : dict or None
        Template context.
    request : HttpRequest or None
        Current request (needed for RequestContext).
    options : RenderOptions or None
        Rendering options (defaults to settings).
    using : str or None
        Template engine to use.

    Returns
    -------
    PdfDocument
        The rendered PDF document.
    """
    from django.template.loader import render_to_string

    html = render_to_string(template_name, context=context, request=request, using=using)
    opts = options or _get_default_options()

    engine = PdfEngine(default_options=opts)
    return engine.render(html, options=opts)


def render_to_pdf_response(
    request,
    template_name: str,
    context: Optional[Dict[str, Any]] = None,
    *,
    filename: Optional[str] = None,
    inline: bool = False,
    status: int = 200,
    options: Optional[RenderOptions] = None,
    using: Optional[str] = None,
):
    """Render a Django template to an HttpResponse with PDF content.

    Parameters
    ----------
    request : HttpRequest
        Current Django request.
    template_name : str
        Django template name.
    context : dict or None
        Template context variables.
    filename : str or None
        Download filename. If provided, sets Content-Disposition.
    inline : bool
        If *True*, display inline in browser instead of downloading.
    status : int
        HTTP status code (default 200).
    options : RenderOptions or None
        PDF rendering options.
    using : str or None
        Django template engine to use.

    Returns
    -------
    HttpResponse
        Django response with ``application/pdf`` content type.
    """
    from django.http import HttpResponse

    doc = render_to_pdf(
        template_name,
        context,
        request=request,
        options=options,
        using=using,
    )

    response = HttpResponse(
        content=doc.to_bytes(),
        content_type="application/pdf",
        status=status,
    )

    if filename:
        disposition = "inline" if inline else "attachment"
        response["Content-Disposition"] = f'{disposition}; filename="{filename}"'

    return response


def render_html_to_pdf_response(
    html: str,
    *,
    filename: Optional[str] = None,
    inline: bool = False,
    status: int = 200,
    options: Optional[RenderOptions] = None,
    css: Optional[str] = None,
):
    """Render raw HTML to an HttpResponse with PDF content.

    Useful when you build HTML programmatically instead of via templates.
    """
    from django.http import HttpResponse
    from fastpdf.core import render_pdf

    pdf_bytes = render_pdf(html, css=css, options=options)

    response = HttpResponse(
        content=pdf_bytes,
        content_type="application/pdf",
        status=status,
    )

    if filename:
        disposition = "inline" if inline else "attachment"
        response["Content-Disposition"] = f'{disposition}; filename="{filename}"'

    return response


class PdfView:
    """Mixin for Django class-based views that render PDFs.

    Example::

        from django.views.generic import DetailView
        from fastpdf.contrib.django import PdfView

        class InvoicePdfView(PdfView, DetailView):
            model = Invoice
            template_name = "invoices/invoice.html"
            pdf_filename = "invoice.pdf"

    Or as a standalone view::

        class ReportView(PdfView):
            template_name = "reports/monthly.html"
            pdf_filename = "report.pdf"

            def get_context_data(self, **kwargs):
                return {"data": self.get_report_data()}
    """

    pdf_filename: Optional[str] = None
    pdf_inline: bool = False
    pdf_options: Optional[RenderOptions] = None

    def get_pdf_filename(self) -> Optional[str]:
        return self.pdf_filename

    def get_pdf_options(self) -> RenderOptions:
        return self.pdf_options or _get_default_options()

    def render_to_response(self, context, **response_kwargs):
        """Override to return PDF response instead of HTML."""
        template_name = self.get_template_names()[0]
        request = getattr(self, "request", None)
        return render_to_pdf_response(
            request,
            template_name,
            context,
            filename=self.get_pdf_filename(),
            inline=self.pdf_inline,
            options=self.get_pdf_options(),
        )


class PdfMiddleware:
    """Django middleware that converts HTML responses to PDF when
    the ``?format=pdf`` query parameter is present.

    Add to ``MIDDLEWARE``::

        MIDDLEWARE = [
            ...
            "fastpdf.contrib.django.PdfMiddleware",
        ]

    Then any view can be rendered as PDF by appending ``?format=pdf`` to the URL.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        if (
            request.GET.get("format") == "pdf"
            and response.get("Content-Type", "").startswith("text/html")
            and hasattr(response, "content")
        ):
            from fastpdf.core import render_pdf

            opts = _get_default_options()
            html = response.content.decode("utf-8", errors="replace")
            pdf_bytes = render_pdf(html, options=opts)

            from django.http import HttpResponse as DjResponse

            pdf_response = DjResponse(
                content=pdf_bytes,
                content_type="application/pdf",
            )
            pdf_response["Content-Disposition"] = 'inline; filename="document.pdf"'
            return pdf_response

        return response
