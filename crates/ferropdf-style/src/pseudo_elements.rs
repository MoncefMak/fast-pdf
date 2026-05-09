//! Materialise CSS `::before` and `::after` pseudo-elements as real
//! text nodes in the DOM before the cascade runs.
//!
//! ferropdf does not implement a full pseudo-element abstraction (the
//! Mozilla `selectors` crate has all the pieces but wiring up a parallel
//! "fake element" representation across layout, pagination, and the
//! painter is a major change). The pragmatic shortcut is: scan parsed
//! stylesheet rules for selectors ending in `::before` / `::after`,
//! match the prefix against each element, find the rule's `content`
//! declaration, and inject a synthetic text node into the matched
//! element's children. From there everything downstream — cascade,
//! layout, paint — treats the injected text just like author-written
//! text.
//!
//! Limitations:
//! - Only string-literal `content: "..."` is honoured. `attr(href)`,
//!   `counter()`, `url()`, and concatenated content lists are not
//!   substituted.
//! - The injected text node inherits the parent element's style; the
//!   `::before` / `::after` rule's other declarations (color, font, …)
//!   are not applied to the synthetic node yet.

use crate::matching::FerroSelectorParser;
use cssparser::{Parser as CssParser, ParserInput};
use ferropdf_core::{Document, NodeId, NodeType};
use ferropdf_parse::{CssProperty, Stylesheet};
use selectors::parser::{ParseRelative, SelectorList};

/// Inject `::before` and `::after` text nodes into `doc` for every
/// selector that matches an element. Mutates `doc` in place; the new
/// text children appear before/after the original children so the
/// downstream cascade-matching pass styles them as descendants of the
/// matched element.
pub fn inject_pseudo_content(doc: &mut Document, sheets: &[&Stylesheet]) {
    // Collect (prefix, kind, content) tuples first so we don't iterate
    // sheets while mutating doc.
    #[derive(Debug)]
    struct PendingPseudo {
        prefix: String,
        kind: Pseudo,
        content: String,
    }

    let mut pending: Vec<PendingPseudo> = Vec::new();
    for sheet in sheets {
        for rule in &sheet.rules {
            for selector_text in &rule.selectors {
                let Some((prefix, kind)) = strip_pseudo(selector_text) else {
                    continue;
                };
                let Some(content) = extract_content_literal(rule) else {
                    continue;
                };
                pending.push(PendingPseudo {
                    prefix: prefix.to_string(),
                    kind,
                    content,
                });
            }
        }
    }
    if pending.is_empty() {
        return;
    }

    // Snapshot every element node so we don't try to match against
    // synthetic text nodes added in this very pass.
    let element_ids: Vec<NodeId> = doc
        .nodes
        .iter()
        .filter(|(_, n)| matches!(n.node_type, NodeType::Element))
        .map(|(id, _)| id)
        .collect();

    for p in pending {
        let Some(matches) = match_prefix(&p.prefix, doc, &element_ids) else {
            continue;
        };
        for target in matches {
            let text_id = doc.create_text(&p.content);
            match p.kind {
                Pseudo::Before => doc.prepend_child(target, text_id),
                Pseudo::After => doc.append_child(target, text_id),
            }
        }
    }
}

#[derive(Copy, Clone, Debug)]
enum Pseudo {
    Before,
    After,
}

fn strip_pseudo(selector: &str) -> Option<(String, Pseudo)> {
    let trimmed = selector.trim();

    // Try the modern `::name` form first so it wins over the legacy
    // single-colon form (`::before` would otherwise also match `:before`
    // and split as ("::before"[..1], Before) = (":", Before).)
    for (suffix, kind) in [("::before", Pseudo::Before), ("::after", Pseudo::After)] {
        if trimmed.len() > suffix.len()
            && trimmed[trimmed.len() - suffix.len()..].eq_ignore_ascii_case(suffix)
        {
            let prefix = trimmed[..trimmed.len() - suffix.len()].trim().to_string();
            return if prefix.is_empty() {
                None
            } else {
                Some((prefix, kind))
            };
        }
    }

    // Legacy `:before` / `:after` (CSS 2.1). Only accept when the
    // character before isn't another `:` (which would indicate a
    // mistyped `::before` already handled above with an empty prefix).
    for (suffix, kind) in [(":before", Pseudo::Before), (":after", Pseudo::After)] {
        if trimmed.len() > suffix.len()
            && trimmed[trimmed.len() - suffix.len()..].eq_ignore_ascii_case(suffix)
        {
            let head_end = trimmed.len() - suffix.len();
            // Reject `::before` here — only the modern matcher above
            // should accept it.
            if trimmed[..head_end].ends_with(':') {
                continue;
            }
            let prefix = trimmed[..head_end].trim().to_string();
            return if prefix.is_empty() {
                None
            } else {
                Some((prefix, kind))
            };
        }
    }

    None
}

/// Return the literal string used as `content:` for this rule, or `None`
/// if no `content` declaration is present or its value is non-literal.
fn extract_content_literal(rule: &ferropdf_parse::StyleRule) -> Option<String> {
    for decl in &rule.declarations {
        let is_content = match &decl.property {
            CssProperty::Unknown(name) => name.eq_ignore_ascii_case("content"),
            _ => false,
        };
        if !is_content {
            continue;
        }
        let raw = decl.value.to_cow().trim().to_string();
        // Strip surrounding quotes if present.
        if (raw.starts_with('"') && raw.ends_with('"') && raw.len() >= 2)
            || (raw.starts_with('\'') && raw.ends_with('\'') && raw.len() >= 2)
        {
            return Some(raw[1..raw.len() - 1].to_string());
        }
        // CSS keywords like `none`, `normal`: skip.
        if raw.eq_ignore_ascii_case("none") || raw.eq_ignore_ascii_case("normal") {
            return None;
        }
        // Bare keyword content (rare) — accept as-is.
        if !raw.is_empty() && !raw.contains('(') {
            return Some(raw);
        }
        return None;
    }
    None
}

/// Match a selector prefix (e.g. `"li.note"`) against every element in
/// `element_ids`. Returns the matching node IDs, or `None` if the prefix
/// fails to parse.
fn match_prefix(prefix: &str, doc: &Document, element_ids: &[NodeId]) -> Option<Vec<NodeId>> {
    let mut input = ParserInput::new(prefix);
    let mut parser = CssParser::new(&mut input);
    let list = SelectorList::parse(&FerroSelectorParser, &mut parser, ParseRelative::No).ok()?;

    use selectors::context::{
        IgnoreNthChildForInvalidation, MatchingContext, MatchingMode, NeedsSelectorFlags,
        QuirksMode,
    };
    let mut nth_cache = selectors::NthIndexCache::default();

    let mut hits = Vec::new();
    for &id in element_ids {
        let element = crate::matching::DomNode::new(doc, id);
        let any_match = list.0.iter().any(|s| {
            let mut ctx = MatchingContext::new(
                MatchingMode::Normal,
                None,
                &mut nth_cache,
                QuirksMode::NoQuirks,
                NeedsSelectorFlags::No,
                IgnoreNthChildForInvalidation::No,
            );
            selectors::matching::matches_selector(s, 0, None, &element, &mut ctx)
        });
        if any_match {
            hits.push(id);
        }
    }
    Some(hits)
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn detects_before_pseudo() {
        let (prefix, kind) = strip_pseudo("li::before").unwrap();
        assert_eq!(prefix, "li");
        assert!(matches!(kind, Pseudo::Before));
    }

    #[test]
    fn detects_after_pseudo() {
        let (prefix, kind) = strip_pseudo("p.note::after").unwrap();
        assert_eq!(prefix, "p.note");
        assert!(matches!(kind, Pseudo::After));
    }

    #[test]
    fn legacy_single_colon_is_recognised() {
        let (prefix, _) = strip_pseudo("h1:before").unwrap();
        assert_eq!(prefix, "h1");
    }

    #[test]
    fn case_insensitive_pseudo_keyword() {
        let (prefix, kind) = strip_pseudo("a::BEFORE").unwrap();
        assert_eq!(prefix, "a");
        assert!(matches!(kind, Pseudo::Before));
    }

    #[test]
    fn non_pseudo_selectors_return_none() {
        assert!(strip_pseudo("p").is_none());
        assert!(strip_pseudo("div > span").is_none());
    }

    #[test]
    fn pseudo_only_without_prefix_is_rejected() {
        // "::before" as a standalone selector is not meaningful for
        // injection — there's no element to attach to.
        assert!(strip_pseudo("::before").is_none());
    }
}
