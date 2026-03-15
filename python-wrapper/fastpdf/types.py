"""FastPDF type annotations."""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Sequence, Tuple, Union

from fastpdf.core import PdfDocument, PdfEngine, RenderOptions

# Type aliases for user convenience
HtmlInput = Union[str, bytes]
PageSize = Union[str, Tuple[float, float]]
Context = Dict[str, Any]
BatchItem = Dict[str, Any]
BatchItems = Sequence[BatchItem]
