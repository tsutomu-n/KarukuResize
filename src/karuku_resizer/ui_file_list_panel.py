"""File list panel UI builder for the main GUI."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, List, Mapping, Optional, Sequence, Tuple

import customtkinter


@dataclass(frozen=True)
class FileListState:
    scale_px: Callable[[int], int]
    font_small: Any
    colors: Mapping[str, Any]


@dataclass(frozen=True)
class FileListCallbacks:
    on_filter_changed: Callable[[str], None]
    on_clear_loaded: Callable[[], None]
    style_secondary_button: Callable[[Any], None]
    register_tooltip: Callable[[Any, str], None]


@dataclass
class FileListRefs:
    main_content: customtkinter.CTkFrame
    file_list_frame: customtkinter.CTkScrollableFrame
    file_filter_var: customtkinter.StringVar
    file_filter_segment: customtkinter.CTkSegmentedButton
    clear_loaded_button: customtkinter.CTkButton
    file_buttons: List[customtkinter.CTkButton]
    empty_state_label: customtkinter.CTkLabel
    font_small: Any


def _accent_soft_color(colors: Mapping[str, Any]) -> Any:
    return colors.get("accent_soft", colors.get("hover", colors.get("bg_tertiary")))


def _color_with_default(colors: Mapping[str, Any], key: str, default: Any) -> Any:
    value = colors.get(key)
    return default if value is None else value


def build_file_list_panel(
    parent: Any,
    state: FileListState,
    callbacks: FileListCallbacks,
    *,
    filter_values: List[str],
) -> FileListRefs:
    main_content = customtkinter.CTkFrame(parent, fg_color="transparent")
    main_content.pack(fill="both", expand=True, padx=12, pady=8)

    file_list_column = customtkinter.CTkFrame(main_content, fg_color="transparent")
    file_list_column.pack(side="left", fill="y", padx=(0, 6))

    file_list_frame = customtkinter.CTkScrollableFrame(
        file_list_column,
        label_text="ファイルリスト",
        label_font=state.font_small,
        width=250,
        fg_color=state.colors["bg_secondary"],
        border_width=1,
        border_color=state.colors["border_light"],
        label_fg_color=state.colors["bg_tertiary"],
        label_text_color=state.colors["text_secondary"],
        corner_radius=12,
    )
    file_list_frame.pack(side="top", fill="y", expand=True)

    file_filter_var = customtkinter.StringVar(value=filter_values[0] if filter_values else "全件")
    file_filter_segment = customtkinter.CTkSegmentedButton(
        file_list_frame,
        values=filter_values,
        variable=file_filter_var,
        command=callbacks.on_filter_changed,
        width=220,
        font=state.font_small,
        selected_color=state.colors["primary"],
        selected_hover_color=state.colors["hover"],
        unselected_color=state.colors["bg_tertiary"],
        unselected_hover_color=_accent_soft_color(state.colors),
        text_color=state.colors["text_primary"],
    )
    file_filter_segment.pack(fill="x", padx=8, pady=(8, 4))

    callbacks.register_tooltip(
        file_filter_segment,
        "一覧表示を全件・失敗・未処理で切り替えます。",
    )

    empty_state_label = customtkinter.CTkLabel(
        file_list_frame,
        text="",
        justify="left",
        anchor="w",
        font=state.font_small,
        text_color=state.colors["text_secondary"],
        wraplength=220,
    )
    empty_state_label.pack(fill="x", padx=8, pady=(8, 4))

    clear_loaded_button = customtkinter.CTkButton(
        file_list_column,
        text="読み込み一覧をクリア",
        width=220,
        command=callbacks.on_clear_loaded,
        font=state.font_small,
    )
    callbacks.style_secondary_button(clear_loaded_button)
    clear_loaded_button.pack(side="top", fill="x", padx=8, pady=(6, 0))

    return FileListRefs(
        main_content=main_content,
        file_list_frame=file_list_frame,
        file_filter_var=file_filter_var,
        file_filter_segment=file_filter_segment,
        clear_loaded_button=clear_loaded_button,
        file_buttons=[],
        empty_state_label=empty_state_label,
        font_small=state.font_small,
    )


def file_button_label(job: Any) -> str:
    """Build a human-readable list label for a job."""
    if getattr(job, "last_process_state", "") == "failed":
        return f"［失敗］ {getattr(job.path, 'name', str(job))}"
    if getattr(job, "last_process_state", "") == "success":
        return f"［完了］ {getattr(job.path, 'name', str(job))}"
    return getattr(job.path, "name", str(job))


def file_passes_filter(job: Any, filter_label: str, file_filter_label_to_id: Mapping[str, str]) -> bool:
    """Return whether a job should be visible under the current list filter."""
    filter_id = file_filter_label_to_id.get(filter_label, "all")
    if filter_id == "failed":
        return getattr(job, "last_process_state", "") == "failed"
    if filter_id == "unprocessed":
        return getattr(job, "last_process_state", "") == "unprocessed"
    return True


def build_file_button_entries(
    jobs: Sequence[Any],
    *,
    file_filter_label: str,
    file_filter_label_to_id: Mapping[str, str],
) -> List[Tuple[int, str]]:
    """Build visible job index/label pairs for list rendering."""
    job_entries: List[Tuple[int, str]] = []
    for index, job in enumerate(jobs):
        if not file_passes_filter(job, file_filter_label, file_filter_label_to_id):
            continue
        job_entries.append((index, file_button_label(job)))
    return job_entries


def sync_file_list_buttons(
    refs: FileListRefs,
    job_entries: Sequence[Tuple[int, str]],
    *,
    selected_job_index: Optional[int],
    on_select_job: Callable[[int], None],
    register_tooltip: Callable[[Any, str], None],
    tooltip_text: Callable[[int, str], str],
    colors: Mapping[str, Any],
    empty_state_text: str,
) -> Tuple[List[customtkinter.CTkButton], List[int]]:
    """Rebuild the list buttons and return button references and visible indices."""
    for button in refs.file_buttons:
        button.destroy()

    refs.file_buttons = []
    visible_job_indices: List[int] = []

    if not job_entries:
        refs.empty_state_label.configure(text=empty_state_text)
        if refs.empty_state_label.winfo_manager() != "pack":
            refs.empty_state_label.pack(fill="x", padx=8, pady=(8, 4))
    else:
        if refs.empty_state_label.winfo_manager():
            refs.empty_state_label.pack_forget()

    for job_index, label in job_entries:
        accent_soft = _accent_soft_color(colors)
        button = customtkinter.CTkButton(
            refs.file_list_frame,
            text=label,
            command=lambda i=job_index: on_select_job(i),
            fg_color=accent_soft if job_index == selected_job_index else colors["bg_tertiary"],
            hover_color=accent_soft,
            text_color=colors["text_primary"],
            border_width=1,
            border_color=colors["primary"] if job_index == selected_job_index else colors["border_light"],
            corner_radius=8,
            font=refs.font_small,
        )
        button.pack(fill="x", padx=8, pady=4)
        register_tooltip(button, tooltip_text(job_index, label))
        refs.file_buttons.append(button)
        visible_job_indices.append(job_index)

    return refs.file_buttons, visible_job_indices


def refresh_file_list_panel(
    refs: FileListRefs,
    jobs: Sequence[Any],
    *,
    file_filter_label: str,
    file_filter_label_to_id: Mapping[str, str],
    selected_job_index: Optional[int],
    on_select_job: Callable[[int], None],
    register_tooltip: Callable[[Any, str], None],
    tooltip_text: Callable[[int, str], str],
    colors: Mapping[str, Any],
    empty_state_text: str,
) -> List[int]:
    """Rebuild file list buttons from current job state and return visible job indices."""
    job_entries = build_file_button_entries(
        jobs,
        file_filter_label=file_filter_label,
        file_filter_label_to_id=file_filter_label_to_id,
    )
    _, visible_job_indices = sync_file_list_buttons(
        refs,
        job_entries,
        selected_job_index=selected_job_index,
        on_select_job=on_select_job,
        register_tooltip=register_tooltip,
        tooltip_text=tooltip_text,
        colors=colors,
        empty_state_text=empty_state_text,
    )
    return visible_job_indices


def apply_empty_state_hint(
    refs: FileListRefs,
    has_jobs: bool,
    *,
    is_pro_mode: bool,
    processing_hint: str,
    build_empty_state_text_fn,
) -> None:
    """Update file-list empty hint visibility and message."""
    if has_jobs:
        if refs.empty_state_label.winfo_manager():
            refs.empty_state_label.pack_forget()
        return
    refs.empty_state_label.configure(
        text=build_empty_state_text_fn(
            is_pro_mode=is_pro_mode,
            processing_hint=processing_hint,
        )
    )
    if refs.empty_state_label.winfo_manager() != "pack":
        refs.empty_state_label.pack(fill="x", padx=8, pady=(8, 4))


def list_position_for_job(visible_job_indices: Sequence[int], job_index: Optional[int]) -> Optional[int]:
    if job_index is None:
        return None
    try:
        return visible_job_indices.index(job_index)
    except ValueError:
        return None


def apply_file_list_selection(
    refs: FileListRefs,
    *,
    previous_job_index: Optional[int],
    current_job_index: Optional[int],
    visible_job_indices: Sequence[int],
    colors: Mapping[str, Any],
) -> None:
    """Update button styles for previous/current selection indices."""
    bg_tertiary = _color_with_default(colors, "bg_tertiary", "#EFF4FA")
    border_light = _color_with_default(colors, "border_light", "#D9E2EC")
    text_primary = _color_with_default(colors, "text_primary", "#1F2A37")
    primary = _color_with_default(colors, "primary", border_light)
    previous_pos = list_position_for_job(
        visible_job_indices,
        previous_job_index,
    )
    if previous_pos is not None and previous_pos < len(refs.file_buttons):
        refs.file_buttons[previous_pos].configure(
            fg_color=bg_tertiary,
            border_color=border_light,
            text_color=text_primary,
        )

    current_pos = list_position_for_job(
        visible_job_indices,
        current_job_index,
    )
    if current_pos is not None and current_pos < len(refs.file_buttons):
        accent_soft = _accent_soft_color(colors)
        refs.file_buttons[current_pos].configure(
            fg_color=accent_soft,
            border_color=primary,
            text_color=text_primary,
        )
