from __future__ import annotations

from typing import Any, Callable

from karuku_resizer.ui.settings_header import register_setting_watchers


class _TraceVar:
    def __init__(self) -> None:
        self.calls: list[tuple[str, Callable[..., None]]] = []

    def trace_add(self, mode: str, callback: Callable[..., None]) -> None:
        self.calls.append((mode, callback))


class _DummyApp:
    def __init__(self) -> None:
        self.output_format_var = _TraceVar()
        self.quality_var = _TraceVar()
        self.webp_method_var = _TraceVar()
        self.webp_lossless_var = _TraceVar()
        self.avif_speed_var = _TraceVar()
        self.exif_mode_var = _TraceVar()
        self.remove_gps_var = _TraceVar()
        self.dry_run_var = _TraceVar()
        self.summary_update_count = 0

    def _update_settings_summary(self) -> None:
        self.summary_update_count += 1


def _watched_vars(app: _DummyApp) -> tuple[_TraceVar, ...]:
    return (
        app.output_format_var,
        app.quality_var,
        app.webp_method_var,
        app.webp_lossless_var,
        app.avif_speed_var,
        app.exif_mode_var,
        app.remove_gps_var,
        app.dry_run_var,
    )


def test_register_setting_watchers_uses_injected_callback() -> None:
    app = _DummyApp()
    called: list[tuple[Any, ...]] = []

    def on_change(*args: Any) -> None:
        called.append(args)

    register_setting_watchers(app, on_change)

    for var in _watched_vars(app):
        assert var.calls == [("write", on_change)]

    callback = app.output_format_var.calls[0][1]
    callback("name", "index", "write")
    assert len(called) == 1


def test_register_setting_watchers_default_callback_updates_summary() -> None:
    app = _DummyApp()

    register_setting_watchers(app)

    callback = app.output_format_var.calls[0][1]
    callback("name", "index", "write")
    assert app.summary_update_count == 1
