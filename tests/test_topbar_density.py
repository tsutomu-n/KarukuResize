from karuku_resizer.gui_app import TOPBAR_DENSITY_COMPACT_MAX_WIDTH, ResizeApp


def test_topbar_density_is_compact_at_threshold() -> None:
    assert ResizeApp._topbar_density_for_width(TOPBAR_DENSITY_COMPACT_MAX_WIDTH - 1) == "compact"
    assert ResizeApp._topbar_density_for_width(TOPBAR_DENSITY_COMPACT_MAX_WIDTH) == "compact"


def test_topbar_density_switches_to_normal_above_threshold() -> None:
    assert ResizeApp._topbar_density_for_width(TOPBAR_DENSITY_COMPACT_MAX_WIDTH + 1) == "normal"


def test_batch_button_text_changes_with_density() -> None:
    assert ResizeApp._batch_button_text_for_density("normal") == "一括適用保存"
    assert ResizeApp._batch_button_text_for_density("compact") == "一括保存"
