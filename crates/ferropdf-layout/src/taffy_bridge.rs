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
    // Maps a DOM NodeId to the Taffy NodeId that represents it in the layout tree.
    // For table internals (thead/tbody/tr), the DOM node itself may NOT appear in
    // node_map because its children are flattened into the grid. Instead, the
    // table's grid node is used, and each <td>/<th> is a direct grid child.
    let mut table_cell_parent: HashMap<NodeId, NodeId> = HashMap::new();

    let root = doc.root();
    let body = find_body(doc, root).unwrap_or(root);

    build_taffy_tree(doc, body, styles, &mut taffy, &mut node_map, &mut table_cell_parent)?;

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
    let layout_root = read_layout(doc, body, styles, &taffy, &node_map, &table_cell_parent, 0.0, 0.0);

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

/// Recursively build the Taffy layout tree.
///
/// For `<table>` elements, the structure is flattened:
///   - The `<table>` becomes a `Display::Grid` node.
///   - `<thead>`, `<tbody>`, `<tfoot>`, `<tr>` are skipped (not added to Taffy).
///   - `<td>` and `<th>` cells are added as direct children of the grid node.
///   - `grid-template-columns` is set to `repeat(num_cols, auto)`.
fn build_taffy_tree(
    doc: &Document,
    node_id: NodeId,
    styles: &StyleTree,
    taffy: &mut TaffyTree,
    node_map: &mut HashMap<NodeId, taffy::NodeId>,
    table_cell_parent: &mut HashMap<NodeId, NodeId>,
) -> ferropdf_core::Result<()> {
    let node = doc.get(node_id);
    let style = styles.get(&node_id).cloned().unwrap_or_default();

    if style.display == FDisplay::None {
        return Ok(());
    }

    // ── Table: flatten to CSS Grid ──
    if style.display == FDisplay::Table {
        return build_table_as_grid(doc, node_id, styles, taffy, node_map, table_cell_parent);
    }

    let taffy_style = if node.is_text() {
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

    for &child_id in &node.children {
        build_taffy_tree(doc, child_id, styles, taffy, node_map, table_cell_parent)?;
        if let Some(&tid) = node_map.get(&child_id) {
            child_taffy_ids.push(tid);
        }
    }

    let taffy_node = taffy.new_with_children(taffy_style, &child_taffy_ids)
        .map_err(|e| ferropdf_core::FerroError::Layout(format!("Taffy node error: {:?}", e)))?;

    node_map.insert(node_id, taffy_node);
    Ok(())
}

/// Build a `<table>` element as a CSS Grid in Taffy.
///
/// 1. Collect all rows → cells (flattening thead/tbody/tfoot/tr).
/// 2. Count max columns.
/// 3. Create a Grid node with `grid_template_columns: repeat(num_cols, auto)`.
/// 4. Each cell becomes a direct grid child (its own subtree is built recursively).
fn build_table_as_grid(
    doc: &Document,
    table_id: NodeId,
    styles: &StyleTree,
    taffy: &mut TaffyTree,
    node_map: &mut HashMap<NodeId, taffy::NodeId>,
    table_cell_parent: &mut HashMap<NodeId, NodeId>,
) -> ferropdf_core::Result<()> {
    let table_style = styles.get(&table_id).cloned().unwrap_or_default();

    // Collect all cells in row-major order
    let rows = collect_table_rows(doc, table_id, styles);
    let num_cols = rows.iter().map(|r| r.len()).max().unwrap_or(1).max(1);

    // Build child Taffy nodes for each cell
    let mut cell_taffy_ids = Vec::new();
    for row in &rows {
        for &cell_id in row {
            // Build the cell's subtree
            build_taffy_tree(doc, cell_id, styles, taffy, node_map, table_cell_parent)?;
            if let Some(&tid) = node_map.get(&cell_id) {
                cell_taffy_ids.push(tid);
            }
            // Record that this cell's parent (for read_layout) is the table
            table_cell_parent.insert(cell_id, table_id);
        }
    }

    // Build the grid style for the <table>
    let mut grid_style = style_to_taffy::convert_table_to_grid(&table_style, num_cols);

    let grid_node = taffy.new_with_children(grid_style, &cell_taffy_ids)
        .map_err(|e| ferropdf_core::FerroError::Layout(format!("Taffy grid node error: {:?}", e)))?;

    node_map.insert(table_id, grid_node);
    Ok(())
}

/// Collect all rows in a table. Each row is a Vec of cell NodeIds.
fn collect_table_rows(doc: &Document, table_id: NodeId, styles: &StyleTree) -> Vec<Vec<NodeId>> {
    let mut rows = Vec::new();
    let table_node = doc.get(table_id);

    for &child_id in &table_node.children {
        let child_style = styles.get(&child_id).cloned().unwrap_or_default();
        match child_style.display {
            FDisplay::TableRow => {
                rows.push(collect_cells(doc, child_id, styles));
            }
            FDisplay::TableHeaderGroup | FDisplay::TableRowGroup | FDisplay::TableFooterGroup => {
                let group_node = doc.get(child_id);
                for &row_id in &group_node.children {
                    let row_style = styles.get(&row_id).cloned().unwrap_or_default();
                    if row_style.display == FDisplay::TableRow {
                        rows.push(collect_cells(doc, row_id, styles));
                    }
                }
            }
            _ => {}
        }
    }
    rows
}

fn collect_cells(doc: &Document, row_id: NodeId, styles: &StyleTree) -> Vec<NodeId> {
    let row_node = doc.get(row_id);
    row_node.children.iter()
        .filter(|&&child_id| {
            let s = styles.get(&child_id).cloned().unwrap_or_default();
            s.display == FDisplay::TableCell
        })
        .copied()
        .collect()
}

/// Read layout results from Taffy and build the LayoutBox tree.
///
/// For tables: the <table> grid node's children are the cells directly.
/// We reconstruct the visual tree: table → rows → cells.
fn read_layout(
    doc: &Document,
    node_id: NodeId,
    styles: &StyleTree,
    taffy: &TaffyTree,
    node_map: &HashMap<NodeId, taffy::NodeId>,
    table_cell_parent: &HashMap<NodeId, NodeId>,
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

    let margin = resolve_margin_insets(&style);

    // Build children
    let mut children = Vec::new();

    if style.display == FDisplay::Table {
        // Table: the Taffy node is a grid whose children are the <td>/<th> cells.
        // We read each cell's layout (which is a direct Taffy child of the grid).
        let rows = collect_table_rows(doc, node_id, styles);
        for row in &rows {
            for &cell_id in row {
                if node_map.contains_key(&cell_id) {
                    let child_box = read_layout(doc, cell_id, styles, taffy, node_map, table_cell_parent, x, y);
                    children.push(child_box);
                }
            }
        }
    } else {
        // Normal: recurse into DOM children
        for &child_id in &node.children {
            // Skip nodes that are part of a table grid (they are read by the table branch above)
            if table_cell_parent.contains_key(&child_id) {
                continue;
            }
            if node_map.contains_key(&child_id) {
                let child_box = read_layout(doc, child_id, styles, taffy, node_map, table_cell_parent, x, y);
                children.push(child_box);
            }
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
