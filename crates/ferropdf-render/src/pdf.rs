use pdf_writer::{Pdf, Ref, Content, Finish, Name, Str, TextStr, Rect as PdfRect};
use ferropdf_core::PageConfig;
use crate::display_list::{DrawOp, PageDisplayList};
use crate::RenderOptions;

/// Write a complete PDF document from display lists.
pub fn write_pdf(
    pages: &[PageDisplayList],
    config: &PageConfig,
    opts: &RenderOptions,
) -> ferropdf_core::Result<Vec<u8>> {
    let mut pdf = Pdf::new();
    let mut ref_id = 1;
    let mut next_ref = || { let r = Ref::new(ref_id); ref_id += 1; r };

    let catalog_ref = next_ref();
    let page_tree_ref = next_ref();

    // Font reference (Helvetica built-in)
    let font_ref = next_ref();
    let font_bold_ref = next_ref();
    let font_italic_ref = next_ref();

    let (page_w, page_h) = config.size.dimensions_pt();

    // Collect page refs
    let mut page_refs = Vec::new();
    let mut content_refs = Vec::new();

    for _ in pages {
        page_refs.push(next_ref());
        content_refs.push(next_ref());
    }

    // Write catalog
    pdf.catalog(catalog_ref).pages(page_tree_ref);

    // Write page tree
    let mut page_tree = pdf.pages(page_tree_ref);
    page_tree.count(pages.len() as i32);
    page_tree.kids(page_refs.iter().copied());
    page_tree.finish();

    // Write each page
    for (i, display_list) in pages.iter().enumerate() {
        let page_ref = page_refs[i];
        let content_ref = content_refs[i];

        // Page dictionary
        let mut page = pdf.page(page_ref);
        page.parent(page_tree_ref);
        page.media_box(PdfRect::new(0.0, 0.0, page_w, page_h));

        // Resources with fonts
        let mut resources = page.resources();
        let mut fonts = resources.fonts();
        fonts.pair(Name(b"F1"), font_ref);
        fonts.pair(Name(b"F2"), font_bold_ref);
        fonts.pair(Name(b"F3"), font_italic_ref);
        fonts.finish();
        resources.finish();

        page.contents(content_ref);
        page.finish();

        // Content stream
        let mut content = Content::new();

        for op in &display_list.ops {
            match op {
                DrawOp::FillRect { rect, color, .. } => {
                    if !color.is_transparent() {
                        content.set_fill_rgb(color.r, color.g, color.b);
                        let pdf_y = page_h - rect.y - rect.height;
                        content.rect(rect.x, pdf_y, rect.width, rect.height);
                        content.fill_nonzero();
                    }
                }
                DrawOp::StrokeRect { rect, color, width, .. } => {
                    content.set_stroke_rgb(color.r, color.g, color.b);
                    content.set_line_width(*width);
                    let pdf_y = page_h - rect.y - rect.height;
                    content.rect(rect.x, pdf_y, rect.width.max(0.1), rect.height.max(0.1));
                    content.stroke();
                }
                DrawOp::DrawText { text, x, y, font_size, color, bold, italic, .. } => {
                    let font_name = if *bold {
                        "F2"
                    } else if *italic {
                        "F3"
                    } else {
                        "F1"
                    };

                    content.set_fill_rgb(color.r, color.g, color.b);
                    content.begin_text();
                    content.set_font(Name(font_name.as_bytes()), *font_size);
                    let pdf_y = page_h - *y;
                    content.next_line(*x, pdf_y);
                    content.show(Str(encode_pdf_text(text).as_bytes()));
                    content.end_text();
                }
                DrawOp::Save => { content.save_state(); }
                DrawOp::Restore => { content.restore_state(); }
                _ => {}
            }
        }

        let content_bytes = content.finish();
        pdf.stream(content_ref, &content_bytes);
    }

    // Write fonts (Type1 built-in fonts — no embedding needed)
    write_type1_font(&mut pdf, font_ref, "Helvetica");
    write_type1_font(&mut pdf, font_bold_ref, "Helvetica-Bold");
    write_type1_font(&mut pdf, font_italic_ref, "Helvetica-Oblique");

    // Write metadata
    let mut info = pdf.document_info(next_ref());
    info.producer(TextStr("ferropdf"));
    if let Some(ref title) = opts.title {
        info.title(TextStr(title));
    }
    if let Some(ref author) = opts.author {
        info.author(TextStr(author));
    }
    info.finish();

    Ok(pdf.finish())
}

fn write_type1_font(pdf: &mut Pdf, font_ref: Ref, base_font: &str) {
    let mut font = pdf.type1_font(font_ref);
    font.base_font(Name(base_font.as_bytes()));
    font.encoding_predefined(Name(b"WinAnsiEncoding"));
    font.finish();
}

fn encode_pdf_text(text: &str) -> String {
    text.chars().map(|c| {
        if c.is_ascii() {
            c
        } else {
            '?'
        }
    }).collect()
}
