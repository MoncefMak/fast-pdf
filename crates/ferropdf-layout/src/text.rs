use ferropdf_core::ComputedStyle;

/// Estimate text width based on font size and character count.
/// This is a simplified measurement — cosmic-text will be used for proper shaping later.
pub fn estimate_text_width(text: &str, style: &ComputedStyle) -> f32 {
    // Average character width ≈ 0.6 * font_size for most fonts
    let avg_char_width = style.font_size * 0.6;
    let char_count = text.chars().count() as f32;
    char_count * avg_char_width + style.letter_spacing * (char_count - 1.0).max(0.0)
}

/// Estimate the height needed for text given a container width.
pub fn estimate_text_height(text: &str, style: &ComputedStyle, available_width: f32) -> f32 {
    if text.is_empty() {
        return 0.0;
    }

    let text_width = estimate_text_width(text, style);
    let lines = (text_width / available_width.max(1.0)).ceil().max(1.0);
    lines * style.line_height
}
