"""Preset manager dialog helpers for ResizeApp."""

from __future__ import annotations

from datetime import datetime
from tkinter import messagebox
from typing import Any, Dict, List, Mapping, Optional, Tuple

import customtkinter

from karuku_resizer.processing_preset_store import ProcessingPreset, merge_processing_values

ColorMap = Dict[str, Tuple[str, str]]


def open_preset_manager_dialog(
    app: Any,
    *,
    colors: ColorMap,
    format_id_to_label: Mapping[str, str],
    exif_id_to_label: Mapping[str, str],
    preset_none_label: str,
) -> None:
    if app._preset_dialog is not None and app._preset_dialog.winfo_exists():
        app._preset_dialog.focus_set()
        return

    dialog = customtkinter.CTkToplevel(app)
    app._preset_dialog = dialog
    dialog.title("プリセット管理")
    dialog.geometry("700x360")
    dialog.resizable(False, False)
    dialog.transient(app)
    dialog.grab_set()
    dialog.configure(fg_color=colors["bg_primary"])
    dialog.grid_columnconfigure(1, weight=1)

    selected_label_var = customtkinter.StringVar(value=app.preset_var.get())
    name_var = customtkinter.StringVar(value="")
    description_var = customtkinter.StringVar(value="")
    info_var = customtkinter.StringVar(value="")
    default_status_var = customtkinter.StringVar(value="")

    def _close_dialog() -> None:
        if dialog.winfo_exists():
            dialog.grab_release()
            dialog.destroy()
        app._preset_dialog = None

    def _current_preset_id() -> str:
        return app._preset_name_to_id.get(selected_label_var.get(), "")

    def _current_preset() -> Optional[ProcessingPreset]:
        return app._get_preset_by_id(_current_preset_id())

    def _refresh_dialog_menu(selected_id: Optional[str] = None) -> None:
        labels = list(app._preset_name_to_id.keys()) or [preset_none_label]
        preset_option_menu.configure(values=labels)
        if selected_id:
            selected_label_var.set(app._preset_label_for_id(selected_id, labels[0]))
        elif selected_label_var.get() not in labels:
            selected_label_var.set(labels[0])

    def _build_preset_info_text(preset: ProcessingPreset) -> str:
        values = merge_processing_values(preset.values)
        mode = str(values.get("mode", "ratio"))
        if mode == "ratio":
            size_text = f"比率 {values.get('ratio_value', '100')}%"
        elif mode == "width":
            size_text = f"幅 {values.get('width_value', '')}px"
        elif mode == "height":
            size_text = f"高さ {values.get('height_value', '')}px"
        else:
            size_text = f"固定 {values.get('width_value', '')}x{values.get('height_value', '')}px"
        format_id = str(values.get("output_format", "auto")).lower()
        format_label = format_id_to_label.get(format_id, "自動")
        exif_mode_label = exif_id_to_label.get(str(values.get("exif_mode", "keep")), "保持")
        preset_kind = "組み込み" if preset.is_builtin else "ユーザー"
        updated_at = preset.updated_at or "-"
        return (
            f"種別: {preset_kind} / ID: {preset.preset_id}\n"
            f"サイズ: {size_text} / 形式: {format_label} / 品質: {values.get('quality', '85')}\n"
            f"EXIF: {exif_mode_label} / GPS削除: {'ON' if app._to_bool(values.get('remove_gps', False)) else 'OFF'} / "
            f"ドライラン: {'ON' if app._to_bool(values.get('dry_run', False)) else 'OFF'}\n"
            f"更新日時: {updated_at}"
        )

    def _refresh_dialog_fields(*_args: object) -> None:
        preset = _current_preset()
        default_id = str(app.settings.get("default_preset_id", "")).strip()
        if preset is None:
            name_var.set("")
            description_var.set("")
            info_var.set("プリセットを選択してください。")
            default_status_var.set("既定プリセット: 未設定")
            name_entry.configure(state="disabled")
            description_entry.configure(state="disabled")
            update_button.configure(state="disabled")
            delete_button.configure(state="disabled")
            apply_button.configure(state="disabled")
            set_default_button.configure(state="disabled")
            return

        name_var.set(preset.name)
        description_var.set(preset.description)
        info_var.set(_build_preset_info_text(preset))
        default_label = app._preset_label_for_id(default_id, preset_none_label) if default_id else preset_none_label
        default_status_var.set(f"既定プリセット: {default_label}")

        is_user = not preset.is_builtin
        field_state = "normal" if is_user else "disabled"
        name_entry.configure(state=field_state)
        description_entry.configure(state=field_state)
        update_button.configure(state="normal" if is_user else "disabled")
        delete_button.configure(state="normal" if is_user else "disabled")
        apply_button.configure(state="normal")
        set_default_button.configure(state="normal")

    def _apply_dialog_preset() -> None:
        preset_id = _current_preset_id()
        if not preset_id:
            return
        if app._apply_preset_by_id(preset_id, announce=True, persist=True):
            app._refresh_preset_menu(selected_preset_id=preset_id)
            selected_label_var.set(app._preset_label_for_id(preset_id, selected_label_var.get()))
            _refresh_dialog_fields()

    def _set_default_preset() -> None:
        preset_id = _current_preset_id()
        if not preset_id:
            return
        app.settings["default_preset_id"] = preset_id
        app._save_current_settings()
        default_status_var.set(f"既定プリセット: {app._preset_label_for_id(preset_id, preset_none_label)}")
        app.status_var.set("既定プリセットを更新しました。")

    def _clear_default_preset() -> None:
        app.settings["default_preset_id"] = ""
        app._save_current_settings()
        default_status_var.set(f"既定プリセット: {preset_none_label}")
        app.status_var.set("既定プリセットを解除しました。")

    def _update_user_preset_from_current() -> None:
        preset = _current_preset()
        if preset is None or preset.is_builtin:
            messagebox.showwarning("プリセット更新", "ユーザープリセットを選択してください。", parent=dialog)
            return

        updated_name = name_var.get().strip()
        if not updated_name:
            messagebox.showwarning("プリセット更新", "プリセット名を入力してください。", parent=dialog)
            return

        for existing in app._user_presets():
            if existing.preset_id != preset.preset_id and existing.name == updated_name:
                messagebox.showwarning(
                    "プリセット更新",
                    f"同名のユーザープリセット「{updated_name}」が存在します。",
                    parent=dialog,
                )
                return

        updated_desc = description_var.get().strip()
        updated_values = app._capture_current_processing_values(
            require_valid_exif_datetime=True,
            warning_parent=dialog,
        )
        if updated_values is None:
            return

        user_presets: List[ProcessingPreset] = []
        for existing in app._user_presets():
            if existing.preset_id == preset.preset_id:
                existing.name = updated_name
                existing.description = updated_desc
                existing.values = merge_processing_values(updated_values)
                existing.updated_at = datetime.now().isoformat(timespec="seconds")
            user_presets.append(existing)

        app._persist_user_presets(user_presets, selected_preset_id=preset.preset_id)
        app._set_selected_preset_label_by_id(preset.preset_id)
        _refresh_dialog_menu(selected_id=preset.preset_id)
        _refresh_dialog_fields()
        app._save_current_settings()
        app.status_var.set(f"プリセット更新: {updated_name}")

    def _delete_user_preset() -> None:
        preset = _current_preset()
        if preset is None or preset.is_builtin:
            messagebox.showwarning("プリセット削除", "削除できるのはユーザープリセットのみです。", parent=dialog)
            return

        if not messagebox.askyesno(
            "プリセット削除",
            f"「{preset.name}」を削除しますか？",
            parent=dialog,
        ):
            return

        remaining = [existing for existing in app._user_presets() if existing.preset_id != preset.preset_id]
        deleted_id = preset.preset_id
        app._persist_user_presets(remaining)
        if str(app.settings.get("default_preset_id", "")).strip() == deleted_id:
            app.settings["default_preset_id"] = ""
            app._save_current_settings()
        fallback_id = app._selected_preset_id()
        _refresh_dialog_menu(selected_id=fallback_id)
        _refresh_dialog_fields()
        app.status_var.set(f"プリセット削除: {preset.name}")

    row = 0
    customtkinter.CTkLabel(
        dialog,
        text="対象プリセット",
        font=app.font_default,
        text_color=colors["text_secondary"],
    ).grid(row=row, column=0, padx=(20, 10), pady=(18, 8), sticky="w")
    preset_option_menu = customtkinter.CTkOptionMenu(
        dialog,
        variable=selected_label_var,
        values=list(app._preset_name_to_id.keys()) or [preset_none_label],
        fg_color=colors["bg_tertiary"],
        button_color=colors["primary"],
        button_hover_color=colors["hover"],
        text_color=colors["text_primary"],
        dropdown_fg_color=colors["bg_secondary"],
        dropdown_text_color=colors["text_primary"],
    )
    preset_option_menu.grid(row=row, column=1, padx=(0, 20), pady=(18, 8), sticky="ew")

    row += 1
    customtkinter.CTkLabel(
        dialog,
        text="名称（ユーザーのみ変更可）",
        font=app.font_default,
        text_color=colors["text_secondary"],
    ).grid(row=row, column=0, padx=(20, 10), pady=8, sticky="w")
    name_entry = customtkinter.CTkEntry(
        dialog,
        textvariable=name_var,
        fg_color=colors["input_bg"],
        border_color=colors["border_light"],
        text_color=colors["text_primary"],
    )
    name_entry.grid(row=row, column=1, padx=(0, 20), pady=8, sticky="ew")

    row += 1
    customtkinter.CTkLabel(
        dialog,
        text="説明（任意）",
        font=app.font_default,
        text_color=colors["text_secondary"],
    ).grid(row=row, column=0, padx=(20, 10), pady=8, sticky="w")
    description_entry = customtkinter.CTkEntry(
        dialog,
        textvariable=description_var,
        fg_color=colors["input_bg"],
        border_color=colors["border_light"],
        text_color=colors["text_primary"],
    )
    description_entry.grid(row=row, column=1, padx=(0, 20), pady=8, sticky="ew")

    row += 1
    customtkinter.CTkLabel(
        dialog,
        textvariable=default_status_var,
        font=app.font_small,
        text_color=colors["text_tertiary"],
        anchor="w",
        justify="left",
    ).grid(row=row, column=0, columnspan=2, padx=20, pady=(2, 6), sticky="ew")

    row += 1
    customtkinter.CTkLabel(
        dialog,
        textvariable=info_var,
        font=app.font_small,
        text_color=colors["text_tertiary"],
        anchor="w",
        justify="left",
    ).grid(row=row, column=0, columnspan=2, padx=20, pady=(0, 10), sticky="ew")

    row += 1
    action_frame = customtkinter.CTkFrame(dialog, fg_color="transparent")
    action_frame.grid(row=row, column=0, columnspan=2, padx=20, pady=(0, 16), sticky="e")

    apply_button = customtkinter.CTkButton(
        action_frame,
        text="適用",
        width=88,
        command=_apply_dialog_preset,
        font=app.font_small,
    )
    app._style_secondary_button(apply_button)
    apply_button.pack(side="left", padx=(0, 8))

    set_default_button = customtkinter.CTkButton(
        action_frame,
        text="既定に設定",
        width=108,
        command=_set_default_preset,
        font=app.font_small,
    )
    app._style_secondary_button(set_default_button)
    set_default_button.pack(side="left", padx=(0, 8))

    clear_default_button = customtkinter.CTkButton(
        action_frame,
        text="既定解除",
        width=92,
        command=_clear_default_preset,
        font=app.font_small,
    )
    app._style_secondary_button(clear_default_button)
    clear_default_button.pack(side="left", padx=(0, 8))

    update_button = customtkinter.CTkButton(
        action_frame,
        text="現在設定で更新",
        width=132,
        command=_update_user_preset_from_current,
        font=app.font_small,
    )
    app._style_primary_button(update_button)
    update_button.pack(side="left", padx=(0, 8))

    delete_button = customtkinter.CTkButton(
        action_frame,
        text="削除",
        width=82,
        command=_delete_user_preset,
        font=app.font_small,
    )
    app._style_secondary_button(delete_button)
    delete_button.pack(side="left", padx=(0, 8))

    close_button = customtkinter.CTkButton(
        action_frame,
        text="閉じる",
        width=82,
        command=_close_dialog,
        font=app.font_small,
    )
    app._style_secondary_button(close_button)
    close_button.pack(side="left")

    selected_label_var.trace_add("write", _refresh_dialog_fields)
    _refresh_dialog_menu()
    _refresh_dialog_fields()

    dialog.protocol("WM_DELETE_WINDOW", _close_dialog)
    dialog.focus_set()
