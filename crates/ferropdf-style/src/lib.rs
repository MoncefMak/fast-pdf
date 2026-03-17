mod cascade;
mod inherit;
mod compute;
mod matching;

use std::collections::HashMap;
use ferropdf_core::{ComputedStyle, Document, NodeId, NodeType};
use ferropdf_parse::{Stylesheet, CssProperty, CssValue};

pub type StyleTree = HashMap<NodeId, ComputedStyle>;

/// Resolve all styles for a document given stylesheets.
pub fn resolve(
    document:    &Document,
    stylesheets: &[Stylesheet],
    ua_css:      &str,
    page_width:  f32,
) -> ferropdf_core::Result<StyleTree> {
    let ua_sheet = ferropdf_parse::parse_stylesheet(ua_css)?;
    let mut all_sheets = vec![ua_sheet];
    all_sheets.extend(stylesheets.iter().cloned());

    let root = document.root();
    let mut style_tree = StyleTree::new();
    let root_font_size = 16.0_f32;

    resolve_recursive(document, root, &all_sheets, &mut style_tree, None, root_font_size, page_width);

    Ok(style_tree)
}

fn resolve_recursive(
    doc: &Document,
    node_id: NodeId,
    sheets: &[Stylesheet],
    tree: &mut StyleTree,
    parent_style: Option<&ComputedStyle>,
    root_font_size: f32,
    page_width: f32,
) {
    let node = doc.get(node_id);

    let mut style = match parent_style {
        Some(ps) => inherit::inherit_from(ps),
        None => ComputedStyle::default(),
    };

    if node.node_type == NodeType::Element {
        // Apply matched rules from stylesheets
        let matched = matching::match_rules(doc, node_id, sheets);
        cascade::apply_declarations(&mut style, &matched, root_font_size);

        // Apply inline style attribute
        if let Some(inline) = node.attr("style") {
            if let Ok(sheet) = ferropdf_parse::parse_stylesheet(&format!("__inline__ {{ {} }}", inline)) {
                for rule in &sheet.rules {
                    cascade::apply_rule_declarations(&mut style, &rule.declarations, root_font_size);
                }
            }
        }

        // Apply tag-specific defaults
        compute::apply_tag_defaults(&mut style, node.tag());

        // Resolve relative units
        compute::resolve_units(&mut style, parent_style, root_font_size);
    } else if node.node_type == NodeType::Text {
        // Text nodes inherit everything from parent
    }

    tree.insert(node_id, style.clone());

    for &child in &node.children {
        resolve_recursive(doc, child, sheets, tree, Some(&style), root_font_size, page_width);
    }
}
