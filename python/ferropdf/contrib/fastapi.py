import asyncio
from fastapi.responses import Response
import ferropdf

async def pdf_response(
    html: str,
    filename: str = "document.pdf",
    options=None,
    inline: bool = True,
) -> Response:
    """
    Retourne une Response FastAPI avec le PDF.
    Non-bloquant : le GIL est libéré côté Rust.

    Usage :
        @router.get("/invoice/{id}/pdf")
        async def invoice_pdf(id: int, db: Session = Depends(get_db)):
            html = templates.get_template("invoice.html").render(...)
            return await pdf_response(html, filename=f"invoice-{id}.pdf")
    """
    engine = ferropdf.Engine(options or ferropdf.Options())
    loop   = asyncio.get_event_loop()
    pdf    = await loop.run_in_executor(None, engine.render, html)
    d      = "inline" if inline else "attachment"
    return Response(
        content=pdf,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'{d}; filename="{filename}"',
            "Content-Length":      str(len(pdf)),
        },
    )
