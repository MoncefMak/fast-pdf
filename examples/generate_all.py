#!/usr/bin/env python3
"""
FastPDF — Generate All Example PDFs
=====================================

Generates a collection of showcase PDFs in examples/output/.

Usage:
    python examples/generate_all.py
"""

import os
import sys

# Ensure the package is importable
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from pathlib import Path
from fastpdf import render_pdf, render_pdf_to_file, PdfEngine, RenderOptions

OUTPUT = Path(__file__).parent / "output"
TEMPLATES = Path(__file__).parent / "templates"


def ensure_output():
    OUTPUT.mkdir(parents=True, exist_ok=True)


# ─── 1. Simple "Hello World" ───────────────────────────────────────────────────

def example_hello_world():
    html = """
    <html>
    <head><style>
        body { font-family: Helvetica; padding: 60px; }
        h1 { font-size: 36pt; color: #1e3a5f; margin-bottom: 10px; }
        p { font-size: 14pt; color: #555; line-height: 1.6; }
        hr { border: none; border-top: 2px solid #1e3a5f; margin: 20px 0; }
        .badge {
            display: inline-block;
            background-color: #1e3a5f;
            color: white;
            padding: 4px 14px;
            font-size: 10pt;
            font-weight: bold;
        }
    </style></head>
    <body>
        <h1>Hello, FastPDF!</h1>
        <hr>
        <p>
            This is a minimal PDF generated entirely from <strong>HTML and CSS</strong>,
            rendered at native speed by FastPDF's <em>Rust layout engine</em>.
        </p>
        <p>No headless browser. No external dependencies. Just fast, clean PDFs.</p>
        <br>
        <span class="badge">FastPDF v0.1</span>
    </body>
    </html>
    """
    path = OUTPUT / "01_hello_world.pdf"
    render_pdf_to_file(html, str(path))
    return path


# ─── 2. Typography Showcase ────────────────────────────────────────────────────

def example_typography():
    html = """
    <html>
    <head><style>
        body { font-family: Helvetica; padding: 40px; color: #222; }
        h1 { font-size: 28pt; color: #0f172a; margin-bottom: 6px; }
        .subtitle { font-size: 12pt; color: #64748b; margin-bottom: 30px; }
        h2 { font-size: 16pt; color: #334155; margin-top: 24px; margin-bottom: 8px;
             border-bottom: 1px solid #e2e8f0; padding-bottom: 4px; }
        p { font-size: 11pt; line-height: 1.7; margin-bottom: 10px; }
        .sample { margin-bottom: 14px; }
        .label { font-size: 9pt; color: #94a3b8; text-transform: uppercase; margin-bottom: 2px; }
        .size-48 { font-size: 48pt; font-weight: bold; color: #0f172a; }
        .size-36 { font-size: 36pt; font-weight: bold; color: #1e293b; }
        .size-24 { font-size: 24pt; color: #334155; }
        .size-18 { font-size: 18pt; color: #475569; }
        .size-14 { font-size: 14pt; color: #64748b; }
        .size-11 { font-size: 11pt; color: #64748b; }
        .size-9  { font-size: 9pt; color: #94a3b8; }
        .inline-demo { font-size: 12pt; line-height: 1.8; margin-bottom: 20px; }
    </style></head>
    <body>
        <h1>Typography</h1>
        <div class="subtitle">Font sizes &amp; inline formatting rendered by FastPDF</div>

        <h2>Type Scale</h2>
        <div class="sample"><div class="label">48 pt — Display</div><div class="size-48">Aa Bb Cc</div></div>
        <div class="sample"><div class="label">36 pt — Hero</div><div class="size-36">Aa Bb Cc</div></div>
        <div class="sample"><div class="label">24 pt — Heading 1</div><div class="size-24">The quick brown fox</div></div>
        <div class="sample"><div class="label">18 pt — Heading 2</div><div class="size-18">The quick brown fox jumps over the lazy dog</div></div>
        <div class="sample"><div class="label">14 pt — Lead</div><div class="size-14">The quick brown fox jumps over the lazy dog</div></div>
        <div class="sample"><div class="label">11 pt — Body</div><div class="size-11">The quick brown fox jumps over the lazy dog. Pack my box with five dozen liquor jugs.</div></div>
        <div class="sample"><div class="label">9 pt — Caption</div><div class="size-9">The quick brown fox jumps over the lazy dog. Pack my box with five dozen liquor jugs.</div></div>

        <h2>Inline Formatting</h2>
        <div class="inline-demo">
            <p>
                Regular text, then <strong>bold text</strong>, then <em>italic text</em>,
                and <strong><em>bold italic</em></strong> all flowing together on one line.
            </p>
            <p>
                You can mix <strong>weights</strong> and <em>styles</em> freely within
                a single paragraph — the inline formatting context keeps everything aligned.
            </p>
        </div>

        <h2>Paragraph Flow</h2>
        <p>
            FastPDF's layout engine wraps long text into multiple lines automatically.
            This paragraph contains enough text to demonstrate word-wrapping behavior
            across the full width of an A4 page with standard margins. The engine
            measures each glyph using built-in font metrics for Helvetica, Times,
            and Courier, producing accurate line breaks without any browser dependency.
        </p>
        <p>
            Second paragraph with <strong>bold sections</strong> and <em>italic
            sections</em> that maintain proper spacing. The inline formatting context
            tracks the x-advance of each element and wraps to the next line when the
            available width is exceeded.
        </p>
    </body>
    </html>
    """
    path = OUTPUT / "02_typography.pdf"
    render_pdf_to_file(html, str(path))
    return path


# ─── 3. Table Showcase ─────────────────────────────────────────────────────────

def example_tables():
    html = """
    <html>
    <head><style>
        body { font-family: Helvetica; padding: 40px; color: #1f2937; font-size: 10pt; }
        h1 { font-size: 24pt; color: #111827; margin-bottom: 6px; }
        .subtitle { font-size: 11pt; color: #6b7280; margin-bottom: 30px; }
        h2 { font-size: 14pt; color: #374151; margin-top: 28px; margin-bottom: 10px; }

        /* Clean table */
        table.clean { width: 100%; border-collapse: collapse; margin-bottom: 30px; }
        table.clean thead th {
            background-color: #111827; color: white;
            padding: 10px 14px; text-align: left;
            font-size: 9pt; text-transform: uppercase; letter-spacing: 0.5px;
        }
        table.clean tbody td {
            padding: 10px 14px; border-bottom: 1px solid #e5e7eb;
        }
        table.clean tbody tr:nth-child(even) { background-color: #f9fafb; }

        /* Bordered table */
        table.bordered { width: 100%; border-collapse: collapse; margin-bottom: 30px; }
        table.bordered th, table.bordered td {
            border: 1px solid #d1d5db; padding: 8px 12px;
        }
        table.bordered thead th {
            background-color: #2563eb; color: white;
            font-size: 9pt; text-transform: uppercase;
        }

        /* Minimal table */
        table.minimal { width: 100%; border-collapse: collapse; margin-bottom: 30px; }
        table.minimal thead th {
            border-bottom: 2px solid #111827; padding: 8px 12px;
            text-align: left; font-size: 9pt; text-transform: uppercase; color: #374151;
        }
        table.minimal tbody td {
            padding: 8px 12px; border-bottom: 1px solid #f3f4f6;
        }

        .right { text-align: right; }
        .status-ok { color: #059669; font-weight: bold; }
        .status-warn { color: #d97706; font-weight: bold; }
        .status-err { color: #dc2626; font-weight: bold; }
    </style></head>
    <body>
        <h1>Tables</h1>
        <div class="subtitle">Three table styles rendered with thead/tbody support</div>

        <h2>Dark Header</h2>
        <table class="clean">
            <thead>
                <tr>
                    <th>Endpoint</th>
                    <th>Method</th>
                    <th class="right">Latency</th>
                    <th>Status</th>
                </tr>
            </thead>
            <tbody>
                <tr><td>/api/users</td><td>GET</td><td class="right">12 ms</td><td class="status-ok">200 OK</td></tr>
                <tr><td>/api/users/42</td><td>GET</td><td class="right">8 ms</td><td class="status-ok">200 OK</td></tr>
                <tr><td>/api/orders</td><td>POST</td><td class="right">45 ms</td><td class="status-ok">201 Created</td></tr>
                <tr><td>/api/auth/token</td><td>POST</td><td class="right">230 ms</td><td class="status-warn">429 Rate Limited</td></tr>
                <tr><td>/api/reports/gen</td><td>GET</td><td class="right">5200 ms</td><td class="status-err">504 Timeout</td></tr>
            </tbody>
        </table>

        <h2>Bordered</h2>
        <table class="bordered">
            <thead>
                <tr><th>Quarter</th><th class="right">Revenue</th><th class="right">Expenses</th><th class="right">Profit</th></tr>
            </thead>
            <tbody>
                <tr><td>Q1 2025</td><td class="right">$1,240,000</td><td class="right">$890,000</td><td class="right">$350,000</td></tr>
                <tr><td>Q2 2025</td><td class="right">$1,380,000</td><td class="right">$920,000</td><td class="right">$460,000</td></tr>
                <tr><td>Q3 2025</td><td class="right">$1,510,000</td><td class="right">$970,000</td><td class="right">$540,000</td></tr>
                <tr><td>Q4 2025</td><td class="right">$1,720,000</td><td class="right">$1,050,000</td><td class="right">$670,000</td></tr>
            </tbody>
        </table>

        <h2>Minimal</h2>
        <table class="minimal">
            <thead>
                <tr><th>Package</th><th>Version</th><th>License</th><th class="right">Size</th></tr>
            </thead>
            <tbody>
                <tr><td>fastpdf</td><td>0.1.0</td><td>MIT</td><td class="right">2.4 MB</td></tr>
                <tr><td>printpdf</td><td>0.7.0</td><td>MIT</td><td class="right">1.1 MB</td></tr>
                <tr><td>html5ever</td><td>0.27</td><td>MIT/Apache</td><td class="right">680 KB</td></tr>
                <tr><td>pyo3</td><td>0.22</td><td>MIT/Apache</td><td class="right">520 KB</td></tr>
                <tr><td>jinja2</td><td>3.1</td><td>BSD</td><td class="right">320 KB</td></tr>
            </tbody>
        </table>
    </body>
    </html>
    """
    path = OUTPUT / "03_tables.pdf"
    render_pdf_to_file(html, str(path))
    return path


# ─── 4. Invoice (Jinja2 template) ──────────────────────────────────────────────

def example_invoice():
    engine = PdfEngine(
        template_dir=str(TEMPLATES),
        default_options=RenderOptions(
            page_size="A4",
            margin_top=15,
            margin_right=15,
            margin_bottom=20,
            margin_left=15,
            title="Invoice INV-2026-0087",
        ),
    )

    context = {
        "invoice_number": "INV-2026-0087",
        "date": "March 15, 2026",
        "due_date": "April 14, 2026",
        "company": {
            "name": "FastPDF Labs",
            "address": "42 Rue de Rivoli",
            "city": "75001 Paris, France",
            "email": "billing@fastpdf.dev",
        },
        "customer": {
            "name": "Marie Dupont",
            "company": "Agence Digitale SAS",
            "address": "8 Avenue des Champs-Elysees",
            "city": "75008 Paris, France",
            "email": "marie@agence-digitale.fr",
        },
        "items": [
            {"description": "FastPDF Enterprise License (annual)", "quantity": 1, "rate": 4800.00},
            {"description": "Custom Template Design — Invoice Suite", "quantity": 3, "rate": 650.00},
            {"description": "Custom Template Design — Report Suite", "quantity": 2, "rate": 750.00},
            {"description": "On-site Integration Workshop (days)", "quantity": 2, "rate": 1200.00},
            {"description": "Priority Support — 12 months", "quantity": 1, "rate": 1800.00},
        ],
        "tax_rate": 0.20,
        "notes": "Payment due within 30 days by wire transfer. IBAN: FR76 3000 4000 0500 0012 3456 789. BIC: BNPAFRPP.",
    }

    for item in context["items"]:
        item["total"] = item["quantity"] * item["rate"]
    context["subtotal"] = sum(i["total"] for i in context["items"])
    context["tax"] = context["subtotal"] * context["tax_rate"]
    context["total"] = context["subtotal"] + context["tax"]

    doc = engine.render_template("invoice.html", context=context)
    path = OUTPUT / "04_invoice.pdf"
    doc.save(str(path))
    return path


# ─── 5. Report / Multi-section Document ────────────────────────────────────────

def example_report():
    html = """
    <html>
    <head><style>
        body { font-family: Helvetica; padding: 40px; color: #1f2937; font-size: 10pt; }
        .cover { text-align: center; padding: 120px 40px 60px; }
        .cover h1 { font-size: 32pt; color: #0f172a; margin-bottom: 8px; }
        .cover .sub { font-size: 14pt; color: #64748b; margin-bottom: 40px; }
        .cover .meta { font-size: 10pt; color: #94a3b8; }

        h2 { font-size: 18pt; color: #0f172a; margin-top: 36px; margin-bottom: 10px;
             border-bottom: 2px solid #2563eb; padding-bottom: 6px; }
        h3 { font-size: 13pt; color: #334155; margin-top: 20px; margin-bottom: 6px; }
        p { line-height: 1.7; margin-bottom: 10px; }
        ul { margin-bottom: 10px; }
        li { margin-bottom: 4px; line-height: 1.5; }

        .kpi-row { display: flex; justify-content: space-between; margin: 20px 0 28px; }
        .kpi { text-align: center; width: 23%; padding: 14px 8px;
               border: 1px solid #e2e8f0; background-color: #f8fafc; }
        .kpi-value { font-size: 22pt; font-weight: bold; color: #2563eb; }
        .kpi-label { font-size: 9pt; color: #64748b; text-transform: uppercase; margin-top: 2px; }

        table { width: 100%; border-collapse: collapse; margin: 14px 0 20px; }
        thead th { background-color: #1e293b; color: white; padding: 8px 12px;
                   text-align: left; font-size: 9pt; text-transform: uppercase; }
        tbody td { padding: 8px 12px; border-bottom: 1px solid #e5e7eb; }
        tbody tr:nth-child(even) { background-color: #f9fafb; }
        .right { text-align: right; }

        .callout { background-color: #eff6ff; border-left: 4px solid #2563eb;
                   padding: 12px 16px; margin: 16px 0; font-size: 10pt; color: #1e40af; }

        .footer { margin-top: 40px; text-align: center; font-size: 8pt; color: #94a3b8;
                  border-top: 1px solid #e5e7eb; padding-top: 12px; }
    </style></head>
    <body>
        <div class="cover">
            <h1>Q4 2025 Performance Report</h1>
            <div class="sub">Engineering &amp; Infrastructure Division</div>
            <div class="meta">Prepared by FastPDF Labs — March 2026</div>
            <div class="meta">CONFIDENTIAL</div>
        </div>

        <h2>1. Executive Summary</h2>
        <p>
            The fourth quarter of 2025 marked a significant milestone for the platform team.
            We shipped <strong>47 features</strong>, reduced average API latency by
            <strong>38%</strong>, and achieved <strong>99.97% uptime</strong> across all
            production services. This report summarizes key metrics, project outcomes,
            and recommendations for Q1 2026.
        </p>

        <div class="kpi-row">
            <div class="kpi"><div class="kpi-value">47</div><div class="kpi-label">Features Shipped</div></div>
            <div class="kpi"><div class="kpi-value">99.97%</div><div class="kpi-label">Uptime</div></div>
            <div class="kpi"><div class="kpi-value">-38%</div><div class="kpi-label">Latency Reduction</div></div>
            <div class="kpi"><div class="kpi-value">12</div><div class="kpi-label">Team Members</div></div>
        </div>

        <h2>2. Service Health</h2>
        <p>All critical services maintained SLOs throughout the quarter. Two incidents were
        escalated to P1 but resolved within the 30-minute target window.</p>

        <table>
            <thead>
                <tr><th>Service</th><th class="right">Requests/day</th><th class="right">p99 Latency</th><th>Status</th></tr>
            </thead>
            <tbody>
                <tr><td>API Gateway</td><td class="right">14.2M</td><td class="right">45 ms</td><td><strong>Healthy</strong></td></tr>
                <tr><td>Auth Service</td><td class="right">8.7M</td><td class="right">22 ms</td><td><strong>Healthy</strong></td></tr>
                <tr><td>Billing Engine</td><td class="right">1.1M</td><td class="right">120 ms</td><td><strong>Healthy</strong></td></tr>
                <tr><td>PDF Renderer</td><td class="right">620K</td><td class="right">180 ms</td><td><strong>Healthy</strong></td></tr>
                <tr><td>Notification Hub</td><td class="right">3.4M</td><td class="right">38 ms</td><td><strong>Healthy</strong></td></tr>
                <tr><td>Search Index</td><td class="right">5.9M</td><td class="right">65 ms</td><td><strong>Degraded</strong></td></tr>
            </tbody>
        </table>

        <div class="callout">
            <strong>Action Required:</strong> The Search Index service exceeded its p99 latency SLO
            on 4 days during December. A capacity planning review is scheduled for January 15.
        </div>

        <h2>3. Key Projects Delivered</h2>

        <h3>3.1 API v3 Migration</h3>
        <p>
            Completed the migration of all public endpoints from API v2 to v3. The new version
            introduces consistent pagination, standardized error responses, and OpenAPI 3.1
            schema generation. Adoption rate reached 78% by end of quarter.
        </p>

        <h3>3.2 Infrastructure Cost Optimization</h3>
        <p>
            Reduced monthly cloud spend by <strong>$42,000</strong> through right-sizing
            instances, adopting spot capacity for batch workloads, and implementing automated
            scaling policies. Total annual savings projected at <strong>$504,000</strong>.
        </p>

        <h3>3.3 Observability Platform Upgrade</h3>
        <p>
            Deployed unified tracing across all microservices using OpenTelemetry. Mean time
            to detection (MTTD) improved from 12 minutes to 3 minutes. Dashboards now cover
            100% of critical business flows.
        </p>

        <h2>4. Team Velocity</h2>
        <table>
            <thead>
                <tr><th>Month</th><th class="right">Story Points</th><th class="right">PRs Merged</th><th class="right">Bugs Fixed</th><th class="right">Tech Debt Items</th></tr>
            </thead>
            <tbody>
                <tr><td>October</td><td class="right">142</td><td class="right">87</td><td class="right">23</td><td class="right">11</td></tr>
                <tr><td>November</td><td class="right">158</td><td class="right">94</td><td class="right">19</td><td class="right">14</td></tr>
                <tr><td>December</td><td class="right">131</td><td class="right">72</td><td class="right">28</td><td class="right">8</td></tr>
            </tbody>
        </table>

        <h2>5. Recommendations for Q1 2026</h2>
        <ul>
            <li><strong>Search Index:</strong> Allocate 2 engineers to the capacity upgrade project (target: p99 under 50 ms)</li>
            <li><strong>API v2 Sunset:</strong> Set deprecation date for March 31, 2026 and notify remaining v2 consumers</li>
            <li><strong>Security Audit:</strong> Schedule annual pen-test for February; address all critical findings within 2 sprints</li>
            <li><strong>Hiring:</strong> Open 3 positions — 2 backend engineers and 1 SRE — to support Q2 growth targets</li>
            <li><strong>Documentation:</strong> Complete internal runbooks for all Tier-1 services before end of January</li>
        </ul>

        <div class="footer">
            FastPDF Labs — Q4 2025 Performance Report — Page 1 of 1 — CONFIDENTIAL
        </div>
    </body>
    </html>
    """
    path = OUTPUT / "05_report.pdf"
    opts = RenderOptions(
        page_size="A4",
        margin_top=20, margin_right=20, margin_bottom=20, margin_left=20,
        title="Q4 2025 Performance Report",
        author="FastPDF Labs",
    )
    render_pdf_to_file(html, str(path), options=opts)
    return path


# ─── 6. Résumé / CV ────────────────────────────────────────────────────────────

def example_resume():
    html = """
    <html>
    <head><style>
        body { font-family: Helvetica; padding: 40px 45px; color: #1f2937; font-size: 10pt; }

        .header { margin-bottom: 20px; border-bottom: 3px solid #111827; padding-bottom: 14px; }
        .name { font-size: 26pt; font-weight: bold; color: #111827; }
        .title-role { font-size: 13pt; color: #4b5563; margin-top: 2px; }
        .contact { font-size: 9pt; color: #6b7280; margin-top: 6px; }

        h2 { font-size: 12pt; color: #111827; text-transform: uppercase; letter-spacing: 1px;
             margin-top: 22px; margin-bottom: 8px; border-bottom: 1px solid #d1d5db; padding-bottom: 4px; }

        .entry { margin-bottom: 14px; }
        .entry-header { display: flex; justify-content: space-between; }
        .entry-title { font-size: 11pt; font-weight: bold; color: #1f2937; }
        .entry-date { font-size: 10pt; color: #6b7280; }
        .entry-subtitle { font-size: 10pt; color: #4b5563; font-style: italic; margin-bottom: 4px; }
        .entry ul { margin-left: 16px; }
        .entry li { margin-bottom: 3px; line-height: 1.5; }

        .skills-grid { display: flex; flex-wrap: wrap; }
        .skill-group { width: 48%; margin-bottom: 10px; }
        .skill-label { font-weight: bold; font-size: 10pt; color: #374151; margin-bottom: 2px; }
        .skill-items { font-size: 10pt; color: #4b5563; }
    </style></head>
    <body>
        <div class="header">
            <div class="name">Alexandre Martin</div>
            <div class="title-role">Senior Software Engineer</div>
            <div class="contact">Paris, France — alex.martin@email.com — github.com/alexmartin — +33 6 12 34 56 78</div>
        </div>

        <h2>Experience</h2>

        <div class="entry">
            <div class="entry-header">
                <div class="entry-title">Senior Software Engineer — Dataflow Inc.</div>
                <div class="entry-date">2023 — Present</div>
            </div>
            <div class="entry-subtitle">Real-time data processing platform (Series B, 120 employees)</div>
            <ul>
                <li>Designed and shipped a Rust-based PDF rendering engine processing 2M documents/month with p99 latency under 200ms</li>
                <li>Led migration from monolith to microservices, reducing deploy time from 45 min to 4 min</li>
                <li>Mentored 4 junior engineers; established code review guidelines adopted team-wide</li>
            </ul>
        </div>

        <div class="entry">
            <div class="entry-header">
                <div class="entry-title">Software Engineer — CloudScale SAS</div>
                <div class="entry-date">2020 — 2023</div>
            </div>
            <div class="entry-subtitle">Enterprise cloud infrastructure platform</div>
            <ul>
                <li>Built a Python SDK serving 800+ enterprise customers with 99.9% API availability</li>
                <li>Implemented automated billing pipeline processing $3.2M ARR with zero discrepancies</li>
                <li>Reduced infrastructure costs by 35% through spot instance strategy and auto-scaling</li>
            </ul>
        </div>

        <div class="entry">
            <div class="entry-header">
                <div class="entry-title">Junior Developer — WebAgency</div>
                <div class="entry-date">2018 — 2020</div>
            </div>
            <div class="entry-subtitle">Digital agency — full-stack web development</div>
            <ul>
                <li>Delivered 15+ client projects using Django, React, and PostgreSQL</li>
                <li>Created internal component library reducing new project bootstrap time by 60%</li>
            </ul>
        </div>

        <h2>Education</h2>

        <div class="entry">
            <div class="entry-header">
                <div class="entry-title">MSc Computer Science — Ecole Polytechnique</div>
                <div class="entry-date">2016 — 2018</div>
            </div>
            <div class="entry-subtitle">Specialization in distributed systems and compiler design</div>
        </div>

        <div class="entry">
            <div class="entry-header">
                <div class="entry-title">BSc Mathematics &amp; Computer Science — Universite Paris-Saclay</div>
                <div class="entry-date">2013 — 2016</div>
            </div>
        </div>

        <h2>Technical Skills</h2>
        <div class="skills-grid">
            <div class="skill-group">
                <div class="skill-label">Languages</div>
                <div class="skill-items">Rust, Python, TypeScript, Go, SQL</div>
            </div>
            <div class="skill-group">
                <div class="skill-label">Frameworks</div>
                <div class="skill-items">Django, FastAPI, React, Actix-web</div>
            </div>
            <div class="skill-group">
                <div class="skill-label">Infrastructure</div>
                <div class="skill-items">AWS, Docker, Kubernetes, Terraform</div>
            </div>
            <div class="skill-group">
                <div class="skill-label">Data</div>
                <div class="skill-items">PostgreSQL, Redis, Kafka, Elasticsearch</div>
            </div>
        </div>

        <h2>Open Source</h2>
        <div class="entry">
            <ul>
                <li><strong>fastpdf</strong> — High-performance HTML-to-PDF engine in Rust with Python bindings (1.2k stars)</li>
                <li><strong>pystream</strong> — Async stream processing library for Python (680 stars)</li>
            </ul>
        </div>
    </body>
    </html>
    """
    path = OUTPUT / "06_resume.pdf"
    opts = RenderOptions(
        page_size="A4",
        margin_top=15, margin_right=15, margin_bottom=15, margin_left=15,
        title="Alexandre Martin — Resume",
    )
    render_pdf_to_file(html, str(path), options=opts)
    return path


# ─── 7. Receipt ────────────────────────────────────────────────────────────────

def example_receipt():
    html = """
    <html>
    <head><style>
        body { font-family: Courier; padding: 30px 50px; color: #111; font-size: 10pt; }
        .receipt { max-width: 380px; margin: 0 auto; }
        .center { text-align: center; }
        .shop-name { font-size: 16pt; font-weight: bold; }
        .divider { border-top: 1px dashed #999; margin: 10px 0; }
        .row { display: flex; justify-content: space-between; margin-bottom: 2px; }
        .row-bold { display: flex; justify-content: space-between; font-weight: bold; margin-bottom: 2px; }
        .total-row { display: flex; justify-content: space-between; font-size: 14pt; font-weight: bold; margin: 4px 0; }
        .small { font-size: 8pt; color: #666; }
        table { width: 100%; border-collapse: collapse; }
        th { text-align: left; border-bottom: 1px solid #333; padding: 3px 0; font-size: 9pt; }
        td { padding: 3px 0; }
        .right { text-align: right; }
    </style></head>
    <body>
        <div class="receipt">
            <div class="center">
                <div class="shop-name">CAFE DE FLORE</div>
                <div>172 Boulevard Saint-Germain</div>
                <div>75006 Paris</div>
                <div class="small">Tel: +33 1 45 48 55 26</div>
                <div class="small">SIRET: 552 120 222 00013</div>
            </div>

            <div class="divider"></div>

            <div class="row">
                <span>Date: 15/03/2026</span>
                <span>14:32</span>
            </div>
            <div class="row">
                <span>Table: 12</span>
                <span>Server: MH</span>
            </div>

            <div class="divider"></div>

            <table>
                <thead>
                    <tr><th>Item</th><th class="right">Qty</th><th class="right">Price</th></tr>
                </thead>
                <tbody>
                    <tr><td>Espresso</td><td class="right">2</td><td class="right">7.00</td></tr>
                    <tr><td>Cafe Creme</td><td class="right">1</td><td class="right">5.50</td></tr>
                    <tr><td>Croissant Beurre</td><td class="right">2</td><td class="right">5.00</td></tr>
                    <tr><td>Pain au Chocolat</td><td class="right">1</td><td class="right">3.00</td></tr>
                    <tr><td>Jus d'Orange</td><td class="right">1</td><td class="right">6.00</td></tr>
                    <tr><td>Tartine Confiture</td><td class="right">1</td><td class="right">4.50</td></tr>
                </tbody>
            </table>

            <div class="divider"></div>

            <div class="row"><span>Sous-total HT</span><span>25.83</span></div>
            <div class="row"><span>TVA 20%</span><span>5.17</span></div>
            <div class="divider"></div>
            <div class="total-row"><span>TOTAL EUR</span><span>31.00</span></div>
            <div class="divider"></div>

            <div class="row"><span>CB Visa ****4821</span><span>31.00</span></div>
            <div class="small center" style="margin-top: 6px;">Transaction: 8A2F-C041-9E72</div>

            <div class="divider"></div>

            <div class="center small" style="margin-top: 8px;">
                Merci de votre visite !<br>
                A bientot au Cafe de Flore
            </div>
        </div>
    </body>
    </html>
    """
    path = OUTPUT / "07_receipt.pdf"
    opts = RenderOptions(page_size=(120.0, 210.0), margin_top=10, margin_right=10, margin_bottom=10, margin_left=10)
    render_pdf_to_file(html, str(path), options=opts)
    return path


# ─── 8. Letter / Formal Document ───────────────────────────────────────────────

def example_letter():
    html = """
    <html>
    <head><style>
        body { font-family: Times; padding: 50px; color: #1a1a1a; font-size: 12pt; line-height: 1.6; }
        .sender { margin-bottom: 30px; }
        .sender-name { font-size: 14pt; font-weight: bold; }
        .sender-detail { font-size: 10pt; color: #555; }
        .date { margin-bottom: 30px; color: #333; }
        .recipient { margin-bottom: 30px; }
        .subject { font-weight: bold; margin-bottom: 20px; font-size: 12pt; }
        .body p { margin-bottom: 14px; text-align: justify; }
        .closing { margin-top: 30px; }
        .signature { margin-top: 40px; font-weight: bold; font-size: 13pt; }
    </style></head>
    <body>
        <div class="sender">
            <div class="sender-name">Dr. Sophie Laurent</div>
            <div class="sender-detail">Directrice de Recherche</div>
            <div class="sender-detail">Laboratoire d'Informatique de Paris</div>
            <div class="sender-detail">4 Place Jussieu, 75005 Paris</div>
            <div class="sender-detail">sophie.laurent@lip.fr</div>
        </div>

        <div class="date">Paris, March 15, 2026</div>

        <div class="recipient">
            Prof. James Mitchell<br>
            Department of Computer Science<br>
            Stanford University<br>
            353 Jane Stanford Way<br>
            Stanford, CA 94305
        </div>

        <div class="subject">Re: Collaboration on High-Performance Document Processing</div>

        <div class="body">
            <p>Dear Professor Mitchell,</p>

            <p>
                Thank you for your letter of February 28 regarding the proposed joint research
                project on high-performance document processing systems. I am writing to confirm
                our laboratory's strong interest in this collaboration and to outline the initial
                contributions we envision from our team.
            </p>

            <p>
                Our group has been developing <strong>FastPDF</strong>, an open-source PDF rendering
                engine implemented in Rust with Python bindings. The engine parses HTML and CSS,
                computes a layout tree, and generates PDF output without relying on any browser
                engine. Current benchmarks show rendering throughput of approximately 2,000 pages
                per second on a single core, with memory usage under 50 MB for typical documents.
            </p>

            <p>
                We believe this work aligns well with your team's research on streaming document
                transformations. Specifically, we propose the following areas of joint investigation:
                adaptive layout algorithms for variable-length content, incremental rendering for
                real-time preview, and formal verification of CSS layout compliance.
            </p>

            <p>
                I would be delighted to arrange a video conference in the coming weeks to discuss
                the details of the collaboration framework, including shared deliverables, publication
                plans, and student exchange opportunities. My assistant can coordinate scheduling
                at your convenience.
            </p>

            <p>
                Please find enclosed our latest technical report (LIP-TR-2026-03) for your review.
                I look forward to your response and to a productive partnership.
            </p>
        </div>

        <div class="closing">With kind regards,</div>
        <div class="signature">Dr. Sophie Laurent</div>
    </body>
    </html>
    """
    path = OUTPUT / "08_letter.pdf"
    opts = RenderOptions(
        page_size="A4",
        margin_top=25, margin_right=25, margin_bottom=25, margin_left=25,
        title="Letter — Collaboration Proposal",
    )
    render_pdf_to_file(html, str(path), options=opts)
    return path


# ─── Main ───────────────────────────────────────────────────────────────────────

EXAMPLES = [
    ("Hello World",  example_hello_world),
    ("Typography",   example_typography),
    ("Tables",       example_tables),
    ("Invoice",      example_invoice),
    ("Report",       example_report),
    ("Resume / CV",  example_resume),
    ("Receipt",      example_receipt),
    ("Formal Letter", example_letter),
]


if __name__ == "__main__":
    ensure_output()
    print("FastPDF — Generating Example PDFs")
    print("=" * 50)

    for name, fn in EXAMPLES:
        try:
            path = fn()
            size_kb = os.path.getsize(path) / 1024
            print(f"  ✓ {name:<20s} → {path.name}  ({size_kb:.1f} KB)")
        except Exception as e:
            print(f"  ✗ {name:<20s} → ERROR: {e}")

    print("=" * 50)
    print(f"Output directory: {OUTPUT.resolve()}")
