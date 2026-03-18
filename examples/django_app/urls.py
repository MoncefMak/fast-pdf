from django.urls import path
from views import home, invoice_pdf, receipt_pdf, dashboard_pdf, letter_pdf

urlpatterns = [
    path("", home, name="home"),
    path("invoice/<int:invoice_id>/pdf/", invoice_pdf, name="invoice_pdf"),
    path("receipt/pdf/", receipt_pdf, name="receipt_pdf"),
    path("dashboard/pdf/", dashboard_pdf, name="dashboard_pdf"),
    path("letter/pdf/", letter_pdf, name="letter_pdf"),
]
