"""Tests de performance — détectent les régressions."""
import time
import pytest

try:
    from fastpdf import render_pdf, batch_render, RenderOptions
    HAS_ENGINE = True
except ImportError:
    HAS_ENGINE = False

pytestmark = pytest.mark.skipif(not HAS_ENGINE, reason="Rust engine not built")

SIMPLE_HTML = "<h1>Hello World</h1><p>A simple test paragraph.</p>"
MEDIUM_HTML = (
    "<html><body><h1>Report Title</h1>"
    "<p>Introduction paragraph with some content.</p>"
    "<table><tr><th>Name</th><th>Value</th><th>Status</th></tr>"
    + "".join(
        f"<tr><td>Item {i}</td><td>{i * 10}</td><td>Active</td></tr>"
        for i in range(25)
    )
    + "</table><p>Conclusion paragraph.</p></body></html>"
)


def test_simple_render_under_500ms():
    """A simple render must complete in under 500ms (CI-safe threshold)."""
    # Warm up
    render_pdf(SIMPLE_HTML)

    times = []
    for _ in range(5):
        start = time.perf_counter()
        render_pdf(SIMPLE_HTML)
        times.append(time.perf_counter() - start)

    avg_ms = (sum(times) / len(times)) * 1000
    assert avg_ms < 500, f"Simple render too slow: {avg_ms:.1f}ms (threshold: 500ms)"


def test_batch_parallel_speedup():
    """batch_render should be faster than sequential renders."""
    docs = [{"html": f"<h1>Doc {i}</h1><p>Content paragraph {i}</p>"} for i in range(8)]

    # Warm up
    render_pdf(docs[0]["html"])

    # Sequential
    start = time.perf_counter()
    for d in docs:
        render_pdf(d["html"])
    sequential_time = time.perf_counter() - start

    # Parallel
    start = time.perf_counter()
    batch_render(docs)
    parallel_time = time.perf_counter() - start

    speedup = sequential_time / parallel_time if parallel_time > 0 else 0

    # On multi-core machines, expect at least 1.3x speedup.
    # If GIL is held incorrectly, speedup ≈ 1.0 or worse.
    assert speedup >= 1.3, (
        f"Insufficient speedup: {speedup:.2f}x "
        f"(sequential={sequential_time * 1000:.0f}ms, "
        f"parallel={parallel_time * 1000:.0f}ms) — "
        "Check that py.allow_threads() is in place (action S1-1)"
    )


def test_medium_document_under_2s():
    """A medium-sized document should render in under 2 seconds."""
    render_pdf(MEDIUM_HTML)  # warm up

    start = time.perf_counter()
    result = render_pdf(MEDIUM_HTML)
    elapsed_ms = (time.perf_counter() - start) * 1000

    assert result[:4] == b"%PDF"
    assert elapsed_ms < 2000, f"Medium document too slow: {elapsed_ms:.0f}ms (threshold: 2000ms)"
