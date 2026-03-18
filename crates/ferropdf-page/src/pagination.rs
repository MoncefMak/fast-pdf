// =============================================================================
// pagination.rs — Algorithme de fragmentation et pagination PDF
// =============================================================================
// Source d'inspiration :
//   CSS Fragmentation Module Level 3
//   https://www.w3.org/TR/css-break-3/
//
//   Blink fragmentation utils :
//   blink/renderer/core/layout/fragmentation_utils.cc
//   blink/renderer/core/layout/ng/ng_block_break_token.cc
//
// Ce module s'exécute APRÈS Taffy + block_flow.
// Il prend le LayoutTree (ruban infini de contenu) et le découpe en pages.
//
// MODÈLE MENTAL :
//   Le ruban de contenu infini (positions Y de 0 à +∞) est découpé
//   en pages. On parcourt les blocs enfants de la racine et on les
//   place un par un sur la page courante. Quand un bloc ne tient pas,
//   on le fragmente (récursivement dans ses enfants) ou on le pousse
//   sur la page suivante.
//
//   La variable clé est `page_y_offset` : la coordonnée Y absolue
//   dans le ruban qui correspond à Y=0 sur la page courante.
//   Pour repositionner un bloc sur la page :
//     y_on_page = y_absolute - page_y_offset
// =============================================================================

use ferropdf_core::{LayoutBox, PageConfig, PageBreak, PageBreakInside, Rect, Insets};
use ferropdf_core::layout::Page;

// =============================================================================
// STRUCTURES DE DONNÉES
// =============================================================================

/// État courant du paginateur — inspiré de FragmentainerContext dans Blink.
#[derive(Debug)]
struct PaginationContext {
    /// Position Y absolue (dans le ruban) correspondant au haut de la page courante.
    page_y_offset: f32,
    /// Hauteur consommée sur la page courante (pour savoir combien d'espace reste).
    used_height: f32,
    /// Contenu de la page en cours de construction.
    current_page_boxes: Vec<LayoutBox>,
    /// Pages déjà terminées.
    finished_pages: Vec<Page>,
    /// Hauteur d'une page (content area, en CSS pixels).
    page_height: f32,
}

impl PaginationContext {
    fn new(page_height: f32) -> Self {
        Self {
            page_y_offset: 0.0,
            used_height: 0.0,
            current_page_boxes: Vec::new(),
            finished_pages: Vec::new(),
            page_height,
        }
    }

    /// Espace restant sur la page courante.
    fn remaining_height(&self) -> f32 {
        (self.page_height - self.used_height).max(0.0)
    }

    /// Flush la page courante et commence une nouvelle.
    /// `next_y` est la position Y absolue du prochain élément à placer
    /// (utilisé pour définir page_y_offset de la nouvelle page).
    fn flush_page(&mut self, next_y: f32) {
        if !self.current_page_boxes.is_empty() {
            let page_number = self.finished_pages.len() as u32 + 1;
            self.finished_pages.push(Page {
                page_number,
                total_pages: 0,
                content: std::mem::take(&mut self.current_page_boxes),
                margin_boxes: Vec::new(),
            });
        }
        self.page_y_offset = next_y;
        self.used_height = 0.0;
    }

    fn is_current_page_empty(&self) -> bool {
        self.current_page_boxes.is_empty()
    }
}

// =============================================================================
// POINT D'ENTRÉE PRINCIPAL
// =============================================================================

/// Fragmente un LayoutTree root en pages PDF.
pub fn paginate(root: &LayoutBox, config: &PageConfig) -> Vec<Page> {
    let page_height = config.content_height_px();
    let mut ctx = PaginationContext::new(page_height);

    // Traiter les enfants directs de la racine
    for child in &root.children {
        fragment_box(child, &mut ctx);
    }

    // Flush la dernière page si non vide
    if !ctx.is_current_page_empty() {
        ctx.flush_page(0.0);
    }

    // Si aucune page n'a été produite, créer une page vide
    if ctx.finished_pages.is_empty() {
        ctx.finished_pages.push(Page {
            page_number: 1,
            total_pages: 1,
            content: Vec::new(),
            margin_boxes: Vec::new(),
        });
    }

    // Update total_pages
    let total = ctx.finished_pages.len() as u32;
    for page in &mut ctx.finished_pages {
        page.total_pages = total;
    }

    ctx.finished_pages
}

// =============================================================================
// FRAGMENTATION D'UN LAYOUT BOX
// CSS Fragmentation Level 3 §4 — Fragmentation Model
// =============================================================================

fn fragment_box(layout_box: &LayoutBox, ctx: &mut PaginationContext) {
    let style = &layout_box.style;
    let box_height = layout_box.rect.height;

    // ─── Règle 1 : page-break-before ────────────────────────────────────────
    if should_break_before(style) && !ctx.is_current_page_empty() {
        ctx.flush_page(layout_box.rect.y);
    }

    // ─── Position-based fit check ────────────────────────────────────────────
    // Check if the box, at its actual ribbon position, fits within the current page.
    let box_bottom_on_page = (layout_box.rect.y - ctx.page_y_offset) + box_height;
    let fits_on_current_page = box_bottom_on_page <= ctx.page_height;
    let fits_on_new_page = box_height <= ctx.page_height;

    // ─── Règle 2 : page-break-inside: avoid ─────────────────────────────────
    let avoid_break_inside = style.page_break_inside == PageBreakInside::Avoid;

    if !fits_on_current_page && avoid_break_inside {
        if fits_on_new_page {
            if !ctx.is_current_page_empty() {
                ctx.flush_page(layout_box.rect.y);
            }
            place_box_on_current_page(layout_box, ctx);
            if should_break_after(style) {
                ctx.flush_page(layout_box.rect.y + layout_box.rect.height);
            }
            return;
        }
        // Le bloc est plus grand qu'une page → on ne peut pas éviter la coupure.
    }

    // ─── Règle 3 : Le bloc tient sur la page courante ───────────────────────
    if fits_on_current_page {
        place_box_on_current_page(layout_box, ctx);
        if should_break_after(style) {
            ctx.flush_page(layout_box.rect.y + layout_box.rect.height);
        }
        return;
    }

    // ─── Règle 4 : Le bloc ne tient pas → fragmentation ─────────────────────
    if !layout_box.children.is_empty() {
        // Create a container fragment on the current page (preserves background/borders)
        fragment_container(layout_box, ctx);
    } else {
        // Boîte feuille (texte, image, etc.)
        if ctx.is_current_page_empty() {
            // Force : même trop grande, on la met sur la page vide (anti-boucle infinie)
            place_box_on_current_page(layout_box, ctx);
            ctx.flush_page(layout_box.rect.y + layout_box.rect.height);
        } else {
            // Pousse sur la page suivante
            ctx.flush_page(layout_box.rect.y);
            place_box_on_current_page(layout_box, ctx);
            if box_height > ctx.page_height {
                ctx.flush_page(layout_box.rect.y + layout_box.rect.height);
            }
        }
    }

    // ─── Règle 5 : page-break-after ─────────────────────────────────────────
    if should_break_after(style) && !ctx.is_current_page_empty() {
        ctx.flush_page(layout_box.rect.y + layout_box.rect.height);
    }
}

// =============================================================================
// FRAGMENTATION D'UN CONTENEUR
// Quand un conteneur ne tient pas sur la page courante, on distribue
// ses enfants entre la page courante et les suivantes, en créant des
// "wrapper fragments" sur chaque page pour préserver le contexte visuel
// (background, borders) du conteneur parent.
// =============================================================================

fn fragment_container(layout_box: &LayoutBox, ctx: &mut PaginationContext) {
    // Collect children that go on the current page vs next pages
    let mut current_page_children: Vec<LayoutBox> = Vec::new();
    let mut is_first_page = true;

    for child in &layout_box.children {
        let child_height = child.rect.height;
        // Position-based fit check: does this child's bottom fit on the current page?
        let child_bottom_on_page = (child.rect.y - ctx.page_y_offset) + child_height;
        let child_fits = child_bottom_on_page <= ctx.page_height;

        if child_fits {
            // Child fits on current page — add to current wrapper
            let mut placed_child = child.clone();
            offset_y_recursive(&mut placed_child, -ctx.page_y_offset);
            current_page_children.push(placed_child);
            ctx.used_height = ctx.used_height.max(child_bottom_on_page);
        } else if !child.children.is_empty() && child_height > ctx.page_height {
            // Child is a large container that doesn't fit on any single page
            // Flush current wrapper first, then recurse into this child
            if !current_page_children.is_empty() {
                let wrapper = make_container_fragment(layout_box, &current_page_children, ctx, is_first_page, false);
                ctx.current_page_boxes.push(wrapper);
                current_page_children.clear();
            }
            // Recurse into the child's own fragmentation
            fragment_box(child, ctx);
            is_first_page = false;
        } else {
            // Child doesn't fit — flush current page and start new
            if !current_page_children.is_empty() || !ctx.is_current_page_empty() {
                if !current_page_children.is_empty() {
                    let wrapper = make_container_fragment(layout_box, &current_page_children, ctx, is_first_page, false);
                    ctx.current_page_boxes.push(wrapper);
                    current_page_children.clear();
                }
                ctx.flush_page(child.rect.y);
                is_first_page = false;
            }

            // Place child on new page
            let mut placed_child = child.clone();
            offset_y_recursive(&mut placed_child, -ctx.page_y_offset);
            let child_bottom = placed_child.rect.y + placed_child.rect.height;
            current_page_children.push(placed_child);
            ctx.used_height = ctx.used_height.max(child_bottom);
        }
    }

    // Flush remaining children as a wrapper on the current page
    if !current_page_children.is_empty() {
        let wrapper = make_container_fragment(layout_box, &current_page_children, ctx, is_first_page, true);
        ctx.current_page_boxes.push(wrapper);
    }
}

/// Create a container fragment (partial copy of the parent) that wraps
/// a subset of children for one page. Preserves background, borders, etc.
fn make_container_fragment(
    parent: &LayoutBox,
    children: &[LayoutBox],
    ctx: &PaginationContext,
    is_first_fragment: bool,
    is_last_fragment: bool,
) -> LayoutBox {
    // Compute bounding box of children on this page
    let min_y = children.iter().map(|c| c.rect.y).fold(f32::MAX, f32::min);
    let max_bottom = children.iter()
        .map(|c| c.rect.y + c.rect.height)
        .fold(0.0f32, f32::max);
    let fragment_height = max_bottom - min_y
        + if is_first_fragment { parent.padding.top + parent.border.top } else { 0.0 }
        + if is_last_fragment { parent.padding.bottom + parent.border.bottom } else { 0.0 };

    let page_rel_y = (parent.rect.y - ctx.page_y_offset).max(0.0);
    let y = if is_first_fragment { page_rel_y } else { 0.0 };

    let rect = Rect::new(parent.rect.x, y, parent.rect.width, fragment_height);
    let content = Rect::new(
        parent.content.x,
        y + if is_first_fragment { parent.padding.top + parent.border.top } else { 0.0 },
        parent.content.width,
        (fragment_height - parent.padding.vertical() - parent.border.vertical()).max(0.0),
    );

    LayoutBox {
        node_id: parent.node_id,
        style: parent.style.clone(),
        rect,
        content,
        padding: if is_first_fragment { parent.padding } else {
            Insets { top: 0.0, ..parent.padding }
        },
        border: if is_first_fragment { parent.border } else {
            Insets { top: 0.0, ..parent.border }
        },
        margin: Insets::zero(),
        children: children.to_vec(),
        shaped_lines: Vec::new(),
        image_src: None,
        text_content: None,
        out_of_flow: false,
        visual_offset_x: 0.0,
        visual_offset_y: 0.0,
    }
}

// =============================================================================
// PLACEMENT D'UNE BOX SUR LA PAGE COURANTE
// Repositionnement Y : y_page = y_absolute - page_y_offset
// =============================================================================

fn place_box_on_current_page(layout_box: &LayoutBox, ctx: &mut PaginationContext) {
    let mut placed_box = layout_box.clone();
    offset_y_recursive(&mut placed_box, -ctx.page_y_offset);

    // Track the actual bottom extent on the page (not sum of heights)
    let box_bottom = placed_box.rect.y + placed_box.rect.height;
    ctx.used_height = ctx.used_height.max(box_bottom);
    ctx.current_page_boxes.push(placed_box);
}

/// Recursively offset all Y coordinates in a LayoutBox tree.
fn offset_y_recursive(layout_box: &mut LayoutBox, dy: f32) {
    layout_box.rect.y += dy;
    layout_box.content.y += dy;
    for child in &mut layout_box.children {
        offset_y_recursive(child, dy);
    }
}

// =============================================================================
// HELPERS — Détection des règles CSS de fragmentation
// =============================================================================

fn should_break_before(style: &ferropdf_core::ComputedStyle) -> bool {
    matches!(
        style.page_break_before,
        PageBreak::Always | PageBreak::Page | PageBreak::Left | PageBreak::Right
    )
}

fn should_break_after(style: &ferropdf_core::ComputedStyle) -> bool {
    matches!(
        style.page_break_after,
        PageBreak::Always | PageBreak::Page | PageBreak::Left | PageBreak::Right
    )
}

/// Crée une page vide.
pub fn create_empty_page(_config: &PageConfig) -> Page {
    Page {
        page_number: 1,
        total_pages: 1,
        content: Vec::new(),
        margin_boxes: Vec::new(),
    }
}
