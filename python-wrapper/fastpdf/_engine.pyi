"""Type stubs for fastpdf._engine (Rust native module)."""

from typing import List, Optional, Tuple


class RenderOptions:
    page_size: str
    orientation: str
    margins: List[float]
    title: str
    author: str
    tailwind: bool
    base_path: str
    header_html: str
    footer_html: str

    def __init__(
        self,
        page_size: str = "a4",
        orientation: str = "portrait",
        margins: Optional[List[float]] = None,
        title: str = "",
        author: str = "",
        tailwind: bool = False,
        base_path: str = "",
        header_html: str = "",
        footer_html: str = "",
    ) -> None: ...


class PdfDocument:
    def to_bytes(self) -> bytes: ...
    def save(self, path: str) -> None: ...
    @property
    def page_count(self) -> int: ...
    @property
    def size(self) -> int: ...


class PdfEngine:
    def __init__(self) -> None: ...
    def render(
        self,
        html: str,
        css: Optional[str] = None,
        options: Optional[RenderOptions] = None,
    ) -> PdfDocument: ...
    def render_to_file(
        self,
        html: str,
        output: str,
        css: Optional[str] = None,
        options: Optional[RenderOptions] = None,
    ) -> None: ...
    def batch_render(
        self,
        documents: List[Tuple[str, str]],
        options: Optional[RenderOptions] = None,
        parallel: bool = True,
    ) -> List[PdfDocument]: ...
    def register_font(
        self,
        family: str,
        path: str,
        weight: Optional[int] = None,
        italic: Optional[bool] = None,
    ) -> None: ...
    def set_base_path(self, path: str) -> None: ...


def render_html_to_pdf(
    html: str,
    output: str,
    css: Optional[str] = None,
    options: Optional[RenderOptions] = None,
) -> None: ...
def render_html_to_pdf_bytes(
    html: str,
    css: Optional[str] = None,
    options: Optional[RenderOptions] = None,
) -> PdfDocument: ...
def batch_render(
    documents: List[Tuple[str, str]],
    options: Optional[RenderOptions] = None,
    parallel: bool = True,
) -> List[PdfDocument]: ...
def get_version() -> str: ...
    options: Optional[RenderOptions] = None,
) -> List[bytes]: ...
def get_version() -> str: ...
