"""Settings dialog UI builder for the main GUI."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Mapping, Sequence

import customtkinter
from tkinter import filedialog, messagebox

from karuku_resizer.gui_settings_store import default_gui_settings
from karuku_resizer.image_save_pipeline import normalize_quality


@dataclass(frozen=True)
class SettingsDialogState:
    """Current values to initialize the dialog."""

    ui_mode_label: str
    appearance_label: str
    ui_scale_mode: str
    zoom_preference: str
    quality: str
    output_format_label: str
    default_output_dir: str
    default_preset_label: str
    pro_input_mode: str
    show_tooltips: bool


@dataclass(frozen=True)
class SettingsDialogMappings:
    """Label/id mapping configuration used for validation and defaults."""

    ui_mode_label_to_id: Mapping[str, str]
    appearance_label_to_id: Mapping[str, str]
    ui_scale_label_to_id: Mapping[str, str]
    pro_input_label_to_id: Mapping[str, str]
    ui_mode_id_to_label: Mapping[str, str]
    appearance_id_to_label: Mapping[str, str]
    ui_scale_id_to_label: Mapping[str, str]
    pro_input_id_to_label: Mapping[str, str]
    preset_name_to_id: Mapping[str, str]
    preset_labels_with_none: Callable[[], Sequence[str]]
    build_output_format_labels: Callable[[], Sequence[str]]
    output_format_id_to_label: Mapping[str, str]
    output_format_fallback_label: str
    zoom_preference_values: Sequence[str]
    quality_values: Sequence[str]
    pro_input_default_fallback_label: str
    preset_none_label: str
    ui_scale_factor: float
    settings_getter: Callable[[], Mapping[str, Any]]


@dataclass(frozen=True)
class SettingsDialogResult:
    """Validated values emitted when dialog values are saved."""

    ui_mode_label: str
    appearance_label: str
    ui_scale_label: str
    zoom_preference: str
    quality: str
    output_format_label: str
    pro_input_mode_id: str
    default_preset_id: str
    default_output_dir: str
    show_tooltips: bool


@dataclass(frozen=True)
class SettingsDialogCallbacks:
    """Dependency injection points for app-level behavior."""

    register_tooltip: Callable[[Any, str], None]
    style_primary_button: Callable[[Any], None]
    style_secondary_button: Callable[[Any], None]
    scale_px: Callable[[int], int]
    on_show_help: Callable[[], None]
    on_open_preset_manager: Callable[[], None]
    on_apply: Callable[[SettingsDialogResult], None]
    on_status_set: Callable[[str], None]
    on_dialog_closed: Callable[[], None]
    font_default: Any
    font_small: Any
    colors: Mapping[str, Any]


def _expand_output_dir(raw: str) -> str:
    stripped = str(raw).strip()
    if not stripped:
        return ""
    return str(Path(stripped).expanduser())


def _resolve_output_format_label(
    defaults: Mapping[str, Any],
    *,
    output_format_id_to_label: Mapping[str, str],
    output_format_fallback_label: str,
    available_output_formats: Sequence[str],
) -> str:
    """Return the configured default output-format label, with deterministic fallback."""

    default_output_label = output_format_id_to_label.get(
        str(defaults.get("output_format", "auto")),
        output_format_fallback_label,
    )
    if default_output_label in available_output_formats:
        return default_output_label
    return output_format_fallback_label


def open_settings_dialog(
    parent: customtkinter.CTk,
    *,
    state: SettingsDialogState,
    mappings: SettingsDialogMappings,
    callbacks: SettingsDialogCallbacks,
) -> customtkinter.CTkToplevel:
    """Open settings dialog and return dialog instance."""

    dialog = customtkinter.CTkToplevel(parent)
    dialog.title("設定")
    base_width, base_height = 680, 565
    width = max(base_width, round(base_width * mappings.ui_scale_factor))
    height = max(base_height, round(base_height * mappings.ui_scale_factor))
    dialog.geometry(f"{width}x{height}")
    dialog.minsize(width, height)
    dialog.resizable(True, True)
    dialog.transient(parent)
    dialog.grab_set()
    dialog.configure(fg_color=callbacks.colors["bg_primary"])
    dialog.grid_rowconfigure(0, weight=1)
    dialog.grid_rowconfigure(1, weight=0)
    dialog.grid_columnconfigure(0, weight=1)

    settings_content = customtkinter.CTkScrollableFrame(dialog, fg_color="transparent")
    settings_content.grid(
        row=0,
        column=0,
        padx=callbacks.scale_px(8),
        pady=(0, 0),
        sticky="nsew",
    )
    settings_content.grid_columnconfigure(0, weight=0)
    settings_content.grid_columnconfigure(1, weight=1)

    ui_mode_var = customtkinter.StringVar(value=state.ui_mode_label)
    appearance_var = customtkinter.StringVar(value=state.appearance_label)
    ui_scale_var = customtkinter.StringVar(
        value=mappings.ui_scale_id_to_label.get(
            state.ui_scale_mode,
            mappings.ui_scale_id_to_label.get("normal", "通常"),
        )
    )
    zoom_pref_var = customtkinter.StringVar(value=state.zoom_preference)
    quality_var = customtkinter.StringVar(value=state.quality)
    output_format_var = customtkinter.StringVar(value=state.output_format_label)
    default_preset_var = customtkinter.StringVar(value=state.default_preset_label)
    pro_input_var = customtkinter.StringVar(
        value=mappings.pro_input_id_to_label.get(
            state.pro_input_mode,
            mappings.pro_input_default_fallback_label,
        )
    )
    show_tooltips_var = customtkinter.BooleanVar(value=state.show_tooltips)
    default_output_dir_var = customtkinter.StringVar(value=state.default_output_dir)

    def _scale_px(value: int) -> int:
        return callbacks.scale_px(value)

    def _scale_pad(value: Any) -> Any:
        if isinstance(value, (list, tuple)):
            return tuple(_scale_px(int(v)) for v in value)
        return _scale_px(int(value))

    def _close_dialog() -> None:
        if dialog.winfo_exists():
            dialog.grab_release()
            dialog.destroy()
        callbacks.on_dialog_closed()

    def _browse_default_output_dir() -> None:
        settings = mappings.settings_getter()
        initial_dir = (
            default_output_dir_var.get().strip()
            or str(settings.get("last_output_dir", ""))
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
        ui_mode_var.set(mappings.ui_mode_id_to_label.get(defaults["ui_mode"], "オフ"))
        appearance_var.set(
            mappings.appearance_id_to_label.get(defaults["appearance_mode"], "OSに従う")
        )
        ui_scale_var.set(mappings.ui_scale_id_to_label.get(defaults["ui_scale_mode"], "通常"))
        zoom_pref_var.set(str(defaults.get("zoom_preference", "画面に合わせる")))
        quality_var.set(str(normalize_quality(int(defaults["quality"]))))
        available_output_formats = list(mappings.build_output_format_labels())
        output_format_var.set(
            _resolve_output_format_label(
                defaults,
                output_format_id_to_label=mappings.output_format_id_to_label,
                output_format_fallback_label=mappings.output_format_fallback_label,
                available_output_formats=available_output_formats,
            )
        )
        pro_input_var.set(
            mappings.pro_input_id_to_label.get(
                str(defaults.get("pro_input_mode", "recursive")),
                mappings.pro_input_default_fallback_label,
            )
        )
        show_tooltips_var.set(bool(defaults.get("show_tooltips", True)))
        default_output_dir_var.set(str(defaults.get("default_output_dir", "")))
        default_preset_var.set(mappings.preset_none_label)

    def _save_dialog_values() -> None:
        try:
            quality_value = normalize_quality(int(quality_var.get()))
        except (TypeError, ValueError):
            messagebox.showwarning("入力エラー", "品質は数値で指定してください。", parent=dialog)
            return

        ui_mode_label = ui_mode_var.get()
        if ui_mode_label not in mappings.ui_mode_label_to_id:
            ui_mode_label = mappings.ui_mode_id_to_label.get("simple", "オフ")

        appearance_label = appearance_var.get()
        if appearance_label not in mappings.appearance_label_to_id:
            appearance_label = mappings.appearance_id_to_label.get("system", "OSに従う")

        ui_scale_label = ui_scale_var.get()
        if ui_scale_label not in mappings.ui_scale_label_to_id:
            ui_scale_label = mappings.ui_scale_id_to_label.get("normal", "通常")

        zoom_pref_label = zoom_pref_var.get()
        if zoom_pref_label not in mappings.zoom_preference_values:
            zoom_pref_label = "画面に合わせる"

        format_label = output_format_var.get()
        available_output_formats = list(mappings.build_output_format_labels())
        if format_label not in available_output_formats:
            format_label = (
                _resolve_output_format_label(
                    mappings.settings_getter(),
                    output_format_id_to_label=mappings.output_format_id_to_label,
                    output_format_fallback_label=mappings.output_format_fallback_label,
                    available_output_formats=available_output_formats,
                )
            )

        pro_input_mode = mappings.pro_input_label_to_id.get(
            pro_input_var.get(),
            "recursive",
        )
        selected_default_label = default_preset_var.get().strip()
        if selected_default_label == mappings.preset_none_label:
            default_preset_id = ""
        else:
            default_preset_id = mappings.preset_name_to_id.get(selected_default_label, "")

        callbacks.on_apply(
            SettingsDialogResult(
                ui_mode_label=ui_mode_label,
                appearance_label=appearance_label,
                ui_scale_label=ui_scale_label,
                zoom_preference=zoom_pref_label,
                quality=str(quality_value),
                output_format_label=format_label,
                pro_input_mode_id=pro_input_mode,
                default_preset_id=default_preset_id,
                default_output_dir=_expand_output_dir(default_output_dir_var.get()),
                show_tooltips=bool(show_tooltips_var.get()),
            )
        )
        callbacks.on_status_set("設定を保存しました。")
        _close_dialog()

    row = 0

    customtkinter.CTkLabel(
        settings_content,
        text="Proモード",
        font=callbacks.font_default,
        text_color=callbacks.colors["text_secondary"],
    ).grid(row=row, column=0, padx=_scale_pad((20, 10)), pady=_scale_pad((18, 8)), sticky="w")
    ui_mode_menu = customtkinter.CTkOptionMenu(
        settings_content,
        values=list(mappings.ui_mode_label_to_id.keys()),
        variable=ui_mode_var,
        fg_color=callbacks.colors["bg_tertiary"],
        button_color=callbacks.colors["primary"],
        button_hover_color=callbacks.colors["hover"],
        text_color=callbacks.colors["text_primary"],
        dropdown_fg_color=callbacks.colors["bg_secondary"],
        dropdown_text_color=callbacks.colors["text_primary"],
    )
    ui_mode_menu.grid(row=row, column=1, padx=_scale_pad((0, 20)), pady=_scale_pad((18, 8)), sticky="ew")
    callbacks.register_tooltip(ui_mode_menu, "Pro向け機能のオン/オフを切り替えます。")

    row += 1
    customtkinter.CTkLabel(
        settings_content,
        text="カラーテーマ",
        font=callbacks.font_default,
        text_color=callbacks.colors["text_secondary"],
    ).grid(row=row, column=0, padx=_scale_pad((20, 10)), pady=_scale_px(8), sticky="w")
    appearance_menu = customtkinter.CTkOptionMenu(
        settings_content,
        values=list(mappings.appearance_label_to_id.keys()),
        variable=appearance_var,
        fg_color=callbacks.colors["bg_tertiary"],
        button_color=callbacks.colors["primary"],
        button_hover_color=callbacks.colors["hover"],
        text_color=callbacks.colors["text_primary"],
        dropdown_fg_color=callbacks.colors["bg_secondary"],
        dropdown_text_color=callbacks.colors["text_primary"],
    )
    appearance_menu.grid(row=row, column=1, padx=_scale_pad((0, 20)), pady=_scale_px(8), sticky="ew")
    callbacks.register_tooltip(appearance_menu, "OSに従う/ライト/ダークを選択します。")

    row += 1
    customtkinter.CTkLabel(
        settings_content,
        text="文字サイズ",
        font=callbacks.font_default,
        text_color=callbacks.colors["text_secondary"],
    ).grid(row=row, column=0, padx=_scale_pad((20, 10)), pady=_scale_px(8), sticky="w")
    ui_scale_menu = customtkinter.CTkOptionMenu(
        settings_content,
        values=list(mappings.ui_scale_label_to_id.keys()),
        variable=ui_scale_var,
        fg_color=callbacks.colors["bg_tertiary"],
        button_color=callbacks.colors["primary"],
        button_hover_color=callbacks.colors["hover"],
        text_color=callbacks.colors["text_primary"],
        dropdown_fg_color=callbacks.colors["bg_secondary"],
        dropdown_text_color=callbacks.colors["text_primary"],
    )
    ui_scale_menu.grid(row=row, column=1, padx=_scale_pad((0, 20)), pady=_scale_px(8), sticky="ew")
    callbacks.register_tooltip(ui_scale_menu, "通常 / 大きめ の文字サイズを切り替えます。")

    row += 1
    customtkinter.CTkLabel(
        settings_content,
        text="プレビュー拡大率",
        font=callbacks.font_default,
        text_color=callbacks.colors["text_secondary"],
    ).grid(row=row, column=0, padx=_scale_pad((20, 10)), pady=_scale_px(8), sticky="w")
    zoom_pref_menu = customtkinter.CTkOptionMenu(
        settings_content,
        values=list(mappings.zoom_preference_values),
        variable=zoom_pref_var,
        fg_color=callbacks.colors["bg_tertiary"],
        button_color=callbacks.colors["primary"],
        button_hover_color=callbacks.colors["hover"],
        text_color=callbacks.colors["text_primary"],
        dropdown_fg_color=callbacks.colors["bg_secondary"],
        dropdown_text_color=callbacks.colors["text_primary"],
    )
    zoom_pref_menu.grid(row=row, column=1, padx=_scale_pad((0, 20)), pady=_scale_px(8), sticky="ew")
    callbacks.register_tooltip(zoom_pref_menu, "プレビューの既定拡大率を設定します。")

    row += 1
    customtkinter.CTkLabel(
        settings_content,
        text="ヘルプ/管理",
        font=callbacks.font_default,
        text_color=callbacks.colors["text_secondary"],
    ).grid(row=row, column=0, padx=_scale_pad((20, 10)), pady=_scale_px(8), sticky="w")
    support_actions = customtkinter.CTkFrame(settings_content, fg_color="transparent")
    support_actions.grid(row=row, column=1, padx=_scale_pad((0, 20)), pady=_scale_px(8), sticky="w")
    help_in_settings_button = customtkinter.CTkButton(
        support_actions,
        text="使い方を開く",
        width=_scale_px(132),
        command=callbacks.on_show_help,
        font=callbacks.font_default,
    )
    callbacks.style_secondary_button(help_in_settings_button)
    help_in_settings_button.pack(side="left", padx=(0, _scale_px(8)))
    preset_manage_in_settings_button = customtkinter.CTkButton(
        support_actions,
        text="プリセット管理",
        width=_scale_px(132),
        command=callbacks.on_open_preset_manager,
        font=callbacks.font_default,
    )
    callbacks.style_secondary_button(preset_manage_in_settings_button)
    preset_manage_in_settings_button.pack(side="left")
    callbacks.register_tooltip(help_in_settings_button, "使い方ガイドを表示します。")
    callbacks.register_tooltip(
        preset_manage_in_settings_button,
        "プリセットの追加・編集・削除を行います。",
    )

    row += 1
    customtkinter.CTkLabel(
        settings_content,
        text="ホバー説明",
        font=callbacks.font_default,
        text_color=callbacks.colors["text_secondary"],
    ).grid(row=row, column=0, padx=_scale_pad((20, 10)), pady=_scale_px(8), sticky="w")
    show_tooltips_check = customtkinter.CTkCheckBox(
        settings_content,
        text="有効にする",
        variable=show_tooltips_var,
        font=callbacks.font_default,
        fg_color=callbacks.colors["primary"],
        hover_color=callbacks.colors["hover"],
        border_color=callbacks.colors["border_medium"],
        text_color=callbacks.colors["text_primary"],
    )
    show_tooltips_check.grid(row=row, column=1, padx=_scale_pad((0, 20)), pady=_scale_px(8), sticky="w")
    callbacks.register_tooltip(show_tooltips_check, "ホバー説明の表示を切り替えます。")

    row += 1
    customtkinter.CTkLabel(
        settings_content,
        text="既定の出力形式",
        font=callbacks.font_default,
        text_color=callbacks.colors["text_secondary"],
    ).grid(row=row, column=0, padx=_scale_pad((20, 10)), pady=_scale_px(8), sticky="w")
    output_format_menu = customtkinter.CTkOptionMenu(
        settings_content,
        values=list(mappings.build_output_format_labels()),
        variable=output_format_var,
        fg_color=callbacks.colors["bg_tertiary"],
        button_color=callbacks.colors["primary"],
        button_hover_color=callbacks.colors["hover"],
        text_color=callbacks.colors["text_primary"],
        dropdown_fg_color=callbacks.colors["bg_secondary"],
        dropdown_text_color=callbacks.colors["text_primary"],
    )
    output_format_menu.grid(row=row, column=1, padx=_scale_pad((0, 20)), pady=_scale_px(8), sticky="ew")
    callbacks.register_tooltip(output_format_menu, "起動時の既定出力形式を選択します。")

    row += 1
    customtkinter.CTkLabel(
        settings_content,
        text="既定の品質",
        font=callbacks.font_default,
        text_color=callbacks.colors["text_secondary"],
    ).grid(row=row, column=0, padx=_scale_pad((20, 10)), pady=_scale_px(8), sticky="w")
    quality_menu = customtkinter.CTkOptionMenu(
        settings_content,
        values=list(mappings.quality_values),
        variable=quality_var,
        fg_color=callbacks.colors["bg_tertiary"],
        button_color=callbacks.colors["primary"],
        button_hover_color=callbacks.colors["hover"],
        text_color=callbacks.colors["text_primary"],
        dropdown_fg_color=callbacks.colors["bg_secondary"],
        dropdown_text_color=callbacks.colors["text_primary"],
    )
    quality_menu.grid(row=row, column=1, padx=_scale_pad((0, 20)), pady=_scale_px(8), sticky="ew")
    callbacks.register_tooltip(quality_menu, "起動時の既定品質を選択します。")

    row += 1
    customtkinter.CTkLabel(
        settings_content,
        text="既定プリセット",
        font=callbacks.font_default,
        text_color=callbacks.colors["text_secondary"],
    ).grid(row=row, column=0, padx=_scale_pad((20, 10)), pady=_scale_px(8), sticky="w")
    default_preset_menu = customtkinter.CTkOptionMenu(
        settings_content,
        values=list(mappings.preset_labels_with_none()),
        variable=default_preset_var,
        fg_color=callbacks.colors["bg_tertiary"],
        button_color=callbacks.colors["primary"],
        button_hover_color=callbacks.colors["hover"],
        text_color=callbacks.colors["text_primary"],
        dropdown_fg_color=callbacks.colors["bg_secondary"],
        dropdown_text_color=callbacks.colors["text_primary"],
    )
    default_preset_menu.grid(row=row, column=1, padx=_scale_pad((0, 20)), pady=_scale_px(8), sticky="ew")
    callbacks.register_tooltip(default_preset_menu, "起動時に使うプリセットを選択します。")

    row += 1
    customtkinter.CTkLabel(
        settings_content,
        text="プロモード入力方式",
        font=callbacks.font_default,
        text_color=callbacks.colors["text_secondary"],
    ).grid(row=row, column=0, padx=_scale_pad((20, 10)), pady=_scale_px(8), sticky="w")
    pro_input_menu = customtkinter.CTkOptionMenu(
        settings_content,
        values=list(mappings.pro_input_label_to_id.keys()),
        variable=pro_input_var,
        fg_color=callbacks.colors["bg_tertiary"],
        button_color=callbacks.colors["primary"],
        button_hover_color=callbacks.colors["hover"],
        text_color=callbacks.colors["text_primary"],
        dropdown_fg_color=callbacks.colors["bg_secondary"],
        dropdown_text_color=callbacks.colors["text_primary"],
    )
    pro_input_menu.grid(row=row, column=1, padx=_scale_pad((0, 20)), pady=_scale_px(8), sticky="ew")
    callbacks.register_tooltip(pro_input_menu, "プロモードの既定入力方式を選択します。")

    row += 1
    customtkinter.CTkLabel(
        settings_content,
        text="既定の保存先フォルダ",
        font=callbacks.font_default,
        text_color=callbacks.colors["text_secondary"],
    ).grid(row=row, column=0, padx=_scale_pad((20, 10)), pady=_scale_px(8), sticky="w")
    default_output_frame = customtkinter.CTkFrame(settings_content, fg_color="transparent")
    default_output_frame.grid(row=row, column=1, padx=_scale_pad((0, 20)), pady=_scale_px(8), sticky="ew")
    default_output_frame.grid_columnconfigure(0, weight=1)
    default_output_entry = customtkinter.CTkEntry(
        default_output_frame,
        textvariable=default_output_dir_var,
        fg_color=callbacks.colors["input_bg"],
        border_color=callbacks.colors["border_light"],
        text_color=callbacks.colors["text_primary"],
    )
    default_output_entry.grid(row=0, column=0, sticky="ew")
    callbacks.register_tooltip(default_output_entry, "既定の保存先フォルダを設定します。")
    browse_button = customtkinter.CTkButton(
        default_output_frame,
        text="参照",
        width=_scale_px(70),
        command=_browse_default_output_dir,
        font=callbacks.font_small,
    )
    callbacks.style_secondary_button(browse_button)
    browse_button.grid(row=0, column=1, padx=_scale_pad((8, 0)))
    callbacks.register_tooltip(browse_button, "フォルダ選択を開きます。")

    button_frame = customtkinter.CTkFrame(dialog, fg_color="transparent")
    button_frame.grid(
        row=1,
        column=0,
        padx=_scale_px(20),
        pady=_scale_pad((18, 16)),
        sticky="e",
    )

    reset_button = customtkinter.CTkButton(
        button_frame,
        text="初期化",
        width=_scale_px(90),
        command=_reset_dialog_values,
        font=callbacks.font_small,
    )
    callbacks.style_secondary_button(reset_button)
    reset_button.pack(side="left", padx=_scale_pad((0, 8)))
    callbacks.register_tooltip(reset_button, "設定値を初期状態へ戻します。")

    cancel_button = customtkinter.CTkButton(
        button_frame,
        text="キャンセル",
        width=_scale_px(90),
        command=_close_dialog,
        font=callbacks.font_small,
    )
    callbacks.style_secondary_button(cancel_button)
    cancel_button.pack(side="left", padx=_scale_pad((0, 8)))
    callbacks.register_tooltip(cancel_button, "変更を保存せず閉じます。")

    save_button = customtkinter.CTkButton(
        button_frame,
        text="保存",
        width=_scale_px(90),
        command=_save_dialog_values,
        font=callbacks.font_small,
    )
    callbacks.style_primary_button(save_button)
    save_button.pack(side="left")
    callbacks.register_tooltip(save_button, "設定を保存して反映します。")

    dialog.protocol("WM_DELETE_WINDOW", _close_dialog)
    dialog.focus_set()

    return dialog
