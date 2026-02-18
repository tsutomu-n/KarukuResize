"""Detail controls UI builders for the main GUI."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Mapping, Optional, Protocol, Sequence

import customtkinter


@dataclass(frozen=True)
class DetailHeaderState:
    scale_px: Callable[[int], int]
    font_small: Any
    font_default: Any
    colors: Mapping[str, Any]
    style_card_frame: "StyleCardFrame"


@dataclass(frozen=True)
class DetailHeaderCallbacks:
    on_toggle_details: Callable[[], None]


@dataclass(frozen=True)
class DetailEntryState:
    scale_px: Callable[[int], int]
    font_default: Any
    colors: Mapping[str, Any]
    style_secondary_button: Callable[[Any], None]
    validate_callback: Callable[[str], bool]


@dataclass(frozen=True)
class DetailEntryCallbacks:
    on_mode_changed: Callable[[], None]


@dataclass(frozen=True)
class DetailOutputState:
    scale_px: Callable[[int], int]
    font_small: Any
    font_default: Any
    colors: Mapping[str, Any]
    style_card_frame: "StyleCardFrame"
    style_primary_button: Callable[[Any], None]
    style_secondary_button: Callable[[Any], None]
    output_labels: Sequence[str]
    quality_values: Sequence[str]
    webp_method_values: Sequence[str]
    avif_speed_values: Sequence[str]


@dataclass(frozen=True)
class DetailOutputCallbacks:
    on_output_format_changed: Callable[[str], None]
    on_quality_changed: Callable[[str], None]
    on_exif_mode_changed: Callable[[str], None]
    on_codec_setting_changed: Callable[[], None]
    on_webp_method_changed: Callable[[str], None]
    on_avif_speed_changed: Callable[[str], None]
    on_webp_lossless_changed: Callable[[], None]
    on_verbose_log: Callable[[], None]
    on_exif_preview: Callable[[], None]
    on_open_log_folder: Callable[[], None]


class StyleCardFrame(Protocol):
    def __call__(self, frame: Any, *, corner_radius: int = ...) -> None: ...


@dataclass
class DetailHeaderRefs:
    settings_header_frame: customtkinter.CTkFrame
    settings_summary_var: customtkinter.StringVar
    settings_summary_label: customtkinter.CTkLabel
    details_toggle_button: customtkinter.CTkButton
    recent_settings_row: customtkinter.CTkFrame
    recent_settings_title_label: customtkinter.CTkLabel
    recent_settings_buttons_frame: customtkinter.CTkFrame
    recent_settings_empty_label: customtkinter.CTkLabel


@dataclass
class DetailEntryRefs:
    mode_var: customtkinter.StringVar
    mode_radio_buttons: List[customtkinter.CTkRadioButton]
    entry_frame: customtkinter.CTkFrame
    ratio_entry: customtkinter.CTkEntry
    entry_w_single: customtkinter.CTkEntry
    entry_h_single: customtkinter.CTkEntry
    entry_w_fixed: customtkinter.CTkEntry
    entry_h_fixed: customtkinter.CTkEntry
    mode_frames: Dict[str, customtkinter.CTkFrame]
    active_mode_frame: customtkinter.CTkFrame | None
    all_entries: List[customtkinter.CTkEntry]
    entry_widgets: Dict[str, List[customtkinter.CTkEntry]]


@dataclass
class DetailOutputRefs:
    basic_controls_frame: customtkinter.CTkFrame
    output_format_var: customtkinter.StringVar
    quality_var: customtkinter.StringVar
    webp_method_var: customtkinter.StringVar
    webp_lossless_var: customtkinter.BooleanVar
    avif_speed_var: customtkinter.StringVar
    dry_run_var: customtkinter.BooleanVar
    verbose_log_var: customtkinter.BooleanVar
    exif_mode_var: customtkinter.StringVar
    remove_gps_var: customtkinter.BooleanVar

    output_format_menu: customtkinter.CTkOptionMenu
    quality_menu: customtkinter.CTkOptionMenu
    exif_mode_menu: customtkinter.CTkOptionMenu
    remove_gps_check: customtkinter.CTkCheckBox
    dry_run_check: customtkinter.CTkCheckBox
    advanced_controls_frame: customtkinter.CTkFrame
    verbose_log_check: customtkinter.CTkCheckBox
    exif_preview_button: customtkinter.CTkButton
    open_log_folder_button: customtkinter.CTkButton
    codec_controls_frame: customtkinter.CTkFrame
    webp_method_menu: customtkinter.CTkOptionMenu
    webp_lossless_check: customtkinter.CTkCheckBox
    avif_speed_menu: customtkinter.CTkOptionMenu

    exif_artist_var: customtkinter.StringVar
    exif_copyright_var: customtkinter.StringVar
    exif_user_comment_var: customtkinter.StringVar
    exif_datetime_original_var: customtkinter.StringVar
    exif_artist_entry: customtkinter.CTkEntry
    exif_copyright_entry: customtkinter.CTkEntry
    exif_comment_entry: customtkinter.CTkEntry
    exif_datetime_entry: customtkinter.CTkEntry
    exif_edit_frame: customtkinter.CTkFrame


@dataclass(frozen=True)
class DetailFormState:
    header: DetailHeaderState
    entry: DetailEntryState
    output: DetailOutputState


@dataclass(frozen=True)
class DetailFormCallbacks:
    header: DetailHeaderCallbacks
    entry: DetailEntryCallbacks
    output: DetailOutputCallbacks


@dataclass
class DetailFormRefs:
    header: DetailHeaderRefs
    entry: DetailEntryRefs
    output: DetailOutputRefs


def build_detail_form(
    parent: Any,
    state: DetailFormState,
    callbacks: DetailFormCallbacks,
    *,
    existing_entry_refs: Optional[DetailEntryRefs] = None,
) -> DetailFormRefs:
    """Build detail header, entry controls, and output controls at once."""
    header_refs = build_detail_header(
        parent,
        state=state.header,
        callbacks=callbacks.header,
    )
    entry_refs = existing_entry_refs
    if entry_refs is None:
        entry_refs = build_detail_entry_controls(
            parent,
            state=state.entry,
            callbacks=callbacks.entry,
        )
    output_refs = build_detail_output_controls(
        parent,
        state=state.output,
        callbacks=callbacks.output,
    )
    return DetailFormRefs(
        header=header_refs,
        entry=entry_refs,
        output=output_refs,
    )


def bind_detail_entry_refs(app: Any, refs: DetailEntryRefs) -> None:
    """Bind detail entry refs to a gui app instance."""
    app.mode_var = refs.mode_var
    app.mode_radio_buttons = refs.mode_radio_buttons
    app.entry_frame = refs.entry_frame
    app.ratio_entry = refs.ratio_entry
    app.entry_w_single = refs.entry_w_single
    app.entry_h_single = refs.entry_h_single
    app.entry_w_fixed = refs.entry_w_fixed
    app.entry_h_fixed = refs.entry_h_fixed
    app.mode_frames = refs.mode_frames
    app.active_mode_frame = refs.active_mode_frame
    app._all_entries = refs.all_entries
    app._entry_widgets = refs.entry_widgets
    app.pct_var = refs.ratio_entry.cget("textvariable")
    app.w_var = refs.entry_w_single.cget("textvariable")
    app.h_var = refs.entry_h_single.cget("textvariable")


def bind_detail_output_refs(app: Any, refs: DetailOutputRefs) -> None:
    """Bind detail output refs to a gui app instance."""
    app.detail_output_refs = refs
    app.detail_settings_frame = refs.basic_controls_frame
    app.basic_controls_frame = refs.basic_controls_frame
    app.output_format_var = refs.output_format_var
    app.quality_var = refs.quality_var
    app.webp_method_var = refs.webp_method_var
    app.webp_lossless_var = refs.webp_lossless_var
    app.avif_speed_var = refs.avif_speed_var
    app.dry_run_var = refs.dry_run_var
    app.verbose_log_var = refs.verbose_log_var
    app.exif_mode_var = refs.exif_mode_var
    app.remove_gps_var = refs.remove_gps_var
    app.output_format_menu = refs.output_format_menu
    app.quality_menu = refs.quality_menu
    app.exif_mode_menu = refs.exif_mode_menu
    app.remove_gps_check = refs.remove_gps_check
    app.dry_run_check = refs.dry_run_check
    app.advanced_controls_frame = refs.advanced_controls_frame
    app.verbose_log_check = refs.verbose_log_check
    app.exif_preview_button = refs.exif_preview_button
    app.open_log_folder_button = refs.open_log_folder_button
    app.codec_controls_frame = refs.codec_controls_frame
    app.webp_method_menu = refs.webp_method_menu
    app.webp_lossless_check = refs.webp_lossless_check
    app.avif_speed_menu = refs.avif_speed_menu
    app.exif_artist_var = refs.exif_artist_var
    app.exif_copyright_var = refs.exif_copyright_var
    app.exif_user_comment_var = refs.exif_user_comment_var
    app.exif_datetime_original_var = refs.exif_datetime_original_var
    app.exif_artist_entry = refs.exif_artist_entry
    app.exif_copyright_entry = refs.exif_copyright_entry
    app.exif_comment_entry = refs.exif_comment_entry
    app.exif_datetime_entry = refs.exif_datetime_entry
    app.exif_edit_frame = refs.exif_edit_frame


def bind_detail_form_refs(app: Any, refs: DetailFormRefs) -> None:
    """Bind detail refs to a gui app instance."""
    app.detail_form_refs = refs
    app.settings_header_frame = refs.header.settings_header_frame
    app.settings_summary_var = refs.header.settings_summary_var
    app.settings_summary_label = refs.header.settings_summary_label
    app.details_toggle_button = refs.header.details_toggle_button
    app.recent_settings_row = refs.header.recent_settings_row
    app.recent_settings_title_label = refs.header.recent_settings_title_label
    app.recent_settings_buttons_frame = refs.header.recent_settings_buttons_frame
    app.recent_settings_empty_label = refs.header.recent_settings_empty_label

    bind_detail_entry_refs(app, refs.entry)
    bind_detail_output_refs(app, refs.output)


def apply_output_controls_state_for_app(
    app: Any,
    *,
    output_format_to_id: Mapping[str, str],
    exif_label_to_id: Mapping[str, str],
) -> None:
    """Apply output-control states from application state values."""
    refs = getattr(app, "detail_output_refs", None)
    if refs is None:
        return
    output_format_id = output_format_to_id.get(refs.output_format_var.get(), "auto")
    details_expanded = getattr(app, "details_expanded", False)
    apply_detail_output_state(
        refs,
        is_pro_mode=app._is_pro_mode(),
        details_expanded=details_expanded,
        output_format_id=output_format_id,
        is_exif_edit_mode=exif_label_to_id.get(app.exif_mode_var.get(), "keep") == "edit",
        is_exif_remove_mode=exif_label_to_id.get(app.exif_mode_var.get(), "keep") == "remove",
        remove_gps_var=app.remove_gps_var,
        scale_px=app._scale_px,
    )


def apply_detail_panel_visibility(
    app: Any,
    *,
    expanded: bool,
) -> None:
    refs = getattr(app, "detail_form_refs", None)
    if refs is None:
        return
    is_pro = getattr(app, "_is_pro_mode", lambda: False)()
    apply_detail_controls_visibility(
        refs,
        expanded=expanded,
        is_pro_mode=is_pro,
        scale_px=app._scale_px,
    )


def apply_detail_controls_visibility(
    refs: DetailFormRefs,
    *,
    expanded: bool,
    is_pro_mode: bool = False,
    scale_px: Callable[[int], int],
) -> None:
    if expanded:
        if refs.output.basic_controls_frame.winfo_manager() != "pack":
            refs.output.basic_controls_frame.pack(
                after=refs.header.settings_header_frame,
                side="top",
                fill="x",
                padx=scale_px(12),
                pady=(0, scale_px(8)),
            )
        if is_pro_mode:
            if refs.output.advanced_controls_frame.winfo_manager() != "pack":
                refs.output.advanced_controls_frame.pack(
                    side="top",
                    fill="x",
                    padx=scale_px(10),
                    pady=(0, scale_px(6)),
                )
            if refs.output.codec_controls_frame.winfo_manager() != "pack":
                refs.output.codec_controls_frame.pack(
                    side="top",
                    fill="x",
                    padx=scale_px(10),
                    pady=(0, scale_px(6)),
                )
        refs.header.details_toggle_button.configure(text="詳細設定を隠す")
        if refs.header.recent_settings_row.winfo_manager() != "pack":
            refs.header.recent_settings_row.pack(
                side="bottom",
                fill="x",
                padx=scale_px(10),
                pady=(0, scale_px(8)),
            )
        return

    if refs.output.basic_controls_frame.winfo_manager():
        refs.output.basic_controls_frame.pack_forget()
    if refs.output.advanced_controls_frame.winfo_manager():
        refs.output.advanced_controls_frame.pack_forget()
    if refs.output.codec_controls_frame.winfo_manager():
        refs.output.codec_controls_frame.pack_forget()
    refs.header.details_toggle_button.configure(text="詳細設定を表示")
    if refs.header.recent_settings_row.winfo_manager():
        refs.header.recent_settings_row.pack_forget()


def apply_detail_output_state(
    output_refs: DetailOutputRefs,
    *,
    is_pro_mode: bool,
    details_expanded: bool = True,
    output_format_id: str,
    is_exif_edit_mode: bool,
    is_exif_remove_mode: bool,
    remove_gps_var: customtkinter.BooleanVar,
    scale_px: Callable[[int], int],
) -> None:
    apply_detail_mode(
        output_refs,
        is_pro_mode=is_pro_mode,
        details_expanded=details_expanded,
        scale_px=scale_px,
    )
    webp_state = "normal" if output_format_id == "webp" else "disabled"
    avif_state = "normal" if output_format_id == "avif" else "disabled"
    output_refs.webp_method_menu.configure(state=webp_state)
    output_refs.webp_lossless_check.configure(state=webp_state)
    output_refs.avif_speed_menu.configure(state=avif_state)

    is_edit_mode = is_exif_edit_mode
    state = "normal" if is_edit_mode else "disabled"
    for entry in (
        output_refs.exif_artist_entry,
        output_refs.exif_copyright_entry,
        output_refs.exif_comment_entry,
        output_refs.exif_datetime_entry,
    ):
        entry.configure(state=state)

    gps_state = "disabled" if is_exif_remove_mode else "normal"
    if gps_state == "disabled":
        remove_gps_var.set(False)
    output_refs.remove_gps_check.configure(state=gps_state)

    if is_pro_mode and is_exif_edit_mode:
        if output_refs.exif_edit_frame.winfo_manager() != "pack":
            output_refs.exif_edit_frame.pack(
                side="top",
                fill="x",
                padx=scale_px(10),
                pady=(0, scale_px(6)),
            )
    else:
        if output_refs.exif_edit_frame.winfo_manager():
            output_refs.exif_edit_frame.pack_forget()


def build_detail_header(
    parent: Any,
    state: DetailHeaderState,
    callbacks: DetailHeaderCallbacks,
) -> DetailHeaderRefs:
    settings_header_frame = customtkinter.CTkFrame(parent)
    state.style_card_frame(settings_header_frame, corner_radius=12)
    settings_header_frame.pack(
        side="top",
        fill="x",
        padx=state.scale_px(12),
        pady=(0, state.scale_px(3)),
    )

    settings_summary_var = customtkinter.StringVar(value="")
    settings_summary_label = customtkinter.CTkLabel(
        settings_header_frame,
        textvariable=settings_summary_var,
        anchor="w",
        font=state.font_default,
        text_color=state.colors["primary"],
    )
    settings_summary_label.pack(
        side="left",
        fill="x",
        expand=True,
        padx=(state.scale_px(10), 0),
        pady=state.scale_px(4),
    )

    details_toggle_button = customtkinter.CTkButton(
        settings_header_frame,
        text="詳細設定を表示",
        width=state.scale_px(140),
        command=callbacks.on_toggle_details,
        font=state.font_small,
    )
    details_toggle_button.pack(side="right", padx=(0, state.scale_px(6)), pady=state.scale_px(4))

    recent_settings_row = customtkinter.CTkFrame(settings_header_frame, fg_color="transparent")
    recent_settings_title_label = customtkinter.CTkLabel(
        recent_settings_row,
        text="最近使った設定",
        font=state.font_small,
        text_color=state.colors["text_secondary"],
    )
    recent_settings_title_label.pack(side="left", padx=(0, 8))
    recent_settings_buttons_frame = customtkinter.CTkFrame(
        recent_settings_row,
        fg_color="transparent",
    )
    recent_settings_buttons_frame.pack(side="left", fill="x", expand=True)
    recent_settings_empty_label = customtkinter.CTkLabel(
        recent_settings_buttons_frame,
        text="まだありません",
        font=state.font_small,
        text_color=state.colors["text_tertiary"],
    )
    recent_settings_empty_label.pack(side="left")
    recent_settings_row.pack_forget()

    return DetailHeaderRefs(
        settings_header_frame=settings_header_frame,
        settings_summary_var=settings_summary_var,
        settings_summary_label=settings_summary_label,
        details_toggle_button=details_toggle_button,
        recent_settings_row=recent_settings_row,
        recent_settings_title_label=recent_settings_title_label,
        recent_settings_buttons_frame=recent_settings_buttons_frame,
        recent_settings_empty_label=recent_settings_empty_label,
    )


def build_detail_entry_controls(
    parent: Any,
    state: DetailEntryState,
    callbacks: DetailEntryCallbacks,
) -> DetailEntryRefs:
    mode_var = customtkinter.StringVar(value="ratio")
    mode_radio_buttons: List[customtkinter.CTkRadioButton] = []
    modes = [
        ("比率 %", "ratio"),
        ("幅 px", "width"),
        ("高さ px", "height"),
        ("幅×高", "fixed"),
    ]
    for text, value in modes:
        mode_radio = customtkinter.CTkRadioButton(
            parent,
            text=text,
            variable=mode_var,
            value=value,
            command=callbacks.on_mode_changed,
            font=state.font_default,
            fg_color=state.colors["primary"],
            hover_color=state.colors["hover"],
            border_color=state.colors["border_medium"],
            text_color=state.colors["text_primary"],
        )
        mode_radio.pack(side="left", padx=(0, state.scale_px(6)))
        state.style_secondary_button(mode_radio)
        mode_radio_buttons.append(mode_radio)

    entry_frame = customtkinter.CTkFrame(parent, fg_color="transparent")
    entry_frame.pack(side="left", padx=(state.scale_px(8), state.scale_px(10)))

    vcmd = (parent.register(state.validate_callback), "%P")

    frame_ratio = customtkinter.CTkFrame(entry_frame, fg_color="transparent")
    ratio_entry = customtkinter.CTkEntry(
        frame_ratio,
        textvariable=customtkinter.StringVar(value="100"),
        width=54,
        validate="key",
        validatecommand=vcmd,
        font=state.font_default,
        fg_color=state.colors["input_bg"],
        border_color=state.colors["border_light"],
        text_color=state.colors["text_primary"],
        corner_radius=8,
    )
    ratio_entry.pack(side="left")
    customtkinter.CTkLabel(
        frame_ratio,
        text="%",
        font=state.font_default,
        text_color=state.colors["text_secondary"],
    ).pack(side="left")

    frame_width = customtkinter.CTkFrame(entry_frame, fg_color="transparent")
    entry_w_single = customtkinter.CTkEntry(
        frame_width,
        textvariable=customtkinter.StringVar(),
        width=64,
        validate="key",
        validatecommand=vcmd,
        fg_color=state.colors["input_bg"],
        border_color=state.colors["border_light"],
        text_color=state.colors["text_primary"],
        corner_radius=8,
    )
    entry_w_single.pack(side="left")
    customtkinter.CTkLabel(
        frame_width,
        text="px",
        font=state.font_default,
        text_color=state.colors["text_secondary"],
    ).pack(side="left")

    frame_height = customtkinter.CTkFrame(entry_frame, fg_color="transparent")
    entry_h_single = customtkinter.CTkEntry(
        frame_height,
        textvariable=customtkinter.StringVar(),
        width=64,
        validate="key",
        validatecommand=vcmd,
        fg_color=state.colors["input_bg"],
        border_color=state.colors["border_light"],
        text_color=state.colors["text_primary"],
        corner_radius=8,
    )
    entry_h_single.pack(side="left")
    customtkinter.CTkLabel(
        frame_height,
        text="px",
        font=state.font_default,
        text_color=state.colors["text_secondary"],
    ).pack(side="left")

    frame_fixed = customtkinter.CTkFrame(entry_frame, fg_color="transparent")
    entry_w_fixed = customtkinter.CTkEntry(
        frame_fixed,
        textvariable=customtkinter.StringVar(),
        width=64,
        validate="key",
        validatecommand=vcmd,
        fg_color=state.colors["input_bg"],
        border_color=state.colors["border_light"],
        text_color=state.colors["text_primary"],
        corner_radius=8,
    )
    entry_w_fixed.pack(side="left")
    customtkinter.CTkLabel(
        frame_fixed,
        text="×",
        font=state.font_default,
        text_color=state.colors["text_secondary"],
    ).pack(side="left")
    entry_h_fixed = customtkinter.CTkEntry(
        frame_fixed,
        textvariable=customtkinter.StringVar(),
        width=64,
        validate="key",
        validatecommand=vcmd,
        fg_color=state.colors["input_bg"],
        border_color=state.colors["border_light"],
        text_color=state.colors["text_primary"],
        corner_radius=8,
    )
    entry_h_fixed.pack(side="left")
    customtkinter.CTkLabel(
        frame_fixed,
        text="px",
        font=state.font_default,
        text_color=state.colors["text_secondary"],
    ).pack(side="left")

    mode_frames = {
        "ratio": frame_ratio,
        "width": frame_width,
        "height": frame_height,
        "fixed": frame_fixed,
    }
    entry_widgets = {
        "ratio": [ratio_entry],
        "width": [entry_w_single],
        "height": [entry_h_single],
        "fixed": [entry_w_fixed, entry_h_fixed],
    }

    return DetailEntryRefs(
        mode_var=mode_var,
        mode_radio_buttons=mode_radio_buttons,
        entry_frame=entry_frame,
        ratio_entry=ratio_entry,
        entry_w_single=entry_w_single,
        entry_h_single=entry_h_single,
        entry_w_fixed=entry_w_fixed,
        entry_h_fixed=entry_h_fixed,
        mode_frames=mode_frames,
        active_mode_frame=frame_ratio,
        all_entries=[ratio_entry, entry_w_single, entry_h_single, entry_w_fixed, entry_h_fixed],
        entry_widgets=entry_widgets,
    )


def build_detail_output_controls(
    parent: Any,
    state: DetailOutputState,
    callbacks: DetailOutputCallbacks,
) -> DetailOutputRefs:
    basic_controls_frame = customtkinter.CTkFrame(parent)
    state.style_card_frame(basic_controls_frame, corner_radius=10)
    basic_controls_frame.pack(
        side="top",
        fill="x",
        padx=state.scale_px(10),
        pady=(state.scale_px(10), state.scale_px(6)),
    )

    output_format_var = customtkinter.StringVar(value="自動")
    quality_var = customtkinter.StringVar(value="85")
    webp_method_var = customtkinter.StringVar(value="6")
    webp_lossless_var = customtkinter.BooleanVar(value=False)
    avif_speed_var = customtkinter.StringVar(value="6")
    dry_run_var = customtkinter.BooleanVar(value=False)
    verbose_log_var = customtkinter.BooleanVar(value=False)
    exif_mode_var = customtkinter.StringVar(value="保持")
    remove_gps_var = customtkinter.BooleanVar(value=False)

    customtkinter.CTkLabel(
        basic_controls_frame,
        text="出力形式",
        font=state.font_small,
        text_color=state.colors["text_secondary"],
    ).pack(side="left", padx=(state.scale_px(10), state.scale_px(4)), pady=state.scale_px(8))
    output_format_menu = customtkinter.CTkOptionMenu(
        basic_controls_frame,
        variable=output_format_var,
        values=list(state.output_labels),
        width=state.scale_px(110),
        command=callbacks.on_output_format_changed,
        font=state.font_small,
        fg_color=state.colors["bg_tertiary"],
        button_color=state.colors["primary"],
        button_hover_color=state.colors["hover"],
        text_color=state.colors["text_primary"],
        dropdown_fg_color=state.colors["bg_secondary"],
        dropdown_text_color=state.colors["text_primary"],
    )
    output_format_menu.pack(side="left", padx=(0, state.scale_px(12)), pady=state.scale_px(8))

    customtkinter.CTkLabel(
        basic_controls_frame,
        text="品質",
        font=state.font_small,
        text_color=state.colors["text_secondary"],
    ).pack(side="left", padx=(0, state.scale_px(4)), pady=state.scale_px(8))
    quality_menu = customtkinter.CTkOptionMenu(
        basic_controls_frame,
        variable=quality_var,
        values=list(state.quality_values),
        width=state.scale_px(90),
        command=callbacks.on_quality_changed,
        font=state.font_small,
        fg_color=state.colors["bg_tertiary"],
        button_color=state.colors["primary"],
        button_hover_color=state.colors["hover"],
        text_color=state.colors["text_primary"],
        dropdown_fg_color=state.colors["bg_secondary"],
        dropdown_text_color=state.colors["text_primary"],
    )
    quality_menu.pack(side="left", padx=(0, state.scale_px(12)), pady=state.scale_px(8))

    customtkinter.CTkLabel(
        basic_controls_frame,
        text="EXIF",
        font=state.font_small,
        text_color=state.colors["text_secondary"],
    ).pack(side="left", padx=(0, state.scale_px(4)), pady=state.scale_px(8))
    exif_mode_menu = customtkinter.CTkOptionMenu(
        basic_controls_frame,
        variable=exif_mode_var,
        values=["保持", "編集", "削除"],
        width=state.scale_px(90),
        command=callbacks.on_exif_mode_changed,
        font=state.font_small,
        fg_color=state.colors["bg_tertiary"],
        button_color=state.colors["primary"],
        button_hover_color=state.colors["hover"],
        text_color=state.colors["text_primary"],
        dropdown_fg_color=state.colors["bg_secondary"],
        dropdown_text_color=state.colors["text_primary"],
    )
    exif_mode_menu.pack(side="left", padx=(0, state.scale_px(10)), pady=state.scale_px(8))

    remove_gps_check = customtkinter.CTkCheckBox(
        basic_controls_frame,
        text="GPS削除",
        variable=remove_gps_var,
        font=state.font_small,
        fg_color=state.colors["primary"],
        hover_color=state.colors["hover"],
        border_color=state.colors["border_medium"],
        text_color=state.colors["text_primary"],
    )
    remove_gps_check.pack(side="left", padx=(0, state.scale_px(10)), pady=state.scale_px(8))

    dry_run_check = customtkinter.CTkCheckBox(
        basic_controls_frame,
        text="ドライラン",
        variable=dry_run_var,
        font=state.font_small,
        fg_color=state.colors["primary"],
        hover_color=state.colors["hover"],
        border_color=state.colors["border_medium"],
        text_color=state.colors["text_primary"],
    )
    dry_run_check.pack(side="left", padx=(0, state.scale_px(12)), pady=state.scale_px(8))

    advanced_controls_frame = customtkinter.CTkFrame(parent)
    state.style_card_frame(advanced_controls_frame, corner_radius=10)
    advanced_controls_frame.pack(
        side="top",
        fill="x",
        padx=state.scale_px(10),
        pady=(0, state.scale_px(6)),
    )

    verbose_log_check = customtkinter.CTkCheckBox(
        advanced_controls_frame,
        text="詳細ログ",
        variable=verbose_log_var,
        command=callbacks.on_verbose_log,
        font=state.font_small,
        fg_color=state.colors["primary"],
        hover_color=state.colors["hover"],
        border_color=state.colors["border_medium"],
        text_color=state.colors["text_primary"],
    )
    verbose_log_check.pack(side="left", padx=(state.scale_px(10), state.scale_px(8)), pady=state.scale_px(8))

    exif_preview_button = customtkinter.CTkButton(
        advanced_controls_frame,
        text="EXIF差分",
        width=state.scale_px(95),
        command=callbacks.on_exif_preview,
        font=state.font_small,
    )
    state.style_secondary_button(exif_preview_button)
    exif_preview_button.pack(side="left", padx=(0, state.scale_px(10)), pady=state.scale_px(8))

    open_log_folder_button = customtkinter.CTkButton(
        advanced_controls_frame,
        text="ログフォルダ",
        width=state.scale_px(110),
        command=callbacks.on_open_log_folder,
        font=state.font_small,
    )
    state.style_secondary_button(open_log_folder_button)
    open_log_folder_button.pack(side="left", padx=(0, state.scale_px(10)), pady=state.scale_px(8))

    codec_controls_frame = customtkinter.CTkFrame(parent)
    state.style_card_frame(codec_controls_frame, corner_radius=10)
    codec_controls_frame.pack(
        side="top",
        fill="x",
        padx=state.scale_px(10),
        pady=(0, state.scale_px(6)),
    )

    customtkinter.CTkLabel(
        codec_controls_frame,
        text="WEBP method",
        font=state.font_small,
        text_color=state.colors["text_secondary"],
    ).pack(side="left", padx=(state.scale_px(10), state.scale_px(4)), pady=state.scale_px(8))
    webp_method_menu = customtkinter.CTkOptionMenu(
        codec_controls_frame,
        variable=webp_method_var,
        values=list(state.webp_method_values),
        width=state.scale_px(80),
        command=callbacks.on_webp_method_changed,
        font=state.font_small,
        fg_color=state.colors["bg_tertiary"],
        button_color=state.colors["primary"],
        button_hover_color=state.colors["hover"],
        text_color=state.colors["text_primary"],
        dropdown_fg_color=state.colors["bg_secondary"],
        dropdown_text_color=state.colors["text_primary"],
    )
    webp_method_menu.pack(side="left", padx=(0, state.scale_px(8)), pady=state.scale_px(8))

    webp_lossless_check = customtkinter.CTkCheckBox(
        codec_controls_frame,
        text="WEBP lossless",
        variable=webp_lossless_var,
        command=callbacks.on_webp_lossless_changed,
        font=state.font_small,
        fg_color=state.colors["primary"],
        hover_color=state.colors["hover"],
        border_color=state.colors["border_medium"],
        text_color=state.colors["text_primary"],
    )
    webp_lossless_check.pack(side="left", padx=(0, state.scale_px(14)), pady=state.scale_px(8))

    customtkinter.CTkLabel(
        codec_controls_frame,
        text="AVIF speed（低速=高品質）",
        font=state.font_small,
        text_color=state.colors["text_secondary"],
    ).pack(side="left", padx=(0, state.scale_px(4)), pady=state.scale_px(8))
    avif_speed_menu = customtkinter.CTkOptionMenu(
        codec_controls_frame,
        variable=avif_speed_var,
        values=list(state.avif_speed_values),
        width=state.scale_px(80),
        command=callbacks.on_avif_speed_changed,
        font=state.font_small,
        fg_color=state.colors["bg_tertiary"],
        button_color=state.colors["primary"],
        button_hover_color=state.colors["hover"],
        text_color=state.colors["text_primary"],
        dropdown_fg_color=state.colors["bg_secondary"],
        dropdown_text_color=state.colors["text_primary"],
    )
    avif_speed_menu.pack(side="left", padx=(0, state.scale_px(8)), pady=state.scale_px(8))

    exif_artist_var = customtkinter.StringVar(value="")
    exif_copyright_var = customtkinter.StringVar(value="")
    exif_user_comment_var = customtkinter.StringVar(value="")
    exif_datetime_original_var = customtkinter.StringVar(value="")

    exif_edit_frame = customtkinter.CTkFrame(parent)
    state.style_card_frame(exif_edit_frame, corner_radius=10)

    customtkinter.CTkLabel(
        exif_edit_frame,
        text="撮影者",
        font=state.font_small,
        text_color=state.colors["text_secondary"],
    ).pack(side="left", padx=(state.scale_px(10), state.scale_px(4)), pady=state.scale_px(8))
    exif_artist_entry = customtkinter.CTkEntry(
        exif_edit_frame,
        textvariable=exif_artist_var,
        width=state.scale_px(124),
        font=state.font_small,
        fg_color=state.colors["input_bg"],
        border_color=state.colors["border_light"],
        text_color=state.colors["text_primary"],
        corner_radius=8,
    )
    exif_artist_entry.pack(side="left", padx=(0, state.scale_px(8)), pady=state.scale_px(8))

    customtkinter.CTkLabel(
        exif_edit_frame,
        text="著作権",
        font=state.font_small,
        text_color=state.colors["text_secondary"],
    ).pack(side="left", padx=(0, state.scale_px(4)), pady=state.scale_px(8))
    exif_copyright_entry = customtkinter.CTkEntry(
        exif_edit_frame,
        textvariable=exif_copyright_var,
        width=state.scale_px(144),
        font=state.font_small,
        fg_color=state.colors["input_bg"],
        border_color=state.colors["border_light"],
        text_color=state.colors["text_primary"],
        corner_radius=8,
    )
    exif_copyright_entry.pack(side="left", padx=(0, state.scale_px(8)), pady=state.scale_px(8))

    customtkinter.CTkLabel(
        exif_edit_frame,
        text="コメント",
        font=state.font_small,
        text_color=state.colors["text_secondary"],
    ).pack(side="left", padx=(0, state.scale_px(4)), pady=state.scale_px(8))
    exif_comment_entry = customtkinter.CTkEntry(
        exif_edit_frame,
        textvariable=exif_user_comment_var,
        width=state.scale_px(184),
        font=state.font_small,
        fg_color=state.colors["input_bg"],
        border_color=state.colors["border_light"],
        text_color=state.colors["text_primary"],
        corner_radius=8,
    )
    exif_comment_entry.pack(side="left", padx=(0, state.scale_px(8)), pady=state.scale_px(8))

    customtkinter.CTkLabel(
        exif_edit_frame,
        text="撮影日時",
        font=state.font_small,
        text_color=state.colors["text_secondary"],
    ).pack(side="left", padx=(0, state.scale_px(4)), pady=state.scale_px(8))
    exif_datetime_entry = customtkinter.CTkEntry(
        exif_edit_frame,
        textvariable=exif_datetime_original_var,
        width=state.scale_px(150),
        placeholder_text="YYYY:MM:DD HH:MM:SS",
        font=state.font_small,
        fg_color=state.colors["input_bg"],
        border_color=state.colors["border_light"],
        text_color=state.colors["text_primary"],
        corner_radius=8,
    )
    exif_datetime_entry.pack(side="left", pady=state.scale_px(8))

    return DetailOutputRefs(
        basic_controls_frame=basic_controls_frame,
        output_format_var=output_format_var,
        quality_var=quality_var,
        webp_method_var=webp_method_var,
        webp_lossless_var=webp_lossless_var,
        avif_speed_var=avif_speed_var,
        dry_run_var=dry_run_var,
        verbose_log_var=verbose_log_var,
        exif_mode_var=exif_mode_var,
        remove_gps_var=remove_gps_var,
        output_format_menu=output_format_menu,
        quality_menu=quality_menu,
        exif_mode_menu=exif_mode_menu,
        remove_gps_check=remove_gps_check,
        dry_run_check=dry_run_check,
        advanced_controls_frame=advanced_controls_frame,
        verbose_log_check=verbose_log_check,
        exif_preview_button=exif_preview_button,
        open_log_folder_button=open_log_folder_button,
        codec_controls_frame=codec_controls_frame,
        webp_method_menu=webp_method_menu,
        webp_lossless_check=webp_lossless_check,
        avif_speed_menu=avif_speed_menu,
        exif_artist_var=exif_artist_var,
        exif_copyright_var=exif_copyright_var,
        exif_user_comment_var=exif_user_comment_var,
        exif_datetime_original_var=exif_datetime_original_var,
        exif_artist_entry=exif_artist_entry,
        exif_copyright_entry=exif_copyright_entry,
        exif_comment_entry=exif_comment_entry,
        exif_datetime_entry=exif_datetime_entry,
        exif_edit_frame=exif_edit_frame,
    )


def apply_detail_mode(
    output_refs: DetailOutputRefs,
    *,
    is_pro_mode: bool,
    details_expanded: bool = True,
    scale_px: Callable[[int], int],
) -> None:
    if is_pro_mode and details_expanded:
        if output_refs.advanced_controls_frame.winfo_manager() != "pack":
            output_refs.advanced_controls_frame.pack(
                side="top",
                fill="x",
                padx=scale_px(10),
                pady=(0, scale_px(6)),
            )
        if output_refs.codec_controls_frame.winfo_manager() != "pack":
            output_refs.codec_controls_frame.pack(
                side="top",
                fill="x",
                padx=scale_px(10),
                pady=(0, scale_px(6)),
            )
        return

    if output_refs.advanced_controls_frame.winfo_manager():
        output_refs.advanced_controls_frame.pack_forget()
    if output_refs.codec_controls_frame.winfo_manager():
        output_refs.codec_controls_frame.pack_forget()
