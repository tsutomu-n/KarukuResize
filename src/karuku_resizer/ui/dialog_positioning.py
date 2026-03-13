"""Helpers for positioning transient dialogs relative to the main app window."""

from __future__ import annotations

import logging
from typing import Any


def center_window_on_parent(
    parent: Any,
    window: Any,
    *,
    width: int | None = None,
    height: int | None = None,
) -> None:
    """Place a child window near the visual center of its parent."""
    try:
        parent.update_idletasks()
        window.update_idletasks()
        resolved_width = max(int(width if width is not None else window.winfo_width()), 1)
        resolved_height = max(int(height if height is not None else window.winfo_height()), 1)
        parent_width = max(parent.winfo_width(), 1)
        parent_height = max(parent.winfo_height(), 1)
        parent_x = parent.winfo_rootx()
        parent_y = parent.winfo_rooty()
        screen_width = max(window.winfo_screenwidth(), 1)
        screen_height = max(window.winfo_screenheight(), 1)
        x = parent_x + (parent_width - resolved_width) // 2
        y = parent_y + (parent_height - resolved_height) // 2
        x = max(min(x, screen_width - resolved_width), 0)
        y = max(min(y, screen_height - resolved_height), 0)
        window.geometry(f"{resolved_width}x{resolved_height}+{x}+{y}")
    except Exception:
        logging.exception("Failed to center child window on parent")

