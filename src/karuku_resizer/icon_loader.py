"""Icon loader for CustomTkinter buttons.

- assets/icons/light/<name>_<size>.png
- assets/icons/dark/<name>_<size>.png

PyInstaller(onefile)実行時は ``sys._MEIPASS`` を優先して探索する。
"""

from __future__ import annotations

import logging
import sys
from functools import lru_cache
from pathlib import Path
from typing import Optional, Tuple

import customtkinter
from PIL import Image


@lru_cache(maxsize=128)
def _resolve_icon_paths(name: str, size: int) -> Tuple[Optional[Path], Optional[Path]]:
    filename = f"{name}_{size}.png"

    candidates: list[Path] = []
    meipass = getattr(sys, "_MEIPASS", None)
    if meipass:
        candidates.append(Path(str(meipass)))

    # src/karuku_resizer/icon_loader.py -> project root
    candidates.append(Path(__file__).resolve().parents[2])

    for base in candidates:
        light = base / "assets" / "icons" / "light" / filename
        dark = base / "assets" / "icons" / "dark" / filename
        if light.exists() and dark.exists():
            return light, dark

    return None, None


@lru_cache(maxsize=128)
def load_icon(name: str, size: int = 16) -> Optional[customtkinter.CTkImage]:
    light_path, dark_path = _resolve_icon_paths(name, size)
    if light_path is None or dark_path is None:
        logging.warning("Icon not found: %s (size=%s)", name, size)
        return None

    try:
        light_img = Image.open(light_path)
        dark_img = Image.open(dark_path)
        return customtkinter.CTkImage(light_image=light_img, dark_image=dark_img, size=(size, size))
    except Exception:
        logging.exception("Failed to load icon: %s (size=%s)", name, size)
        return None
