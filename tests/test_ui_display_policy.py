from karuku_resizer.ui_display_policy import (
    TOPBAR_DENSITY_COMPACT_MAX_WIDTH,
    TopActionGuideState,
    effective_topbar_window_width,
    top_action_guide_text,
    topbar_batch_button_text,
    topbar_density_for_width,
)


def test_density_is_compact_at_or_below_threshold() -> None:
    assert topbar_density_for_width(TOPBAR_DENSITY_COMPACT_MAX_WIDTH) == "compact"
    assert topbar_density_for_width(TOPBAR_DENSITY_COMPACT_MAX_WIDTH - 1) == "compact"


def test_density_switches_to_normal_above_threshold() -> None:
    assert topbar_density_for_width(TOPBAR_DENSITY_COMPACT_MAX_WIDTH + 1) == "normal"


def test_density_respects_ui_scale_correction() -> None:
    assert effective_topbar_window_width(1537, 1.125) == 1366
    assert topbar_density_for_width(1538, 1.125) == "normal"


def test_batch_label_is_compact_and_normal() -> None:
    assert topbar_batch_button_text("compact") == "一括適用保存"
    assert topbar_batch_button_text("normal") == "一括適用保存"


def test_top_action_guide_state_text() -> None:
    assert top_action_guide_text(TopActionGuideState(is_loading_files=True, is_processing=False)) == "画像読み込み中…"
    assert top_action_guide_text(TopActionGuideState(is_loading_files=False, is_processing=True)) == "処理中 — キャンセル以外の操作はできません"
    assert top_action_guide_text(TopActionGuideState(is_loading_files=False, is_processing=False)) == ""
