from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace
from typing import Any

from karuku_resizer import ui_bootstrap


class _StatusVar:
    def __init__(self) -> None:
        self.value = ""

    def set(self, value: str) -> None:
        self.value = value


class _DummyApp:
    def __init__(self) -> None:
        self._visible_job_indices = [1]
        self.jobs = [
            SimpleNamespace(path=Path("first.jpg")),
            SimpleNamespace(path=Path("second.jpg")),
        ]
        self.current_index: int | None = None
        self.file_list_panel_refs = object()
        self.status_var = _StatusVar()
        self.drawn_job: Any = None
        self.metadata_job: Any = None
        self.refresh_count = 0

    def _reset_zoom(self) -> None:
        return None

    def _draw_previews(self, job: Any) -> None:
        self.drawn_job = job

    def _update_metadata_preview(self, job: Any) -> None:
        self.metadata_job = job

    def _refresh_status_indicators(self) -> None:
        self.refresh_count += 1


def test_bootstrap_on_select_change_keeps_passed_idx(monkeypatch) -> None:
    captured: dict[str, Any] = {}

    def _fake_apply_file_list_selection(_refs: Any, **kwargs: Any) -> None:
        captured.update(kwargs)

    monkeypatch.setattr(ui_bootstrap, "apply_file_list_selection", _fake_apply_file_list_selection)

    app = _DummyApp()
    ui_bootstrap.bootstrap_on_select_change(app, idx=1, force=True)

    assert app.current_index == 1
    assert app.drawn_job.path.name == "second.jpg"
    assert captured["current_job_index"] == 1


def test_bootstrap_on_select_change_uses_complete_color_fallback(monkeypatch) -> None:
    captured: dict[str, Any] = {}

    def _fake_apply_file_list_selection(_refs: Any, **kwargs: Any) -> None:
        captured.update(kwargs)

    monkeypatch.setattr(ui_bootstrap, "apply_file_list_selection", _fake_apply_file_list_selection)

    app = _DummyApp()
    ui_bootstrap.bootstrap_on_select_change(app, idx=1, force=True)

    colors = captured["colors"]
    assert "primary" in colors
    assert "bg_tertiary" in colors
    assert "border_light" in colors
    assert "text_primary" in colors
