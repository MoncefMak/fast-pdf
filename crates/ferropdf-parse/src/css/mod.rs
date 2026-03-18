mod parser;

pub use parser::{parse_stylesheet, CssProperty, CssValue, Declaration, StyleRule, Stylesheet};

/// User-agent stylesheet embarqué
pub const UA_CSS: &str = include_str!("ua.css");
