//! Pagination — splitting a layout tree into pages for PDF output.

use super::box_model::LayoutBox;

/// Standard page sizes in CSS pixels (at 96 DPI).
#[derive(Debug, Clone, Copy)]
pub struct PageSize {
    pub width: f64,
    pub height: f64,
}

impl PageSize {
    /// A4 paper (210mm × 297mm).
    pub fn a4() -> Self {
        Self {
            width: 210.0 * 96.0 / 25.4,  // 793.7px
            height: 297.0 * 96.0 / 25.4, // 1122.5px
        }
    }

    /// US Letter (8.5" × 11").
    pub fn letter() -> Self {
        Self {
            width: 8.5 * 96.0,  // 816px
            height: 11.0 * 96.0, // 1056px
        }
    }

    /// US Legal (8.5" × 14").
    pub fn legal() -> Self {
        Self {
            width: 8.5 * 96.0,
            height: 14.0 * 96.0,
        }
    }

    /// Custom page size.
    pub fn custom(width_mm: f64, height_mm: f64) -> Self {
        Self {
            width: width_mm * 96.0 / 25.4,
            height: height_mm * 96.0 / 25.4,
        }
    }

    /// Get dimensions in millimeters.
    pub fn to_mm(&self) -> (f64, f64) {
        (self.width * 25.4 / 96.0, self.height * 25.4 / 96.0)
    }

    /// Get dimensions in points (1pt = 1/72 inch).
    pub fn to_pt(&self) -> (f64, f64) {
        (self.width * 72.0 / 96.0, self.height * 72.0 / 96.0)
    }
}

/// Page layout configuration.
#[derive(Debug, Clone)]
pub struct PageLayout {
    pub size: PageSize,
    pub margin_top: f64,
    pub margin_right: f64,
    pub margin_bottom: f64,
    pub margin_left: f64,
    /// Header content template (optional).
    pub header_html: Option<String>,
    /// Footer content template (optional).
    pub footer_html: Option<String>,
    /// Header height reservation.
    pub header_height: f64,
    /// Footer height reservation.
    pub footer_height: f64,
}

impl PageLayout {
    pub fn new(size: PageSize) -> Self {
        Self {
            size,
            margin_top: 72.0,    // 1 inch
            margin_right: 72.0,
            margin_bottom: 72.0,
            margin_left: 72.0,
            header_html: None,
            footer_html: None,
            header_height: 0.0,
            footer_height: 0.0,
        }
    }

    /// The content area width (page width minus left/right margins).
    pub fn content_width(&self) -> f64 {
        self.size.width - self.margin_left - self.margin_right
    }

    /// The content area height (page height minus top/bottom margins and header/footer).
    pub fn content_height(&self) -> f64 {
        self.size.height
            - self.margin_top
            - self.margin_bottom
            - self.header_height
            - self.footer_height
    }

    /// The y-coordinate where content starts.
    pub fn content_top(&self) -> f64 {
        self.margin_top + self.header_height
    }

    /// The x-coordinate where content starts.
    pub fn content_left(&self) -> f64 {
        self.margin_left
    }

    pub fn with_margins(mut self, top: f64, right: f64, bottom: f64, left: f64) -> Self {
        self.margin_top = top;
        self.margin_right = right;
        self.margin_bottom = bottom;
        self.margin_left = left;
        self
    }
}

impl Default for PageLayout {
    fn default() -> Self {
        Self::new(PageSize::a4())
    }
}

/// A single page containing layout boxes.
#[derive(Debug, Clone)]
pub struct Page {
    pub number: usize,
    pub layout: PageLayout,
    pub content: Vec<LayoutBox>,
}

impl Page {
    pub fn new(number: usize, layout: PageLayout) -> Self {
        Self {
            number,
            layout,
            content: Vec::new(),
        }
    }
}

/// Paginator splits a continuous layout into pages.
pub struct Paginator {
    pub page_layout: PageLayout,
}

impl Paginator {
    pub fn new(layout: PageLayout) -> Self {
        Self {
            page_layout: layout,
        }
    }

    /// Split a root layout box into pages.
    pub fn paginate(&self, root: &LayoutBox) -> Vec<Page> {
        let mut pages = Vec::new();
        let mut current_page = Page::new(1, self.page_layout.clone());
        let content_height = self.page_layout.content_height();
        let mut y_offset = 0.0;

        self.split_into_pages(root, &mut pages, &mut current_page, &mut y_offset, content_height);

        // Add the last page if it has content
        if !current_page.content.is_empty() {
            pages.push(current_page);
        }

        // Ensure at least one page
        if pages.is_empty() {
            pages.push(Page::new(1, self.page_layout.clone()));
        }

        // Renumber pages
        for (i, page) in pages.iter_mut().enumerate() {
            page.number = i + 1;
        }

        pages
    }

    fn split_into_pages(
        &self,
        layout_box: &LayoutBox,
        pages: &mut Vec<Page>,
        current_page: &mut Page,
        y_offset: &mut f64,
        page_height: f64,
    ) {
        // Check for page break before
        if layout_box.page_break_before && !current_page.content.is_empty() {
            let page_num = pages.len() + 2;
            let completed = std::mem::replace(
                current_page,
                Page::new(page_num, self.page_layout.clone()),
            );
            pages.push(completed);
            *y_offset = 0.0;
        }

        let box_height = layout_box.dimensions.margin_box().height;

        // Check if the box fits on the current page
        if *y_offset + box_height > page_height && *y_offset > 0.0 {
            // Start a new page
            let page_num = pages.len() + 2;
            let completed = std::mem::replace(
                current_page,
                Page::new(page_num, self.page_layout.clone()),
            );
            pages.push(completed);
            *y_offset = 0.0;
        }

        // If the box wants to avoid breaking inside and fits on a fresh page,
        // keep it together
        if layout_box.avoid_break_inside && box_height <= page_height {
            let mut adjusted_box = layout_box.clone();
            adjusted_box.dimensions.content.y =
                self.page_layout.content_top() + *y_offset;
            current_page.content.push(adjusted_box);
            *y_offset += box_height;
        } else if box_height > page_height && !layout_box.children.is_empty() {
            // Box is taller than a page — split children across pages
            for child in &layout_box.children {
                self.split_into_pages(child, pages, current_page, y_offset, page_height);
            }
        } else {
            // Box fits on current page
            let mut adjusted_box = layout_box.clone();
            adjusted_box.dimensions.content.y =
                self.page_layout.content_top() + *y_offset;
            current_page.content.push(adjusted_box);
            *y_offset += box_height;
        }

        // Check for page break after
        if layout_box.page_break_after {
            let page_num = pages.len() + 2;
            let completed = std::mem::replace(
                current_page,
                Page::new(page_num, self.page_layout.clone()),
            );
            pages.push(completed);
            *y_offset = 0.0;
        }
    }
}
