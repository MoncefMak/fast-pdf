//! Style resolver — maps DOM + CSS into computed styles for each node.


use crate::css::properties::{ComputedStyle, CssProperty};
use crate::css::selector::Specificity;
use crate::css::stylesheet::{Declaration, Stylesheet};
use crate::css::values::CssValue;
use crate::css::CssParser;
use crate::html::dom::ElementData;

/// Resolves CSS styles for DOM nodes.
pub struct StyleResolver<'a> {
    stylesheets: Vec<&'a Stylesheet>,
}

impl<'a> StyleResolver<'a> {
    pub fn new(stylesheets: Vec<&'a Stylesheet>) -> Self {
        Self { stylesheets }
    }

    /// Compute the style for a given element, given its ancestors.
    pub fn compute_style(
        &self,
        element: &ElementData,
        parent_style: &ComputedStyle,
        ancestors: &[&ElementData],
        siblings: &[&ElementData],
    ) -> ComputedStyle {
        let mut style = ComputedStyle::new();

        // 1. Apply inherited properties from parent
        style.inherit_from(parent_style);

        // 2. Collect all matching rules with specificity
        let mut matched: Vec<(Specificity, &Declaration)> = Vec::new();

        for stylesheet in &self.stylesheets {
            for rule in &stylesheet.rules {
                for selector in &rule.selectors {
                    if selector.matches(element, ancestors, siblings) {
                        let specificity = selector.specificity();
                        for decl in &rule.declarations {
                            matched.push((specificity, decl));
                        }
                    }
                }
            }
        }

        // 3. Sort by specificity (stable sort preserves source order for equal specificity)
        matched.sort_by_key(|(spec, _)| *spec);

        // 4. Apply declarations in specificity order
        for (_, decl) in &matched {
            if !decl.important {
                style.set(decl.property.clone(), decl.value.clone());
            }
        }

        // 5. Apply !important declarations (override everything)
        for (_, decl) in &matched {
            if decl.important {
                style.set(decl.property.clone(), decl.value.clone());
            }
        }

        // 6. Apply inline styles (highest specificity for non-important)
        if let Some(inline) = element.get_attr("style") {
            if let Ok(inline_decls) = CssParser::parse_inline(inline) {
                for decl in inline_decls {
                    style.set(decl.property, decl.value);
                }
            }
        }

        style
    }

    /// Apply default display values based on tag name.
    pub fn apply_tag_defaults(tag_name: &str, style: &mut ComputedStyle) {
        match tag_name {
            "h1" | "h2" | "h3" | "h4" | "h5" | "h6" => {
                if style.get(&CssProperty::FontWeight).is_none() {
                    style.set(CssProperty::FontWeight, CssValue::Keyword("bold".to_string()));
                }
            }
            "b" | "strong" => {
                if style.get(&CssProperty::FontWeight).is_none() {
                    style.set(CssProperty::FontWeight, CssValue::Keyword("bold".to_string()));
                }
            }
            "i" | "em" => {
                if style.get(&CssProperty::FontStyle).is_none() {
                    style.set(CssProperty::FontStyle, CssValue::Keyword("italic".to_string()));
                }
            }
            "a" => {
                if style.get(&CssProperty::Color).is_none() {
                    style.set(CssProperty::Color, CssValue::Color(crate::css::values::Color::rgb(0, 0, 238)));
                }
                if style.get(&CssProperty::TextDecoration).is_none() {
                    style.set(CssProperty::TextDecoration, CssValue::Keyword("underline".to_string()));
                }
            }
            "code" | "pre" => {
                if style.get(&CssProperty::FontFamily).is_none() {
                    style.set(CssProperty::FontFamily, CssValue::Keyword("monospace".to_string()));
                }
            }
            _ => {}
        }
    }
}
