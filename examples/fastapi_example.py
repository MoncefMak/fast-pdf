"""
FastPDF FastAPI Example
=======================

Complete FastAPI application demonstrating PDF generation.

Run: uvicorn examples.fastapi_example:app --reload
"""

from fastapi import FastAPI, Query
from fastapi.responses import HTMLResponse

from fastpdf import RenderOptions
from fastpdf.contrib.fastapi import (
    PdfResponse,
    render_pdf_response,
    render_template_to_pdf_response,
    render_pdf_async,
)

app = FastAPI(title="FastPDF Demo API")


@app.get("/", response_class=HTMLResponse)
async def index():
    return """
    <html>
    <body>
        <h1>FastPDF Demo API</h1>
        <ul>
            <li><a href="/simple.pdf">Simple PDF</a></li>
            <li><a href="/styled.pdf">Styled PDF</a></li>
            <li><a href="/invoice/42">Invoice #42</a></li>
            <li><a href="/report?title=Monthly+Report">Report</a></li>
        </ul>
    </body>
    </html>
    """


@app.get("/simple.pdf")
async def simple_pdf():
    """Simplest PDF endpoint."""
    return PdfResponse(
        "<h1>Hello from FastAPI!</h1><p>Generated with FastPDF.</p>",
        filename="simple.pdf",
    )


@app.get("/styled.pdf")
async def styled_pdf():
    """PDF with custom styling."""
    html = """
    <html>
    <head><style>
        body { font-family: Helvetica; padding: 40px; }
        h1 { color: #059669; border-bottom: 2px solid #059669; }
        .stats { display: flex; gap: 20px; margin-top: 20px; }
        .stat { background: #f0fdf4; padding: 20px; border-radius: 8px; text-align: center; }
        .stat-value { font-size: 24pt; font-weight: bold; color: #059669; }
        .stat-label { color: #6b7280; font-size: 10pt; }
    </style></head>
    <body>
        <h1>Performance Dashboard</h1>
        <div class="stats">
            <div class="stat">
                <div class="stat-value">42ms</div>
                <div class="stat-label">Avg Render Time</div>
            </div>
            <div class="stat">
                <div class="stat-value">12MB</div>
                <div class="stat-label">Memory Usage</div>
            </div>
            <div class="stat">
                <div class="stat-value">1000+</div>
                <div class="stat-label">PDFs/minute</div>
            </div>
        </div>
    </body>
    </html>
    """
    options = RenderOptions(title="Performance Dashboard", author="FastPDF")
    return PdfResponse(html, options=options, filename="dashboard.pdf")


@app.get("/invoice/{invoice_id}")
async def invoice(invoice_id: int):
    """Generate an invoice PDF."""
    html = f"""
    <html>
    <head><style>
        body {{ font-family: Helvetica; }}
        h1 {{ color: #1e40af; }}
        table {{ width: 100%; border-collapse: collapse; margin-top: 20px; }}
        th {{ background: #1e40af; color: white; padding: 10px; text-align: left; }}
        td {{ padding: 8px 10px; border-bottom: 1px solid #e5e7eb; }}
    </style></head>
    <body>
        <h1>Invoice #{invoice_id:04d}</h1>
        <p>Date: 2024-12-15</p>
        <table>
            <tr><th>Item</th><th>Qty</th><th>Price</th><th>Total</th></tr>
            <tr><td>Widget A</td><td>10</td><td>$25.00</td><td>$250.00</td></tr>
            <tr><td>Widget B</td><td>5</td><td>$50.00</td><td>$250.00</td></tr>
            <tr><td>Service Fee</td><td>1</td><td>$100.00</td><td>$100.00</td></tr>
        </table>
        <p style="text-align: right; font-size: 18pt; font-weight: bold; margin-top: 20px;">
            Total: $600.00
        </p>
    </body>
    </html>
    """
    return PdfResponse(
        html,
        filename=f"invoice-{invoice_id}.pdf",
        options=RenderOptions(title=f"Invoice #{invoice_id}"),
    )


@app.get("/report")
async def report(title: str = Query(default="Report")):
    """Generate a report using async rendering."""
    html = f"<h1>{title}</h1><p>This was rendered asynchronously.</p>"
    pdf_bytes = await render_pdf_async(html, options=RenderOptions(title=title))

    from starlette.responses import Response

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'inline; filename="report.pdf"'},
    )


@app.get("/batch")
async def batch_invoices():
    """Generate multiple invoices (returns count, not PDFs)."""
    from fastpdf.contrib.fastapi import batch_render_async

    items = [
        {"html": f"<h1>Invoice #{i}</h1><p>Amount: ${i * 100}</p>"}
        for i in range(1, 6)
    ]
    results = await batch_render_async(items)
    return {"generated": len(results), "total_bytes": sum(len(r) for r in results)}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
