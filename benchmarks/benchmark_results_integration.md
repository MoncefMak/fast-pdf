## FastAPI & Django Integration Benchmarks

> Machine: `` — Linux 6.1.0-43-amd64  
> Python `3.11.2` — 2026-03-16

### FastAPI — HTTP endpoint (full round-trip)

| Endpoint | Mean | Median | Min | p95 |
|---|---|---|---|---|
| `GET /simple.pdf  (plain HTML)` | 1.53 ms | 1.49 ms | 1.18 ms | 1.89 ms |
| `GET /styled.pdf  (CSS styled)` | 2.33 ms | 2.26 ms | 1.85 ms | 2.70 ms |
| `GET /invoice.pdf (10-row table)` | 3.78 ms | 3.69 ms | 3.43 ms | 4.31 ms |
| `GET /async.pdf   (async helper)` | 2.12 ms | 2.06 ms | 1.57 ms | 2.67 ms |
| `GET /tailwind.pdf (Tailwind CSS)` | 2.24 ms | 2.13 ms | 1.62 ms | 2.83 ms |

### FastAPI — `render_pdf_async` (asyncio, thread-pool dispatch)

| Operation | Mean | Median | Min | p95 |
|---|---|---|---|---|
| `render_pdf_async (simple)` | 389 µs | 360 µs | 280 µs | 644 µs |
| `render_pdf_async (styled)` | 662 µs | 608 µs | 492 µs | 1.01 ms |
| `render_pdf_async (invoice)` | 1.55 ms | 1.50 ms | 1.32 ms | 1.83 ms |
| `batch_render_async 5 docs` | 2.25 ms | 2.21 ms | 1.64 ms | 3.77 ms |
| `batch_render_async 10 docs` | 1.61 ms | 1.55 ms | 1.16 ms | 2.51 ms |

### Django — `render_pdf` + contrib helpers (in-process)

| Operation | Mean | Median | Min | p95 |
|---|---|---|---|---|
| `render_pdf (simple)` | 215 µs | 204 µs | 189 µs | 295 µs |
| `render_pdf (styled CSS)` | 472 µs | 428 µs | 386 µs | 669 µs |
| `render_pdf (invoice table)` | 1.26 ms | 1.24 ms | 1.14 ms | 1.49 ms |
| `render_pdf (Tailwind)` | 746 µs | 834 µs | 520 µs | 919 µs |
| `render_html_to_pdf_response (simple)` | 352 µs | 330 µs | 304 µs | 457 µs |
| `render_html_to_pdf_response (styled)` | 631 µs | 661 µs | 413 µs | 769 µs |
| `render_html_to_pdf_response (inline)` | 435 µs | 433 µs | 398 µs | 493 µs |

### Multi-page rendering

| Document | Mean | Median | Min | p95 |
|---|---|---|---|---|
| `render_pdf (simple, 1 page)` | 203 µs | 192 µs | 183 µs | 311 µs |
| `render_pdf (multi-page, ~3 pages)` | 25.22 ms | 24.17 ms | 22.88 ms | 34.77 ms |
| `render_pdf (invoice, 1 page)` | 1.29 ms | 1.18 ms | 1.11 ms | 1.89 ms |
| `render_pdf_async (multi-page)` | 25.35 ms | 24.32 ms | 22.00 ms | 31.87 ms |

### Concurrent load (`render_pdf_async` via `asyncio.gather`)

| Concurrency | Mean total | p95 total | Throughput |
|---|---|---|---|
| 1 | 883 µs | 1.38 ms | 1132.1 req/s |
| 5 | 2.34 ms | 3.81 ms | 2136.6 req/s |
| 10 | 3.36 ms | 4.67 ms | 2979.1 req/s |
| 25 | 10.52 ms | 19.76 ms | 2376.7 req/s |
| 50 | 9.99 ms | 10.87 ms | 5006.0 req/s |

> 1 warm-up run + 30 timed iterations per case. Mean +/- stdev reported.
> Reproduce: `python benchmarks/benchmark_integrations.py`