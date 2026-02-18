"""Main UI panel builders for the ResizeApp."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Mapping, Sequence, Tuple, Protocol

import customtkinter

from karuku_resizer.ui_file_list_panel import (
    FileListCallbacks,
    FileListRefs,
    FileListState,
    build_file_list_panel,
)
from karuku_resizer.ui_metadata_panel import (
    MetadataPanelCallbacks,
    MetadataPanelRefs,
    MetadataPanelState,
    build_metadata_panel,
)
from karuku_resizer.ui_preview_panel import (
    PreviewPanelCallbacks,
    PreviewPanelRefs,
    PreviewPanelState,
    build_preview_panel,
)
from karuku_resizer.ui_statusbar import (
    StatusBarCallbacks,
    StatusBarRefs,
    StatusBarState,
    build_statusbar,
)


class StyleCardFrame(Protocol):
    def __call__(self, frame: Any, *, corner_radius: int = ...) -> None: ...


@dataclass(frozen=True)
class MainPanelState:
    """State required for top-level panel construction."""

    scale_px: Callable[[int], int]
    font_default: Any
    font_small: Any
    colors: Mapping[str, Any]
    style_card_frame: StyleCardFrame
    style_secondary_button: Callable[[Any], None]
    canvas_background_color: Callable[[], str]


@dataclass(frozen=True)
class MainPanelCallbacks:
    """Callback wiring used while building the main content area."""

    on_filter_changed: Callable[[str], None]
    on_clear_loaded: Callable[[], None]
    register_tooltip: Callable[[Any, str], None]
    on_zoom_original: Callable[[Any], None]
    on_zoom_resized: Callable[[Any], None]
    on_drag_original_press: Callable[[Any], None]
    on_drag_original_move: Callable[[Any], None]
    on_drag_resized_press: Callable[[Any], None]
    on_drag_resized_move: Callable[[Any], None]
    on_toggle_metadata_panel: Callable[[], None]
    on_cancel_active: Callable[[], None]


@dataclass
class MainPanelRefs:
    """Reference container returned from :func:`build_main_panel`."""

    statusbar: StatusBarRefs
    file_list: FileListRefs
    preview: PreviewPanelRefs
    metadata: MetadataPanelRefs
    main_content: customtkinter.CTkFrame


def output_format_labels(available_formats: Sequence[str]) -> list[str]:
    """Build output format labels used by detail controls."""
    labels = ["自動", "JPEG", "PNG"]
    normalized = {str(fmt).strip().lower() for fmt in available_formats}
    if "webp" in normalized:
        labels.append("WEBP")
    if "avif" in normalized:
        labels.append("AVIF")
    return labels


def build_main_panel(
    parent: Any,
    *,
    state: MainPanelState,
    callbacks: MainPanelCallbacks,
    filter_values: Sequence[str],
) -> MainPanelRefs:
    """Build the main panel (status bar, file list, preview, metadata)."""

    statusbar = build_statusbar(
        parent=parent,
        state=StatusBarState(
            font_default=state.font_default,
            font_small=state.font_small,
            colors=state.colors,
            style_secondary_button=state.style_secondary_button,
        ),
        callbacks=StatusBarCallbacks(on_cancel=callbacks.on_cancel_active),
    )

    file_list = build_file_list_panel(
        parent=parent,
        state=FileListState(
            scale_px=state.scale_px,
            font_small=state.font_small,
            colors=state.colors,
        ),
        callbacks=FileListCallbacks(
            on_filter_changed=callbacks.on_filter_changed,
            on_clear_loaded=callbacks.on_clear_loaded,
            style_secondary_button=state.style_secondary_button,
            register_tooltip=callbacks.register_tooltip,
        ),
        filter_values=list(filter_values),
    )

    preview = build_preview_panel(
        parent=file_list.main_content,
        state=PreviewPanelState(
            font_default=state.font_default,
            colors=state.colors,
            style_card_frame=state.style_card_frame,
            canvas_background_color=state.canvas_background_color,
        ),
        callbacks=PreviewPanelCallbacks(
            on_zoom_original=callbacks.on_zoom_original,
            on_zoom_resized=callbacks.on_zoom_resized,
            on_drag_original_press=callbacks.on_drag_original_press,
            on_drag_original_move=callbacks.on_drag_original_move,
            on_drag_resized_press=callbacks.on_drag_resized_press,
            on_drag_resized_move=callbacks.on_drag_resized_move,
        ),
    )

    metadata = build_metadata_panel(
        parent=preview.preview_pane,
        state=MetadataPanelState(
            font_default=state.font_default,
            font_small=state.font_small,
            colors=state.colors,
            style_card_frame=state.style_card_frame,
            style_secondary_button=state.style_secondary_button,
        ),
        callbacks=MetadataPanelCallbacks(on_toggle_expanded=callbacks.on_toggle_metadata_panel),
    )

    return MainPanelRefs(
        statusbar=statusbar,
        file_list=file_list,
        preview=preview,
        metadata=metadata,
        main_content=file_list.main_content,
    )


def setup_main_layout(
    app: Any,
    *,
    state: MainPanelState,
    callbacks: MainPanelCallbacks,
    filter_values: Sequence[str],
    initial_canvas_size: Tuple[int, int] = (0, 0),
) -> MainPanelRefs:
    """Build the reusable main layout and bind refs onto app."""
    main_panel_refs = build_main_panel(
        app,
        state=state,
        callbacks=callbacks,
        filter_values=list(filter_values),
    )
    apply_main_panel_refs(app, main_panel_refs)
    app.bind("<Configure>", app._on_root_resize)
    app._last_canvas_size = initial_canvas_size
    app._imgtk_org = None
    app._imgtk_resz = None
    app._zoom_org = None
    app._zoom_resz = None
    return main_panel_refs


def apply_main_panel_refs(app: Any, refs: MainPanelRefs) -> None:
    """Attach built refs onto an app object."""

    app._statusbar_refs = refs.statusbar
    app.progress_bar = refs.statusbar.progress_bar
    app.cancel_button = refs.statusbar.cancel_button
    app.operation_stage_var = refs.statusbar.operation_stage_var
    app.operation_stage_label = refs.statusbar.operation_stage_label
    app.action_hint_var = refs.statusbar.action_hint_var
    app.action_hint_label = refs.statusbar.action_hint_label
    app.session_summary_var = refs.statusbar.session_summary_var
    app.session_summary_label = refs.statusbar.session_summary_label
    app.status_var = refs.statusbar.status_var
    app.status_label = refs.statusbar.status_label

    app.main_content = refs.main_content
    app.file_list_panel_refs = refs.file_list
    app.file_list_frame = refs.file_list.file_list_frame
    app.file_filter_var = refs.file_list.file_filter_var
    app.file_filter_segment = refs.file_list.file_filter_segment
    app.clear_loaded_button = refs.file_list.clear_loaded_button
    app.file_buttons = refs.file_list.file_buttons
    app.empty_state_label = refs.file_list.empty_state_label

    app.preview_pane = refs.preview.preview_pane
    app.frame_original = refs.preview.frame_original
    app.canvas_org = refs.preview.canvas_org
    app.info_orig_var = refs.preview.info_orig_var
    app.frame_resized = refs.preview.frame_resized
    app.lf_resized = refs.preview.frame_resized
    app.canvas_resz = refs.preview.canvas_resz
    app.info_resized_var = refs.preview.info_resized_var
    app.resized_title_label = refs.preview.resized_title_label

    app.metadata_panel_refs = refs.metadata
    app.metadata_frame = refs.metadata.metadata_frame
    app.metadata_header_frame = refs.metadata.metadata_header_frame
    app.metadata_title_label = refs.metadata.metadata_title_label
    app.metadata_toggle_button = refs.metadata.metadata_toggle_button
    app.metadata_status_var = refs.metadata.metadata_status_var
    app.metadata_status_label = refs.metadata.metadata_status_label
    app.metadata_textbox = refs.metadata.metadata_textbox
