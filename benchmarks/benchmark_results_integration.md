## FastAPI & Django Integration Benchmarks

> Machine: `` — Linux 6.1.0-43-amd64  
> Python `3.11.2` — 2026-03-16

### FastAPI — HTTP endpoint (full round-trip)

| Endpoint | Mean | Median | Min | p95 |
|---|---|---|---|---|
| `GET /simple.pdf  (plain HTML)` | 1.61 ms | 1.54 ms | 1.28 ms | 2.02 ms |
| `GET /styled.pdf  (CSS styled)` | 1.61 ms | 1.62 ms | 1.30 ms | 1.92 ms |
| `GET /invoice.pdf (10-row table)` | 2.40 ms | 2.40 ms | 2.02 ms | 2.73 ms |
| `GET /async.pdf   (async helper)` | 1.88 ms | 1.84 ms | 1.49 ms | 2.48 ms |
| `GET /tailwind.pdf (Tailwind CSS)` | 2.04 ms | 1.93 ms | 1.69 ms | 2.55 ms |

### FastAPI — `render_pdf_async` (asyncio, thread-pool dispatch)

| Operation | Mean | Median | Min | p95 |
|---|---|---|---|---|
| `render_pdf_async (simple)` | 352 µs | 348 µs | 244 µs | 442 µs |
| `render_pdf_async (styled)` | 576 µs | 558 µs | 385 µs | 845 µs |
| `render_pdf_async (invoice)` | 1.37 ms | 1.28 ms | 1.07 ms | 1.82 ms |
| `batch_render_async 5 docs` | 1.60 ms | 1.58 ms | 1.30 ms | 2.03 ms |
| `batch_render_async 10 docs` | 1.49 ms | 1.36 ms | 1.06 ms | 2.47 ms |

### Django — `render_pdf` + contrib helpers (in-process)

| Operation | Mean | Median | Min | p95 |
|---|---|---|---|---|
| `render_pdf (simple)` | 179 µs | 165 µs | 156 µs | 242 µs |
| `render_pdf (styled CSS)` | 318 µs | 307 µs | 297 µs | 392 µs |
| `render_pdf (invoice table)` | 992 µs | 970 µs | 904 µs | 1.17 ms |
| `render_pdf (Tailwind)` | 722 µs | 671 µs | 618 µs | 1.04 ms |
| `render_html_to_pdf_response (simple)` | 200 µs | 190 µs | 181 µs | 266 µs |
| `render_html_to_pdf_response (styled)` | 339 µs | 325 µs | 318 µs | 388 µs |
| `render_html_to_pdf_response (inline)` | 362 µs | 342 µs | 317 µs | 445 µs |

### Multi-page rendering

| Document | Mean | Median | Min | p95 |
|---|---|---|---|---|
| `render_pdf (simple, 1 page)` | 166 µs | 159 µs | 157 µs | 219 µs |
| `render_pdf (multi-page, ~3 pages)` | 18.81 ms | 18.64 ms | 17.23 ms | 21.22 ms |
| `render_pdf (invoice, 1 page)` | 1.12 ms | 1.09 ms | 945 µs | 1.42 ms |
| `render_pdf_async (multi-page)` | 21.77 ms | 19.19 ms | 18.00 ms | 35.67 ms |

### Concurrent load (`render_pdf_async` via `asyncio.gather`)

| Concurrency | Mean total | p95 total | Throughput |
|---|---|---|---|
| 1 | 1.29 ms | 2.72 ms | 773.9 req/s |
| 5 | 5.28 ms | 14.26 ms | 946.9 req/s |
| 10 | 7.06 ms | 7.67 ms | 1416.5 req/s |
| 25 | 16.04 ms | 21.26 ms | 1558.7 req/s |
| 50 | 20.00 ms | 23.68 ms | 2500.6 req/s |

> 1 warm-up run + 30 timed iterations per case. Mean +/- stdev reported.
> Reproduce: `python benchmarks/benchmark_integrations.py`