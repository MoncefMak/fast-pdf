#[allow(dead_code)]
mod at_page;
#[allow(dead_code)]
mod fragment;
pub mod pagination;

pub use ferropdf_core::layout::Page;
use ferropdf_core::{LayoutTree, PageConfig};

/// Paginate a layout tree into individual pages.
pub fn paginate(
    layout_tree: &LayoutTree,
    page_config: &PageConfig,
) -> ferropdf_core::Result<Vec<Page>> {
    let root = match &layout_tree.root {
        Some(r) => r,
        None => return Ok(vec![pagination::create_empty_page(page_config)]),
    };

    let pages = pagination::paginate(root, page_config);

    if pages.is_empty() {
        Ok(vec![pagination::create_empty_page(page_config)])
    } else {
        Ok(pages)
    }
}
