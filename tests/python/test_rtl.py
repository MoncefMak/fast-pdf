"""Tests pour le support RTL et les langues arabes/hébraïques."""
import pytest

try:
    from fastpdf import render_pdf, RenderOptions
    HAS_ENGINE = True
except ImportError:
    HAS_ENGINE = False

pytestmark = pytest.mark.skipif(not HAS_ENGINE, reason="Rust engine not built")


def test_arabic_text_no_panic():
    html = '<p dir="rtl">مرحبا بالعالم</p>'
    result = render_pdf(html)
    assert result[:4] == b"%PDF"


def test_hebrew_text_no_panic():
    html = '<p dir="rtl">שלום עולם</p>'
    result = render_pdf(html)
    assert result[:4] == b"%PDF"


def test_rtl_direction_css():
    html = '<html dir="rtl"><body><p>نص عربي</p></body></html>'
    css = "body { direction: rtl; } p { direction: rtl; }"
    result = render_pdf(html, css=css)
    assert result[:4] == b"%PDF"


def test_mixed_ltr_rtl():
    html = """
    <div>
        <p>English text left to right</p>
        <p dir="rtl">نص عربي من اليمين إلى اليسار</p>
        <p>More English text</p>
    </div>
    """
    result = render_pdf(html)
    assert result[:4] == b"%PDF"


def test_rtl_table():
    html = """
    <table dir="rtl">
        <tr><th>الاسم</th><th>القيمة</th></tr>
        <tr><td>عنصر أ</td><td>١٠٠</td></tr>
        <tr><td>عنصر ب</td><td>٢٠٠</td></tr>
    </table>
    """
    result = render_pdf(html)
    assert result[:4] == b"%PDF"


def test_rtl_auto_detection():
    """Arabic text should auto-detect as RTL even without explicit dir attribute."""
    html = "<p>مرحبا بالعالم، هذا نص عربي تلقائي</p>"
    result = render_pdf(html)
    assert result[:4] == b"%PDF"
