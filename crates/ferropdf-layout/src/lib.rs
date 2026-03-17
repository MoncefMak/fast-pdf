pub mod style_to_taffy;
pub mod text;
mod taffy_bridge;

use ferropdf_core::{Document, NodeId, NodeType, ComputedStyle, LayoutBox, LayoutTree, Rect, Insets, Length, Display};
use ferropdf_style::StyleTree;

/// Build a layout tree from a styled document using Taffy for layout computation.
pub fn layout(
    document: &Document,
    styles: &StyleTree,
    available_width: f32,
    available_height: f32,
) -> ferropdf_core::Result<LayoutTree> {
    taffy_bridge::build_layout(document, styles, available_width, available_height)
}
