"""
FastPDF — FastAPI & Django Integration Benchmarks
==================================================

Measures end-to-end HTTP response time for PDF endpoints built with the
FastAPI contrib helper and the equivalent in-process timing for Django-style
rendering (Django views use the same Python path, so in-process time = view time).

Run:
    python benchmarks/benchmark_integrations.py
"""
from __future__ import annotations

import asyncio
import statistics
import sys
import time
import platform
import threading
from typing import Callable


# ─── HTML fixtures ────────────────────────────────────────────────────────────

SIMPLE_HTML = "<h1>Hello World</h1><p>Simple document.</p>"

STYLED_HTML = """<html><head><style>
body { font-family: Helvetica; color: #333; }
h1 { color: #1a56db; border-bottom: 2px solid #1a56db; }
p { line-height: 1.6; }
</style></head><body>
<h1>Integration Benchmark</h1>
<p>Testing the FastAPI and Django contrib helpers end-to-end.</p>
<p>Second paragraph with a bit more content to exercise the layout engine.</p>
</body></html>"""

INVOICE_HTML = """<html><head><style>
body {{ font-family: Helvetica; }}
h1 {{ color: #1e40af; }}
table {{ width:100%; border-collapse:collapse; margin-top:20px; }}
th {{ background:#1e40af; color:white; padding:10px; text-align:left; }}
td {{ padding:8px 10px; border-bottom:1px solid #e5e7eb; }}
.total {{ font-weight: bold; font-size: 14pt; }}
</style></head><body>
<h1>Invoice #0042</h1>
<p>Date: 2026-03-16</p>
<table>
<thead><tr><th>Item</th><th>Qty</th><th>Unit price</th><th>Total</th></tr></thead>
<tbody>
{rows}
<tr class="total"><td colspan="3">Grand Total</td><td>$6 500.00</td></tr>
</tbody>
</table>
</body></html>""".format(
    rows="\n".join(
        f"<tr><td>Line item {i}</td><td>{i}</td><td>${i*50:.2f}</td><td>${i*i*10:.2f}</td></tr>"
        for i in range(1, 11)
    )
)

TAILWIND_HTML = """<div class="p-8 bg-white">
<h1 class="text-3xl font-bold text-blue-600 mb-4">Tailwind Report</h1>
<p class="text-gray-600 mb-2">Integration benchmark with Tailwind CSS utilities.</p>
<div class="flex gap-4 mt-4">
  <div class="flex-1 p-4 bg-blue-50 rounded">
    <p class="font-bold text-blue-800">Revenue</p>
    <p class="text-2xl font-black text-blue-600">$48 320</p>
  </div>
  <div class="flex-1 p-4 bg-green-50 rounded">
    <p class="font-bold text-green-800">Orders</p>
    <p class="text-2xl font-black text-green-600">1 284</p>
  </div>
</div>
</div>"""


# ─── Timing helpers ───────────────────────────────────────────────────────────

def time_sync(fn: Callable, iterations: int = 30) -> dict:
    fn()  # warm-up
    times = []
    for _ in range(iterations):
        t0 = time.perf_counter()
        fn()
        times.append((time.perf_counter() - t0) * 1000)
    return {
        "mean_ms":   statistics.mean(times),
        "median_ms": statistics.median(times),
        "min_ms":    min(times),
        "stdev_ms":  statistics.stdev(times),
        "p95_ms":    sorted(times)[int(len(times) * 0.95)],
    }


async def time_async(coro_fn: Callable, iterations: int = 30) -> dict:
    await coro_fn()  # warm-up
    times = []
    for _ in range(iterations):
        t0 = time.perf_counter()
        await coro_fn()
        times.append((time.perf_counter() - t0) * 1000)
    return {
        "mean_ms":   statistics.mean(times),
        "median_ms": statistics.median(times),
        "min_ms":    min(times),
        "stdev_ms":  statistics.stdev(times),
        "p95_ms":    sorted(times)[int(len(times) * 0.95)],
    }


def fmt(ms: float) -> str:
    if ms < 1:
        return f"{ms*1000:.0f} µs"
    if ms < 1000:
        return f"{ms:.2f} ms"
    return f"{ms/1000:.3f} s"


def print_row(label: str, r: dict):
    print(
        f"  {label:<35} "
        f"mean={fmt(r['mean_ms']):>10}  "
        f"median={fmt(r['median_ms']):>10}  "
        f"min={fmt(r['min_ms']):>10}  "
        f"p95={fmt(r['p95_ms']):>10}"
    )


# ─── FastAPI HTTP benchmark ───────────────────────────────────────────────────

def run_fastapi_benchmark():
    print("\nFastAPI — HTTP endpoint benchmark")
    print("-" * 80)

    try:
        import uvicorn
        import httpx
        from fastapi import FastAPI
        from fastpdf import RenderOptions
        from fastpdf.contrib.fastapi import PdfResponse, render_pdf_async
    except ImportError as e:
        print(f"  Skipped: {e}")
        return {}

    app = FastAPI()

    @app.get("/simple.pdf")
    async def ep_simple():
        return PdfResponse(SIMPLE_HTML, filename="simple.pdf")

    @app.get("/styled.pdf")
    async def ep_styled():
        return PdfResponse(STYLED_HTML, filename="styled.pdf")

    @app.get("/invoice.pdf")
    async def ep_invoice():
        opts = RenderOptions(title="Invoice", author="Benchmark")
        return PdfResponse(INVOICE_HTML, options=opts, filename="invoice.pdf")

    @app.get("/async.pdf")
    async def ep_async():
        pdf = await render_pdf_async(STYLED_HTML)
        from fastapi.responses import Response
        return Response(content=pdf, media_type="application/pdf")

    @app.get("/tailwind.pdf")
    async def ep_tailwind():
        opts = RenderOptions(tailwind=True)
        return PdfResponse(TAILWIND_HTML, options=opts, filename="tailwind.pdf")

    # Start server in a background thread
    server = uvicorn.Server(uvicorn.Config(app, host="127.0.0.1", port=18765, log_level="error"))
    t = threading.Thread(target=server.run, daemon=True)
    t.start()
    time.sleep(0.8)  # let server start

    results = {}
    with httpx.Client(base_url="http://127.0.0.1:18765", timeout=30.0) as client:
        try:
            client.get("/simple.pdf")  # pre-warm connection
        except Exception:
            pass

        for path, label in [
            ("/simple.pdf",   "GET /simple.pdf  (plain HTML)"),
            ("/styled.pdf",   "GET /styled.pdf  (CSS styled)"),
            ("/invoice.pdf",  "GET /invoice.pdf (10-row table)"),
            ("/async.pdf",    "GET /async.pdf   (async helper)"),
            ("/tailwind.pdf", "GET /tailwind.pdf (Tailwind CSS)"),
        ]:
            r = time_sync(lambda p=path: client.get(p), iterations=30)
            print_row(label, r)
            results[label] = r

    server.should_exit = True
    return results


# ─── Django in-process benchmark ─────────────────────────────────────────────

def run_django_benchmark():
    """
    Django views are thin wrappers over render_pdf; the measured time is the
    same as calling render_pdf directly plus the HttpResponse construction.
    We simulate exactly that: strip HTML tags → render_pdf → HttpResponse.
    """
    print("\nDjango — contrib helper in-process benchmark")
    print("-" * 80)

    try:
        import django
        from django.conf import settings
        from django.http import HttpResponse
        if not settings.configured:
            settings.configure(
                DATABASES={},
                INSTALLED_APPS=[],
                USE_TZ=False,
            )
            django.setup()
        from fastpdf import render_pdf, RenderOptions
        from fastpdf.contrib.django import render_html_to_pdf_response
    except ImportError as e:
        print(f"  Skipped: {e}")
        return {}

    results = {}

    fixtures = [
        ("render_pdf (simple)",                        lambda: render_pdf(SIMPLE_HTML)),
        ("render_pdf (styled CSS)",                    lambda: render_pdf(STYLED_HTML)),
        ("render_pdf (invoice table)",                 lambda: render_pdf(INVOICE_HTML)),
        ("render_pdf (Tailwind)",                      lambda: render_pdf(TAILWIND_HTML, options=RenderOptions(tailwind=True))),
        ("render_html_to_pdf_response (simple)",       lambda: render_html_to_pdf_response(SIMPLE_HTML, filename="out.pdf")),
        ("render_html_to_pdf_response (styled)",       lambda: render_html_to_pdf_response(STYLED_HTML, filename="out.pdf")),
        ("render_html_to_pdf_response (inline)",       lambda: render_html_to_pdf_response(STYLED_HTML, filename="out.pdf", inline=True)),
    ]

    for label, fn in fixtures:
        r = time_sync(fn, iterations=30)
        print_row(label, r)
        results[label] = r

    return results


# ─── async FastAPI render_pdf_async standalone ───────────────────────────────

def run_async_benchmark():
    print("\nFastAPI — render_pdf_async (asyncio, no HTTP overhead)")
    print("-" * 80)

    try:
        from fastpdf.contrib.fastapi import render_pdf_async, batch_render_async
        from fastpdf import RenderOptions
    except ImportError as e:
        print(f"  Skipped: {e}")
        return {}

    results = {}

    async def _run():
        items = [
            ("render_pdf_async (simple)",   lambda: render_pdf_async(SIMPLE_HTML)),
            ("render_pdf_async (styled)",   lambda: render_pdf_async(STYLED_HTML)),
            ("render_pdf_async (invoice)",  lambda: render_pdf_async(INVOICE_HTML)),
            ("batch_render_async 5 docs",
             lambda: batch_render_async([
                 {"html": SIMPLE_HTML}, {"html": STYLED_HTML}, {"html": INVOICE_HTML},
                 {"html": SIMPLE_HTML}, {"html": STYLED_HTML},
             ])),
            ("batch_render_async 10 docs",
             lambda: batch_render_async(
                 [{"html": SIMPLE_HTML}] * 5 + [{"html": STYLED_HTML}] * 5
             )),
        ]
        for label, coro_factory in items:
            r = await time_async(coro_factory, iterations=30)
            print_row(label, r)
            results[label] = r

    asyncio.run(_run())
    return results


# ─── Markdown report ─────────────────────────────────────────────────────────

def save_integration_markdown(fastapi_http, django_results, async_results, path="benchmarks/benchmark_results_integration.md"):
    lines = [
        "## FastAPI & Django Integration Benchmarks",
        "",
        f"> Machine: `{platform.processor()}` — {platform.system()} {platform.release()}  ",
        f"> Python `{sys.version.split()[0]}` — {time.strftime('%Y-%m-%d')}",
        "",
        "### FastAPI — HTTP endpoint (full round-trip)",
        "",
        "| Endpoint | Mean | Median | Min | p95 |",
        "|---|---|---|---|---|",
    ]
    for label, r in fastapi_http.items():
        lines.append(
            f"| `{label}` | {fmt(r['mean_ms'])} | {fmt(r['median_ms'])} | {fmt(r['min_ms'])} | {fmt(r['p95_ms'])} |"
        )
    lines += [
        "",
        "### FastAPI — `render_pdf_async` (asyncio, thread-pool dispatch)",
        "",
        "| Operation | Mean | Median | Min | p95 |",
        "|---|---|---|---|---|",
    ]
    for label, r in async_results.items():
        lines.append(
            f"| `{label}` | {fmt(r['mean_ms'])} | {fmt(r['median_ms'])} | {fmt(r['min_ms'])} | {fmt(r['p95_ms'])} |"
        )
    lines += [
        "",
        "### Django — `render_pdf` + contrib helpers (in-process)",
        "",
        "| Operation | Mean | Median | Min | p95 |",
        "|---|---|---|---|---|",
    ]
    for label, r in django_results.items():
        lines.append(
            f"| `{label}` | {fmt(r['mean_ms'])} | {fmt(r['median_ms'])} | {fmt(r['min_ms'])} | {fmt(r['p95_ms'])} |"
        )
    lines += [
        "",
        "> 1 warm-up run + 30 timed iterations per case. Mean +/- stdev reported.",
        "> Reproduce: `python benchmarks/benchmark_integrations.py`",
    ]
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print(f"\n  Markdown  ->  {path}")


# ─── main ─────────────────────────────────────────────────────────────────────

def main():
    print("=" * 80)
    print("FastPDF — FastAPI & Django Integration Benchmarks")
    print("=" * 80)
    print(f"Platform : {platform.platform()}")
    print(f"Python   : {sys.version.split()[0]}")
    print(f"Date     : {time.strftime('%Y-%m-%d %H:%M:%S')}")

    fastapi_http = run_fastapi_benchmark()
    async_results = run_async_benchmark()
    django_results = run_django_benchmark()

    save_integration_markdown(fastapi_http, django_results, async_results)

    print("\n" + "=" * 80)
    print("All done.")


if __name__ == "__main__":
    main()
