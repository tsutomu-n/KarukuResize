"""Metadata panel UI builder for the main GUI."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Mapping, Optional, Protocol, Sequence, Tuple

import customtkinter


@dataclass(frozen=True)
class MetadataPanelState:
    font_default: Any
    font_small: Any
    colors: Mapping[str, Any]
    style_card_frame: "StyleCardFrame"
    style_secondary_button: Callable[[Any], None]


@dataclass(frozen=True)
class MetadataPanelCallbacks:
    on_toggle_expanded: Callable[[], None]


class StyleCardFrame(Protocol):
    def __call__(self, frame: Any, *, corner_radius: int = ...) -> None: ...


@dataclass
class MetadataPanelRefs:
    metadata_frame: customtkinter.CTkFrame
    metadata_header_frame: customtkinter.CTkFrame
    metadata_title_label: customtkinter.CTkLabel
    metadata_toggle_button: customtkinter.CTkButton
    metadata_status_var: customtkinter.StringVar
    metadata_status_label: customtkinter.CTkLabel
    metadata_textbox: customtkinter.CTkTextbox


def build_metadata_panel(parent: Any, state: MetadataPanelState, callbacks: MetadataPanelCallbacks) -> MetadataPanelRefs:
    metadata_frame = customtkinter.CTkFrame(parent, corner_radius=12)
    state.style_card_frame(metadata_frame, corner_radius=12)

    metadata_header_frame = customtkinter.CTkFrame(metadata_frame, fg_color="transparent")
    metadata_header_frame.pack(side="top", fill="x", padx=8, pady=(8, 4))

    metadata_title_label = customtkinter.CTkLabel(
        metadata_header_frame,
        text="メタデータ（プロ）",
        font=state.font_default,
        text_color=state.colors["text_secondary"],
    )
    metadata_title_label.pack(side="left")

    metadata_toggle_button = customtkinter.CTkButton(
        metadata_header_frame,
        text="表示",
        width=80,
        command=callbacks.on_toggle_expanded,
        font=state.font_small,
    )
    state.style_secondary_button(metadata_toggle_button)
    metadata_toggle_button.pack(side="right")

    metadata_status_var = customtkinter.StringVar(value="画像を選択するとメタデータを表示できます")
    metadata_status_label = customtkinter.CTkLabel(
        metadata_frame,
        textvariable=metadata_status_var,
        anchor="w",
        justify="left",
        font=state.font_small,
        text_color=state.colors["text_tertiary"],
    )
    metadata_status_label.pack(side="top", fill="x", padx=10, pady=(0, 4))

    metadata_textbox = customtkinter.CTkTextbox(
        metadata_frame,
        height=120,
        corner_radius=8,
        border_width=1,
        border_color=state.colors["border_light"],
        fg_color=state.colors["input_bg"],
        text_color=state.colors["text_primary"],
        font=state.font_small,
        wrap="word",
    )
    metadata_textbox.pack_forget()

    return MetadataPanelRefs(
        metadata_frame=metadata_frame,
        metadata_header_frame=metadata_header_frame,
        metadata_title_label=metadata_title_label,
        metadata_toggle_button=metadata_toggle_button,
        metadata_status_var=metadata_status_var,
        metadata_status_label=metadata_status_label,
        metadata_textbox=metadata_textbox,
    )


def apply_metadata_mode(refs: MetadataPanelRefs, *, is_pro_mode: bool) -> None:
    if is_pro_mode:
        if refs.metadata_frame.winfo_manager() != "grid":
            refs.metadata_frame.grid(row=2, column=0, sticky="ew", pady=(6, 0))
        return

    if refs.metadata_frame.winfo_manager():
        refs.metadata_frame.grid_remove()


def apply_metadata_expanded(refs: MetadataPanelRefs, *, expanded: bool) -> None:
    """Show or hide metadata text area."""
    if expanded:
        if refs.metadata_textbox.winfo_manager() != "pack":
            refs.metadata_textbox.pack(
                side="top",
                fill="x",
                padx=10,
                pady=(0, 10),
            )
        refs.metadata_toggle_button.configure(text="隠す")
        return

    if refs.metadata_textbox.winfo_manager():
        refs.metadata_textbox.pack_forget()
    refs.metadata_toggle_button.configure(text="表示")


def apply_metadata_text(refs: MetadataPanelRefs, text: str) -> None:
    """Set metadata textbox content with locked editing disabled."""
    refs.metadata_textbox.configure(state="normal")
    refs.metadata_textbox.delete("1.0", "end")
    refs.metadata_textbox.insert("1.0", text)
    refs.metadata_textbox.configure(state="disabled")


def apply_metadata_status(refs: MetadataPanelRefs, text: str) -> None:
    """Set metadata status label."""
    refs.metadata_status_var.set(text)


def apply_metadata_preview(
    refs: MetadataPanelRefs,
    job: Optional[Any],
    *,
    extract_metadata_text: Callable[[Any], str],
) -> None:
    """Update metadata widget content from a selected image."""
    if job is None:
        apply_metadata_status(refs, "画像を選択するとメタデータを表示できます")
        apply_metadata_text(refs, "（画像未選択）")
        return
    metadata_text = extract_metadata_text(job)
    if getattr(job, "metadata_error", None):
        apply_metadata_status(refs, f"メタデータ: 取得失敗 ({job.path.name})")
    else:
        apply_metadata_status(refs, f"メタデータ: {job.path.name}")
    apply_metadata_text(refs, metadata_text)
