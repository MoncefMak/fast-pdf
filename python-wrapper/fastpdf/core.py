"""
Core FastPDF API - wraps the Rust engine with a Pythonic interface.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Union

try:
    from fastpdf._engine import (
        PdfDocument as _RustPdfDocument,
        PdfEngine as _RustPdfEngine,
        RenderOptions as _RustRenderOptions,
        batch_render as _rust_batch_render,
        get_version as _rust_get_version,
        render_html_to_pdf as _rust_render_html_to_pdf,
        render_html_to_pdf_bytes as _rust_render_html_to_pdf_bytes,
    )

    _ENGINE_AVAILABLE = True
except ImportError:
    _ENGINE_AVAILABLE = False


class FastPdfError(Exception):
    """Base exception for FastPDF errors."""

    pass


class RenderError(FastPdfError):
    """Raised when PDF rendering fails."""

    pass


class TemplateError(FastPdfError):
    """Raised when template loading or rendering fails."""

    pass


class ConfigError(FastPdfError):
    """Raised when configuration is invalid."""

    pass


def _convert_rust_error(exc: Exception) -> FastPdfError:
    """Map a raw Rust/PyO3 ``RuntimeError`` to a typed ``FastPdfError`` subclass.

    PyO3 surfaces Rust errors as ``RuntimeError`` with descriptive messages.
    This helper inspects the message and returns the most specific Python
    exception so callers can ``except RenderError`` instead of a bare
    ``RuntimeError``.
    """
    msg = str(exc)
    low = msg.lower()

    if "template" in low or "jinja" in low:
        return TemplateError(f"Template rendering error: {msg}")
    if "config" in low or "option" in low or "invalid" in low:
        return ConfigError(f"Configuration error: {msg}")
    if "font" in low:
        return RenderError(
            f"Font error: {msg}\nHint: check that the font file exists and is valid TTF/OTF."
        )
    if "image" in low:
        return RenderError(f"Image processing error: {msg}")
    if "css" in low:
        return RenderError(f"CSS processing error: {msg}")
    if ("html" in low and ("parse" in low or "error" in low)) or "parse" in low:
        return RenderError(f"HTML parsing failed: {msg}")
    if "layout" in low:
        return RenderError(f"Layout computation error: {msg}")
    if "pdf" in low or "generat" in low:
        return RenderError(f"PDF generation failed: {msg}")
    return RenderError(f"Rendering failed: {msg}")


# ---------------------------------------------------------------------------
# Page size presets (width_mm, height_mm)
# ---------------------------------------------------------------------------
PAGE_SIZES = {
    "A3": (297.0, 420.0),
    "A4": (210.0, 297.0),
    "A5": (148.0, 210.0),
    "Letter": (215.9, 279.4),
    "Legal": (215.9, 355.6),
    "Tabloid": (279.4, 431.8),
}


@dataclass
class RenderOptions:
    """Options controlling PDF rendering.

    Parameters
    ----------
    page_size : str or tuple[float, float]
        Named page size (``"A4"``, ``"Letter"`` …) or ``(width_mm, height_mm)``.
    orientation : str
        ``"portrait"`` or ``"landscape"``.
    margin_top : float
        Top margin in millimetres (default 10).
    margin_right : float
        Right margin in mm (default 10).
    margin_bottom : float
        Bottom margin in mm (default 10).
    margin_left : float
        Left margin in mm (default 10).
    title : str or None
        PDF document title metadata.
    author : str or None
        PDF document author metadata.
    tailwind : bool
        If *True*, resolve Tailwind CSS utility classes before rendering.
    base_path : str or None
        Base path for resolving relative asset URLs (images, fonts …).
    header_html : str or None
        HTML fragment rendered as running header on every page.
    footer_html : str or None
        HTML fragment rendered as running footer on every page.
    """

    page_size: Union[str, tuple] = "A4"
    orientation: str = "portrait"
    margin_top: float = 10.0
    margin_right: float = 10.0
    margin_bottom: float = 10.0
    margin_left: float = 10.0
    title: Optional[str] = None
    author: Optional[str] = None
    tailwind: bool = False
    base_path: Optional[str] = None
    header_html: Optional[str] = None
    footer_html: Optional[str] = None

    def _to_rust(self) -> "_RustRenderOptions":
        """Convert to the Rust-level RenderOptions."""
        if not _ENGINE_AVAILABLE:
            raise FastPdfError(
                "FastPDF native engine not available. "
                "Install with: pip install fastpdf"
            )

        r = _RustRenderOptions()

        # Page size
        if isinstance(self.page_size, str):
            r.page_size = self.page_size
        elif isinstance(self.page_size, (tuple, list)) and len(self.page_size) == 2:
            r.page_size = f"{self.page_size[0]}x{self.page_size[1]}"
        else:
            raise ConfigError(
                f"Invalid page_size: {self.page_size!r}. "
                "Use a name like 'A4' or a (width_mm, height_mm) tuple."
            )

        # Margins (Rust expects a list [top, right, bottom, left])
        r.margins = [self.margin_top, self.margin_right, self.margin_bottom, self.margin_left]

        # Metadata
        if self.title:
            r.title = self.title
        if self.author:
            r.author = self.author

        # Features
        r.tailwind = self.tailwind
        if self.base_path:
            r.base_path = self.base_path
        if self.header_html:
            r.header_html = self.header_html
        if self.footer_html:
            r.footer_html = self.footer_html

        return r


class PdfDocument:
    """Represents a rendered PDF document.

    Provides methods to save, retrieve bytes, or inspect the document.
    """

    def __init__(self, data: bytes, page_count: int = 1, title: Optional[str] = None):
        self._data = data
        self._page_count = page_count
        self._title = title

    @property
    def page_count(self) -> int:
        """Number of pages in the PDF."""
        return self._page_count

    @property
    def title(self) -> Optional[str]:
        """Document title metadata."""
        return self._title

    def to_bytes(self) -> bytes:
        """Return the raw PDF bytes."""
        return self._data

    def save(self, path: Union[str, Path]) -> None:
        """Write the PDF to disk.

        Parameters
        ----------
        path : str or Path
            Destination file path.
        """
        p = Path(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(self._data)

    def __len__(self) -> int:
        return len(self._data)

    def __repr__(self) -> str:
        size_kb = len(self._data) / 1024
        return (
            f"<PdfDocument pages={self._page_count} "
            f"size={size_kb:.1f}KB title={self._title!r}>"
        )


class PdfEngine:
    """Full-featured PDF engine with caching and configuration.

    Use this class when you need to generate many PDFs with shared settings,
    cached fonts, or template directories.

    Example::

        engine = PdfEngine(template_dir="templates/")
        engine.register_font("custom", "/fonts/CustomFont.ttf")

        doc = engine.render("<h1>Hello</h1>")
        doc.save("hello.pdf")

        doc2 = engine.render_template("invoice.html", context={...})
        doc2.save("invoice.pdf")
    """

    def __init__(
        self,
        *,
        default_options: Optional[RenderOptions] = None,
        template_dir: Optional[Union[str, Path]] = None,
        base_path: Optional[Union[str, Path]] = None,
    ):
        if not _ENGINE_AVAILABLE:
            raise FastPdfError(
                "FastPDF native engine not available. "
                "Install with: pip install fastpdf"
            )

        self._rust_engine = _RustPdfEngine()
        self._default_options = default_options or RenderOptions()
        self._template_dir = Path(template_dir) if template_dir else None
        self._jinja_env = None

        if base_path:
            self._rust_engine.set_base_path(str(base_path))
            self._default_options.base_path = str(base_path)

    def _get_jinja_env(self):
        """Lazy-initialise Jinja2 environment."""
        if self._jinja_env is None:
            try:
                from jinja2 import Environment, FileSystemLoader, select_autoescape
            except ImportError:
                raise FastPdfError(
                    "jinja2 is required for template rendering. "
                    "Install with: pip install jinja2"
                )

            loader_paths = []
            if self._template_dir and self._template_dir.exists():
                loader_paths.append(str(self._template_dir))
            loader_paths.append(".")

            self._jinja_env = Environment(
                loader=FileSystemLoader(loader_paths),
                autoescape=select_autoescape(["html", "xml"]),
            )
        return self._jinja_env

    def register_font(
        self,
        name: str,
        path: Union[str, Path],
        *,
        weight: str = "normal",
        italic: bool = False,
    ) -> None:
        """Register a custom font file.

        Parameters
        ----------
        name : str
            Font family name to use in CSS.
        path : str or Path
            Path to the font file (.ttf, .otf, .woff2).
        weight : str
            Font weight (e.g. ``"normal"``, ``"bold"``, ``"300"``).
        italic : bool
            Whether this is an italic variant.
        """
        _weight_map = {
            "normal": 400, "bold": 700,
            "100": 100, "200": 200, "300": 300, "400": 400,
            "500": 500, "600": 600, "700": 700, "800": 800, "900": 900,
        }
        w = _weight_map.get(str(weight), 400)
        self._rust_engine.register_font(name, str(path), w, italic)

    def render(
        self,
        html: str,
        *,
        css: Optional[str] = None,
        options: Optional[RenderOptions] = None,
    ) -> PdfDocument:
        """Render an HTML string to a PDF document.

        Parameters
        ----------
        html : str
            HTML content to render.
        css : str or None
            Additional CSS to apply (injected as ``<style>`` block).
        options : RenderOptions or None
            Override default rendering options.
        """
        opts = options or self._default_options

        if css:
            html = f"<style>{css}</style>\n{html}"

        rust_opts = opts._to_rust()
        try:
            pdf_bytes = self._rust_engine.render(html, options=rust_opts)
        except Exception as e:
            raise _convert_rust_error(e) from e

        return PdfDocument(
            data=pdf_bytes,
            page_count=1,  # TODO: get from rust engine
            title=opts.title,
        )

    def render_template(
        self,
        template_name: str,
        *,
        context: Optional[Dict[str, Any]] = None,
        css: Optional[str] = None,
        options: Optional[RenderOptions] = None,
    ) -> PdfDocument:
        """Render a Jinja2 template to a PDF document.

        Parameters
        ----------
        template_name : str
            Template filename (resolved from ``template_dir``).
        context : dict or None
            Template context variables.
        css : str or None
            Additional CSS to apply.
        options : RenderOptions or None
            Override default rendering options.
        """
        env = self._get_jinja_env()
        try:
            template = env.get_template(template_name)
        except Exception as e:
            raise TemplateError(f"Failed to load template '{template_name}': {e}")

        try:
            html = template.render(**(context or {}))
        except Exception as e:
            raise TemplateError(f"Failed to render template '{template_name}': {e}")

        return self.render(html, css=css, options=options)

    def render_to_file(
        self,
        html: str,
        path: Union[str, Path],
        *,
        css: Optional[str] = None,
        options: Optional[RenderOptions] = None,
    ) -> PdfDocument:
        """Render HTML and save directly to a file.

        Returns the PdfDocument for further inspection.
        """
        doc = self.render(html, css=css, options=options)
        doc.save(path)
        return doc

    def batch_render(
        self,
        items: Sequence[Dict[str, Any]],
        *,
        options: Optional[RenderOptions] = None,
        parallel: bool = True,
    ) -> List[PdfDocument]:
        """Render multiple HTMLs in parallel.

        Parameters
        ----------
        items : list of dict
            Each dict should have an ``"html"`` key and optionally ``"css"``
            and ``"options"`` keys.
        options : RenderOptions or None
            Default options applied to all items.
        parallel : bool
            If *True*, render in parallel using Rayon thread pool.
        """
        opts = options or self._default_options
        rust_opts = opts._to_rust()

        doc_pairs = []
        for item in items:
            html = item.get("html", "")
            css = item.get("css", "")
            doc_pairs.append((html, css))

        try:
            results = self._rust_engine.batch_render(doc_pairs, options=rust_opts)
        except Exception as e:
            raise _convert_rust_error(e) from e

        return [
            PdfDocument(data=pdf_bytes, page_count=1, title=opts.title)
            for pdf_bytes in results
        ]


# ---------------------------------------------------------------------------
# Module-level convenience functions
# ---------------------------------------------------------------------------


def render_pdf(
    html: str,
    *,
    css: Optional[str] = None,
    options: Optional[RenderOptions] = None,
) -> bytes:
    """Render HTML to PDF bytes.

    This is the simplest way to generate a PDF::

        pdf_bytes = render_pdf("<h1>Hello</h1>")

    Parameters
    ----------
    html : str
        HTML content to render.
    css : str or None
        Additional CSS stylesheet.
    options : RenderOptions or None
        Rendering options.

    Returns
    -------
    bytes
        Raw PDF file content.
    """
    if not _ENGINE_AVAILABLE:
        raise FastPdfError("FastPDF native engine not available.")

    if css:
        html = f"<style>{css}</style>\n{html}"

    try:
        if options:
            rust_opts = options._to_rust()
            return _rust_render_html_to_pdf_bytes(html, options=rust_opts)
        else:
            return _rust_render_html_to_pdf_bytes(html)
    except FastPdfError:
        raise
    except Exception as e:
        raise _convert_rust_error(e) from e


def render_pdf_to_file(
    html: str,
    path: Union[str, Path],
    *,
    css: Optional[str] = None,
    options: Optional[RenderOptions] = None,
) -> PdfDocument:
    """Render HTML to a PDF file.

    Parameters
    ----------
    html : str
        HTML content to render.
    path : str or Path
        Output file path.
    css : str or None
        Additional CSS.
    options : RenderOptions or None
        Rendering options.

    Returns
    -------
    PdfDocument
        The rendered document.
    """
    pdf_bytes = render_pdf(html, css=css, options=options)
    doc = PdfDocument(data=pdf_bytes, title=options.title if options else None)
    doc.save(path)
    return doc


def render_pdf_from_template(
    template_name: str,
    *,
    context: Optional[Dict[str, Any]] = None,
    template_dir: Optional[Union[str, Path]] = None,
    css: Optional[str] = None,
    options: Optional[RenderOptions] = None,
) -> bytes:
    """Render a Jinja2 template to PDF bytes.

    Parameters
    ----------
    template_name : str
        Template filename.
    context : dict or None
        Template variables.
    template_dir : str or Path or None
        Directory containing templates.
    css : str or None
        Additional CSS.
    options : RenderOptions or None
        Rendering options.

    Returns
    -------
    bytes
        Raw PDF content.
    """
    engine = PdfEngine(
        template_dir=template_dir,
        default_options=options or RenderOptions(),
    )
    doc = engine.render_template(template_name, context=context, css=css, options=options)
    return doc.to_bytes()


def batch_render(
    items: Sequence[Dict[str, Any]],
    *,
    options: Optional[RenderOptions] = None,
    parallel: bool = True,
) -> List[bytes]:
    """Render multiple HTML documents to PDF bytes in parallel.

    Parameters
    ----------
    items : list of dict
        Each dict has ``"html"`` and optionally ``"css"`` keys.
    options : RenderOptions or None
        Default options for all items.
    parallel : bool
        Use parallel rendering.

    Returns
    -------
    list of bytes
        PDF bytes for each input.
    """
    engine = PdfEngine(default_options=options or RenderOptions())
    docs = engine.batch_render(items, options=options, parallel=parallel)
    return [doc.to_bytes() for doc in docs]


def get_version() -> str:
    """Return the FastPDF version string."""
    if _ENGINE_AVAILABLE:
        return _rust_get_version()
    return "0.1.0 (engine unavailable)"
