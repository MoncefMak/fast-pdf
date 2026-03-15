//! PyO3 Python bindings for the FastPDF engine.
//!
//! Exposes the Rust rendering pipeline to Python with a clean, ergonomic API.

use std::sync::Arc;

use pyo3::prelude::*;
use pyo3::types::PyBytes;
use rayon::prelude::*;

use crate::css::CssParser;
use crate::error::FastPdfError;
use crate::fonts::FontCache;
use crate::html::HtmlParser;
use crate::images::ImageCache;
use crate::layout::engine::LayoutEngine;
use crate::layout::pagination::{PageLayout, PageSize};
use crate::pdf::generator::{PdfConfig, PdfGenerator};
use crate::renderer::paint::Renderer;
use crate::tailwind::TailwindResolver;

/// Render options passed from Python.
#[pyclass]
#[derive(Debug, Clone)]
pub struct RenderOptions {
    /// Page size: "a4", "letter", "legal", or custom "WxH" in mm.
    #[pyo3(get, set)]
    pub page_size: String,
    /// Page margins in mm [top, right, bottom, left].
    #[pyo3(get, set)]
    pub margins: Vec<f64>,
    /// Document title.
    #[pyo3(get, set)]
    pub title: String,
    /// Document author.
    #[pyo3(get, set)]
    pub author: String,
    /// Enable Tailwind CSS class resolution.
    #[pyo3(get, set)]
    pub tailwind: bool,
    /// Base path for resolving relative file references.
    #[pyo3(get, set)]
    pub base_path: String,
    /// Header HTML template.
    #[pyo3(get, set)]
    pub header_html: String,
    /// Footer HTML template.
    #[pyo3(get, set)]
    pub footer_html: String,
}

#[pymethods]
impl RenderOptions {
    #[new]
    #[pyo3(signature = (
        page_size = "a4".to_string(),
        margins = vec![20.0, 15.0, 20.0, 15.0],
        title = String::new(),
        author = String::new(),
        tailwind = false,
        base_path = String::new(),
        header_html = String::new(),
        footer_html = String::new(),
    ))]
    fn new(
        page_size: String,
        margins: Vec<f64>,
        title: String,
        author: String,
        tailwind: bool,
        base_path: String,
        header_html: String,
        footer_html: String,
    ) -> Self {
        Self {
            page_size,
            margins,
            title,
            author,
            tailwind,
            base_path,
            header_html,
            footer_html,
        }
    }
}

impl RenderOptions {
    fn to_page_layout(&self) -> PageLayout {
        let size = match self.page_size.to_lowercase().as_str() {
            "a4" => PageSize::a4(),
            "letter" => PageSize::letter(),
            "legal" => PageSize::legal(),
            custom => {
                // Parse "WxH" format in mm
                let parts: Vec<&str> = custom.split('x').collect();
                if parts.len() == 2 {
                    let w = parts[0].parse::<f64>().unwrap_or(210.0);
                    let h = parts[1].parse::<f64>().unwrap_or(297.0);
                    PageSize::custom(w, h)
                } else {
                    PageSize::a4()
                }
            }
        };

        let margins = if self.margins.len() == 4 {
            (
                self.margins[0] * 96.0 / 25.4,
                self.margins[1] * 96.0 / 25.4,
                self.margins[2] * 96.0 / 25.4,
                self.margins[3] * 96.0 / 25.4,
            )
        } else {
            let m = 20.0 * 96.0 / 25.4; // 20mm default
            (m, m, m, m)
        };

        let mut layout = PageLayout::new(size).with_margins(margins.0, margins.1, margins.2, margins.3);

        if !self.header_html.is_empty() {
            layout.header_html = Some(self.header_html.clone());
            layout.header_height = 40.0; // ~10mm
        }

        if !self.footer_html.is_empty() {
            layout.footer_html = Some(self.footer_html.clone());
            layout.footer_height = 40.0;
        }

        layout
    }

    fn to_pdf_config(&self) -> PdfConfig {
        PdfConfig {
            title: if self.title.is_empty() { None } else { Some(self.title.clone()) },
            author: if self.author.is_empty() { None } else { Some(self.author.clone()) },
            ..PdfConfig::default()
        }
    }
}

/// The main PDF engine class exposed to Python.
#[pyclass]
pub struct PdfEngine {
    font_cache: Arc<FontCache>,
    image_cache: Arc<ImageCache>,
}

#[pymethods]
impl PdfEngine {
    #[new]
    fn new() -> Self {
        Self {
            font_cache: Arc::new(FontCache::default()),
            image_cache: Arc::new(ImageCache::default()),
        }
    }

    /// Register a custom font from a file path.
    #[pyo3(signature = (family, path, weight = None, italic = None))]
    fn register_font(
        &self,
        family: &str,
        path: &str,
        weight: Option<u32>,
        italic: Option<bool>,
    ) -> PyResult<()> {
        self.font_cache
            .register_font_file(family, weight.unwrap_or(400), italic.unwrap_or(false), path)
            .map_err(|e| pyo3::exceptions::PyRuntimeError::new_err(e.to_string()))
    }

    /// Set the base path for resolving relative paths.
    fn set_base_path(&self, path: &str) {
        self.image_cache.set_base_path(path);
    }

    /// Render HTML + CSS to PDF bytes.
    #[pyo3(signature = (html, css = None, options = None))]
    fn render<'py>(
        &self,
        py: Python<'py>,
        html: &str,
        css: Option<&str>,
        options: Option<&RenderOptions>,
    ) -> PyResult<Bound<'py, PyBytes>> {
        let bytes = self.render_internal(html, css.unwrap_or(""), options)?;
        Ok(PyBytes::new_bound(py, &bytes))
    }

    /// Render HTML + CSS and save to a file.
    #[pyo3(signature = (html, output, css = None, options = None))]
    fn render_to_file(
        &self,
        html: &str,
        output: &str,
        css: Option<&str>,
        options: Option<&RenderOptions>,
    ) -> PyResult<()> {
        let bytes = self.render_internal(html, css.unwrap_or(""), options)?;
        std::fs::write(output, bytes)
            .map_err(|e| pyo3::exceptions::PyIOError::new_err(e.to_string()))
    }

    /// Batch render multiple documents in parallel.
    #[pyo3(signature = (documents, options = None))]
    fn batch_render<'py>(
        &self,
        py: Python<'py>,
        documents: Vec<(String, String)>, // (html, css) pairs
        options: Option<&RenderOptions>,
    ) -> PyResult<Vec<Bound<'py, PyBytes>>> {
        let font_cache = self.font_cache.clone();
        // Use rayon for parallel rendering
        let results: Vec<Result<Vec<u8>, FastPdfError>> = documents
            .par_iter()
            .map(|(html, css)| {
                let default_opts = RenderOptions::new(
                    "a4".to_string(),
                    vec![20.0, 15.0, 20.0, 15.0],
                    String::new(),
                    String::new(),
                    false,
                    String::new(),
                    String::new(),
                    String::new(),
                );
                let opts = options.unwrap_or(&default_opts);
                render_pipeline(html, css, opts, Some(font_cache.clone()))
            })
            .collect();

        results
            .into_iter()
            .map(|r| {
                let bytes = r.map_err(|e| pyo3::exceptions::PyRuntimeError::new_err(e.to_string()))?;
                Ok(PyBytes::new_bound(py, &bytes))
            })
            .collect()
    }
}

impl PdfEngine {
    fn render_internal(
        &self,
        html: &str,
        css: &str,
        options: Option<&RenderOptions>,
    ) -> PyResult<Vec<u8>> {
        let default_opts = RenderOptions::new(
            "a4".to_string(),
            vec![20.0, 15.0, 20.0, 15.0],
            String::new(),
            String::new(),
            false,
            String::new(),
            String::new(),
            String::new(),
        );
        let opts = options.unwrap_or(&default_opts);

        render_pipeline(html, css, opts, Some(self.font_cache.clone()))
            .map_err(|e| pyo3::exceptions::PyRuntimeError::new_err(e.to_string()))
    }
}

/// A Python-facing PDF document wrapper.
#[pyclass]
pub struct PdfDocument {
    data: Vec<u8>,
    page_count: usize,
}

#[pymethods]
impl PdfDocument {
    /// Get the PDF as bytes.
    fn to_bytes<'py>(&self, py: Python<'py>) -> Bound<'py, PyBytes> {
        PyBytes::new_bound(py, &self.data)
    }

    /// Save the PDF to a file.
    fn save(&self, path: &str) -> PyResult<()> {
        std::fs::write(path, &self.data)
            .map_err(|e| pyo3::exceptions::PyIOError::new_err(e.to_string()))
    }

    /// Get the number of pages.
    #[getter]
    fn page_count(&self) -> usize {
        self.page_count
    }

    /// Get the size in bytes.
    #[getter]
    fn size(&self) -> usize {
        self.data.len()
    }
}

/// The core rendering pipeline.
fn render_pipeline(
    html: &str,
    css: &str,
    options: &RenderOptions,
    font_cache: Option<Arc<FontCache>>,
) -> Result<Vec<u8>, FastPdfError> {
    // 1. Parse HTML
    let dom = HtmlParser::parse_fragment(html)?;

    // 2. Parse CSS
    let mut stylesheets = Vec::new();

    // Extract inline <style> elements
    for style_text in dom.extract_styles() {
        let sheet = CssParser::parse(&style_text)?;
        stylesheets.push(sheet);
    }

    // Parse external CSS
    if !css.is_empty() {
        let sheet = CssParser::parse(css)?;
        stylesheets.push(sheet);
    }

    // 3. Tailwind CSS resolution
    if options.tailwind {
        let classes = TailwindResolver::extract_classes_from_html(html);
        let tw_sheet = TailwindResolver::resolve_classes(&classes);
        stylesheets.push(tw_sheet);
    }

    // 4. Layout
    let page_layout = options.to_page_layout();
    let mut engine = LayoutEngine::new(page_layout);
    if let Some(ref cache) = font_cache {
        engine = engine.with_font_cache(Arc::clone(cache));
    }
    let pages = engine.layout(&dom, &stylesheets)?;

    // 5. Render to paint commands
    let renderer = Renderer::new();
    let page_commands = renderer.render_pages(&pages);

    // 6. Generate PDF
    let pdf_config = options.to_pdf_config();
    let mut generator = PdfGenerator::new(pdf_config);
    if let Some(cache) = font_cache {
        generator = generator.with_font_cache(cache);
    }
    let bytes = generator.generate(&pages, &page_commands)?;

    Ok(bytes)
}

// ── Standalone Python functions ──

/// Render HTML to PDF and save to a file.
#[pyfunction]
#[pyo3(signature = (html, output, css = None, options = None))]
pub fn render_html_to_pdf(
    html: &str,
    output: &str,
    css: Option<&str>,
    options: Option<&RenderOptions>,
) -> PyResult<()> {
    let default_opts = RenderOptions::new(
        "a4".to_string(),
        vec![20.0, 15.0, 20.0, 15.0],
        String::new(),
        String::new(),
        false,
        String::new(),
        String::new(),
        String::new(),
    );
    let opts = options.unwrap_or(&default_opts);

    let bytes = render_pipeline(html, css.unwrap_or(""), opts, None)
        .map_err(|e| pyo3::exceptions::PyRuntimeError::new_err(e.to_string()))?;

    std::fs::write(output, bytes)
        .map_err(|e| pyo3::exceptions::PyIOError::new_err(e.to_string()))
}

/// Render HTML to PDF and return as bytes.
#[pyfunction]
#[pyo3(signature = (html, css = None, options = None))]
pub fn render_html_to_pdf_bytes<'py>(
    py: Python<'py>,
    html: &str,
    css: Option<&str>,
    options: Option<&RenderOptions>,
) -> PyResult<Bound<'py, PyBytes>> {
    let default_opts = RenderOptions::new(
        "a4".to_string(),
        vec![20.0, 15.0, 20.0, 15.0],
        String::new(),
        String::new(),
        false,
        String::new(),
        String::new(),
        String::new(),
    );
    let opts = options.unwrap_or(&default_opts);

    let bytes = render_pipeline(html, css.unwrap_or(""), opts, None)
        .map_err(|e| pyo3::exceptions::PyRuntimeError::new_err(e.to_string()))?;

    Ok(PyBytes::new_bound(py, &bytes))
}

/// Render multiple documents in parallel.
#[pyfunction]
#[pyo3(signature = (documents, options = None))]
pub fn batch_render<'py>(
    py: Python<'py>,
    documents: Vec<(String, String)>,
    options: Option<&RenderOptions>,
) -> PyResult<Vec<Bound<'py, PyBytes>>> {
    let default_opts = RenderOptions::new(
        "a4".to_string(),
        vec![20.0, 15.0, 20.0, 15.0],
        String::new(),
        String::new(),
        false,
        String::new(),
        String::new(),
        String::new(),
    );
    let opts = options.unwrap_or(&default_opts);

    let results: Vec<Result<Vec<u8>, FastPdfError>> = documents
        .par_iter()
        .map(|(html, css)| render_pipeline(html, css, opts, None))
        .collect();

    results
        .into_iter()
        .map(|r| {
            let bytes = r.map_err(|e| pyo3::exceptions::PyRuntimeError::new_err(e.to_string()))?;
            Ok(PyBytes::new_bound(py, &bytes))
        })
        .collect()
}

/// Get the engine version.
#[pyfunction]
pub fn get_version() -> String {
    env!("CARGO_PKG_VERSION").to_string()
}
