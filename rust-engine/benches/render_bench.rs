use criterion::{black_box, criterion_group, criterion_main, Criterion};
use fastpdf_engine::html::HtmlParser;
use fastpdf_engine::css::Stylesheet;

fn bench_html_parse(c: &mut Criterion) {
    let parser = HtmlParser::new();
    let html = "<html><body><h1>Test</h1><p>Paragraph with <strong>bold</strong> text.</p><ul><li>Item 1</li><li>Item 2</li></ul></body></html>";

    c.bench_function("html_parse_simple", |b| {
        b.iter(|| {
            let _ = parser.parse(black_box(html));
        })
    });
}

fn bench_css_parse(c: &mut Criterion) {
    let css = r#"
        body { font-family: Helvetica, sans-serif; color: #333; font-size: 12pt; }
        h1 { color: #1a56db; border-bottom: 2px solid #1a56db; padding-bottom: 10px; }
        p { line-height: 1.6; margin: 10px 0; }
        table { width: 100%; border-collapse: collapse; }
        th { background-color: #1a56db; color: white; padding: 12px; }
        td { padding: 10px 12px; border-bottom: 1px solid #e5e7eb; }
    "#;

    c.bench_function("css_parse_basic", |b| {
        b.iter(|| {
            let parser = fastpdf_engine::css::CssParser::new();
            let _ = parser.parse(black_box(css));
        })
    });
}

fn bench_default_stylesheet(c: &mut Criterion) {
    c.bench_function("default_stylesheet", |b| {
        b.iter(|| {
            black_box(Stylesheet::default_stylesheet());
        })
    });
}

criterion_group!(benches, bench_html_parse, bench_css_parse, bench_default_stylesheet);
criterion_main!(benches);
