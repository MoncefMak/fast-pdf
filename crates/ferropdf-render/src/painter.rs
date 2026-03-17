use ferropdf_core::{LayoutBox, PageConfig, Color, Rect, BorderStyle};
use ferropdf_core::layout::Page;
use crate::display_list::{DrawOp, PageDisplayList};

/// Paint a page into a display list.
pub fn paint_page(page: &Page, config: &PageConfig) -> PageDisplayList {
    let mut ops = Vec::new();

    for layout_box in &page.content {
        paint_box(layout_box, &mut ops, config.margins.left, config.margins.top);
    }

    PageDisplayList {
        ops,
        page_number: page.page_number,
        total_pages: page.total_pages,
    }
}

fn paint_box(layout_box: &LayoutBox, ops: &mut Vec<DrawOp>, offset_x: f32, offset_y: f32) {
    let style = &layout_box.style;

    if !style.visibility {
        return;
    }

    let border_box = layout_box.border_box();
    let x = border_box.x + offset_x;
    let y = border_box.y + offset_y;
    let rect = Rect::new(x, y, border_box.width, border_box.height);

    // Background
    if !style.background_color.is_transparent() {
        ops.push(DrawOp::FillRect {
            rect,
            color: style.background_color,
            border_radius: style.border_radius.to_array(),
        });
    }

    // Borders
    paint_borders(layout_box, ops, rect);

    // Text content
    if let Some(ref text) = layout_box.text_content {
        let text = text.trim();
        if !text.is_empty() {
            let text_x = layout_box.content.x + offset_x;
            let text_y = layout_box.content.y + offset_y + style.font_size;
            ops.push(DrawOp::DrawText {
                text: text.to_string(),
                x: text_x,
                y: text_y,
                font_size: style.font_size,
                color: style.color,
                font_family: style.font_family.clone(),
                bold: style.font_weight.is_bold(),
                italic: style.font_style == ferropdf_core::FontStyle::Italic,
            });
        }
    }

    // Children
    for child in &layout_box.children {
        paint_box(child, ops, offset_x, offset_y);
    }
}

fn paint_borders(layout_box: &LayoutBox, ops: &mut Vec<DrawOp>, rect: Rect) {
    let style = &layout_box.style;

    // Top border
    if style.border_top.width > 0.0 && style.border_top.style != BorderStyle::None {
        ops.push(DrawOp::StrokeRect {
            rect: Rect::new(rect.x, rect.y, rect.width, 0.0),
            color: style.border_top.color,
            width: style.border_top.width,
            style: style.border_top.style.clone(),
        });
    }

    // Right border
    if style.border_right.width > 0.0 && style.border_right.style != BorderStyle::None {
        ops.push(DrawOp::StrokeRect {
            rect: Rect::new(rect.right(), rect.y, 0.0, rect.height),
            color: style.border_right.color,
            width: style.border_right.width,
            style: style.border_right.style.clone(),
        });
    }

    // Bottom border
    if style.border_bottom.width > 0.0 && style.border_bottom.style != BorderStyle::None {
        ops.push(DrawOp::StrokeRect {
            rect: Rect::new(rect.x, rect.bottom(), rect.width, 0.0),
            color: style.border_bottom.color,
            width: style.border_bottom.width,
            style: style.border_bottom.style.clone(),
        });
    }

    // Left border
    if style.border_left.width > 0.0 && style.border_left.style != BorderStyle::None {
        ops.push(DrawOp::StrokeRect {
            rect: Rect::new(rect.x, rect.y, 0.0, rect.height),
            color: style.border_left.color,
            width: style.border_left.width,
            style: style.border_left.style.clone(),
        });
    }
}
