mod display_list;
mod painter;
mod pdf;

use ferropdf_core::{PageConfig, PageSize, PageMargins};

/// Rendering options passed from Python bindings.
pub struct RenderOptions {
    pub page_size: String,
    pub margin: String,
    pub base_url: Option<String>,
    pub title: Option<String>,
    pub author: Option<String>,
}

/// Main entry point: render HTML string to PDF bytes.
pub fn render(html: &str, opts: &RenderOptions) -> ferropdf_core::Result<Vec<u8>> {
    // 1. Parse HTML
    let parse_result = ferropdf_parse::parse(html)?;

    // 2. Parse stylesheets (UA + inline)
    let ua_css = ferropdf_parse::css::UA_CSS;
    let mut stylesheets = vec![];
    for css_text in &parse_result.inline_styles {
        if let Ok(sheet) = ferropdf_parse::parse_stylesheet(css_text) {
            stylesheets.push(sheet);
        }
    }

    // 3. Build page config
    let page_config = PageConfig {
        size: PageSize::from_str(&opts.page_size),
        margins: PageMargins::from_css_str(&opts.margin),
        orientation: ferropdf_core::Orientation::Portrait,
    };

    // 4. Resolve styles
    let styles = ferropdf_style::resolve(
        &parse_result.document,
        &stylesheets,
        ua_css,
        page_config.content_width(),
    )?;

    // 5. Layout with Taffy
    let layout_tree = ferropdf_layout::layout(
        &parse_result.document,
        &styles,
        page_config.content_width(),
        page_config.content_height(),
    )?;

    // 6. Paginate
    let pages = ferropdf_page::paginate(&layout_tree, &page_config)?;

    // 7. Build display lists
    let display_lists: Vec<_> = pages.iter()
        .map(|page| painter::paint_page(page, &page_config))
        .collect();

    // 8. Write PDF
    let pdf_bytes = pdf::write_pdf(&display_lists, &page_config, opts)?;

    Ok(pdf_bytes)
}
