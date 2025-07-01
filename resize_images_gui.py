"""Validated simple image resizer GUI.

This version streamlines the UI so the user only chooses **how to specify size**
(ratio%, width, height, or explicit both).  All algorithm/format decisions are
handled automatically for best quality.

Usage:
    uv run python resize_images_gui.py
"""
from __future__ import annotations

import io
import tkinter as tk
from dataclasses import dataclass
from pathlib import Path
from tkinter import filedialog, messagebox, ttk
from typing import List, Optional, Tuple

from PIL import Image, ImageTk
import tkinter.font as tkfont

# Pillow ≥10 moves resampling constants to Image.Resampling
try:
    from PIL.Image import Resampling
except ImportError:  # Pillow<10 fallback
    class _Resampling:  # type: ignore
        LANCZOS = Image.LANCZOS  # type: ignore

    Resampling = _Resampling()  # type: ignore

DEFAULT_PREVIEW = 480

# -------------------- UI color constants --------------------
UI_COLORS = {
    "primary": "#0078d4",
    "success": "#2e7d32",
    "danger": "#d32f2f",
    "active": "#dbeafe",  # light blue for current task
    "inactive": "white",
    "text_inactive": "#999999",
}
ZOOM_STEP = 1.1
MIN_ZOOM = 0.2
MAX_ZOOM = 10.0


@dataclass
class ImageJob:
    path: Path
    image: Image.Image
    resized: Optional[Image.Image] = None  # cache of last processed result


class ResizeApp(tk.Tk):
