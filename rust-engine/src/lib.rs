//! FastPDF Engine - High-performance PDF generation from HTML/CSS
//!
//! This is the core Rust engine that powers the FastPDF library.
//! It provides HTML parsing, CSS styling, layout computation, and PDF rendering.

pub mod css;
pub mod error;
pub mod fonts;
pub mod html;
pub mod images;
pub mod layout;
pub mod pdf;
pub mod renderer;
pub mod tailwind;

mod bindings;

use pyo3::prelude::*;

/// The main entry point for the Python module.
/// Maturin maps this to fastpdf._engine
#[pymodule]
fn _engine(m: &Bound<'_, PyModule>) -> PyResult<()> {
    // Initialise env_logger so log macros produce output when RUST_LOG is set
    let _ = env_logger::try_init();

    // Register Python-facing classes and functions
    m.add_class::<bindings::PdfEngine>()?;
    m.add_class::<bindings::PdfDocument>()?;
    m.add_class::<bindings::RenderOptions>()?;
    m.add_function(wrap_pyfunction!(bindings::render_html_to_pdf, m)?)?;
    m.add_function(wrap_pyfunction!(bindings::render_html_to_pdf_bytes, m)?)?;
    m.add_function(wrap_pyfunction!(bindings::batch_render, m)?)?;
    m.add_function(wrap_pyfunction!(bindings::get_version, m)?)?;
    Ok(())
}
