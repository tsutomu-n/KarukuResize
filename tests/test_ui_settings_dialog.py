"""Tests for settings dialog helpers and apply contract."""

from __future__ import annotations

from typing import Any

from karuku_resizer.gui_app import ResizeApp
from karuku_resizer.ui_settings_dialog import (
    SettingsDialogResult,
    _resolve_output_format_label,
)


class _DummyVar:
    def __init__(self, value: str = "") -> None:
        self.value = value

    def get(self) -> str:
        return self.value

    def set(self, value: str) -> None:
        self.value = value


class _DummyTooltipManager:
    def __init__(self) -> None:
        self.hidden = 0

    def hide(self) -> None:
        self.hidden += 1


class _DummyResizeAppForSettings:
    def __init__(self) -> None:
        self.ui_mode_var = _DummyVar("off")
        self.appearance_mode_var = _DummyVar("system")
        self.zoom_var = _DummyVar("100%")
        self.quality_var = _DummyVar("85")
        self.output_format_var = _DummyVar("自動")
        self.settings: dict[str, Any] = {}
        self.calls: list[tuple[Any, ...]] = []
        self._ui_scale_mode = "normal"
        self._tooltip_manager = _DummyTooltipManager()
        self.current_index = None
        self.jobs: list[Any] = []

    def _normalize_ui_scale_mode(self, value: str) -> str:
        return value

    def _apply_ui_mode(self) -> None:
        self.calls.append(("apply_ui_mode",))

    def _apply_user_appearance_mode(self, appearance_id: str, redraw: bool) -> None:
        self.calls.append(("apply_user_appearance_mode", appearance_id, redraw))

    def _apply_ui_scale_mode(self, mode: str) -> None:
        self.calls.append(("apply_ui_scale_mode", mode))

    def _apply_zoom_selection(self) -> None:
        self.calls.append(("apply_zoom_selection", self.zoom_var.get()))

    def _on_output_format_changed(self, value: str) -> None:
        self.calls.append(("on_output_format_changed", value))

    def _on_quality_changed(self, value: str) -> None:
        self.calls.append(("on_quality_changed", value))

    def _update_settings_summary(self) -> None:
        self.calls.append(("update_settings_summary",))

    def _save_current_settings(self) -> None:
        self.calls.append(("save_current_settings",))

    def _refresh_status_indicators(self) -> None:
        self.calls.append(("refresh_status_indicators",))

    def _appearance_mode_id(self) -> str:
        return "system"


def test_resolve_output_format_label_uses_default_setting_not_first_label() -> None:
    defaults = {"output_format": "jpeg"}
    available_output_formats = ["自動", "PNG", "JPEG", "WEBP"]
    selected = _resolve_output_format_label(
        defaults,
        output_format_id_to_label={"jpeg": "JPEG", "auto": "自動"},
        output_format_fallback_label="自動",
        available_output_formats=available_output_formats,
    )
    assert selected == "JPEG"


def test_apply_settings_dialog_result_updates_app_state_and_calls_handlers() -> None:
    app = _DummyResizeAppForSettings()
    result = SettingsDialogResult(
        ui_mode_label="Pro",
        appearance_label="ライト",
        ui_scale_label="通常",
        zoom_preference="200%",
        quality="90",
        output_format_label="JPEG",
        pro_input_mode_id="recursive",
        default_preset_id="preset_1",
        default_output_dir="/tmp/output",
        show_tooltips=False,
    )

    ResizeApp._apply_settings_dialog_result(app, result)

    assert app.ui_mode_var.get() == "Pro"
    assert app.appearance_mode_var.get() == "ライト"
    assert app.zoom_var.get() == "200%"
    assert app.quality_var.get() == "90"
    assert app.output_format_var.get() == "JPEG"
    assert app.settings["pro_input_mode"] == "recursive"
    assert app.settings["default_output_dir"] == "/tmp/output"
    assert app.settings["default_preset_id"] == "preset_1"
    assert app.settings["show_tooltips"] is False
    assert app._tooltip_manager.hidden == 1
    assert ("apply_ui_scale_mode", "normal") in app.calls
    assert ("apply_user_appearance_mode", "system", True) in app.calls
    assert ("on_output_format_changed", "JPEG") in app.calls
    assert ("on_quality_changed", "90") in app.calls
    assert ("save_current_settings",) in app.calls
