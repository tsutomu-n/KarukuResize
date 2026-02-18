"""Preview panel UI builders for the main GUI."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Mapping, Protocol

import customtkinter


@dataclass(frozen=True)
class PreviewPanelState:
    font_default: Any
    colors: Mapping[str, Any]
    style_card_frame: "StyleCardFrame"
    canvas_background_color: Callable[[], str]


@dataclass(frozen=True)
class PreviewPanelCallbacks:
    on_zoom_original: Callable[[Any], None]
    on_zoom_resized: Callable[[Any], None]
    on_drag_original_press: Callable[[Any], None]
    on_drag_original_move: Callable[[Any], None]
    on_drag_resized_press: Callable[[Any], None]
    on_drag_resized_move: Callable[[Any], None]


class StyleCardFrame(Protocol):
    def __call__(self, frame: Any, *, corner_radius: int = ...) -> None: ...


@dataclass
class PreviewPanelRefs:
    preview_pane: customtkinter.CTkFrame
    frame_original: customtkinter.CTkFrame
    canvas_org: customtkinter.CTkCanvas
    info_orig_var: customtkinter.StringVar
    frame_resized: customtkinter.CTkFrame
    canvas_resz: customtkinter.CTkCanvas
    info_resized_var: customtkinter.StringVar
    resized_title_label: customtkinter.CTkLabel


def build_preview_panel(
    parent: Any,
    state: PreviewPanelState,
    callbacks: PreviewPanelCallbacks,
) -> PreviewPanelRefs:
    preview_pane = customtkinter.CTkFrame(parent, fg_color="transparent")
    preview_pane.pack(side="right", fill="both", expand=True, padx=(5, 0))
    preview_pane.grid_rowconfigure(0, weight=1)
    preview_pane.grid_columnconfigure(0, weight=1)
    preview_pane.grid_columnconfigure(1, weight=1)

    frame_original = customtkinter.CTkFrame(preview_pane, corner_radius=12)
    state.style_card_frame(frame_original, corner_radius=12)
    frame_original.grid(row=0, column=0, sticky="nswe", padx=(0, 3))
    frame_original.grid_rowconfigure(1, weight=1)
    frame_original.grid_columnconfigure(0, weight=1)
    customtkinter.CTkLabel(
        frame_original,
        text="オリジナル",
        font=state.font_default,
        text_color=state.colors["text_secondary"],
    ).grid(row=0, column=0, sticky="w", padx=10, pady=(8, 0))
    canvas_org = customtkinter.CTkCanvas(
        frame_original,
        bg=state.canvas_background_color(),
        highlightthickness=0,
    )
    canvas_org.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)
    info_orig_var = customtkinter.StringVar(value="--- x ---  ---")
    customtkinter.CTkLabel(
        frame_original,
        textvariable=info_orig_var,
        justify="left",
        font=state.font_default,
        text_color=state.colors["text_tertiary"],
    ).grid(row=2, column=0, sticky="ew", padx=10, pady=(0, 8))

    frame_resized = customtkinter.CTkFrame(preview_pane, corner_radius=12)
    state.style_card_frame(frame_resized, corner_radius=12)
    frame_resized.grid(row=0, column=1, sticky="nswe", padx=(3, 0))
    frame_resized.grid_rowconfigure(1, weight=1)
    frame_resized.grid_columnconfigure(0, weight=1)
    resized_title_label = customtkinter.CTkLabel(
        frame_resized,
        text="リサイズ後",
        font=state.font_default,
        text_color=state.colors["text_secondary"],
    )
    resized_title_label.grid(row=0, column=0, sticky="w", padx=10, pady=(8, 0))
    canvas_resz = customtkinter.CTkCanvas(
        frame_resized,
        bg=state.canvas_background_color(),
        highlightthickness=0,
    )
    canvas_resz.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)
    info_resized_var = customtkinter.StringVar(value="--- x ---  ---  (---)")
    customtkinter.CTkLabel(
        frame_resized,
        textvariable=info_resized_var,
        justify="left",
        font=state.font_default,
        text_color=state.colors["text_tertiary"],
    ).grid(row=2, column=0, sticky="ew", padx=10, pady=(0, 8))

    canvas_org.bind("<MouseWheel>", callbacks.on_zoom_original)
    canvas_resz.bind("<MouseWheel>", callbacks.on_zoom_resized)
    canvas_org.bind("<ButtonPress-1>", callbacks.on_drag_original_press)
    canvas_org.bind("<B1-Motion>", callbacks.on_drag_original_move)
    canvas_resz.bind("<ButtonPress-1>", callbacks.on_drag_resized_press)
    canvas_resz.bind("<B1-Motion>", callbacks.on_drag_resized_move)

    return PreviewPanelRefs(
        preview_pane=preview_pane,
        frame_original=frame_original,
        canvas_org=canvas_org,
        info_orig_var=info_orig_var,
        frame_resized=frame_resized,
        canvas_resz=canvas_resz,
        info_resized_var=info_resized_var,
        resized_title_label=resized_title_label,
    )
