use ferropdf_core::{Document, NodeId, NodeType};
use ferropdf_parse::{Stylesheet, StyleRule, Declaration};

/// Match all stylesheet rules against a given node and return matching declarations.
/// Rules are returned in source order; cascade sorting happens in cascade.rs.
pub fn match_rules(
    doc: &Document,
    node_id: NodeId,
    sheets: &[Stylesheet],
) -> Vec<Declaration> {
    let node = doc.get(node_id);
    if node.node_type != NodeType::Element {
        return Vec::new();
    }

    let tag = node.tag_name.as_deref().unwrap_or("");
    let id = node.attr("id").unwrap_or("");
    let classes: Vec<&str> = node.attr("class")
        .map(|c| c.split_whitespace().collect())
        .unwrap_or_default();

    let mut result = Vec::new();

    for sheet in sheets {
        for rule in &sheet.rules {
            for selector in &rule.selectors {
                if matches_selector(selector, tag, id, &classes, doc, node_id) {
                    result.extend(rule.declarations.clone());
                }
            }
        }
    }

    result
}

fn matches_selector(
    selector: &str,
    tag: &str,
    id: &str,
    classes: &[&str],
    doc: &Document,
    node_id: NodeId,
) -> bool {
    let selector = selector.trim();

    // Universal selector
    if selector == "*" {
        return true;
    }

    // Handle descendant combinator (space-separated)
    if selector.contains(' ') && !selector.contains(':') {
        let parts: Vec<&str> = selector.split_whitespace().collect();
        if parts.len() == 2 {
            // Simple descendant: "parent child"
            let parent_sel = parts[0];
            let child_sel = parts[1];
            if matches_simple_selector(child_sel, tag, id, classes) {
                // Check if any ancestor matches the parent selector
                let mut current = doc.get(node_id).parent;
                while let Some(pid) = current {
                    let pnode = doc.get(pid);
                    let ptag = pnode.tag_name.as_deref().unwrap_or("");
                    let pid_attr = pnode.attr("id").unwrap_or("");
                    let pclasses: Vec<&str> = pnode.attr("class")
                        .map(|c| c.split_whitespace().collect())
                        .unwrap_or_default();
                    if matches_simple_selector(parent_sel, ptag, pid_attr, &pclasses) {
                        return true;
                    }
                    current = pnode.parent;
                }
                return false;
            }
            return false;
        }
    }

    // Handle child combinator (>)
    if selector.contains('>') {
        let parts: Vec<&str> = selector.split('>').map(|s| s.trim()).collect();
        if parts.len() == 2 {
            let parent_sel = parts[0];
            let child_sel = parts[1];
            if matches_simple_selector(child_sel, tag, id, classes) {
                if let Some(pid) = doc.get(node_id).parent {
                    let pnode = doc.get(pid);
                    let ptag = pnode.tag_name.as_deref().unwrap_or("");
                    let pid_attr = pnode.attr("id").unwrap_or("");
                    let pclasses: Vec<&str> = pnode.attr("class")
                        .map(|c| c.split_whitespace().collect())
                        .unwrap_or_default();
                    return matches_simple_selector(parent_sel, ptag, pid_attr, &pclasses);
                }
            }
            return false;
        }
    }

    // Handle comma-separated selectors (already split by the parser)
    matches_simple_selector(selector, tag, id, classes)
}

fn matches_simple_selector(selector: &str, tag: &str, id: &str, classes: &[&str]) -> bool {
    let selector = selector.trim();

    // Skip pseudo-selectors like :nth-child, :hover, etc.
    let selector = if let Some(pos) = selector.find(':') {
        &selector[..pos]
    } else {
        selector
    };

    if selector.is_empty() || selector == "*" {
        return true;
    }

    // ID selector: #foo
    if selector.starts_with('#') {
        return id == &selector[1..];
    }

    // Class selector: .foo
    if selector.starts_with('.') {
        return classes.contains(&&selector[1..]);
    }

    // Tag + class: div.foo
    if let Some(dot_pos) = selector.find('.') {
        let tag_part = &selector[..dot_pos];
        let class_part = &selector[dot_pos+1..];
        return tag == tag_part && classes.contains(&class_part);
    }

    // Tag + ID: div#foo
    if let Some(hash_pos) = selector.find('#') {
        let tag_part = &selector[..hash_pos];
        let id_part = &selector[hash_pos+1..];
        return tag == tag_part && id == id_part;
    }

    // Tag selector
    tag == selector
}
