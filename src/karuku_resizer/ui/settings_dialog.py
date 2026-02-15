"""Settings dialog helpers for ResizeApp."""

from __future__ import annotations

from pathlib import Path
from tkinter import filedialog, messagebox
from typing import Any, Dict, Mapping, Sequence, Tuple

import customtkinter

from karuku_resizer.gui_settings_store import default_gui_settings
from karuku_resizer.image_save_pipeline import normalize_quality

ColorMap = Dict[str, Tuple[str, str]]


def open_settings_dialog(
    app: Any,
    *,
    colors: ColorMap,
    ui_mode_id_to_label: Mapping[str, str],
    ui_mode_label_to_id: Mapping[str, str],
    appearance_id_to_label: Mapping[str, str],
    appearance_label_to_id: Mapping[str, str],
    format_id_to_label: Mapping[str, str],
    pro_input_mode_id_to_label: Mapping[str, str],
    pro_input_mode_label_to_id: Mapping[str, str],
    preset_none_label: str,
    quality_values: Sequence[str],
) -> None:
    if app._settings_dialog is not None and app._settings_dialog.winfo_exists():
        app._settings_dialog.focus_set()
        return

    dialog = customtkinter.CTkToplevel(app)
    app._settings_dialog = dialog
    dialog.title("設定")
    dialog.geometry("640x470")
    dialog.resizable(False, False)
    dialog.transient(app)
    dialog.grab_set()
    dialog.configure(fg_color=colors["bg_primary"])
    dialog.grid_columnconfigure(1, weight=1)

    ui_mode_var = customtkinter.StringVar(value=app.ui_mode_var.get())
    appearance_var = customtkinter.StringVar(value=app.appearance_mode_var.get())
    quality_var = customtkinter.StringVar(value=app.quality_var.get())
    output_format_var = customtkinter.StringVar(value=app.output_format_var.get())
    default_preset_var = customtkinter.StringVar(
        value=app._preset_label_for_id(
            str(app.settings.get("default_preset_id", "")).strip(),
            preset_none_label,
        )
    )
    pro_input_var = customtkinter.StringVar(
        value=pro_input_mode_id_to_label.get(
            app._normalized_pro_input_mode(str(app.settings.get("pro_input_mode", "recursive"))),
            "フォルダ再帰",
        )
    )
    show_tooltips_var = customtkinter.BooleanVar(
        value=app._to_bool(app.settings.get("show_tooltips", True))
    )
    default_output_dir_var = customtkinter.StringVar(value=str(app.settings.get("default_output_dir", "")))

    def _close_dialog() -> None:
        if dialog.winfo_exists():
            dialog.grab_release()
            dialog.destroy()
        app._settings_dialog = None

    def _browse_default_output_dir() -> None:
        initial_dir = (
            default_output_dir_var.get().strip()
            or str(app.settings.get("last_output_dir", ""))
            or str(Path.home())
        )
        selected_dir = filedialog.askdirectory(
            title="既定の保存先フォルダを選択",
            initialdir=initial_dir,
        )
        if selected_dir:
            default_output_dir_var.set(selected_dir)

    def _reset_dialog_values() -> None:
        if not messagebox.askyesno(
            "設定初期化の確認",
            "設定をデフォルト値に戻しますか？\n（保存するまでは反映されません）",
            parent=dialog,
        ):
            return
        defaults = default_gui_settings()
        ui_mode_var.set(ui_mode_id_to_label.get(defaults["ui_mode"], "簡易"))
        appearance_var.set(appearance_id_to_label.get(defaults["appearance_mode"], "システム"))
        quality_var.set(str(defaults["quality"]))
        output_format_var.set(format_id_to_label.get(defaults["output_format"], "自動"))
        pro_input_var.set(pro_input_mode_id_to_label.get(defaults["pro_input_mode"], "フォルダ再帰"))
        show_tooltips_var.set(app._to_bool(defaults.get("show_tooltips", True)))
        default_output_dir_var.set(str(defaults.get("default_output_dir", "")))
        default_preset_var.set(preset_none_label)

    def _save_dialog_values() -> None:
        try:
            quality_value = normalize_quality(int(quality_var.get()))
        except (TypeError, ValueError):
            messagebox.showwarning("入力エラー", "品質は数値で指定してください。", parent=dialog)
            return

        ui_mode_label = ui_mode_var.get()
        if ui_mode_label not in ui_mode_label_to_id:
            ui_mode_label = "簡易"

        appearance_label = appearance_var.get()
        if appearance_label not in appearance_label_to_id:
            appearance_label = "システム"

        format_label = output_format_var.get()
        available_formats = app._build_output_format_labels()
        if format_label not in available_formats:
            format_label = "自動"

        pro_input_mode = pro_input_mode_label_to_id.get(pro_input_var.get(), "recursive")
        default_output_dir = default_output_dir_var.get().strip()
        if default_output_dir:
            default_output_dir = str(Path(default_output_dir).expanduser())

        selected_default_label = default_preset_var.get().strip()
        if selected_default_label == preset_none_label:
            default_preset_id = ""
        else:
            default_preset_id = app._preset_name_to_id.get(selected_default_label, "")

        app.ui_mode_var.set(ui_mode_label)
        app.appearance_mode_var.set(appearance_label)
        app.quality_var.set(str(quality_value))
        app.output_format_var.set(format_label)
        app.settings["pro_input_mode"] = pro_input_mode
        app.settings["default_output_dir"] = default_output_dir
        app.settings["default_preset_id"] = default_preset_id
        app.settings["show_tooltips"] = bool(show_tooltips_var.get())
        if not app.settings["show_tooltips"]:
            app._tooltip_manager.hide()

        app._apply_ui_mode()
        app._apply_user_appearance_mode(app._appearance_mode_id(), redraw=True)
        app._on_output_format_changed(app.output_format_var.get())
        app._on_quality_changed(app.quality_var.get())
        app._update_settings_summary()
        app._save_current_settings()
        app.status_var.set("設定を保存しました。")

        _close_dialog()

    row = 0

    customtkinter.CTkLabel(
        dialog,
        text="UIモード",
        font=app.font_default,
        text_color=colors["text_secondary"],
    ).grid(row=row, column=0, padx=(20, 10), pady=(18, 8), sticky="w")
    ui_mode_menu = customtkinter.CTkOptionMenu(
        dialog,
        values=list(ui_mode_label_to_id.keys()),
        variable=ui_mode_var,
        fg_color=colors["bg_tertiary"],
        button_color=colors["primary"],
        button_hover_color=colors["hover"],
        text_color=colors["text_primary"],
        dropdown_fg_color=colors["bg_secondary"],
        dropdown_text_color=colors["text_primary"],
    )
    ui_mode_menu.grid(row=row, column=1, padx=(0, 20), pady=(18, 8), sticky="ew")
    app._register_tooltip(ui_mode_menu, "簡易/プロモードを選択します。")

    row += 1
    customtkinter.CTkLabel(
        dialog,
        text="テーマ",
        font=app.font_default,
        text_color=colors["text_secondary"],
    ).grid(row=row, column=0, padx=(20, 10), pady=8, sticky="w")
    appearance_menu = customtkinter.CTkOptionMenu(
        dialog,
        values=list(appearance_label_to_id.keys()),
        variable=appearance_var,
        fg_color=colors["bg_tertiary"],
        button_color=colors["primary"],
        button_hover_color=colors["hover"],
        text_color=colors["text_primary"],
        dropdown_fg_color=colors["bg_secondary"],
        dropdown_text_color=colors["text_primary"],
    )
    appearance_menu.grid(row=row, column=1, padx=(0, 20), pady=8, sticky="ew")
    app._register_tooltip(appearance_menu, "外観テーマを選択します。")

    row += 1
    customtkinter.CTkLabel(
        dialog,
        text="ホバー説明",
        font=app.font_default,
        text_color=colors["text_secondary"],
    ).grid(row=row, column=0, padx=(20, 10), pady=8, sticky="w")
    show_tooltips_check = customtkinter.CTkCheckBox(
        dialog,
        text="有効にする",
        variable=show_tooltips_var,
        font=app.font_default,
        fg_color=colors["primary"],
        hover_color=colors["hover"],
        border_color=colors["border_medium"],
        text_color=colors["text_primary"],
    )
    show_tooltips_check.grid(row=row, column=1, padx=(0, 20), pady=8, sticky="w")
    app._register_tooltip(show_tooltips_check, "ホバー説明の表示を切り替えます。")

    row += 1
    customtkinter.CTkLabel(
        dialog,
        text="既定の出力形式",
        font=app.font_default,
        text_color=colors["text_secondary"],
    ).grid(row=row, column=0, padx=(20, 10), pady=8, sticky="w")
    output_format_menu = customtkinter.CTkOptionMenu(
        dialog,
        values=app._build_output_format_labels(),
        variable=output_format_var,
        fg_color=colors["bg_tertiary"],
        button_color=colors["primary"],
        button_hover_color=colors["hover"],
        text_color=colors["text_primary"],
        dropdown_fg_color=colors["bg_secondary"],
        dropdown_text_color=colors["text_primary"],
    )
    output_format_menu.grid(row=row, column=1, padx=(0, 20), pady=8, sticky="ew")
    app._register_tooltip(output_format_menu, "起動時の既定出力形式を選択します。")

    row += 1
    customtkinter.CTkLabel(
        dialog,
        text="既定の品質",
        font=app.font_default,
        text_color=colors["text_secondary"],
    ).grid(row=row, column=0, padx=(20, 10), pady=8, sticky="w")
    quality_menu = customtkinter.CTkOptionMenu(
        dialog,
        values=list(quality_values),
        variable=quality_var,
        fg_color=colors["bg_tertiary"],
        button_color=colors["primary"],
        button_hover_color=colors["hover"],
        text_color=colors["text_primary"],
        dropdown_fg_color=colors["bg_secondary"],
        dropdown_text_color=colors["text_primary"],
    )
    quality_menu.grid(row=row, column=1, padx=(0, 20), pady=8, sticky="ew")
    app._register_tooltip(quality_menu, "起動時の既定品質を選択します。")

    row += 1
    customtkinter.CTkLabel(
        dialog,
        text="既定プリセット",
        font=app.font_default,
        text_color=colors["text_secondary"],
    ).grid(row=row, column=0, padx=(20, 10), pady=8, sticky="w")
    default_preset_menu = customtkinter.CTkOptionMenu(
        dialog,
        values=app._preset_labels_with_none(),
        variable=default_preset_var,
        fg_color=colors["bg_tertiary"],
        button_color=colors["primary"],
        button_hover_color=colors["hover"],
        text_color=colors["text_primary"],
        dropdown_fg_color=colors["bg_secondary"],
        dropdown_text_color=colors["text_primary"],
    )
    default_preset_menu.grid(row=row, column=1, padx=(0, 20), pady=8, sticky="ew")
    app._register_tooltip(default_preset_menu, "起動時に使うプリセットを選択します。")

    row += 1
    customtkinter.CTkLabel(
        dialog,
        text="プロモード入力方式",
        font=app.font_default,
        text_color=colors["text_secondary"],
    ).grid(row=row, column=0, padx=(20, 10), pady=8, sticky="w")
    pro_input_menu = customtkinter.CTkOptionMenu(
        dialog,
        values=list(pro_input_mode_label_to_id.keys()),
        variable=pro_input_var,
        fg_color=colors["bg_tertiary"],
        button_color=colors["primary"],
        button_hover_color=colors["hover"],
        text_color=colors["text_primary"],
        dropdown_fg_color=colors["bg_secondary"],
        dropdown_text_color=colors["text_primary"],
    )
    pro_input_menu.grid(row=row, column=1, padx=(0, 20), pady=8, sticky="ew")
    app._register_tooltip(pro_input_menu, "プロモードの既定入力方法を選択します。")

    row += 1
    customtkinter.CTkLabel(
        dialog,
        text="既定の保存先フォルダ",
        font=app.font_default,
        text_color=colors["text_secondary"],
    ).grid(row=row, column=0, padx=(20, 10), pady=8, sticky="w")
    default_output_frame = customtkinter.CTkFrame(dialog, fg_color="transparent")
    default_output_frame.grid(row=row, column=1, padx=(0, 20), pady=8, sticky="ew")
    default_output_frame.grid_columnconfigure(0, weight=1)
    default_output_entry = customtkinter.CTkEntry(
        default_output_frame,
        textvariable=default_output_dir_var,
        fg_color=colors["input_bg"],
        border_color=colors["border_light"],
        text_color=colors["text_primary"],
    )
    default_output_entry.grid(row=0, column=0, sticky="ew")
    app._register_tooltip(default_output_entry, "既定の保存先フォルダを設定します。")
    browse_button = customtkinter.CTkButton(
        default_output_frame,
        text="参照",
        width=70,
        command=_browse_default_output_dir,
        font=app.font_small,
    )
    app._style_secondary_button(browse_button)
    browse_button.grid(row=0, column=1, padx=(8, 0))
    app._register_tooltip(browse_button, "フォルダ選択を開きます。")

    button_row = row + 1
    button_frame = customtkinter.CTkFrame(dialog, fg_color="transparent")
    button_frame.grid(row=button_row, column=0, columnspan=2, padx=20, pady=(18, 16), sticky="e")

    reset_button = customtkinter.CTkButton(
        button_frame,
        text="初期化",
        width=90,
        command=_reset_dialog_values,
        font=app.font_small,
    )
    app._style_secondary_button(reset_button)
    reset_button.pack(side="left", padx=(0, 8))
    app._register_tooltip(reset_button, "設定値を初期状態へ戻します。")

    cancel_button = customtkinter.CTkButton(
        button_frame,
        text="キャンセル",
        width=90,
        command=_close_dialog,
        font=app.font_small,
    )
    app._style_secondary_button(cancel_button)
    cancel_button.pack(side="left", padx=(0, 8))
    app._register_tooltip(cancel_button, "変更を保存せず閉じます。")

    save_button = customtkinter.CTkButton(
        button_frame,
        text="保存",
        width=90,
        command=_save_dialog_values,
        font=app.font_small,
    )
    app._style_primary_button(save_button)
    save_button.pack(side="left")
    app._register_tooltip(save_button, "設定を保存して反映します。")

    dialog.protocol("WM_DELETE_WINDOW", _close_dialog)
    dialog.focus_set()
