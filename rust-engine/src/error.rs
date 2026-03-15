//! Error types for the FastPDF engine.

use thiserror::Error;

/// Core error type for the FastPDF engine.
#[derive(Error, Debug)]
pub enum FastPdfError {
    #[error("HTML parsing error: {0}")]
    HtmlParse(String),

    #[error("CSS parsing error: {0}")]
    CssParse(String),

    #[error("Layout error: {0}")]
    Layout(String),

    #[error("Rendering error: {0}")]
    Render(String),

    #[error("PDF generation error: {0}")]
    PdfGeneration(String),

    #[error("Font error: {0}")]
    Font(String),

    #[error("Image error: {0}")]
    Image(String),

    #[error("SVG error: {0}")]
    Svg(String),

    #[error("Template error: {0}")]
    Template(String),

    #[error("I/O error: {0}")]
    Io(#[from] std::io::Error),

    #[error("Configuration error: {0}")]
    Config(String),
}

/// Result type alias for FastPDF operations.
pub type Result<T> = std::result::Result<T, FastPdfError>;

impl From<FastPdfError> for pyo3::PyErr {
    fn from(err: FastPdfError) -> pyo3::PyErr {
        pyo3::exceptions::PyRuntimeError::new_err(err.to_string())
    }
}
