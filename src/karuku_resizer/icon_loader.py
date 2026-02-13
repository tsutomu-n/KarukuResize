"""Lucide PNGアイコンをCTkImageとして読み込むユーティリティ。

assets/icons/{dark,light}/ に配置されたPNGファイルを読み込み、
CustomTkinterのダーク/ライトモード自動切替に対応したCTkImageを返す。
"""
from __future__ import annotations

import logging
import sys
from functools import lru_cache
from pathlib import Path
from typing import Optional

import customtkinter
from PIL import Image

_ICONS_DIR = Path(__file__).resolve().parent.parent.parent / "assets" / "icons"

_logger = logging.getLogger(__name__)


def _find_icons_dir() -> Path:
    """アイコンディレクトリを探索する。パッケージ内またはプロジェクトルートから。"""
    candidates: list[Path] = []
    if getattr(sys, "frozen", False):
        meipass = getattr(sys, "_MEIPASS", None)
        if meipass:
            candidates.append(Path(str(meipass)) / "assets" / "icons")
    candidates.extend([
        _ICONS_DIR,
        Path(__file__).resolve().parent / "assets" / "icons",
        Path.cwd() / "assets" / "icons",
    ])
    for candidate in candidates:
        if candidate.is_dir():
            return candidate
    return _ICONS_DIR


@lru_cache(maxsize=64)
def load_icon(name: str, size: int = 16) -> Optional[customtkinter.CTkImage]:
    """Lucideアイコンを読み込んでCTkImageを返す。

    Args:
        name: アイコン名（例: "folder-open", "save", "settings"）
        size: アイコンサイズ（16, 20, 24, 32）

    Returns:
        CTkImage or None（ファイルが見つからない場合）
    """
    icons_dir = _find_icons_dir()
    dark_path = icons_dir / "dark" / f"{name}_{size}.png"
    light_path = icons_dir / "light" / f"{name}_{size}.png"

    if not dark_path.exists() or not light_path.exists():
        _logger.warning("Icon not found: %s (size=%d)", name, size)
        return None

    try:
        dark_img = Image.open(dark_path)
        light_img = Image.open(light_path)
        return customtkinter.CTkImage(
            light_image=light_img,
            dark_image=dark_img,
            size=(size, size),
        )
    except Exception:
        _logger.exception("Failed to load icon: %s (size=%d)", name, size)
        return None
