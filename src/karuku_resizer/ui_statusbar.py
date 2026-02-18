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
    progress_bar = customtkinter.CTkProgressBar(
        parent,
        width=400,
        height=20,
        fg_color=state.colors["bg_tertiary"],
        progress_color=state.colors["primary"],
    )
    progress_bar.set(0)
    progress_bar.pack_forget()

    cancel_button = customtkinter.CTkButton(
        parent,
        text="キャンセル",
        width=100,
        command=callbacks.on_cancel,
    )
    state.style_secondary_button(cancel_button)
    cancel_button.pack_forget()

    operation_stage_var = customtkinter.StringVar(value="")
    operation_stage_label = customtkinter.CTkLabel(
        parent,
        textvariable=operation_stage_var,
        anchor="w",
        font=state.font_small,
        text_color=state.colors["warning"],
        fg_color=state.colors["bg_secondary"],
        corner_radius=10,
        padx=10,
    )
    operation_stage_label.pack_forget()

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
    action_hint_label.pack(side="bottom", fill="x", padx=12, pady=(0, 4))

    session_summary_var = customtkinter.StringVar(value="")
    session_summary_label = customtkinter.CTkLabel(
        parent,
        textvariable=session_summary_var,
        anchor="w",
        font=state.font_small,
        text_color=state.colors["text_tertiary"],
        fg_color=state.colors["bg_secondary"],
        corner_radius=10,
        padx=10,
    )
    session_summary_label.pack(side="bottom", fill="x", padx=12, pady=(0, 4))

    status_var = customtkinter.StringVar(value="準備完了")
    status_label = customtkinter.CTkLabel(
        parent,
        textvariable=status_var,
        anchor="w",
        font=state.font_default,
        text_color=state.colors["text_secondary"],
        fg_color=state.colors["bg_secondary"],
        corner_radius=10,
        padx=10,
    )
    status_label.pack(side="bottom", fill="x", padx=12, pady=(0, 8))

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
