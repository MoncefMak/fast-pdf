"""
FastPDF Performance Benchmarks
==============================

Compares FastPDF rendering performance against other PDF libraries.

Run: python benchmarks/benchmark.py
"""

from __future__ import annotations

import statistics
import time
from typing import Callable, List


def time_function(func: Callable, iterations: int = 100) -> dict:
    """Time a function over multiple iterations."""
    times = []
    for _ in range(iterations):
        start = time.perf_counter()
        func()
        elapsed = (time.perf_counter() - start) * 1000  # ms
        times.append(elapsed)

    return {
        "iterations": iterations,
        "mean_ms": statistics.mean(times),
        "median_ms": statistics.median(times),
        "min_ms": min(times),
        "max_ms": max(times),
        "stdev_ms": statistics.stdev(times) if len(times) > 1 else 0,
        "p95_ms": sorted(times)[int(len(times) * 0.95)],
        "p99_ms": sorted(times)[int(len(times) * 0.99)],
    }


def format_result(name: str, result: dict) -> str:
    return (
        f"  {name:30s} "
        f"mean={result['mean_ms']:7.2f}ms  "
        f"median={result['median_ms']:7.2f}ms  "
        f"min={result['min_ms']:7.2f}ms  "
        f"p95={result['p95_ms']:7.2f}ms  "
        f"p99={result['p99_ms']:7.2f}ms"
    )


# ---------------------------------------------------------------------------
# Test documents
# ---------------------------------------------------------------------------

SIMPLE_HTML = "<h1>Hello World</h1><p>Simple document.</p>"

STYLED_HTML = """
<html><head><style>
body { font-family: Helvetica; color: #333; }
h1 { color: #1a56db; border-bottom: 2px solid #1a56db; }
p { line-height: 1.6; margin: 10px 0; }
</style></head><body>
<h1>Styled Document</h1>
<p>This is a styled paragraph with some formatting.</p>
<p>Second paragraph with more content to render.</p>
</body></html>
"""

TABLE_HTML = """
<html><head><style>
table { width: 100%%; border-collapse: collapse; }
th { background: #1a56db; color: white; padding: 8px; }
td { padding: 6px 8px; border-bottom: 1px solid #eee; }
</style></head><body>
<h1>Table Document</h1>
<table>
<thead><tr><th>ID</th><th>Name</th><th>Email</th><th>Amount</th></tr></thead>
<tbody>
%s
</tbody>
</table>
</body></html>
""" % "\n".join(
    f'<tr><td>{i}</td><td>Customer {i}</td><td>cust{i}@example.com</td><td>${i * 100:.2f}</td></tr>'
    for i in range(1, 51)
)

COMPLEX_HTML = """
<html><head><style>
body { font-family: Helvetica; font-size: 10pt; }
.header { background: #1e3a5f; color: white; padding: 20px; }
.section { margin: 15px 0; }
h2 { color: #1e3a5f; border-bottom: 1px solid #ddd; padding-bottom: 5px; }
.grid { display: flex; gap: 10px; }
.card { border: 1px solid #ddd; padding: 10px; flex: 1; }
table { width: 100%%; border-collapse: collapse; }
th, td { padding: 6px; border: 1px solid #ddd; }
th { background: #f5f5f5; }
</style></head><body>
<div class="header"><h1>Complex Report</h1><p>Generated at high speed</p></div>
<div class="section"><h2>Summary</h2>
<div class="grid">
<div class="card"><strong>Revenue</strong><br>$1,234,567</div>
<div class="card"><strong>Users</strong><br>45,678</div>
<div class="card"><strong>Growth</strong><br>23.4%%</div>
</div></div>
<div class="section"><h2>Details</h2>
<table><thead><tr><th>Metric</th><th>Q1</th><th>Q2</th><th>Q3</th><th>Q4</th></tr></thead>
<tbody>
%s
</tbody></table></div>
<div class="section"><h2>Notes</h2>
%s
</div>
</body></html>
""" % (
    "\n".join(
        f'<tr><td>Metric {i}</td><td>{i*10}</td><td>{i*12}</td><td>{i*15}</td><td>{i*18}</td></tr>'
        for i in range(1, 21)
    ),
    "\n".join(f"<p>Detailed note paragraph {i} with enough text to fill some space in the document.</p>" for i in range(1, 11)),
)


def run_benchmarks():
    print("=" * 80)
    print("FastPDF Performance Benchmarks")
    print("=" * 80)
    print()

    # --- FastPDF benchmarks ---
    try:
        from fastpdf import render_pdf, batch_render, RenderOptions

        print("FastPDF Engine:")
        print("-" * 80)

        result = time_function(lambda: render_pdf(SIMPLE_HTML), iterations=200)
        print(format_result("Simple HTML", result))

        result = time_function(lambda: render_pdf(STYLED_HTML), iterations=200)
        print(format_result("Styled HTML", result))

        result = time_function(lambda: render_pdf(TABLE_HTML), iterations=100)
        print(format_result("50-row Table", result))

        result = time_function(lambda: render_pdf(COMPLEX_HTML), iterations=100)
        print(format_result("Complex Report", result))

        # Tailwind
        tw_html = '<div class="p-8"><h1 class="text-2xl font-bold text-blue-600 mb-4">Tailwind</h1><p class="text-gray-600">Content</p></div>'
        result = time_function(
            lambda: render_pdf(tw_html, options=RenderOptions(tailwind=True)),
            iterations=100,
        )
        print(format_result("Tailwind CSS", result))

        # Batch (10 docs parallel)
        batch_items = [{"html": f"<h1>Doc {i}</h1>"} for i in range(10)]
        result = time_function(lambda: batch_render(batch_items), iterations=50)
        print(format_result("Batch 10 docs (parallel)", result))

        # Batch (50 docs parallel)
        batch_50 = [{"html": f"<h1>Doc {i}</h1><p>Content {i}</p>"} for i in range(50)]
        result = time_function(lambda: batch_render(batch_50), iterations=20)
        print(format_result("Batch 50 docs (parallel)", result))

        print()

    except ImportError:
        print("FastPDF not installed. Skipping FastPDF benchmarks.")
        print()

    # --- WeasyPrint comparison ---
    try:
        import weasyprint

        print("WeasyPrint (comparison):")
        print("-" * 80)

        result = time_function(
            lambda: weasyprint.HTML(string=SIMPLE_HTML).write_pdf(),
            iterations=20,
        )
        print(format_result("Simple HTML", result))

        result = time_function(
            lambda: weasyprint.HTML(string=STYLED_HTML).write_pdf(),
            iterations=20,
        )
        print(format_result("Styled HTML", result))

        result = time_function(
            lambda: weasyprint.HTML(string=TABLE_HTML).write_pdf(),
            iterations=10,
        )
        print(format_result("50-row Table", result))

        result = time_function(
            lambda: weasyprint.HTML(string=COMPLEX_HTML).write_pdf(),
            iterations=10,
        )
        print(format_result("Complex Report", result))

        print()

    except ImportError:
        print("WeasyPrint not installed. Skipping comparison.")
        print("Install with: pip install weasyprint")
        print()

    # --- Memory benchmark ---
    print("Memory Usage (approximate):")
    print("-" * 80)
    try:
        import tracemalloc

        tracemalloc.start()

        from fastpdf import render_pdf as fp_render

        # Warm up
        fp_render(SIMPLE_HTML)

        tracemalloc.reset_peak()
        for _ in range(100):
            fp_render(COMPLEX_HTML)
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()

        print(f"  FastPDF 100x Complex:  current={current/1024:.0f}KB  peak={peak/1024:.0f}KB")
    except Exception as e:
        print(f"  Memory tracking failed: {e}")

    print()
    print("=" * 80)
    print("Benchmark complete.")


if __name__ == "__main__":
    run_benchmarks()
