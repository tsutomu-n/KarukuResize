from karuku_resizer.ui import main_layout


class DummyApp:
    def __init__(self) -> None:
        self.bind_calls = []
        self.row_weights = []
        self.col_weights = []

    def grid_rowconfigure(self, index, weight=0):
        self.row_weights.append((index, weight))

    def grid_columnconfigure(self, index, weight=0):
        self.col_weights.append((index, weight))

    def bind(self, event, callback):
        self.bind_calls.append((event, callback))

    def _on_root_resize(self, _event):
        return None

    def __getattr__(self, name):
        if name == "_file_filter_label_to_id":
            raise AssertionError("setup_main_layout must not access app._file_filter_label_to_id")
        raise AttributeError(name)


def test_setup_main_layout_uses_explicit_file_filter_labels(monkeypatch):
    app = DummyApp()
    captured = {}

    monkeypatch.setattr(main_layout, "setup_progress_bar_and_cancel", lambda app, *, colors: None)
    monkeypatch.setattr(main_layout, "setup_status_bar", lambda app, *, colors: None)

    def _fake_setup_left_panel(app, *, colors, file_filter_labels):
        captured["labels"] = list(file_filter_labels)

    monkeypatch.setattr(main_layout, "setup_left_panel", _fake_setup_left_panel)
    monkeypatch.setattr(main_layout, "setup_right_panel", lambda app, *, colors: None)

    main_layout.setup_main_layout(
        app,
        colors={"bg_secondary": ("#fff", "#000")},
        default_preview=480,
        file_filter_labels=["全件", "失敗", "未処理"],
    )

    assert captured["labels"] == ["全件", "失敗", "未処理"]
    assert app.row_weights == [(1, 1)]
    assert app.col_weights == [(1, 1)]
    assert app.bind_calls and app.bind_calls[0][0] == "<Configure>"
    assert app._last_canvas_size == (480, 480)
