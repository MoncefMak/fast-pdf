use std::collections::HashMap;
use taffy::prelude::*;
use ferropdf_core::{
    Document, NodeId, NodeType, ComputedStyle, Display as FDisplay,
    LayoutBox, LayoutTree, Rect, Insets, Length,
};
use ferropdf_style::StyleTree;
use crate::{style_to_taffy, text};

/// Build a LayoutTree from a styled Document using Taffy for layout computation.
pub fn build_layout(
    doc: &Document,
    styles: &StyleTree,
    available_width: f32,
    available_height: f32,
) -> ferropdf_core::Result<LayoutTree> {
    let mut taffy = TaffyTree::new();
    let mut node_map: HashMap<NodeId, taffy::NodeId> = HashMap::new();

    let root = doc.root();
    let body = find_body(doc, root).unwrap_or(root);

    build_taffy_tree(doc, body, styles, &mut taffy, &mut node_map)?;

    let taffy_root = match node_map.get(&body) {
        Some(n) => *n,
        None => return Ok(LayoutTree::new()),
    };

    // Compute layout with Taffy
    taffy.compute_layout(
        taffy_root,
        Size {
            width: AvailableSpace::Definite(available_width),
            height: AvailableSpace::Definite(available_height),
        },
    ).map_err(|e| ferropdf_core::FerroError::Layout(format!("Taffy layout error: {:?}", e)))?;

    // Read results from Taffy and build LayoutBox tree
    let layout_root = read_layout(doc, body, styles, &taffy, &node_map, 0.0, 0.0);

    Ok(LayoutTree { root: Some(layout_root) })
}

fn find_body(doc: &Document, start: NodeId) -> Option<NodeId> {
    let node = doc.get(start);
    if node.tag_name.as_deref() == Some("body") {
        return Some(start);
    }
    for &child in &node.children {
        if let Some(found) = find_body(doc, child) {
            return Some(found);
        }
    }
    None
}

fn build_taffy_tree(
    doc: &Document,
    node_id: NodeId,
    styles: &StyleTree,
    taffy: &mut TaffyTree,
    node_map: &mut HashMap<NodeId, taffy::NodeId>,
) -> ferropdf_core::Result<()> {
    let node = doc.get(node_id);
    let style = styles.get(&node_id).cloned().unwrap_or_default();

    if style.display == FDisplay::None {
        return Ok(());
    }

    let taffy_style = if node.is_text() {
        // Text nodes: estimate size based on content
        let text_content = node.text.as_deref().unwrap_or("");
        let text_width = text::estimate_text_width(text_content, &style);
        let mut ts = taffy::Style::default();
        ts.size = Size {
            width: Dimension::Length(text_width),
            height: Dimension::Length(style.line_height),
        };
        ts
    } else {
        style_to_taffy::convert(&style)
    };

    let mut child_taffy_ids = Vec::new();

    // Build children first
    for &child_id in &node.children {
        build_taffy_tree(doc, child_id, styles, taffy, node_map)?;
        if let Some(&tid) = node_map.get(&child_id) {
            child_taffy_ids.push(tid);
        }
    }

    let taffy_node = taffy.new_with_children(taffy_style, &child_taffy_ids)
        .map_err(|e| ferropdf_core::FerroError::Layout(format!("Taffy node error: {:?}", e)))?;

    node_map.insert(node_id, taffy_node);
    Ok(())
}

fn read_layout(
    doc: &Document,
    node_id: NodeId,
    styles: &StyleTree,
    taffy: &TaffyTree,
    node_map: &HashMap<NodeId, taffy::NodeId>,
    offset_x: f32,
    offset_y: f32,
) -> LayoutBox {
    let node = doc.get(node_id);
    let style = styles.get(&node_id).cloned().unwrap_or_default();

    let taffy_node = match node_map.get(&node_id) {
        Some(n) => *n,
        None => return LayoutBox::default(),
    };

    let layout = taffy.layout(taffy_node)
        .expect("Layout should be computed");

    let x = offset_x + layout.location.x;
    let y = offset_y + layout.location.y;

    let content = Rect::new(
        x + layout.padding.left + layout.border.left,
        y + layout.padding.top + layout.border.top,
        (layout.size.width - layout.padding.left - layout.padding.right - layout.border.left - layout.border.right).max(0.0),
        (layout.size.height - layout.padding.top - layout.padding.bottom - layout.border.top - layout.border.bottom).max(0.0),
    );

    let padding = Insets {
        top: layout.padding.top,
        right: layout.padding.right,
        bottom: layout.padding.bottom,
        left: layout.padding.left,
    };

    let border = Insets {
        top: layout.border.top,
        right: layout.border.right,
        bottom: layout.border.bottom,
        left: layout.border.left,
    };

    // Taffy 0.5 Layout doesn't expose margin — resolve from style
    let margin = resolve_margin_insets(&style);

    let mut children = Vec::new();
    for &child_id in &node.children {
        if node_map.contains_key(&child_id) {
            let child_box = read_layout(doc, child_id, styles, taffy, node_map, x, y);
            children.push(child_box);
        }
    }

    let text_content = if node.is_text() {
        node.text.clone()
    } else {
        None
    };

    let image_src = if node.tag_name.as_deref() == Some("img") {
        node.attr("src").map(|s| s.to_string())
    } else {
        None
    };

    LayoutBox {
        node_id: Some(node_id),
        style,
        content,
        padding,
        border,
        margin,
        children,
        shaped_lines: Vec::new(),
        image_src,
        text_content,
    }
}

fn resolve_margin_insets(style: &ComputedStyle) -> Insets {
    Insets {
        top:    length_to_px(&style.margin[0]),
        right:  length_to_px(&style.margin[1]),
        bottom: length_to_px(&style.margin[2]),
        left:   length_to_px(&style.margin[3]),
    }
}

fn length_to_px(l: &Length) -> f32 {
    match l {
        Length::Px(v) => *v,
        Length::Zero => 0.0,
        _ => 0.0,
    }
}
