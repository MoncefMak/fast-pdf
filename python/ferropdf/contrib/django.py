from django.http import HttpResponse
from django.template.loader import render_to_string
import ferropdf

class PdfResponse(HttpResponse):
    """
    HttpResponse PDF depuis un template Django.

    Usage :
        def invoice(request, pk):
            return PdfResponse("invoice.html", {"pk": pk}, request=request)
    """
    def __init__(
        self,
        template_name: str,
        context: dict,
        request=None,
        filename: str = "document.pdf",
        options=None,
        inline: bool = True,
        **kwargs,
    ):
        html     = render_to_string(template_name, context, request=request)
        base_url = request.build_absolute_uri("/") if request else None
        engine   = ferropdf.Engine(options or ferropdf.Options(base_url=base_url))
        pdf      = engine.render(html)

        super().__init__(content=pdf, content_type="application/pdf", **kwargs)
        disposition = "inline" if inline else "attachment"
        self["Content-Disposition"] = f'{disposition}; filename="{filename}"'
        self["Content-Length"]      = str(len(pdf))
