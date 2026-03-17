use ferropdf_core::{LayoutBox, PageConfig, PageBreak, Rect};
use ferropdf_core::layout::Page;

/// Fragment a layout tree into pages based on available height.
pub fn fragment_into_pages(root: &LayoutBox, config: &PageConfig) -> Vec<Page> {
    let page_height = config.content_height();
    let mut pages: Vec<Page> = Vec::new();
    let mut current_content: Vec<LayoutBox> = Vec::new();
    let mut current_y = 0.0_f32;

    fragment_box(root, config, page_height, &mut pages, &mut current_content, &mut current_y);

    // Flush remaining content
    if !current_content.is_empty() {
        let page_num = pages.len() as u32 + 1;
        pages.push(Page {
            page_number: page_num,
            total_pages: 0,
            content: current_content,
            margin_boxes: Vec::new(),
        });
    }

    // Update total_pages
    let total = pages.len() as u32;
    for page in &mut pages {
        page.total_pages = total;
    }

    pages
}

fn fragment_box(
    layout_box: &LayoutBox,
    config: &PageConfig,
    page_height: f32,
    pages: &mut Vec<Page>,
    current_content: &mut Vec<LayoutBox>,
    current_y: &mut f32,
) {
    // Check for page-break-before: always
    if layout_box.style.page_break_before == PageBreak::Always && !current_content.is_empty() {
        flush_page(pages, current_content, current_y);
    }

    let box_height = layout_box.margin_box_height();

    // If the box fits on the current page, add it
    if *current_y + box_height <= page_height || current_content.is_empty() {
        current_content.push(layout_box.clone());
        *current_y += box_height;
    } else {
        // Start a new page
        flush_page(pages, current_content, current_y);
        current_content.push(layout_box.clone());
        *current_y += box_height;
    }

    // Check for page-break-after: always
    if layout_box.style.page_break_after == PageBreak::Always {
        flush_page(pages, current_content, current_y);
    }
}

fn flush_page(pages: &mut Vec<Page>, content: &mut Vec<LayoutBox>, current_y: &mut f32) {
    if content.is_empty() {
        return;
    }
    let page_num = pages.len() as u32 + 1;
    pages.push(Page {
        page_number: page_num,
        total_pages: 0,
        content: std::mem::take(content),
        margin_boxes: Vec::new(),
    });
    *current_y = 0.0;
}

pub fn create_empty_page(config: &PageConfig) -> Page {
    Page {
        page_number: 1,
        total_pages: 1,
        content: Vec::new(),
        margin_boxes: Vec::new(),
    }
}
