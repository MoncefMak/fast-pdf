mod parser;

pub use parser::{parse_stylesheet, Stylesheet, StyleRule, Declaration, CssProperty, CssValue};

/// User-agent stylesheet embarqué
pub const UA_CSS: &str = include_str!("ua.css");
