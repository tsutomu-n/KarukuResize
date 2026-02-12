"""Tooltip utilities for CustomTkinter/Tkinter widgets."""

from __future__ import annotations

import tkinter as tk
from typing import Callable, Dict, Optional


class TooltipManager:
    """Simple delayed tooltip manager shared by multiple widgets."""

    def __init__(
        self,
        root: tk.Misc,
        *,
        enabled_provider: Callable[[], bool],
        delay_ms: int = 400,
        wraplength: int = 320,
    ) -> None:
        self.root = root
        self.enabled_provider = enabled_provider
        self.delay_ms = max(0, int(delay_ms))
        self.wraplength = max(120, int(wraplength))

        self._texts: Dict[tk.Misc, str] = {}
        self._after_id: Optional[str] = None
        self._pending_widget: Optional[tk.Misc] = None
        self._pending_via_focus = False
        self._window: Optional[tk.Toplevel] = None
        self._label: Optional[tk.Label] = None
        self._visible_for: Optional[tk.Misc] = None

    def register(self, widget: tk.Misc, text: str) -> None:
        """Register tooltip text for a widget."""
        clean_text = str(text).strip()
        if not clean_text:
            return
        self._texts[widget] = clean_text

        widget.bind("<Enter>", lambda _e, w=widget: self._schedule_show(w, via_focus=False), add="+")
        widget.bind("<Leave>", lambda _e, w=widget: self._hide_if_for_widget(w), add="+")
        widget.bind("<FocusIn>", lambda _e, w=widget: self._schedule_show(w, via_focus=True), add="+")
        widget.bind("<FocusOut>", lambda _e, w=widget: self._hide_if_for_widget(w), add="+")
        widget.bind("<ButtonPress>", lambda _e: self.hide(), add="+")
        widget.bind("<Destroy>", lambda _e, w=widget: self._unregister_widget(w), add="+")

    def hide(self) -> None:
        """Hide tooltip immediately."""
        self._cancel_pending()
        if self._window is not None:
            self._window.withdraw()
        self._visible_for = None

    def _unregister_widget(self, widget: tk.Misc) -> None:
        self._texts.pop(widget, None)
        if self._pending_widget is widget:
            self._cancel_pending()
        if self._visible_for is widget:
            self.hide()

    def _schedule_show(self, widget: tk.Misc, *, via_focus: bool) -> None:
        if not self.enabled_provider():
            self.hide()
            return
        if widget not in self._texts:
            return
        self._cancel_pending()
        self._pending_widget = widget
        self._pending_via_focus = via_focus
        self._after_id = self.root.after(self.delay_ms, self._show_pending)

    def _cancel_pending(self) -> None:
        if self._after_id is not None:
            try:
                self.root.after_cancel(self._after_id)
            except Exception:
                pass
        self._after_id = None
        self._pending_widget = None
        self._pending_via_focus = False

    def _hide_if_for_widget(self, widget: tk.Misc) -> None:
        if self._pending_widget is widget:
            self._cancel_pending()
        if self._visible_for is widget:
            self.hide()

    def _show_pending(self) -> None:
        self._after_id = None
        widget = self._pending_widget
        via_focus = self._pending_via_focus
        self._pending_widget = None
        self._pending_via_focus = False
        if widget is None:
            return
        if not self.enabled_provider():
            self.hide()
            return
        if not widget.winfo_exists():
            return
        text = self._texts.get(widget, "")
        if not text:
            return

        window, label = self._ensure_window()
        label.configure(text=text)
        window.update_idletasks()

        if via_focus:
            x = widget.winfo_rootx() + widget.winfo_width() + 12
            y = widget.winfo_rooty() + 4
        else:
            x = self.root.winfo_pointerx() + 14
            y = self.root.winfo_pointery() + 18

        screen_w = self.root.winfo_screenwidth()
        screen_h = self.root.winfo_screenheight()
        tip_w = max(160, window.winfo_reqwidth())
        tip_h = max(40, window.winfo_reqheight())
        x = min(max(8, x), max(8, screen_w - tip_w - 8))
        y = min(max(8, y), max(8, screen_h - tip_h - 8))

        window.geometry(f"+{x}+{y}")
        window.deiconify()
        window.lift()
        self._visible_for = widget

    def _ensure_window(self) -> tuple[tk.Toplevel, tk.Label]:
        if self._window is not None and self._window.winfo_exists() and self._label is not None:
            return self._window, self._label

        window = tk.Toplevel(self.root)
        window.withdraw()
        window.overrideredirect(True)
        window.attributes("-topmost", True)
        window.configure(bg="#1F2A37")

        label = tk.Label(
            window,
            text="",
            justify="left",
            bg="#1F2A37",
            fg="#F4F7FB",
            bd=1,
            relief="solid",
            padx=8,
            pady=6,
            wraplength=self.wraplength,
        )
        label.pack(fill="both", expand=True)

        self._window = window
        self._label = label
        return window, label
