"""Main layout, status bar, and metadata panel helpers for ResizeApp."""

from __future__ import annotations

from typing import Any, Callable, Dict, List, Mapping, Optional, Sequence, Tuple, cast

import customtkinter
from PIL import Image
from PIL.ExifTags import GPSTAGS

ColorMap = Dict[str, Tuple[str, str]]


def setup_main_layout(
    app: Any,
    *,
    colors: ColorMap,
    default_preview: int,
    file_filter_labels: Sequence[str],
) -> None:
    setup_progress_bar_and_cancel(app, colors=colors)
    setup_status_bar(app, colors=colors)

    app.grid_rowconfigure(1, weight=1)
    app.grid_columnconfigure(1, weight=1)

    setup_left_panel(
        app,
        colors=colors,
        file_filter_labels=file_filter_labels,
    )
    setup_right_panel(app, colors=colors)

    app.bind("<Configure>", app._on_root_resize)
    app._last_canvas_size = (default_preview, default_preview)
    app._imgtk_org = None
    app._imgtk_resz = None
    app._zoom_org = None
    app._zoom_resz = None


def setup_progress_bar_and_cancel(app: Any, *, colors: ColorMap) -> None:
    app.progress_bar = customtkinter.CTkProgressBar(
        app,
        width=400,
        height=20,
        fg_color=colors["bg_tertiary"],
        progress_color=colors["primary"],
    )
    app.progress_bar.set(0)
    app.progress_bar.pack_forget()

    app.cancel_button = customtkinter.CTkButton(
        app,
        text="キャンセル",
        width=100,
        command=app._cancel_active_operation,
    )
    app._style_secondary_button(app.cancel_button)
    app.cancel_button.pack_forget()


def setup_status_bar(app: Any, *, colors: ColorMap) -> None:
    app.operation_stage_var = customtkinter.StringVar(value="")
    app.operation_stage_label = customtkinter.CTkLabel(
        app,
        textvariable=app.operation_stage_var,
        anchor="w",
        font=app.font_small,
        text_color=colors["warning"],
        fg_color=colors["bg_secondary"],
        corner_radius=10,
        padx=10,
    )
    app.operation_stage_label.pack_forget()

    app.action_hint_var = customtkinter.StringVar(value="")
    app.action_hint_label = customtkinter.CTkLabel(
        app,
        textvariable=app.action_hint_var,
        anchor="w",
        font=app.font_small,
        text_color=colors["warning"],
        fg_color=colors["bg_secondary"],
        corner_radius=10,
        padx=10,
    )
    app.action_hint_label.pack(side="bottom", fill="x", padx=12, pady=(0, 4))

    app.session_summary_var = customtkinter.StringVar(value="")
    app.session_summary_label = customtkinter.CTkLabel(
        app,
        textvariable=app.session_summary_var,
        anchor="w",
        font=app.font_small,
        text_color=colors["text_tertiary"],
        fg_color=colors["bg_secondary"],
        corner_radius=10,
        padx=10,
    )
    app.session_summary_label.pack(side="bottom", fill="x", padx=12, pady=(0, 4))

    app.status_var = customtkinter.StringVar(value="準備完了")
    app.status_label = customtkinter.CTkLabel(
        app,
        textvariable=app.status_var,
        anchor="w",
        font=app.font_default,
        text_color=colors["text_secondary"],
        fg_color=colors["bg_secondary"],
        corner_radius=10,
        padx=10,
    )
    app.status_label.pack(side="bottom", fill="x", padx=12, pady=(0, 8))


def show_operation_stage(app: Any, stage_text: str, *, operation_only_cancel_hint: str) -> None:
    if not stage_text:
        return
    app.operation_stage_var.set(f"処理段階: {stage_text} / {operation_only_cancel_hint}")
    if app.operation_stage_label.winfo_manager() != "pack":
        app.operation_stage_label.pack(side="bottom", fill="x", padx=12, pady=(0, 4))


def hide_operation_stage(app: Any) -> None:
    app.operation_stage_var.set("")
    if app.operation_stage_label.winfo_manager():
        app.operation_stage_label.pack_forget()


def shorten_path_for_summary(path_text: str, max_len: int = 46) -> str:
    value = str(path_text).strip()
    if len(value) <= max_len:
        return value
    head = max_len // 2 - 1
    tail = max_len - head - 1
    return f"{value[:head]}…{value[-tail:]}"


def session_status_text(
    app: Any,
    *,
    file_filter_label_to_id: Mapping[str, str],
    file_filter_id_to_label: Mapping[str, str],
) -> str:
    mode = app.ui_mode_var.get() if hasattr(app, "ui_mode_var") else "簡易"
    dry_run = "ON" if (hasattr(app, "dry_run_var") and app.dry_run_var.get()) else "OFF"
    total = len(app.jobs)
    failed = sum(1 for job in app.jobs if job.last_process_state == "failed")
    unprocessed = sum(1 for job in app.jobs if job.last_process_state == "unprocessed")
    visible = len(app._visible_job_indices)
    if hasattr(app, "file_filter_var"):
        filter_label_value = app.file_filter_var.get()
    else:
        filter_label_value = "全件"
    filter_id = file_filter_label_to_id.get(filter_label_value, "all")
    filter_label = file_filter_id_to_label.get(filter_id, filter_label_value)
    output_dir = str(app.settings.get("last_output_dir") or app.settings.get("default_output_dir") or "-")
    output_dir = shorten_path_for_summary(output_dir)
    return (
        f"セッション: モード {mode} / 表示 {visible}/{total} ({filter_label}) / "
        f"未処理 {unprocessed} / 失敗 {failed} / ドライラン {dry_run} / 保存先 {output_dir}"
    )


def update_session_summary(
    app: Any,
    *,
    file_filter_label_to_id: Mapping[str, str],
    file_filter_id_to_label: Mapping[str, str],
) -> None:
    if not hasattr(app, "session_summary_var"):
        return
    app.session_summary_var.set(
        session_status_text(
            app,
            file_filter_label_to_id=file_filter_label_to_id,
            file_filter_id_to_label=file_filter_id_to_label,
        )
    )


def refresh_status_indicators(
    app: Any,
    *,
    file_filter_label_to_id: Mapping[str, str],
    file_filter_id_to_label: Mapping[str, str],
) -> None:
    update_action_hint(app)
    update_session_summary(
        app,
        file_filter_label_to_id=file_filter_label_to_id,
        file_filter_id_to_label=file_filter_id_to_label,
    )


def update_action_hint(app: Any) -> None:
    if not hasattr(app, "action_hint_var"):
        return
    if app._is_loading_files:
        reason = "読み込み中です。完了または中止後に操作できます。"
    elif app._operation_scope is not None and app._operation_scope.active:
        reason = "処理中です。キャンセル以外の操作はできません。"
    elif not app.jobs:
        reason = "画像が未選択です。まず画像を読み込んでください。"
    elif app.current_index is None:
        reason = "左の一覧から対象画像を選択してください。"
    else:
        reason = "準備完了です。プレビュー・保存を実行できます。"
    app._action_hint_reason = reason
    app.action_hint_var.set(f"操作ガイド: {reason}")


def show_progress_with_cancel(
    app: Any,
    cancel_text: str,
    cancel_command: Callable[[], None],
    initial_progress: float,
) -> None:
    app.progress_bar.pack(side="bottom", fill="x", padx=10, pady=(0, 5))
    app.cancel_button.configure(text=cancel_text, command=cancel_command)
    app.cancel_button.pack(side="bottom", pady=(0, 10))
    app.progress_bar.set(max(0.0, min(1.0, initial_progress)))


def hide_progress_with_cancel(app: Any) -> None:
    app.progress_bar.pack_forget()
    app.cancel_button.pack_forget()
    app.cancel_button.configure(text="キャンセル", command=app._cancel_active_operation)


def build_operation_scope_hooks(app: Any, *, operation_scope_hooks_cls: Any) -> Any:
    return operation_scope_hooks_cls(
        set_controls_enabled=app._set_interactive_controls_enabled,
        show_progress_with_cancel=app._show_progress_with_cancel,
        hide_progress_with_cancel=app._hide_progress_with_cancel,
        show_stage=app._show_operation_stage,
        hide_stage=app._hide_operation_stage,
    )


def begin_operation_scope(
    app: Any,
    *,
    operation_scope_cls: Any,
    operation_scope_hooks_cls: Any,
    stage_text: str,
    cancel_text: str,
    cancel_command: Callable[[], None],
    initial_progress: float,
) -> None:
    end_operation_scope(app)
    app._operation_scope = operation_scope_cls(
        hooks=build_operation_scope_hooks(app, operation_scope_hooks_cls=operation_scope_hooks_cls),
        stage_text=stage_text,
        cancel_text=cancel_text,
        cancel_command=cancel_command,
        initial_progress=initial_progress,
    )
    app._operation_scope.begin()


def set_operation_stage(app: Any, stage_text: str) -> None:
    if app._operation_scope is not None and app._operation_scope.active:
        app._operation_scope.set_stage(stage_text)
        return
    app._show_operation_stage(stage_text)


def end_operation_scope(app: Any) -> None:
    if app._operation_scope is None:
        return
    app._operation_scope.close()
    app._operation_scope = None


def setup_left_panel(
    app: Any,
    *,
    colors: ColorMap,
    file_filter_labels: Sequence[str],
) -> None:
    app.main_content = customtkinter.CTkFrame(app, fg_color="transparent")
    app.main_content.pack(fill="both", expand=True, padx=12, pady=8)

    app.file_list_frame = customtkinter.CTkScrollableFrame(
        app.main_content,
        label_text="ファイルリスト",
        label_font=app.font_small,
        width=250,
        fg_color=colors["bg_secondary"],
        border_width=1,
        border_color=colors["border_light"],
        label_fg_color=colors["bg_tertiary"],
        label_text_color=colors["text_secondary"],
        corner_radius=12,
    )
    app.file_list_frame.pack(side="left", fill="y", padx=(0, 6))
    app.file_filter_var = customtkinter.StringVar(value="全件")
    app.file_filter_segment = customtkinter.CTkSegmentedButton(
        app.file_list_frame,
        values=list(file_filter_labels),
        variable=app.file_filter_var,
        command=app._on_file_filter_changed,
        width=220,
        font=app.font_small,
        selected_color=colors["primary"],
        selected_hover_color=colors["hover"],
        unselected_color=colors["bg_tertiary"],
        unselected_hover_color=colors["accent_soft"],
        text_color=colors["text_primary"],
    )
    app.file_filter_segment.pack(fill="x", padx=8, pady=(8, 4))
    app._register_tooltip(app.file_filter_segment, "一覧表示を全件・失敗・未処理で切り替えます。")

    app.file_buttons = []
    app.empty_state_label = customtkinter.CTkLabel(
        app.file_list_frame,
        text="",
        justify="left",
        anchor="w",
        font=app.font_small,
        text_color=colors["text_secondary"],
        wraplength=220,
    )
    app.empty_state_label.pack(fill="x", padx=8, pady=(8, 4))
    app._update_empty_state_hint()


def setup_right_panel(app: Any, *, colors: ColorMap) -> None:
    preview_pane = customtkinter.CTkFrame(app.main_content, fg_color="transparent")
    preview_pane.pack(side="right", fill="both", expand=True, padx=(5, 0))
    preview_pane.grid_rowconfigure(0, weight=1)
    preview_pane.grid_rowconfigure(1, weight=0)
    preview_pane.grid_columnconfigure(0, weight=1)
    preview_pane.grid_columnconfigure(1, weight=1)

    frame_original = customtkinter.CTkFrame(preview_pane, corner_radius=12)
    app._style_card_frame(frame_original, corner_radius=12)
    frame_original.grid(row=0, column=0, sticky="nswe", padx=(0, 4), pady=(0, 5))
    frame_original.grid_rowconfigure(1, weight=1)
    frame_original.grid_columnconfigure(0, weight=1)
    customtkinter.CTkLabel(
        frame_original,
        text="オリジナル",
        font=app.font_default,
        text_color=colors["text_secondary"],
    ).grid(row=0, column=0, sticky="w", padx=10, pady=(8, 0))
    app.canvas_org = customtkinter.CTkCanvas(
        frame_original,
        bg=app._canvas_background_color(),
        highlightthickness=0,
    )
    app.canvas_org.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)
    app.info_orig_var = customtkinter.StringVar(value="--- x ---  ---")
    customtkinter.CTkLabel(
        frame_original,
        textvariable=app.info_orig_var,
        justify="left",
        font=app.font_small,
        text_color=colors["text_tertiary"],
    ).grid(row=2, column=0, sticky="ew", padx=10, pady=(0, 8))

    app.lf_resized = customtkinter.CTkFrame(preview_pane, corner_radius=12)
    app._style_card_frame(app.lf_resized, corner_radius=12)
    app.lf_resized.grid(row=0, column=1, sticky="nswe", padx=(4, 0), pady=(0, 5))
    app.lf_resized.grid_rowconfigure(1, weight=1)
    app.lf_resized.grid_columnconfigure(0, weight=1)
    app.resized_title_label = customtkinter.CTkLabel(
        app.lf_resized,
        text="リサイズ後",
        font=app.font_default,
        text_color=colors["text_secondary"],
    )
    app.resized_title_label.grid(row=0, column=0, sticky="w", padx=10, pady=(8, 0))
    app.canvas_resz = customtkinter.CTkCanvas(
        app.lf_resized,
        bg=app._canvas_background_color(),
        highlightthickness=0,
    )
    app.canvas_resz.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)
    app.info_resized_var = customtkinter.StringVar(value="--- x ---  ---  (---)")
    customtkinter.CTkLabel(
        app.lf_resized,
        textvariable=app.info_resized_var,
        justify="left",
        font=app.font_small,
        text_color=colors["text_tertiary"],
    ).grid(row=2, column=0, sticky="ew", padx=10, pady=(0, 8))

    app.canvas_org.bind("<MouseWheel>", lambda e: app._on_zoom(e, is_resized=False))
    app.canvas_resz.bind("<MouseWheel>", lambda e: app._on_zoom(e, is_resized=True))
    app.canvas_org.bind("<ButtonPress-1>", lambda e: app.canvas_org.scan_mark(e.x, e.y))
    app.canvas_org.bind("<B1-Motion>", lambda e: app.canvas_org.scan_dragto(e.x, e.y, gain=1))
    app.canvas_resz.bind("<ButtonPress-1>", lambda e: app.canvas_resz.scan_mark(e.x, e.y))
    app.canvas_resz.bind("<B1-Motion>", lambda e: app.canvas_resz.scan_dragto(e.x, e.y, gain=1))

    app.metadata_frame = customtkinter.CTkFrame(preview_pane, corner_radius=12)
    app._style_card_frame(app.metadata_frame, corner_radius=12)
    app.metadata_frame.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(6, 0))

    app.metadata_header_frame = customtkinter.CTkFrame(app.metadata_frame, fg_color="transparent")
    app.metadata_header_frame.pack(side="top", fill="x", padx=8, pady=(8, 4))

    app.metadata_title_label = customtkinter.CTkLabel(
        app.metadata_header_frame,
        text="メタデータ（プロ）",
        font=app.font_default,
        text_color=colors["text_secondary"],
    )
    app.metadata_title_label.pack(side="left")

    app.metadata_toggle_button = customtkinter.CTkButton(
        app.metadata_header_frame,
        text="表示",
        width=80,
        command=app._toggle_metadata_panel,
        font=app.font_small,
    )
    app._style_tertiary_button(app.metadata_toggle_button)
    app.metadata_toggle_button.pack(side="right")

    app.metadata_status_var = customtkinter.StringVar(value="画像を選択するとメタデータを表示できます")
    app.metadata_status_label = customtkinter.CTkLabel(
        app.metadata_frame,
        textvariable=app.metadata_status_var,
        anchor="w",
        justify="left",
        font=app.font_small,
        text_color=colors["text_tertiary"],
    )
    app.metadata_status_label.pack(side="top", fill="x", padx=10, pady=(0, 4))

    app.metadata_textbox = customtkinter.CTkTextbox(
        app.metadata_frame,
        height=120,
        corner_radius=8,
        border_width=1,
        border_color=colors["border_light"],
        fg_color=colors["input_bg"],
        text_color=cast(Any, colors["text_primary"]),
        font=app.font_small,
        wrap="word",
    )
    app.metadata_expanded = False
    set_metadata_panel_expanded(app, False)
    set_metadata_text(app, "（プロモードで表示可能）")


def toggle_metadata_panel(app: Any) -> None:
    set_metadata_panel_expanded(app, not app.metadata_expanded)


def set_metadata_panel_expanded(app: Any, expanded: bool) -> None:
    app.metadata_expanded = expanded
    if expanded:
        if app.metadata_textbox.winfo_manager() != "pack":
            app.metadata_textbox.pack(side="top", fill="x", padx=10, pady=(0, 10))
        app.metadata_toggle_button.configure(text="隠す")
    else:
        if app.metadata_textbox.winfo_manager():
            app.metadata_textbox.pack_forget()
        app.metadata_toggle_button.configure(text="表示")


def set_metadata_text(app: Any, text: str) -> None:
    app.metadata_textbox.configure(state="normal")
    app.metadata_textbox.delete("1.0", "end")
    app.metadata_textbox.insert("1.0", text)
    app.metadata_textbox.configure(state="disabled")


def decode_exif_value(value: object) -> str:
    if value is None:
        return ""
    if isinstance(value, bytes):
        raw = value
        if raw.startswith(b"ASCII\x00\x00\x00"):
            raw = raw[8:]
        text = raw.decode("utf-8", errors="ignore").strip("\x00 ").strip()
        if not text:
            text = raw.decode("latin-1", errors="ignore").strip("\x00 ").strip()
        return text
    if hasattr(value, "numerator") and hasattr(value, "denominator"):
        denominator = getattr(value, "denominator", 1) or 1
        numerator = getattr(value, "numerator", 0)
        try:
            ratio = float(numerator) / float(denominator)
            if abs(ratio - round(ratio)) < 1e-9:
                return str(int(round(ratio)))
            return f"{ratio:.4g}"
        except Exception:
            return str(value).strip()
    if isinstance(value, tuple):
        if len(value) == 2 and all(isinstance(v, (int, float)) for v in value):
            denominator = value[1] if value[1] else 1
            ratio = value[0] / denominator
            if abs(ratio - round(ratio)) < 1e-9:
                return str(int(round(ratio)))
            return f"{ratio:.4g}"
        parts = [decode_exif_value(v) for v in value]
        return ", ".join(p for p in parts if p)
    return str(value).strip()


def extract_metadata_text(
    app: Any,
    job: Any,
    *,
    exif_gps_info_tag: int,
    exif_preview_tags: Sequence[Tuple[str, int]],
) -> str:
    if job.metadata_loaded:
        return job.metadata_text

    try:
        with Image.open(job.path) as src:
            exif = src.getexif()
        has_exif = bool(exif)
        tag_count = len(exif)
        try:
            gps_ifd = exif.get_ifd(exif_gps_info_tag)
            has_gps = bool(gps_ifd)
        except Exception:
            has_gps = exif_gps_info_tag in exif

        lines = [
            f"EXIF: {'あり' if has_exif else 'なし'}",
            f"タグ数: {tag_count}",
            f"GPS: {'あり' if has_gps else 'なし'}",
        ]
        for label, tag_id in exif_preview_tags:
            text = decode_exif_value(exif.get(tag_id))
            if text:
                lines.append(f"{label}: {app._trim_preview_text(text, max_len=80)}")

        if not has_exif:
            lines.append("元画像にEXIFメタデータはありません。")

        if has_gps:
            try:
                gps_ifd = exif.get_ifd(exif_gps_info_tag)
                gps_keys = [GPSTAGS.get(key, str(key)) for key in gps_ifd.keys()]
                gps_preview = ", ".join(gps_keys[:5])
                if gps_preview:
                    lines.append(f"GPSタグ: {gps_preview}")
            except Exception:
                pass

        job.metadata_text = "\n".join(lines)
        job.metadata_error = None
    except Exception as exc:
        job.metadata_error = str(exc)
        job.metadata_text = "メタデータの取得に失敗しました。"

    job.metadata_loaded = True
    return job.metadata_text


def update_metadata_preview(app: Any, job: Optional[Any]) -> None:
    if not hasattr(app, "metadata_status_var"):
        return
    if job is None:
        app.metadata_status_var.set("画像を選択するとメタデータを表示できます")
        set_metadata_text(app, "（画像未選択）")
        return

    metadata_text = app._extract_metadata_text(job)
    if job.metadata_error:
        app.metadata_status_var.set(f"メタデータ: 取得失敗 ({job.path.name})")
    else:
        app.metadata_status_var.set(f"メタデータ: {job.path.name}")
    set_metadata_text(app, metadata_text)


def update_metadata_panel_state(app: Any) -> None:
    if not hasattr(app, "metadata_frame"):
        return
    if app._is_pro_mode():
        if app.metadata_frame.winfo_manager() != "grid":
            app.metadata_frame.grid()
        selected_job = None
        if app.current_index is not None and app.current_index < len(app.jobs):
            selected_job = app.jobs[app.current_index]
        update_metadata_preview(app, selected_job)
    else:
        if app.metadata_frame.winfo_manager():
            app.metadata_frame.grid_remove()
