"""
Tests fondamentaux — ces tests doivent TOUS passer avant de considérer
le projet fonctionnel.
"""
import ferropdf
import pytest

def pdf_is_valid(data: bytes) -> bool:
    return data[:4] == b"%PDF"

def count_pages(pdf: bytes) -> int:
    """Compter les pages dans un PDF de manière approximative."""
    return pdf.count(b"/Type /Page\n")


class TestModule:
    def test_import(self):
        assert hasattr(ferropdf, "Engine")
        assert hasattr(ferropdf, "Options")
        assert hasattr(ferropdf, "from_html")
        assert hasattr(ferropdf, "from_file")
        assert hasattr(ferropdf, "__version__")

    def test_from_html_minimal(self):
        pdf = ferropdf.from_html("<p>Hello</p>")
        assert pdf_is_valid(pdf)

    def test_from_html_with_styles(self):
        html = open("tests/fixtures/simple.html").read()
        pdf  = ferropdf.from_html(html)
        assert pdf_is_valid(pdf)

    def test_from_file(self):
        pdf = ferropdf.from_file("tests/fixtures/simple.html")
        assert pdf_is_valid(pdf)

    def test_write_pdf(self, tmp_path):
        out = tmp_path / "out.pdf"
        ferropdf.write_pdf("<p>Test</p>", str(out))
        assert out.exists()
        assert pdf_is_valid(out.read_bytes())

    def test_empty_html(self):
        pdf = ferropdf.from_html("")
        assert pdf_is_valid(pdf)

    def test_malformed_html_no_crash(self):
        cases = [
            "<p>Unclosed",
            "<div><p>Double unclosed",
            "Texte brut sans balises",
            "<script>alert(1)</script><p>xss</p>",
        ]
        for html in cases:
            assert pdf_is_valid(ferropdf.from_html(html)), f"Crash sur: {html!r}"


class TestOptions:
    def test_default(self):
        opts = ferropdf.Options()
        pdf  = ferropdf.from_html("<p>Test</p>", options=opts)
        assert pdf_is_valid(pdf)

    def test_a4(self):
        opts = ferropdf.Options(page_size="A4", margin="20mm")
        assert pdf_is_valid(ferropdf.from_html("<p>A4</p>", options=opts))

    def test_letter(self):
        opts = ferropdf.Options(page_size="Letter")
        assert pdf_is_valid(ferropdf.from_html("<p>Letter</p>", options=opts))

    def test_a3(self):
        opts = ferropdf.Options(page_size="A3")
        assert pdf_is_valid(ferropdf.from_html("<p>A3</p>", options=opts))


class TestLayout:
    def test_width_100_percent(self):
        html = """
        <div style="width:500px">
          <table style="width:100%">
            <tr><td>Col 1</td><td>Col 2</td><td>Col 3</td></tr>
            <tr><td>Data</td><td>Data</td><td>Data</td></tr>
          </table>
        </div>
        """
        pdf = ferropdf.from_html(html)
        assert pdf_is_valid(pdf)
        assert count_pages(pdf) <= 2

    def test_no_double_padding(self):
        html = """
        <div style="width:400px; padding:20px; background:#eee">
          <div style="width:100%; background:#ccc">
            <p style="padding:10px">Texte imbriqué</p>
          </div>
        </div>
        """
        pdf = ferropdf.from_html(html)
        assert pdf_is_valid(pdf)
        assert count_pages(pdf) == 1

    def test_flex_row(self):
        html = """
        <div style="display:flex; width:600px; gap:20px">
          <div style="flex:1; background:red; min-height:50px">A</div>
          <div style="flex:1; background:blue; min-height:50px">B</div>
          <div style="flex:1; background:green; min-height:50px">C</div>
        </div>
        """
        assert pdf_is_valid(ferropdf.from_html(html))

    def test_invoice_page_count(self):
        html = open("tests/fixtures/invoice.html").read()
        pdf  = ferropdf.from_html(html)
        assert pdf_is_valid(pdf)
        pages = count_pages(pdf)
        assert pages <= 2, f"Invoice : {pages} pages détectées (max 2)"


class TestEngine:
    def test_reusable(self):
        engine = ferropdf.Engine()
        r1 = engine.render("<p>Doc 1</p>")
        r2 = engine.render("<p>Doc 2</p>")
        assert pdf_is_valid(r1)
        assert pdf_is_valid(r2)
        assert r1 != r2

    def test_render_file(self, tmp_path):
        f = tmp_path / "page.html"
        f.write_text("<h1>From file</h1>", encoding="utf-8")
        engine = ferropdf.Engine()
        assert pdf_is_valid(engine.render_file(str(f)))


class TestErrors:
    def test_hierarchy(self):
        assert issubclass(ferropdf.ParseError,  ferropdf.FerroError)
        assert issubclass(ferropdf.LayoutError, ferropdf.FerroError)
        assert issubclass(ferropdf.FontError,   ferropdf.FerroError)
        assert issubclass(ferropdf.RenderError, ferropdf.FerroError)

    def test_ferro_error_is_exception(self):
        assert issubclass(ferropdf.FerroError, Exception)
