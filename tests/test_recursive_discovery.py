from pathlib import Path

from karuku_resizer.gui_app import ResizeApp


def test_discover_recursive_image_paths_filters_and_recurses(tmp_path: Path) -> None:
    (tmp_path / "a").mkdir()
    (tmp_path / "a" / "b").mkdir()
    (tmp_path / "root.JPG").write_bytes(b"x")
    (tmp_path / "a" / "img.jpeg").write_bytes(b"x")
    (tmp_path / "a" / "b" / "img.png").write_bytes(b"x")
    (tmp_path / "a" / "b" / "skip.webp").write_bytes(b"x")
    (tmp_path / "a" / "b" / "skip.txt").write_bytes(b"x")

    found = ResizeApp._discover_recursive_image_paths(tmp_path)
    rel_paths = {p.relative_to(tmp_path).as_posix() for p in found}

    assert rel_paths == {"root.JPG", "a/img.jpeg", "a/b/img.png"}
    assert all(p.suffix.lower() in {".jpg", ".jpeg", ".png"} for p in found)


def test_discover_recursive_image_paths_returns_sorted_paths(tmp_path: Path) -> None:
    (tmp_path / "z.jpeg").write_bytes(b"x")
    (tmp_path / "a.jpg").write_bytes(b"x")
    (tmp_path / "m.png").write_bytes(b"x")

    found = ResizeApp._discover_recursive_image_paths(tmp_path)
    normalized = [str(p).lower() for p in found]

    assert normalized == sorted(normalized)


def test_normalized_pro_input_mode() -> None:
    assert ResizeApp._normalized_pro_input_mode("recursive") == "recursive"
    assert ResizeApp._normalized_pro_input_mode("files") == "files"
    assert ResizeApp._normalized_pro_input_mode("FILES") == "files"
    assert ResizeApp._normalized_pro_input_mode("unknown") == "recursive"
