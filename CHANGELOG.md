# Changelog

## 0.1.0 (2026-03-15)

### Features

- **HTML/CSS rendering** — Full HTML5 parsing (html5ever), CSS3 styling with selector matching and inheritance
- **Layout engine** — Block, inline (IFC with word-wrap), flexbox, and table layout
- **Pagination** — Automatic page breaks, explicit `page-break-before/after`, widows/orphans
- **Tailwind CSS** — Utility class resolution without a build step
- **Template rendering** — Jinja2 templates with context variables
- **Custom fonts** — Register and embed TrueType/OpenType fonts
- **Arabic / RTL support** — HarfBuzz text shaping (rustybuzz), Unicode BiDi reordering, direction-aware alignment
- **Django integration** — `render_to_pdf_response()`, `PdfView` CBV mixin, `PdfMiddleware`
- **FastAPI integration** — `PdfResponse`, async rendering helpers
- **Batch rendering** — Parallel PDF generation via Rayon
- **Page sizes** — A4, Letter, Legal, Tabloid, A3, A5, and custom `(width_mm, height_mm)`
