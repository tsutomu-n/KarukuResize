from __future__ import annotations

import json
from pathlib import Path

from karuku_resizer.resize_core import (
    _discover_cli_image_paths,
    _normalize_cli_extensions,
    _write_failures_file,
)


def test_normalize_cli_extensions() -> None:
    assert _normalize_cli_extensions("jpg, .png, JPEG") == [".jpeg", ".jpg", ".png"]


def test_discover_cli_image_paths_recursive(tmp_path: Path) -> None:
    (tmp_path / "a").mkdir()
    (tmp_path / "a" / "img.jpg").write_bytes(b"x")
    (tmp_path / "a" / "skip.webp").write_bytes(b"x")
    (tmp_path / "root.png").write_bytes(b"x")

    found = _discover_cli_image_paths(
        tmp_path,
        recursive=True,
        extensions=[".jpg", ".png"],
    )
    rel = {path.relative_to(tmp_path).as_posix() for path in found}
    assert rel == {"a/img.jpg", "root.png"}


def test_discover_cli_image_paths_non_recursive(tmp_path: Path) -> None:
    (tmp_path / "a").mkdir()
    (tmp_path / "a" / "img.jpg").write_bytes(b"x")
    (tmp_path / "root.jpg").write_bytes(b"x")

    found = _discover_cli_image_paths(
        tmp_path,
        recursive=False,
        extensions=[".jpg"],
    )
    rel = [path.relative_to(tmp_path).as_posix() for path in found]
    assert rel == ["root.jpg"]


def test_write_failures_file(tmp_path: Path) -> None:
    out = tmp_path / "logs" / "failures.json"
    _write_failures_file(
        out,
        source=tmp_path / "input",
        dest=tmp_path / "output",
        failed_files=[{"file": "a.jpg", "error": "broken"}],
    )

    payload = json.loads(out.read_text(encoding="utf-8"))
    assert payload["failed_count"] == 1
    assert payload["failed_files"][0]["file"] == "a.jpg"
