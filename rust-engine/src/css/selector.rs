//! CSS selector matching and specificity.

use crate::html::dom::ElementData;

/// A CSS selector.
#[derive(Debug, Clone)]
pub enum Selector {
    /// Universal selector `*`
    Universal,
    /// Type/tag selector (e.g., `div`, `p`)
    Type(String),
    /// Class selector (e.g., `.container`)
    Class(String),
    /// ID selector (e.g., `#main`)
    Id(String),
    /// Attribute selector (e.g., `[href]`)
    Attribute(String, Option<String>),
    /// Pseudo-class (e.g., `:first-child`)
    PseudoClass(String),
    /// Pseudo-element (e.g., `::before`)
    PseudoElement(String),
    /// Compound selector (e.g., `div.container#main`)
    Compound(Vec<Selector>),
    /// Descendant combinator (e.g., `div p`)
    Descendant(Box<Selector>, Box<Selector>),
    /// Child combinator (e.g., `div > p`)
    Child(Box<Selector>, Box<Selector>),
    /// Adjacent sibling combinator (e.g., `h1 + p`)
    AdjacentSibling(Box<Selector>, Box<Selector>),
    /// General sibling combinator (e.g., `h1 ~ p`)
    GeneralSibling(Box<Selector>, Box<Selector>),
}

/// CSS selector specificity (a, b, c).
#[derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord)]
pub struct Specificity(pub u32, pub u32, pub u32);

impl Specificity {
    pub fn new(a: u32, b: u32, c: u32) -> Self {
        Self(a, b, c)
    }

    pub fn zero() -> Self {
        Self(0, 0, 0)
    }

    pub fn add(self, other: Self) -> Self {
        Self(self.0 + other.0, self.1 + other.1, self.2 + other.2)
    }
}

impl Selector {
    /// Calculate the specificity of this selector.
    pub fn specificity(&self) -> Specificity {
        match self {
            Selector::Universal => Specificity(0, 0, 0),
            Selector::Type(_) => Specificity(0, 0, 1),
            Selector::Class(_) => Specificity(0, 1, 0),
            Selector::Id(_) => Specificity(1, 0, 0),
            Selector::Attribute(_, _) => Specificity(0, 1, 0),
            Selector::PseudoClass(_) => Specificity(0, 1, 0),
            Selector::PseudoElement(_) => Specificity(0, 0, 1),
            Selector::Compound(parts) => {
                parts.iter().fold(Specificity::zero(), |acc, s| {
                    acc.add(s.specificity())
                })
            }
            Selector::Descendant(a, b)
            | Selector::Child(a, b)
            | Selector::AdjacentSibling(a, b)
            | Selector::GeneralSibling(a, b) => a.specificity().add(b.specificity()),
        }
    }

    /// Check if this selector matches the given element.
    /// `ancestors` is the list of ancestor elements from root to parent.
    /// `siblings` is the list of preceding sibling elements.
    pub fn matches(
        &self,
        element: &ElementData,
        ancestors: &[&ElementData],
        siblings: &[&ElementData],
    ) -> bool {
        match self {
            Selector::Universal => true,
            Selector::Type(tag) => element.tag_name == *tag,
            Selector::Class(class) => element.has_class(class),
            Selector::Id(id) => element.id() == Some(id.as_str()),
            Selector::Attribute(name, value) => match value {
                Some(val) => element.get_attr(name) == Some(val.as_str()),
                None => element.get_attr(name).is_some(),
            },
            Selector::PseudoClass(pseudo) => match pseudo.as_str() {
                "first-child" => siblings.is_empty(),
                "last-child" => false, // Requires sibling context
                _ => false,
            },
            Selector::PseudoElement(_) => false, // Handled separately
            Selector::Compound(parts) => {
                parts.iter().all(|s| s.matches(element, ancestors, siblings))
            }
            Selector::Descendant(ancestor_sel, self_sel) => {
                if !self_sel.matches(element, ancestors, siblings) {
                    return false;
                }
                ancestors
                    .iter()
                    .any(|anc| ancestor_sel.matches(anc, &[], &[]))
            }
            Selector::Child(parent_sel, self_sel) => {
                if !self_sel.matches(element, ancestors, siblings) {
                    return false;
                }
                ancestors
                    .last()
                    .map(|parent| parent_sel.matches(parent, &[], &[]))
                    .unwrap_or(false)
            }
            Selector::AdjacentSibling(prev_sel, self_sel) => {
                if !self_sel.matches(element, ancestors, siblings) {
                    return false;
                }
                siblings
                    .last()
                    .map(|prev| prev_sel.matches(prev, &[], &[]))
                    .unwrap_or(false)
            }
            Selector::GeneralSibling(sib_sel, self_sel) => {
                if !self_sel.matches(element, ancestors, siblings) {
                    return false;
                }
                siblings
                    .iter()
                    .any(|sib| sib_sel.matches(sib, &[], &[]))
            }
        }
    }

    /// Parse a simple selector string.
    pub fn parse(input: &str) -> Option<Self> {
        let input = input.trim();
        if input.is_empty() {
            return None;
        }

        // Handle descendant combinators (space-separated)
        let parts: Vec<&str> = input.split_whitespace().collect();
        if parts.len() > 1 {
            // Check for combinators
            let mut i = 0;
            let mut result: Option<Selector> = None;

            while i < parts.len() {
                let part = parts[i];

                if part == ">" && i + 1 < parts.len() {
                    let right = Self::parse_simple(parts[i + 1])?;
                    result = Some(Selector::Child(
                        Box::new(result?),
                        Box::new(right),
                    ));
                    i += 2;
                } else if part == "+" && i + 1 < parts.len() {
                    let right = Self::parse_simple(parts[i + 1])?;
                    result = Some(Selector::AdjacentSibling(
                        Box::new(result?),
                        Box::new(right),
                    ));
                    i += 2;
                } else if part == "~" && i + 1 < parts.len() {
                    let right = Self::parse_simple(parts[i + 1])?;
                    result = Some(Selector::GeneralSibling(
                        Box::new(result?),
                        Box::new(right),
                    ));
                    i += 2;
                } else {
                    let sel = Self::parse_simple(part)?;
                    result = Some(match result {
                        Some(left) => Selector::Descendant(Box::new(left), Box::new(sel)),
                        None => sel,
                    });
                    i += 1;
                }
            }

            return result;
        }

        Self::parse_simple(input)
    }

    /// Parse a simple (non-combinator) selector.
    fn parse_simple(input: &str) -> Option<Self> {
        if input == "*" {
            return Some(Selector::Universal);
        }

        // Check for compound selectors
        let mut parts = Vec::new();
        let mut current = String::new();
        let mut chars = input.chars().peekable();

        while let Some(&ch) = chars.peek() {
            match ch {
                '.' | '#' if !current.is_empty() => {
                    parts.push(Self::parse_single_simple(&current)?);
                    current.clear();
                    current.push(chars.next().unwrap());
                }
                '[' => {
                    if !current.is_empty() {
                        parts.push(Self::parse_single_simple(&current)?);
                        current.clear();
                    }
                    // Read until ]
                    current.push(chars.next().unwrap());
                    while let Some(&c) = chars.peek() {
                        current.push(chars.next().unwrap());
                        if c == ']' {
                            break;
                        }
                    }
                    parts.push(Self::parse_single_simple(&current)?);
                    current.clear();
                }
                ':' => {
                    if !current.is_empty() {
                        parts.push(Self::parse_single_simple(&current)?);
                        current.clear();
                    }
                    current.push(chars.next().unwrap());
                }
                _ => {
                    current.push(chars.next().unwrap());
                }
            }
        }

        if !current.is_empty() {
            parts.push(Self::parse_single_simple(&current)?);
        }

        match parts.len() {
            0 => None,
            1 => Some(parts.into_iter().next().unwrap()),
            _ => Some(Selector::Compound(parts)),
        }
    }

    fn parse_single_simple(input: &str) -> Option<Self> {
        if input.starts_with('#') {
            Some(Selector::Id(input[1..].to_string()))
        } else if input.starts_with('.') {
            Some(Selector::Class(input[1..].to_string()))
        } else if input.starts_with('[') && input.ends_with(']') {
            let inner = &input[1..input.len() - 1];
            if let Some(eq_pos) = inner.find('=') {
                let name = inner[..eq_pos].trim().to_string();
                let value = inner[eq_pos + 1..]
                    .trim()
                    .trim_matches('"')
                    .trim_matches('\'')
                    .to_string();
                Some(Selector::Attribute(name, Some(value)))
            } else {
                Some(Selector::Attribute(inner.to_string(), None))
            }
        } else if input.starts_with("::") {
            Some(Selector::PseudoElement(input[2..].to_string()))
        } else if input.starts_with(':') {
            Some(Selector::PseudoClass(input[1..].to_string()))
        } else {
            Some(Selector::Type(input.to_string()))
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::collections::HashMap;

    fn make_element(tag: &str, class: &str, id: &str) -> ElementData {
        let mut attrs = HashMap::new();
        if !class.is_empty() {
            attrs.insert("class".to_string(), class.to_string());
        }
        if !id.is_empty() {
            attrs.insert("id".to_string(), id.to_string());
        }
        ElementData {
            tag_name: tag.to_string(),
            attributes: attrs,
        }
    }

    #[test]
    fn test_type_selector() {
        let sel = Selector::parse("div").unwrap();
        let elem = make_element("div", "", "");
        assert!(sel.matches(&elem, &[], &[]));
    }

    #[test]
    fn test_class_selector() {
        let sel = Selector::parse(".container").unwrap();
        let elem = make_element("div", "container", "");
        assert!(sel.matches(&elem, &[], &[]));
    }

    #[test]
    fn test_id_selector() {
        let sel = Selector::parse("#main").unwrap();
        let elem = make_element("div", "", "main");
        assert!(sel.matches(&elem, &[], &[]));
    }

    #[test]
    fn test_specificity_ordering() {
        let a = Specificity::new(0, 0, 1); // type
        let b = Specificity::new(0, 1, 0); // class
        let c = Specificity::new(1, 0, 0); // id
        assert!(a < b);
        assert!(b < c);
    }
}
