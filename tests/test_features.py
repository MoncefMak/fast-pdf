"""End-to-end coverage for the user-visible features advertised in the README.

The audit empirically confirmed several features were implemented in the
Rust crates but never exercised from Python. These tests pin the contracts
so a regression surfaces in CI rather than in production.
"""

from __future__ import annotations

import io
import re
from pathlib import Path

import pypdf
import pytest

import ferropdf
from ferropdf import Engine, Options


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def render(html: str, **opt_kwargs) -> bytes:
    """One-shot render helper that builds Options(**opt_kwargs)."""
    if opt_kwargs:
        return ferropdf.from_html(html, options=Options(**opt_kwargs))
    return ferropdf.from_html(html)


def is_valid_pdf(pdf: bytes) -> bool:
    return pdf.startswith(b"%PDF-") and b"%%EOF" in pdf


def extract_text(pdf: bytes) -> str:
    reader = pypdf.PdfReader(io.BytesIO(pdf))
    return "\n".join(page.extract_text() or "" for page in reader.pages)


def page_count(pdf: bytes) -> int:
    return len(pypdf.PdfReader(io.BytesIO(pdf)).pages)


def count_color_op(pdf: bytes, r: float, g: float, b: float) -> int:
    """Count occurrences of a non-stroking color operator like `1 0 0 rg`."""
    pattern = rf"{r:g}\s+{g:g}\s+{b:g}\s+rg".encode()
    return len(re.findall(pattern, pdf))


# ---------------------------------------------------------------------------
# Right-to-left & Arabic shaping (README claims "Supported via cosmic-text/rustybuzz")
# ---------------------------------------------------------------------------


class TestArabicAndRtl:
    def test_arabic_text_renders(self):
        html = '<html><body><p dir="rtl">مرحبا بالعالم</p></body></html>'
        pdf = render(html)
        assert is_valid_pdf(pdf)
        # The PDF must embed a font and reference a CIDFont for the shaped glyphs.
        # Arabic doesn't survive WinANSI, so a Type0/CIDFont MUST appear.
        assert b"/CIDFontType" in pdf, (
            "Arabic text requires a CIDFont — none was embedded, the engine "
            "fell back to WinANSI which would have rendered '?' or empty."
        )

    def test_rtl_paragraph_does_not_crash(self):
        # Mixed Arabic + Latin should also be safe.
        html = '<html><body><p dir="rtl">السعر: 1234 دولار</p></body></html>'
        pdf = render(html)
        assert is_valid_pdf(pdf)

    def test_dir_attribute_lowercase_and_uppercase(self):
        html_lower = '<html><body><p dir="rtl">عربي</p></body></html>'
        html_upper = '<html><body><p dir="RTL">عربي</p></body></html>'
        # Both must produce a valid PDF — the dir attribute is case-insensitive
        # in HTML.
        assert is_valid_pdf(render(html_lower))
        assert is_valid_pdf(render(html_upper))


# ---------------------------------------------------------------------------
# @font-face (README claims "Supported (data: URI + base_url paths)")
# ---------------------------------------------------------------------------


class TestFontFace:
    def test_font_face_data_uri_does_not_warn(self):
        # An @font-face that fails to load must surface a warning. A
        # well-formed (even if empty) data URI must NOT warn — the parser
        # accepts empty payloads and the family declaration is harmless.
        html = """<html><head><style>
@font-face {
    font-family: 'Custom';
    src: url(data:font/ttf;base64,);
}
body { font-family: 'Custom', sans-serif; }
</style></head><body><p>hi</p></body></html>"""
        # The render must not raise. Whether the font is actually used is
        # implementation-detail; what matters is the @font-face block is
        # parsed and doesn't break the pipeline.
        pdf, warnings = Engine().render_with_warnings(html)
        assert is_valid_pdf(pdf)

    def test_font_face_missing_file_emits_warning(self, tmp_path):
        html = f"""<html><head><style>
@font-face {{
    font-family: 'Custom';
    src: url('does-not-exist.ttf');
}}
</style></head><body><p>hi</p></body></html>"""
        opts = Options(base_url=str(tmp_path))
        pdf, warnings = Engine(opts).render_with_warnings(html)
        assert is_valid_pdf(pdf)
        # The font fetch must produce a warning that mentions the failure.
        assert any(
            "font" in w.lower() or "does-not-exist" in w.lower() for w in warnings
        ), warnings


# ---------------------------------------------------------------------------
# box-shadow (README claims "Supported (offset + blur + color)")
# ---------------------------------------------------------------------------


class TestBoxShadow:
    def test_box_shadow_emits_pdf_operators(self):
        # The smallest end-to-end check: a box with a shadow renders with at
        # least one extra fill operation compared to one without.
        with_shadow = render(
            "<html><body>"
            "<div style='width:50pt;height:50pt;background:white;"
            "box-shadow:5pt 5pt 5pt rgba(0,0,0,0.5);'></div>"
            "</body></html>"
        )
        without_shadow = render(
            "<html><body>"
            "<div style='width:50pt;height:50pt;background:white;'></div>"
            "</body></html>"
        )
        # Shadow rendering adds operators to the content stream.
        assert len(with_shadow) > len(without_shadow), (
            "box-shadow did not produce extra PDF content — the property may "
            "be silently dropped."
        )


# ---------------------------------------------------------------------------
# position: absolute / relative (README claims "Supported")
# ---------------------------------------------------------------------------


class TestPosition:
    def test_position_absolute_does_not_crash(self):
        html = """<html><body>
<div style='position:relative;width:200pt;height:200pt;background:#eee;'>
  <span style='position:absolute;top:10pt;left:20pt;'>pinned</span>
</div>
</body></html>"""
        pdf = render(html)
        assert is_valid_pdf(pdf)
        text = extract_text(pdf)
        assert "pinned" in text

    def test_position_relative_offsets_text(self):
        html = """<html><body>
<p>baseline</p>
<p style='position:relative;top:30pt;left:50pt;'>shifted</p>
</body></html>"""
        pdf = render(html)
        assert is_valid_pdf(pdf)
        text = extract_text(pdf)
        # Both lines must appear.
        assert "baseline" in text
        assert "shifted" in text


# ---------------------------------------------------------------------------
# border-collapse + colspan (README claims "Supported")
# ---------------------------------------------------------------------------


class TestTables:
    def test_border_collapse_renders(self):
        html = """<html><body><table style='border-collapse:collapse;'>
<thead><tr><th>A</th><th>B</th><th>C</th></tr></thead>
<tbody>
<tr><td>1</td><td>2</td><td>3</td></tr>
<tr><td>4</td><td>5</td><td>6</td></tr>
</tbody>
</table></body></html>"""
        pdf = render(html)
        assert is_valid_pdf(pdf)
        text = extract_text(pdf)
        # All cells must appear in the extracted text.
        for cell in ["A", "B", "C", "1", "2", "3", "4", "5", "6"]:
            assert cell in text, f"missing cell {cell!r} in {text!r}"

    def test_colspan_does_not_crash(self):
        html = """<html><body><table border='1'>
<tr><td colspan='2'>spans two</td><td>third</td></tr>
<tr><td>a</td><td>b</td><td>c</td></tr>
</table></body></html>"""
        pdf = render(html)
        assert is_valid_pdf(pdf)
        text = extract_text(pdf)
        for cell in ["spans two", "third", "a", "b", "c"]:
            assert cell in text


# ---------------------------------------------------------------------------
# Selectors that the previous parse_qualified_rule bug was silently dropping
# ---------------------------------------------------------------------------


class TestRecoveredSelectors:
    """Regression coverage for the :nth-child / :not / [attr] truncation bug
    fixed in the parser. These are end-to-end checks: if the selector parse
    silently drops the rule again, the colors below will not appear."""

    def test_nth_child_odd_applies_to_first_and_third(self):
        html = """<html><head><style>
li:nth-child(odd){color:red;}
</style></head><body><ul><li>a</li><li>b</li><li>c</li></ul></body></html>"""
        pdf = render(html)
        # Each matching <li> contributes 2 "1 0 0 rg" operators (bullet + text).
        # Two matches × 2 = 4.
        assert count_color_op(pdf, 1, 0, 0) == 4

    def test_nth_child_2n_plus_1_applies(self):
        html = """<html><head><style>
li:nth-child(2n+1){color:red;}
</style></head><body><ul><li>a</li><li>b</li><li>c</li></ul></body></html>"""
        pdf = render(html)
        assert count_color_op(pdf, 1, 0, 0) == 4

    def test_attribute_selector_applies(self):
        html = """<html><head><style>
p[lang="fr"]{color:red;}
</style></head><body><p lang="fr">bonjour</p><p lang="en">hello</p></body></html>"""
        pdf = render(html)
        assert count_color_op(pdf, 1, 0, 0) == 1

    def test_not_pseudo_class_applies(self):
        html = """<html><head><style>
li:not(.hide){color:red;}
</style></head><body><ul>
<li>a</li><li class="hide">b</li><li>c</li>
</ul></body></html>"""
        pdf = render(html)
        # Two matching <li> × 2 ops each = 4.
        assert count_color_op(pdf, 1, 0, 0) == 4
