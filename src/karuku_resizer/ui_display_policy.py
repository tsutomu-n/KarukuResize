"""Display policy helpers for shared UI behavior."""

from __future__ import annotations

from dataclasses import dataclass


TOPBAR_DENSITY_COMPACT_MAX_WIDTH = 1366


@dataclass(frozen=True)
class TopActionGuideState:
    """Runtime flags used for top action guide text."""

    is_loading_files: bool
    is_processing: bool


def effective_topbar_window_width(window_width: int, ui_scale_factor: float = 1.0) -> int:
    """Return width used for density calculation after UI scale correction."""
    scale = ui_scale_factor if ui_scale_factor > 1.0 else 1.0
    return max(1, round(window_width / scale))


def topbar_density_for_width(window_width: int, ui_scale_factor: float = 1.0) -> str:
    """Return compact/normal density for the effective topbar width."""
    return (
        "compact"
        if effective_topbar_window_width(window_width, ui_scale_factor) <= TOPBAR_DENSITY_COMPACT_MAX_WIDTH
        else "normal"
    )


def topbar_batch_button_text(density: str) -> str:
    """Return density-dependent label for the batch action."""
    return "一括保存" if density == "compact" else "一括適用保存"


def should_show_pro_elements(is_pro_mode: bool) -> bool:
    """Whether Pro-only topbar elements should be visible."""
    return bool(is_pro_mode)


def top_action_guide_text(state: TopActionGuideState) -> str:
    """Build guide text for loading/processing states."""
    if state.is_loading_files:
        return "画像読み込み中…"
    if state.is_processing:
        return "処理中 — キャンセル以外の操作はできません"
    return ""

