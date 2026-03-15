"""
FastPDF Invoice Template Example
=================================

Demonstrates generating a professional invoice PDF using Jinja2 templates.
"""

from fastpdf import PdfEngine, RenderOptions


def generate_invoice():
    engine = PdfEngine(
        template_dir="examples/templates/",
        default_options=RenderOptions(
            page_size="A4",
            margin_top=15,
            margin_right=15,
            margin_bottom=20,
            margin_left=15,
            title="Invoice",
        ),
    )

    context = {
        "invoice_number": "INV-2024-0042",
        "date": "2024-12-15",
        "due_date": "2025-01-14",
        "company": {
            "name": "Acme Corp",
            "address": "123 Business Ave, Suite 100",
            "city": "San Francisco, CA 94105",
            "email": "billing@acme.com",
        },
        "customer": {
            "name": "John Smith",
            "company": "Smith Enterprises",
            "address": "456 Client St",
            "city": "New York, NY 10001",
            "email": "john@smith-ent.com",
        },
        "items": [
            {"description": "Web Development - Phase 1", "quantity": 40, "rate": 150.00},
            {"description": "UI/UX Design", "quantity": 20, "rate": 125.00},
            {"description": "API Integration", "quantity": 15, "rate": 175.00},
            {"description": "Testing & QA", "quantity": 10, "rate": 100.00},
            {"description": "Project Management", "quantity": 8, "rate": 130.00},
        ],
        "tax_rate": 0.085,
        "notes": "Payment due within 30 days. Late payments subject to 1.5% monthly interest.",
    }

    # Calculate totals
    for item in context["items"]:
        item["total"] = item["quantity"] * item["rate"]
    context["subtotal"] = sum(item["total"] for item in context["items"])
    context["tax"] = context["subtotal"] * context["tax_rate"]
    context["total"] = context["subtotal"] + context["tax"]

    doc = engine.render_template("invoice.html", context=context)
    doc.save("output/invoice.pdf")
    print(f"✓ Invoice generated: {doc}")


if __name__ == "__main__":
    import os
    os.makedirs("output", exist_ok=True)
    generate_invoice()
