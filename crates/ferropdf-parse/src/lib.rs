mod html;
pub mod css;

pub use html::parse_html;
pub use css::{parse_stylesheet, Stylesheet, StyleRule, Declaration, CssProperty, CssValue};

/// Résultat du parsing HTML complet
pub struct ParseResult {
    pub document:             ferropdf_core::Document,
    /// Contenu des balises <style>
    pub inline_styles:        Vec<String>,
    /// href des balises <link rel="stylesheet">
    pub external_stylesheets: Vec<String>,
}

/// Parser du HTML et collecter les feuilles de style
pub fn parse(html: &str) -> ferropdf_core::Result<ParseResult> {
    html::parse_full(html)
}
