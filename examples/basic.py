"""
Exemple basique — génère un PDF simple dans output/
"""
import ferropdf
from pathlib import Path

output_dir = Path(__file__).parent.parent / "output"
output_dir.mkdir(exist_ok=True)

# 1. PDF minimal
ferropdf.write_pdf("<h1>Hello ferropdf!</h1>", str(output_dir / "hello.pdf"))
print(f"✓ {output_dir / 'hello.pdf'}")

# 2. PDF avec styles
html = """
<html>
<head><style>
  body { font-family: sans-serif; margin: 40px; }
  h1 { color: #1e40af; border-bottom: 2px solid #1e40af; padding-bottom: 10px; }
  .card { background: #f3f4f6; padding: 20px; border-radius: 8px; margin-top: 20px; }
  .card p { margin: 8px 0; }
</style></head>
<body>
  <h1>Rapport de test</h1>
  <div class="card">
    <p><strong>Projet :</strong> ferropdf</p>
    <p><strong>Version :</strong> 0.1.0</p>
    <p><strong>Status :</strong> Tous les tests passent</p>
  </div>
</body>
</html>
"""
ferropdf.write_pdf(html, str(output_dir / "styled.pdf"))
print(f"✓ {output_dir / 'styled.pdf'}")

# 3. Facture
invoice = open(Path(__file__).parent.parent / "tests" / "fixtures" / "invoice.html").read()
ferropdf.write_pdf(invoice, str(output_dir / "invoice.pdf"))
print(f"✓ {output_dir / 'invoice.pdf'}")

print(f"\n📄 PDFs générés dans {output_dir}/")
