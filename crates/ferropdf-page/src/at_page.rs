use ferropdf_core::PageConfig;

/// Parse @page rules and update PageConfig.
/// For now this is a placeholder — @page rule parsing will be added
/// when ferropdf-parse supports at-rule extraction.
pub fn apply_at_page_rules(_config: &mut PageConfig, _css: &str) {
    // Future: parse @page { margin: 2cm; } etc.
}
