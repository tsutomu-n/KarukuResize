from __future__ import annotations

from karuku_resizer.ui.input_sources import setup_drag_and_drop


class _DummyTkDnD:
    @staticmethod
    def _require(_app) -> None:
        raise AssertionError("_require should not be called when root has no drop_target_register")


class _DummyApp:
    pass


def test_setup_drag_and_drop_skips_when_root_lacks_drop_target_register() -> None:
    app = _DummyApp()

    setup_drag_and_drop(
        app,
        tkdnd_available=True,
        tkdnd_cls=_DummyTkDnD,
        dnd_files="DND_Files",
    )

    assert app._drag_drop_enabled is False
