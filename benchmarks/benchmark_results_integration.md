## FastAPI & Django Integration Benchmarks

> Machine: `` — Linux 6.1.0-43-amd64  
> Python `3.11.2` — 2026-03-16

### FastAPI — HTTP endpoint (full round-trip)

| Endpoint | Mean | Median | Min | p95 |
|---|---|---|---|---|
| `GET /simple.pdf  (plain HTML)` | 995 µs | 927 µs | 877 µs | 1.32 ms |
| `GET /styled.pdf  (CSS styled)` | 1.27 ms | 1.23 ms | 1.04 ms | 1.55 ms |
| `GET /invoice.pdf (10-row table)` | 1.87 ms | 1.85 ms | 1.73 ms | 2.21 ms |
| `GET /async.pdf   (async helper)` | 1.45 ms | 1.41 ms | 1.25 ms | 1.71 ms |
| `GET /tailwind.pdf (Tailwind CSS)` | 1.78 ms | 1.75 ms | 1.48 ms | 2.15 ms |

### FastAPI — `render_pdf_async` (asyncio, thread-pool dispatch)

| Operation | Mean | Median | Min | p95 |
|---|---|---|---|---|
| `render_pdf_async (simple)` | 304 µs | 297 µs | 240 µs | 361 µs |
| `render_pdf_async (styled)` | 390 µs | 376 µs | 369 µs | 461 µs |
| `render_pdf_async (invoice)` | 1.06 ms | 1.04 ms | 982 µs | 1.12 ms |
| `batch_render_async 5 docs` | 1.55 ms | 1.52 ms | 1.34 ms | 1.87 ms |
| `batch_render_async 10 docs` | 1.27 ms | 1.11 ms | 1.04 ms | 2.65 ms |

### Django — `render_pdf` + contrib helpers (in-process)

| Operation | Mean | Median | Min | p95 |
|---|---|---|---|---|
| `render_pdf (simple)` | 160 µs | 158 µs | 156 µs | 170 µs |
| `render_pdf (styled CSS)` | 310 µs | 304 µs | 300 µs | 343 µs |
| `render_pdf (invoice table)` | 940 µs | 930 µs | 912 µs | 985 µs |
| `render_pdf (Tailwind)` | 639 µs | 633 µs | 620 µs | 681 µs |
| `render_html_to_pdf_response (simple)` | 191 µs | 185 µs | 182 µs | 217 µs |
| `render_html_to_pdf_response (styled)` | 334 µs | 329 µs | 323 µs | 355 µs |
| `render_html_to_pdf_response (inline)` | 339 µs | 327 µs | 323 µs | 393 µs |

> 1 warm-up run + 30 timed iterations per case. Mean +/- stdev reported.
> Reproduce: `python benchmarks/benchmark_integrations.py`