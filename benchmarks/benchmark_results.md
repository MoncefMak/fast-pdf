## Performance Benchmarks

> Machine: `` — Linux 6.1.0-43-amd64  
> Python `3.11.2` — 2026-03-15

### Full pipeline: HTML to PDF

| Document | FerroPDF | WeasyPrint | wkhtmltopdf | Speedup vs WeasyPrint |
|---|---|---|---|---|
| **Simple HTML** | 264 µs +/-18 µs | 17.8 ms +/-1.1 ms | N/A | **67.4x faster** |
| **Styled HTML** | 352 µs +/-39 µs | 31.0 ms +/-2.5 ms | N/A | **88.2x faster** |
| **Table  10 rows** | 1.5 ms +/-220 µs | 110.7 ms +/-13.8 ms | N/A | **74.1x faster** |
| **Table  50 rows** | 5.0 ms +/-606 µs | 394.9 ms +/-48.0 ms | N/A | **78.9x faster** |
| **Table 100 rows** | 11.8 ms +/-2.1 ms | 745.1 ms +/-44.6 ms | N/A | **63.2x faster** |

> 1 warm-up run + N timed iterations. Mean +/- stdev shown.
> Reproduce: `python benchmarks/benchmark_comparison.py`