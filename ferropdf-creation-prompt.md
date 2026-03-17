# ferropdf — Prompt de Création Complète du Projet

> **Instructions pour l'agent** : Ce prompt décrit la création complète du projet
> ferropdf depuis zéro. Suis chaque instruction **exactement** dans l'ordre.
> **Ne génère jamais de code si une lib existante fait déjà ce travail.**
> Après chaque fichier créé, vérifie que `cargo check` passe avant de continuer.

---

## RÈGLES ABSOLUES — Lire avant tout

```
RÈGLE 1 : Ne JAMAIS écrire de parser HTML maison       → utiliser html5ever
RÈGLE 2 : Ne JAMAIS écrire de parser CSS maison        → utiliser cssparser + selectors
RÈGLE 3 : Ne JAMAIS écrire de moteur de layout maison  → utiliser taffy
RÈGLE 4 : Ne JAMAIS écrire de text shaper maison       → utiliser cosmic-text
RÈGLE 5 : Ne JAMAIS écrire de générateur PDF maison    → utiliser pdf-writer
RÈGLE 6 : Ne JAMAIS faire de cp manuel pour maturin    → utiliser maturin develop
RÈGLE 7 : Chaque étape doit compiler avant de passer à la suivante
RÈGLE 8 : Aucun unwrap() dans le code non-test         → toujours propager les erreurs
RÈGLE 9 : Aucun todo!() dans le code livré             → implémenter ou laisser Err(...)
RÈGLE 10: Un seul Cargo.toml workspace à la racine     → versions centralisées
```

---

## Structure finale attendue

```
ferropdf/
│
├── Cargo.toml                    ← workspace racine, versions centralisées
├── pyproject.toml                ← maturin config
├── Makefile                      ← dev/test/bench en une commande
├── README.md
│
├── crates/
│   ├── ferropdf-core/            ← types partagés uniquement, aucune logique
│   │   └── src/
│   │       ├── lib.rs
│   │       ├── color.rs
│   │       ├── geometry.rs
│   │       ├── length.rs
│   │       ├── page.rs
│   │       ├── dom.rs
│   │       ├── style.rs
│   │       ├── layout.rs
│   │       └── error.rs
│   │
│   ├── ferropdf-parse/           ← html5ever + cssparser → DOM + CSSOM
│   │   └── src/
│   │       ├── lib.rs
│   │       ├── html.rs           ← TreeSink impl pour html5ever
│   │       └── css/
│   │           ├── mod.rs
│   │           ├── parser.rs     ← cssparser wrapper
│   │           ├── properties.rs ← enum Property + Value
│   │           └── ua.css        ← user-agent stylesheet embarqué
│   │
│   ├── ferropdf-style/           ← cascade CSS + computed styles
│   │   └── src/
│   │       ├── lib.rs
│   │       ├── cascade.rs        ← origine + spécificité + ordre
│   │       ├── inherit.rs        ← héritage + valeurs initiales
│   │       ├── compute.rs        ← em/rem/% → px, currentColor → rgba
│   │       └── matching.rs       ← sélecteurs → nœuds DOM
│   │
│   ├── ferropdf-layout/          ← taffy + cosmic-text
│   │   └── src/
│   │       ├── lib.rs
│   │       ├── taffy_bridge.rs   ← build + read taffy tree
│   │       ├── style_to_taffy.rs ← ComputedStyle → taffy::Style
│   │       └── text.rs           ← cosmic-text wrapper
│   │
│   ├── ferropdf-page/            ← pagination + fragmentation
│   │   └── src/
│   │       ├── lib.rs
│   │       ├── fragment.rs       ← algorithme de coupure entre pages
│   │       └── at_page.rs        ← @page, headers, footers, counters
│   │
│   └── ferropdf-render/          ← display list + pdf-writer
│       └── src/
│           ├── lib.rs
│           ├── display_list.rs   ← DrawOp enum
│           ├── painter.rs        ← LayoutTree → DisplayList
│           └── pdf.rs            ← DisplayList → pdf-writer → bytes
│
├── bindings/
│   └── python/
│       ├── Cargo.toml
│       └── src/
│           └── lib.rs            ← PyO3 bindings
│
├── python/
│   └── ferropdf/
│       ├── __init__.py
│       ├── py.typed
│       └── contrib/
│           ├── __init__.py
│           ├── django.py
│           └── fastapi.py
│
├── tests/
│   ├── test_basic.py
│   ├── test_layout.py
│   └── fixtures/
│       ├── invoice.html
│       └── simple.html
│
└── bench/
    └── compare.py
```

---

## ÉTAPE 1 — Cargo.toml workspace racine

Créer `/ferropdf/Cargo.toml` :

```toml
[workspace]
members = [
    "crates/ferropdf-core",
    "crates/ferropdf-parse",
    "crates/ferropdf-style",
    "crates/ferropdf-layout",
    "crates/ferropdf-page",
    "crates/ferropdf-render",
    "bindings/python",
]
resolver = "2"

[workspace.dependencies]
# HTML — NE PAS écrire de parser HTML maison
html5ever    = "0.27"
markup5ever  = "0.12"

# CSS — NE PAS écrire de parser CSS maison
cssparser    = "0.31"
selectors    = "0.25"

# Layout — NE PAS écrire de moteur de layout maison
taffy        = "0.5"

# Text + Fonts — NE PAS écrire de text shaper maison
cosmic-text  = "0.12"
fontdb       = "0.16"
ttf-parser   = "0.20"

# Images
image        = { version = "0.25", features = ["png", "jpeg", "webp"] }
resvg        = "0.42"
usvg         = "0.42"
tiny-skia    = "0.11"

# PDF output — NE PAS écrire de générateur PDF maison
pdf-writer   = "0.9"

# Utils
thiserror    = "1.0"
url          = "2.5"
id-arena     = "2.2"
rayon        = "1.8"
hashbrown    = "0.14"
log          = "0.4"
base64       = "0.22"
flate2       = "1.0"
ureq         = { version = "2.9", features = ["tls"] }

# Python bindings
pyo3         = { version = "0.21", features = ["extension-module"] }

[profile.release]
lto           = true
opt-level     = 3
codegen-units = 1
strip         = true
```

**Vérification** : `cargo check --workspace` — doit passer sans erreur.

---

## ÉTAPE 2 — ferropdf-core

Créer `crates/ferropdf-core/Cargo.toml` :

```toml
[package]
name    = "ferropdf-core"
version = "0.1.0"
edition = "2021"

[dependencies]
thiserror = { workspace = true }
id-arena  = { workspace = true }
hashbrown = { workspace = true }
```

### `crates/ferropdf-core/src/lib.rs`

```rust
pub mod color;
pub mod geometry;
pub mod length;
pub mod page;
pub mod dom;
pub mod style;
pub mod layout;
pub mod error;

// Re-exports publics
pub use color::Color;
pub use geometry::{Rect, Point, Size, Insets};
pub use length::Length;
pub use page::{PageSize, PageConfig, PageMargins, Orientation};
pub use dom::{Document, Node, NodeId, NodeType};
pub use style::{
    ComputedStyle, Display, Position, FontWeight, FontStyle,
    TextAlign, FlexDirection, FlexWrap, JustifyContent,
    AlignItems, AlignSelf, PageBreak, BorderSide, BorderStyle,
    BorderRadius,
};
pub use layout::{LayoutBox, LayoutTree, ShapedLine, ShapedGlyph};
pub use error::{FerroError, Result};
```

### `crates/ferropdf-core/src/error.rs`

```rust
#[derive(Debug, thiserror::Error)]
pub enum FerroError {
    #[error("HTML parse error: {0}")]   HtmlParse(String),
    #[error("CSS parse error: {0}")]    CssParse(String),
    #[error("Style error: {0}")]        Style(String),
    #[error("Layout error: {0}")]       Layout(String),
    #[error("Font error: {0}")]         Font(String),
    #[error("Image error: {0}")]        Image(String),
    #[error("PDF write error: {0}")]    PdfWrite(String),
    #[error("Network error: {0}")]      Network(String),
    #[error("IO error: {0}")]           Io(#[from] std::io::Error),
}

pub type Result<T> = std::result::Result<T, FerroError>;
```

### `crates/ferropdf-core/src/geometry.rs`

```rust
#[derive(Debug, Clone, Copy, Default, PartialEq)]
pub struct Rect {
    pub x: f32, pub y: f32,
    pub width: f32, pub height: f32,
}
impl Rect {
    pub fn new(x: f32, y: f32, w: f32, h: f32) -> Self { Self { x, y, width: w, height: h } }
    pub fn zero() -> Self { Self::default() }
    pub fn right(&self)  -> f32 { self.x + self.width }
    pub fn bottom(&self) -> f32 { self.y + self.height }
    pub fn size(&self) -> Size { Size { width: self.width, height: self.height } }
}

#[derive(Debug, Clone, Copy, Default, PartialEq)]
pub struct Size { pub width: f32, pub height: f32 }

#[derive(Debug, Clone, Copy, Default, PartialEq)]
pub struct Point { pub x: f32, pub y: f32 }

#[derive(Debug, Clone, Copy, Default, PartialEq)]
pub struct Insets {
    pub top: f32, pub right: f32,
    pub bottom: f32, pub left: f32,
}
impl Insets {
    pub fn uniform(v: f32) -> Self {
        Self { top: v, right: v, bottom: v, left: v }
    }
    pub fn horizontal(&self) -> f32 { self.left + self.right }
    pub fn vertical(&self)   -> f32 { self.top + self.bottom }
    pub fn zero() -> Self { Self::default() }
}
```

### `crates/ferropdf-core/src/color.rs`

```rust
#[derive(Debug, Clone, Copy, PartialEq, Default)]
pub struct Color { pub r: f32, pub g: f32, pub b: f32, pub a: f32 }

impl Color {
    pub fn new(r: f32, g: f32, b: f32, a: f32) -> Self { Self { r, g, b, a } }
    pub fn black()       -> Self { Self::new(0.0, 0.0, 0.0, 1.0) }
    pub fn white()       -> Self { Self::new(1.0, 1.0, 1.0, 1.0) }
    pub fn transparent() -> Self { Self::new(0.0, 0.0, 0.0, 0.0) }

    pub fn from_rgb8(r: u8, g: u8, b: u8) -> Self {
        Self::new(r as f32 / 255.0, g as f32 / 255.0, b as f32 / 255.0, 1.0)
    }

    pub fn from_rgba8(r: u8, g: u8, b: u8, a: u8) -> Self {
        Self::new(r as f32/255.0, g as f32/255.0, b as f32/255.0, a as f32/255.0)
    }

    pub fn from_hex(hex: &str) -> Option<Self> {
        let hex = hex.trim_start_matches('#');
        match hex.len() {
            3 => {
                let r = u8::from_str_radix(&hex[0..1].repeat(2), 16).ok()?;
                let g = u8::from_str_radix(&hex[1..2].repeat(2), 16).ok()?;
                let b = u8::from_str_radix(&hex[2..3].repeat(2), 16).ok()?;
                Some(Self::from_rgb8(r, g, b))
            }
            6 => {
                let r = u8::from_str_radix(&hex[0..2], 16).ok()?;
                let g = u8::from_str_radix(&hex[2..4], 16).ok()?;
                let b = u8::from_str_radix(&hex[4..6], 16).ok()?;
                Some(Self::from_rgb8(r, g, b))
            }
            8 => {
                let r = u8::from_str_radix(&hex[0..2], 16).ok()?;
                let g = u8::from_str_radix(&hex[2..4], 16).ok()?;
                let b = u8::from_str_radix(&hex[4..6], 16).ok()?;
                let a = u8::from_str_radix(&hex[6..8], 16).ok()?;
                Some(Self::from_rgba8(r, g, b, a))
            }
            _ => None,
        }
    }

    pub fn is_transparent(&self) -> bool { self.a < 0.001 }
}
```

### `crates/ferropdf-core/src/length.rs`

```rust
/// Longueur CSS avant résolution.
/// Les valeurs em/rem sont résolues par ferropdf-style.
/// Les valeurs Percent sont passées à Taffy qui les résout pendant le layout.
#[derive(Debug, Clone, Copy, PartialEq)]
pub enum Length {
    Px(f32),
    Pt(f32),
    Mm(f32),
    Em(f32),
    Rem(f32),
    Percent(f32),
    Auto,
    Zero,
    None,
}

impl Default for Length {
    fn default() -> Self { Length::Auto }
}

impl Length {
    pub fn is_auto(&self)    -> bool { matches!(self, Length::Auto) }
    pub fn is_percent(&self) -> bool { matches!(self, Length::Percent(_)) }
    pub fn is_none(&self)    -> bool { matches!(self, Length::None) }

    /// Résoudre en px quand le contexte est connu.
    /// Retourne None pour Auto, None, Percent (résolu par Taffy).
    pub fn to_px(&self, font_size_px: f32, root_font_size: f32) -> Option<f32> {
        match self {
            Length::Px(v)      => Some(*v),
            Length::Pt(v)      => Some(v * 1.333_333),
            Length::Mm(v)      => Some(v * 3.779_528),
            Length::Em(v)      => Some(v * font_size_px),
            Length::Rem(v)     => Some(v * root_font_size),
            Length::Zero       => Some(0.0),
            Length::Percent(_) => None,
            Length::Auto       => None,
            Length::None       => None,
        }
    }
}
```

### `crates/ferropdf-core/src/page.rs`

```rust
const MM_TO_PT: f32 = 2.834_646;

#[derive(Debug, Clone, PartialEq)]
pub enum PageSize { A3, A4, A5, Letter, Legal, Custom(f32, f32) }

impl PageSize {
    pub fn dimensions_pt(&self) -> (f32, f32) {
        match self {
            PageSize::A3           => (841.89, 1190.55),
            PageSize::A4           => (595.28,  841.89),
            PageSize::A5           => (419.53,  595.28),
            PageSize::Letter       => (612.0,   792.0),
            PageSize::Legal        => (612.0,  1008.0),
            PageSize::Custom(w, h) => (*w, *h),
        }
    }
    pub fn from_str(s: &str) -> Self {
        match s.to_uppercase().as_str() {
            "A3"     => PageSize::A3,
            "A5"     => PageSize::A5,
            "LETTER" => PageSize::Letter,
            "LEGAL"  => PageSize::Legal,
            _        => PageSize::A4,   // défaut A4
        }
    }
    pub fn name(&self) -> &'static str {
        match self {
            PageSize::A3     => "A3",
            PageSize::A4     => "A4",
            PageSize::A5     => "A5",
            PageSize::Letter => "Letter",
            PageSize::Legal  => "Legal",
            PageSize::Custom(_, _) => "Custom",
        }
    }
}

#[derive(Debug, Clone)]
pub enum Orientation { Portrait, Landscape }

#[derive(Debug, Clone)]
pub struct PageMargins {
    pub top: f32, pub right: f32,
    pub bottom: f32, pub left: f32,
}

impl Default for PageMargins {
    fn default() -> Self { Self::mm(20.0, 20.0, 20.0, 20.0) }
}

impl PageMargins {
    pub fn mm(top: f32, right: f32, bottom: f32, left: f32) -> Self {
        Self {
            top:    top    * MM_TO_PT,
            right:  right  * MM_TO_PT,
            bottom: bottom * MM_TO_PT,
            left:   left   * MM_TO_PT,
        }
    }
    pub fn uniform_mm(v: f32) -> Self { Self::mm(v, v, v, v) }
    pub fn uniform_pt(v: f32) -> Self {
        Self { top: v, right: v, bottom: v, left: v }
    }
    pub fn from_css_str(s: &str) -> Self {
        // Exemple: "20mm", "1in", "72pt"
        let v = parse_css_length_to_pt(s).unwrap_or(56.69); // 20mm par défaut
        Self::uniform_pt(v)
    }
}

fn parse_css_length_to_pt(s: &str) -> Option<f32> {
    let s = s.trim();
    if s.ends_with("mm") {
        s[..s.len()-2].trim().parse::<f32>().ok().map(|v| v * MM_TO_PT)
    } else if s.ends_with("cm") {
        s[..s.len()-2].trim().parse::<f32>().ok().map(|v| v * MM_TO_PT * 10.0)
    } else if s.ends_with("in") {
        s[..s.len()-2].trim().parse::<f32>().ok().map(|v| v * 72.0)
    } else if s.ends_with("pt") {
        s[..s.len()-2].trim().parse::<f32>().ok()
    } else if s.ends_with("px") {
        s[..s.len()-2].trim().parse::<f32>().ok().map(|v| v * 0.75)
    } else {
        None
    }
}

#[derive(Debug, Clone)]
pub struct PageConfig {
    pub size:        PageSize,
    pub margins:     PageMargins,
    pub orientation: Orientation,
}

impl Default for PageConfig {
    fn default() -> Self {
        Self {
            size:        PageSize::A4,
            margins:     PageMargins::default(),
            orientation: Orientation::Portrait,
        }
    }
}

impl PageConfig {
    pub fn content_width(&self) -> f32 {
        let (w, _) = self.size.dimensions_pt();
        (w - self.margins.left - self.margins.right).max(0.0)
    }
    pub fn content_height(&self) -> f32 {
        let (_, h) = self.size.dimensions_pt();
        (h - self.margins.top - self.margins.bottom).max(0.0)
    }
}
```

### `crates/ferropdf-core/src/dom.rs`

```rust
use std::collections::HashMap;
use id_arena::{Arena, Id};

pub type NodeId = Id<Node>;

#[derive(Debug, Clone, PartialEq)]
pub enum NodeType { Document, Element, Text, Comment }

#[derive(Debug, Clone)]
pub struct Node {
    pub node_type:  NodeType,
    pub tag_name:   Option<String>,
    pub attributes: HashMap<String, String>,
    pub text:       Option<String>,
    pub parent:     Option<NodeId>,
    pub children:   Vec<NodeId>,
}

impl Node {
    pub fn is_element(&self) -> bool { self.node_type == NodeType::Element }
    pub fn is_text(&self)    -> bool { self.node_type == NodeType::Text }
    pub fn tag(&self) -> Option<&str> { self.tag_name.as_deref() }
    pub fn attr(&self, name: &str) -> Option<&str> {
        self.attributes.get(name).map(|s| s.as_str())
    }
}

#[derive(Debug, Default)]
pub struct Document {
    pub nodes: Arena<Node>,
    pub root:  Option<NodeId>,
}

impl Document {
    pub fn new() -> Self { Self::default() }

    pub fn create_document_root(&mut self) -> NodeId {
        let id = self.nodes.alloc(Node {
            node_type:  NodeType::Document,
            tag_name:   None,
            attributes: HashMap::new(),
            text:       None,
            parent:     None,
            children:   Vec::new(),
        });
        self.root = Some(id);
        id
    }

    pub fn create_element(
        &mut self,
        tag:   &str,
        attrs: HashMap<String, String>,
    ) -> NodeId {
        self.nodes.alloc(Node {
            node_type:  NodeType::Element,
            tag_name:   Some(tag.to_lowercase()),
            attributes: attrs,
            text:       None,
            parent:     None,
            children:   Vec::new(),
        })
    }

    pub fn create_text(&mut self, content: &str) -> NodeId {
        self.nodes.alloc(Node {
            node_type:  NodeType::Text,
            tag_name:   None,
            attributes: HashMap::new(),
            text:       Some(content.to_string()),
            parent:     None,
            children:   Vec::new(),
        })
    }

    pub fn append_child(&mut self, parent: NodeId, child: NodeId) {
        self.nodes[child].parent = Some(parent);
        self.nodes[parent].children.push(child);
    }

    pub fn get(&self, id: NodeId) -> &Node { &self.nodes[id] }

    pub fn root(&self) -> NodeId {
        self.root.expect("Document has no root node")
    }

    /// Itérer sur tous les nœuds (pre-order depth-first)
    pub fn iter_preorder(&self, start: NodeId) -> PreorderIter<'_> {
        PreorderIter { doc: self, stack: vec![start] }
    }
}

pub struct PreorderIter<'a> {
    doc:   &'a Document,
    stack: Vec<NodeId>,
}

impl<'a> Iterator for PreorderIter<'a> {
    type Item = NodeId;
    fn next(&mut self) -> Option<NodeId> {
        let id   = self.stack.pop()?;
        let node = self.doc.get(id);
        // Ajouter les enfants en ordre inverse pour que le premier soit traité en premier
        for &child in node.children.iter().rev() {
            self.stack.push(child);
        }
        Some(id)
    }
}
```

### `crates/ferropdf-core/src/style.rs`

```rust
use crate::{Color, Length};

#[derive(Debug, Clone, PartialEq, Default)]
pub enum Display {
    #[default]
    Block,
    Inline, InlineBlock,
    Flex, Grid,
    Table, TableRow, TableCell,
    TableHeaderGroup, TableRowGroup, TableFooterGroup,
    ListItem, None,
}

#[derive(Debug, Clone, PartialEq, Default)]
pub enum Position { #[default] Static, Relative, Absolute, Fixed, Sticky }

#[derive(Debug, Clone, PartialEq)]
pub enum FontWeight {
    Normal, Bold, Bolder, Lighter,
    W100, W200, W300, W400, W500, W600, W700, W800, W900,
}
impl Default for FontWeight { fn default() -> Self { FontWeight::Normal } }
impl FontWeight {
    pub fn to_number(&self) -> u16 {
        match self {
            FontWeight::Normal | FontWeight::W400 => 400,
            FontWeight::Bold   | FontWeight::W700 => 700,
            FontWeight::W100 => 100, FontWeight::W200 => 200,
            FontWeight::W300 => 300, FontWeight::W500 => 500,
            FontWeight::W600 => 600, FontWeight::W800 => 800,
            FontWeight::W900 => 900,
            FontWeight::Bolder  => 700,
            FontWeight::Lighter => 300,
        }
    }
    pub fn is_bold(&self) -> bool { self.to_number() >= 600 }
}

#[derive(Debug, Clone, PartialEq, Default)]
pub enum FontStyle { #[default] Normal, Italic, Oblique }

#[derive(Debug, Clone, PartialEq, Default)]
pub enum TextAlign { #[default] Left, Right, Center, Justify }

#[derive(Debug, Clone, PartialEq, Default)]
pub enum TextDecoration { #[default] None, Underline, LineThrough, Overline }

#[derive(Debug, Clone, PartialEq, Default)]
pub enum FlexDirection { #[default] Row, Column, RowReverse, ColumnReverse }

#[derive(Debug, Clone, PartialEq, Default)]
pub enum FlexWrap { #[default] NoWrap, Wrap, WrapReverse }

#[derive(Debug, Clone, PartialEq, Default)]
pub enum JustifyContent {
    #[default] FlexStart, FlexEnd, Center,
    SpaceBetween, SpaceAround, SpaceEvenly,
}

#[derive(Debug, Clone, PartialEq, Default)]
pub enum AlignItems { FlexStart, FlexEnd, Center, #[default] Stretch, Baseline }

#[derive(Debug, Clone, PartialEq, Default)]
pub enum AlignSelf { #[default] Auto, FlexStart, FlexEnd, Center, Stretch, Baseline }

#[derive(Debug, Clone, PartialEq, Default)]
pub enum PageBreak { #[default] Auto, Always, Avoid }

#[derive(Debug, Clone, PartialEq, Default)]
pub enum BorderStyle { #[default] None, Solid, Dashed, Dotted, Double }

#[derive(Debug, Clone)]
pub struct BorderSide {
    pub width: f32,
    pub color: Color,
    pub style: BorderStyle,
}
impl Default for BorderSide {
    fn default() -> Self {
        Self { width: 0.0, color: Color::black(), style: BorderStyle::None }
    }
}

#[derive(Debug, Clone, Default)]
pub struct BorderRadius {
    pub top_left: f32, pub top_right: f32,
    pub bottom_right: f32, pub bottom_left: f32,
}
impl BorderRadius {
    pub fn uniform(r: f32) -> Self {
        Self { top_left: r, top_right: r, bottom_right: r, bottom_left: r }
    }
    pub fn any_nonzero(&self) -> bool {
        self.top_left > 0.0 || self.top_right > 0.0
        || self.bottom_right > 0.0 || self.bottom_left > 0.0
    }
    pub fn to_array(&self) -> [f32; 4] {
        [self.top_left, self.top_right, self.bottom_right, self.bottom_left]
    }
}

/// Toutes les propriétés résolues en valeurs absolues.
/// Pas de em/rem ici. Les Percent sont gardés pour Taffy (layout).
#[derive(Debug, Clone)]
pub struct ComputedStyle {
    pub display:    Display,
    pub position:   Position,
    pub visibility: bool,   // true = visible

    // Dimensions (Percent passé à Taffy, Auto passé à Taffy)
    pub width:      Length,
    pub height:     Length,
    pub min_width:  Length,
    pub max_width:  Length,
    pub min_height: Length,
    pub max_height: Length,

    // Spacing — [top, right, bottom, left]
    pub margin:  [Length; 4],
    pub padding: [Length; 4],

    // Borders
    pub border_top:    BorderSide,
    pub border_right:  BorderSide,
    pub border_bottom: BorderSide,
    pub border_left:   BorderSide,
    pub border_radius: BorderRadius,

    // Couleurs et fond
    pub color:            Color,
    pub background_color: Color,
    pub opacity:          f32,

    // Texte (toutes les valeurs en px)
    pub font_family:      Vec<String>,
    pub font_size:        f32,
    pub font_weight:      FontWeight,
    pub font_style:       FontStyle,
    pub line_height:      f32,
    pub text_align:       TextAlign,
    pub text_decoration:  TextDecoration,
    pub letter_spacing:   f32,

    // Flexbox
    pub flex_direction:  FlexDirection,
    pub flex_wrap:       FlexWrap,
    pub justify_content: JustifyContent,
    pub align_items:     AlignItems,
    pub align_self:      AlignSelf,
    pub flex_grow:       f32,
    pub flex_shrink:     f32,
    pub flex_basis:      Length,
    pub column_gap:      Length,
    pub row_gap:         Length,

    // Pagination
    pub page_break_before: PageBreak,
    pub page_break_after:  PageBreak,
    pub page_break_inside: PageBreak,
    pub orphans:           u32,
    pub widows:            u32,
}

impl Default for ComputedStyle {
    fn default() -> Self {
        Self {
            display:          Display::Block,
            position:         Position::Static,
            visibility:       true,
            width:            Length::Auto,
            height:           Length::Auto,
            min_width:        Length::Zero,
            max_width:        Length::None,
            min_height:       Length::Zero,
            max_height:       Length::None,
            margin:           [Length::Zero; 4],
            padding:          [Length::Zero; 4],
            border_top:       BorderSide::default(),
            border_right:     BorderSide::default(),
            border_bottom:    BorderSide::default(),
            border_left:      BorderSide::default(),
            border_radius:    BorderRadius::default(),
            color:            Color::black(),
            background_color: Color::transparent(),
            opacity:          1.0,
            font_family:      vec!["sans-serif".to_string()],
            font_size:        16.0,
            font_weight:      FontWeight::Normal,
            font_style:       FontStyle::Normal,
            line_height:      19.2,
            text_align:       TextAlign::Left,
            text_decoration:  TextDecoration::None,
            letter_spacing:   0.0,
            flex_direction:   FlexDirection::Row,
            flex_wrap:        FlexWrap::NoWrap,
            justify_content:  JustifyContent::FlexStart,
            align_items:      AlignItems::Stretch,
            align_self:       AlignSelf::Auto,
            flex_grow:        0.0,
            flex_shrink:      1.0,
            flex_basis:       Length::Auto,
            column_gap:       Length::Zero,
            row_gap:          Length::Zero,
            page_break_before: PageBreak::Auto,
            page_break_after:  PageBreak::Auto,
            page_break_inside: PageBreak::Auto,
            orphans:           2,
            widows:            2,
        }
    }
}
```

### `crates/ferropdf-core/src/layout.rs`

```rust
use crate::{ComputedStyle, NodeId, Rect, Insets};

#[derive(Debug, Clone)]
pub struct ShapedGlyph {
    pub glyph_id: u16,
    pub x:        f32,
    pub y:        f32,
    pub advance:  f32,
    pub font_id:  u64,
}

#[derive(Debug, Clone)]
pub struct ShapedLine {
    pub glyphs: Vec<ShapedGlyph>,
    pub width:  f32,
    pub y:      f32,
}

#[derive(Debug, Clone)]
pub struct LayoutBox {
    pub node_id:      Option<NodeId>,
    pub style:        ComputedStyle,
    pub content:      Rect,
    pub padding:      Insets,
    pub border:       Insets,
    pub margin:       Insets,
    pub children:     Vec<LayoutBox>,
    pub shaped_lines: Vec<ShapedLine>,
    pub image_src:    Option<String>,
    pub text_content: Option<String>,
}

impl Default for LayoutBox {
    fn default() -> Self {
        Self {
            node_id:      None,
            style:        ComputedStyle::default(),
            content:      Rect::zero(),
            padding:      Insets::zero(),
            border:       Insets::zero(),
            margin:       Insets::zero(),
            children:     Vec::new(),
            shaped_lines: Vec::new(),
            image_src:    None,
            text_content: None,
        }
    }
}

impl LayoutBox {
    pub fn border_box(&self) -> Rect {
        Rect::new(
            self.content.x - self.padding.left - self.border.left,
            self.content.y - self.padding.top  - self.border.top,
            self.content.width  + self.padding.horizontal() + self.border.horizontal(),
            self.content.height + self.padding.vertical()   + self.border.vertical(),
        )
    }

    pub fn margin_box_height(&self) -> f32 {
        self.margin.top + self.border.top + self.padding.top
        + self.content.height
        + self.padding.bottom + self.border.bottom + self.margin.bottom
    }

    pub fn is_text_leaf(&self) -> bool {
        self.text_content.is_some() && self.children.is_empty()
    }
}

#[derive(Debug, Default)]
pub struct LayoutTree {
    pub root: Option<LayoutBox>,
}

impl LayoutTree {
    pub fn new() -> Self { Self::default() }
}

/// Une page paginée = un sous-ensemble du LayoutTree
#[derive(Debug, Clone)]
pub struct Page {
    pub page_number: u32,
    pub total_pages: u32,   // rempli en post-processing
    pub content:     Vec<LayoutBox>,
    pub margin_boxes: Vec<MarginBox>,
}

#[derive(Debug, Clone)]
pub struct MarginBox {
    pub position: MarginBoxPosition,
    pub rect:     Rect,
    pub text:     String,
    pub style:    ComputedStyle,
}

#[derive(Debug, Clone, PartialEq)]
pub enum MarginBoxPosition {
    TopLeft, TopCenter, TopRight,
    BottomLeft, BottomCenter, BottomRight,
}
```

**Vérification** :
```bash
cargo build -p ferropdf-core
# Zéro erreur, zéro warning
```

---

## ÉTAPE 3 — ferropdf-parse

```toml
# crates/ferropdf-parse/Cargo.toml
[package]
name    = "ferropdf-parse"
version = "0.1.0"
edition = "2021"

[dependencies]
ferropdf-core = { path = "../ferropdf-core" }
html5ever      = { workspace = true }
markup5ever    = { workspace = true }
cssparser      = { workspace = true }
selectors      = { workspace = true }
url            = { workspace = true }
log            = { workspace = true }
hashbrown      = { workspace = true }
```

### `crates/ferropdf-parse/src/lib.rs`

```rust
mod html;
pub mod css;

pub use html::parse_html;
pub use css::{parse_stylesheet, Stylesheet, StyleRule, Declaration, CssProperty, CssValue};

use ferropdf_core::Result;

/// Résultat du parsing HTML complet
pub struct ParseResult {
    pub document:             ferropdf_core::Document,
    /// Contenu des balises <style>
    pub inline_styles:        Vec<String>,
    /// href des balises <link rel="stylesheet">
    pub external_stylesheets: Vec<String>,
}

/// Parser du HTML et collecter les feuilles de style
pub fn parse(html: &str) -> Result<ParseResult> {
    html::parse_full(html)
}
```

### `crates/ferropdf-parse/src/html.rs`

Implémenter `TreeSink` pour `html5ever` — c'est la seule chose à écrire pour le HTML.
html5ever gère toute la spec HTML5, l'error recovery, les balises imbriquées incorrectes, etc.

```rust
use std::collections::HashMap;
use html5ever::{
    parse_document, tendril::TendrilSink,
    tree_builder::{NodeOrText, TreeSink, ElementFlags},
    QualName, Attribute,
};
use markup5ever::interface::QuirksMode;
use ferropdf_core::{Document, NodeId};
use crate::ParseResult;

pub fn parse_full(html: &str) -> ferropdf_core::Result<ParseResult> {
    let sink = DomSink::new();
    let mut sink = parse_document(sink, Default::default()).one(html);
    let inline_styles = extract_style_tags(&sink.doc);
    Ok(ParseResult {
        external_stylesheets: sink.external_sheets,
        inline_styles,
        document: sink.doc,
    })
}

pub fn parse_html(html: &str) -> ferropdf_core::Result<Document> {
    Ok(parse_full(html)?.document)
}

struct DomSink {
    doc:             Document,
    external_sheets: Vec<String>,
}

impl DomSink {
    fn new() -> Self {
        let mut doc = Document::new();
        doc.create_document_root();
        Self { doc, external_sheets: Vec::new() }
    }
}

impl TreeSink for DomSink {
    type Handle = NodeId;
    type Output = Self;
    type Error  = std::convert::Infallible;

    fn finish(self) -> Self { self }

    fn get_document(&mut self) -> Self::Handle { self.doc.root() }
    fn get_template_contents(&mut self, t: &Self::Handle) -> Self::Handle { *t }
    fn same_node(&self, x: &Self::Handle, y: &Self::Handle) -> bool { x == y }

    fn elem_name<'a>(&'a self, target: &'a Self::Handle) -> html5ever::ExpandedName<'a> {
        let tag = self.doc.get(*target).tag_name.as_deref().unwrap_or("div");
        html5ever::expanded_name!(html tag)
    }

    fn create_element(
        &mut self, name: QualName,
        attrs: Vec<Attribute>,
        _: ElementFlags,
    ) -> Self::Handle {
        let tag = name.local.as_ref().to_lowercase();
        let attr_map: HashMap<String, String> = attrs.iter()
            .map(|a| (a.name.local.to_string(), a.value.to_string()))
            .collect();

        // Collecter les <link rel="stylesheet">
        if tag == "link"
            && attr_map.get("rel").map(|s| s.to_lowercase()) == Some("stylesheet".to_string())
        {
            if let Some(href) = attr_map.get("href") {
                self.external_sheets.push(href.clone());
            }
        }

        self.doc.create_element(&tag, attr_map)
    }

    fn create_text_node(&mut self, text: html5ever::tendril::StrTendril) -> Self::Handle {
        self.doc.create_text(text.as_ref())
    }

    fn create_comment(&mut self, _: html5ever::tendril::StrTendril) -> Self::Handle {
        self.doc.create_text("") // ignorer les commentaires HTML
    }

    fn create_pi(&mut self, _: html5ever::tendril::StrTendril,
                 _: html5ever::tendril::StrTendril) -> Self::Handle {
        self.doc.create_text("")
    }

    fn append(&mut self, parent: &Self::Handle, child: NodeOrText<Self::Handle>) {
        match child {
            NodeOrText::AppendNode(id)   => self.doc.append_child(*parent, id),
            NodeOrText::AppendText(text) => {
                let id = self.doc.create_text(text.as_ref());
                self.doc.append_child(*parent, id);
            }
        }
    }

    fn append_based_on_parent_node(
        &mut self, element: &Self::Handle,
        _prev: &Self::Handle,
        child: NodeOrText<Self::Handle>,
    ) { self.append(element, child); }

    fn append_doctype_to_document(&mut self, _: html5ever::tendril::StrTendril,
        _: html5ever::tendril::StrTendril, _: html5ever::tendril::StrTendril) {}

    fn add_attrs_if_missing(&mut self, target: &Self::Handle, attrs: Vec<Attribute>) {
        for attr in attrs {
            self.doc.nodes[*target].attributes
                .entry(attr.name.local.to_string())
                .or_insert_with(|| attr.value.to_string());
        }
    }

    fn associate_with_form(&mut self, _: &Self::Handle, _: &Option<Self::Handle>,
        _: NodeOrText<Self::Handle>, _: &Option<Self::Handle>) {}

    fn remove_from_parent(&mut self, target: &Self::Handle) {
        if let Some(pid) = self.doc.nodes[*target].parent.take() {
            self.doc.nodes[pid].children.retain(|&c| c != *target);
        }
    }

    fn reparent_children(&mut self, node: &Self::Handle, new_parent: &Self::Handle) {
        let children: Vec<_> = self.doc.nodes[*node].children.drain(..).collect();
        for child in children {
            self.doc.nodes[child].parent = Some(*new_parent);
            self.doc.nodes[*new_parent].children.push(child);
        }
    }

    fn mark_script_already_started(&mut self, _: &Self::Handle) {}
    fn pop(&mut self, _: &Self::Handle) {}
    fn set_quirks_mode(&mut self, _: QuirksMode) {}
    fn is_mathml_annotation_xml_integration_point(&self, _: &Self::Handle) -> bool { false }
    fn set_current_line(&mut self, _: u64) {}
    fn on_parse_error(&mut self, msg: std::borrow::Cow<'static, str>) {
        log::debug!("HTML parse warning: {}", msg);
    }
}

fn extract_style_tags(doc: &Document) -> Vec<String> {
    doc.nodes.iter()
        .filter(|(_, n)| n.tag_name.as_deref() == Some("style"))
        .map(|(id, n)| {
            n.children.iter()
                .filter_map(|&c| doc.nodes[c].text.clone())
                .collect::<String>()
        })
        .filter(|s| !s.is_empty())
        .collect()
}
```

### `crates/ferropdf-parse/src/css/ua.css`

```css
/* User-Agent stylesheet — styles navigateur par défaut */
/* Embarqué avec include_str!("ua.css") */

* { box-sizing: border-box; }
html, body { margin: 0; padding: 0; }
body { font-family: sans-serif; font-size: 16px; color: #000; background: #fff; }

h1 { display: block; font-size: 2em;    font-weight: bold; margin: 0.67em 0; }
h2 { display: block; font-size: 1.5em;  font-weight: bold; margin: 0.75em 0; }
h3 { display: block; font-size: 1.17em; font-weight: bold; margin: 0.83em 0; }
h4 { display: block; font-size: 1em;    font-weight: bold; margin: 1.12em 0; }
h5 { display: block; font-size: 0.83em; font-weight: bold; margin: 1.5em  0; }
h6 { display: block; font-size: 0.67em; font-weight: bold; margin: 1.67em 0; }

p  { display: block; margin: 1em 0; }
blockquote { display: block; margin: 1em 40px; }
pre  { display: block; white-space: pre; margin: 1em 0; font-family: monospace; }
code, kbd, samp, tt { font-family: monospace; }

ul, ol { display: block; margin: 1em 0; padding-left: 40px; }
li     { display: list-item; }
ul > li { list-style-type: disc; }
ol > li { list-style-type: decimal; }

a         { color: #0000ee; text-decoration: underline; }
strong, b { font-weight: bold; }
em, i     { font-style: italic; }
small     { font-size: 0.83em; }
sub       { font-size: 0.83em; }
sup       { font-size: 0.83em; }

hr { display: block; margin: 0.5em 0; border: 1px solid #ccc; }

table   { display: table; border-collapse: separate; border-spacing: 2px; }
thead   { display: table-header-group; }
tbody   { display: table-row-group; }
tfoot   { display: table-footer-group; }
tr      { display: table-row; }
th      { display: table-cell; font-weight: bold; text-align: center; }
td      { display: table-cell; }

img     { display: inline; }
div, section, article, aside, header, footer, main, nav { display: block; }
span, label, abbr { display: inline; }

@media print {
    body { background-color: transparent; }
    h1, h2, h3 { page-break-after: avoid; }
    table, figure { page-break-inside: avoid; }
}
```

**Vérification** :
```bash
cargo build -p ferropdf-parse
```

---

## ÉTAPE 4 — ferropdf-style

```toml
# crates/ferropdf-style/Cargo.toml
[package]
name    = "ferropdf-style"
version = "0.1.0"
edition = "2021"

[dependencies]
ferropdf-core  = { path = "../ferropdf-core" }
ferropdf-parse = { path = "../ferropdf-parse" }
cssparser      = { workspace = true }
selectors      = { workspace = true }
hashbrown      = { workspace = true }
log            = { workspace = true }
```

Ce crate implémente :
- `cascade.rs` : origines UA / author / inline / !important + spécificité
- `inherit.rs` : liste des propriétés héritées + valeurs initiales
- `compute.rs` : em/rem → px, currentColor → rgba
- `matching.rs` : sélecteurs CSS → nœuds DOM (via `selectors` crate)

Point d'entrée public :
```rust
// crates/ferropdf-style/src/lib.rs

pub fn resolve(
    document:    &ferropdf_core::Document,
    stylesheets: &[ferropdf_parse::Stylesheet],
    ua_css:      &str,
    page_width:  f32,
) -> ferropdf_core::Result<StyleTree>
```

où `StyleTree` = `HashMap<NodeId, ComputedStyle>`.

**Vérification** :
```bash
cargo build -p ferropdf-style
```

---

## ÉTAPE 5 — ferropdf-layout

```toml
# crates/ferropdf-layout/Cargo.toml
[package]
name    = "ferropdf-style"
version = "0.1.0"
edition = "2021"

[dependencies]
ferropdf-core  = { path = "../ferropdf-core" }
ferropdf-style = { path = "../ferropdf-style" }
taffy          = { workspace = true }
cosmic-text    = { workspace = true }
fontdb         = { workspace = true }
log            = { workspace = true }
```

### Règle critique pour ce crate

> **Ne jamais calculer width/height/padding manuellement.**
> Taffy le fait. Passer les valeurs à Taffy et lire les résultats.

### `crates/ferropdf-layout/src/style_to_taffy.rs`

```rust
use taffy::prelude::*;
use ferropdf_core::{ComputedStyle, Length};

/// Convertir ComputedStyle → taffy::Style
/// Taffy gère automatiquement :
/// - width:100% résolu par rapport au containing block (Fix 1)
/// - padding soustrait une seule fois (Fix 2)
/// - flex, grid, block layout
pub fn convert(style: &ComputedStyle) -> taffy::Style {
    taffy::Style {
        display: match style.display {
            ferropdf_core::Display::Block       => Display::Block,
            ferropdf_core::Display::Flex        => Display::Flex,
            ferropdf_core::Display::Grid        => Display::Grid,
            ferropdf_core::Display::None        => Display::None,
            // Inline et InlineBlock traités comme Block pour le PDF
            _                                   => Display::Block,
        },

        size: Size {
            width:  length_to_dim(&style.width),
            height: length_to_dim(&style.height),
        },
        min_size: Size {
            width:  length_to_dim(&style.min_width),
            height: length_to_dim(&style.min_height),
        },
        max_size: Size {
            width:  length_to_dim(&style.max_width),
            height: length_to_dim(&style.max_height),
        },

        // IMPORTANT : Taffy gère le padding correctement — ne pas le recalculer
        padding: Rect {
            top:    lp(&style.padding[0]),
            right:  lp(&style.padding[1]),
            bottom: lp(&style.padding[2]),
            left:   lp(&style.padding[3]),
        },
        border: Rect {
            top:    LengthPercentage::Length(style.border_top.width),
            right:  LengthPercentage::Length(style.border_right.width),
            bottom: LengthPercentage::Length(style.border_bottom.width),
            left:   LengthPercentage::Length(style.border_left.width),
        },
        margin: Rect {
            top:    lpa(&style.margin[0]),
            right:  lpa(&style.margin[1]),
            bottom: lpa(&style.margin[2]),
            left:   lpa(&style.margin[3]),
        },

        flex_direction: match style.flex_direction {
            ferropdf_core::FlexDirection::Row           => FlexDirection::Row,
            ferropdf_core::FlexDirection::Column        => FlexDirection::Column,
            ferropdf_core::FlexDirection::RowReverse    => FlexDirection::RowReverse,
            ferropdf_core::FlexDirection::ColumnReverse => FlexDirection::ColumnReverse,
        },
        flex_wrap: match style.flex_wrap {
            ferropdf_core::FlexWrap::NoWrap      => FlexWrap::NoWrap,
            ferropdf_core::FlexWrap::Wrap        => FlexWrap::Wrap,
            ferropdf_core::FlexWrap::WrapReverse => FlexWrap::WrapReverse,
        },
        justify_content: Some(match style.justify_content {
            ferropdf_core::JustifyContent::FlexStart    => JustifyContent::FlexStart,
            ferropdf_core::JustifyContent::FlexEnd      => JustifyContent::FlexEnd,
            ferropdf_core::JustifyContent::Center       => JustifyContent::Center,
            ferropdf_core::JustifyContent::SpaceBetween => JustifyContent::SpaceBetween,
            ferropdf_core::JustifyContent::SpaceAround  => JustifyContent::SpaceAround,
            ferropdf_core::JustifyContent::SpaceEvenly  => JustifyContent::SpaceEvenly,
        }),
        align_items: Some(match style.align_items {
            ferropdf_core::AlignItems::Stretch   => AlignItems::Stretch,
            ferropdf_core::AlignItems::FlexStart => AlignItems::FlexStart,
            ferropdf_core::AlignItems::FlexEnd   => AlignItems::FlexEnd,
            ferropdf_core::AlignItems::Center    => AlignItems::Center,
            ferropdf_core::AlignItems::Baseline  => AlignItems::Baseline,
        }),
        flex_grow:   style.flex_grow,
        flex_shrink: style.flex_shrink,
        flex_basis:  length_to_dim(&style.flex_basis),
        gap: Size {
            width:  lp(&style.column_gap),
            height: lp(&style.row_gap),
        },

        ..Default::default()
    }
}

fn length_to_dim(l: &Length) -> Dimension {
    match l {
        Length::Px(v)      => Dimension::Length(*v),
        Length::Percent(v) => Dimension::Percent(v / 100.0),
        Length::Auto       => Dimension::Auto,
        Length::Zero       => Dimension::Length(0.0),
        Length::None       => Dimension::Auto,
        other => {
            log::warn!("Unresolved length passed to Taffy: {:?}", other);
            Dimension::Auto
        }
    }
}

fn lp(l: &Length) -> LengthPercentage {
    match l {
        Length::Px(v)      => LengthPercentage::Length(*v),
        Length::Percent(v) => LengthPercentage::Percent(v / 100.0),
        Length::Zero       => LengthPercentage::Length(0.0),
        _                  => LengthPercentage::Length(0.0),
    }
}

fn lpa(l: &Length) -> LengthPercentageAuto {
    match l {
        Length::Px(v)      => LengthPercentageAuto::Length(*v),
        Length::Percent(v) => LengthPercentageAuto::Percent(v / 100.0),
        Length::Auto       => LengthPercentageAuto::Auto,
        Length::Zero       => LengthPercentageAuto::Length(0.0),
        _                  => LengthPercentageAuto::Auto,
    }
}
```

**Vérification** :
```bash
cargo build -p ferropdf-layout
```

---

## ÉTAPE 6 — bindings/python

```toml
# bindings/python/Cargo.toml
[package]
name    = "ferropdf-python"
version = "0.1.0"
edition = "2021"

[lib]
# NOM DÉFINITIF — NE JAMAIS CHANGER
# Si on le change, maturin produit un .so avec un autre nom
# et Python ne peut plus l'importer
name       = "_ferropdf"
crate-type = ["cdylib"]

[dependencies]
ferropdf-render = { path = "../../crates/ferropdf-render" }
ferropdf-core   = { path = "../../crates/ferropdf-core" }
pyo3 = { workspace = true }

[features]
default = ["pyo3/extension-module"]
```

```rust
// bindings/python/src/lib.rs
use pyo3::prelude::*;
use pyo3::types::PyBytes;

pyo3::create_exception!(ferropdf, FerroError,  pyo3::exceptions::PyRuntimeError);
pyo3::create_exception!(ferropdf, ParseError,  FerroError);
pyo3::create_exception!(ferropdf, LayoutError, FerroError);
pyo3::create_exception!(ferropdf, FontError,   FerroError);
pyo3::create_exception!(ferropdf, RenderError, FerroError);

#[pyclass(name = "Options")]
#[derive(Clone, Debug)]
pub struct PyOptions {
    pub page_size: String,
    pub margin:    String,
    pub base_url:  Option<String>,
    pub title:     Option<String>,
    pub author:    Option<String>,
}

#[pymethods]
impl PyOptions {
    #[new]
    #[pyo3(signature = (
        page_size = "A4",
        margin    = "20mm",
        base_url  = None,
        title     = None,
        author    = None,
    ))]
    fn new(
        page_size: &str,
        margin:    &str,
        base_url:  Option<String>,
        title:     Option<String>,
        author:    Option<String>,
    ) -> Self {
        Self {
            page_size: page_size.to_string(),
            margin:    margin.to_string(),
            base_url, title, author,
        }
    }

    fn __repr__(&self) -> String {
        format!("Options(page_size='{}', margin='{}')", self.page_size, self.margin)
    }
}

#[pyclass(name = "Engine")]
pub struct PyEngine {
    options: PyOptions,
}

#[pymethods]
impl PyEngine {
    #[new]
    #[pyo3(signature = (options = None))]
    fn new(options: Option<PyOptions>) -> Self {
        Self { options: options.unwrap_or_else(|| PyOptions {
            page_size: "A4".to_string(),
            margin:    "20mm".to_string(),
            base_url:  None,
            title:     None,
            author:    None,
        })}
    }

    /// Rendre du HTML en PDF.
    /// py.allow_threads() libère le GIL → compatible asyncio/FastAPI/Django.
    fn render<'py>(&self, py: Python<'py>, html: &str) -> PyResult<&'py PyBytes> {
        let html = html.to_string();
        let opts = self.options.clone();

        // ← Libérer le GIL ici — le rendu Rust est thread-safe
        let result = py.allow_threads(move || {
            ferropdf_render::render(&html, &opts.into())
        });

        match result {
            Ok(bytes) => Ok(PyBytes::new(py, &bytes)),
            Err(e)    => Err(to_py_err(e)),
        }
    }

    fn render_file<'py>(&self, py: Python<'py>, path: &str) -> PyResult<&'py PyBytes> {
        let html = std::fs::read_to_string(path)
            .map_err(|e| PyErr::new::<pyo3::exceptions::PyIOError, _>(e.to_string()))?;
        self.render(py, &html)
    }
}

#[pyfunction]
#[pyo3(signature = (html, base_url = None, options = None))]
fn from_html<'py>(
    py:       Python<'py>,
    html:     &str,
    base_url: Option<&str>,
    options:  Option<PyOptions>,
) -> PyResult<&'py PyBytes> {
    let mut opts = options.unwrap_or_else(|| PyOptions {
        page_size: "A4".to_string(), margin: "20mm".to_string(),
        base_url: None, title: None, author: None,
    });
    if let Some(u) = base_url { opts.base_url = Some(u.to_string()); }
    PyEngine::new(Some(opts)).render(py, html)
}

#[pyfunction]
#[pyo3(signature = (path, options = None))]
fn from_file<'py>(py: Python<'py>, path: &str, options: Option<PyOptions>) -> PyResult<&'py PyBytes> {
    let html = std::fs::read_to_string(path)
        .map_err(|e| PyErr::new::<pyo3::exceptions::PyIOError, _>(e.to_string()))?;
    from_html(py, &html, None, options)
}

#[pyfunction]
#[pyo3(signature = (html, output_path, base_url = None, options = None))]
fn write_pdf(
    py:          Python<'_>,
    html:        &str,
    output_path: &str,
    base_url:    Option<&str>,
    options:     Option<PyOptions>,
) -> PyResult<()> {
    let bytes = from_html(py, html, base_url, options)?;
    std::fs::write(output_path, bytes.as_bytes())
        .map_err(|e| PyErr::new::<pyo3::exceptions::PyIOError, _>(e.to_string()))
}

// Nom du module = "_ferropdf" (correspond à [lib] name dans Cargo.toml)
#[pymodule]
fn _ferropdf(py: Python, m: &PyModule) -> PyResult<()> {
    m.add_class::<PyOptions>()?;
    m.add_class::<PyEngine>()?;
    m.add_function(wrap_pyfunction!(from_html,  m)?)?;
    m.add_function(wrap_pyfunction!(from_file,  m)?)?;
    m.add_function(wrap_pyfunction!(write_pdf,  m)?)?;
    m.add("FerroError",  py.get_type::<FerroError>())?;
    m.add("ParseError",  py.get_type::<ParseError>())?;
    m.add("LayoutError", py.get_type::<LayoutError>())?;
    m.add("FontError",   py.get_type::<FontError>())?;
    m.add("RenderError", py.get_type::<RenderError>())?;
    m.add("__version__", env!("CARGO_PKG_VERSION"))?;
    Ok(())
}

fn to_py_err(e: ferropdf_core::FerroError) -> PyErr {
    use ferropdf_core::FerroError::*;
    match e {
        HtmlParse(m) | CssParse(m) => PyErr::new::<ParseError,  _>(m),
        Layout(m)                  => PyErr::new::<LayoutError, _>(m),
        Font(m)                    => PyErr::new::<FontError,   _>(m),
        PdfWrite(m)                => PyErr::new::<RenderError, _>(m),
        Io(e)  => PyErr::new::<pyo3::exceptions::PyIOError, _>(e.to_string()),
        other  => PyErr::new::<FerroError, _>(other.to_string()),
    }
}
```

---

## ÉTAPE 7 — pyproject.toml + wrapper Python

### `pyproject.toml` (racine)

```toml
[build-system]
requires      = ["maturin>=1.5,<2"]
build-backend = "maturin"

[project]
name            = "ferropdf"
version         = "0.1.0"
description     = "Fast HTML to PDF — Rust-powered, 10x faster than WeasyPrint"
readme          = "README.md"
requires-python = ">=3.8"
license         = { text = "MIT" }
keywords        = ["pdf", "html", "rust", "weasyprint"]

[tool.maturin]
# Chemin vers le Cargo.toml des bindings
manifest-path = "bindings/python/Cargo.toml"
# Dossier contenant ferropdf/__init__.py
python-source = "python"
# NOM DÉFINITIF — doit correspondre à [lib] name = "_ferropdf"
module-name   = "ferropdf._ferropdf"
features      = ["pyo3/extension-module"]
```

### `python/ferropdf/__init__.py`

```python
from ._ferropdf import (
    Engine, Options,
    FerroError, ParseError, LayoutError, FontError, RenderError,
    from_html, from_file, write_pdf,
    __version__,
)

__all__ = [
    "Engine", "Options",
    "FerroError", "ParseError", "LayoutError", "FontError", "RenderError",
    "from_html", "from_file", "write_pdf",
    "__version__",
]
```

### `python/ferropdf/contrib/django.py`

```python
from django.http import HttpResponse
from django.template.loader import render_to_string
import ferropdf

class PdfResponse(HttpResponse):
    """
    HttpResponse PDF depuis un template Django.

    Usage :
        def invoice(request, pk):
            return PdfResponse("invoice.html", {"pk": pk}, request=request)
    """
    def __init__(
        self,
        template_name: str,
        context: dict,
        request=None,
        filename: str = "document.pdf",
        options=None,
        inline: bool = True,
        **kwargs,
    ):
        html     = render_to_string(template_name, context, request=request)
        base_url = request.build_absolute_uri("/") if request else None
        engine   = ferropdf.Engine(options or ferropdf.Options(base_url=base_url))
        pdf      = engine.render(html)

        super().__init__(content=pdf, content_type="application/pdf", **kwargs)
        disposition = "inline" if inline else "attachment"
        self["Content-Disposition"] = f'{disposition}; filename="{filename}"'
        self["Content-Length"]      = str(len(pdf))
```

### `python/ferropdf/contrib/fastapi.py`

```python
import asyncio
from fastapi.responses import Response
import ferropdf

async def pdf_response(
    html: str,
    filename: str = "document.pdf",
    options=None,
    inline: bool = True,
) -> Response:
    """
    Retourne une Response FastAPI avec le PDF.
    Non-bloquant : le GIL est libéré côté Rust.

    Usage :
        @router.get("/invoice/{id}/pdf")
        async def invoice_pdf(id: int, db: Session = Depends(get_db)):
            html = templates.get_template("invoice.html").render(...)
            return await pdf_response(html, filename=f"invoice-{id}.pdf")
    """
    engine = ferropdf.Engine(options or ferropdf.Options())
    loop   = asyncio.get_event_loop()
    pdf    = await loop.run_in_executor(None, engine.render, html)
    d      = "inline" if inline else "attachment"
    return Response(
        content=pdf,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'{d}; filename="{filename}"',
            "Content-Length":      str(len(pdf)),
        },
    )
```

---

## ÉTAPE 8 — Makefile

```makefile
.PHONY: dev release test bench check clean

# Développement : compile + installe dans le venv
# NE JAMAIS faire de cp manuel — maturin gère tout
dev:
	maturin develop

# Release : compile optimisé
release:
	maturin develop --release

# Tests
test: dev
	cargo test --workspace
	pytest tests/ -v

# Benchmarks vs WeasyPrint
bench: release
	python bench/compare.py

# Check Rust seulement
check:
	cargo check --workspace
	cargo clippy --workspace -- -D warnings

# Nettoyer
clean:
	cargo clean
	find . -name "*.so" -delete
	find . -name "__pycache__" -exec rm -rf {} +
```

---

## ÉTAPE 9 — Tests

### `tests/fixtures/simple.html`

```html
<!DOCTYPE html>
<html>
<head>
  <style>
    body { font-family: sans-serif; margin: 20px; }
    h1   { color: #2563eb; }
    .box { background: #f3f4f6; padding: 16px; border-radius: 8px; }
  </style>
</head>
<body>
  <h1>Simple Test</h1>
  <div class="box"><p>Contenu de test</p></div>
</body>
</html>
```

### `tests/fixtures/invoice.html`

```html
<!DOCTYPE html>
<html>
<head>
  <style>
    body   { font-family: sans-serif; margin: 40px; font-size: 14px; }
    .header { display: flex; justify-content: space-between; margin-bottom: 40px; }
    .title  { font-size: 28px; font-weight: bold; color: #1e40af; }
    table   { width: 100%; border-collapse: collapse; margin-top: 20px; }
    th      { background: #1e40af; color: white; padding: 10px; text-align: left; }
    td      { padding: 10px; border-bottom: 1px solid #e5e7eb; }
    tr:nth-child(even) td { background: #f9fafb; }
    .total  { font-size: 18px; font-weight: bold; text-align: right; margin-top: 20px; }
  </style>
</head>
<body>
  <div class="header">
    <div class="title">FACTURE #2024-001</div>
    <div>Date : 17/03/2026</div>
  </div>
  <table>
    <thead>
      <tr><th>Description</th><th>Qté</th><th>Prix unit.</th><th>Total</th></tr>
    </thead>
    <tbody>
      <tr><td>Développement Rust</td><td>10</td><td>150€</td><td>1500€</td></tr>
      <tr><td>Intégration Python</td><td>5</td><td>120€</td><td>600€</td></tr>
      <tr><td>Tests et documentation</td><td>3</td><td>100€</td><td>300€</td></tr>
    </tbody>
  </table>
  <div class="total">Total : 2400€ HT</div>
</body>
</html>
```

### `tests/test_basic.py`

```python
"""
Tests fondamentaux — ces tests doivent TOUS passer avant de considérer
le projet fonctionnel.
"""
import ferropdf
import pytest

def pdf_is_valid(data: bytes) -> bool:
    return data[:4] == b"%PDF"

def count_pages(pdf: bytes) -> int:
    """Compter les pages dans un PDF de manière approximative."""
    return pdf.count(b"/Type /Page\n")


class TestModule:
    def test_import(self):
        assert hasattr(ferropdf, "Engine")
        assert hasattr(ferropdf, "Options")
        assert hasattr(ferropdf, "from_html")
        assert hasattr(ferropdf, "from_file")
        assert hasattr(ferropdf, "__version__")

    def test_from_html_minimal(self):
        pdf = ferropdf.from_html("<p>Hello</p>")
        assert pdf_is_valid(pdf)

    def test_from_html_with_styles(self):
        html = open("tests/fixtures/simple.html").read()
        pdf  = ferropdf.from_html(html)
        assert pdf_is_valid(pdf)

    def test_from_file(self):
        pdf = ferropdf.from_file("tests/fixtures/simple.html")
        assert pdf_is_valid(pdf)

    def test_write_pdf(self, tmp_path):
        out = tmp_path / "out.pdf"
        ferropdf.write_pdf("<p>Test</p>", str(out))
        assert out.exists()
        assert pdf_is_valid(out.read_bytes())

    def test_empty_html(self):
        pdf = ferropdf.from_html("")
        assert pdf_is_valid(pdf)

    def test_malformed_html_no_crash(self):
        cases = [
            "<p>Unclosed",
            "<div><p>Double unclosed",
            "Texte brut sans balises",
            "<script>alert(1)</script><p>xss</p>",
        ]
        for html in cases:
            assert pdf_is_valid(ferropdf.from_html(html)), f"Crash sur: {html!r}"


class TestOptions:
    def test_default(self):
        opts = ferropdf.Options()
        pdf  = ferropdf.from_html("<p>Test</p>", options=opts)
        assert pdf_is_valid(pdf)

    def test_a4(self):
        opts = ferropdf.Options(page_size="A4", margin="20mm")
        assert pdf_is_valid(ferropdf.from_html("<p>A4</p>", options=opts))

    def test_letter(self):
        opts = ferropdf.Options(page_size="Letter")
        assert pdf_is_valid(ferropdf.from_html("<p>Letter</p>", options=opts))

    def test_a3(self):
        opts = ferropdf.Options(page_size="A3")
        assert pdf_is_valid(ferropdf.from_html("<p>A3</p>", options=opts))


class TestLayout:
    def test_width_100_percent(self):
        """
        CRITIQUE — ce test couvre le Fix 1 du projet précédent.
        width:100% doit être résolu par rapport au containing block,
        pas retourner 0px.
        Si ce test génère un PDF de plus de 3 pages, le bug est présent.
        """
        html = """
        <div style="width:500px">
          <table style="width:100%">
            <tr><td>Col 1</td><td>Col 2</td><td>Col 3</td></tr>
            <tr><td>Data</td><td>Data</td><td>Data</td></tr>
          </table>
        </div>
        """
        pdf = ferropdf.from_html(html)
        assert pdf_is_valid(pdf)
        # 1 seule page attendue (pas 8)
        assert count_pages(pdf) <= 2

    def test_no_double_padding(self):
        """
        CRITIQUE — ce test couvre le Fix 2 du projet précédent.
        Le padding ne doit être soustrait qu'une seule fois.
        """
        html = """
        <div style="width:400px; padding:20px; background:#eee">
          <div style="width:100%; background:#ccc">
            <p style="padding:10px">Texte imbriqué</p>
          </div>
        </div>
        """
        pdf = ferropdf.from_html(html)
        assert pdf_is_valid(pdf)
        assert count_pages(pdf) == 1

    def test_flex_row(self):
        html = """
        <div style="display:flex; width:600px; gap:20px">
          <div style="flex:1; background:red; min-height:50px">A</div>
          <div style="flex:1; background:blue; min-height:50px">B</div>
          <div style="flex:1; background:green; min-height:50px">C</div>
        </div>
        """
        assert pdf_is_valid(ferropdf.from_html(html))

    def test_invoice_page_count(self):
        """La facture de test doit tenir en 1-2 pages, pas 8."""
        html = open("tests/fixtures/invoice.html").read()
        pdf  = ferropdf.from_html(html)
        assert pdf_is_valid(pdf)
        pages = count_pages(pdf)
        assert pages <= 2, f"Invoice : {pages} pages détectées (max 2)"


class TestEngine:
    def test_reusable(self):
        """Engine réutilisable sans état résiduel entre les rendus."""
        engine = ferropdf.Engine()
        r1 = engine.render("<p>Doc 1</p>")
        r2 = engine.render("<p>Doc 2</p>")
        assert pdf_is_valid(r1)
        assert pdf_is_valid(r2)
        assert r1 != r2   # deux PDFs différents

    def test_render_file(self, tmp_path):
        f = tmp_path / "page.html"
        f.write_text("<h1>From file</h1>", encoding="utf-8")
        engine = ferropdf.Engine()
        assert pdf_is_valid(engine.render_file(str(f)))


class TestErrors:
    def test_hierarchy(self):
        assert issubclass(ferropdf.ParseError,  ferropdf.FerroError)
        assert issubclass(ferropdf.LayoutError, ferropdf.FerroError)
        assert issubclass(ferropdf.FontError,   ferropdf.FerroError)
        assert issubclass(ferropdf.RenderError, ferropdf.FerroError)

    def test_ferro_error_is_exception(self):
        assert issubclass(ferropdf.FerroError, Exception)


class TestDjango:
    def test_pdf_response(self, tmp_path):
        """Test minimal sans vrai projet Django."""
        from ferropdf.contrib.django import PdfResponse
        # Vérifier que la classe existe et est importable
        assert PdfResponse is not None


class TestFastAPI:
    def test_pdf_response_async(self):
        import asyncio
        from ferropdf.contrib.fastapi import pdf_response

        async def run():
            resp = await pdf_response("<h1>FastAPI Test</h1>")
            assert resp.media_type == "application/pdf"
            assert pdf_is_valid(resp.body)

        asyncio.run(run())


class TestPerformance:
    def test_faster_than_weasyprint(self):
        """
        Objectif : 10x+ plus rapide que WeasyPrint.
        Ce test mesure uniquement ferropdf.
        Comparer manuellement avec bench/compare.py.
        """
        import time
        engine = ferropdf.Engine()
        html   = open("tests/fixtures/invoice.html").read()

        # Warm-up
        engine.render(html)

        N  = 20
        t0 = time.perf_counter()
        for _ in range(N):
            engine.render(html)
        ms = (time.perf_counter() - t0) / N * 1000

        print(f"\n⚡ ferropdf: {ms:.1f}ms/doc ({N} itérations)")
        assert ms < 300, f"Trop lent: {ms:.1f}ms (cible: < 300ms pour MVP)"
```

### `bench/compare.py`

```python
"""
Benchmark ferropdf vs WeasyPrint.
Lancer avec : python bench/compare.py
"""
import time, sys

try:
    import ferropdf
except ImportError:
    print("❌ ferropdf non installé. Lancer: maturin develop --release")
    sys.exit(1)

try:
    import weasyprint
    HAS_WEASYPRINT = True
except ImportError:
    HAS_WEASYPRINT = False
    print("⚠️  WeasyPrint non installé — benchmark partiel")

HTML = open("tests/fixtures/invoice.html").read()
N    = 20

print(f"\n{'='*50}")
print(f"Benchmark — {N} rendus de invoice.html")
print(f"{'='*50}")

# ferropdf
engine = ferropdf.Engine()
engine.render(HTML)   # warm-up

t0 = time.perf_counter()
for _ in range(N):
    engine.render(HTML)
ferro_ms = (time.perf_counter() - t0) / N * 1000
print(f"\n⚡ ferropdf    : {ferro_ms:.1f}ms/doc")

# WeasyPrint
if HAS_WEASYPRINT:
    # warm-up
    weasyprint.HTML(string=HTML).write_pdf()

    t0 = time.perf_counter()
    for _ in range(N):
        weasyprint.HTML(string=HTML).write_pdf()
    weasyprit_ms = (time.perf_counter() - t0) / N * 1000
    print(f"🐌 WeasyPrint  : {weasyprit_ms:.1f}ms/doc")
    print(f"\n🏆 Speedup     : {weasyprit_ms / ferro_ms:.1f}x")

    if ferro_ms < weasyprit_ms / 5:
        print("✅ OBJECTIF ATTEINT : > 5x plus rapide")
    else:
        print("⚠️  Objectif non atteint : < 5x")
else:
    print(f"\n✅ ferropdf fonctionne à {ferro_ms:.1f}ms/doc")
```

---

## ÉTAPE 10 — Build et vérification finale

```bash
# 1. Setup
python -m venv .venv
source .venv/bin/activate    # Windows: .venv\Scripts\activate
pip install maturin pytest

# 2. Premier build
maturin develop

# 3. Smoke test
python -c "
import ferropdf
pdf = ferropdf.from_html('<h1>Hello ferropdf</h1>')
assert pdf[:4] == b'%PDF', 'Le PDF doit commencer par %PDF'
print(f'✅ ferropdf {ferropdf.__version__} fonctionne')
"

# 4. Tests complets
pytest tests/ -v

# 5. Build release pour les perfs
maturin develop --release
python bench/compare.py

# 6. Vérifications Rust
cargo check --workspace
cargo clippy --workspace -- -D warnings
cargo test --workspace
```

### Résultats attendus

```
✅ maturin develop        — compile sans erreur
✅ smoke test             — %PDF détecté
✅ pytest tests/ -v       — tous les tests passent
✅ invoice.html           — 1-2 pages maximum
✅ cargo clippy           — 0 warnings
✅ bench/compare.py       — > 5x WeasyPrint au MVP, objectif 10x+
```

---

## Résumé des libs utilisées

| Besoin | Lib | Raison |
|---|---|---|
| Parser HTML | `html5ever` | Spec HTML5, même moteur que Firefox |
| Parser CSS | `cssparser` | Mozilla, battle-tested |
| Sélecteurs CSS | `selectors` | Mozilla, identique à Firefox |
| Layout | `taffy` | Flexbox + Grid corrects, aucun bug connu |
| Text shaping | `cosmic-text` | Bidi, ligatures, wrapping correct |
| Fonts | `fontdb` + `ttf-parser` | Résolution fonts système + custom |
| Images raster | `image` | PNG, JPEG, WebP |
| SVG | `resvg` | Rendu SVG fidèle |
| PDF output | `pdf-writer` | Bas niveau, propre, performant |
| Python bindings | `pyo3` + `maturin` | Standard de l'industrie |

**Aucune de ces libs ne doit être réécrite.**
Le travail à faire = les assembler dans la pipeline correcte.
