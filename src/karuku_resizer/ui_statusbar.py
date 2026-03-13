"""Statusbar / progressbar UI builders for the main GUI."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Mapping

import customtkinter


@dataclass(frozen=True)
class StatusBarState:
    font_default: Any
    font_small: Any
    colors: Mapping[str, Any]
    style_secondary_button: Callable[[Any], None]


@dataclass(frozen=True)
class StatusBarCallbacks:
    on_cancel: Callable[[], None]


@dataclass
class StatusBarRefs:
    progress_bar: customtkinter.CTkProgressBar
    cancel_button: customtkinter.CTkButton
    operation_stage_var: customtkinter.StringVar
    operation_stage_label: customtkinter.CTkLabel
    action_hint_var: customtkinter.StringVar
    action_hint_label: customtkinter.CTkLabel
    session_summary_var: customtkinter.StringVar
    session_summary_label: customtkinter.CTkLabel
    status_var: customtkinter.StringVar
    status_label: customtkinter.CTkLabel


def build_statusbar(parent: Any, state: StatusBarState, callbacks: StatusBarCallbacks) -> StatusBarRefs:
    status_row = customtkinter.CTkFrame(parent, fg_color="transparent")
    status_row.pack(side="bottom", fill="x", padx=12, pady=(0, 8))
    status_row.grid_columnconfigure(0, weight=3)
    status_row.grid_columnconfigure(1, weight=4)
    status_row.grid_columnconfigure(2, weight=2)

    progress_bar = customtkinter.CTkProgressBar(
        status_row,
        width=260,
        height=20,
        fg_color=state.colors["bg_tertiary"],
        progress_color=state.colors["primary"],
    )
    progress_bar.set(0)

    cancel_button = customtkinter.CTkButton(
        status_row,
        text="キャンセル",
        width=100,
        command=callbacks.on_cancel,
    )
    state.style_secondary_button(cancel_button)

    operation_stage_var = customtkinter.StringVar(value="")
    operation_stage_label = customtkinter.CTkLabel(
        status_row,
        textvariable=operation_stage_var,
        anchor="w",
        font=state.font_small,
        text_color=state.colors["warning"],
        fg_color=state.colors["bg_secondary"],
        corner_radius=10,
        padx=10,
    )
    operation_stage_label.grid(row=0, column=1, sticky="ew", padx=(12, 12), pady=(0, 4))
    operation_stage_label.grid_remove()

    progress_controls_frame = customtkinter.CTkFrame(status_row, fg_color="transparent")
    progress_controls_frame.grid(row=1, column=1, sticky="ew", padx=(12, 12))
    progress_controls_frame.grid_columnconfigure(0, weight=1)

    progress_bar.grid(row=0, column=0, sticky="ew")
    progress_bar.grid_remove()
    cancel_button.grid(row=0, column=1, padx=(8, 0))
    cancel_button.grid_remove()

    action_hint_var = customtkinter.StringVar(value="")
    action_hint_label = customtkinter.CTkLabel(
        parent,
        textvariable=action_hint_var,
        anchor="w",
        font=state.font_small,
        text_color=state.colors["warning"],
        fg_color=state.colors["bg_secondary"],
        corner_radius=10,
        padx=10,
    )
    action_hint_label.pack_forget()

    session_summary_var = customtkinter.StringVar(value="")
    session_summary_label = customtkinter.CTkLabel(
        status_row,
        textvariable=session_summary_var,
        anchor="e",
        font=state.font_small,
        text_color=state.colors["text_tertiary"],
        fg_color=state.colors["bg_secondary"],
        corner_radius=10,
        padx=10,
    )
    session_summary_label.grid(row=0, column=2, rowspan=2, sticky="e")

    status_var = customtkinter.StringVar(value="準備完了")
    status_label = customtkinter.CTkLabel(
        status_row,
        textvariable=status_var,
        anchor="w",
        font=state.font_default,
        text_color=state.colors["text_secondary"],
        fg_color=state.colors["bg_secondary"],
        corner_radius=10,
        padx=10,
    )
    status_label.grid(row=0, column=0, rowspan=2, sticky="ew")

    return StatusBarRefs(
        progress_bar=progress_bar,
        cancel_button=cancel_button,
        operation_stage_var=operation_stage_var,
        operation_stage_label=operation_stage_label,
        action_hint_var=action_hint_var,
        action_hint_label=action_hint_label,
        session_summary_var=session_summary_var,
        session_summary_label=session_summary_label,
        status_var=status_var,
        status_label=status_label,
    )
