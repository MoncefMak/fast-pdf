"""Tests to validate that the GIL is released during batch_render."""
import threading
import time
import pytest

try:
    from fastpdf import batch_render, render_pdf
    HAS_ENGINE = True
except ImportError:
    HAS_ENGINE = False

pytestmark = pytest.mark.skipif(not HAS_ENGINE, reason="Rust engine not built")


def test_gil_released_during_batch():
    """The GIL must be released: a Python thread must make progress during batch."""
    counter = {"value": 0, "running": True}

    def increment():
        while counter["running"]:
            counter["value"] += 1
            time.sleep(0)  # yield

    # Use complex enough HTML so batch_render takes measurable time
    row = "".join(f"<tr><td>Item {j}</td><td>{j*10}</td></tr>" for j in range(20))
    docs = [
        {"html": f"<h1>Invoice #{i}</h1><table>{row}</table><p>Footer</p>"}
        for i in range(50)
    ]

    t = threading.Thread(target=increment)
    t.start()

    batch_render(docs)
    counter["running"] = False
    t.join(timeout=5)

    # If the GIL were held throughout, counter["value"] would be near 0
    assert counter["value"] > 5, (
        f"GIL was likely held during batch_render: "
        f"concurrent thread only progressed {counter['value']} times"
    )


def test_batch_returns_valid_pdfs():
    docs = [
        {"html": "<h1>Doc 1</h1>"},
        {"html": "<p>Paragraph content here.</p>"},
        {"html": "<table><tr><td>Cell</td></tr></table>"},
    ]
    results = batch_render(docs)
    assert len(results) == 3
    for pdf_bytes in results:
        assert pdf_bytes[:4] == b"%PDF", "Result is not a valid PDF"


def test_batch_empty_list():
    results = batch_render([])
    assert results == []


def test_batch_with_css():
    docs = [
        {"html": "<p class='red'>Text</p>", "css": ".red { color: #ff0000; }"},
    ]
    results = batch_render(docs)
    assert len(results) == 1
    assert results[0][:4] == b"%PDF"


def test_batch_single_document():
    docs = [{"html": "<h1>Single</h1>"}]
    results = batch_render(docs)
    assert len(results) == 1
    assert results[0][:4] == b"%PDF"
