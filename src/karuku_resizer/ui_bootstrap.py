"""Bootstrap helpers for building ResizeApp UI."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
import queue
import threading
from typing import Any, Callable, Dict, List, Mapping, Optional, Sequence, Tuple

import customtkinter
from PIL import Image, ImageTk
import logging
import platform
import sys
import time
import tkinter.font as tkfont
from tkinter import filedialog, messagebox

from karuku_resizer.runtime_logging import write_run_summary
from karuku_resizer.image_save_pipeline import (
    SaveFormat,
    SaveResult,
    destination_with_extension,
)
from karuku_resizer.ui_text_presenter import (
    build_batch_completion_message,
    build_batch_progress_status_text,
    build_batch_run_mode_text,
    build_exif_status_text,
    build_readable_os_error as presenter_build_readable_os_error,
)
from karuku_resizer.ui.result_dialog import show_operation_result_dialog
from karuku_resizer.ui_save_helpers import (
    build_batch_save_options,
    build_save_options,
    build_single_save_filetypes,
    build_unique_batch_base_path,
    is_windows_path_length_risky,
    normalize_windows_output_filename,
    preflight_output_directory,
    preflight_output_directory_only,
)
from karuku_resizer.ui_file_list_panel import apply_file_list_selection
from karuku_resizer.ui.file_load_session import (
    begin_file_load_session as file_load_begin_session,
    start_drop_load_async as file_load_start_drop,
    start_recursive_load_async as file_load_start_recursive,
    start_retry_failed_load_async as file_load_start_retry_failed,
)
from karuku_resizer.ui_file_load_helpers import (
    dedupe_paths,
    is_selectable_input_file,
    parse_drop_paths as parse_drop_paths_from_helper,
)

from karuku_resizer.ui_detail_controls import (
    DetailHeaderCallbacks,
    DetailHeaderState,
    DetailEntryCallbacks,
    DetailEntryState,
    DetailFormCallbacks,
    DetailFormState,
    DetailOutputCallbacks,
    DetailOutputState,
    apply_detail_panel_visibility,
    build_detail_entry_controls,
    build_detail_form,
    bind_detail_entry_refs,
    bind_detail_form_refs,
)
from karuku_resizer.ui_main_panel import (
    output_format_labels as main_output_format_labels,
    MainPanelCallbacks,
    MainPanelState,
    setup_main_layout,
)
from karuku_resizer.ui_metadata_panel import (
    apply_metadata_expanded,
    apply_metadata_text,
)
from karuku_resizer.ui_topbar import TopBarController


DEFAULT_APP_COLORS: Dict[str, Any] = {
    "primary": "#2F7FC8",
    "hover": "#286CB0",
    "accent_soft": "#E8F3FF",
    "pressed": "#1F7DCF",
    "text_primary": "#1F2A37",
    "text_secondary": "#5B6878",
    "text_tertiary": "#7A8696",
    "bg_primary": "#F4F7FB",
    "bg_secondary": "#FFFFFF",
    "bg_tertiary": "#EFF4FA",
    "input_bg": "#FFFFFF",
    "border_light": "#D9E2EC",
    "border_medium": "#CBD5E1",
    "warning": "#C97A00",
}


def bootstrap_resolve_app_colors(app: Any) -> Dict[str, Any]:
    resolved = dict(DEFAULT_APP_COLORS)
    colors = getattr(app, "_app_colors", None)
    if isinstance(colors, Mapping):
        resolved.update(dict(colors))
    return resolved


def setup_resize_app_layout(
    app: Any,
    *,
    colors: Dict[str, Any],
    available_formats: Sequence[str],
    file_filter_values: Sequence[str],
    quality_values: Sequence[str],
    webp_method_values: Sequence[str],
    avif_speed_values: Sequence[str],
    preset_none_label: str,
    initial_canvas_size: Tuple[int, int] = (480, 480),
) -> None:
    """Build ResizeApp UI widgets and bind refs onto the app instance."""

    app.zoom_var = customtkinter.StringVar(value="画面に合わせる")
    app.preset_var = customtkinter.StringVar(value=preset_none_label)
    app._topbar_controller = TopBarController(
        on_select=app._select_files,
        on_help=app._show_help,
        on_settings=app._open_settings_dialog,
        on_preset_manage=app._open_preset_manager_dialog,
        on_preset_changed=app._on_preset_menu_changed,
        on_preview=app._preview_current,
        on_save=app._save_current,
        on_batch=app._batch_save,
        on_zoom_changed=app._apply_zoom_selection,
        scale_px=app._scale_px,
        scale_topbar_widths=app._scale_topbar_widths,
        style_primary_button=app._style_primary_button,
        style_secondary_button=app._style_secondary_button,
        style_card_frame=app._style_card_frame,
        font_default=app.font_default,
        font_small=app.font_small,
        colors=colors,
        get_topbar_density=lambda: app._topbar_density,
        set_topbar_density=lambda density: setattr(app, "_topbar_density", density),
        select_button_text=app._select_button_text_for_state,
        icon_folder=app._icon_folder,
        icon_circle_help=app._icon_circle_help,
        icon_settings=app._icon_settings,
        icon_refresh=app._icon_refresh,
        icon_save=app._icon_save,
        icon_folder_open=app._icon_folder_open,
        preset_var=app.preset_var,
        zoom_var=app.zoom_var,
    )

    def _build_topbar_entry_controls(parent: Any) -> None:
        entry_refs = build_detail_entry_controls(
            parent,
            state=DetailEntryState(
                scale_px=app._scale_px,
                font_default=app.font_default,
                colors=colors,
                style_secondary_button=app._style_secondary_button,
                validate_callback=app._validate_int,
            ),
            callbacks=DetailEntryCallbacks(on_mode_changed=app._update_mode),
        )
        app._detail_entry_refs = entry_refs
        bind_detail_entry_refs(app, entry_refs)

    topbar_widgets = app._topbar_controller.build(
        app,
        setup_entry_widgets=_build_topbar_entry_controls,
    )
    app.select_button = topbar_widgets.select_button
    app.help_button = topbar_widgets.help_button
    app.settings_button = topbar_widgets.settings_button
    app.preset_manage_button = topbar_widgets.preset_manage_button
    app.preset_menu = topbar_widgets.preset_menu
    app.preset_caption_label = topbar_widgets.preset_caption_label
    app.preview_button = topbar_widgets.preview_button
    app.save_button = topbar_widgets.save_button
    app.batch_button = topbar_widgets.batch_button
    app.zoom_cb = topbar_widgets.zoom_cb
    if app._topbar_controller is not None:
        app._topbar_controller.apply_density(app._topbar_density_window_width(max(app.winfo_width(), 1200)))

    detail_form_refs = build_detail_form(
        app,
        state=DetailFormState(
            header=DetailHeaderState(
                scale_px=app._scale_px,
                font_small=app.font_small,
                font_default=app.font_default,
                colors=colors,
                style_card_frame=app._style_card_frame,
            ),
            entry=DetailEntryState(
                scale_px=app._scale_px,
                font_default=app.font_default,
                colors=colors,
                style_secondary_button=app._style_secondary_button,
                validate_callback=app._validate_int,
            ),
            output=DetailOutputState(
                scale_px=app._scale_px,
                font_small=app.font_small,
                font_default=app.font_default,
                colors=colors,
                style_card_frame=app._style_card_frame,
                style_primary_button=app._style_primary_button,
                style_secondary_button=app._style_secondary_button,
                output_labels=main_output_format_labels(available_formats),
                quality_values=quality_values,
                webp_method_values=webp_method_values,
                avif_speed_values=avif_speed_values,
            ),
        ),
        callbacks=DetailFormCallbacks(
            header=DetailHeaderCallbacks(on_toggle_details=app._toggle_details_panel),
            entry=DetailEntryCallbacks(on_mode_changed=app._update_mode),
            output=DetailOutputCallbacks(
                on_output_format_changed=app._on_output_format_changed,
                on_quality_changed=app._on_quality_changed,
                on_exif_mode_changed=app._on_exif_mode_changed,
                on_codec_setting_changed=app._on_codec_setting_changed,
                on_webp_method_changed=app._on_webp_method_changed,
                on_avif_speed_changed=app._on_avif_speed_changed,
                on_webp_lossless_changed=app._on_codec_setting_changed,
                on_verbose_log=app._apply_log_level,
                on_exif_preview=app._show_exif_preview_dialog,
                on_open_log_folder=app._open_log_folder,
            ),
        ),
        existing_entry_refs=app._detail_entry_refs,
    )
    app.detail_form_refs = detail_form_refs
    bind_detail_form_refs(app, detail_form_refs)
    apply_detail_panel_visibility(app, expanded=False)

    setup_main_layout(
        app,
        state=MainPanelState(
            scale_px=app._scale_px,
            font_default=app.font_default,
            font_small=app.font_small,
            colors=colors,
            style_card_frame=app._style_card_frame,
            style_secondary_button=app._style_secondary_button,
            canvas_background_color=app._canvas_background_color,
        ),
        callbacks=MainPanelCallbacks(
            on_filter_changed=app._on_file_filter_changed,
            on_clear_loaded=app._clear_loaded_items,
            register_tooltip=app._register_tooltip,
            on_zoom_original=lambda event: app._on_zoom(event, is_resized=False),
            on_zoom_resized=lambda event: app._on_zoom(event, is_resized=True),
            on_drag_original_press=lambda event: app.canvas_org.scan_mark(event.x, event.y),
            on_drag_original_move=lambda event: app.canvas_org.scan_dragto(event.x, event.y, gain=1),
            on_drag_resized_press=lambda event: app.canvas_resz.scan_mark(event.x, event.y),
            on_drag_resized_move=lambda event: app.canvas_resz.scan_dragto(event.x, event.y, gain=1),
            on_toggle_metadata_panel=app._toggle_metadata_panel,
            on_cancel_active=app._cancel_active_operation,
        ),
        filter_values=list(file_filter_values),
        initial_canvas_size=initial_canvas_size,
    )
    if hasattr(app, "metadata_panel_refs"):
        apply_metadata_expanded(app.metadata_panel_refs, expanded=False)
        apply_metadata_text(app.metadata_panel_refs, "（プロモードで表示可能）")
    if app._topbar_controller is not None:
        app._topbar_controller.refresh_top_action_guide("")


def bootstrap_create_initial_run_summary(app: Any, *, log_app_name: str) -> Dict[str, Any]:
    return {
        "run_id": app._run_log_artifacts.run_id,
        "started_at": datetime.now().isoformat(timespec="seconds"),
        "finished_at": None,
        "app_name": log_app_name,
        "platform": platform.platform(),
        "python_version": platform.python_version(),
        "log_file": str(app._run_log_artifacts.run_log_path),
        "summary_file": str(app._run_log_artifacts.summary_path),
        "batch_runs": [],
        "errors": [],
        "totals": {
            "batch_run_count": 0,
            "processed_count": 0,
            "failed_count": 0,
            "dry_run_count": 0,
            "cancelled_count": 0,
        },
    }


def bootstrap_write_run_summary_safe(app: Any) -> None:
    try:
        write_run_summary(app._run_log_artifacts.summary_path, app._run_summary_payload)
    except Exception:
        logging.exception("Failed to write run summary")


def bootstrap_finalize_run_summary(app: Any) -> None:
    if getattr(app, "_run_summary_finalized", False):
        return
    app._run_summary_payload["finished_at"] = datetime.now().isoformat(timespec="seconds")
    app._run_summary_finalized = True
    bootstrap_write_run_summary_safe(app)


def bootstrap_ensure_run_log_handler(app: Any) -> None:
    root_logger = logging.getLogger()
    run_log_path = app._run_log_artifacts.run_log_path
    log_dir = app._run_log_artifacts.log_dir

    has_run_handler = False
    for handler in list(root_logger.handlers):
        if not isinstance(handler, logging.FileHandler):
            continue
        base_filename = getattr(handler, "baseFilename", "")
        if not base_filename:
            continue
        handler_path = Path(base_filename)
        if handler_path == run_log_path:
            has_run_handler = True
            continue
        if handler_path.parent == log_dir and handler_path.name.startswith("run_") and handler_path.suffix == ".log":
            root_logger.removeHandler(handler)
            handler.close()

    if has_run_handler:
        return

    run_log_path.parent.mkdir(parents=True, exist_ok=True)
    handler = logging.FileHandler(run_log_path, encoding="utf-8")
    handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s"))
    root_logger.addHandler(handler)


def bootstrap_style_primary_button(button: customtkinter.CTkButton, *, colors: Mapping[str, Any]) -> None:
    button.configure(
        fg_color=colors["primary"],
        hover_color=colors["hover"],
        text_color=colors["text_primary"],
        corner_radius=10,
        border_width=0,
    )


def bootstrap_style_secondary_button(button: Any, *, colors: Mapping[str, Any]) -> None:
    if isinstance(button, customtkinter.CTkRadioButton):
        return
    hover_color = colors.get("accent_soft", colors.get("hover", colors.get("bg_tertiary")))
    button.configure(
        fg_color=colors["bg_tertiary"],
        hover_color=hover_color,
        text_color=colors["text_primary"],
        border_width=1,
        border_color=colors["border_light"],
        corner_radius=10,
    )


def bootstrap_style_card_frame(frame: customtkinter.CTkFrame, *, colors: Mapping[str, Any], corner_radius: int = 12) -> None:
    frame.configure(
        fg_color=colors["bg_secondary"],
        border_width=1,
        border_color=colors["border_light"],
        corner_radius=corner_radius,
    )


def bootstrap_canvas_background_color() -> str:
    appearance = customtkinter.get_appearance_mode()
    return "#EEF3FA" if appearance == "Light" else "#111722"


def bootstrap_canvas_label_color() -> str:
    appearance = customtkinter.get_appearance_mode()
    return "#1F2A37" if appearance == "Light" else "#E8EEF5"


def bootstrap_normalize_font_candidate(value: str) -> str:
    return " ".join(str(value).strip().split()).lower()


def bootstrap_available_font_families() -> set[str]:
    try:
        return set(tkfont.families())
    except Exception:
        return set()


def bootstrap_pick_first_existing_font(candidate_fonts: Sequence[str], available: set[str]) -> str | None:
    if not available:
        return None
    normalized_available = {bootstrap_normalize_font_candidate(font): font for font in available}
    for candidate in candidate_fonts:
        normalized_candidate = bootstrap_normalize_font_candidate(candidate)
        if normalized_candidate in normalized_available:
            return normalized_available[normalized_candidate]
    return None


def bootstrap_register_font_resource_windows(font_path: Path) -> bool:
    if platform.system() != "Windows":
        return False
    try:
        import ctypes
        FR_PRIVATE = 0x10
        result = int(ctypes.windll.gdi32.AddFontResourceExW(str(font_path), FR_PRIVATE, None))
        if result <= 0:
            return False
        try:
            HWND_BROADCAST = 0xFFFF
            WM_FONTCHANGE = 0x001D
            SMTO_ABORTIFHUNG = 0x0002
            timeout = 1000
            ctypes.windll.user32.SendMessageTimeoutW(
                HWND_BROADCAST,
                WM_FONTCHANGE,
                0,
                0,
                SMTO_ABORTIFHUNG,
                timeout,
                None,
            )
        except Exception:
            pass
        return True
    except Exception:
        return False


def bootstrap_setup_ui_icons(app: Any, icon_loader: Callable[[str, int], Any]) -> None:
    app._icon_folder = icon_loader("folder", 16)
    app._icon_circle_help = icon_loader("circle-help", 16)
    app._icon_settings = icon_loader("settings", 16)
    app._icon_folder_open = icon_loader("folder-open", 16)
    app._icon_refresh = icon_loader("refresh-cw", 16)
    app._icon_save = icon_loader("save", 16)
    app._icon_trash = None  # TODO: Add trash-2_16.png to assets/icons/light/ and assets/icons/dark/


def bootstrap_apply_window_icon(app: Any, *, load_icon_paths: Callable[[], Tuple[Path | None, Path | None]]) -> None:
    ico_path, png_path = load_icon_paths()
    if platform.system() == "Windows" and ico_path is not None:
        try:
            app.iconbitmap(default=str(ico_path))
        except Exception:
            logging.exception("Failed to set Windows window icon via iconbitmap: %s", ico_path)

    if png_path is not None:
        try:
            app._window_icon_image = ImageTk.PhotoImage(file=str(png_path))
            app.iconphoto(True, app._window_icon_image)
        except Exception:
            logging.exception("Failed to set window icon via iconphoto: %s", png_path)


def bootstrap_runtime_base_dir() -> Path:
    if getattr(sys, "frozen", False):
        meipass = getattr(sys, "_MEIPASS", None)
        if meipass:
            return Path(str(meipass))
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parents[2]


def bootstrap_resolve_icon_paths() -> Tuple[Path | None, Path | None]:
    base = bootstrap_runtime_base_dir()
    ico = base / "assets" / "app.ico"
    png = base / "img" / "karuku.png"
    return (ico if ico.is_file() else None, png if png.is_file() else None)


def bootstrap_register_embedded_biz_ud_gothic_fonts(*, asset_font_dir: Path, font_asset_files: Sequence[str]) -> bool:
    if not asset_font_dir.is_dir():
        return False
    added = False
    for filename in font_asset_files:
        font_path = asset_font_dir / filename
        if not font_path.is_file():
            continue
        if bootstrap_register_font_resource_windows(font_path):
            added = True
    return added


def bootstrap_resolve_system_font_family(
    *,
    system_font_candidates: Sequence[str],
    font_asset_files: Sequence[str],
    fallback_font_families: Sequence[str],
    non_windows_font_families: Sequence[str],
) -> str:
    if platform.system() == "Windows":
        available = bootstrap_available_font_families()
        selected = bootstrap_pick_first_existing_font(system_font_candidates, available)
        if selected is not None:
            return selected

        if bootstrap_register_embedded_biz_ud_gothic_fonts(
            asset_font_dir=bootstrap_runtime_base_dir() / "assets" / "fonts",
            font_asset_files=font_asset_files,
        ):
            available = bootstrap_available_font_families()
            selected = bootstrap_pick_first_existing_font(system_font_candidates, available)
            if selected is not None:
                return selected

        selected = bootstrap_pick_first_existing_font(fallback_font_families, available)
        if selected is not None:
            return selected
        return "Segoe UI"

    available = bootstrap_available_font_families()
    selected = bootstrap_pick_first_existing_font(non_windows_font_families, available)
    return selected if selected is not None else "SF Pro Display"


def bootstrap_normalize_appearance_mode(
    value: str,
    appearance_id_to_label: Mapping[str, str],
    appearance_label_to_id: Mapping[str, str],
) -> str:
    raw = str(value).strip()
    normalized = raw.lower()
    if normalized in appearance_id_to_label:
        return normalized
    if raw in appearance_label_to_id:
        return appearance_label_to_id[raw]
    if normalized in {"システム", "system", "osに従う"}:
        return "system"
    return "system"


def bootstrap_normalize_ui_scale_mode(value: str, ui_scale_ids: Mapping[str, str], ui_scale_labels: Mapping[str, str]) -> str:
    raw = str(value).strip()
    if raw in ui_scale_ids:
        return raw
    if raw in ui_scale_labels:
        return ui_scale_labels[raw]
    normalized = raw.lower()
    if normalized in {"normal", "標準", "通常"}:
        return "normal"
    if normalized in {"125", "125%", "large", "large125", "18", "18px", "見やすい", "大きめ"}:
        return "large"
    return "normal"


def bootstrap_apply_ui_scale_mode(
    app: Any,
    mode_id: str,
    ui_scale_factors: Mapping[str, float],
    ui_font_size_pairs: Mapping[str, tuple[int, int]],
) -> None:
    normalized = bootstrap_normalize_ui_scale_mode(
        mode_id,
        ui_scale_ids={"normal": "normal", "large": "large"},
        ui_scale_labels={"normal": "normal", "large": "large", "標準": "normal", "大きめ": "large"},
    )
    app._ui_scale_mode = normalized
    scale = ui_scale_factors.get(normalized, 1.0)
    app._ui_scale_factor = scale
    if hasattr(customtkinter, "set_widget_scaling"):
        try:
            customtkinter.set_widget_scaling(scale)
        except Exception:
            pass

    default_size, small_size = ui_font_size_pairs.get(normalized, (16, 14))
    app.font_default = customtkinter.CTkFont(
        family=app._system_font,
        size=max(1, default_size),
        weight="normal",
    )
    app.font_small = customtkinter.CTkFont(
        family=app._system_font,
        size=max(1, small_size),
        weight="normal",
    )
    app.font_bold = customtkinter.CTkFont(
        family=app._system_font,
        size=max(1, default_size),
        weight="bold",
    )


def bootstrap_scale_px(app: Any, value: int) -> int:
    return max(1, round(value * app._ui_scale_factor))


def bootstrap_scale_pad_values(value: Any, factor: float) -> Any:
    if isinstance(value, (list, tuple)):
        return tuple(max(1, round(int(v) * factor)) for v in value)
    return max(1, round(int(value) * factor))


def bootstrap_scale_pad(app: Any, value: Any) -> Any:
    return bootstrap_scale_pad_values(value, app._ui_scale_factor)


def bootstrap_scale_topbar_widths(
    app: Any,
    density: str,
    topbar_widths: Mapping[str, Mapping[str, int]],
) -> Dict[str, int]:
    base = topbar_widths.get(density, topbar_widths["normal"])
    return {name: bootstrap_scale_px(app, width) for name, width in base.items()}


def bootstrap_topbar_density_window_width(window_width: int, scale_factor: float) -> int:
    return int(window_width / scale_factor)


def bootstrap_to_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"1", "true", "yes", "on"}


def bootstrap_setup_keyboard_shortcuts(app: Any, *, preview_action: Callable[[], None], save_action: Callable[[], None], batch_action: Callable[[], None]) -> None:
    app.bind_all("<Control-p>", lambda event: bootstrap_handle_shortcut_action(event, preview_action, lambda: bootstrap_is_modal_dialog_open(app)))
    app.bind_all("<Control-s>", lambda event: bootstrap_handle_shortcut_action(event, save_action, lambda: bootstrap_is_modal_dialog_open(app)))
    app.bind_all("<Control-Shift-S>", lambda event: bootstrap_handle_shortcut_action(event, batch_action, lambda: bootstrap_is_modal_dialog_open(app)))


def bootstrap_handle_shortcut_action(_event: Any, action: Callable[[], None], is_modal_dialog_open: Callable[[], bool]) -> str:
    if is_modal_dialog_open():
        return "break"
    action()
    return "break"


def bootstrap_is_modal_dialog_open(app: Any) -> bool:
    dialogs = [
        getattr(app, "_settings_dialog", None),
        getattr(app, "_preset_dialog", None),
        getattr(app, "_result_dialog", None),
    ]
    return any(dialog is not None and dialog.winfo_exists() for dialog in dialogs)


def bootstrap_register_tooltip(app: Any, widget: Any, text: str) -> None:
    if widget is None:
        return
    try:
        app._tooltip_manager.register(widget, text)
    except Exception:
        logging.exception("Tooltip registration failed for widget %s", widget)


def bootstrap_register_segmented_value_tooltips(app: Any, segmented: Any, text_by_value: Mapping[str, str]) -> None:
    buttons_dict = getattr(segmented, "_buttons_dict", None)
    if not isinstance(buttons_dict, dict):
        return
    for value, text in text_by_value.items():
        button = buttons_dict.get(value)
        if button is None:
            continue
        bootstrap_register_tooltip(app, button, text)


def bootstrap_register_tooltip_by_name(app: Any, attr_name: str, text: str) -> None:
    widget = getattr(app, attr_name, None)
    bootstrap_register_tooltip(app, widget, text)


FILE_LOAD_FAILURE_PREVIEW_LIMIT = 20
DROP_RECURSIVE_EXTENSIONS = (".jpg", ".jpeg", ".png")


def bootstrap_discover_recursive_image_paths(root_dir: Path) -> List[Path]:
    root = Path(root_dir)
    if not root.is_dir():
        return []
    return sorted(
        (path for path in root.rglob("*") if path.is_file() and path.suffix.lower() in {".jpg", ".jpeg", ".png"}),
        key=lambda path: str(path).lower(),
    )


def bootstrap_normalized_pro_input_mode(value: str) -> str:
    normalized = str(value).strip().lower()
    if normalized in {"recursive", "files"}:
        return normalized
    return "recursive"


def bootstrap_setup_drag_and_drop(
    app: Any,
    *,
    tkdnd_available: bool,
    tkdnd_cls: Any,
    copy_token: str,
    dnd_files: str,
    selectable_input_extensions: Sequence[str],
) -> None:
    if not tkdnd_available or tkdnd_cls is None:
        logging.info("Drag and drop disabled: tkinterdnd2 unavailable")
        return

    if not hasattr(app, "drop_target_register"):
        logging.info("Drag and drop disabled: root widget does not support drop_target_register")
        return

    try:
        tkdnd_cls._require(app)
    except Exception as exc:
        logging.warning("Drag and drop initialization failed: %s", exc)
        return

    targets = [
        app,
        app.main_content,
        app.file_list_frame,
        app.canvas_org,
        app.canvas_resz,
    ]
    registered = 0
    for widget in targets:
        try:
            widget.drop_target_register(dnd_files)
            widget.dnd_bind("<<DropEnter>>", lambda event: bootstrap_on_drop_enter(event, copy_token=copy_token))
            widget.dnd_bind("<<DropPosition>>", lambda event: bootstrap_on_drop_position(event, copy_token=copy_token))
            widget.dnd_bind("<<DropLeave>>", bootstrap_on_drop_leave)
            widget.dnd_bind(
                "<<Drop>>",
                lambda event: bootstrap_on_drop_files(
                    app,
                    event,
                    copy_token=copy_token,
                    selectable_input_extensions=selectable_input_extensions,
                ),
            )
            registered += 1
        except Exception:
            logging.exception("Failed to register drop target: %s", widget)

    app._drag_drop_enabled = registered > 0
    if app._drag_drop_enabled:
        logging.info("Drag and drop enabled on %d widgets", registered)


def bootstrap_on_drop_enter(_event: Any, copy_token: str) -> str:
    return str(copy_token)


def bootstrap_on_drop_position(_event: Any, copy_token: str) -> str:
    return str(copy_token)


def bootstrap_on_drop_leave(_event: Any) -> None:
    return None


def bootstrap_on_drop_files(
    app: Any,
    event: Any,
    *,
    copy_token: str,
    selectable_input_extensions: Sequence[str],
) -> str:
    if app._is_loading_files:
        messagebox.showinfo("処理中", "現在、画像読み込み処理中です。完了またはキャンセル後に再実行してください。")
        return str(copy_token)

    dropped_paths = parse_drop_paths_from_helper(
        lambda text: list(app.tk.splitlist(text)),
        raw_data=getattr(event, "data", ""),
    )
    if not dropped_paths:
        messagebox.showwarning("ドラッグ&ドロップ", "ドロップされたパスを解釈できませんでした。")
        return str(copy_token)

    bootstrap_handle_dropped_paths(
        app,
        dropped_paths,
        selectable_input_extensions=selectable_input_extensions,
    )
    return str(copy_token)


def bootstrap_handle_dropped_paths(
    app: Any,
    dropped_paths: List[Path],
    *,
    selectable_input_extensions: Sequence[str],
) -> None:
    files: List[Path] = []
    dirs: List[Path] = []
    ignored_count = 0
    for path in dropped_paths:
        try:
            if not path.exists():
                ignored_count += 1
                continue
            if path.is_dir():
                dirs.append(path)
            elif path.is_file() and is_selectable_input_file(
                path,
                selectable_exts=selectable_input_extensions,
            ):
                files.append(path)
            else:
                ignored_count += 1
        except OSError:
            ignored_count += 1

    files = dedupe_paths(files)
    dirs = dedupe_paths(dirs)
    if not files and not dirs:
        messagebox.showwarning("ドラッグ&ドロップ", "画像ファイルまたはフォルダーが見つかりませんでした。")
        return

    if dirs and not app._is_pro_mode():
        switch_to_pro = messagebox.askyesno(
            "ドラッグ&ドロップ",
            "フォルダーが含まれています。\n"
            "プロモードへ切り替えて再帰読み込みしますか？",
        )
        if switch_to_pro:
            app.ui_mode_var.set("プロ")
            app._apply_ui_mode()
            app._update_settings_summary()
        else:
            dirs = []

    if not files and not dirs:
        messagebox.showwarning("ドラッグ&ドロップ", "フォルダーを扱うにはプロモードに切り替えてください。")
        return

    if dirs:
        app.settings["pro_input_mode"] = "recursive"
    elif app._is_pro_mode():
        app.settings["pro_input_mode"] = "files"

    bootstrap_start_drop_load_async(
        app,
        files=files,
        dirs=dirs,
    )
    if ignored_count > 0:
        app.status_var.set(f"{app.status_var.get()} / 対象外 {ignored_count}件をスキップ")


def bootstrap_start_drop_load_async(
    app: Any,
    files: List[Path],
    dirs: List[Path],
    *,
    recursive_extensions: Sequence[str] = DROP_RECURSIVE_EXTENSIONS,
    selectable_input_extensions: Sequence[str] = (".png", ".jpg", ".jpeg", ".webp", ".avif"),
) -> None:
    if not files and not dirs:
        return

    file_load_start_drop(
        app,
        files=files,
        dirs=dirs,
        max_files=app._max_files_for_mode(app._is_pro_mode()),
        selectable_input_extensions=selectable_input_extensions,
        recursive_extensions=recursive_extensions,
    )


def bootstrap_begin_file_load_session(
    app: Any,
    mode_label: str,
    root_dir: Optional[Path],
    clear_existing_jobs: bool,
) -> None:
    file_load_begin_session(
        app,
        mode_label=mode_label,
        root_dir=root_dir,
        clear_existing_jobs=clear_existing_jobs,
        max_files=app._max_files_for_mode(app._is_pro_mode()),
    )


def bootstrap_select_files(app: Any, *, selectable_input_extensions: Sequence[str]) -> Tuple[List[Path], Optional[Path], bool]:
    if app._is_loading_files:
        messagebox.showinfo("処理中", "現在、画像読み込み処理中です。完了またはキャンセル後に再実行してください。")
        return [], None, False

    initial_dir = app.settings.get("last_input_dir", "")
    file_limit = app._max_files_for_mode(app._is_pro_mode())
    if app._is_pro_mode():
        paths, remembered_dir, started_async = bootstrap_select_files_in_pro_mode(
            app,
            initial_dir,
            selectable_input_extensions=selectable_input_extensions,
        )
        if started_async:
            return [], None, True
    else:
        paths, remembered_dir = bootstrap_select_files_in_simple_mode(
            initial_dir,
            max_files=file_limit,
            selectable_input_extensions=selectable_input_extensions,
        )
        started_async = False
    return paths, remembered_dir, started_async


def bootstrap_select_files_in_simple_mode(
    initial_dir: str,
    max_files: Optional[int],
    *,
    selectable_input_extensions: Sequence[str],
) -> Tuple[List[Path], Optional[Path]]:
    selected = filedialog.askopenfilenames(
        title="画像を選択",
        initialdir=initial_dir,
        filetypes=[("画像", " ".join(f"*.{ext.lstrip('.')}" for ext in selectable_input_extensions)), ("すべて", "*.*")],
    )
    if not selected:
        return [], None
    paths = [Path(p) for p in selected]
    if max_files is not None and len(paths) > max_files:
        messagebox.showwarning(
            "読み込み上限",
            f"選択した画像は {len(paths)} 枚ですが、モード上限 {max_files} 枚で制限して読み込みます。",
        )
        paths = paths[:max_files]
    return paths, paths[0].parent


def bootstrap_select_files_in_pro_mode(
    app: Any,
    initial_dir: str,
    *,
    selectable_input_extensions: Sequence[str],
) -> Tuple[List[Path], Optional[Path], bool]:
    saved_mode = bootstrap_normalized_pro_input_mode(str(app.settings.get("pro_input_mode", "recursive")))
    default_mode_text = "フォルダー再帰" if saved_mode == "recursive" else "ファイル個別"
    choice = messagebox.askyesnocancel(
        "画像選択（プロ）",
        "はい: フォルダーを再帰読み込み\n"
        "いいえ: ファイルを個別選択\n"
        f"キャンセル: 中止\n\n既定: {default_mode_text}",
        default="yes" if saved_mode == "recursive" else "no",
    )
    if choice is None:
        return [], None, False
    if choice is False:
        app.settings["pro_input_mode"] = "files"
        paths, remembered_dir = bootstrap_select_files_in_simple_mode(
            initial_dir,
            max_files=app._max_files_for_mode(is_pro=True),
            selectable_input_extensions=selectable_input_extensions,
        )
        return paths, remembered_dir, False

    app.settings["pro_input_mode"] = "recursive"
    root_dir_str = filedialog.askdirectory(
        title="対象フォルダーを選択（再帰）",
        initialdir=initial_dir,
    )
    if not root_dir_str:
        return [], None, False

    root_dir = Path(root_dir_str)
    bootstrap_start_recursive_load_async(app, root_dir=root_dir)
    return [], root_dir, True


def bootstrap_start_recursive_load_async(
    app: Any,
    root_dir: Path,
    *,
    recursive_extensions: Sequence[str] = DROP_RECURSIVE_EXTENSIONS,
) -> None:
    file_load_start_recursive(
        app,
        root_dir=root_dir,
        max_files=app._max_files_for_mode(is_pro=True),
        recursive_extensions=recursive_extensions,
    )


def bootstrap_start_retry_failed_load_async(app: Any, paths: List[Path]) -> None:
    file_load_start_retry_failed(app, paths=paths)


def bootstrap_on_select_change(
    app: Any,
    idx: Optional[int] = None,
    force: bool = False,
) -> None:
    if idx is None:
        if app._visible_job_indices:
            idx = app._visible_job_indices[0]
    if not isinstance(idx, int):
        return
    if idx >= len(app.jobs):
        return
    if app._visible_job_indices and idx not in app._visible_job_indices:
        return
    if (app.current_index == idx) and (not force):
        return

    previous_index = app.current_index
    if hasattr(app, "file_list_panel_refs"):
        apply_file_list_selection(
            app.file_list_panel_refs,
            previous_job_index=previous_index,
            current_job_index=idx,
            visible_job_indices=app._visible_job_indices,
            colors=bootstrap_resolve_app_colors(app),
        )
    app.current_index = idx

    previous_job = app.jobs[idx]
    now = datetime.now().strftime("%Y%m%d_%H%M%S")
    app.status_var.set(f"[{now}] {previous_job.path.name} を選択しました")
    logging.getLogger(__name__).info("Selected: %s", previous_job.path.name)

    app._reset_zoom()
    app._draw_previews(previous_job)
    app._update_metadata_preview(previous_job)
    app._refresh_status_indicators()


def bootstrap_preview_current(app: Any) -> None:
    if app._is_loading_files:
        messagebox.showinfo("処理中", "画像の読み込み中です。完了またはキャンセル後に実行してください。")
        return
    if app.current_index is None:
        messagebox.showwarning("ファイル未選択", "ファイルを選択してください")
        return
    app._start_async_preview(app.current_index)


def bootstrap_save_current(app: Any) -> None:
    if app._single_save_thread is not None and app._single_save_thread.is_alive():
        messagebox.showinfo("保存中", "既に保存処理中です。完了後に再実行してください。")
        return
    if app._is_loading_files:
        messagebox.showinfo("処理中", "画像の読み込み中です。完了またはキャンセル後に実行してください。")
        return
    if app.current_index is None:
        messagebox.showwarning("ファイル未選択", "ファイルを選択してください")
        return

    job = app.jobs[app.current_index]

    output_format = app._resolve_output_format_for_image(job.image)
    ext_default = destination_with_extension(Path(f"{job.path.stem}_resized"), output_format).suffix
    initial_dir = (
        app.settings.get("last_output_dir")
        or app.settings.get("default_output_dir")
        or Path.home()
    )
    initial_file = f"{job.path.stem}_resized{ext_default}"

    save_path_str = filedialog.asksaveasfilename(
        title="名前を付けて保存",
        initialdir=str(initial_dir),
        initialfile=initial_file,
        filetypes=build_single_save_filetypes(app.available_formats),
        defaultextension=ext_default,
    )
    if not save_path_str:
        return

    save_path = Path(save_path_str)
    save_path, normalized_message = normalize_windows_output_filename(
        save_path,
        reserved_names=app._reserved_names if hasattr(app, "_reserved_names") else set(),
    )
    if normalized_message is not None:
        if not messagebox.askyesno(
            "保存先名の調整",
            f"{normalized_message}\n\n保存先を以下に変更しますか？\n{save_path}",
            icon="warning",
        ):
            return

    app.settings["last_output_dir"] = str(save_path.parent)

    preflight_error = preflight_output_directory(
        save_path,
        create_if_missing=False,
        readable_os_error=presenter_build_readable_os_error,
    )
    if preflight_error is not None:
        messagebox.showerror("保存先エラー", preflight_error)
        return
    if is_windows_path_length_risky(save_path):
        result = messagebox.askyesno(
            "パス長警告",
            "保存先パスが長く、保存失敗の可能性があります。\n"
            "そのまま実行しますか？",
            icon="warning",
        )
        if not result:
            return

    options = build_save_options(
        app,
        output_format,
        exif_mode=app.exif_mode_var.get(),
    )
    if options is None:
        return

    app._single_save_version += 1
    version = app._single_save_version
    app._single_save_cancel_event.clear()
    app._begin_operation_scope(
        stage_text="保存中",
        cancel_text="停止中",
        cancel_command=app._cancel_active_operation,
        initial_progress=0.0,
    )

    source_image = job.image
    target_size = app._snapshot_resize_target(source_image.size)
    if not target_size:
        messagebox.showwarning("保存エラー", "リサイズ設定が無効です")
        return

    def worker() -> None:
        resized_for_save: Optional[Image.Image] = None
        try:
            resized_for_save = app._resize_image_to_target(source_image, target_size)
            if resized_for_save is None:
                raise RuntimeError("リサイズ設定が無効です")

            result, attempts = app._save_with_retry(
                source_image=source_image,
                resized_image=resized_for_save,
                output_path=save_path,
                options=options,
                allow_retry=app._is_pro_mode(),
                cancel_event=app._single_save_cancel_event,
            )
        except Exception as exc:  # pragma: no cover
            logging.exception("Unexpected error during single save")
            error = SaveResult(
                success=False,
                output_path=save_path,
                exif_mode=options.exif_mode,
                error=str(exc),
            )
            result = error
            attempts = 1

        def complete() -> None:
            try:
                if not app.winfo_exists():
                    return
            except Exception:
                return
            if version != app._single_save_version:
                return
            app._single_save_thread = None
            app._end_operation_scope()

            if not result.success:
                if result.error == "保存をキャンセルしました":
                    app.status_var.set("保存をキャンセルしました")
                    app._single_save_cancel_event.clear()
                    return

                job.last_process_state = "failed"
                retry_note = "（再試行あり）" if attempts > 1 else ""
                error_detail = result.error or "保存失敗"
                if result.error_guidance:
                    error_detail = f"{error_detail}\n{result.error_guidance}"
                job.last_error_detail = f"{error_detail}{retry_note}"
                app._populate_listbox()
                messagebox.showerror(
                    "保存エラー",
                    f"ファイルの保存に失敗しました:{' 再試行後' if attempts > 1 else ''}\n{error_detail}\n{build_exif_status_text(result)}",
                )
                return

            job.last_process_state = "success"
            job.last_error_detail = None
            if resized_for_save is not None:
                job.resized = resized_for_save
            if result.dry_run:
                msg = f"ドライラン完了: {result.output_path.name} を生成予定です"
            else:
                msg = f"{result.output_path.name} を保存しました"
            if attempts > 1:
                msg = f"{msg}（再試行後に成功）"
            msg = f"{msg}\n{build_exif_status_text(result)}"
            app._register_recent_setting_from_current()
            app._populate_listbox()
            app.status_var.set(msg)
            messagebox.showinfo("保存結果", msg)

        app.after(0, complete)

    app._single_save_thread = threading.Thread(
        target=worker,
        daemon=True,
        name="karuku-single-save",
    )
    app._single_save_thread.start()


def bootstrap_confirm_batch_save(
    app: Any,
    reference_job: Any,
    reference_target: Tuple[int, int],
    reference_format_label: str,
    batch_options: Any,
    output_dir: Path,
) -> bool:
    return messagebox.askokcancel(
        "一括適用保存の確認",
        f"基準画像: {reference_job.path.name}\n"
        f"適用サイズ: {reference_target[0]} x {reference_target[1]} px\n"
        f"出力形式: {reference_format_label}\n"
        f"モード: {build_batch_run_mode_text(batch_options.dry_run)}\n"
        f"EXIF: {app.exif_mode_var.get()} / GPS削除: {'ON' if app.remove_gps_var.get() else 'OFF'}\n"
        f"保存先: {output_dir}\n"
        f"対象枚数: {len(app.jobs)}枚\n\n"
        "読み込み済み全画像に同じ設定を適用して処理します。",
    )


def bootstrap_select_batch_output_dir(app: Any) -> Optional[Path]:
    initial_dir = (
        app.settings.get("last_output_dir")
        or app.settings.get("default_output_dir")
        or app.settings.get("last_input_dir")
        or Path.home()
    )
    output_dir_str = filedialog.askdirectory(title="保存先フォルダを選択", initialdir=str(initial_dir))
    if not output_dir_str:
        return None
    return Path(output_dir_str)


def bootstrap_prepare_batch_ui(app: Any) -> None:
    app._cancel_batch = False
    app._begin_operation_scope(
        stage_text="保存中",
        cancel_text="キャンセル",
        cancel_command=app._cancel_active_operation,
        initial_progress=0.0,
    )
    app._refresh_status_indicators()


def bootstrap_process_single_batch_job(
    app: Any,
    *,
    job: Any,
    output_dir: Path,
    reference_target: Tuple[int, int],
    reference_output_format: SaveFormat,
    batch_options: Any,
    stats: Any,
) -> None:
    resized_img: Optional[Any] = None
    try:
        resized_img = app._resize_image_to_target(job.image, reference_target)
        if not resized_img:
            job.last_process_state = "failed"
            job.last_error_detail = "リサイズ失敗"
            stats.record_failure(job.path.name, "リサイズ失敗", file_path=job.path)
            return

        out_base = build_unique_batch_base_path(
            output_dir=output_dir,
            stem=job.path.stem,
            output_format=reference_output_format,
            destination_with_extension_func=destination_with_extension,
            dry_run=batch_options.dry_run,
        )
        result, attempts = app._save_with_retry(
            source_image=job.image,
            resized_image=resized_img,
            output_path=out_base,
            options=batch_options,
            allow_retry=app._is_pro_mode(),
        )
        if result.success:
            job.last_process_state = "success"
            job.last_error_detail = None
            stats.record_success(result)
            return

        error_detail = result.error or "保存処理で不明なエラー"
        if result.error_guidance:
            error_detail = f"{error_detail}\n{result.error_guidance}"
        if attempts > 1:
            error_detail = f"{error_detail}（再試行後失敗）"
        job.last_process_state = "failed"
        job.last_error_detail = error_detail
        stats.record_failure(job.path.name, error_detail, file_path=job.path)
        logging.error("Failed to save %s", result.output_path)
    finally:
        if resized_img is not None:
            resized_img.close()


def bootstrap_run_batch_save(
    app: Any,
    *,
    output_dir: Path,
    reference_target: Tuple[int, int],
    reference_output_format: SaveFormat,
    batch_options: Any,
    target_jobs: Optional[List[Any]] = None,
) -> tuple[Any, int]:
    logging.warning(
        "bootstrap_run_batch_save: legacy sync path invoked. target_jobs=%s total=%d",
        "provided" if target_jobs is not None else "default",
        len(target_jobs) if target_jobs is not None else len(app.jobs),
    )
    stats = app._create_batch_stats()
    jobs_to_process = list(target_jobs) if target_jobs is not None else list(app.jobs)
    total_files = len(jobs_to_process)
    if hasattr(app, "_show_batch_processing_placeholders"):
        try:
            app._show_batch_processing_placeholders(total_files)
        except Exception:
            logging.exception("Failed to show batch processing placeholders")
    for job in jobs_to_process:
        job.last_process_state = "unprocessed"
        job.last_error_detail = None
    bootstrap_prepare_batch_ui(app)
    started_at = time.monotonic()
    try:
        for i, job in enumerate(jobs_to_process):
            if app._cancel_batch:
                break
            if hasattr(app, "_show_batch_processing_placeholders"):
                try:
                    app._show_batch_processing_placeholders(total_files, job.path.name, i + 1)
                except Exception:
                    logging.exception("Failed to update batch processing placeholders")
            try:
                bootstrap_process_single_batch_job(
                    app,
                    job=job,
                    output_dir=output_dir,
                    reference_target=reference_target,
                    reference_output_format=reference_output_format,
                    batch_options=batch_options,
                    stats=stats,
                )
            except Exception as e:
                job.last_process_state = "failed"
                job.last_error_detail = f"例外 {e}"
                stats.record_failure(job.path.name, f"例外 {e}", file_path=job.path)
                logging.exception("Unexpected error during batch save: %s", job.path)
            finally:
                done = i + 1
                app.progress_bar.set(done / total_files if total_files > 0 else 1.0)
                app.status_var.set(
                    build_batch_progress_status_text(
                        done_count=done,
                        total_count=total_files,
                        processed_count=stats.processed_count,
                        failed_count=stats.failed_count,
                        elapsed_sec=time.monotonic() - started_at,
                        current_file_name=job.path.name,
                        mode_text=build_batch_run_mode_text(dry_run=batch_options.dry_run),
                    )
                )
    finally:
        if hasattr(app, "_hide_batch_processing_placeholders"):
            try:
                app._hide_batch_processing_placeholders()
            except Exception:
                logging.exception("Failed to hide batch processing placeholders")
        app._end_operation_scope()
        app._populate_listbox()
        app._refresh_status_indicators()
    return stats, total_files


def bootstrap_run_batch_save_async(
    app: Any,
    *,
    output_dir: Path,
    reference_target: Tuple[int, int],
    reference_output_format: SaveFormat,
    batch_options: Any,
    target_jobs: Optional[List[Any]] = None,
    on_complete: Optional[Callable[[Any, int], None]] = None,
) -> threading.Thread:
    logging.info(
        "bootstrap_run_batch_save_async: invoked. target_jobs=%s total=%d output_dir=%s",
        "provided" if target_jobs is not None else "default",
        len(target_jobs) if target_jobs is not None else len(app.jobs),
        output_dir,
    )
    stats = app._create_batch_stats()
    jobs_to_process = list(target_jobs) if target_jobs is not None else list(app.jobs)
    total_files = len(jobs_to_process)
    for job in jobs_to_process:
        job.last_process_state = "unprocessed"
        job.last_error_detail = None

    progress_queue: "queue.Queue[tuple[str, Any]]" = queue.Queue()
    started_at = time.monotonic()

    def emit_progress(index: int, file_name: str) -> None:
        progress_queue.put(
            (
                "progress",
                index,
                file_name,
                stats.processed_count,
                stats.failed_count,
                time.monotonic() - started_at,
            )
        )

    def emit_processing(file_name: str, current_index: int) -> None:
        progress_queue.put(("processing", file_name, current_index))

    def worker() -> None:
        try:
            for i, job in enumerate(jobs_to_process):
                if app._cancel_batch:
                    break
                emit_processing(job.path.name, i + 1)
                try:
                    bootstrap_process_single_batch_job(
                        app,
                        job=job,
                        output_dir=output_dir,
                        reference_target=reference_target,
                        reference_output_format=reference_output_format,
                        batch_options=batch_options,
                        stats=stats,
                    )
                except Exception as e:
                    job.last_process_state = "failed"
                    job.last_error_detail = f"例外 {e}"
                    stats.record_failure(job.path.name, f"例外 {e}", file_path=job.path)
                    logging.exception("Unexpected error during batch save: %s", job.path)
                finally:
                    done = i + 1
                    emit_progress(done, job.path.name)
        finally:
            progress_queue.put(("done",))

    app._batch_save_thread = threading.Thread(
        target=worker,
        daemon=True,
        name="karuku-batch-save",
    )
    app._batch_save_thread.start()
    logging.info("bootstrap_run_batch_save_async: thread started: %s", app._batch_save_thread.name)

    def poll_queue() -> None:
        latest_progress = None
        latest_processing = None
        done_received = False
        try:
            while True:
                event = progress_queue.get_nowait()
                event_kind = event[0]
                if event_kind == "progress":
                    latest_progress = event
                elif event_kind == "processing":
                    latest_processing = event
                elif event_kind == "done":
                    done_received = True
        except queue.Empty:
            pass

        if done_received:
            app._batch_save_thread = None
            if hasattr(app, "_hide_batch_processing_placeholders"):
                try:
                    app._hide_batch_processing_placeholders()
                except Exception:
                    logging.exception("Failed to hide batch processing placeholders")
            app._end_operation_scope()
            app._populate_listbox()
            app._refresh_status_indicators()
            logging.info(
                "bootstrap_run_batch_save_async: done total=%d processed=%d failed=%d",
                total_files,
                stats.processed_count,
                stats.failed_count,
            )
            if on_complete is not None:
                on_complete(stats, total_files)
            return

        if latest_progress is not None:
            _, done_count, current_file_name, processed_count, failed_count, elapsed_sec = latest_progress
            app.progress_bar.set(done_count / total_files if total_files > 0 else 1.0)
            app.status_var.set(
                build_batch_progress_status_text(
                    done_count=done_count,
                    total_count=total_files,
                    processed_count=processed_count,
                    failed_count=failed_count,
                    elapsed_sec=elapsed_sec,
                    current_file_name=current_file_name,
                    mode_text=build_batch_run_mode_text(dry_run=batch_options.dry_run),
                )
            )

        if latest_processing is not None and hasattr(app, "_show_batch_processing_placeholders"):
            try:
                _, current_file_name, current_index = latest_processing
                app._show_batch_processing_placeholders(total_files, current_file_name, current_index)
            except Exception:
                logging.exception("Failed to update batch processing placeholders")

        if app._batch_save_thread is not None and app._batch_save_thread.is_alive():
            app.after(50, poll_queue)
        else:
            progress_queue.put(("done",))
            poll_queue()

    bootstrap_prepare_batch_ui(app)
    logging.info(
        "bootstrap_run_batch_save_async: UI prepared. cancel=%s",
        app._cancel_batch,
    )
    if hasattr(app, "_show_batch_processing_placeholders"):
        try:
            app._show_batch_processing_placeholders(total_files)
        except Exception:
            logging.exception("Failed to show batch processing placeholders")
    app.after(0, poll_queue)

    return app._batch_save_thread


def bootstrap_record_batch_run_summary(
    app: Any,
    *,
    stats: Any,
    output_dir: Path,
    selected_count: int,
    reference_job: Any,
    reference_target: Tuple[int, int],
    reference_format_label: str,
    batch_options: Any,
) -> None:
    entry = {
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "mode": "dry-run" if batch_options.dry_run else "save",
        "cancelled": bool(app._cancel_batch),
        "output_dir": str(output_dir),
        "reference_file": reference_job.path.name,
        "reference_target": {
            "width": reference_target[0],
            "height": reference_target[1],
        },
        "reference_format": reference_format_label,
        "totals": {
            "selected_count": selected_count,
            "processed_count": stats.processed_count,
            "failed_count": stats.failed_count,
            "dry_run_count": stats.dry_run_count,
            "exif_applied_count": stats.exif_applied_count,
            "exif_fallback_count": stats.exif_fallback_count,
            "gps_removed_count": stats.gps_removed_count,
        },
        "failed_files": list(stats.failed_details),
    }
    app._run_summary_payload["batch_runs"].append(entry)
    totals = app._run_summary_payload["totals"]
    totals["batch_run_count"] += 1
    totals["processed_count"] += stats.processed_count
    totals["failed_count"] += stats.failed_count
    totals["dry_run_count"] += stats.dry_run_count
    if app._cancel_batch:
        totals["cancelled_count"] += 1
    app._write_run_summary_safe()


def bootstrap_batch_save(app: Any) -> None:
    if app._is_loading_files:
        messagebox.showinfo("処理中", "画像の読み込み中です。完了またはキャンセル後に実行してください。")
        return
    if not app.jobs:
        messagebox.showwarning("ファイル未選択", "ファイルが選択されていません")
        return

    reference = app._resolve_batch_reference()
    if reference is None:
        messagebox.showwarning("設定エラー", "基準画像の設定が無効です")
        return
    reference_job, reference_target, reference_output_format = reference
    reference_format_label: str = {
        "jpeg": "JPEG",
        "png": "PNG",
        "webp": "WEBP",
        "avif": "AVIF",
    }.get(reference_output_format, str(reference_output_format).upper())
    batch_options = build_batch_save_options(
        app,
        reference_output_format,
        exif_mode=app._get_current_exif_mode() if hasattr(app, "_get_current_exif_mode") else app.exif_mode_var.get(),
    )
    if batch_options is None:
        return

    output_dir = bootstrap_select_batch_output_dir(app)
    if output_dir is None:
        return
    app.settings["last_output_dir"] = str(output_dir)
    output_dir_preflight = preflight_output_directory_only(
        output_dir,
        create_if_missing=True,
        readable_os_error=presenter_build_readable_os_error,
    )
    if output_dir_preflight is not None:
        messagebox.showerror("保存先エラー", output_dir_preflight)
        return
    if is_windows_path_length_risky(output_dir / "probe"):
        messagebox.showwarning(
            "パス長注意",
            "保存先パスが長い環境です。実行は継続しますが、必要に応じて保存先を短くしてください。",
        )

    if not bootstrap_confirm_batch_save(
        app,
        reference_job=reference_job,
        reference_target=reference_target,
        reference_format_label=reference_format_label,
        batch_options=batch_options,
        output_dir=output_dir,
    ):
        return
    logging.info("bootstrap_batch_save: using async flow")

    def _handle_batch_result(stats: Any, total_files: int) -> None:
        bootstrap_record_batch_run_summary(
            app,
            stats=stats,
            output_dir=output_dir,
            selected_count=total_files,
            reference_job=reference_job,
            reference_target=reference_target,
            reference_format_label=reference_format_label,
            batch_options=batch_options,
        )
        msg = build_batch_completion_message(
            total_files=total_files,
            processed_count=stats.processed_count,
            failed_count=stats.failed_count,
            exif_applied_count=stats.exif_applied_count,
            exif_fallback_count=stats.exif_fallback_count,
            gps_removed_count=stats.gps_removed_count,
            reference_job_name=reference_job.path.name,
            reference_target=reference_target,
            reference_format_label=reference_format_label,
            dry_run=batch_options.dry_run,
            batch_cancelled=app._cancel_batch,
            dry_run_count=stats.dry_run_count,
        )
        if stats.processed_count > 0:
            app._register_recent_setting_from_current()
        app.status_var.set(msg)
        retry_callback: Optional[Callable[[], None]] = None
        if stats.failed_paths and not app._cancel_batch:
            failed_path_set = {path for path in stats.failed_paths}

            def _retry_failed_batch_only() -> None:
                retry_jobs = [job for job in app.jobs if job.path in failed_path_set]
                if not retry_jobs:
                    messagebox.showinfo("再試行", "再試行対象の失敗ファイルが見つかりません。")
                    return

                def _handle_retry_result(retry_stats: Any, retry_total_files: int) -> None:
                    retry_msg = (
                        f"失敗再試行完了。成功: {retry_stats.processed_count}件 / "
                        f"失敗: {retry_stats.failed_count}件 / 対象: {retry_total_files}件"
                    )
                    app.status_var.set(retry_msg)
                    show_operation_result_dialog(
                        app,
                        colors=bootstrap_resolve_app_colors(app),
                        file_load_failure_preview_limit=FILE_LOAD_FAILURE_PREVIEW_LIMIT,
                        title="失敗再試行結果",
                        summary_text=retry_msg,
                        failed_details=retry_stats.failed_details,
                        retry_callback=None,
                    )

                bootstrap_run_batch_save_async(
                    app,
                    output_dir=output_dir,
                    reference_target=reference_target,
                    reference_output_format=reference_output_format,
                    batch_options=batch_options,
                    target_jobs=retry_jobs,
                    on_complete=_handle_retry_result,
                )

            retry_callback = _retry_failed_batch_only

        show_operation_result_dialog(
            app,
            colors=bootstrap_resolve_app_colors(app),
            file_load_failure_preview_limit=FILE_LOAD_FAILURE_PREVIEW_LIMIT,
            title="一括処理結果",
            summary_text=msg,
            failed_details=stats.failed_details,
            retry_callback=retry_callback,
        )

    bootstrap_run_batch_save_async(
        app,
        output_dir=output_dir,
        reference_target=reference_target,
        reference_output_format=reference_output_format,
        batch_options=batch_options,
        on_complete=_handle_batch_result,
    )


def bootstrap_cancel_batch_save(app: Any) -> None:
    app._cancel_batch = True
    app._set_operation_stage("キャンセル中")
