"""Validated simple image resizer GUI.

This version streamlines the UI so the user only chooses **how to specify size**
(ratio%, width, height, or explicit both).  All algorithm/format decisions are
handled automatically for best quality.

Usage:
    uv run python -m karuku_resizer.gui_app

A convenience CLI entry point `karuku-resizer` is also provided if installed as a package.
"""
from __future__ import annotations

import io
import json
import logging
import os
import platform
import queue
import math
import re
import subprocess
import sys
import threading
import time
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, List, Mapping, Optional, Tuple, cast
from tkinter import filedialog, messagebox, simpledialog

import customtkinter
from PIL import Image, ImageOps, ImageTk
try:
    from tkinterdnd2 import COPY, DND_FILES, TkinterDnD
    TKDND_AVAILABLE = True
except Exception:
    COPY = "copy"  # type: ignore[assignment]
    DND_FILES = "DND_Files"  # type: ignore[assignment]
    TkinterDnD = None  # type: ignore[assignment]
    TKDND_AVAILABLE = False

# ヘルプコンテンツとダイアログをインポート
from karuku_resizer.help_content import HELP_CONTENT, STEP_DESCRIPTIONS
from karuku_resizer.help_dialog import HelpDialog
from karuku_resizer.operation_flow import OperationScope, OperationScopeHooks
from karuku_resizer.gui_settings_store import GuiSettingsStore, default_gui_settings
from karuku_resizer.processing_preset_store import (
    ProcessingPreset,
    ProcessingPresetStore,
    merge_processing_values,
)
from karuku_resizer.image_save_pipeline import (
    ExifEditValues,
    SaveOptions,
    SaveFormat,
    ExifPreview,
    SaveResult,
    build_encoder_save_kwargs,
    destination_with_extension,
    normalize_avif_speed,
    normalize_quality,
    normalize_webp_method,
    preview_exif_plan,
    resolve_output_format,
    save_image,
    supported_output_formats,
)
from karuku_resizer.runtime_logging import (
    DEFAULT_MAX_FILES,
    DEFAULT_RETENTION_DAYS,
    RunLogArtifacts,
    create_run_log_artifacts,
    write_run_summary,
)
from karuku_resizer.tools.tooltip_manager import TooltipManager
from karuku_resizer.ui_tooltip_content import (
    ADVANCED_CONTROL_TOOLTIPS,
    ENTRY_AND_ACTION_TOOLTIPS,
    FILE_FILTER_VALUE_TOOLTIPS,
    SIZE_MODE_TOOLTIPS,
    TOP_AND_PRESET_TOOLTIPS,
    UI_MODE_VALUE_TOOLTIPS,
)
from karuku_resizer.icon_loader import load_icon
from karuku_resizer.ui_display_policy import (
    topbar_batch_button_text,
    topbar_density_for_width,
)
from karuku_resizer.ui_bootstrap import (
    bootstrap_apply_window_icon,
    bootstrap_apply_ui_scale_mode,
    bootstrap_canvas_background_color,
    bootstrap_canvas_label_color,
    bootstrap_create_initial_run_summary,
    bootstrap_ensure_run_log_handler,
    bootstrap_finalize_run_summary,
    bootstrap_normalize_appearance_mode,
    bootstrap_normalize_ui_scale_mode,
    bootstrap_resolve_system_font_family,
    bootstrap_resolve_icon_paths,
    bootstrap_scale_pad,
    bootstrap_scale_px,
    bootstrap_scale_topbar_widths,
    bootstrap_setup_keyboard_shortcuts,
    bootstrap_setup_ui_icons,
    bootstrap_style_card_frame,
    bootstrap_style_primary_button,
    bootstrap_style_secondary_button,
    bootstrap_runtime_base_dir,
    bootstrap_topbar_density_window_width,
    bootstrap_to_bool,
    bootstrap_write_run_summary_safe,
    setup_resize_app_layout,
    bootstrap_register_tooltip,
    bootstrap_register_segmented_value_tooltips,
    bootstrap_register_tooltip_by_name,
)
import karuku_resizer.ui_bootstrap as ui_bootstrap
from karuku_resizer.ui.main_layout import (
    begin_operation_scope as layout_begin_operation_scope,
    extract_metadata_text as layout_extract_metadata_text,
    build_operation_scope_hooks as layout_build_operation_scope_hooks,
    end_operation_scope as layout_end_operation_scope,
    refresh_status_indicators as layout_refresh_status_indicators,
    show_operation_stage as layout_show_operation_stage,
    hide_operation_stage as layout_hide_operation_stage,
    show_progress_with_cancel as layout_show_progress_with_cancel,
    hide_progress_with_cancel as layout_hide_progress_with_cancel,
    set_operation_stage as layout_set_operation_stage,
    update_session_summary as layout_update_session_summary,
)
from karuku_resizer.ui_main_panel import (
    output_format_labels as main_output_format_labels,
)
from karuku_resizer.ui_file_list_panel import (
    apply_file_list_selection,
    apply_empty_state_hint,
    refresh_file_list_panel,
    FileListRefs,
)
from karuku_resizer.ui_file_load_helpers import (
    dedupe_paths,
    is_selectable_input_file,
    normalize_dropped_path_text,
)
from karuku_resizer.ui_metadata_panel import (
    apply_metadata_preview,
    apply_metadata_expanded,
    apply_metadata_mode,
    apply_metadata_text,
    MetadataPanelRefs,
)
from karuku_resizer.ui_detail_controls import (
    apply_detail_panel_visibility,
    apply_output_controls_state_for_app,
    DetailEntryRefs,
    DetailFormRefs,
    DetailOutputRefs,
)
from karuku_resizer.ui_text_presenter import (
    build_batch_progress_status_text,
    build_batch_run_mode_text,
    build_empty_state_text,
    build_exif_preview_message,
    build_exif_status_text,
    build_load_error_detail,
    build_loading_hint_text,
    build_loading_progress_status_text,
    build_save_failure_hint,
    build_settings_summary_text,
    build_trim_preview_text,
    build_top_action_guide_text,
)
from karuku_resizer.ui.file_load_session import (
    handle_file_load_message as file_load_handle_message,
    poll_file_load_queue as file_load_poll_queue,
)
from karuku_resizer.ui.settings_header import (
    apply_recent_setting,
    normalize_recent_settings_entries,
    recent_setting_label_from_values,
    recent_settings_entries,
    recent_settings_fingerprint,
    register_recent_setting_from_current,
    register_setting_watchers,
    refresh_recent_settings_buttons,
)
from karuku_resizer.ui_settings_dialog import (
    SettingsDialogCallbacks,
    SettingsDialogMappings,
    SettingsDialogResult,
    SettingsDialogState,
    open_settings_dialog,
)
from karuku_resizer.ui.preset_dialog import open_preset_manager_dialog
from karuku_resizer.ui.result_dialog import show_operation_result_dialog
from karuku_resizer.ui_theme_tokens import TOPBAR_WIDTHS
from karuku_resizer.ui_main_panel import MainPanelRefs
from karuku_resizer.ui_preview_panel import PreviewPanelRefs
from karuku_resizer.ui_statusbar import StatusBarRefs

# Pillow ≥10 moves resampling constants to Image.Resampling
try:
    from PIL.Image import Resampling
except ImportError:  # Pillow<10 fallback
    class _Resampling:  # type: ignore
        LANCZOS = Image.LANCZOS  # type: ignore

    Resampling = _Resampling()  # type: ignore

DEFAULT_PREVIEW = 480
DEFAULT_WINDOW_GEOMETRY = "1200x800"
MIN_WINDOW_WIDTH = 1200
MIN_WINDOW_HEIGHT = 1
WINDOW_GEOMETRY_PATTERN = re.compile(r"^\s*(\d+)x(\d+)([+-]\d+[+-]\d+)?\s*$")
TOOLTIP_DELAY_MS = 400

# -------------------- UI color constants --------------------
METALLIC_COLORS = {
    # Accent
    "primary": ("#125FAF", "#2F7FC8"),
    "hover": ("#0F4E93", "#286CB0"),
    "accent_soft": ("#E8F3FF", "#1E2D40"),
    "pressed": ("#0F67C4", "#1F7DCF"),
    # Text
    "text_primary": ("#1F2A37", "#E8EEF5"),
    "text_secondary": ("#5B6878", "#A7B4C4"),
    "text_tertiary": ("#7A8696", "#7E8A9A"),
    # Background
    "bg_primary": ("#F4F7FB", "#12161D"),
    "bg_secondary": ("#FFFFFF", "#171C24"),
    "bg_tertiary": ("#EFF4FA", "#202835"),
    "input_bg": ("#FFFFFF", "#111723"),
    # Border
    "border_light": ("#D9E2EC", "#2A3340"),
    "border_medium": ("#CBD5E1", "#334155"),
    # Status
    "success": ("#2E8B57", "#3CA66A"),
    "warning": ("#C97A00", "#EF9A1A"),
    "error": ("#CC3344", "#E25A68"),
    # Canvas
    "canvas_bg": ("#EEF3FA", "#111722"),
}
ZOOM_STEP = 1.1
MIN_ZOOM = 0.2
MAX_ZOOM = 10.0
RESIZE_PREVIEW_DEBOUNCE_MS = 80
ZOOM_PREVIEW_DEBOUNCE_MS = 50
PREVIEW_ESTIMATION_SAMPLE_MAX_PIXELS = 800_000
PREVIEW_ESTIMATION_FAST_QUALITY = 75
PREVIEW_ESTIMATION_TIMEOUT_MS = 1500
QUALITY_VALUES = [str(v) for v in range(5, 101, 5)]
WEBP_METHOD_VALUES = [str(v) for v in range(0, 7)]
AVIF_SPEED_VALUES = [str(v) for v in range(0, 11)]
PRO_MODE_RECURSIVE_INPUT_EXTENSIONS = (".jpg", ".jpeg", ".png")
SELECTABLE_INPUT_EXTENSIONS = (".png", ".jpg", ".jpeg", ".webp", ".avif")
FILE_LOAD_FAILURE_PREVIEW_LIMIT = 20
RECENT_SETTINGS_MAX = 6
OPERATION_ONLY_CANCEL_HINT = "中止のみ可能"
SIMPLE_MODE_MAX_FILES_DEFAULT = 120
PRO_MODE_MAX_FILES_DEFAULT = 600
FILE_FILTER_LABEL_TO_ID = {
    "全件": "all",
    "失敗": "failed",
    "未処理": "unprocessed",
}
FILE_FILTER_ID_TO_LABEL = {v: k for k, v in FILE_FILTER_LABEL_TO_ID.items()}

FORMAT_LABEL_TO_ID = {
    "自動": "auto",
    "JPEG": "jpeg",
    "PNG": "png",
    "WEBP": "webp",
    "AVIF": "avif",
}

FORMAT_ID_TO_LABEL = {v: k for k, v in FORMAT_LABEL_TO_ID.items()}

EXIF_LABEL_TO_ID = {
    "保持": "keep",
    "編集": "edit",
    "削除": "remove",
}

EXIF_ID_TO_LABEL = {v: k for k, v in EXIF_LABEL_TO_ID.items()}

UI_MODE_LABEL_TO_ID = {
    "オフ": "simple",
    "オン（Pro）": "pro",
}

UI_MODE_ID_TO_LABEL = {v: k for k, v in UI_MODE_LABEL_TO_ID.items()}

APPEARANCE_LABEL_TO_ID = {
    "OSに従う": "system",
    "ライト": "light",
    "ダーク": "dark",
}

APPEARANCE_ID_TO_LABEL = {v: k for k, v in APPEARANCE_LABEL_TO_ID.items()}

UI_SCALE_LABEL_TO_ID = {
    "通常": "normal",
    "大きめ": "large",
}

UI_SCALE_ID_TO_LABEL = {v: k for k, v in UI_SCALE_LABEL_TO_ID.items()}
UI_SCALE_FACTORS = {
    "normal": 1.0,
    "large": 1.125,
}
UI_FONT_SIZE_PAIRS = {
    "normal": (16, 14),
    "large": (18, 16),
}
WINDOWS_RESERVED_NAMES = {
    "CON",
    "PRN",
    "AUX",
    "NUL",
    "COM1",
    "COM2",
    "COM3",
    "COM4",
    "COM5",
    "COM6",
    "COM7",
    "COM8",
    "COM9",
    "LPT1",
    "LPT2",
    "LPT3",
    "LPT4",
    "LPT5",
    "LPT6",
    "LPT7",
    "LPT8",
    "LPT9",
}

BIZ_UD_GOTHIC_FONT_CANDIDATES = [
    "BIZ UDPGothic",
    "BIZ UDPゴシック",
    "BIZ UDP Gothic",
    "BIZ UDGothic",
    "BIZ UDGothic M",
    "BIZ UDGothicM",
    "BIZ UDGothic B",
    "BIZ UDGothicB",
    "BIZ UDゴシック",
    "BIZ UDゴシック R",
    "BIZ UDゴシック M",
    "BIZ UDゴシックM",
    "BIZ UDGothicB",
    "BIZ UDGothic R",
]
BIZ_UD_GOTHIC_ASSET_FILES = (
    "BIZUDPGothic-Regular.ttf",
    "BIZUDPGothic-Bold.ttf",
    "BIZUDGothic-Regular.ttf",
    "BIZUDGothic-Bold.ttf",
)
BIZ_UD_GOTHIC_FALLBACK_FONT_FAMILIES = [
    "Yu Gothic",
    "Yu Gothic UI",
    "Meiryo",
    "MS PGothic",
    "Segoe UI",
]
NON_WINDOWS_FONT_FAMILIES = [
    "SF Pro Display",
    "Hiragino Kaku Gothic ProN",
    "Hiragino Kaku Gothic Pro",
    "Yu Gothic",
    "Meiryo",
]
PRO_INPUT_MODE_LABEL_TO_ID = {
    "フォルダ再帰": "recursive",
    "ファイル個別": "files",
}

PRO_INPUT_MODE_ID_TO_LABEL = {v: k for k, v in PRO_INPUT_MODE_LABEL_TO_ID.items()}
PRESET_NONE_LABEL = "未設定"
USER_PRESET_MAX = 6

EXIF_PREVIEW_TAGS = [
    ("メーカー", 0x010F),
    ("機種", 0x0110),
    ("レンズ", 0xA434),
    ("撮影日時", 0x9003),
    ("ISO", 0x8827),
    ("F値", 0x829D),
    ("露出時間", 0x829A),
    ("焦点距離", 0x920A),
    ("撮影者", 0x013B),
    ("著作権", 0x8298),
    ("コメント", 0x9286),
]

EXIF_GPS_INFO_TAG = 0x8825
LOG_APP_NAME = "KarukuResize"


@dataclass
class ImageJob:
    path: Path
    image: Image.Image
    resized: Optional[Image.Image] = None  # cache of last processed result
    preview_target_size: Optional[Tuple[int, int]] = None  # size used for resized cache
    preview_size_cache: Dict[Tuple[Any, ...], Tuple[float, bool]] = field(
        default_factory=dict,
    )
    source_size_bytes: int = 0
    metadata_loaded: bool = False
    metadata_text: str = ""
    metadata_error: Optional[str] = None
    last_process_state: str = "unprocessed"  # unprocessed / success / failed
    last_error_detail: Optional[str] = None


@dataclass
class BatchSaveStats:
    processed_count: int = 0
    failed_count: int = 0
    dry_run_count: int = 0
    exif_applied_count: int = 0
    exif_fallback_count: int = 0
    gps_removed_count: int = 0
    failed_details: List[str] = field(default_factory=list)
    failed_paths: List[Path] = field(default_factory=list)

    def record_success(self, result: SaveResult) -> None:
        self.processed_count += 1
        if result.dry_run:
            self.dry_run_count += 1
        if result.exif_attached:
            self.exif_applied_count += 1
        if result.exif_fallback_without_metadata:
            self.exif_fallback_count += 1
        if result.gps_removed:
            self.gps_removed_count += 1

    def record_failure(self, file_name: str, detail: str, file_path: Optional[Path] = None) -> None:
        self.failed_count += 1
        self.failed_details.append(f"{file_name}: {detail}")
        if file_path is not None:
            self.failed_paths.append(file_path)


DEBUG = False

logger = logging.getLogger(__name__)


class ResizeApp(customtkinter.CTk):
    # Runtime UI refs (bound by setup functions and ui modules)
    mode_segment: customtkinter.CTkSegmentedButton
    file_filter_segment: customtkinter.CTkSegmentedButton
    preset_menu: customtkinter.CTkOptionMenu
    preset_var: customtkinter.StringVar
    exif_mode_var: customtkinter.StringVar
    mode_var: customtkinter.StringVar
    pct_var: customtkinter.StringVar
    w_var: customtkinter.StringVar
    h_var: customtkinter.StringVar
    output_format_var: customtkinter.StringVar
    webp_lossless_var: customtkinter.BooleanVar
    dry_run_var: customtkinter.BooleanVar
    status_var: customtkinter.StringVar
    canvas_org: customtkinter.CTkCanvas
    canvas_resz: customtkinter.CTkCanvas
    exif_mode_menu: customtkinter.CTkOptionMenu
    quality_var: customtkinter.StringVar
    webp_method_var: customtkinter.StringVar
    avif_speed_var: customtkinter.StringVar
    settings_summary_var: customtkinter.StringVar
    file_list_panel_refs: FileListRefs
    metadata_panel_refs: MetadataPanelRefs
    mode_frames: Dict[str, customtkinter.CTkFrame]
    _entry_widgets: Dict[str, List[customtkinter.CTkEntry]]
    _all_entries: List[customtkinter.CTkEntry]
    main_content: customtkinter.CTkFrame
    file_list_frame: customtkinter.CTkFrame | customtkinter.CTkScrollableFrame
    info_orig_var: customtkinter.StringVar
    info_resized_var: customtkinter.StringVar
    resized_title_label: customtkinter.CTkLabel
    remove_gps_var: customtkinter.BooleanVar
    exif_artist_var: customtkinter.StringVar
    exif_copyright_var: customtkinter.StringVar
    exif_user_comment_var: customtkinter.StringVar
    exif_datetime_original_var: customtkinter.StringVar
    verbose_log_var: customtkinter.BooleanVar
    zoom_var: customtkinter.StringVar
    ratio_entry: customtkinter.CTkEntry
    entry_w_single: customtkinter.CTkEntry
    entry_h_single: customtkinter.CTkEntry
    entry_w_fixed: customtkinter.CTkEntry
    entry_h_fixed: customtkinter.CTkEntry
    exif_artist_entry: customtkinter.CTkEntry
    exif_copyright_entry: customtkinter.CTkEntry
    exif_comment_entry: customtkinter.CTkEntry
    exif_datetime_entry: customtkinter.CTkEntry
    file_filter_var: customtkinter.StringVar
    exif_preview_button: customtkinter.CTkButton
    open_log_folder_button: customtkinter.CTkButton
    output_format_menu: customtkinter.CTkOptionMenu
    quality_menu: customtkinter.CTkOptionMenu
    remove_gps_check: customtkinter.CTkCheckBox
    dry_run_check: customtkinter.CTkCheckBox
    verbose_log_check: customtkinter.CTkCheckBox
    webp_method_menu: customtkinter.CTkOptionMenu
    webp_lossless_check: customtkinter.CTkCheckBox
    avif_speed_menu: customtkinter.CTkOptionMenu
    select_button: customtkinter.CTkButton
    help_button: customtkinter.CTkButton
    settings_button: customtkinter.CTkButton
    preset_manage_button: customtkinter.CTkButton
    preview_button: customtkinter.CTkButton
    save_button: customtkinter.CTkButton
    clear_loaded_button: customtkinter.CTkButton
    batch_button: customtkinter.CTkButton
    details_toggle_button: customtkinter.CTkButton
    zoom_cb: customtkinter.CTkComboBox
    progress_bar: customtkinter.CTkProgressBar
    settings_summary_row: customtkinter.CTkFrame
    operation_stage_var: customtkinter.StringVar
    session_summary_var: customtkinter.StringVar
    _statusbar_refs: StatusBarRefs
    detail_form_refs: DetailFormRefs
    detail_entry_refs: DetailEntryRefs
    detail_output_refs: DetailOutputRefs
    main_panel_refs: MainPanelRefs
    preview_panel_refs: PreviewPanelRefs
    font_default: customtkinter.CTkFont
    font_small: customtkinter.CTkFont
    font_bold: customtkinter.CTkFont
    font_resized_info: customtkinter.CTkFont

    def __init__(self) -> None:
        super().__init__()

        self._to_bool = bootstrap_to_bool
        self._normalize_appearance_mode = lambda value: bootstrap_normalize_appearance_mode(
            value,
            APPEARANCE_ID_TO_LABEL,
            APPEARANCE_LABEL_TO_ID,
        )
        self._normalize_ui_scale_mode = lambda value: bootstrap_normalize_ui_scale_mode(
            value,
            UI_SCALE_ID_TO_LABEL,
            UI_SCALE_LABEL_TO_ID,
        )
        self._apply_ui_scale_mode = self._apply_scaled_fonts
        self._style_primary_button = lambda button: bootstrap_style_primary_button(
            button,
            colors=METALLIC_COLORS,
        )
        self._style_secondary_button = lambda button: bootstrap_style_secondary_button(
            button,
            colors=METALLIC_COLORS,
        )
        self._style_card_frame = lambda frame, corner_radius=12: bootstrap_style_card_frame(
            frame,
            colors=METALLIC_COLORS,
            corner_radius=corner_radius,
        )
        self._canvas_background_color = bootstrap_canvas_background_color
        self._canvas_label_color = bootstrap_canvas_label_color
        self._app_colors = METALLIC_COLORS
        self._scale_px = lambda value: bootstrap_scale_px(self, value)
        self._scale_pad = lambda value: bootstrap_scale_pad(self, value)
        self._scale_topbar_widths = lambda density: bootstrap_scale_topbar_widths(
            self,
            density=density,
            topbar_widths=TOPBAR_WIDTHS,
        )
        self._topbar_density_window_width = (
            lambda window_width: bootstrap_topbar_density_window_width(
                window_width=window_width,
                scale_factor=self._ui_scale_factor if hasattr(self, "_ui_scale_factor") else 1.0,
            )
        )
        self._setup_keyboard_shortcuts = lambda: bootstrap_setup_keyboard_shortcuts(
            self,
            preview_action=self._preview_current,
            save_action=self._save_current,
            batch_action=self._batch_save,
        )
        self._recent_setting_label_from_values = lambda values: recent_setting_label_from_values(
            values,
            merge_processing_values_fn=merge_processing_values,
            format_id_to_label=FORMAT_ID_TO_LABEL,
        )
        self._recent_settings_fingerprint = lambda values: recent_settings_fingerprint(
            values,
            merge_processing_values_fn=merge_processing_values,
        )
        self._normalize_recent_settings_entries = (
            lambda raw: normalize_recent_settings_entries(
                raw,
                recent_settings_max=RECENT_SETTINGS_MAX,
                merge_processing_values_fn=merge_processing_values,
                recent_settings_fingerprint_fn=self._recent_settings_fingerprint,
                recent_setting_label_fn=self._recent_setting_label_from_values,
            )
        )
        self._create_initial_run_summary = lambda: bootstrap_create_initial_run_summary(
            self,
            log_app_name=LOG_APP_NAME,
        )
        self._write_run_summary_safe = lambda: bootstrap_write_run_summary_safe(self)
        self._finalize_run_summary = lambda: bootstrap_finalize_run_summary(self)
        self._ensure_run_log_handler = lambda: bootstrap_ensure_run_log_handler(self)
        self._register_tooltip = lambda widget, text: bootstrap_register_tooltip(
            self,
            widget,
            text,
        )
        self._register_segmented_value_tooltips = lambda segmented, text_by_value: bootstrap_register_segmented_value_tooltips(
            self,
            segmented,
            text_by_value,
        )
        self._register_tooltip_by_name = (
            lambda attr_name, text: bootstrap_register_tooltip_by_name(self, attr_name, text)
        )

        # 設定マネージャー初期化
        self.settings_store = GuiSettingsStore()
        self.settings = self.settings_store.load()
        self.settings["show_tooltips"] = bootstrap_to_bool(self.settings.get("show_tooltips", True))
        self.available_formats = supported_output_formats()
        self.preset_store = ProcessingPresetStore()
        self.processing_presets: List[ProcessingPreset] = self.preset_store.load()
        self._preset_name_to_id: Dict[str, str] = {}

        # --- Theme ---
        customtkinter.set_appearance_mode("system")
        customtkinter.set_default_color_theme("blue")
        self.configure(fg_color=METALLIC_COLORS["bg_primary"])

        # -------------------- フォント設定 --------------------
        # フォント設定（WindowsはBIZ UDゴシック優先。未検出時はOS既定へフォールバック）
        self._system_font = bootstrap_resolve_system_font_family(
            system_font_candidates=BIZ_UD_GOTHIC_FONT_CANDIDATES,
            font_asset_files=BIZ_UD_GOTHIC_ASSET_FILES,
            fallback_font_families=BIZ_UD_GOTHIC_FALLBACK_FONT_FAMILIES,
            non_windows_font_families=NON_WINDOWS_FONT_FAMILIES,
        )
        self._ui_scale_mode = self._normalize_ui_scale_mode(self.settings.get("ui_scale_mode", "normal"))
        self._apply_ui_scale_mode(self._ui_scale_mode)

        self.title("画像リサイズツール (DEBUG)" if DEBUG else "画像リサイズツール")
        self.minsize(MIN_WINDOW_WIDTH, MIN_WINDOW_HEIGHT)
        self._window_icon_image: Optional[ImageTk.PhotoImage] = None
        bootstrap_apply_window_icon(self, load_icon_paths=bootstrap_resolve_icon_paths)
        bootstrap_setup_ui_icons(self, icon_loader=load_icon)
        self._tooltip_manager = TooltipManager(
            self,
            enabled_provider=lambda: bootstrap_to_bool(self.settings.get("show_tooltips", True)),
            delay_ms=TOOLTIP_DELAY_MS,
        )

        # 例外を握りつぶさず、GUI上で明示してログへ残す
        self.report_callback_exception = self._report_callback_exception
        
        # ウィンドウ閉じる時のイベント
        self.protocol("WM_DELETE_WINDOW", self._on_closing)

        self.jobs: List[ImageJob] = []
        self.current_index: Optional[int] = None
        self._visible_job_indices: List[int] = []
        self._cancel_batch = False
        self._is_loading_files = False
        self._file_load_cancel_event = threading.Event()
        self._file_load_queue: "queue.Queue[Dict[str, Any]]" = queue.Queue(maxsize=8)
        self._file_load_after_id: Optional[str] = None
        self._file_load_total_candidates = 0
        self._file_load_loaded_count = 0
        self._file_load_failed_details: List[str] = []
        self._file_load_failed_paths: List[Path] = []
        self._file_load_limited = False
        self._file_load_limit = 0
        self._file_load_root_dir: Optional[Path] = None
        self._file_load_mode_label = "再帰読み込み"
        self._file_scan_started_at = 0.0
        self._file_load_started_at = 0.0
        self._file_scan_pulse = 0.0
        self._drag_drop_enabled = False
        self._settings_dialog: Optional[customtkinter.CTkToplevel] = None
        self._preset_dialog: Optional[customtkinter.CTkToplevel] = None
        self._result_dialog: Optional[customtkinter.CTkToplevel] = None
        self._operation_scope: Optional[OperationScope] = None
        self._action_hint_reason = ""
        self._auto_preview_after_id: Optional[str] = None
        self._recent_setting_buttons: List[customtkinter.CTkButton] = []
        self._run_log_artifacts: RunLogArtifacts = create_run_log_artifacts(
            app_name=LOG_APP_NAME,
            retention_days=DEFAULT_RETENTION_DAYS,
            max_files=DEFAULT_MAX_FILES,
        )
        self._recent_settings_max = RECENT_SETTINGS_MAX
        self._run_summary_payload = self._create_initial_run_summary()
        self._run_summary_finalized = False
        self._topbar_density = "normal"
        self._topbar_controller: Any = None
        self._ui_scale_factor = UI_SCALE_FACTORS.get(self._ui_scale_mode, 1.0)
        self._batch_preview_placeholder_active = False
        self._batch_placeholder_items: Dict[customtkinter.CTkCanvas, Tuple[Optional[int], Optional[int]]] = {}
        self._single_preview_placeholder_active = False
        self._single_preview_placeholder_items: Dict[customtkinter.CTkCanvas, Tuple[Optional[int], Optional[int]]] = {}
        self._single_preview_placeholder_version = 0
        self._single_save_thread: Optional[threading.Thread] = None
        self._single_save_cancel_event = threading.Event()
        self._single_save_version = 0
        self._preview_draw_after_id: Optional[str] = None
        self._preview_thread: Optional[threading.Thread] = None
        self._preview_version = 0
        self._size_estimation_version = 0
        self._size_estimation_inflight_key: Optional[Tuple[Any, ...]] = None
        self._size_estimation_timeout_id: Optional[str] = None
        self.appearance_mode_var = customtkinter.StringVar(
            value=APPEARANCE_ID_TO_LABEL.get(
                self._normalize_appearance_mode(self.settings.get("appearance_mode", "system")),
                "OSに従う",
            )
        )
        self.ui_mode_var = customtkinter.StringVar(
            value=UI_MODE_ID_TO_LABEL.get(
                str(self.settings.get("ui_mode", "simple")),
                "オフ",
            )
        )
        self._suppress_preset_menu_callback = True
        self._setup_ui()
        self._setup_tooltips()
        self._setup_keyboard_shortcuts()
        self._setup_drag_and_drop()
        self._refresh_preset_menu(selected_preset_id=self.settings.get("default_preset_id", ""))
        self._restore_settings()
        self._apply_default_preset_if_configured()
        self._suppress_preset_menu_callback = False
        self._apply_log_level()
        self._write_run_summary_safe()

        self.after(0, self._update_mode)  # set initial enable states
        self.after(0, self._refresh_status_indicators)
        logging.info("ResizeApp initialized")
        logging.info("Run log: %s", self._run_log_artifacts.run_log_path)
        logging.info("Run summary: %s", self._run_log_artifacts.summary_path)

    def _apply_scaled_fonts(self, mode_id: str) -> None:
        normalized = self._normalize_ui_scale_mode(mode_id)
        bootstrap_apply_ui_scale_mode(
            self,
            normalized,
            UI_SCALE_FACTORS,
            UI_FONT_SIZE_PAIRS,
        )
        _default_size, small_size = UI_FONT_SIZE_PAIRS.get(normalized, (16, 14))
        self.font_resized_info = customtkinter.CTkFont(
            family=self._system_font,
            size=max(1, small_size - 1),
            weight="normal",
        )

    def _setup_tooltips(self) -> None:
        for attr_name, text in TOP_AND_PRESET_TOOLTIPS.items():
            self._register_tooltip_by_name(attr_name, text)

        self._register_segmented_value_tooltips(
            self.mode_segment,
            dict(zip(["比率 %", "幅 px", "高さ px", "幅×高"], SIZE_MODE_TOOLTIPS)),
        )

        for attr_name, text in ENTRY_AND_ACTION_TOOLTIPS.items():
            self._register_tooltip_by_name(attr_name, text)

        for attr_name, text in ADVANCED_CONTROL_TOOLTIPS.items():
            self._register_tooltip_by_name(attr_name, text)

        ui_mode_segment = getattr(self, "ui_mode_segment", None)
        if ui_mode_segment is not None:
            self._register_segmented_value_tooltips(
                ui_mode_segment,
                UI_MODE_VALUE_TOOLTIPS,
            )
        self._register_segmented_value_tooltips(
            self.file_filter_segment,
            FILE_FILTER_VALUE_TOOLTIPS,
        )

    def _refresh_preset_menu(self, selected_preset_id: Optional[str] = None) -> None:
        label_to_id: Dict[str, str] = {}
        labels: List[str] = []
        for preset in self.processing_presets:
            base_label = preset.name.strip() or preset.preset_id
            if preset.is_builtin:
                base_label = f"標準 {base_label}"
            label = base_label
            suffix_index = 2
            while label in label_to_id:
                label = f"{base_label} ({suffix_index})"
                suffix_index += 1
            labels.append(label)
            label_to_id[label] = preset.preset_id

        if not labels:
            labels = [PRESET_NONE_LABEL]

        self._preset_name_to_id = label_to_id
        if hasattr(self, "preset_menu"):
            self.preset_menu.configure(values=labels)

        if selected_preset_id:
            self._set_selected_preset_label_by_id(selected_preset_id)
            return

        current_label = self.preset_var.get() if hasattr(self, "preset_var") else PRESET_NONE_LABEL
        if current_label in labels:
            self._set_selected_preset_label(current_label)
        else:
            self._set_selected_preset_label(labels[0])

    def _set_selected_preset_label_by_id(self, preset_id: str) -> None:
        for label, mapped_id in self._preset_name_to_id.items():
            if mapped_id == preset_id:
                self._set_selected_preset_label(label)
                return
        if self._preset_name_to_id:
            self._set_selected_preset_label(next(iter(self._preset_name_to_id.keys())))
        else:
            self._set_selected_preset_label(PRESET_NONE_LABEL)

    def _selected_preset_id(self) -> str:
        return self._preset_name_to_id.get(self.preset_var.get(), "")

    def _preset_label_for_id(self, preset_id: str, fallback: str = PRESET_NONE_LABEL) -> str:
        for label, mapped_id in self._preset_name_to_id.items():
            if mapped_id == preset_id:
                return label
        return fallback

    def _preset_labels_with_none(self) -> List[str]:
        labels = [PRESET_NONE_LABEL]
        labels.extend(self._preset_name_to_id.keys())
        return labels

    def _get_preset_by_id(self, preset_id: str) -> Optional[ProcessingPreset]:
        if not preset_id:
            return None
        for preset in self.processing_presets:
            if preset.preset_id == preset_id:
                return preset
        return None

    def _user_presets(self) -> List[ProcessingPreset]:
        return [preset for preset in self.processing_presets if not preset.is_builtin]

    def _persist_user_presets(
        self,
        user_presets: List[ProcessingPreset],
        *,
        selected_preset_id: Optional[str] = None,
    ) -> None:
        selected_id = selected_preset_id or self._selected_preset_id()
        self.preset_store.save_users(user_presets)
        self.processing_presets = self.preset_store.load()
        if selected_id and self._get_preset_by_id(selected_id) is None:
            selected_id = ""
        if not selected_id and self.processing_presets:
            selected_id = self.processing_presets[0].preset_id
        self._refresh_preset_menu(selected_preset_id=selected_id)

        default_preset_id = str(self.settings.get("default_preset_id", "")).strip()
        if default_preset_id and self._get_preset_by_id(default_preset_id) is None:
            self.settings["default_preset_id"] = ""
            self._save_current_settings()

    def _select_user_preset_to_replace(
        self,
        user_presets: List[ProcessingPreset],
        *,
        parent: Optional[customtkinter.CTkToplevel] = None,
    ) -> Optional[ProcessingPreset]:
        choices = [preset.name for preset in user_presets]
        hint = "\n".join(f"- {name}" for name in choices)
        while True:
            selected_name = simpledialog.askstring(
                "プリセット上限",
                f"ユーザープリセットは最大{USER_PRESET_MAX}件です。\n"
                "置き換える既存プリセット名を入力してください。\n\n"
                f"{hint}",
                parent=parent or self,
            )
            if selected_name is None:
                return None
            selected_name = selected_name.strip()
            target = next((preset for preset in user_presets if preset.name == selected_name), None)
            if target is not None:
                return target
            messagebox.showwarning(
                "プリセット上限",
                "入力された名前のプリセットが見つかりませんでした。",
                parent=parent or self,
            )

    def _capture_current_processing_values(
        self,
        *,
        require_valid_exif_datetime: bool = False,
        warning_parent: Optional[customtkinter.CTkToplevel] = None,
    ) -> Optional[dict[str, Any]]:
        edit_values = self._current_exif_edit_values(
            show_warning=require_valid_exif_datetime,
            strict=require_valid_exif_datetime,
            warning_parent=warning_parent,
        )
        if EXIF_LABEL_TO_ID.get(self.exif_mode_var.get(), "keep") == "edit" and edit_values is None:
            return None
        if edit_values is None:
            edit_values = ExifEditValues()
        return merge_processing_values(
            {
                "mode": self.mode_var.get(),
                "ratio_value": self.pct_var.get(),
                "width_value": self.w_var.get(),
                "height_value": self.h_var.get(),
                "quality": str(self._current_quality()),
                "output_format": FORMAT_LABEL_TO_ID.get(self.output_format_var.get(), "auto"),
                "webp_method": str(self._current_webp_method()),
                "webp_lossless": self.webp_lossless_var.get(),
                "avif_speed": str(self._current_avif_speed()),
                "dry_run": self.dry_run_var.get(),
                "exif_mode": EXIF_LABEL_TO_ID.get(self.exif_mode_var.get(), "keep"),
                "remove_gps": self.remove_gps_var.get(),
                "exif_artist": edit_values.artist or "",
                "exif_copyright": edit_values.copyright_text or "",
                "exif_user_comment": edit_values.user_comment or "",
                "exif_datetime_original": edit_values.datetime_original or "",
            }
        )

    def _apply_processing_values(self, values: Mapping[str, Any]) -> None:
        merged = merge_processing_values(values)

        mode = str(merged.get("mode", "ratio"))
        if mode not in {"ratio", "width", "height", "fixed"}:
            mode = "ratio"
        self.mode_var.set(mode)
        self.pct_var.set(str(merged.get("ratio_value", "100")))
        self.w_var.set(str(merged.get("width_value", "")))
        self.h_var.set(str(merged.get("height_value", "")))

        try:
            quality = normalize_quality(int(merged.get("quality", 85)))
        except (TypeError, ValueError):
            quality = 85
        self.quality_var.set(str(quality))

        output_format_id = str(merged.get("output_format", "auto")).lower()
        if output_format_id not in FORMAT_ID_TO_LABEL:
            output_format_id = "auto"
        output_label = FORMAT_ID_TO_LABEL.get(output_format_id, "自動")
        if output_label not in main_output_format_labels(self.available_formats):
            output_label = "自動"
        self.output_format_var.set(output_label)

        try:
            webp_method = normalize_webp_method(int(merged.get("webp_method", 6)))
        except (TypeError, ValueError):
            webp_method = 6
        self.webp_method_var.set(str(webp_method))
        self.webp_lossless_var.set(self._to_bool(merged.get("webp_lossless", False)))

        try:
            avif_speed = normalize_avif_speed(int(merged.get("avif_speed", 6)))
        except (TypeError, ValueError):
            avif_speed = 6
        self.avif_speed_var.set(str(avif_speed))

        self.dry_run_var.set(self._to_bool(merged.get("dry_run", False)))

        exif_mode_id = str(merged.get("exif_mode", "keep")).lower()
        if exif_mode_id not in EXIF_ID_TO_LABEL:
            exif_mode_id = "keep"
        if exif_mode_id == "edit" and not self._is_pro_mode():
            self.ui_mode_var.set("プロ")
        self.exif_mode_var.set(EXIF_ID_TO_LABEL.get(exif_mode_id, "保持"))
        self.remove_gps_var.set(self._to_bool(merged.get("remove_gps", False)))
        self.exif_artist_var.set(str(merged.get("exif_artist", "")))
        self.exif_copyright_var.set(str(merged.get("exif_copyright", "")))
        self.exif_user_comment_var.set(str(merged.get("exif_user_comment", "")))
        self.exif_datetime_original_var.set(str(merged.get("exif_datetime_original", "")))

        self._update_mode()
        self._apply_ui_mode()
        self._on_output_format_changed(self.output_format_var.get())
        self._on_quality_changed(self.quality_var.get())
        self._on_exif_mode_changed(self.exif_mode_var.get())
        self._update_settings_summary()

        if self.current_index is not None and self.current_index < len(self.jobs):
            self._draw_previews(self.jobs[self.current_index])

    def _apply_preset_by_id(self, preset_id: str, *, announce: bool = True, persist: bool = True) -> bool:
        preset = self._get_preset_by_id(preset_id)
        if preset is None:
            return False

        if not preset.is_builtin:
            preset.last_used_at = datetime.now().isoformat(timespec="seconds")
            self._persist_user_presets(self._user_presets(), selected_preset_id=preset.preset_id)
            refreshed = self._get_preset_by_id(preset.preset_id)
            if refreshed is not None:
                preset = refreshed

        self._apply_processing_values(preset.values)
        self._set_selected_preset_label_by_id(preset.preset_id)
        if persist:
            self._save_current_settings()
        if announce:
            self.status_var.set(f"プリセット適用: {preset.name}")
        return True

    def _set_selected_preset_label(self, label: str) -> None:
        if not hasattr(self, "preset_var"):
            return
        previous_suppression = self._suppress_preset_menu_callback
        self._suppress_preset_menu_callback = True
        self.preset_var.set(label)
        self._suppress_preset_menu_callback = previous_suppression

    def _on_preset_menu_changed(self, _value: str) -> None:
        if self._suppress_preset_menu_callback:
            return
        preset_id = self._selected_preset_id()
        if not preset_id:
            return
        self._apply_preset_by_id(preset_id, announce=True, persist=True)

    def _apply_selected_preset(self) -> None:
        preset_id = self._selected_preset_id()
        if not preset_id:
            messagebox.showinfo("プリセット", "適用するプリセットを選択してください。")
            return
        if not self._apply_preset_by_id(preset_id, announce=True, persist=True):
            messagebox.showerror("プリセット", "選択されたプリセットを適用できませんでした。")

    def _apply_default_preset_if_configured(self) -> None:
        preset_id = str(self.settings.get("default_preset_id", "")).strip()
        if not preset_id:
            return
        if self._apply_preset_by_id(preset_id, announce=False, persist=False):
            preset = self._get_preset_by_id(preset_id)
            if preset is not None:
                self.status_var.set(f"既定プリセット適用: {preset.name}")
            return

        self.settings["default_preset_id"] = ""
        self._save_current_settings()

    def _save_current_as_preset(self) -> None:
        if self._is_loading_files:
            messagebox.showinfo("処理中", "画像読み込み中はプリセット保存できません。")
            return

        initial_name = ""
        selected_preset = self._get_preset_by_id(self._selected_preset_id())
        if selected_preset is not None and not selected_preset.is_builtin:
            initial_name = selected_preset.name

        name = simpledialog.askstring(
            "プリセット保存",
            "プリセット名を入力してください。",
            parent=self,
            initialvalue=initial_name,
        )
        if name is None:
            return
        name = name.strip()
        if not name:
            messagebox.showwarning("プリセット保存", "プリセット名を入力してください。")
            return

        captured_values = self._capture_current_processing_values(require_valid_exif_datetime=True)
        if captured_values is None:
            return
        now = datetime.now().isoformat(timespec="seconds")
        user_presets = self._user_presets()
        existing = next((preset for preset in user_presets if preset.name == name), None)
        if existing is not None:
            overwrite = messagebox.askyesno(
                "プリセット保存",
                f"同名のプリセット「{name}」があります。上書きしますか？",
            )
            if not overwrite:
                return
            existing.values = merge_processing_values(captured_values)
            existing.updated_at = now
            target_id = existing.preset_id
            status_text = f"プリセット更新: {name}"
        else:
            if len(user_presets) >= USER_PRESET_MAX:
                replace_target = self._select_user_preset_to_replace(user_presets)
                if replace_target is None:
                    return
                if not messagebox.askyesno(
                    "プリセット置換",
                    f"「{replace_target.name}」を「{name}」で置き換えますか？",
                ):
                    return
                if any(
                    preset.preset_id != replace_target.preset_id and preset.name == name
                    for preset in user_presets
                ):
                    messagebox.showwarning(
                        "プリセット保存",
                        f"同名のユーザープリセット「{name}」が既に存在します。",
                    )
                    return
                replace_target.name = name
                replace_target.description = ""
                replace_target.values = merge_processing_values(captured_values)
                replace_target.updated_at = now
                target_id = replace_target.preset_id
                status_text = f"プリセット置換: {name}"
            else:
                new_preset = ProcessingPresetStore.new_user_preset(
                    name=name,
                    description="",
                    values=captured_values,
                    existing_ids=[preset.preset_id for preset in self.processing_presets],
                )
                user_presets.append(new_preset)
                target_id = new_preset.preset_id
                status_text = f"プリセット保存: {name}"

        self._persist_user_presets(user_presets, selected_preset_id=target_id)
        self._set_selected_preset_label_by_id(target_id)
        self._save_current_settings()
        self.status_var.set(status_text)

    def _open_preset_manager_dialog(self) -> None:
        open_preset_manager_dialog(
            self,
            colors=METALLIC_COLORS,
            format_id_to_label=FORMAT_ID_TO_LABEL,
            exif_id_to_label=EXIF_ID_TO_LABEL,
            preset_none_label=PRESET_NONE_LABEL,
        )

    @staticmethod
    def _normalize_dropped_path_text(value: str) -> str:
        return normalize_dropped_path_text(value)

    @staticmethod
    def _dedupe_paths(paths: List[Path]) -> List[Path]:
        return dedupe_paths(paths)

    @staticmethod
    def _is_selectable_input_file(path: Path) -> bool:
        return is_selectable_input_file(path, selectable_exts=SELECTABLE_INPUT_EXTENSIONS)

    @staticmethod
    def _recent_setting_label_from_values(values: Mapping[str, Any]) -> str:
        return recent_setting_label_from_values(
            values,
            merge_processing_values_fn=merge_processing_values,
            format_id_to_label=FORMAT_ID_TO_LABEL,
        )

    @staticmethod
    def _recent_settings_fingerprint(values: Mapping[str, Any]) -> str:
        return recent_settings_fingerprint(
            values,
            merge_processing_values_fn=merge_processing_values,
        )

    @staticmethod
    def _merge_processing_values(values: Mapping[str, Any]) -> Mapping[str, Any]:
        return merge_processing_values(values)

    @staticmethod
    def _normalize_recent_settings_entries(raw: Any) -> List[Dict[str, Any]]:
        return normalize_recent_settings_entries(
            raw,
            recent_settings_max=RECENT_SETTINGS_MAX,
            merge_processing_values_fn=merge_processing_values,
            recent_settings_fingerprint_fn=ResizeApp._recent_settings_fingerprint,
            recent_setting_label_fn=ResizeApp._recent_setting_label_from_values,
        )

    @staticmethod
    def _discover_recursive_image_paths(root_dir: Path) -> List[Path]:
        return ui_bootstrap.bootstrap_discover_recursive_image_paths(root_dir)

    def _setup_ui(self):
        """UI要素をセットアップ"""
        setup_resize_app_layout(
            self,
            colors=METALLIC_COLORS,
            available_formats=self.available_formats,
            file_filter_values=list(FILE_FILTER_LABEL_TO_ID.keys()),
            quality_values=QUALITY_VALUES,
            webp_method_values=WEBP_METHOD_VALUES,
            avif_speed_values=AVIF_SPEED_VALUES,
            preset_none_label=PRESET_NONE_LABEL,
            initial_canvas_size=(DEFAULT_PREVIEW, DEFAULT_PREVIEW),
        )
        register_setting_watchers(self, self._on_setting_var_changed)
        self._refresh_status_indicators()
        apply_output_controls_state_for_app(
            self,
            output_format_to_id=FORMAT_LABEL_TO_ID,
            exif_label_to_id=EXIF_LABEL_TO_ID,
        )

    def _max_files_for_mode(self, is_pro: bool) -> int:
        raw = self.settings.get("max_files_pro_mode" if is_pro else "max_files_simple_mode")
        if raw is None:
            return PRO_MODE_MAX_FILES_DEFAULT if is_pro else SIMPLE_MODE_MAX_FILES_DEFAULT
        if isinstance(raw, bool):
            return PRO_MODE_MAX_FILES_DEFAULT if is_pro else SIMPLE_MODE_MAX_FILES_DEFAULT
        try:
            value = int(raw)
        except (TypeError, ValueError):
            return PRO_MODE_MAX_FILES_DEFAULT if is_pro else SIMPLE_MODE_MAX_FILES_DEFAULT
        if value < 0:
            return PRO_MODE_MAX_FILES_DEFAULT if is_pro else SIMPLE_MODE_MAX_FILES_DEFAULT
        if value == 0:
            return 0
        return value

    @staticmethod
    def _is_retryable_save_error(result: SaveResult) -> bool:
        if result.retryable:
            return True
        if result.error_category in {"sharing_violation"}:
            return True

        error_text = result.error or ""
        if not error_text:
            return False
        text = error_text.lower()
        if (result.error_code is not None) and result.error_code in {32, 33}:
            return True
        return any(
            token in text
            for token in (
                "resource temporarily unavailable",
                "temporarily unavailable",
                "used by another process",
                "used by another",
                "in use",
                "timed out",
                "timeout",
                "アクセスが拒否",
            )
        )

    def _save_with_retry(
        self,
        *,
        source_image: Image.Image,
        resized_image: Image.Image,
        output_path: Path,
        options: SaveOptions,
        allow_retry: bool,
        cancel_event: Optional[threading.Event] = None,
    ) -> Tuple[SaveResult, int]:
        max_attempts = 2 if allow_retry else 1
        result: SaveResult = SaveResult(
            success=False,
            output_path=output_path,
            exif_mode="keep",
            error="未実行",
        )

        for attempt in range(1, max_attempts + 1):
            if cancel_event is not None and cancel_event.is_set():
                return SaveResult(
                    success=False,
                    output_path=output_path,
                    exif_mode=options.exif_mode,
                    error="保存をキャンセルしました",
                ), attempt
            result = save_image(
                source_image=source_image,
                resized_image=resized_image,
                output_path=output_path,
                options=options,
            )
            if result.success:
                return result, attempt
            if not allow_retry or attempt >= max_attempts:
                return result, attempt
            if not self._is_retryable_save_error(result):
                return result, attempt
            if cancel_event is not None and cancel_event.is_set():
                return SaveResult(
                    success=False,
                    output_path=output_path,
                    exif_mode=options.exif_mode,
                    error="保存をキャンセルしました",
                ), attempt
            retry_delay = 0.35 * attempt
            logging.info(
                "保存再試行: %s (%s)",
                output_path,
                result.error,
            )
            if cancel_event is not None and cancel_event.is_set():
                return SaveResult(
                    success=False,
                    output_path=output_path,
                    exif_mode=options.exif_mode,
                    error="保存をキャンセルしました",
                ), attempt
            time.sleep(min(1.5, retry_delay))

        return result, max_attempts

    def _recent_settings_entries(self) -> List[Dict[str, Any]]:
        return recent_settings_entries(self)

    def _refresh_recent_settings_buttons(self) -> None:
        refresh_recent_settings_buttons(self)

    def _apply_recent_setting(self, fingerprint: str) -> None:
        apply_recent_setting(self, fingerprint)

    def _register_recent_setting_from_current(self) -> None:
        register_recent_setting_from_current(self)

    def _select_button_text_for_state(self) -> str:
        if self._is_pro_mode():
            if self._topbar_density == "compact":
                return "画像/フォルダ選択"
            return "画像/フォルダを選択"
        return "画像を選択"

    @staticmethod
    def _topbar_density_for_width(window_width: int) -> str:
        return topbar_density_for_width(window_width)

    @staticmethod
    def _batch_button_text_for_density(density: str) -> str:
        return topbar_batch_button_text(density)

    @staticmethod
    def _runtime_base_dir() -> Path:
        return bootstrap_runtime_base_dir()

    @staticmethod
    def _resolve_icon_paths() -> tuple[Path | None, Path | None]:
        return bootstrap_resolve_icon_paths()

    def _topbar_density_window_width(self, window_width: int) -> int:
        scale_factor = getattr(self, "_ui_scale_factor", 1.0)
        return bootstrap_topbar_density_window_width(
            window_width=window_width,
            scale_factor=scale_factor,
        )

    @staticmethod
    def _normalize_ui_mode_label(value: str) -> str:
        raw = str(value).strip()
        if raw in UI_MODE_LABEL_TO_ID:
            return UI_MODE_LABEL_TO_ID[raw]
        normalized = raw.lower()
        if normalized in {"pro", "on", "on(pro)", "on（pro）"} or raw in {"プロ", "オン", "オン(Pro)", "オン（Pro）"}:
            return "pro"
        return "simple"

    def _ui_mode_id(self) -> str:
        ui_mode_var = getattr(self, "ui_mode_var", None)
        if ui_mode_var is None:
            return "simple"
        return self._normalize_ui_mode_label(ui_mode_var.get())

    def _is_pro_mode(self) -> bool:
        return self._ui_mode_id() == "pro"

    def _appearance_mode_id(self) -> str:
        appearance_mode_var = getattr(self, "appearance_mode_var", None)
        if appearance_mode_var is None:
            return "system"
        return APPEARANCE_LABEL_TO_ID.get(appearance_mode_var.get(), "system")

    def _on_appearance_mode_changed(self, _value: str):
        self._apply_user_appearance_mode(self._appearance_mode_id(), redraw=True)
        self._update_settings_summary()

    def _apply_user_appearance_mode(self, mode_id: str, redraw: bool = False):
        normalized = self._normalize_appearance_mode(mode_id)
        customtkinter.set_appearance_mode(normalized)
        self.configure(fg_color=METALLIC_COLORS["bg_primary"])

        if hasattr(self, "canvas_org") and self.canvas_org.winfo_exists():
            self.canvas_org.configure(bg=self._canvas_background_color())
        if hasattr(self, "canvas_resz") and self.canvas_resz.winfo_exists():
            self.canvas_resz.configure(bg=self._canvas_background_color())

        if redraw and self.current_index is not None and self.current_index < len(self.jobs):
            self._draw_previews(self.jobs[self.current_index])

    def _on_ui_mode_changed(self, _value: str):
        self._apply_ui_mode()
        self._refresh_status_indicators()
        self._update_settings_summary()
        if self.current_index is not None and self.current_index < len(self.jobs):
            self._draw_previews(self.jobs[self.current_index])

    def _on_setting_var_changed(self, *_args: Any) -> None:
        self._update_settings_summary()
        self._schedule_auto_preview()

    def _update_exif_mode_options_for_ui_mode(self):
        if self._is_pro_mode():
            values = list(EXIF_LABEL_TO_ID.keys())
        else:
            values = ["保持", "削除"]
        self.exif_mode_menu.configure(values=values)
        if self.exif_mode_var.get() not in values:
            self.exif_mode_var.set("保持")

    def _apply_ui_mode(self):
        pro_mode = self._is_pro_mode()
        self._update_exif_mode_options_for_ui_mode()
        if self._topbar_controller is not None:
            self._topbar_controller.apply_ui_mode(
                is_pro_mode=pro_mode,
                is_loading=self._is_loading_files,
            )

        if hasattr(self, "detail_output_refs"):
            apply_output_controls_state_for_app(
                self,
                output_format_to_id=FORMAT_LABEL_TO_ID,
                exif_label_to_id=EXIF_LABEL_TO_ID,
            )
        self._apply_log_level()
        self._update_metadata_panel_state()
        self._update_empty_state_hint()
        self._refresh_recent_settings_buttons()

    def _update_settings_summary(self):
        format_id = FORMAT_LABEL_TO_ID.get(self.output_format_var.get(), "auto")

        exif_label = self.exif_mode_var.get()
        summary_text = build_settings_summary_text(
            output_format=self.output_format_var.get(),
            quality=self.quality_var.get(),
            exif_mode_label=exif_label,
            remove_gps=self.remove_gps_var.get(),
            dry_run=self.dry_run_var.get(),
            is_pro_mode=self._is_pro_mode(),
            format_id=format_id,
            webp_method=self.webp_method_var.get(),
            webp_lossless=self.webp_lossless_var.get(),
            avif_speed=self.avif_speed_var.get(),
        )
        self.settings_summary_var.set(summary_text)
        layout_update_session_summary(
            self,
            file_filter_label_to_id=FILE_FILTER_LABEL_TO_ID,
            file_filter_id_to_label=FILE_FILTER_ID_TO_LABEL,
        )

    def _update_empty_state_hint(self) -> None:
        if not hasattr(self, "file_list_panel_refs"):
            return
        apply_empty_state_hint(
            self.file_list_panel_refs,
            has_jobs=bool(self.jobs),
            is_pro_mode=self._is_pro_mode(),
            processing_hint=OPERATION_ONLY_CANCEL_HINT,
            build_empty_state_text_fn=build_empty_state_text,
        )

    def _toggle_details_panel(self):
        expanded = not self.details_expanded
        self.details_expanded = expanded
        apply_detail_panel_visibility(self, expanded=expanded)

    def _set_details_panel_visibility(self, expanded: bool):
        self.details_expanded = expanded
        apply_detail_panel_visibility(self, expanded=expanded)

    def _on_quality_changed(self, value: str):
        try:
            raw = int(value)
        except ValueError:
            raw = 85
        normalized = str(normalize_quality(raw))
        if normalized != value:
            self.quality_var.set(normalized)
        if self.current_index is not None and self.current_index < len(self.jobs):
            self._draw_previews(self.jobs[self.current_index])

    def _on_output_format_changed(self, _value: str):
        apply_output_controls_state_for_app(
            self,
            output_format_to_id=FORMAT_LABEL_TO_ID,
            exif_label_to_id=EXIF_LABEL_TO_ID,
        )
        if self.current_index is not None and self.current_index < len(self.jobs):
            self._draw_previews(self.jobs[self.current_index])

    def _on_exif_mode_changed(self, _value: str):
        apply_output_controls_state_for_app(
            self,
            output_format_to_id=FORMAT_LABEL_TO_ID,
            exif_label_to_id=EXIF_LABEL_TO_ID,
        )
        self._update_settings_summary()

    def _on_webp_method_changed(self, value: str):
        try:
            raw = int(value)
        except ValueError:
            raw = 6
        normalized = str(normalize_webp_method(raw))
        if normalized != value:
            self.webp_method_var.set(normalized)
        self._on_codec_setting_changed()

    def _on_avif_speed_changed(self, value: str):
        try:
            raw = int(value)
        except ValueError:
            raw = 6
        normalized = str(normalize_avif_speed(raw))
        if normalized != value:
            self.avif_speed_var.set(normalized)
        self._on_codec_setting_changed()

    def _on_codec_setting_changed(self):
        if self.current_index is not None and self.current_index < len(self.jobs):
            self._draw_previews(self.jobs[self.current_index])

    def _apply_log_level(self):
        level = logging.DEBUG if (self.verbose_log_var.get() and self._is_pro_mode()) else logging.INFO
        root_logger = logging.getLogger()
        root_logger.setLevel(level)
        self._ensure_run_log_handler()

    def _show_operation_stage(self, stage_text: str) -> None:
        layout_show_operation_stage(self, stage_text, operation_only_cancel_hint=OPERATION_ONLY_CANCEL_HINT)

    def _hide_operation_stage(self) -> None:
        layout_hide_operation_stage(self)

    def _refresh_status_indicators(self) -> None:
        layout_refresh_status_indicators(
            self,
            file_filter_label_to_id=FILE_FILTER_LABEL_TO_ID,
            file_filter_id_to_label=FILE_FILTER_ID_TO_LABEL,
        )
        if self._topbar_controller is not None:
            self._topbar_controller.refresh_top_action_guide(
                build_top_action_guide_text(
                    is_loading_files=self._is_loading_files,
                    is_processing=self._operation_scope is not None and self._operation_scope.active,
                )
            )

    def _show_progress_with_cancel(
        self,
        cancel_text: str,
        cancel_command: Callable[[], None],
        initial_progress: float,
    ) -> None:
        layout_show_progress_with_cancel(
            self,
            cancel_text=cancel_text,
            cancel_command=cancel_command,
            initial_progress=initial_progress,
        )

    def _hide_progress_with_cancel(self) -> None:
        layout_hide_progress_with_cancel(self)

    def _build_operation_scope_hooks(self) -> OperationScopeHooks:
        return layout_build_operation_scope_hooks(
            self,
            operation_scope_hooks_cls=OperationScopeHooks,
        )

    def _begin_operation_scope(
        self,
        *,
        stage_text: str,
        cancel_text: str,
        cancel_command: Callable[[], None],
        initial_progress: float,
    ) -> None:
        layout_begin_operation_scope(
            self,
            operation_scope_cls=OperationScope,
            operation_scope_hooks_cls=OperationScopeHooks,
            stage_text=stage_text,
            cancel_text=cancel_text,
            cancel_command=cancel_command,
            initial_progress=initial_progress,
        )

    def _set_operation_stage(self, stage_text: str) -> None:
        layout_set_operation_stage(self, stage_text)

    def _end_operation_scope(self) -> None:
        layout_end_operation_scope(self)

    def _toggle_metadata_panel(self):
        self.metadata_expanded = not self.metadata_expanded
        if hasattr(self, "metadata_panel_refs"):
            apply_metadata_expanded(self.metadata_panel_refs, expanded=self.metadata_expanded)

    def _update_metadata_preview(self, job: Optional[ImageJob]):
        if not hasattr(self, "metadata_panel_refs"):
            return
        apply_metadata_preview(
            self.metadata_panel_refs,
            job,
            extract_metadata_text=lambda target_job: layout_extract_metadata_text(
                self,
                target_job,
                exif_gps_info_tag=EXIF_GPS_INFO_TAG,
                exif_preview_tags=EXIF_PREVIEW_TAGS,
            ),
        )

    def _update_metadata_panel_state(self):
        if not hasattr(self, "metadata_frame"):
            return
        if hasattr(self, "metadata_panel_refs"):
            apply_metadata_mode(self.metadata_panel_refs, is_pro_mode=self._is_pro_mode())

        if self._is_pro_mode():
            selected_job = None
            if self.current_index is not None and self.current_index < len(self.jobs):
                selected_job = self.jobs[self.current_index]
            self._update_metadata_preview(selected_job)

    def _restore_settings(self):
        """保存された設定を復元"""
        # モード復元
        self._apply_ui_scale_mode(self.settings.get("ui_scale_mode", "normal"))
        self.mode_var.set(self.settings["mode"])
        self.ui_mode_var.set(
            UI_MODE_ID_TO_LABEL.get(
                str(self.settings.get("ui_mode", "simple")),
                "オフ",
            )
        )
        saved_appearance = self._normalize_appearance_mode(self.settings.get("appearance_mode", "system"))
        self.appearance_mode_var.set(APPEARANCE_ID_TO_LABEL.get(saved_appearance, "OSに従う"))
        
        # 値復元
        self.pct_var.set(self.settings["ratio_value"])
        self.w_var.set(self.settings["width_value"])
        self.h_var.set(self.settings["height_value"])
        try:
            saved_quality = int(self.settings.get("quality", "85"))
        except (TypeError, ValueError):
            saved_quality = 85
        self.quality_var.set(str(normalize_quality(saved_quality)))
        try:
            saved_webp_method = int(self.settings.get("webp_method", "6"))
        except (TypeError, ValueError):
            saved_webp_method = 6
        self.webp_method_var.set(str(normalize_webp_method(saved_webp_method)))
        try:
            saved_avif_speed = int(self.settings.get("avif_speed", "6"))
        except (TypeError, ValueError):
            saved_avif_speed = 6
        self.avif_speed_var.set(str(normalize_avif_speed(saved_avif_speed)))
        webp_lossless_raw = self.settings.get("webp_lossless", False)
        if isinstance(webp_lossless_raw, bool):
            webp_lossless = webp_lossless_raw
        else:
            webp_lossless = str(webp_lossless_raw).lower() in {"1", "true", "yes", "on"}
        self.webp_lossless_var.set(webp_lossless)
        output_label = FORMAT_ID_TO_LABEL.get(
            self.settings.get("output_format", "auto"),
            "自動",
        )
        if output_label not in main_output_format_labels(self.available_formats):
            output_label = "自動"
        self.output_format_var.set(output_label)
        self.exif_mode_var.set(
            EXIF_ID_TO_LABEL.get(
                self.settings.get("exif_mode", "keep"),
                "保持",
            )
        )
        self.remove_gps_var.set(self._to_bool(self.settings.get("remove_gps", False)))
        self.exif_artist_var.set(str(self.settings.get("exif_artist", "")))
        self.exif_copyright_var.set(str(self.settings.get("exif_copyright", "")))
        self.exif_user_comment_var.set(str(self.settings.get("exif_user_comment", "")))
        self.exif_datetime_original_var.set(str(self.settings.get("exif_datetime_original", "")))
        self.dry_run_var.set(self._to_bool(self.settings.get("dry_run", False)))
        self.verbose_log_var.set(self._to_bool(self.settings.get("verbose_logging", False)))
        self.settings["show_tooltips"] = self._to_bool(self.settings.get("show_tooltips", True))
        details_expanded = self.settings.get("details_expanded", False)
        if not isinstance(details_expanded, bool):
            details_expanded = str(details_expanded).lower() in {"1", "true", "yes", "on"}
        metadata_panel_expanded = self.settings.get("metadata_panel_expanded", False)
        if not isinstance(metadata_panel_expanded, bool):
            metadata_panel_expanded = str(metadata_panel_expanded).lower() in {"1", "true", "yes", "on"}

        # ウィンドウサイズ復元
        try:
            saved_geometry = self._normalize_window_geometry(self.settings.get("window_geometry"))
            self.geometry(saved_geometry)
        except Exception:
            self.geometry(DEFAULT_WINDOW_GEOMETRY)  # フォールバック
        
        # ズーム設定復元
        self.zoom_var.set(self.settings["zoom_preference"])
        if hasattr(self, "metadata_panel_refs"):
            self.metadata_expanded = metadata_panel_expanded
            apply_metadata_expanded(self.metadata_panel_refs, expanded=metadata_panel_expanded)
        self._apply_user_appearance_mode(saved_appearance, redraw=False)
        self._apply_ui_mode()
        self._set_details_panel_visibility(details_expanded)
        if self._topbar_controller is not None:
            self._topbar_controller.apply_density(self._topbar_density_window_width(max(self.winfo_width(), MIN_WINDOW_WIDTH)))
        self._refresh_recent_settings_buttons()
        self._update_empty_state_hint()
        self._update_settings_summary()

    @staticmethod
    def _normalize_window_geometry(value: Any) -> str:
        """ウィンドウジオメトリを正規化し、最小横幅を保証する。"""
        geometry_text = str(value or DEFAULT_WINDOW_GEOMETRY).strip()
        matched = WINDOW_GEOMETRY_PATTERN.match(geometry_text)
        if not matched:
            return DEFAULT_WINDOW_GEOMETRY

        width = max(int(matched.group(1)), MIN_WINDOW_WIDTH)
        height = max(int(matched.group(2)), 1)
        position = matched.group(3) or ""
        return f"{width}x{height}{position}"
    
    def _save_current_settings(self):
        """現在の設定を保存"""
        self.settings.update({
            "mode": self.mode_var.get(),
            "ui_mode": self._ui_mode_id(),
            "appearance_mode": self._appearance_mode_id(),
            "ui_scale_mode": self._normalize_ui_scale_mode(self._ui_scale_mode),
            "ratio_value": self.pct_var.get(),
            "width_value": self.w_var.get(),
            "height_value": self.h_var.get(),
            "quality": self.quality_var.get(),
            "output_format": FORMAT_LABEL_TO_ID.get(self.output_format_var.get(), "auto"),
            "webp_method": self.webp_method_var.get(),
            "webp_lossless": self.webp_lossless_var.get(),
            "avif_speed": self.avif_speed_var.get(),
            "exif_mode": EXIF_LABEL_TO_ID.get(self.exif_mode_var.get(), "keep"),
            "remove_gps": self.remove_gps_var.get(),
            "exif_artist": self.exif_artist_var.get(),
            "exif_copyright": self.exif_copyright_var.get(),
            "exif_user_comment": self.exif_user_comment_var.get(),
            "exif_datetime_original": self.exif_datetime_original_var.get(),
            "dry_run": self.dry_run_var.get(),
            "verbose_logging": self.verbose_log_var.get(),
            "show_tooltips": self._to_bool(self.settings.get("show_tooltips", True)),
            "details_expanded": self.details_expanded,
            "metadata_panel_expanded": self.metadata_expanded,
            "window_geometry": self.geometry(),
            "zoom_preference": self.zoom_var.get(),
            "default_output_dir": str(self.settings.get("default_output_dir", "")),
            "default_preset_id": str(self.settings.get("default_preset_id", "")).strip(),
            "pro_input_mode": self._normalized_pro_input_mode(
                str(self.settings.get("pro_input_mode", "recursive"))
            ),
            "recent_processing_settings": self._normalize_recent_settings_entries(
                self.settings.get("recent_processing_settings", [])
            ),
        })
        self.settings_store.save(self.settings)
    
    def _on_closing(self):
        """アプリ終了時の処理"""
        if self._preview_draw_after_id is not None:
            try:
                self.after_cancel(self._preview_draw_after_id)
            except Exception:
                pass
            self._preview_draw_after_id = None
        if self._is_loading_files:
            self._file_load_cancel_event.set()
        if self._single_save_thread is not None and self._single_save_thread.is_alive():
            self._single_save_cancel_event.set()
        self._save_current_settings()
        self._finalize_run_summary()
        self.destroy()

    # -------------------- validation helpers ---------------------------
    @staticmethod
    def _validate_int(text: str) -> bool:
        """Return True if text is empty or all digits."""
        return text == "" or text.isdigit()

    def _parse_positive(self, widget: customtkinter.CTkEntry, min_val: int = 1) -> Optional[int]:
        if widget == self.ratio_entry:
            s = self.pct_var.get() # pct_var is already validated
        else:
            s = widget.get()
        if not s:
            return None
        num = int(s)
        if not (min_val <= num):
            messagebox.showwarning("入力エラー", f"{min_val} 以上の整数で入力してください")
            widget.focus_set()
            return None
        return num

    @staticmethod
    def _parse_positive_text(value: str, min_val: int = 1) -> Optional[int]:
        s = value.strip()
        if not s:
            return None
        try:
            num = int(s)
        except ValueError:
            return None
        if not (min_val <= num):
            return None
        return num

    def _snapshot_resize_target(self, source_size: Tuple[int, int]) -> Optional[Tuple[int, int]]:
        mode = self.mode_var.get()
        ow, oh = source_size
        if ow <= 0 or oh <= 0:
            return None

        if mode == "ratio":
            pct = self._parse_positive_text(self.pct_var.get())
            if pct is None:
                return None
            return int(ow * pct / 100), int(oh * pct / 100)

        if mode == "width":
            w = self._parse_positive_text(self.entry_w_single.get())
            if w is None:
                return None
            return w, int(oh * w / ow)

        if mode == "height":
            h = self._parse_positive_text(self.entry_h_single.get())
            if h is None:
                return None
            return int(ow * h / oh), h

        w = self._parse_positive_text(self.entry_w_fixed.get())
        if w is None:
            return None
        h = self._parse_positive_text(self.entry_h_fixed.get())
        if h is None:
            return None
        return w, h

    @staticmethod
    def _parse_int_or_default(value: str, default: int) -> int:
        try:
            return int(value.strip())
        except ValueError:
            return default

    def _snapshot_encoder_settings(self) -> Tuple[int, int, int, bool]:
        quality = normalize_quality(self._parse_int_or_default(self.quality_var.get(), 85))
        webp_method = normalize_webp_method(self._parse_int_or_default(self.webp_method_var.get(), 6))
        avif_speed = normalize_avif_speed(self._parse_int_or_default(self.avif_speed_var.get(), 6))
        return quality, webp_method, avif_speed, bool(self.webp_lossless_var.get())

    # ------------------------------------------------------------------
    # Helper: summarize current resize settings for confirmation dialogs
    # ------------------------------------------------------------------

    def _current_resize_settings_text(self) -> str:
        mode = self.mode_var.get()
        if mode == "ratio":
            pct = self.ratio_entry.get().strip() or "---"
            return f"倍率 {pct}%"
        if mode == "width":
            w = self.entry_w_single.get().strip() or "---"
            return f"幅 {w}px"
        if mode == "height":
            h = self.entry_h_single.get().strip() or "---"
            return f"高さ {h}px"
        w = self.entry_w_fixed.get().strip() or "---"
        h = self.entry_h_fixed.get().strip() or "---"
        return f"固定 {w}×{h}px"

    def _get_settings_summary(self):
        """Return (settings_text, fmt, target) for current UI selections."""
        settings_text = self._current_resize_settings_text()

        # 既定の出力形式と目標サイズを算出
        fmt = self.output_format_var.get()
        target = None
        if self.jobs:
            first_img = self.jobs[0].image
            resolved_format = self._resolve_output_format_for_image(first_img)
            fmt = FORMAT_ID_TO_LABEL.get(resolved_format, "JPEG")
            target = self._get_target(first_img.size)
        return settings_text, fmt, target

    def _resolve_output_format_for_image(self, source_image: Image.Image) -> SaveFormat:
        selected_id = FORMAT_LABEL_TO_ID.get(self.output_format_var.get(), "auto")
        return resolve_output_format(
            selected=selected_id,
            source_image=source_image,
            available_formats=self.available_formats,
        )

    def _current_quality(self) -> int:
        try:
            value = int(self.quality_var.get())
        except ValueError:
            value = 85
        normalized = normalize_quality(value)
        self.quality_var.set(str(normalized))
        return normalized

    def _current_webp_method(self) -> int:
        try:
            value = int(self.webp_method_var.get())
        except ValueError:
            value = 6
        normalized = normalize_webp_method(value)
        self.webp_method_var.set(str(normalized))
        return normalized

    def _current_avif_speed(self) -> int:
        try:
            value = int(self.avif_speed_var.get())
        except ValueError:
            value = 6
        normalized = normalize_avif_speed(value)
        self.avif_speed_var.set(str(normalized))
        return normalized

    def _current_exif_edit_values(
        self,
        show_warning: bool = True,
        *,
        strict: bool = False,
        warning_parent: Optional[customtkinter.CTkToplevel] = None,
    ) -> Optional[ExifEditValues]:
        datetime_text = self.exif_datetime_original_var.get().strip()
        if datetime_text and not self._validate_exif_datetime(datetime_text):
            if show_warning:
                messagebox.showwarning(
                    "EXIF日時形式",
                    "撮影日時は YYYY:MM:DD HH:MM:SS 形式で入力してください。\n"
                    "不正な値のため、この操作を中止しました。",
                    parent=warning_parent or self,
                )
            if strict:
                return None
            datetime_text = ""

        return ExifEditValues(
            artist=self.exif_artist_var.get(),
            copyright_text=self.exif_copyright_var.get(),
            user_comment=self.exif_user_comment_var.get(),
            datetime_original=datetime_text,
        )

    def _show_exif_preview_dialog(self):
        if self.current_index is None or self.current_index >= len(self.jobs):
            messagebox.showwarning("ファイル未選択", "EXIF差分を確認する画像を選択してください")
            return

        job = self.jobs[self.current_index]
        exif_mode = EXIF_LABEL_TO_ID.get(self.exif_mode_var.get(), "keep")
        edit_values = self._current_exif_edit_values(show_warning=True) if exif_mode == "edit" else None
        preview = preview_exif_plan(
            source_image=job.image,
            exif_mode=exif_mode,  # type: ignore[arg-type]
            remove_gps=self.remove_gps_var.get(),
            edit_values=edit_values,
        )
        edit_values_payload = {}
        if edit_values is not None:
            edit_values_payload = {
                "Artist": edit_values.artist or "",
                "Copyright": edit_values.copyright_text or "",
                "DateTimeOriginal": edit_values.datetime_original or "",
                "UserComment": edit_values.user_comment or "",
            }
        messagebox.showinfo(
            "EXIF差分プレビュー",
            build_exif_preview_message(
                job_name=job.path.name,
                exif_mode_label=EXIF_ID_TO_LABEL.get(preview.exif_mode, "保持"),
                source_tag_count=preview.source_tag_count,
                source_has_gps=preview.source_has_gps,
                exif_will_be_attached=preview.exif_will_be_attached,
                exif_mode=preview.exif_mode,
                gps_removed=preview.gps_removed,
                edited_fields=list(preview.edited_fields),
                edit_values=edit_values_payload,
                skipped_reason=preview.skipped_reason,
                has_multiple_jobs=len(self.jobs) > 1,
            ),
        )

    @staticmethod
    def _validate_exif_datetime(value: str) -> bool:
        try:
            datetime.strptime(value, "%Y:%m:%d %H:%M:%S")
            return True
        except ValueError:
            return False

    #     # -------------------- mode handling --------------------------------
    def _report_callback_exception(self, exc, val, tb):
        # Custom exception handler to log full traceback
        logging.error("Tkinter callback exception", exc_info=(exc, val, tb))
        self._run_summary_payload["errors"].append(
            {
                "timestamp": datetime.now().isoformat(timespec="seconds"),
                "type": exc.__name__,
                "message": str(val),
            }
        )
        self._write_run_summary_safe()
        messagebox.showerror("例外", f"{exc.__name__}: {val}")

    def _update_mode(self, _e=None):
        mode = self.mode_var.get()

        # --- Hide previous frame and show the new one ---
        if self.active_mode_frame is not None:
            self.active_mode_frame.pack_forget()

        current_mode_frame = cast(customtkinter.CTkFrame, self.mode_frames[mode])
        self.active_mode_frame = current_mode_frame
        current_mode_frame.pack(side="left")

        # --- Enable/disable entries based on mode ---
        actives = self._entry_widgets.get(mode, [])
        for entry in self._all_entries:
            if entry in actives:
                entry.configure(state="normal")
            else:
                entry.configure(state="disabled")

        # set focus to first active entry
        actives = self._entry_widgets.get(mode, [])
        if actives:
            actives[0].focus_set()
        self._schedule_auto_preview()

    def _schedule_auto_preview(self) -> None:
        """Schedule an automatic preview update with 500ms debounce."""
        if self._auto_preview_after_id is not None:
            try:
                self.after_cancel(self._auto_preview_after_id)
            except Exception:
                pass
            self._auto_preview_after_id = None
        if self.current_index is None or self._is_loading_files or self.current_index >= len(self.jobs):
            return
        self._auto_preview_after_id = self.after(500, self._auto_preview)

    def _auto_preview(self) -> None:
        """Execute automatic preview after debounce delay."""
        self._auto_preview_after_id = None
        if self.current_index is None or self._is_loading_files or self.current_index >= len(self.jobs):
            return
        self._start_async_preview(self.current_index)

    def _schedule_preview_redraw(self, *, delay_ms: int = RESIZE_PREVIEW_DEBOUNCE_MS) -> None:
        if self.current_index is None or self.current_index >= len(self.jobs):
            return
        if self._preview_draw_after_id is not None:
            try:
                self.after_cancel(self._preview_draw_after_id)
            except Exception:
                pass
            self._preview_draw_after_id = None
        self._preview_draw_after_id = self.after(delay_ms, self._flush_preview_redraw)

    def _flush_preview_redraw(self) -> None:
        self._preview_draw_after_id = None
        if self.current_index is None or self.current_index >= len(self.jobs) or self._is_loading_files:
            return
        self._start_async_preview(self.current_index)

    def _setup_drag_and_drop(self) -> None:
        ui_bootstrap.bootstrap_setup_drag_and_drop(
            self,
            tkdnd_available=TKDND_AVAILABLE,
            tkdnd_cls=TkinterDnD,
            copy_token=str(COPY),
            dnd_files=DND_FILES,
            selectable_input_extensions=SELECTABLE_INPUT_EXTENSIONS,
        )

    def _on_drop_enter(self, _event: Any) -> str:
        return ui_bootstrap.bootstrap_on_drop_enter(_event, str(COPY))

    def _on_drop_position(self, _event: Any) -> str:
        return ui_bootstrap.bootstrap_on_drop_position(_event, str(COPY))

    def _on_drop_leave(self, _event: Any) -> None:
        ui_bootstrap.bootstrap_on_drop_leave(_event)
        return None

    def _on_drop_files(self, event: Any) -> str:
        return ui_bootstrap.bootstrap_on_drop_files(
            self,
            event,
            copy_token=str(COPY),
            selectable_input_extensions=SELECTABLE_INPUT_EXTENSIONS,
        )

    def _handle_dropped_paths(self, dropped_paths: List[Path]) -> None:
        ui_bootstrap.bootstrap_handle_dropped_paths(
            self,
            dropped_paths,
            selectable_input_extensions=SELECTABLE_INPUT_EXTENSIONS,
        )

    def _start_drop_load_async(self, files: List[Path], dirs: List[Path]) -> None:
        ui_bootstrap.bootstrap_start_drop_load_async(
            self,
            files=files,
            dirs=dirs,
            selectable_input_extensions=SELECTABLE_INPUT_EXTENSIONS,
        )

    # -------------------- file selection -------------------------------
    def _select_files(self):
        paths, remembered_dir, started_async = ui_bootstrap.bootstrap_select_files(
            self,
            selectable_input_extensions=SELECTABLE_INPUT_EXTENSIONS,
        )
        if started_async:
            return
        if not paths:
            return

        if remembered_dir is not None:
            self.settings["last_input_dir"] = str(remembered_dir)

        self._start_drop_load_async(paths, [])

    def _select_files_in_simple_mode(
        self,
        initial_dir: str,
        max_files: Optional[int] = None,
    ) -> Tuple[List[Path], Optional[Path]]:
        return ui_bootstrap.bootstrap_select_files_in_simple_mode(
            initial_dir,
            max_files=max_files,
            selectable_input_extensions=SELECTABLE_INPUT_EXTENSIONS,
        )

    def _select_files_in_pro_mode(self, initial_dir: str) -> Tuple[List[Path], Optional[Path], bool]:
        return ui_bootstrap.bootstrap_select_files_in_pro_mode(
            self,
            initial_dir=initial_dir,
            selectable_input_extensions=SELECTABLE_INPUT_EXTENSIONS,
        )

    @staticmethod
    def _normalized_pro_input_mode(value: str) -> str:
        return ui_bootstrap.bootstrap_normalized_pro_input_mode(value)

    def _start_recursive_load_async(self, root_dir: Path) -> None:
        ui_bootstrap.bootstrap_start_recursive_load_async(self, root_dir=root_dir)

    def _start_retry_failed_load_async(self, paths: List[Path]) -> None:
        ui_bootstrap.bootstrap_start_retry_failed_load_async(self, paths=paths)

    def _begin_file_load_session(
        self,
        mode_label: str,
        root_dir: Optional[Path],
        clear_existing_jobs: bool,
    ) -> None:
        ui_bootstrap.bootstrap_begin_file_load_session(
            self,
            mode_label=mode_label,
            root_dir=root_dir,
            clear_existing_jobs=clear_existing_jobs,
        )

    def _set_interactive_controls_enabled(self, enabled: bool) -> None:
        state = "normal" if enabled else "disabled"
        widgets = [
            self.select_button,
            self.help_button,
            self.settings_button,
            self.preset_menu,
            self.preset_manage_button,
            self.preview_button,
            self.save_button,
            self.clear_loaded_button,
            self.batch_button,
            self.details_toggle_button,
            self.output_format_menu,
            self.quality_menu,
            self.exif_mode_menu,
            self.remove_gps_check,
            self.dry_run_check,
            self.verbose_log_check,
            self.exif_preview_button,
            self.open_log_folder_button,
            self.webp_method_menu,
            self.webp_lossless_check,
            self.avif_speed_menu,
            self.zoom_cb,
            self.file_filter_segment,
        ]
        ui_mode_segment = getattr(self, "ui_mode_segment", None)
        if ui_mode_segment is not None:
            widgets.append(ui_mode_segment)
        widgets.append(self.mode_segment)
        widgets.extend(self.file_buttons)
        widgets.extend(self._recent_setting_buttons)
        for widget in widgets:
            try:
                widget.configure(state=state)
            except Exception:
                continue

        for entry in self._all_entries:
            entry.configure(state=state)
        for entry in (
            self.exif_artist_entry,
            self.exif_copyright_entry,
            self.exif_comment_entry,
            self.exif_datetime_entry,
        ):
            entry.configure(state=state)

        if enabled:
            self._apply_ui_mode()
            self._update_mode()
            apply_output_controls_state_for_app(
                self,
                output_format_to_id=FORMAT_LABEL_TO_ID,
                exif_label_to_id=EXIF_LABEL_TO_ID,
            )
            self._update_settings_summary()
            self._refresh_recent_settings_buttons()
        self._refresh_status_indicators()

    def _poll_file_load_queue(self) -> None:
        file_load_poll_queue(self)

    def _handle_file_load_message(self, message: Dict[str, Any]) -> None:
        file_load_handle_message(self, message)

    def _finish_recursive_load(self, canceled: bool) -> None:
        retry_paths = list(self._file_load_failed_paths)
        self._is_loading_files = False
        if self._file_load_after_id is not None:
            try:
                self.after_cancel(self._file_load_after_id)
            except Exception:
                pass
            self._file_load_after_id = None

        self._end_operation_scope()

        if self.jobs:
            self._populate_listbox()
        else:
            self._clear_preview_panels()

        total = self._file_load_total_candidates
        loaded = self._file_load_loaded_count
        failed = len(self._file_load_failed_details)
        if canceled:
            msg = f"{self._file_load_mode_label}を中止しました。成功: {loaded}件 / 失敗: {failed}件 / 対象: {total}件"
        else:
            limit_suffix = (
                f"（上限到達: {self._file_load_limit}枚）" if self._file_load_limited else ""
            )
            msg = (
                f"{self._file_load_mode_label}完了。成功: {loaded}件 / "
                f"失敗: {failed}件 / 対象: {total}件{limit_suffix}"
            )
        self.status_var.set(msg)
        retry_callback: Optional[Callable[[], None]] = None
        if (not canceled) and retry_paths:
            def _retry_failed_only() -> None:
                self._start_retry_failed_load_async(retry_paths)

            retry_callback = _retry_failed_only
        show_operation_result_dialog(
            self,
            colors=METALLIC_COLORS,
            file_load_failure_preview_limit=FILE_LOAD_FAILURE_PREVIEW_LIMIT,
            title="読込結果",
            summary_text=msg,
            failed_details=self._file_load_failed_details,
            retry_callback=retry_callback,
        )
        self._refresh_status_indicators()

    def _cancel_file_loading(self) -> None:
        if not self._is_loading_files:
            return
        self._file_load_cancel_event.set()
        self._set_operation_stage("キャンセル中")
        self.status_var.set(f"{self._file_load_mode_label}: キャンセル中...")
        self._refresh_status_indicators()

    def _clear_loaded_items(self) -> None:
        if self._is_loading_files:
            messagebox.showinfo("処理中", "画像読み込み中はクリアできません。完了または中止後に再実行してください。")
            return
        if self._operation_scope is not None and self._operation_scope.active:
            messagebox.showinfo("処理中", "処理中はクリアできません。完了または中止後に再実行してください。")
            return
        if not self.jobs:
            self.status_var.set("クリア対象がありません。")
            self._refresh_status_indicators()
            return
        proceed = messagebox.askyesno(
            "クリア確認",
            "読み込み済みのファイル/フォルダをすべてクリアします。よろしいですか？",
        )
        if not proceed:
            return

        self._reset_loaded_jobs()
        self._file_load_failed_details = []
        self._file_load_failed_paths = []
        self._file_load_total_candidates = 0
        self._file_load_loaded_count = 0
        self._file_load_limited = False
        self._file_load_limit = 0
        self._file_load_root_dir = None
        self.status_var.set("読み込み済みのファイル/フォルダをクリアしました。")
        self._refresh_status_indicators()

    def _reset_loaded_jobs(self) -> None:
        self.jobs.clear()
        self.current_index = None
        self._visible_job_indices = []
        for button in self.file_buttons:
            button.destroy()
        self.file_buttons = []
        self._clear_preview_panels()
        self._update_empty_state_hint()

    def _append_loaded_job(self, path: Path, image: Image.Image) -> None:
        file_size = 0
        try:
            file_size = path.stat().st_size
        except Exception:
            file_size = 0
        self.jobs.append(ImageJob(path, image, source_size_bytes=file_size))

    def _load_selected_paths(self, paths: List[Path]) -> None:
        # 新規選択として状態を初期化する
        self.jobs.clear()
        self.current_index = None
        for path in paths:
            try:
                with Image.open(path) as opened:
                    opened.load()
                    # EXIF Orientationを正規化して表示/処理を統一する。
                    img = ImageOps.exif_transpose(opened)
            except Exception as e:  # pragma: no cover
                detail = build_load_error_detail(path=path, error=e)
                messagebox.showerror("エラー", f"{path} の読み込みに失敗しました: {detail}")
                continue
            self._append_loaded_job(path, img)

    def _on_file_filter_changed(self, _value: str) -> None:
        self._populate_listbox()

    def _populate_listbox(self):
        if not hasattr(self, "file_list_panel_refs"):
            return

        self._visible_job_indices = []
        if not self.jobs:
            self._clear_preview_panels()
            self.status_var.set("有効な画像を読み込めませんでした")
            self._update_empty_state_hint()
            self._refresh_status_indicators()
            return

        filter_label = self.file_filter_var.get() if hasattr(self, "file_filter_var") else "全件"
        self._visible_job_indices = refresh_file_list_panel(
            self.file_list_panel_refs,
            self.jobs,
            file_filter_label=filter_label,
            file_filter_label_to_id=FILE_FILTER_LABEL_TO_ID,
            selected_job_index=self.current_index,
            on_select_job=self._on_select_change,
            register_tooltip=self._register_tooltip,
            tooltip_text=lambda idx, _label: f"この画像を選択します。\n{self.jobs[idx]}",
            colors=METALLIC_COLORS,
            empty_state_text="フィルタ条件に一致する画像がありません。",
        )
        self.file_buttons = self.file_list_panel_refs.file_buttons
        if self._visible_job_indices:
            if self.current_index in self._visible_job_indices:
                self._on_select_change(self.current_index, force=True)
            else:
                self._on_select_change(self._visible_job_indices[0])
        else:
            self.status_var.set("フィルタ条件に一致する画像がありません。")
        self._refresh_status_indicators()

    def _clear_preview_panels(self):
        self.current_index = None
        if self._preview_draw_after_id is not None:
            try:
                self.after_cancel(self._preview_draw_after_id)
            except Exception:
                pass
            self._preview_draw_after_id = None
        self._imgtk_org = None
        self._imgtk_resz = None
        self.canvas_org.delete("all")
        self.canvas_resz.delete("all")
        self.info_orig_var.set("--- x ---  ---")
        self.info_resized_var.set("--- x ---  ---  (---)")
        self.resized_title_label.configure(text="リサイズ後")
        self._update_metadata_preview(None)
        self._refresh_status_indicators()

    def _show_batch_processing_placeholders(
        self,
        total_files: int,
        current_file_name: Optional[str] = None,
        current_index: Optional[int] = None,
    ) -> None:
        self._batch_preview_placeholder_active = True
        placeholder_lines = ["一括保存中"]
        if total_files > 0:
            placeholder_lines.append(f"対象: {total_files}枚")
        if current_file_name:
            max_chars = 36
            if self.canvas_org.winfo_exists():
                width = self.canvas_org.winfo_width()
                if width > 1:
                    max_chars = max(16, int((width - 40) / 8))
            placeholder_lines.append(f"処理中: {self._shorten_file_name_for_placeholder(current_file_name, max_chars=max_chars)}")
        if current_index is not None and total_files > 0:
            placeholder_lines.append(f"進捗: {current_index}/{total_files}枚")
        placeholder_text = "\n".join(placeholder_lines)

        self.info_orig_var.set("処理中...")
        self.info_resized_var.set("処理中...")
        self.resized_title_label.configure(text="一括処理中")

        for canvas in (self.canvas_org, self.canvas_resz):
            if not hasattr(canvas, "winfo_width"):
                continue
            width = canvas.winfo_width()
            height = canvas.winfo_height()
            if width <= 1 or height <= 1:
                width = 260
                height = 180
            existing = self._batch_placeholder_items.get(canvas)
            rect_id: Optional[int] = None
            text_id: Optional[int] = None
            if existing is not None:
                rect_id, text_id = existing

            if (
                rect_id is not None
                and text_id is not None
                and rect_id in canvas.find_all()
                and text_id in canvas.find_all()
            ):
                canvas.coords(rect_id, 4, 4, width - 4, height - 4)
                canvas.itemconfigure(
                    rect_id,
                    outline=self._canvas_label_color(),
                )
                canvas.coords(text_id, width / 2, height / 2)
                canvas.itemconfigure(
                    text_id,
                    text=placeholder_text,
                    fill=self._canvas_label_color(),
                    width=width - 20,
                )
            else:
                canvas.delete("all")
                rect_id = canvas.create_rectangle(
                    4,
                    4,
                    width - 4,
                    height - 4,
                    outline=self._canvas_label_color(),
                    width=2,
                    tags="batch-processing-placeholder",
                )
                text_id = canvas.create_text(
                    width / 2,
                    height / 2,
                    text=placeholder_text,
                    justify="center",
                    anchor="center",
                    fill=self._canvas_label_color(),
                    font=self.font_small,
                    width=width - 20,
                    tags="batch-processing-placeholder",
                )
                self._batch_placeholder_items[canvas] = (rect_id, text_id)

    def _shorten_file_name_for_placeholder(self, file_name: str, max_chars: int = 36) -> str:
        if max_chars <= 0 or len(file_name) <= max_chars:
            return file_name
        if max_chars <= 6:
            return file_name[:max_chars]

        head_chars = (max_chars - 3) // 2
        tail_chars = max_chars - 3 - head_chars
        return f"{file_name[:head_chars]}...{file_name[-tail_chars:]}"

    def _show_single_processing_placeholders(
        self,
        *,
        version: int,
        title_text: str,
        status_text: str,
        file_name: Optional[str] = None,
    ) -> None:
        if self._single_preview_placeholder_active and self._single_preview_placeholder_version != version:
            return

        self._single_preview_placeholder_version = version
        self._single_preview_placeholder_active = True

        placeholder_lines = [status_text]
        if file_name:
            max_chars = 36
            if self.canvas_org.winfo_exists():
                width = self.canvas_org.winfo_width()
                if width > 1:
                    max_chars = max(16, int((width - 40) / 8))
            placeholder_lines.append(f"対象: {self._shorten_file_name_for_placeholder(file_name, max_chars=max_chars)}")

        placeholder_text = "\n".join(placeholder_lines)
        self.info_orig_var.set("処理中...")
        self.info_resized_var.set("処理中...")
        self.resized_title_label.configure(text=title_text)

        for canvas in (self.canvas_org, self.canvas_resz):
            if not hasattr(canvas, "winfo_width"):
                continue
            width = canvas.winfo_width()
            height = canvas.winfo_height()
            if width <= 1 or height <= 1:
                width = 260
                height = 180

            existing = self._single_preview_placeholder_items.get(canvas)
            rect_id: Optional[int] = None
            text_id: Optional[int] = None
            if existing is not None:
                rect_id, text_id = existing

            if (
                rect_id is not None
                and text_id is not None
                and rect_id in canvas.find_all()
                and text_id in canvas.find_all()
            ):
                canvas.coords(rect_id, 4, 4, width - 4, height - 4)
                canvas.itemconfigure(
                    rect_id,
                    outline=self._canvas_label_color(),
                )
                canvas.coords(text_id, width / 2, height / 2)
                canvas.itemconfigure(
                    text_id,
                    text=placeholder_text,
                    fill=self._canvas_label_color(),
                    width=width - 20,
                )
            else:
                canvas.delete("all")
                rect_id = canvas.create_rectangle(
                    4,
                    4,
                    width - 4,
                    height - 4,
                    outline=self._canvas_label_color(),
                    width=2,
                    tags="single-processing-placeholder",
                )
                text_id = canvas.create_text(
                    width / 2,
                    height / 2,
                    text=placeholder_text,
                    justify="center",
                    anchor="center",
                    fill=self._canvas_label_color(),
                    font=self.font_small,
                    width=width - 20,
                    tags="single-processing-placeholder",
                )
                self._single_preview_placeholder_items[canvas] = (rect_id, text_id)

    def _hide_single_processing_placeholders(self, *, version: Optional[int] = None) -> None:
        if not self._single_preview_placeholder_active:
            return
        if version is not None and version != self._single_preview_placeholder_version:
            return

        self._single_preview_placeholder_active = False
        for canvas in (self.canvas_org, self.canvas_resz):
            existing = self._single_preview_placeholder_items.get(canvas)
            if existing is not None:
                rect_id, text_id = existing
                if rect_id is not None:
                    try:
                        canvas.delete(rect_id)
                    except Exception:
                        pass
                if text_id is not None:
                    try:
                        canvas.delete(text_id)
                    except Exception:
                        pass
            canvas.delete("single-processing-placeholder")
        self._single_preview_placeholder_items = {}

    def _hide_batch_processing_placeholders(self) -> None:
        if not self._batch_preview_placeholder_active:
            return
        self._batch_preview_placeholder_active = False
        self._batch_placeholder_items = {}

        next_index = self.current_index
        if next_index is None or next_index >= len(self.jobs):
            if self._visible_job_indices:
                next_index = self._visible_job_indices[0]
            elif self.jobs:
                next_index = 0
            else:
                self._clear_preview_panels()
                return
        self.current_index = next_index
        if self.current_index is None or self.current_index >= len(self.jobs):
            self._clear_preview_panels()
            return
        self._draw_previews(self.jobs[self.current_index])

    def _on_select_change(self, idx: Optional[int] = None, force: bool = False) -> None:
        ui_bootstrap.bootstrap_on_select_change(self, idx=idx, force=force)

    # -------------------- size calculation -----------------------------
    # サイズ計算に関する関数
    def _get_target(self, orig: Tuple[int, int]) -> Optional[Tuple[int, int]]:
        mode = self.mode_var.get()
        ow, oh = orig
        if mode == "ratio":
            pct = self._parse_positive(self.ratio_entry)
            if pct is None:
                return None
            return int(ow * pct / 100), int(oh * pct / 100)
        if mode == "width":
            w = self._parse_positive(self.entry_w_single)
            if w is None:
                return None
            return w, int(oh * w / ow)
        if mode == "height":
            h = self._parse_positive(self.entry_h_single)
            if h is None:
                return None
            return int(ow * h / oh), h
        # fixed
        w = self._parse_positive(self.entry_w_fixed)
        if w is None:
            return None
        h = self._parse_positive(self.entry_h_fixed)
        if h is None:
            return None
        return w, h

    def _process_image(self, img: Image.Image) -> Optional[Image.Image]:
        """Resize image according to current settings."""
        target_size = self._get_target(img.size)
        if not target_size:
            self.status_var.set("リサイズ設定が無効です")
            return None
        if any(d <= 0 for d in target_size):
            self.status_var.set("リサイズ後のサイズが0以下になります")
            return None

        return img.resize(target_size, Resampling.LANCZOS)

    @staticmethod
    def _resize_image_to_target(img: Image.Image, target_size: Tuple[int, int]) -> Optional[Image.Image]:
        """Resize image to the explicit target size used for batch-apply saves."""
        tw, th = target_size
        if tw <= 0 or th <= 0:
            return None
        return img.resize((tw, th), Resampling.LANCZOS)

    def _resolve_batch_reference(self) -> Optional[Tuple[ImageJob, Tuple[int, int], SaveFormat]]:
        """Resolve selected image as batch reference and freeze output params."""
        if not self.jobs:
            return None

        ref_index = self.current_index if self.current_index is not None else 0
        if ref_index >= len(self.jobs):
            ref_index = 0
        reference_job = self.jobs[ref_index]

        target_size = self._get_target(reference_job.image.size)
        if not target_size:
            self.status_var.set("基準画像のリサイズ設定が無効です")
            return None
        if any(d <= 0 for d in target_size):
            self.status_var.set("基準画像のリサイズ後サイズが0以下になります")
            return None

        output_format = self._resolve_output_format_for_image(reference_job.image)
        return reference_job, target_size, output_format

    def _preview_current(self):
        if self.current_index is None:
            return
        self._start_async_preview(self.current_index)

    def _start_async_preview(self, job_index: Optional[int] = None) -> None:
        if self.current_index is None:
            return
        if job_index is None:
            job_index = self.current_index
        if job_index < 0 or job_index >= len(self.jobs):
            return

        job = self.jobs[job_index]
        source = job.image
        target_size = self._snapshot_resize_target(source.size)
        self._preview_version += 1
        version = self._preview_version

        if not target_size:
            self.after(
                0,
                lambda: self._apply_async_preview_result(job_index, None, version, target_size=None),
            )
            return

        if job.resized is not None and job.preview_target_size == target_size:
            self.after(
                0,
                lambda: self._apply_async_preview_result(
                    job_index,
                    job.resized,
                    version,
                    target_size=target_size,
                ),
            )
            return

        self._show_single_processing_placeholders(
            version=version,
            title_text="リサイズ後 (処理中)",
            status_text="処理中...",
            file_name=job.path.name,
        )
        self.info_resized_var.set("計算中...")
        self.resized_title_label.configure(text="リサイズ後 (処理中)")

        def worker() -> None:
            resized: Optional[Image.Image] = None
            try:
                resized = self._resize_image_to_target(source, target_size)
            except Exception:
                logging.exception("プレビュー生成に失敗")
            if version != self._preview_version:
                return
            if self.current_index is None:
                return
            self.after(
                0,
                lambda: self._apply_async_preview_result(job_index, resized, version, target_size=target_size),
            )

        self._preview_thread = threading.Thread(
            target=worker,
            daemon=True,
            name=f"karuku-preview-{job_index}",
        )
        self._preview_thread.start()

    def _apply_async_preview_result(
        self,
        job_index: int,
        resized: Optional[Image.Image],
        version: int,
        *,
        target_size: Optional[Tuple[int, int]],
    ) -> None:
        if version != self._preview_version:
            return
        self._hide_single_processing_placeholders(version=version)
        if self.current_index != job_index:
            return
        if job_index < 0 or job_index >= len(self.jobs):
            return
        if resized is None:
            self.status_var.set("リサイズ設定が無効です")
            self.jobs[job_index].resized = None
            self.jobs[job_index].preview_target_size = None
            self._draw_previews(self.jobs[job_index])
            return
        self.jobs[job_index].resized = resized
        self.jobs[job_index].preview_target_size = target_size
        self._draw_previews(self.jobs[job_index])

    def _save_current(self):
        ui_bootstrap.bootstrap_save_current(self)

    def _confirm_batch_save(
        self,
        reference_job: ImageJob,
        reference_target: Tuple[int, int],
        reference_format_label: str,
        batch_options: SaveOptions,
        output_dir: Path,
    ) -> bool:
        return ui_bootstrap.bootstrap_confirm_batch_save(
            self,
            reference_job=reference_job,
            reference_target=reference_target,
            reference_format_label=reference_format_label,
            batch_options=batch_options,
            output_dir=output_dir,
        )

    def _select_batch_output_dir(self) -> Optional[Path]:
        return ui_bootstrap.bootstrap_select_batch_output_dir(self)

    def _prepare_batch_ui(self) -> None:
        ui_bootstrap.bootstrap_prepare_batch_ui(self)

    def _process_single_batch_job(
        self,
        job: ImageJob,
        output_dir: Path,
        reference_target: Tuple[int, int],
        reference_output_format: SaveFormat,
        batch_options: SaveOptions,
        stats: BatchSaveStats,
    ) -> None:
        ui_bootstrap.bootstrap_process_single_batch_job(
            self,
            job=job,
            output_dir=output_dir,
            reference_target=reference_target,
            reference_output_format=reference_output_format,
            batch_options=batch_options,
            stats=stats,
        )

    def _create_batch_stats(self) -> BatchSaveStats:
        return BatchSaveStats()

    def _run_batch_save(
        self,
        output_dir: Path,
        reference_target: Tuple[int, int],
        reference_output_format: SaveFormat,
        batch_options: SaveOptions,
        target_jobs: Optional[List[ImageJob]] = None,
    ) -> tuple[BatchSaveStats, int]:
        return ui_bootstrap.bootstrap_run_batch_save(
            self,
            output_dir=output_dir,
            reference_target=reference_target,
            reference_output_format=reference_output_format,
            batch_options=batch_options,
            target_jobs=target_jobs,
        )

    def _record_batch_run_summary(
        self,
        *,
        stats: BatchSaveStats,
        output_dir: Path,
        selected_count: int,
        reference_job: ImageJob,
        reference_target: Tuple[int, int],
        reference_format_label: str,
        batch_options: SaveOptions,
    ) -> None:
        ui_bootstrap.bootstrap_record_batch_run_summary(
            self,
            stats=stats,
            output_dir=output_dir,
            selected_count=selected_count,
            reference_job=reference_job,
            reference_target=reference_target,
            reference_format_label=reference_format_label,
            batch_options=batch_options,
        )

    def _batch_save(self):
        ui_bootstrap.bootstrap_batch_save(self)

    def _cancel_batch_save(self):
        ui_bootstrap.bootstrap_cancel_batch_save(self)

    def _cancel_active_operation(self):
        if self._single_save_thread is not None and self._single_save_thread.is_alive():
            self._single_save_cancel_event.set()
            self._set_operation_stage("停止中")
            self.status_var.set("保存処理を停止しています")
            return
        if self._is_loading_files:
            self._cancel_file_loading()
            return
        self._cancel_batch_save()

    def _draw_previews(self, job: ImageJob):
        """Draw original and resized previews on canvases."""
        # Original
        self._imgtk_org = self._draw_image_on_canvas(self.canvas_org, job.image, is_resized=False)
        size = job.image.size
        source_size_kb = (job.source_size_bytes / 1024) if job.source_size_bytes > 0 else 0.0
        self.info_orig_var.set(f"{size[0]} x {size[1]}  {source_size_kb:.1f}KB")

        # Resized
        if job.resized:
            self._imgtk_resz = self._draw_image_on_canvas(self.canvas_resz, job.resized, is_resized=True)
            size = job.resized.size
            output_format = self._resolve_output_format_for_image(job.image)

            orig_w, orig_h = job.image.size
            pct = (size[0] * size[1]) / (orig_w * orig_h) * 100
            fmt_label = FORMAT_ID_TO_LABEL.get(output_format, "JPEG")
            self.info_resized_var.set(f"{size[0]}px x {size[1]}px. 計算中... ({pct:.1f}%) [{fmt_label}]")
            self.resized_title_label.configure(text=f"リサイズ後 ({self._current_resize_settings_text()})")
            self._start_preview_size_estimation(
                job=job,
                source=job.resized,
                output_format=output_format,
                pct=pct,
                fmt_label=fmt_label,
            )
        else:
            self.canvas_resz.delete("all")
            self.info_resized_var.set("--- x ---  ---  (---)")
            self.resized_title_label.configure(text="リサイズ後")

    def _format_preview_size_with_reduction(self, source_bytes: int, estimated_kb: float) -> str:
        if source_bytes <= 0 or estimated_kb <= 0:
            return ""
        source_kb = source_bytes / 1024
        if source_kb <= 0:
            return ""
        ratio = (estimated_kb / source_kb) * 100
        ratio_int = int(round(ratio))
        return f" /オリジナルの約{ratio_int}%"

    def _start_preview_size_estimation(
        self,
        *,
        job: ImageJob,
        source: Image.Image,
        output_format: SaveFormat,
        pct: float,
        fmt_label: str,
    ) -> None:
        quality, webp_method, avif_speed, webp_lossless = self._snapshot_encoder_settings()
        quality_for_preview = min(quality, PREVIEW_ESTIMATION_FAST_QUALITY)
        cache_key = (
            source.width,
            source.height,
            source.mode,
            output_format,
            quality_for_preview,
            webp_method,
            avif_speed,
            bool(webp_lossless),
        )
        cached_entry = job.preview_size_cache.get(cache_key)
        if cached_entry is not None:
            cached_kb, _ = cached_entry
            if cached_kb > 0:
                reduction_text = self._format_preview_size_with_reduction(
                    job.source_size_bytes,
                    cached_kb,
                )
                self.info_resized_var.set(
                    f"{source.width}px x {source.height}px. {cached_kb:.1f}KB "
                    f"({pct:.1f}%) [{fmt_label}]{reduction_text}"
                )
                return

        self._size_estimation_version += 1
        version = self._size_estimation_version
        request_key = (id(job), cache_key)
        if self._size_estimation_inflight_key == request_key:
            return
        self._size_estimation_inflight_key = request_key
        if self._size_estimation_timeout_id is not None:
            try:
                self.after_cancel(self._size_estimation_timeout_id)
            except Exception:
                pass
            self._size_estimation_timeout_id = None
        self.info_resized_var.set(f"{source.width}px x {source.height}px. 計算中... ({pct:.1f}%) [{fmt_label}]")

        def mark_timeout() -> None:
            if self._size_estimation_version != version:
                return
            if self._size_estimation_inflight_key != request_key:
                return
            if self.current_index is None or self.current_index >= len(self.jobs):
                return
            self.info_resized_var.set(
                f"{source.width}px x {source.height}px. 計算時間が長いため省略表示 ({pct:.1f}%) [{fmt_label}]"
            )
            self._size_estimation_inflight_key = None
            self._size_estimation_timeout_id = None

        self._size_estimation_timeout_id = self.after(
            PREVIEW_ESTIMATION_TIMEOUT_MS,
            mark_timeout,
        )

        def worker() -> None:
            save_img = source
            estimated = False
            sample_scale = 1.0
            source_pixels = source.width * source.height
            if source_pixels > PREVIEW_ESTIMATION_SAMPLE_MAX_PIXELS:
                estimated = True
                sample_scale = math.sqrt(PREVIEW_ESTIMATION_SAMPLE_MAX_PIXELS / source_pixels)
                sample_size = (
                    max(1, int(source.width * sample_scale)),
                    max(1, int(source.height * sample_scale)),
                )
                save_img = source.resize(sample_size, Image.Resampling.LANCZOS)
            if output_format in {"jpeg", "avif"} and save_img.mode in {"RGBA", "LA", "P"}:
                save_img = save_img.convert("RGB")
            preview_kwargs = build_encoder_save_kwargs(
                output_format=output_format,
                quality=quality_for_preview,
                webp_method=webp_method,
                webp_lossless=webp_lossless,
                avif_speed=avif_speed,
                for_preview=True,
            )
            try:
                with io.BytesIO() as bio:
                    save_img.save(bio, **cast(Dict[str, Any], preview_kwargs))
                    kb = len(bio.getvalue()) / 1024
                if estimated and sample_scale > 0:
                    sample_area = sample_scale * sample_scale
                    if sample_area > 0:
                        kb = kb / sample_area
            except Exception:
                kb = 0.0

            if version != self._size_estimation_version:
                if self._size_estimation_inflight_key == request_key:
                    self._size_estimation_inflight_key = None
                if self._size_estimation_timeout_id is not None:
                    try:
                        self.after_cancel(self._size_estimation_timeout_id)
                    except Exception:
                        pass
                    self._size_estimation_timeout_id = None
                return

            def apply() -> None:
                if version != self._size_estimation_version:
                    return
                if self.current_index is None or self.current_index >= len(self.jobs):
                    return
                if kb > 0:
                    job.preview_size_cache[cache_key] = (kb, estimated)
                if self._size_estimation_inflight_key == request_key:
                    self._size_estimation_inflight_key = None
                if self._size_estimation_timeout_id is not None:
                    try:
                        self.after_cancel(self._size_estimation_timeout_id)
                    except Exception:
                        pass
                    self._size_estimation_timeout_id = None
                reduction_text = self._format_preview_size_with_reduction(job.source_size_bytes, kb)
                if kb > 0:
                    self.info_resized_var.set(
                        f"{source.width}px x {source.height}px. {kb:.1f}KB "
                        f"({pct:.1f}%) [{fmt_label}]{reduction_text}"
                    )
                else:
                    self.info_resized_var.set(
                        f"{source.width}px x {source.height}px. 変換情報を取得できませんでした ({pct:.1f}%) [{fmt_label}]"
                    )

            self.after(0, apply)

        thread = threading.Thread(
            target=worker,
            daemon=True,
            name="karuku-preview-size-estimation",
        )
        thread.start()

    def _draw_image_on_canvas(self, canvas: customtkinter.CTkCanvas, img: Image.Image, is_resized: bool) -> Optional[ImageTk.PhotoImage]:
        canvas.delete("all")
        canvas_w, canvas_h = canvas.winfo_width(), canvas.winfo_height()
        if canvas_w <= 1 or canvas_h <= 1:  # Canvas not ready
            return None

        zoom_attr = "_zoom_resz" if is_resized else "_zoom_org"
        zoom = getattr(self, zoom_attr)
        label = f"{int(zoom*100)}%" if zoom is not None else "画面に合わせる"

        if zoom is None:  # Fit to screen
            if img.width > 0 and img.height > 0:
                zoom = min(canvas_w / img.width, canvas_h / img.height)
            else:
                zoom = 1.0  # Fallback for zero-sized images
            label = f"Fit ({int(zoom*100)}%)"
        
        new_size = (int(img.width * zoom), int(img.height * zoom))
        if new_size[0] <= 0 or new_size[1] <= 0:
            return None # Avoids errors with tiny images
        
        disp = img.resize(new_size, Resampling.LANCZOS)
        imgtk = ImageTk.PhotoImage(disp)

        # Center the image on the canvas
        x = (canvas_w - new_size[0]) // 2
        y = (canvas_h - new_size[1]) // 2
        canvas.create_image(x, y, anchor="nw", image=imgtk)

        # Draw zoom label
        canvas.create_text(
            10, 10, text=label, anchor="nw", fill=self._canvas_label_color(), font=self.font_small
        )
        return imgtk

    def _show_help(self):
        """使い方ヘルプを表示する"""
        HelpDialog(self, HELP_CONTENT).show()

    def _settings_dialog_state(self) -> SettingsDialogState:
        return SettingsDialogState(
            ui_mode_label=self.ui_mode_var.get(),
            appearance_label=self.appearance_mode_var.get(),
            ui_scale_mode=self._normalize_ui_scale_mode(self._ui_scale_mode),
            zoom_preference=self.zoom_var.get(),
            quality=self.quality_var.get(),
            output_format_label=self.output_format_var.get(),
            default_output_dir=str(self.settings.get("default_output_dir", "")),
            default_preset_label=self._preset_label_for_id(
                str(self.settings.get("default_preset_id", "")).strip(),
                PRESET_NONE_LABEL,
            ),
            pro_input_mode=self._normalized_pro_input_mode(
                str(self.settings.get("pro_input_mode", "recursive"))
            ),
            show_tooltips=self._to_bool(self.settings.get("show_tooltips", True)),
        )

    def _settings_dialog_mappings(self) -> SettingsDialogMappings:
        default_output_label = FORMAT_ID_TO_LABEL.get(
            default_gui_settings()["output_format"], "自動"
        )
        return SettingsDialogMappings(
            ui_mode_label_to_id=UI_MODE_LABEL_TO_ID,
            appearance_label_to_id=APPEARANCE_LABEL_TO_ID,
            ui_scale_label_to_id=UI_SCALE_LABEL_TO_ID,
            pro_input_label_to_id=PRO_INPUT_MODE_LABEL_TO_ID,
            ui_mode_id_to_label=UI_MODE_ID_TO_LABEL,
            appearance_id_to_label=APPEARANCE_ID_TO_LABEL,
            ui_scale_id_to_label=UI_SCALE_ID_TO_LABEL,
            pro_input_id_to_label=PRO_INPUT_MODE_ID_TO_LABEL,
            preset_name_to_id=self._preset_name_to_id,
            preset_labels_with_none=self._preset_labels_with_none,
            build_output_format_labels=lambda: main_output_format_labels(self.available_formats),
            output_format_id_to_label=FORMAT_ID_TO_LABEL,
            output_format_fallback_label=default_output_label,
            zoom_preference_values=("画面に合わせる", "100%", "200%", "300%"),
            quality_values=QUALITY_VALUES,
            pro_input_default_fallback_label="フォルダ再帰",
            preset_none_label=PRESET_NONE_LABEL,
            ui_scale_factor=self._ui_scale_factor,
            settings_getter=lambda: self.settings,
        )

    def _apply_settings_dialog_result(self, result: SettingsDialogResult) -> None:
        self.ui_mode_var.set(result.ui_mode_label)
        self.appearance_mode_var.set(result.appearance_label)
        self._apply_ui_scale_mode(
            UI_SCALE_LABEL_TO_ID.get(result.ui_scale_label, self._normalize_ui_scale_mode("normal"))
        )
        self.zoom_var.set(result.zoom_preference)
        self.quality_var.set(result.quality)
        self.output_format_var.set(result.output_format_label)
        self.settings["pro_input_mode"] = result.pro_input_mode_id
        self.settings["default_output_dir"] = result.default_output_dir
        self.settings["default_preset_id"] = result.default_preset_id
        self.settings["show_tooltips"] = bool(result.show_tooltips)
        if not self.settings["show_tooltips"]:
            self._tooltip_manager.hide()

        self._apply_ui_mode()
        self._apply_user_appearance_mode(self._appearance_mode_id(), redraw=True)
        self._apply_zoom_selection()
        self._on_output_format_changed(self.output_format_var.get())
        self._on_quality_changed(self.quality_var.get())
        self._update_settings_summary()
        self._save_current_settings()
        self._refresh_status_indicators()

    def _open_settings_dialog(self) -> None:
        if self._settings_dialog is not None and self._settings_dialog.winfo_exists():
            self._settings_dialog.focus_set()
            return

        callbacks = SettingsDialogCallbacks(
            register_tooltip=self._register_tooltip,
            style_primary_button=self._style_primary_button,
            style_secondary_button=self._style_secondary_button,
            scale_px=self._scale_px,
            on_show_help=self._show_help,
            on_open_preset_manager=lambda: open_preset_manager_dialog(
                self,
                colors=METALLIC_COLORS,
                format_id_to_label=FORMAT_ID_TO_LABEL,
                exif_id_to_label=EXIF_ID_TO_LABEL,
                preset_none_label=PRESET_NONE_LABEL,
            ),
            on_apply=self._apply_settings_dialog_result,
            on_status_set=self.status_var.set,
            on_dialog_closed=lambda: setattr(self, "_settings_dialog", None),
            font_default=self.font_default,
            font_small=self.font_small,
            colors=METALLIC_COLORS,
        )
        self._settings_dialog = open_settings_dialog(
            self,
            state=self._settings_dialog_state(),
            mappings=self._settings_dialog_mappings(),
            callbacks=callbacks,
        )


    def _open_log_folder(self) -> None:
        log_dir = self._run_log_artifacts.log_dir
        try:
            log_dir.mkdir(parents=True, exist_ok=True)
            if os.name == "nt":
                os.startfile(str(log_dir))  # type: ignore[attr-defined]
            elif platform.system() == "Darwin":
                subprocess.Popen(["open", str(log_dir)])
            else:
                subprocess.Popen(["xdg-open", str(log_dir)])
        except Exception as e:
            logging.exception("Failed to open log directory: %s", log_dir)
            messagebox.showerror(
                "ログフォルダを開けません",
                f"ログフォルダを開けませんでした。\n{log_dir}\n\n{e}",
            )

    # -------------------- Zoom controls --------------------------------
    def _reset_zoom(self):
        """Reset zoom to 'Fit to screen' mode."""
        self._zoom_org = None
        self._zoom_resz = None
        self.zoom_var.set("画面に合わせる")

    def _apply_zoom_selection(self, _choice=None):
        """Apply the zoom selection from the combobox."""
        choice = self.zoom_var.get()
        if choice == "画面に合わせる":
            self._zoom_org = None
            self._zoom_resz = None
        else:
            try:
                pct = int(choice.rstrip("%"))
            except ValueError:
                return
            self._zoom_org = pct / 100.0
            self._zoom_resz = pct / 100.0
        if self.current_index is not None and self.current_index < len(self.jobs):
            self._schedule_preview_redraw(delay_ms=ZOOM_PREVIEW_DEBOUNCE_MS)

    def _get_fit_zoom_ratio(self, canvas: customtkinter.CTkCanvas, is_resized: bool) -> float:
        """Calculates the zoom ratio to fit the image to the canvas."""
        if self.current_index is None or self.current_index >= len(self.jobs):
            return 1.0
        job = self.jobs[self.current_index]
        img = job.resized if is_resized and job.resized else job.image
        canvas_w, canvas_h = canvas.winfo_width(), canvas.winfo_height()
        if img and img.width > 0 and img.height > 0:
            return min(canvas_w / img.width, canvas_h / img.height)
        return 1.0

    def _on_zoom(self, event, is_resized: bool):
        if self.current_index is None:
            return
        
        if platform.system() == "Darwin":  # macOS
            delta = event.delta
        else:  # Windows, Linux
            delta = event.delta // 120

        canvas = self.canvas_resz if is_resized else self.canvas_org
        zoom_attr = "_zoom_resz" if is_resized else "_zoom_org"
        current_zoom = getattr(self, zoom_attr)
        
        if current_zoom is None:
            current_zoom = self._get_fit_zoom_ratio(canvas, is_resized)

        if delta > 0:
            new_zoom = min(current_zoom * ZOOM_STEP, MAX_ZOOM)
        else:
            new_zoom = max(current_zoom / ZOOM_STEP, MIN_ZOOM)

        setattr(self, zoom_attr, new_zoom)
        self.zoom_var.set(f"{int(new_zoom*100)}%")
        if self.current_index is not None and self.current_index < len(self.jobs):
            self._schedule_preview_redraw(delay_ms=ZOOM_PREVIEW_DEBOUNCE_MS)

    def _on_root_resize(self, _e):
        if self._topbar_controller is not None:
            self._topbar_controller.apply_density(
                self._topbar_density_window_width(max(self.winfo_width(), MIN_WINDOW_WIDTH))
            )
        # redraw previews if zoom is 'Fit'
        if self._zoom_org is None or self._zoom_resz is None:
            if self.current_index is not None and self.current_index < len(self.jobs):
                self._schedule_preview_redraw(delay_ms=RESIZE_PREVIEW_DEBOUNCE_MS)

# ----------------------------------------------------------------------

def _set_windows_app_user_model_id() -> None:
    if os.name != "nt":
        return
    try:
        import ctypes

        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("tn.KarukuResize")  # type: ignore[attr-defined]
    except Exception:
        logging.exception("Failed to set Windows AppUserModelID")


def main():
    """Package entry point (CLI script)."""
    _set_windows_app_user_model_id()
    app = ResizeApp()
    app.mainloop()


if __name__ == "__main__":
    main()
