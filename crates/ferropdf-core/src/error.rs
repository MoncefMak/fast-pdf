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
