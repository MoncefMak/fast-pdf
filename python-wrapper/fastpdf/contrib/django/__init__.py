"""
FastPDF Django Integration
==========================

Provides helpers for generating PDFs in Django views using Django's
template engine (DTL or Jinja2 configured in TEMPLATES settings).

The core ``render_pdf()`` does **not** depend on Jinja2 — Django uses
its own template backends configured via ``settings.TEMPLATES``.

Setup
-----

Install with Django extras::

    pip install ferropdf[django]

Quick start::

    from fastpdf.contrib.django import render_to_pdf_response

    def invoice_view(request, invoice_id):
        invoice = get_object_or_404(Invoice, pk=invoice_id)
        return render_to_pdf_response(
            request,
            "invoices/invoice.html",
            {"invoice": invoice},
            filename="invoice.pdf",
        )

Settings
--------

Configure in ``settings.py``::

    FERROPDF = {
        "DEFAULT_PAGE_SIZE": "A4",
        "DEFAULT_ORIENTATION": "portrait",
        "DEFAULT_MARGIN": 10.0,
        "TAILWIND": False,
        "BASE_PATH": None,  # defaults to STATIC_ROOT
    }
"""

from __future__ import annotations

import re
from typing import Any, Dict, Iterator, Optional, Union

try:
    import django  # noqa: F401
except ImportError as _exc:
    raise ImportError(
        "Django is required for fastpdf.contrib.django. "
        "Install it with: pip install ferropdf[django]"
    ) from _exc

from fastpdf.core import PdfEngine, RenderOptions, FastPdfError, render_pdf


# ---------------------------------------------------------------------------
# Settings helpers
# ---------------------------------------------------------------------------

def _get_django_settings() -> dict:
    """Load FastPDF settings from Django settings.FERROPDF."""
    try:
        from django.conf import settings
        return getattr(settings, "FERROPDF", {})
    except Exception:
        return {}


def _get_default_options(**overrides: Any) -> RenderOptions:
    """Build RenderOptions from Django settings + caller overrides."""
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

    # Apply caller overrides (page_size, tailwind, etc.)
    for key, value in overrides.items():
        if hasattr(opts, key):
            setattr(opts, key, value)

    return opts


# ---------------------------------------------------------------------------
# Static URL resolution
# ---------------------------------------------------------------------------

_STATIC_ATTR_RE = re.compile(
    r"""((?:href|src)\s*=\s*["'])(/static/[^"']+)(["'])""",
    re.IGNORECASE,
)


def resolve_static_urls(html: str) -> str:
    """Replace ``/static/...`` URLs with absolute filesystem paths.

    Uses ``django.contrib.staticfiles.finders.find()`` to resolve each
    static path to its on-disk location.

    Parameters
    ----------
    html : str
        HTML string potentially containing ``/static/...`` references.

    Returns
    -------
    str
        HTML with static URLs replaced by absolute paths.
    """
    try:
        from django.contrib.staticfiles.finders import find as find_static
    except ImportError:
        return html

    def _replace(match: re.Match) -> str:
        prefix = match.group(1)
        url_path = match.group(2)
        suffix = match.group(3)

        # Strip the leading /static/ to get the relative path
        relative = url_path
        if relative.startswith("/static/"):
            relative = relative[len("/static/"):]

        resolved = find_static(relative)
        if resolved:
            return f"{prefix}{resolved}{suffix}"
        return match.group(0)

    return _STATIC_ATTR_RE.sub(_replace, html)


# ---------------------------------------------------------------------------
# Rendering helpers
# ---------------------------------------------------------------------------

def render_to_pdf(
    template_name: str,
    context: Optional[Dict[str, Any]] = None,
    *,
    request=None,
    options: Optional[RenderOptions] = None,
    using: Optional[str] = None,
) -> bytes:
    """Render a Django template to PDF bytes.

    Uses ``django.template.loader.render_to_string()`` — works with any
    template backend configured in ``settings.TEMPLATES`` (DTL or Jinja2).
    """
    from django.template.loader import render_to_string

    html = render_to_string(template_name, context=context, request=request, using=using)
    html = resolve_static_urls(html)
    opts = options or _get_default_options()
    return render_pdf(html, options=opts)


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
    **opts_kwargs: Any,
):
    """Render a Django template to an ``HttpResponse`` with PDF content.

    Parameters
    ----------
    request : HttpRequest
        Current Django request.
    template_name : str
        Django template name.
    context : dict or None
        Template context variables.
    filename : str or None
        Download filename. If provided, sets ``Content-Disposition``.
    inline : bool
        If *True*, display inline in browser instead of downloading.
    status : int
        HTTP status code (default 200).
    options : RenderOptions or None
        PDF rendering options.  If *None*, options are built from
        ``settings.FERROPDF`` merged with any extra ``**opts_kwargs``
        (e.g. ``page_size="A4"``, ``tailwind=True``).
    using : str or None
        Django template engine to use.
    **opts_kwargs
        Shorthand overrides forwarded to ``RenderOptions`` fields.
    """
    from django.http import HttpResponse

    if options is None:
        options = _get_default_options(**opts_kwargs)

    pdf_bytes = render_to_pdf(
        template_name,
        context,
        request=request,
        options=options,
        using=using,
    )

    response = HttpResponse(
        content=pdf_bytes,
        content_type="application/pdf",
        status=status,
    )

    if filename:
        disposition = "inline" if inline else "attachment"
        response["Content-Disposition"] = f'{disposition}; filename="{filename}"'

    return response


def render_to_pdf_stream(
    request,
    template_name: str,
    context: Optional[Dict[str, Any]] = None,
    *,
    filename: Optional[str] = None,
    status: int = 200,
    options: Optional[RenderOptions] = None,
    using: Optional[str] = None,
    chunk_size: int = 8192,
    **opts_kwargs: Any,
):
    """Render a Django template to a ``StreamingHttpResponse``.

    Suitable for large PDF documents where you want to avoid holding
    the entire response in memory on the Django side.

    Parameters
    ----------
    chunk_size : int
        Byte-chunk size for streaming (default 8192).
    """
    from django.http import StreamingHttpResponse

    if options is None:
        options = _get_default_options(**opts_kwargs)

    pdf_bytes = render_to_pdf(
        template_name,
        context,
        request=request,
        options=options,
        using=using,
    )

    def _iter_chunks() -> Iterator[bytes]:
        for i in range(0, len(pdf_bytes), chunk_size):
            yield pdf_bytes[i : i + chunk_size]

    response = StreamingHttpResponse(
        streaming_content=_iter_chunks(),
        content_type="application/pdf",
        status=status,
    )

    if filename:
        response["Content-Disposition"] = f'attachment; filename="{filename}"'

    response["Content-Length"] = str(len(pdf_bytes))
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
    """Render raw HTML to an ``HttpResponse`` with PDF content.

    Useful when you build HTML programmatically instead of via templates.
    """
    from django.http import HttpResponse

    html = resolve_static_urls(html)
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


# ---------------------------------------------------------------------------
# Class-Based View mixin
# ---------------------------------------------------------------------------

class PdfMixin:
    """Mixin for Django class-based views that render PDFs.

    Compatible with ``DetailView``, ``ListView``, ``TemplateView``, etc.

    When the URL contains ``?format=pdf``, the view returns a PDF.
    Otherwise it returns the normal HTML response.

    Example::

        from django.views.generic import DetailView
        from fastpdf.contrib.django import PdfMixin

        class InvoiceView(PdfMixin, DetailView):
            model = Invoice
            template_name = "invoice.html"
            pdf_filename = "invoice.pdf"
            pdf_options = {"page_size": "A4", "tailwind": True}
    """

    pdf_filename: Optional[str] = None
    pdf_options: dict = {}
    pdf_inline: bool = False

    def get_pdf_filename(self) -> Optional[str]:
        """Return the PDF download filename. Override for dynamic names."""
        return self.pdf_filename

    def get_pdf_options(self) -> RenderOptions:
        """Build ``RenderOptions`` from ``pdf_options`` dict."""
        return _get_default_options(**self.pdf_options)

    def _should_render_pdf(self) -> bool:
        """Return *True* if the request asks for PDF output."""
        request = getattr(self, "request", None)
        if request is None:
            return False
        return request.GET.get("format") == "pdf"

    def render_to_response(self, context, **response_kwargs):
        """Override: return PDF when ``?format=pdf``, else normal HTML."""
        if not self._should_render_pdf():
            return super().render_to_response(context, **response_kwargs)

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


# ---------------------------------------------------------------------------
# Middleware
# ---------------------------------------------------------------------------

class PdfMiddleware:
    """Django middleware that converts HTML responses to PDF when
    the ``?format=pdf`` query parameter is present.

    Add to ``MIDDLEWARE``::

        MIDDLEWARE = [
            ...
            "fastpdf.contrib.django.PdfMiddleware",
        ]

    Configurable via ``settings.FERROPDF``.
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
            opts = _get_default_options()
            html = response.content.decode("utf-8", errors="replace")
            html = resolve_static_urls(html)
            pdf_bytes = render_pdf(html, options=opts)

            from django.http import HttpResponse as DjResponse

            pdf_response = DjResponse(
                content=pdf_bytes,
                content_type="application/pdf",
            )
            pdf_response["Content-Disposition"] = 'inline; filename="document.pdf"'
            return pdf_response

        return response


# Legacy alias for backwards compatibility
PdfView = PdfMixin

__all__ = [
    "render_to_pdf",
    "render_to_pdf_response",
    "render_to_pdf_stream",
    "render_html_to_pdf_response",
    "resolve_static_urls",
    "PdfMixin",
    "PdfView",
    "PdfMiddleware",
]
