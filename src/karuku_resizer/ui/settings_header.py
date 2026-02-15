"""Settings header / recent settings helpers for ResizeApp."""

from __future__ import annotations

import json
from datetime import datetime
from tkinter import messagebox
from typing import Any, Callable, Dict, List, Mapping, Tuple

import customtkinter

ColorMap = Dict[str, Tuple[str, str]]


def setup_settings_layers(
    app: Any,
    *,
    colors: ColorMap,
    ui_mode_labels: List[str],
    appearance_labels: List[str],
) -> None:
    app.settings_header_frame = customtkinter.CTkFrame(app)
    app._style_card_frame(app.settings_header_frame, corner_radius=12)
    app.settings_header_frame.pack(side="top", fill="x", padx=12, pady=(0, 6))

    app.settings_summary_var = customtkinter.StringVar(value="")
    app.settings_summary_label = customtkinter.CTkLabel(
        app.settings_header_frame,
        textvariable=app.settings_summary_var,
        anchor="w",
        font=app.font_small,
        text_color=colors["text_secondary"],
    )
    app.settings_summary_label.pack(side="left", fill="x", expand=True, padx=(10, 0), pady=8)

    app.ui_mode_var = customtkinter.StringVar(value="簡易")
    app.ui_mode_segment = customtkinter.CTkSegmentedButton(
        app.settings_header_frame,
        values=ui_mode_labels,
        variable=app.ui_mode_var,
        command=app._on_ui_mode_changed,
        width=120,
        font=app.font_small,
        selected_color=colors["primary"],
        selected_hover_color=colors["hover"],
        unselected_color=colors["bg_tertiary"],
        unselected_hover_color=colors["accent_soft"],
        text_color=colors["text_primary"],
    )
    app.ui_mode_segment.pack(side="right", padx=(0, 8), pady=8)

    app.appearance_mode_var = customtkinter.StringVar(value="システム")
    app.appearance_mode_segment = customtkinter.CTkSegmentedButton(
        app.settings_header_frame,
        values=appearance_labels,
        variable=app.appearance_mode_var,
        command=app._on_appearance_mode_changed,
        width=180,
        font=app.font_small,
        selected_color=colors["primary"],
        selected_hover_color=colors["hover"],
        unselected_color=colors["bg_tertiary"],
        unselected_hover_color=colors["accent_soft"],
        text_color=colors["text_primary"],
    )
    app.appearance_mode_segment.pack(side="right", padx=(0, 8), pady=8)

    app.details_toggle_button = customtkinter.CTkButton(
        app.settings_header_frame,
        text="詳細設定を表示",
        width=140,
        command=app._toggle_details_panel,
        font=app.font_small,
    )
    app._style_tertiary_button(app.details_toggle_button)
    app.details_toggle_button.pack(side="right", padx=(0, 6), pady=8)

    app.recent_settings_row = customtkinter.CTkFrame(app.settings_header_frame, fg_color="transparent")
    app.recent_settings_row.pack(side="bottom", fill="x", padx=10, pady=(0, 8))
    app.recent_settings_title_label = customtkinter.CTkLabel(
        app.recent_settings_row,
        text="最近使った設定",
        font=app.font_small,
        text_color=colors["text_secondary"],
    )
    app.recent_settings_title_label.pack(side="left", padx=(0, 8))
    app.recent_settings_buttons_frame = customtkinter.CTkFrame(
        app.recent_settings_row,
        fg_color="transparent",
    )
    app.recent_settings_buttons_frame.pack(side="left", fill="x", expand=True)
    app.recent_settings_empty_label = customtkinter.CTkLabel(
        app.recent_settings_buttons_frame,
        text="まだありません",
        font=app.font_small,
        text_color=colors["text_tertiary"],
    )
    app.recent_settings_empty_label.pack(side="left")

    app.detail_settings_frame = customtkinter.CTkFrame(app)
    app._style_card_frame(app.detail_settings_frame, corner_radius=12)
    app._setup_output_controls(app.detail_settings_frame)
    register_setting_watchers(app)
    refresh_recent_settings_buttons(app)
    app._apply_ui_mode()
    app._update_settings_summary()
    app._set_details_panel_visibility(False)


def register_setting_watchers(app: Any) -> None:
    for var in (
        app.output_format_var,
        app.quality_var,
        app.webp_method_var,
        app.webp_lossless_var,
        app.avif_speed_var,
        app.exif_mode_var,
        app.remove_gps_var,
        app.dry_run_var,
    ):
        var.trace_add("write", app._on_setting_var_changed)


def on_setting_var_changed(app: Any, *_args: Any) -> None:
    app._update_settings_summary()


def recent_setting_label_from_values(
    values: Mapping[str, Any],
    *,
    merge_processing_values_fn: Callable[[Mapping[str, Any]], Mapping[str, Any]],
    format_id_to_label: Mapping[str, str],
) -> str:
    merged = merge_processing_values_fn(values)
    mode = str(merged.get("mode", "ratio"))
    if mode == "width":
        size_text = f"幅{merged.get('width_value', '')}px"
    elif mode == "height":
        size_text = f"高{merged.get('height_value', '')}px"
    elif mode == "fixed":
        size_text = f"固定{merged.get('width_value', '')}x{merged.get('height_value', '')}"
    else:
        size_text = f"比率{merged.get('ratio_value', '100')}%"
    format_id = str(merged.get("output_format", "auto")).lower()
    format_label = format_id_to_label.get(format_id, "自動")
    quality_text = f"Q{merged.get('quality', '85')}"
    return f"{size_text}/{format_label}/{quality_text}"


def recent_settings_fingerprint(
    values: Mapping[str, Any],
    *,
    merge_processing_values_fn: Callable[[Mapping[str, Any]], Mapping[str, Any]],
) -> str:
    merged = merge_processing_values_fn(values)
    return json.dumps(merged, ensure_ascii=False, sort_keys=True)


def normalize_recent_settings_entries(
    raw: Any,
    *,
    recent_settings_max: int,
    merge_processing_values_fn: Callable[[Mapping[str, Any]], Mapping[str, Any]],
    recent_settings_fingerprint_fn: Callable[[Mapping[str, Any]], str],
    recent_setting_label_fn: Callable[[Mapping[str, Any]], str],
) -> List[Dict[str, Any]]:
    if not isinstance(raw, list):
        return []

    entries: List[Dict[str, Any]] = []
    seen: set[str] = set()
    for item in raw:
        if not isinstance(item, dict):
            continue
        values_raw = item.get("values")
        if not isinstance(values_raw, Mapping):
            continue
        values = merge_processing_values_fn(values_raw)
        fingerprint = str(item.get("fingerprint", "")).strip() or recent_settings_fingerprint_fn(values)
        if not fingerprint or fingerprint in seen:
            continue
        seen.add(fingerprint)
        label = str(item.get("label", "")).strip() or recent_setting_label_fn(values)
        used_at = str(item.get("used_at", "")).strip()
        entries.append(
            {
                "fingerprint": fingerprint,
                "label": label,
                "used_at": used_at,
                "values": values,
            }
        )
        if len(entries) >= recent_settings_max:
            break
    return entries


def recent_settings_entries(app: Any) -> List[Dict[str, Any]]:
    entries = app._normalize_recent_settings_entries(app.settings.get("recent_processing_settings", []))
    app.settings["recent_processing_settings"] = entries
    return entries


def refresh_recent_settings_buttons(app: Any) -> None:
    if not hasattr(app, "recent_settings_buttons_frame"):
        return

    for button in app._recent_setting_buttons:
        button.destroy()
    app._recent_setting_buttons = []

    entries = recent_settings_entries(app)
    if not entries:
        if app.recent_settings_empty_label.winfo_manager() != "pack":
            app.recent_settings_empty_label.pack(side="left")
        return

    if app.recent_settings_empty_label.winfo_manager():
        app.recent_settings_empty_label.pack_forget()

    for index, entry in enumerate(entries, start=1):
        button = customtkinter.CTkButton(
            app.recent_settings_buttons_frame,
            text=f"{index}:{entry['label']}",
            width=124,
            command=lambda fp=entry["fingerprint"]: app._apply_recent_setting(fp),
            font=app.font_small,
        )
        app._style_secondary_button(button)
        button.pack(side="left", padx=(0, 6))
        app._register_tooltip(button, app._recent_setting_tooltip_text(entry))
        app._recent_setting_buttons.append(button)


def apply_recent_setting(app: Any, fingerprint: str) -> None:
    if app._is_loading_files:
        messagebox.showinfo("処理中", "画像読み込み中は最近使った設定を適用できません。")
        return

    entries = recent_settings_entries(app)
    target_index = next(
        (index for index, entry in enumerate(entries) if entry.get("fingerprint") == fingerprint),
        -1,
    )
    if target_index < 0:
        messagebox.showwarning("最近使った設定", "選択された設定が見つかりませんでした。")
        refresh_recent_settings_buttons(app)
        return

    entry = entries.pop(target_index)
    values = entry.get("values")
    if not isinstance(values, Mapping):
        messagebox.showwarning("最近使った設定", "設定データが不正です。")
        refresh_recent_settings_buttons(app)
        return

    app._apply_processing_values(values)
    entry["used_at"] = datetime.now().isoformat(timespec="seconds")
    entries.insert(0, entry)
    app.settings["recent_processing_settings"] = entries[: app._recent_settings_max]
    app._save_current_settings()
    refresh_recent_settings_buttons(app)
    app.status_var.set(f"最近使った設定を適用: {entry.get('label', '')}")


def register_recent_setting_from_current(app: Any) -> None:
    values = app._capture_current_processing_values(require_valid_exif_datetime=False)
    if values is None:
        return
    merged = app._merge_processing_values(values)
    fingerprint = app._recent_settings_fingerprint(merged)
    label = app._recent_setting_label_from_values(merged)
    now = datetime.now().isoformat(timespec="seconds")

    entries = recent_settings_entries(app)
    entries = [entry for entry in entries if entry.get("fingerprint") != fingerprint]
    entries.insert(
        0,
        {
            "fingerprint": fingerprint,
            "label": label,
            "used_at": now,
            "values": merged,
        },
    )
    app.settings["recent_processing_settings"] = entries[: app._recent_settings_max]
    app._save_current_settings()
    refresh_recent_settings_buttons(app)

