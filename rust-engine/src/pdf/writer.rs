//! Low-level PDF writer utilities.

use printpdf::*;

use crate::css::values::Color;

/// Convert CSS pixels to PDF points (1pt = 1/72 inch, 1px = 1/96 inch at 96 DPI).
pub fn px_to_pt(px: f64) -> f64 {
    px * 72.0 / 96.0
}

/// Convert CSS pixels to printpdf Mm.
pub fn px_to_mm(px: f64) -> Mm {
    Mm((px * 25.4 / 96.0) as f32)
}

/// Convert a Color to printpdf Rgb.
pub fn color_to_rgb(color: &Color) -> printpdf::Rgb {
    let (r, g, b) = color.to_pdf_rgb();
    Rgb::new(r, g, b, None)
}

/// Map a CSS font family + weight + style to a PDF built-in font.
pub fn resolve_builtin_font(family: &str, weight: u32, italic: bool) -> BuiltinFont {
    let is_bold = weight >= 700;
    let family_lower = family.to_lowercase();

    match family_lower.as_str() {
        "serif" | "times" | "times new roman" | "georgia" => match (is_bold, italic) {
            (true, true) => BuiltinFont::TimesBoldItalic,
            (true, false) => BuiltinFont::TimesBold,
            (false, true) => BuiltinFont::TimesItalic,
            (false, false) => BuiltinFont::TimesRoman,
        },
        "monospace" | "courier" | "courier new" | "consolas" | "monaco" => {
            match (is_bold, italic) {
                (true, true) => BuiltinFont::CourierBoldOblique,
                (true, false) => BuiltinFont::CourierBold,
                (false, true) => BuiltinFont::CourierOblique,
                (false, false) => BuiltinFont::Courier,
            }
        }
        _ => match (is_bold, italic) {
            (true, true) => BuiltinFont::HelveticaBoldOblique,
            (true, false) => BuiltinFont::HelveticaBold,
            (false, true) => BuiltinFont::HelveticaOblique,
            (false, false) => BuiltinFont::Helvetica,
        },
    }
}

/// Map a CSS font family + weight + style to a PDF built-in font name string
/// (for use with the font metrics module).
pub fn resolve_builtin_font_name(family: &str, weight: u32, italic: bool) -> &'static str {
    let is_bold = weight >= 700;
    let family_lower = family.to_lowercase();

    match family_lower.as_str() {
        "serif" | "times" | "times new roman" | "georgia" => match (is_bold, italic) {
            (true, true) => "Times-BoldItalic",
            (true, false) => "Times-Bold",
            (false, true) => "Times-Italic",
            (false, false) => "Times-Roman",
        },
        "monospace" | "courier" | "courier new" | "consolas" | "monaco" => {
            match (is_bold, italic) {
                (true, true) => "Courier-BoldOblique",
                (true, false) => "Courier-Bold",
                (false, true) => "Courier-Oblique",
                (false, false) => "Courier",
            }
        }
        _ => match (is_bold, italic) {
            (true, true) => "Helvetica-BoldOblique",
            (true, false) => "Helvetica-Bold",
            (false, true) => "Helvetica-Oblique",
            (false, false) => "Helvetica",
        },
    }
}

/// Standard PDF page sizes in Mm.
pub fn page_size_a4() -> (Mm, Mm) {
    (Mm(210.0), Mm(297.0))
}

pub fn page_size_letter() -> (Mm, Mm) {
    (Mm(215.9), Mm(279.4))
}

pub fn page_size_legal() -> (Mm, Mm) {
    (Mm(215.9), Mm(355.6))
}
