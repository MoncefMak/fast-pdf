"""
Exemple FastAPI — serveur PDF à la volée.

Lancer :
    pip install fastapi uvicorn jinja2
    cd examples/fastapi_app
    uvicorn main:app --reload

Endpoints :
    GET /                     → page d'accueil
    GET /invoice/1/pdf        → PDF facture
    GET /report/pdf?title=... → PDF rapport custom
"""
from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from jinja2 import Environment, FileSystemLoader
import ferropdf

app = FastAPI(title="ferropdf FastAPI Example")

templates = Environment(loader=FileSystemLoader(Path(__file__).parent / "templates"))


@app.get("/", response_class=HTMLResponse)
async def home():
    return """
    <html>
    <body style="font-family: sans-serif; max-width: 600px; margin: 40px auto;">
        <h1>ferropdf + FastAPI</h1>
        <ul>
            <li><a href="/invoice/1/pdf">📄 Facture #1 (PDF)</a></li>
            <li><a href="/invoice/2/pdf">📄 Facture #2 (PDF)</a></li>
            <li><a href="/report/pdf?title=Rapport%20Mensuel">📄 Rapport custom (PDF)</a></li>
        </ul>
    </body>
    </html>
    """


@app.get("/invoice/{invoice_id}/pdf")
async def invoice_pdf(invoice_id: int):
    """Génère une facture PDF à la volée."""
    import asyncio

    items = [
        {"desc": "Développement Rust", "qty": 10, "price": 150},
        {"desc": "Intégration Python", "qty": 5, "price": 120},
        {"desc": "Tests et QA", "qty": 3, "price": 100},
    ]

    template = templates.get_template("invoice.html")
    html = template.render(
        invoice_id=invoice_id,
        items=items,
        total=sum(i["qty"] * i["price"] for i in items),
    )

    # Render PDF — le GIL est libéré côté Rust
    engine = ferropdf.Engine(ferropdf.Options(margin="15mm"))
    loop = asyncio.get_event_loop()
    pdf_bytes = await loop.run_in_executor(None, engine.render, html)

    from fastapi.responses import Response
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'inline; filename="facture-{invoice_id}.pdf"',
        },
    )


@app.get("/report/pdf")
async def report_pdf(title: str = "Rapport"):
    """Génère un rapport PDF avec titre custom."""
    import asyncio

    template = templates.get_template("report.html")
    html = template.render(title=title)

    engine = ferropdf.Engine()
    loop = asyncio.get_event_loop()
    pdf_bytes = await loop.run_in_executor(None, engine.render, html)

    from fastapi.responses import Response
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'inline; filename="report.pdf"',
        },
    )
