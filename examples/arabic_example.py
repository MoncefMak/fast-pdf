"""
FastPDF Arabic / RTL Language Support Example
==============================================

Demonstrates:
- Arabic text rendering with proper glyph shaping
- Right-to-left (RTL) text direction  
- Mixed Arabic + English (bidirectional) text
- Custom TTF font embedding (DejaVu Sans with Arabic support)

Run: python examples/arabic_example.py
"""

import os
from fastpdf import PdfEngine, RenderOptions

# Use DejaVu Sans (ships with most Linux distros, has Arabic GSUB tables)
ARABIC_FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
ARABIC_FONT_BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "output")
os.makedirs(OUTPUT_DIR, exist_ok=True)


def example_arabic_basic():
    """Basic Arabic text rendering with RTL direction."""
    
    html = """
    <html>
    <head>
        <style>
            body {
                font-family: DejaVuSans;
                font-size: 14px;
                line-height: 1.6;
                color: #1a1a1a;
                direction: rtl;
            }
            h1 {
                font-size: 28px;
                color: #1e3a5f;
                border-bottom: 3px solid #1e3a5f;
                padding-bottom: 12px;
                margin-bottom: 20px;
            }
            h2 {
                font-size: 20px;
                color: #2d5f8a;
                margin-top: 30px;
                margin-bottom: 10px;
            }
            .content {
                margin: 15px 0;
            }
            .highlight {
                background-color: #e8f4f8;
                padding: 15px;
                margin: 15px 0;
            }
            table {
                width: 100%;
                border-collapse: collapse;
                margin: 20px 0;
            }
            th {
                background-color: #1e3a5f;
                color: white;
                padding: 10px;
                text-align: right;
            }
            td {
                padding: 8px 10px;
                border-bottom: 1px solid #ddd;
            }
        </style>
    </head>
    <body>
        <h1>مرحبا بكم في FastPDF</h1>
        
        <div class="content">
            <p>هذا مثال على دعم اللغة العربية في مكتبة FastPDF.</p>
            <p>المكتبة تدعم الآن النصوص العربية مع تشكيل الحروف بشكل صحيح.</p>
        </div>
        
        <h2>المميزات</h2>
        <div class="highlight">
            <p>تشكيل النصوص العربية باستخدام محرك HarfBuzz</p>
            <p>دعم الاتجاه من اليمين إلى اليسار</p>
            <p>دعم النصوص ثنائية الاتجاه</p>
            <p>تضمين خطوط TrueType مخصصة</p>
        </div>

        <h2>جدول المعلومات</h2>
        <table>
            <tr>
                <th>الميزة</th>
                <th>الحالة</th>
            </tr>
            <tr>
                <td>تشكيل عربي</td>
                <td>مدعوم</td>
            </tr>
            <tr>
                <td>اتجاه RTL</td>
                <td>مدعوم</td>
            </tr>
            <tr>
                <td>نصوص مختلطة</td>
                <td>مدعوم</td>
            </tr>
        </table>
    </body>
    </html>
    """

    engine = PdfEngine()
    engine.register_font("DejaVuSans", ARABIC_FONT, weight=400)
    engine.register_font("DejaVuSans", ARABIC_FONT_BOLD, weight=700)

    options = RenderOptions(page_size="A4")
    pdf_doc = engine.render(html, options=options)

    output_path = os.path.join(OUTPUT_DIR, "arabic_basic.pdf")
    pdf_doc.save(output_path)
    pdf_bytes = pdf_doc.to_bytes()
    print(f"✓ Arabic Basic: {len(pdf_bytes):,} bytes → {output_path}")


def example_arabic_mixed():
    """Mixed Arabic and English (bidirectional) text."""
    
    html = """
    <html>
    <head>
        <style>
            body {
                font-family: DejaVuSans;
                font-size: 14px;
                line-height: 1.8;
                color: #2c3e50;
            }
            h1 {
                font-size: 26px;
                color: #2c3e50;
                text-align: center;
                margin-bottom: 25px;
            }
            .section {
                margin: 20px 0;
                padding: 15px;
                background-color: #f8f9fa;
            }
            .section-title {
                font-size: 18px;
                font-weight: bold;
                color: #34495e;
                margin-bottom: 10px;
            }
            .rtl {
                direction: rtl;
            }
            .ltr {
                direction: ltr;
            }
        </style>
    </head>
    <body>
        <h1>Bidirectional Text Demo / عرض النصوص ثنائية الاتجاه</h1>
        
        <div class="section ltr">
            <div class="section-title">English (LTR)</div>
            <p>FastPDF now supports Arabic text rendering with proper OpenType shaping.</p>
            <p>The library uses rustybuzz (HarfBuzz port) for text shaping and unicode-bidi for bidirectional text reordering.</p>
        </div>
        
        <div class="section rtl">
            <div class="section-title">العربية (RTL)</div>
            <p>مكتبة FastPDF تدعم الآن عرض النصوص العربية مع تشكيل الحروف الصحيح.</p>
            <p>تستخدم المكتبة محرك HarfBuzz لتشكيل النصوص ومعيار Unicode BiDi لإعادة ترتيب النصوص.</p>
        </div>

        <div class="section ltr">
            <div class="section-title">Mixed / مختلط</div>
            <p>The word for "library" in Arabic is: مكتبة</p>
            <p>PDF stands for Portable Document Format</p>
        </div>

        <div class="section rtl">
            <div class="section-title">أرقام ونصوص</div>
            <p>عدد الصفحات: 42 صفحة</p>
            <p>الإصدار: 1.0.0</p>
            <p>تاريخ الإصدار: 2025</p>
        </div>
    </body>
    </html>
    """

    engine = PdfEngine()
    engine.register_font("DejaVuSans", ARABIC_FONT, weight=400)
    engine.register_font("DejaVuSans", ARABIC_FONT_BOLD, weight=700)

    options = RenderOptions(page_size="A4")
    pdf_doc = engine.render(html, options=options)

    output_path = os.path.join(OUTPUT_DIR, "arabic_mixed.pdf")
    pdf_doc.save(output_path)
    pdf_bytes = pdf_doc.to_bytes()
    print(f"✓ Arabic Mixed: {len(pdf_bytes):,} bytes → {output_path}")


def example_arabic_invoice():
    """Arabic invoice / فاتورة عربية."""
    
    html = """
    <html>
    <head>
        <style>
            body {
                font-family: DejaVuSans;
                font-size: 13px;
                color: #333;
                direction: rtl;
            }
            .header {
                background-color: #1a365d;
                color: white;
                padding: 25px;
                margin-bottom: 30px;
            }
            .header h1 {
                font-size: 24px;
                margin-bottom: 5px;
            }
            .header p {
                font-size: 12px;
                color: #bee3f8;
            }
            .info-grid {
                display: flex;
                margin-bottom: 25px;
            }
            .info-box {
                padding: 15px;
                background-color: #f7fafc;
                flex-grow: 1;
            }
            .info-box h3 {
                font-size: 14px;
                color: #1a365d;
                margin-bottom: 8px;
            }
            table {
                width: 100%;
                border-collapse: collapse;
                margin: 20px 0;
            }
            th {
                background-color: #2d3748;
                color: white;
                padding: 10px;
                text-align: right;
                font-size: 12px;
            }
            td {
                padding: 10px;
                border-bottom: 1px solid #e2e8f0;
                font-size: 12px;
            }
            .total-row {
                background-color: #edf2f7;
                font-weight: bold;
            }
            .footer {
                margin-top: 30px;
                padding-top: 15px;
                border-top: 2px solid #e2e8f0;
                font-size: 11px;
                color: #718096;
            }
        </style>
    </head>
    <body>
        <div class="header">
            <h1>فاتورة</h1>
            <p>رقم الفاتورة: INV-2025-001</p>
        </div>

        <div class="info-grid">
            <div class="info-box">
                <h3>معلومات الشركة</h3>
                <p>شركة التقنيات المتقدمة</p>
                <p>الرياض، المملكة العربية السعودية</p>
            </div>
            <div class="info-box">
                <h3>معلومات العميل</h3>
                <p>شركة الحلول الرقمية</p>
                <p>جدة، المملكة العربية السعودية</p>
            </div>
        </div>

        <table>
            <tr>
                <th>الوصف</th>
                <th>الكمية</th>
                <th>السعر</th>
                <th>المجموع</th>
            </tr>
            <tr>
                <td>تطوير موقع إلكتروني</td>
                <td>1</td>
                <td>15,000 ر.س</td>
                <td>15,000 ر.س</td>
            </tr>
            <tr>
                <td>تصميم واجهة المستخدم</td>
                <td>1</td>
                <td>8,000 ر.س</td>
                <td>8,000 ر.س</td>
            </tr>
            <tr>
                <td>استضافة سنوية</td>
                <td>1</td>
                <td>2,500 ر.س</td>
                <td>2,500 ر.س</td>
            </tr>
            <tr class="total-row">
                <td>المجموع الكلي</td>
                <td></td>
                <td></td>
                <td>25,500 ر.س</td>
            </tr>
        </table>

        <div class="footer">
            <p>شروط الدفع: خلال 30 يوم من تاريخ الفاتورة</p>
            <p>شكرا لتعاملكم معنا</p>
        </div>
    </body>
    </html>
    """

    engine = PdfEngine()
    engine.register_font("DejaVuSans", ARABIC_FONT, weight=400)
    engine.register_font("DejaVuSans", ARABIC_FONT_BOLD, weight=700)

    options = RenderOptions(page_size="A4")
    pdf_doc = engine.render(html, options=options)

    output_path = os.path.join(OUTPUT_DIR, "arabic_invoice.pdf")
    pdf_doc.save(output_path)
    pdf_bytes = pdf_doc.to_bytes()
    print(f"✓ Arabic Invoice: {len(pdf_bytes):,} bytes → {output_path}")


if __name__ == "__main__":
    print("FastPDF Arabic Language Support Examples")
    print("=" * 45)
    
    if not os.path.exists(ARABIC_FONT):
        print(f"⚠ Arabic font not found: {ARABIC_FONT}")
        print("  Install DejaVu fonts: sudo apt install fonts-dejavu-core")
    else:
        example_arabic_basic()
        example_arabic_mixed()
        example_arabic_invoice()
        print("\nAll Arabic examples generated successfully!")
