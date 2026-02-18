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


class _DummyStats:
    def __init__(self) -> None:
        self.processed_count = 0
        self.failed_count = 0
        self.dry_run_count = 0
        self.exif_applied_count = 0
        self.exif_fallback_count = 0
        self.gps_removed_count = 0
        self.failed_details: list[str] = []
        self.failed_paths: list[Any] = []


class _DummyProgress:
    def __init__(self) -> None:
        self.values: list[float] = []

    def set(self, value: float) -> None:
        self.values.append(value)


class _BatchSaveApp(_DummyApp):
    def __init__(self, jobs: list[Any]) -> None:
        super().__init__()
        self.jobs = jobs
        self.progress_bar = _DummyProgress()
        self._cancel_batch = False
        self.status_var = _StatusVar()
        self._run_summary_payload = {
            "batch_runs": [],
            "totals": {
                "batch_run_count": 0,
                "processed_count": 0,
                "failed_count": 0,
                "dry_run_count": 0,
                "cancelled_count": 0,
            },
        }

    def _create_batch_stats(self) -> _DummyStats:
        return _DummyStats()

    def _is_pro_mode(self) -> bool:
        return False

    def _end_operation_scope(self) -> None:
        return None

    def _populate_listbox(self) -> None:
        return None

    def _refresh_status_indicators(self) -> None:
        self.refresh_count += 1

    def _write_run_summary_safe(self) -> None:
        return None

    def update_idletasks(self) -> None:
        return None

    @property
    def _run_log_artifacts(self) -> Any:
        return None


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


def test_bootstrap_run_batch_save_returns_selected_target_count(monkeypatch) -> None:
    jobs = [SimpleNamespace(path=Path(f"file{i}.jpg"), image=None) for i in range(3)]
    app = _BatchSaveApp(jobs)

    def _dummy_prepare_batch_ui(_app: Any) -> None:
        _app.prepare_count = (_app.prepare_count if hasattr(_app, "prepare_count") else 0) + 1

    monkeypatch.setattr(ui_bootstrap, "bootstrap_prepare_batch_ui", _dummy_prepare_batch_ui)
    monkeypatch.setattr(
        ui_bootstrap,
        "bootstrap_process_single_batch_job",
        lambda *_args, **_kwargs: None,
    )

    target_jobs = jobs[:2]
    _, total_count = ui_bootstrap.bootstrap_run_batch_save(
        app,
        output_dir=Path("/tmp"),
        reference_target=(100, 100),
        reference_output_format="jpeg",
        batch_options=SimpleNamespace(dry_run=False),
        target_jobs=target_jobs,
    )

    assert total_count == 2
    assert app.progress_bar.values[-1] == 1.0


def test_bootstrap_record_batch_run_summary_uses_selected_count() -> None:
    app = _BatchSaveApp([SimpleNamespace(path=Path("a.jpg"))])
    stats = _DummyStats()
    stats.processed_count = 1
    stats.dry_run_count = 0
    stats.exif_applied_count = 0
    stats.exif_fallback_count = 0
    stats.gps_removed_count = 0

    app._cancel_batch = False
    ui_bootstrap.bootstrap_record_batch_run_summary(
        app,
        stats=stats,
        output_dir=Path("/tmp"),
        selected_count=2,
        reference_job=SimpleNamespace(path=Path("ref.jpg")),
        reference_target=(100, 100),
        reference_format_label="JPEG",
        batch_options=SimpleNamespace(dry_run=False),
    )

    assert app._run_summary_payload["batch_runs"][0]["totals"]["selected_count"] == 2
