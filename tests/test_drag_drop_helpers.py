from pathlib import Path

from karuku_resizer.gui_app import ResizeApp


def test_normalize_dropped_path_text_keeps_plain_path() -> None:
    value = "/tmp/example.jpg"
    assert ResizeApp._normalize_dropped_path_text(value) == value


def test_normalize_dropped_path_text_decodes_file_uri() -> None:
    uri = "file:///tmp/a%20b.jpg"
    assert ResizeApp._normalize_dropped_path_text(uri) == "/tmp/a b.jpg"


def test_normalize_dropped_path_text_supports_unc_file_uri() -> None:
    uri = "file://server/share/sample.png"
    assert ResizeApp._normalize_dropped_path_text(uri) == "//server/share/sample.png"


def test_dedupe_paths_is_case_insensitive() -> None:
    paths = [Path("/tmp/A.jpg"), Path("/tmp/a.jpg"), Path("/tmp/B.jpg")]
    deduped = ResizeApp._dedupe_paths(paths)
    assert deduped == [Path("/tmp/A.jpg"), Path("/tmp/B.jpg")]


def test_selectable_input_file_accepts_supported_extensions() -> None:
    assert ResizeApp._is_selectable_input_file(Path("a.jpg"))
    assert ResizeApp._is_selectable_input_file(Path("b.webp"))
    assert ResizeApp._is_selectable_input_file(Path("c.avif"))
    assert not ResizeApp._is_selectable_input_file(Path("d.gif"))
