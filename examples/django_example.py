"""
FastPDF Django Example
======================

Example Django views for PDF generation.
"""

# --- urls.py ---
# from django.urls import path
# from . import views
#
# urlpatterns = [
#     path("invoice/<int:pk>/", views.invoice_pdf, name="invoice-pdf"),
#     path("invoice/<int:pk>/preview/", views.invoice_preview, name="invoice-preview"),
#     path("reports/monthly/", views.MonthlyReportView.as_view(), name="monthly-report"),
# ]


# --- views.py ---

def invoice_pdf(request, pk):
    """Function-based view returning a PDF download."""
    from django.shortcuts import get_object_or_404
    from fastpdf.contrib.django import render_to_pdf_response

    # invoice = get_object_or_404(Invoice, pk=pk)
    # Simulated context:
    context = {
        "invoice_number": f"INV-{pk:04d}",
        "customer_name": "Acme Corp",
        "items": [
            {"name": "Consulting", "hours": 10, "rate": 150, "total": 1500},
            {"name": "Development", "hours": 40, "rate": 125, "total": 5000},
        ],
        "total": 6500,
    }

    return render_to_pdf_response(
        request,
        "invoices/invoice.html",
        context,
        filename=f"invoice-{pk}.pdf",
    )


def invoice_preview(request, pk):
    """Show PDF inline in the browser."""
    from fastpdf.contrib.django import render_to_pdf_response

    context = {"invoice_number": f"INV-{pk:04d}", "preview": True}
    return render_to_pdf_response(
        request,
        "invoices/invoice.html",
        context,
        filename=f"invoice-{pk}.pdf",
        inline=True,  # Display in browser
    )


# --- Class-based view ---

# from django.views.generic import DetailView
# from fastpdf.contrib.django import PdfView
#
# class MonthlyReportView(PdfView):
#     """Class-based view that renders a monthly report as PDF."""
#     template_name = "reports/monthly.html"
#     pdf_filename = "monthly-report.pdf"
#
#     def get_context_data(self, **kwargs):
#         context = super().get_context_data(**kwargs)
#         context["month"] = "December 2024"
#         context["metrics"] = self.get_metrics()
#         return context
#
#     def get_metrics(self):
#         return {"revenue": 50000, "users": 1234, "growth": 12.5}
