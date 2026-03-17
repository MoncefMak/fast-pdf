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
