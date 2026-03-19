use ferropdf_core::*;

/// Create a new style by inheriting inheritable properties from parent.
pub fn inherit_from(parent: &ComputedStyle) -> ComputedStyle {
    ComputedStyle {
        color: parent.color,
        font_family: parent.font_family.clone(),
        font_size: parent.font_size,
        font_weight: parent.font_weight.clone(),
        font_style: parent.font_style.clone(),
        line_height: parent.line_height,
        text_align: parent.text_align,
        text_decoration: parent.text_decoration.clone(),
        letter_spacing: parent.letter_spacing,
        visibility: parent.visibility,
        orphans: parent.orphans,
        widows: parent.widows,
        border_collapse: parent.border_collapse.clone(),
        list_style_type: parent.list_style_type.clone(),
        ..Default::default()
    }
}
