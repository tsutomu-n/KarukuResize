from __future__ import annotations

import sys
from pathlib import Path

from karuku_resizer.gui_app import ResizeApp


def test_resolve_icon_paths_uses_repo_assets_in_dev_mode() -> None:
    ico_path, _png_path = ResizeApp._resolve_icon_paths()
    assert ico_path is not None
    assert ico_path.name == "app.ico"
    assert ico_path.parent.name == "assets"


def test_runtime_base_dir_uses_meipass_when_frozen(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(sys, "frozen", True, raising=False)
    monkeypatch.setattr(sys, "_MEIPASS", str(tmp_path), raising=False)
    assert ResizeApp._runtime_base_dir() == tmp_path
