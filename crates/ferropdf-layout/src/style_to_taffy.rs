use taffy::prelude::*;
use ferropdf_core::{ComputedStyle, Length};

/// Convertir ComputedStyle → taffy::Style
/// Taffy gère automatiquement :
/// - width:100% résolu par rapport au containing block (Fix 1)
/// - padding soustrait une seule fois (Fix 2)
/// - flex, grid, block layout
pub fn convert(style: &ComputedStyle) -> taffy::Style {
    taffy::Style {
        display: match style.display {
            ferropdf_core::Display::Block       => Display::Block,
            ferropdf_core::Display::Flex        => Display::Flex,
            ferropdf_core::Display::Grid        => Display::Grid,
            ferropdf_core::Display::None        => Display::None,
            // Inline et InlineBlock traités comme Block pour le PDF
            _                                   => Display::Block,
        },

        size: Size {
            width:  length_to_dim(&style.width),
            height: length_to_dim(&style.height),
        },
        min_size: Size {
            width:  length_to_dim(&style.min_width),
            height: length_to_dim(&style.min_height),
        },
        max_size: Size {
            width:  length_to_dim(&style.max_width),
            height: length_to_dim(&style.max_height),
        },

        // IMPORTANT : Taffy gère le padding correctement — ne pas le recalculer
        padding: taffy::Rect {
            top:    lp(&style.padding[0]),
            right:  lp(&style.padding[1]),
            bottom: lp(&style.padding[2]),
            left:   lp(&style.padding[3]),
        },
        border: taffy::Rect {
            top:    LengthPercentage::Length(style.border_top.width),
            right:  LengthPercentage::Length(style.border_right.width),
            bottom: LengthPercentage::Length(style.border_bottom.width),
            left:   LengthPercentage::Length(style.border_left.width),
        },
        margin: taffy::Rect {
            top:    lpa(&style.margin[0]),
            right:  lpa(&style.margin[1]),
            bottom: lpa(&style.margin[2]),
            left:   lpa(&style.margin[3]),
        },

        flex_direction: match style.flex_direction {
            ferropdf_core::FlexDirection::Row           => FlexDirection::Row,
            ferropdf_core::FlexDirection::Column        => FlexDirection::Column,
            ferropdf_core::FlexDirection::RowReverse    => FlexDirection::RowReverse,
            ferropdf_core::FlexDirection::ColumnReverse => FlexDirection::ColumnReverse,
        },
        flex_wrap: match style.flex_wrap {
            ferropdf_core::FlexWrap::NoWrap      => FlexWrap::NoWrap,
            ferropdf_core::FlexWrap::Wrap        => FlexWrap::Wrap,
            ferropdf_core::FlexWrap::WrapReverse => FlexWrap::WrapReverse,
        },
        justify_content: Some(match style.justify_content {
            ferropdf_core::JustifyContent::FlexStart    => JustifyContent::FlexStart,
            ferropdf_core::JustifyContent::FlexEnd      => JustifyContent::FlexEnd,
            ferropdf_core::JustifyContent::Center       => JustifyContent::Center,
            ferropdf_core::JustifyContent::SpaceBetween => JustifyContent::SpaceBetween,
            ferropdf_core::JustifyContent::SpaceAround  => JustifyContent::SpaceAround,
            ferropdf_core::JustifyContent::SpaceEvenly  => JustifyContent::SpaceEvenly,
        }),
        align_items: Some(match style.align_items {
            ferropdf_core::AlignItems::Stretch   => AlignItems::Stretch,
            ferropdf_core::AlignItems::FlexStart => AlignItems::FlexStart,
            ferropdf_core::AlignItems::FlexEnd   => AlignItems::FlexEnd,
            ferropdf_core::AlignItems::Center    => AlignItems::Center,
            ferropdf_core::AlignItems::Baseline  => AlignItems::Baseline,
        }),
        flex_grow:   style.flex_grow,
        flex_shrink: style.flex_shrink,
        flex_basis:  length_to_dim(&style.flex_basis),
        gap: Size {
            width:  lp(&style.column_gap),
            height: lp(&style.row_gap),
        },

        ..Default::default()
    }
}

fn length_to_dim(l: &Length) -> Dimension {
    match l {
        Length::Px(v)      => Dimension::Length(*v),
        Length::Percent(v) => Dimension::Percent(v / 100.0),
        Length::Auto       => Dimension::Auto,
        Length::Zero       => Dimension::Length(0.0),
        Length::None       => Dimension::Auto,
        other => {
            log::warn!("Unresolved length passed to Taffy: {:?}", other);
            Dimension::Auto
        }
    }
}

fn lp(l: &Length) -> LengthPercentage {
    match l {
        Length::Px(v)      => LengthPercentage::Length(*v),
        Length::Percent(v) => LengthPercentage::Percent(v / 100.0),
        Length::Zero       => LengthPercentage::Length(0.0),
        _                  => LengthPercentage::Length(0.0),
    }
}

fn lpa(l: &Length) -> LengthPercentageAuto {
    match l {
        Length::Px(v)      => LengthPercentageAuto::Length(*v),
        Length::Percent(v) => LengthPercentageAuto::Percent(v / 100.0),
        Length::Auto       => LengthPercentageAuto::Auto,
        Length::Zero       => LengthPercentageAuto::Length(0.0),
        _                  => LengthPercentageAuto::Auto,
    }
}
