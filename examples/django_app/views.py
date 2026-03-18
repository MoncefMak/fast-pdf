"""
Views Django — chaque vue génère un PDF via ferropdf.
"""
from django.http import HttpResponse
from django.template.loader import render_to_string
import ferropdf


def _pdf_response(template_name: str, context: dict, filename: str = "document.pdf") -> HttpResponse:
    """Rend un template en HTML puis le convertit en PDF."""
    html = render_to_string(template_name, context)
    engine = ferropdf.Engine(ferropdf.Options(margin="15mm"))
    pdf = engine.render(html)
    response = HttpResponse(content=pdf, content_type="application/pdf")
    response["Content-Disposition"] = f'inline; filename="{filename}"'
    return response


def home(request):
    """Page d'accueil avec liens vers tous les PDFs."""
    html = """
    <html>
    <head><style>
      body { font-family: sans-serif; max-width: 640px; margin: 40px auto; color: #1f2937; }
      h1 { color: #1e40af; margin-bottom: 8px; }
      p.sub { color: #6b7280; margin-bottom: 24px; }
      ul { list-style: none; padding: 0; }
      li { padding: 10px 0; border-bottom: 1px solid #e5e7eb; }
      li:last-child { border: none; }
      a { color: #1e40af; text-decoration: none; font-weight: 500; }
      .desc { color: #6b7280; font-size: 13px; }
    </style></head>
    <body>
      <h1>ferropdf + Django</h1>
      <p class="sub">Exemples de génération PDF côté serveur, propulsé par Rust.</p>
      <ul>
        <li>
          <a href="/invoice/1/pdf/">📄 Facture #1</a>
          <div class="desc">Table avec en-tête, lignes, totaux</div>
        </li>
        <li>
          <a href="/invoice/2/pdf/">📄 Facture #2</a>
          <div class="desc">Même template, données différentes</div>
        </li>
        <li>
          <a href="/receipt/pdf/">🧾 Ticket de caisse</a>
          <div class="desc">Bordures pointillées, sous-totaux, TVA</div>
        </li>
        <li>
          <a href="/dashboard/pdf/">📈 Tableau de bord</a>
          <div class="desc">Deux tables, badges colorés, résumé</div>
        </li>
        <li>
          <a href="/letter/pdf/">✉️ Lettre formelle</a>
          <div class="desc">En-tête, adresse, corps, signature</div>
        </li>
      </ul>
    </body>
    </html>
    """
    return HttpResponse(html)


def invoice_pdf(request, invoice_id: int):
    """Facture PDF avec lignes de commande."""
    items = [
        {"desc": "Développement Rust", "qty": 10, "price": 150},
        {"desc": "Intégration Python", "qty": 5, "price": 120},
        {"desc": "Tests et QA", "qty": 3, "price": 100},
    ]
    for item in items:
        item["line_total"] = item["qty"] * item["price"]
    total = sum(i["line_total"] for i in items)
    return _pdf_response("invoice.html", {
        "invoice_id": invoice_id,
        "items": items,
        "total": total,
    }, filename=f"facture-{invoice_id}.pdf")


def receipt_pdf(request):
    """Ticket de caisse avec TVA."""
    items = [
        {"name": "Croissant beurre", "qty": 3, "price": 1.20},
        {"name": "Café allongé", "qty": 2, "price": 2.50},
        {"name": "Jus d'orange pressé", "qty": 1, "price": 3.80},
        {"name": "Pain au chocolat", "qty": 2, "price": 1.40},
        {"name": "Tartine confiture", "qty": 1, "price": 2.90},
    ]
    for item in items:
        item["line_total"] = item["qty"] * item["price"]
    subtotal = sum(i["line_total"] for i in items)
    tax = subtotal * 0.20
    return _pdf_response("receipt.html", {
        "shop_name": "Boulangerie du Code",
        "shop_address": "12 rue des Octets, 75011 Paris",
        "receipt_id": "2026-03-0042",
        "date": "17/03/2026 — 08:34",
        "cashier": "Marie L.",
        "payment_method": "Carte bancaire",
        "items": items,
        "subtotal": f"{subtotal:.2f}",
        "tax": f"{tax:.2f}",
        "total": f"{subtotal + tax:.2f}",
    }, filename="ticket.pdf")


def dashboard_pdf(request):
    """Tableau de bord commercial."""
    categories = [
        {"name": "Logiciels", "revenue": 245000, "margin": 68.2, "trend": "up"},
        {"name": "Services", "revenue": 182000, "margin": 42.5, "trend": "up"},
        {"name": "Formation", "revenue": 67000, "margin": 55.1, "trend": "stable"},
        {"name": "Support", "revenue": 43000, "margin": 31.8, "trend": "down"},
    ]
    for c in categories:
        c["revenue_fmt"] = f"{c['revenue']:,}"
        c["margin_fmt"] = f"{c['margin']:.1f}"
    top_products = [
        {"name": "FerroSuite Enterprise", "units": 342, "revenue": 171000},
        {"name": "FerroAPI Pro", "units": 580, "revenue": 58000},
        {"name": "Consulting On-Site", "units": 15, "revenue": 45000},
        {"name": "Formation Rust Avancé", "units": 28, "revenue": 33600},
        {"name": "Support Premium", "units": 120, "revenue": 24000},
    ]
    for p in top_products:
        p["revenue_fmt"] = f"{p['revenue']:,}"
    total_revenue = sum(c["revenue"] for c in categories)
    avg_margin = sum(c["margin"] for c in categories) / len(categories)
    return _pdf_response("dashboard.html", {
        "title": "Tableau de Bord — T1 2026",
        "period": "T1 2026",
        "date": "17/03/2026",
        "categories": categories,
        "top_products": top_products,
        "total_revenue": f"{total_revenue:,}",
        "avg_margin": f"{avg_margin:.1f}",
        "transactions": 1085,
    }, filename="dashboard.pdf")


def letter_pdf(request):
    """Lettre formelle d'affaires."""
    return _pdf_response("letter.html", {
        "company_name": "FerroTech SARL",
        "company_address": "42 rue du Code, 75001 Paris — contact@ferrotech.dev",
        "recipient_name": "M. Jean Dupont",
        "recipient_company": "Acme Corp",
        "recipient_address": "123 Business Avenue, 69000 Lyon",
        "city": "Paris",
        "date": "17 mars 2026",
        "sender_name": "Sophie Martin",
        "sender_title": "Directrice Technique — FerroTech SARL",
        "subject": "Proposition de partenariat technique",
        "paragraphs": [
            "Suite à notre entretien du 10 mars dernier, nous avons le plaisir de vous "
            "transmettre notre proposition de partenariat pour l'intégration de notre moteur "
            "de rendu PDF haute performance dans votre plateforme documentaire.",
            "Notre solution, ferropdf, repose sur un pipeline Rust optimisé capable de "
            "convertir du HTML/CSS en PDF en quelques millisecondes. Compatible avec Python "
            "via PyO3, elle s'intègre nativement avec FastAPI et Django.",
            "Nous proposons un accompagnement technique complet incluant la formation de "
            "vos équipes, l'intégration dans votre CI/CD, et un support prioritaire pendant "
            "les six premiers mois.",
            "Nous restons à votre disposition pour tout complément d'information et espérons "
            "que cette collaboration sera le début d'un partenariat fructueux.",
        ],
    }, filename="lettre.pdf")
