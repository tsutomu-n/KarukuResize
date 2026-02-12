from karuku_resizer.gui_app import DEFAULT_WINDOW_GEOMETRY, ResizeApp


def test_normalize_window_geometry_keeps_valid_value() -> None:
    assert ResizeApp._normalize_window_geometry("1280x800+10+20") == "1280x800+10+20"


def test_normalize_window_geometry_clamps_min_width() -> None:
    assert ResizeApp._normalize_window_geometry("960x700+40+50") == "1200x700+40+50"


def test_normalize_window_geometry_falls_back_on_invalid_value() -> None:
    assert ResizeApp._normalize_window_geometry("invalid") == DEFAULT_WINDOW_GEOMETRY
