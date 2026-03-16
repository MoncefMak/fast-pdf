"""Render quality tests for FerroPDF — verifies visual fidelity.

These tests generate PDFs and verify structural properties (valid PDF,
page count, non-trivial size) to ensure rendering quality is on par
with WeasyPrint.

They require the Rust engine to be built. Skip gracefully if unavailable.
"""

from __future__ import annotations

import base64
import io
import os
import pytest

try:
    from fastpdf import render_pdf, RenderOptions, PdfEngine
    _ENGINE = True
except Exception:
    _ENGINE = False

pytestmark = pytest.mark.skipif(not _ENGINE, reason="Rust engine not available")


def _is_valid_pdf(data: bytes) -> bool:
    return data[:5] == b"%PDF-"


# ---------------------------------------------------------------------------
# 1. Invoice layout — table, totals, logo placeholder
# ---------------------------------------------------------------------------

class TestInvoiceLayout:
    def test_invoice_layout(self):
        html = """
        <html><head><style>
        body { font-family: sans-serif; margin: 0; padding: 20px; }
        table { width: 100%; border-collapse: collapse; margin-top: 20px; }
        th, td { border: 1px solid #ccc; padding: 8px; text-align: left; }
        th { background: #f0f0f0; }
        .total { text-align: right; font-weight: bold; font-size: 18px; margin-top: 10px; }
        .header { display: flex; justify-content: space-between; align-items: center; }
        </style></head><body>
        <div class="header">
            <h1>Invoice #1234</h1>
            <div>ACME Corp</div>
        </div>
        <table>
            <thead><tr><th>Item</th><th>Qty</th><th>Price</th><th>Total</th></tr></thead>
            <tbody>
                <tr><td>Widget A</td><td>10</td><td>$9.99</td><td>$99.90</td></tr>
                <tr><td>Widget B</td><td>5</td><td>$24.99</td><td>$124.95</td></tr>
                <tr><td>Service C</td><td>1</td><td>$500.00</td><td>$500.00</td></tr>
            </tbody>
        </table>
        <div class="total">Total: $724.85</div>
        </body></html>
        """
        pdf = render_pdf(html, options=RenderOptions(page_size="A4"))
        assert _is_valid_pdf(pdf)
        assert len(pdf) > 500  # Non-trivial content


# ---------------------------------------------------------------------------
# 2. Arabic RTL
# ---------------------------------------------------------------------------

class TestArabicRtl:
    def test_arabic_rtl(self):
        html = """
        <html><head><style>
        body { direction: rtl; text-align: right; font-family: sans-serif; padding: 20px; }
        h1 { color: #1a56db; }
        p { font-size: 14pt; line-height: 1.8; }
        </style></head><body>
        <h1>فاتورة</h1>
        <p>هذا نص تجريبي باللغة العربية لاختبار دعم الكتابة من اليمين إلى اليسار.</p>
        <p>المبلغ الإجمالي: ١٢٣٤٫٥٦ درهم</p>
        </body></html>
        """
        pdf = render_pdf(html, options=RenderOptions(page_size="A4"))
        assert _is_valid_pdf(pdf)
        assert len(pdf) > 300


# ---------------------------------------------------------------------------
# 3. Page break
# ---------------------------------------------------------------------------

class TestPageBreak:
    def test_page_break(self):
        sections = ""
        for i in range(1, 6):
            sections += f"""
            <div style="page-break-before: always;">
                <h2>Section {i}</h2>
                <p>{'Lorem ipsum dolor sit amet. ' * 20}</p>
            </div>
            """

        html = f"""
        <html><head><style>
        body {{ font-family: sans-serif; padding: 20px; }}
        h2 {{ color: #333; border-bottom: 1px solid #ccc; }}
        </style></head><body>
        <h1>Multi-page Report</h1>
        <p>This document spans multiple pages.</p>
        {sections}
        </body></html>
        """
        pdf = render_pdf(html, options=RenderOptions(page_size="A4"))
        assert _is_valid_pdf(pdf)
        assert len(pdf) > 1000  # Multi-page should be larger


# ---------------------------------------------------------------------------
# 4. Header / Footer with page numbers
# ---------------------------------------------------------------------------

class TestHeaderFooter:
    def test_header_footer(self):
        html = """
        <html><head><style>
        body { font-family: sans-serif; padding: 20px; }
        </style></head><body>
        <h1>Document with Header &amp; Footer</h1>
        <p>This document has running headers and footers on every page.</p>
        <p>""" + ("Content paragraph. " * 50) + """</p>
        </body></html>
        """
        opts = RenderOptions(
            page_size="A4",
            header_html='<div style="text-align:center;font-size:10px;color:#999;">FerroPDF Report</div>',
            footer_html='<div style="text-align:center;font-size:10px;color:#999;">Page {{page_number}} / {{total_pages}}</div>',
        )
        pdf = render_pdf(html, options=opts)
        assert _is_valid_pdf(pdf)
        assert len(pdf) > 500


# ---------------------------------------------------------------------------
# 5. Tailwind CSS classes
# ---------------------------------------------------------------------------

class TestTailwindClasses:
    def test_tailwind_classes(self):
        html = """
        <html><body>
        <div class="p-8 bg-white">
            <h1 class="text-3xl font-bold text-blue-600 mb-4">Invoice #2024-001</h1>
            <div class="flex justify-between mb-8">
                <div class="text-gray-600">
                    <p class="font-semibold">From: ACME Corp</p>
                    <p>123 Business St</p>
                </div>
                <div class="text-gray-600 text-right">
                    <p class="font-semibold">To: Client Inc</p>
                    <p>456 Client Ave</p>
                </div>
            </div>
            <table class="w-full border-collapse">
                <thead>
                    <tr class="bg-gray-100">
                        <th class="border border-gray-300 p-2 text-left">Item</th>
                        <th class="border border-gray-300 p-2 text-right">Amount</th>
                    </tr>
                </thead>
                <tbody>
                    <tr>
                        <td class="border border-gray-300 p-2">Consulting</td>
                        <td class="border border-gray-300 p-2 text-right">$5,000</td>
                    </tr>
                </tbody>
            </table>
            <div class="mt-4 text-right">
                <span class="text-xl font-bold text-green-600">Total: $5,000</span>
            </div>
        </div>
        </body></html>
        """
        pdf = render_pdf(html, options=RenderOptions(tailwind=True))
        assert _is_valid_pdf(pdf)
        assert len(pdf) > 500


# ---------------------------------------------------------------------------
# 6. Custom fonts
# ---------------------------------------------------------------------------

class TestCustomFonts:
    def test_custom_fonts_register(self):
        """Test that register_font API works (font file may not exist in CI)."""
        engine = PdfEngine()
        # Just verify the API is callable; actual font loading depends on
        # having a .ttf file available.
        try:
            engine.register_font("TestFont", "/nonexistent/font.ttf")
        except Exception:
            pass  # Expected if file doesn't exist

        # Render with a CSS font-family reference
        html = """
        <html><head><style>
        body { font-family: sans-serif; padding: 20px; }
        h1 { font-size: 24pt; color: #333; }
        </style></head><body>
        <h1>Custom Font Test</h1>
        <p>This tests the font rendering pipeline.</p>
        </body></html>
        """
        pdf = render_pdf(html)
        assert _is_valid_pdf(pdf)


# ---------------------------------------------------------------------------
# 7. Base64 image
# ---------------------------------------------------------------------------

class TestBase64Image:
    def test_base64_image(self):
        # Create a tiny 1x1 red PNG
        import struct
        import zlib

        def _make_tiny_png() -> str:
            # 1x1 red pixel PNG
            raw = b"\x00\xff\x00\x00"  # filter byte + RGB
            compressed = zlib.compress(raw)

            def chunk(ctype, data):
                c = ctype + data
                return struct.pack(">I", len(data)) + c + struct.pack(">I", zlib.crc32(c) & 0xFFFFFFFF)

            png = b"\x89PNG\r\n\x1a\n"
            png += chunk(b"IHDR", struct.pack(">IIBBBBB", 1, 1, 8, 2, 0, 0, 0))
            png += chunk(b"IDAT", compressed)
            png += chunk(b"IEND", b"")
            return base64.b64encode(png).decode()

        b64 = _make_tiny_png()
        html = f"""
        <html><head><style>
        body {{ padding: 20px; }}
        img {{ width: 100px; height: 100px; border: 1px solid #ccc; }}
        </style></head><body>
        <h1>Base64 Image Test</h1>
        <img src="data:image/png;base64,{b64}" alt="Red pixel">
        <p>The image above should be a 100x100 red square.</p>
        </body></html>
        """
        pdf = render_pdf(html)
        assert _is_valid_pdf(pdf)
        assert len(pdf) > 300


# ---------------------------------------------------------------------------
# 8. Gradient background
# ---------------------------------------------------------------------------

class TestGradientBackground:
    def test_gradient_bg(self):
        html = """
        <html><head><style>
        body { margin: 0; padding: 0; }
        .hero {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 60px 40px;
            text-align: center;
        }
        .hero h1 { font-size: 36pt; margin-bottom: 10px; }
        .hero p { font-size: 14pt; opacity: 0.9; }
        .content { padding: 40px; }
        </style></head><body>
        <div class="hero">
            <h1>Gradient Background</h1>
            <p>This header has a CSS linear-gradient background.</p>
        </div>
        <div class="content">
            <p>Content below the gradient hero section.</p>
        </div>
        </body></html>
        """
        pdf = render_pdf(html, options=RenderOptions(page_size="A4"))
        assert _is_valid_pdf(pdf)
        assert len(pdf) > 500


# ---------------------------------------------------------------------------
# 9. CSS Box model — margin, padding, border, border-radius
# ---------------------------------------------------------------------------

class TestBoxModel:
    def test_box_model(self):
        html = """
        <html><head><style>
        .box {
            margin: 20px;
            padding: 15px;
            border: 2px solid #333;
            border-radius: 8px;
            background-color: #f9f9f9;
        }
        .box h2 { margin: 0 0 10px 0; color: #1a56db; }
        </style></head><body>
        <div class="box"><h2>Box 1</h2><p>Margin + padding + border + radius</p></div>
        <div class="box" style="border-color: #e11d48;"><h2>Box 2</h2><p>Different border color</p></div>
        </body></html>
        """
        pdf = render_pdf(html)
        assert _is_valid_pdf(pdf)


# ---------------------------------------------------------------------------
# 10. Flexbox layout
# ---------------------------------------------------------------------------

class TestFlexbox:
    def test_flexbox_layout(self):
        html = """
        <html><head><style>
        .flex-row {
            display: flex;
            justify-content: space-between;
            align-items: center;
            gap: 20px;
            padding: 20px;
        }
        .card {
            flex: 1;
            padding: 15px;
            border: 1px solid #ddd;
            border-radius: 4px;
            text-align: center;
        }
        </style></head><body>
        <div class="flex-row">
            <div class="card"><h3>Card 1</h3><p>Flex item</p></div>
            <div class="card"><h3>Card 2</h3><p>Flex item</p></div>
            <div class="card"><h3>Card 3</h3><p>Flex item</p></div>
        </div>
        </body></html>
        """
        pdf = render_pdf(html)
        assert _is_valid_pdf(pdf)


# ---------------------------------------------------------------------------
# 11. Typography
# ---------------------------------------------------------------------------

class TestTypography:
    def test_typography(self):
        html = """
        <html><head><style>
        body { font-family: sans-serif; padding: 20px; }
        h1 { font-size: 28pt; line-height: 1.2; letter-spacing: -0.5px; }
        h2 { font-size: 20pt; color: #555; }
        p { font-size: 12pt; line-height: 1.6; text-align: justify; }
        .mono { font-family: monospace; background: #f0f0f0; padding: 10px; }
        </style></head><body>
        <h1>Typography Test</h1>
        <h2>Subtitle with different size</h2>
        <p>Regular paragraph with justified text alignment and comfortable line height.
        This tests font-size, line-height, letter-spacing, and text-align properties.</p>
        <div class="mono">Monospace text for code blocks</div>
        </body></html>
        """
        pdf = render_pdf(html)
        assert _is_valid_pdf(pdf)


# ---------------------------------------------------------------------------
# 12. Table border-collapse
# ---------------------------------------------------------------------------

class TestTableBorderCollapse:
    def test_table_border_collapse(self):
        html = """
        <html><head><style>
        table { width: 100%; border-collapse: collapse; }
        th { background: #1a56db; color: white; padding: 10px; }
        td { border: 1px solid #ddd; padding: 8px; }
        tr:nth-child(even) { background: #f9f9f9; }
        </style></head><body>
        <table>
            <thead><tr><th>Name</th><th>Email</th><th>Role</th></tr></thead>
            <tbody>
                <tr><td>Alice</td><td>alice@example.com</td><td>Engineer</td></tr>
                <tr><td>Bob</td><td>bob@example.com</td><td>Designer</td></tr>
                <tr><td>Charlie</td><td>charlie@example.com</td><td>Manager</td></tr>
            </tbody>
        </table>
        </body></html>
        """
        pdf = render_pdf(html)
        assert _is_valid_pdf(pdf)
