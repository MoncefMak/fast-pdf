use ferropdf_core::*;

/// Create a new style by inheriting inheritable properties from parent.
pub fn inherit_from(parent: &ComputedStyle) -> ComputedStyle {
    let mut style = ComputedStyle::default();

    // Inherited properties
    style.color = parent.color;
    style.font_family = parent.font_family.clone();
    style.font_size = parent.font_size;
    style.font_weight = parent.font_weight.clone();
    style.font_style = parent.font_style.clone();
    style.line_height = parent.line_height;
    style.text_align = parent.text_align.clone();
    style.text_decoration = parent.text_decoration.clone();
    style.letter_spacing = parent.letter_spacing;
    style.visibility = parent.visibility;
    style.orphans = parent.orphans;
    style.widows = parent.widows;

    style
}
