"""Utility helpers for FastPDF."""

from __future__ import annotations

import base64
import mimetypes
import re
from pathlib import Path
from typing import Optional, Union


def inline_images(html: str, base_path: Optional[Union[str, Path]] = None) -> str:
    """Convert relative image ``src`` attributes to data URIs.

    This is useful when generating PDFs from HTML that references local images,
    ensuring the images are embedded directly in the HTML source so the Rust
    engine doesn't need filesystem access.

    Parameters
    ----------
    html : str
        HTML string with ``<img src="...">`` tags.
    base_path : str or Path or None
        Base directory for resolving relative image paths.
        Defaults to current working directory.

    Returns
    -------
    str
        HTML with images inlined as base64 data URIs.
    """
    base = Path(base_path) if base_path else Path.cwd()
    img_pattern = re.compile(
        r'(<img\s[^>]*?)src=["\']([^"\']+?)["\']', re.IGNORECASE
    )

    def replace_src(match: re.Match) -> str:
        prefix = match.group(1)
        src = match.group(2)

        # Skip data URIs and absolute URLs
        if src.startswith(("data:", "http://", "https://")):
            return match.group(0)

        img_path = base / src
        if not img_path.exists():
            return match.group(0)

        mime_type, _ = mimetypes.guess_type(str(img_path))
        if not mime_type:
            mime_type = "application/octet-stream"

        img_data = img_path.read_bytes()
        b64 = base64.b64encode(img_data).decode("ascii")
        return f'{prefix}src="data:{mime_type};base64,{b64}"'

    return img_pattern.sub(replace_src, html)


def minify_html(html: str) -> str:
    """Minimal HTML minification - removes excess whitespace.

    This is a lightweight minification that can speed up parsing
    for large documents.
    """
    # Collapse runs of whitespace
    html = re.sub(r"\s+", " ", html)
    # Remove whitespace between tags
    html = re.sub(r">\s+<", "><", html)
    return html.strip()


def css_string(styles: dict) -> str:
    """Convert a dict of CSS properties to a CSS string.

    Example::

        css = css_string({
            "body": {"font-family": "Arial", "font-size": "12pt"},
            "h1": {"color": "#333", "margin-bottom": "20px"},
        })
    """
    parts = []
    for selector, props in styles.items():
        decls = "; ".join(f"{k}: {v}" for k, v in props.items())
        parts.append(f"{selector} {{ {decls} }}")
    return "\n".join(parts)
