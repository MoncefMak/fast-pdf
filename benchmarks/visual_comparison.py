#!/usr/bin/env python3
"""
Visual Comparison: FerroPDF vs WeasyPrint
=========================================

Renders the same HTML/CSS templates with both engines, saves the output
PDFs side by side, and logs size/timing differences.

Usage::

    pip install ferropdf weasyprint
    python benchmarks/visual_comparison.py

Output directory: benchmarks/visual_output/
"""

from __future__ import annotations

import os
import sys
import time
from pathlib import Path

OUTPUT_DIR = Path(__file__).parent / "visual_output"

# ---------------------------------------------------------------------------
# Templates
# ---------------------------------------------------------------------------

TEMPLATES = {
    "invoice": """
    <html><head><style>
    body { font-family: Helvetica, Arial, sans-serif; margin: 0; padding: 30px; color: #333; }
    h1 { color: #1a56db; font-size: 28pt; margin-bottom: 5px; }
    .subtitle { color: #6b7280; font-size: 12pt; margin-bottom: 30px; }
    .flex-header { display: flex; justify-content: space-between; align-items: flex-start; }
    .info { font-size: 10pt; line-height: 1.6; }
    table { width: 100%; border-collapse: collapse; margin: 20px 0; }
    th { background: #1a56db; color: white; padding: 10px 12px; text-align: left; font-size: 10pt; }
    td { border-bottom: 1px solid #e5e7eb; padding: 10px 12px; font-size: 10pt; }
    tr:nth-child(even) { background: #f9fafb; }
    .total-row td { font-weight: bold; border-top: 2px solid #1a56db; }
    .footer { text-align: center; color: #9ca3af; font-size: 9pt; margin-top: 40px; }
    </style></head><body>
    <div class="flex-header">
        <div>
            <h1>INVOICE</h1>
            <div class="subtitle">#INV-2024-0042</div>
        </div>
        <div class="info" style="text-align:right;">
            <strong>ACME Corporation</strong><br>
            123 Business Street<br>
            New York, NY 10001<br>
            billing@acme.com
        </div>
    </div>
    <div class="info" style="margin-bottom:20px;">
        <strong>Bill To:</strong> Client Industries Ltd.<br>
        456 Client Avenue, San Francisco, CA 94102
    </div>
    <table>
        <thead><tr><th>Description</th><th>Qty</th><th>Unit Price</th><th>Amount</th></tr></thead>
        <tbody>
            <tr><td>Web Development Services</td><td>40h</td><td>$150.00</td><td>$6,000.00</td></tr>
            <tr><td>UI/UX Design</td><td>20h</td><td>$120.00</td><td>$2,400.00</td></tr>
            <tr><td>Server Hosting (Annual)</td><td>1</td><td>$1,200.00</td><td>$1,200.00</td></tr>
            <tr><td>SSL Certificate</td><td>1</td><td>$99.00</td><td>$99.00</td></tr>
            <tr><td>Maintenance Package</td><td>12 mo</td><td>$200.00</td><td>$2,400.00</td></tr>
            <tr class="total-row"><td colspan="3">Total</td><td>$12,099.00</td></tr>
        </tbody>
    </table>
    <div class="footer">Thank you for your business! &mdash; Payment due within 30 days.</div>
    </body></html>
    """,

    "arabic_rtl": """
    <html><head><style>
    body { direction: rtl; text-align: right; font-family: sans-serif; padding: 30px; color: #333; }
    h1 { color: #1a56db; font-size: 24pt; border-bottom: 2px solid #1a56db; padding-bottom: 10px; }
    p { font-size: 13pt; line-height: 2; }
    .highlight { background: #fef3c7; padding: 15px; border-radius: 8px; border: 1px solid #f59e0b; }
    </style></head><body>
    <h1>فاتورة رقم ٢٠٢٤-٠٠٤٢</h1>
    <p>هذا نص تجريبي باللغة العربية لاختبار دعم الكتابة من اليمين إلى اليسار في محرّك FerroPDF.</p>
    <div class="highlight">
        <p><strong>المبلغ الإجمالي:</strong> ١٢,٠٩٩.٠٠ درهم</p>
        <p><strong>تاريخ الاستحقاق:</strong> ١٥ مارس ٢٠٢٤</p>
    </div>
    <p>شكراً لتعاملكم معنا.</p>
    </body></html>
    """,

    "page_break": """
    <html><head><style>
    body { font-family: sans-serif; padding: 30px; }
    .page { page-break-after: always; }
    .page:last-child { page-break-after: auto; }
    h2 { color: #1a56db; border-bottom: 1px solid #ccc; padding-bottom: 5px; }
    p { line-height: 1.6; }
    </style></head><body>
    """ + "".join(
        f'<div class="page"><h2>Chapter {i}</h2>'
        f'<p>{"Lorem ipsum dolor sit amet, consectetur adipiscing elit. " * 15}</p></div>'
        for i in range(1, 5)
    ) + "</body></html>",

    "tailwind": """
    <html><body>
    <div class="w-[210mm] min-h-[297mm] p-8 bg-white">
        <div class="flex justify-between items-start mb-8">
            <div>
                <h1 class="text-3xl font-bold text-blue-600">Invoice</h1>
                <p class="text-gray-500 text-sm">#INV-2024-001</p>
            </div>
            <div class="text-right text-sm text-gray-600">
                <p class="font-semibold">ACME Corp</p>
                <p>123 Business St</p>
            </div>
        </div>
        <table class="w-full border-collapse mb-6">
            <thead>
                <tr class="bg-blue-600 text-white">
                    <th class="p-3 text-left text-sm">Item</th>
                    <th class="p-3 text-right text-sm">Amount</th>
                </tr>
            </thead>
            <tbody>
                <tr class="border-b border-gray-200">
                    <td class="p-3 text-sm">Development</td>
                    <td class="p-3 text-right text-sm">$6,000</td>
                </tr>
                <tr class="border-b border-gray-200 bg-gray-50">
                    <td class="p-3 text-sm">Design</td>
                    <td class="p-3 text-right text-sm">$2,400</td>
                </tr>
            </tbody>
        </table>
        <div class="text-right">
            <span class="text-xl font-bold text-green-600">Total: $8,400</span>
        </div>
    </div>
    </body></html>
    """,

    "gradient_hero": """
    <html><head><style>
    body { margin: 0; font-family: sans-serif; }
    .hero {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white; padding: 60px 40px; text-align: center;
    }
    .hero h1 { font-size: 36pt; margin: 0 0 10px 0; }
    .hero p { font-size: 14pt; opacity: 0.9; }
    .content { padding: 40px; }
    .card { border: 1px solid #e5e7eb; border-radius: 8px; padding: 20px; margin: 10px 0; }
    </style></head><body>
    <div class="hero">
        <h1>Annual Report 2024</h1>
        <p>Comprehensive financial and operational overview</p>
    </div>
    <div class="content">
        <div class="card"><h3>Revenue</h3><p>$12.5M (+18% YoY)</p></div>
        <div class="card"><h3>Customers</h3><p>2,847 (+32% YoY)</p></div>
    </div>
    </body></html>
    """,

    "flexbox_grid": """
    <html><head><style>
    body { font-family: sans-serif; padding: 20px; margin: 0; }
    .grid { display: flex; flex-wrap: wrap; gap: 15px; }
    .card {
        flex: 1 1 calc(33.333% - 15px);
        min-width: 150px;
        border: 1px solid #ddd;
        border-radius: 8px;
        padding: 20px;
        text-align: center;
        background: #fafafa;
    }
    .card h3 { margin: 0 0 5px 0; color: #1a56db; }
    .card p { margin: 0; color: #6b7280; font-size: 10pt; }
    </style></head><body>
    <h1 style="text-align:center; color:#333;">Dashboard</h1>
    <div class="grid">
    """ + "".join(
        f'<div class="card"><h3>Metric {i}</h3><p>{i * 123} units</p></div>'
        for i in range(1, 10)
    ) + """
    </div>
    </body></html>
    """,
}


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------

def render_ferropdf(name: str, html: str, output_dir: Path) -> dict:
    """Render with FerroPDF and return timing/size info."""
    from fastpdf import render_pdf, RenderOptions

    tailwind = name == "tailwind"
    opts = RenderOptions(page_size="A4", tailwind=tailwind)

    start = time.perf_counter()
    pdf_bytes = render_pdf(html, options=opts)
    elapsed = time.perf_counter() - start

    path = output_dir / f"{name}_ferropdf.pdf"
    path.write_bytes(pdf_bytes)

    return {"engine": "ferropdf", "name": name, "time_ms": elapsed * 1000, "size_kb": len(pdf_bytes) / 1024, "path": str(path)}


def render_weasyprint(name: str, html: str, output_dir: Path) -> dict:
    """Render with WeasyPrint and return timing/size info."""
    try:
        from weasyprint import HTML
    except ImportError:
        return {"engine": "weasyprint", "name": name, "time_ms": None, "size_kb": None, "path": None, "error": "weasyprint not installed"}

    start = time.perf_counter()
    pdf_bytes = HTML(string=html).write_pdf()
    elapsed = time.perf_counter() - start

    path = output_dir / f"{name}_weasyprint.pdf"
    path.write_bytes(pdf_bytes)

    return {"engine": "weasyprint", "name": name, "time_ms": elapsed * 1000, "size_kb": len(pdf_bytes) / 1024, "path": str(path)}


def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    results = []
    for name, html in TEMPLATES.items():
        print(f"\n{'='*60}")
        print(f"Template: {name}")
        print(f"{'='*60}")

        ferro = render_ferropdf(name, html, OUTPUT_DIR)
        weasy = render_weasyprint(name, html, OUTPUT_DIR)
        results.append((ferro, weasy))

        # Log results
        print(f"  FerroPDF:   {ferro['time_ms']:.2f} ms  |  {ferro['size_kb']:.1f} KB  |  {ferro['path']}")
        if weasy.get("error"):
            print(f"  WeasyPrint: {weasy['error']}")
        else:
            print(f"  WeasyPrint: {weasy['time_ms']:.2f} ms  |  {weasy['size_kb']:.1f} KB  |  {weasy['path']}")
            speedup = weasy["time_ms"] / ferro["time_ms"] if ferro["time_ms"] > 0 else float("inf")
            print(f"  Speedup:    {speedup:.1f}x faster")

    # Summary table
    print(f"\n\n{'='*80}")
    print("SUMMARY")
    print(f"{'='*80}")
    print(f"{'Template':<20} {'FerroPDF (ms)':>15} {'WeasyPrint (ms)':>17} {'Speedup':>10} {'Size Δ':>10}")
    print("-" * 80)
    for ferro, weasy in results:
        name = ferro["name"]
        f_time = f"{ferro['time_ms']:.2f}"
        if weasy.get("error"):
            w_time = "N/A"
            speedup = "N/A"
            size_delta = "N/A"
        else:
            w_time = f"{weasy['time_ms']:.2f}"
            speedup = f"{weasy['time_ms'] / ferro['time_ms']:.1f}x" if ferro["time_ms"] > 0 else "∞"
            size_delta = f"{ferro['size_kb'] - weasy['size_kb']:+.1f} KB"
        print(f"{name:<20} {f_time:>15} {w_time:>17} {speedup:>10} {size_delta:>10}")

    print(f"\nOutput files in: {OUTPUT_DIR.resolve()}")


if __name__ == "__main__":
    main()
