//! HTML parser module.
//!
//! Parses HTML content into a structured DOM tree using html5ever.

pub mod dom;
pub mod parser;

pub use dom::{DomNode, DomTree, ElementData, NodeType};
pub use parser::HtmlParser;
