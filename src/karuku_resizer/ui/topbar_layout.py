"""Top bar layout helpers for ResizeApp.

`gui_app.py` から上部UI構築ロジックを切り出し、責務を分離する。
"""

from __future__ import annotations

from typing import Any, Dict, List, Tuple

import customtkinter

from karuku_resizer.icon_loader import load_icon

TOPBAR_DENSITY_COMPACT_MAX_WIDTH = 1310
TOPBAR_WIDTHS: Dict[str, Dict[str, int]] = {
    "normal": {
        "select": 128,
        "help": 108,
        "settings": 90,
        "preset_menu": 180,
        "preset_action": 72,
        "preview": 118,
        "save": 118,
        "batch": 118,
        "zoom": 140,
    },
    "compact": {
        "select": 118,
        "help": 94,
        "settings": 82,
        "preset_menu": 156,
        "preset_action": 64,
        "preview": 108,
        "save": 96,
        "batch": 106,
        "zoom": 126,
    },
}

ColorMap = Dict[str, Tuple[str, str]]


def topbar_density_for_width(window_width: int) -> str:
    return "compact" if window_width <= TOPBAR_DENSITY_COMPACT_MAX_WIDTH else "normal"


def batch_button_text_for_density(density: str) -> str:
    return "一括保存" if density == "compact" else "一括適用保存"


def select_button_text_for_state(app: Any) -> str:
    if app._is_pro_mode():
        if app._topbar_density == "compact":
            return "画像/フォルダ選択"
        return "画像/フォルダを選択"
    return "画像を選択"


def apply_topbar_density(app: Any, window_width: int, *, min_window_width: int) -> None:
    density = topbar_density_for_width(window_width)
    if density == app._topbar_density:
        return
    app._topbar_density = density
    widths = TOPBAR_WIDTHS[density]

    app.select_button.configure(width=widths["select"])
    app.help_button.configure(width=widths["help"])
    app.settings_button.configure(width=widths["settings"])
    app.preset_menu.configure(width=widths["preset_menu"])
    app.preset_manage_button.configure(width=widths["preset_action"])
    app.preview_button.configure(width=widths["preview"])
    app.save_button.configure(width=widths["save"])
    app.batch_button.configure(
        width=widths["batch"],
        text=batch_button_text_for_density(density),
    )
    app.zoom_cb.configure(width=widths["zoom"])
    app.select_button.configure(text=select_button_text_for_state(app))


def refresh_topbar_density(app: Any, *, min_window_width: int) -> None:
    width = max(app.winfo_width(), min_window_width)
    apply_topbar_density(app, width, min_window_width=min_window_width)


def schedule_auto_preview(app: Any, *_args: Any) -> None:
    if app._auto_preview_timer is not None:
        app.after_cancel(app._auto_preview_timer)
    app._auto_preview_timer = app.after(300, app._auto_preview)


def trigger_auto_preview(app: Any) -> None:
    app._auto_preview_timer = None
    if app.current_index is None:
        return
    if app._is_loading_files:
        return
    if app._operation_scope is not None and app._operation_scope.active:
        return
    try:
        app._draw_previews(app.jobs[app.current_index])
    except Exception:
        pass


def setup_action_buttons(app: Any, parent: Any, *, colors: ColorMap) -> None:
    topbar_widths = TOPBAR_WIDTHS["normal"]
    app._icon_refresh = load_icon("refresh-cw", 16)
    app.preview_button = customtkinter.CTkButton(
        parent,
        text="プレビュー",
        image=app._icon_refresh,
        compound="left",
        width=topbar_widths["preview"],
        command=app._preview_current,
        font=app.font_default,
    )
    app._style_outline_button(app.preview_button)
    app.preview_button.pack(side="left", padx=(0, 8), pady=8)

    app._icon_save = load_icon("save", 16)
    app.save_button = customtkinter.CTkButton(
        parent,
        text="保存",
        image=app._icon_save,
        compound="left",
        width=topbar_widths["save"],
        command=app._save_current,
        font=app.font_default,
    )
    app._style_primary_button(app.save_button)
    app.save_button.pack(side="left", pady=8)

    app._icon_folder = load_icon("folder", 16)
    app.batch_button = customtkinter.CTkButton(
        parent,
        text=batch_button_text_for_density(app._topbar_density),
        image=app._icon_folder,
        compound="left",
        width=topbar_widths["batch"],
        command=app._batch_save,
        font=app.font_default,
    )
    app._style_primary_button(app.batch_button)
    app.batch_button.pack(side="left", padx=8, pady=8)

    app.zoom_var = customtkinter.StringVar(value="画面に合わせる")
    app.zoom_cb = customtkinter.CTkComboBox(
        parent,
        variable=app.zoom_var,
        values=["画面に合わせる", "100%", "200%", "300%"],
        width=topbar_widths["zoom"],
        state="readonly",
        command=app._apply_zoom_selection,
        font=app.font_default,
        fg_color=colors["bg_tertiary"],
        border_color=colors["border_light"],
        button_color=colors["primary"],
        button_hover_color=colors["hover"],
        text_color=colors["text_primary"],
        dropdown_fg_color=colors["bg_secondary"],
        dropdown_text_color=colors["text_primary"],
    )
    app.zoom_cb.pack(side="left", padx=(4, 8), pady=8)


def setup_entry_widgets(app: Any, parent: Any, *, colors: ColorMap) -> None:
    app.entry_frame = customtkinter.CTkFrame(parent, fg_color="transparent")
    app.entry_frame.pack(side="left", padx=(8, 10))

    vcmd = (app.register(app._validate_int), "%P")

    app.pct_var = customtkinter.StringVar(value="100")
    app.w_var = customtkinter.StringVar()
    app.h_var = customtkinter.StringVar()

    frame_ratio = customtkinter.CTkFrame(app.entry_frame, fg_color="transparent")
    app.ratio_entry = customtkinter.CTkEntry(
        frame_ratio,
        textvariable=app.pct_var,
        width=54,
        validate="key",
        validatecommand=vcmd,
        font=app.font_default,
        fg_color=colors["input_bg"],
        border_color=colors["border_light"],
        text_color=colors["text_primary"],
        corner_radius=8,
    )
    app.ratio_entry.pack(side="left")
    customtkinter.CTkLabel(
        frame_ratio,
        text="%",
        font=app.font_default,
        text_color=colors["text_secondary"],
    ).pack(side="left")

    frame_width = customtkinter.CTkFrame(app.entry_frame, fg_color="transparent")
    app.entry_w_single = customtkinter.CTkEntry(
        frame_width,
        textvariable=app.w_var,
        width=64,
        validate="key",
        validatecommand=vcmd,
        fg_color=colors["input_bg"],
        border_color=colors["border_light"],
        text_color=colors["text_primary"],
        corner_radius=8,
    )
    app.entry_w_single.pack(side="left")
    customtkinter.CTkLabel(
        frame_width,
        text="px",
        font=app.font_default,
        text_color=colors["text_secondary"],
    ).pack(side="left")

    frame_height = customtkinter.CTkFrame(app.entry_frame, fg_color="transparent")
    app.entry_h_single = customtkinter.CTkEntry(
        frame_height,
        textvariable=app.h_var,
        width=64,
        validate="key",
        validatecommand=vcmd,
        fg_color=colors["input_bg"],
        border_color=colors["border_light"],
        text_color=colors["text_primary"],
        corner_radius=8,
    )
    app.entry_h_single.pack(side="left")
    customtkinter.CTkLabel(
        frame_height,
        text="px",
        font=app.font_default,
        text_color=colors["text_secondary"],
    ).pack(side="left")

    frame_fixed = customtkinter.CTkFrame(app.entry_frame, fg_color="transparent")
    app.entry_w_fixed = customtkinter.CTkEntry(
        frame_fixed,
        textvariable=app.w_var,
        width=64,
        validate="key",
        validatecommand=vcmd,
        fg_color=colors["input_bg"],
        border_color=colors["border_light"],
        text_color=colors["text_primary"],
        corner_radius=8,
    )
    app.entry_w_fixed.pack(side="left")
    customtkinter.CTkLabel(
        frame_fixed,
        text="×",
        font=app.font_default,
        text_color=colors["text_secondary"],
    ).pack(side="left")
    app.entry_h_fixed = customtkinter.CTkEntry(
        frame_fixed,
        textvariable=app.h_var,
        width=64,
        validate="key",
        validatecommand=vcmd,
        fg_color=colors["input_bg"],
        border_color=colors["border_light"],
        text_color=colors["text_primary"],
        corner_radius=8,
    )
    app.entry_h_fixed.pack(side="left")
    customtkinter.CTkLabel(
        frame_fixed,
        text="px",
        font=app.font_default,
        text_color=colors["text_secondary"],
    ).pack(side="left")

    app.mode_frames = {
        "ratio": frame_ratio,
        "width": frame_width,
        "height": frame_height,
        "fixed": frame_fixed,
    }
    app.active_mode_frame = None

    app._all_entries = [
        app.ratio_entry,
        app.entry_w_single,
        app.entry_h_single,
        app.entry_w_fixed,
        app.entry_h_fixed,
    ]
    app._entry_widgets = {
        "ratio": [app.ratio_entry],
        "width": [app.entry_w_single],
        "height": [app.entry_h_single],
        "fixed": [app.entry_w_fixed, app.entry_h_fixed],
    }

    app._auto_preview_timer = None
    for var in (app.pct_var, app.w_var, app.h_var):
        var.trace_add("write", app._schedule_auto_preview)


def setup_ui(app: Any, *, colors: ColorMap, preset_none_label: str) -> None:
    top_container = customtkinter.CTkFrame(app)
    app._style_card_frame(top_container)
    top_container.pack(side="top", fill="x", padx=12, pady=(8, 6))

    top_row_primary = customtkinter.CTkFrame(top_container, fg_color="transparent")
    top_row_primary.pack(side="top", fill="x", padx=8, pady=(6, 2))

    top_row_secondary = customtkinter.CTkFrame(top_container, fg_color="transparent")
    top_row_secondary.pack(side="top", fill="x", padx=8, pady=(2, 6))
    topbar_widths = TOPBAR_WIDTHS["normal"]

    app._icon_folder_open = load_icon("folder-open", 16)
    app.select_button = customtkinter.CTkButton(
        top_row_primary,
        text="画像を選択",
        image=app._icon_folder_open,
        compound="left",
        width=topbar_widths["select"],
        command=app._select_files,
        font=app.font_default,
    )
    app._style_primary_button(app.select_button)
    app.select_button.pack(side="left", padx=(0, 6), pady=4)
    app._icon_circle_help = load_icon("circle-help", 16)
    app.help_button = customtkinter.CTkButton(
        top_row_primary,
        text="使い方",
        image=app._icon_circle_help,
        compound="left",
        width=topbar_widths["help"],
        command=app._show_help,
        font=app.font_default,
    )
    app._style_tertiary_button(app.help_button)
    app.help_button.pack(side="left", padx=(0, 8), pady=4)
    app._icon_settings = load_icon("settings", 16)
    app.settings_button = customtkinter.CTkButton(
        top_row_primary,
        text="設定",
        image=app._icon_settings,
        compound="left",
        width=topbar_widths["settings"],
        command=app._open_settings_dialog,
        font=app.font_default,
    )
    app._style_tertiary_button(app.settings_button)
    app.settings_button.pack(side="left", padx=(0, 8), pady=4)

    preset_spacer = customtkinter.CTkFrame(top_row_primary, fg_color="transparent")
    preset_spacer.pack(side="left", expand=True)

    customtkinter.CTkLabel(
        top_row_primary,
        text="プリセット",
        font=app.font_small,
        text_color=colors["text_secondary"],
    ).pack(side="left", padx=(0, 4), pady=4)
    app.preset_var = customtkinter.StringVar(value=preset_none_label)
    app.preset_menu = customtkinter.CTkOptionMenu(
        top_row_primary,
        variable=app.preset_var,
        values=[preset_none_label],
        width=topbar_widths["preset_menu"],
        command=app._on_preset_menu_changed,
        font=app.font_small,
        fg_color=colors["bg_tertiary"],
        button_color=colors["primary"],
        button_hover_color=colors["hover"],
        text_color=colors["text_primary"],
        dropdown_fg_color=colors["bg_secondary"],
        dropdown_text_color=colors["text_primary"],
    )
    app.preset_menu.pack(side="left", padx=(0, 6), pady=4)
    app.preset_manage_button = customtkinter.CTkButton(
        top_row_primary,
        text="管理",
        width=topbar_widths["preset_action"],
        command=app._open_preset_manager_dialog,
        font=app.font_small,
    )
    app._style_tertiary_button(app.preset_manage_button)
    app.preset_manage_button.pack(side="left", padx=(0, 0), pady=4)

    size_controls_frame = customtkinter.CTkFrame(top_row_secondary, fg_color="transparent")
    size_controls_frame.pack(side="left", fill="x", expand=True)

    app.mode_var = customtkinter.StringVar(value="ratio")
    app.mode_radio_buttons = []
    modes = [
        ("比率 %", "ratio"),
        ("幅 px", "width"),
        ("高さ px", "height"),
        ("幅×高", "fixed"),
    ]
    for text, val in modes:
        mode_radio = customtkinter.CTkRadioButton(
            size_controls_frame,
            text=text,
            variable=app.mode_var,
            value=val,
            command=app._update_mode,
            font=app.font_default,
            fg_color=colors["primary"],
            hover_color=colors["hover"],
            border_color=colors["border_medium"],
            text_color=colors["text_primary"],
        )
        mode_radio.pack(side="left", padx=(0, 6))
        app.mode_radio_buttons.append(mode_radio)

    setup_entry_widgets(app, size_controls_frame, colors=colors)

    action_controls_frame = customtkinter.CTkFrame(top_row_secondary, fg_color="transparent")
    action_controls_frame.pack(side="right")
    setup_action_buttons(app, action_controls_frame, colors=colors)
    app._setup_settings_layers()
    app._refresh_topbar_density()
    app._setup_main_layout()
