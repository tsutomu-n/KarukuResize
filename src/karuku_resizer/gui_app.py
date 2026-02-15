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
from urllib.parse import unquote, urlparse

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
    APPEARANCE_VALUE_TOOLTIPS,
    ENTRY_AND_ACTION_TOOLTIPS,
    FILE_FILTER_VALUE_TOOLTIPS,
    SIZE_MODE_TOOLTIPS,
    TOP_AND_PRESET_TOOLTIPS,
    UI_MODE_VALUE_TOOLTIPS,
)
from karuku_resizer.ui import topbar_layout
from karuku_resizer.ui import settings_header
from karuku_resizer.ui import main_layout
from karuku_resizer.ui import settings_dialog
from karuku_resizer.ui import preset_dialog
from karuku_resizer.ui import result_dialog
from karuku_resizer.ui import input_sources
from karuku_resizer.ui import file_load_session

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
TOPBAR_DENSITY_COMPACT_MAX_WIDTH = topbar_layout.TOPBAR_DENSITY_COMPACT_MAX_WIDTH
TOPBAR_WIDTHS: Dict[str, Dict[str, int]] = topbar_layout.TOPBAR_WIDTHS

# -------------------- UI color constants --------------------
METALLIC_COLORS = {
    # Accent
    "primary": ("#208CFF", "#3BA7FF"),
    "hover": ("#1279E6", "#2794E6"),
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
QUALITY_VALUES = [str(v) for v in range(5, 101, 5)]
WEBP_METHOD_VALUES = [str(v) for v in range(0, 7)]
AVIF_SPEED_VALUES = [str(v) for v in range(0, 11)]
PRO_MODE_RECURSIVE_INPUT_EXTENSIONS = (".jpg", ".jpeg", ".png")
SELECTABLE_INPUT_EXTENSIONS = (".png", ".jpg", ".jpeg", ".webp", ".avif")
FILE_LOAD_FAILURE_PREVIEW_LIMIT = 20
RECENT_SETTINGS_MAX = 6
OPERATION_ONLY_CANCEL_HINT = "中止のみ可能"
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
    "簡易": "simple",
    "プロ": "pro",
}

UI_MODE_ID_TO_LABEL = {v: k for k, v in UI_MODE_LABEL_TO_ID.items()}

APPEARANCE_LABEL_TO_ID = {
    "システム": "system",
    "ライト": "light",
    "ダーク": "dark",
}

APPEARANCE_ID_TO_LABEL = {v: k for k, v in APPEARANCE_LABEL_TO_ID.items()}

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
    # Top bar / input widgets (ui.topbar_layout から動的に初期化される属性)
    select_button: customtkinter.CTkButton
    help_button: customtkinter.CTkButton
    settings_button: customtkinter.CTkButton
    preset_menu: customtkinter.CTkOptionMenu
    preset_var: customtkinter.StringVar
    preset_manage_button: customtkinter.CTkButton
    preview_button: customtkinter.CTkButton
    save_button: customtkinter.CTkButton
    batch_button: customtkinter.CTkButton
    zoom_cb: customtkinter.CTkComboBox
    zoom_var: customtkinter.StringVar
    mode_var: customtkinter.StringVar
    mode_radio_buttons: List[customtkinter.CTkRadioButton]
    ratio_entry: customtkinter.CTkEntry
    entry_w_single: customtkinter.CTkEntry
    entry_h_single: customtkinter.CTkEntry
    entry_w_fixed: customtkinter.CTkEntry
    entry_h_fixed: customtkinter.CTkEntry
    mode_frames: Dict[str, customtkinter.CTkFrame]
    active_mode_frame: Optional[customtkinter.CTkFrame]
    _all_entries: List[customtkinter.CTkEntry]
    _entry_widgets: Dict[str, List[customtkinter.CTkEntry]]
    pct_var: customtkinter.StringVar
    w_var: customtkinter.StringVar
    h_var: customtkinter.StringVar
    _auto_preview_timer: Optional[str]
    settings_header_frame: customtkinter.CTkFrame
    settings_summary_var: customtkinter.StringVar
    settings_summary_label: customtkinter.CTkLabel
    ui_mode_var: customtkinter.StringVar
    ui_mode_segment: customtkinter.CTkSegmentedButton
    appearance_mode_var: customtkinter.StringVar
    appearance_mode_segment: customtkinter.CTkSegmentedButton
    details_toggle_button: customtkinter.CTkButton
    recent_settings_row: customtkinter.CTkFrame
    recent_settings_title_label: customtkinter.CTkLabel
    recent_settings_buttons_frame: customtkinter.CTkFrame
    recent_settings_empty_label: customtkinter.CTkLabel
    detail_settings_frame: customtkinter.CTkFrame
    _recent_settings_max: int
    _merge_processing_values: Callable[[Mapping[str, Any]], Mapping[str, Any]]
    main_content: customtkinter.CTkFrame
    file_list_frame: customtkinter.CTkScrollableFrame
    file_filter_var: customtkinter.StringVar
    file_filter_segment: customtkinter.CTkSegmentedButton
    empty_state_label: customtkinter.CTkLabel
    canvas_org: customtkinter.CTkCanvas
    canvas_resz: customtkinter.CTkCanvas
    info_orig_var: customtkinter.StringVar
    info_resized_var: customtkinter.StringVar
    resized_title_label: customtkinter.CTkLabel
    metadata_frame: customtkinter.CTkFrame
    metadata_textbox: customtkinter.CTkTextbox
    metadata_status_var: customtkinter.StringVar
    metadata_expanded: bool
    operation_stage_var: customtkinter.StringVar
    action_hint_var: customtkinter.StringVar
    session_summary_var: customtkinter.StringVar
    status_var: customtkinter.StringVar
    progress_bar: customtkinter.CTkProgressBar
    cancel_button: customtkinter.CTkButton

    def __init__(self) -> None:
        super().__init__()

        # 設定マネージャー初期化
        self.settings_store = GuiSettingsStore()
        self.settings = self.settings_store.load()
        self.settings["show_tooltips"] = self._to_bool(self.settings.get("show_tooltips", True))
        self.available_formats = supported_output_formats()
        self.preset_store = ProcessingPresetStore()
        self.processing_presets: List[ProcessingPreset] = self.preset_store.load()
        self._preset_name_to_id: Dict[str, str] = {}

        # --- Theme ---
        customtkinter.set_appearance_mode("system")
        customtkinter.set_default_color_theme("blue")
        self.configure(fg_color=METALLIC_COLORS["bg_primary"])

        # -------------------- フォント設定 --------------------
        # システムフォントを使用（Windows: Segoe UI, macOS: SF Pro Display）
        system_font = "Segoe UI" if platform.system() == "Windows" else "SF Pro Display"
        self.font_default = customtkinter.CTkFont(family=system_font, size=14, weight="normal")
        self.font_small = customtkinter.CTkFont(family=system_font, size=12, weight="normal")
        self.font_bold = customtkinter.CTkFont(family=system_font, size=14, weight="bold")

        self.title("画像リサイズツール (DEBUG)" if DEBUG else "画像リサイズツール")
        self.minsize(MIN_WINDOW_WIDTH, MIN_WINDOW_HEIGHT)
        self._window_icon_image: Optional[ImageTk.PhotoImage] = None
        self._apply_window_icon()
        self._tooltip_manager = TooltipManager(
            self,
            enabled_provider=lambda: self._to_bool(self.settings.get("show_tooltips", True)),
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
        self._recent_setting_buttons: List[customtkinter.CTkButton] = []
        self._recent_settings_max = RECENT_SETTINGS_MAX
        self._merge_processing_values = merge_processing_values
        self._run_log_artifacts: RunLogArtifacts = create_run_log_artifacts(
            app_name=LOG_APP_NAME,
            retention_days=DEFAULT_RETENTION_DAYS,
            max_files=DEFAULT_MAX_FILES,
        )
        self._run_summary_payload = self._create_initial_run_summary()
        self._run_summary_finalized = False
        self._topbar_density = "normal"

        self._setup_ui()
        self._setup_tooltips()
        self._setup_keyboard_shortcuts()
        self._setup_drag_and_drop()
        self._refresh_preset_menu(selected_preset_id=self.settings.get("default_preset_id", ""))
        self._restore_settings()
        self._apply_default_preset_if_configured()
        self._apply_log_level()
        self._write_run_summary_safe()

        self.after(0, self._update_mode)  # set initial enable states
        self.after(0, self._refresh_status_indicators)
        logging.info("ResizeApp initialized")
        logging.info("Run log: %s", self._run_log_artifacts.run_log_path)
        logging.info("Run summary: %s", self._run_log_artifacts.summary_path)

    def _create_initial_run_summary(self) -> Dict[str, Any]:
        started_at = datetime.now().isoformat(timespec="seconds")
        return {
            "run_id": self._run_log_artifacts.run_id,
            "started_at": started_at,
            "finished_at": None,
            "app_name": LOG_APP_NAME,
            "platform": platform.platform(),
            "python_version": platform.python_version(),
            "log_file": str(self._run_log_artifacts.run_log_path),
            "summary_file": str(self._run_log_artifacts.summary_path),
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

    def _write_run_summary_safe(self) -> None:
        try:
            write_run_summary(self._run_log_artifacts.summary_path, self._run_summary_payload)
        except Exception:
            logging.exception("Failed to write run summary")

    def _finalize_run_summary(self) -> None:
        if self._run_summary_finalized:
            return
        self._run_summary_payload["finished_at"] = datetime.now().isoformat(timespec="seconds")
        self._run_summary_finalized = True
        self._write_run_summary_safe()

    def _ensure_run_log_handler(self) -> None:
        root_logger = logging.getLogger()
        run_log_path = self._run_log_artifacts.run_log_path
        log_dir = self._run_log_artifacts.log_dir

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
        handler.setFormatter(
            logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s")
        )
        root_logger.addHandler(handler)

    def _style_primary_button(self, button: customtkinter.CTkButton) -> None:
        button.configure(
            fg_color=METALLIC_COLORS["primary"],
            hover_color=METALLIC_COLORS["hover"],
            text_color=METALLIC_COLORS["text_primary"],
            corner_radius=8,
            border_width=0,
        )

    def _style_secondary_button(self, button: customtkinter.CTkButton) -> None:
        button.configure(
            fg_color=METALLIC_COLORS["bg_tertiary"],
            hover_color=METALLIC_COLORS["accent_soft"],
            text_color=METALLIC_COLORS["text_primary"],
            border_width=1,
            border_color=METALLIC_COLORS["border_light"],
            corner_radius=8,
        )

    def _style_outline_button(self, button: customtkinter.CTkButton) -> None:
        button.configure(
            fg_color="transparent",
            hover_color=METALLIC_COLORS["accent_soft"],
            text_color=METALLIC_COLORS["primary"],
            border_width=2,
            border_color=METALLIC_COLORS["primary"],
            corner_radius=8,
        )

    def _style_tertiary_button(self, button: customtkinter.CTkButton) -> None:
        button.configure(
            fg_color="transparent",
            hover_color=METALLIC_COLORS["bg_tertiary"],
            text_color=METALLIC_COLORS["text_secondary"],
            border_width=1,
            border_color=METALLIC_COLORS["border_light"],
            corner_radius=8,
        )

    @staticmethod
    def _runtime_base_dir() -> Path:
        # PyInstaller onefile展開先では sys._MEIPASS を優先する。
        if getattr(sys, "frozen", False):
            meipass = getattr(sys, "_MEIPASS", None)
            if meipass:
                return Path(str(meipass))
            return Path(sys.executable).resolve().parent
        return Path(__file__).resolve().parents[2]

    @classmethod
    def _resolve_icon_paths(cls) -> Tuple[Optional[Path], Optional[Path]]:
        base = cls._runtime_base_dir()
        ico = base / "assets" / "app.ico"
        png = base / "img" / "karuku.png"
        return (ico if ico.is_file() else None, png if png.is_file() else None)

    def _apply_window_icon(self) -> None:
        ico_path, png_path = self._resolve_icon_paths()

        if platform.system() == "Windows" and ico_path is not None:
            try:
                self.iconbitmap(default=str(ico_path))
            except Exception:
                logging.exception("Failed to set Windows window icon via iconbitmap: %s", ico_path)

        if png_path is not None:
            try:
                self._window_icon_image = ImageTk.PhotoImage(file=str(png_path))
                self.iconphoto(True, cast(Any, self._window_icon_image))
            except Exception:
                logging.exception("Failed to set window icon via iconphoto: %s", png_path)

    def _style_card_frame(self, frame: customtkinter.CTkFrame, corner_radius: int = 12) -> None:
        frame.configure(
            fg_color=METALLIC_COLORS["bg_secondary"],
            border_width=1,
            border_color=METALLIC_COLORS["border_light"],
            corner_radius=corner_radius,
        )

    def _canvas_background_color(self) -> str:
        appearance = customtkinter.get_appearance_mode()
        return "#EEF3FA" if appearance == "Light" else "#111722"

    def _canvas_label_color(self) -> str:
        appearance = customtkinter.get_appearance_mode()
        return "#1F2A37" if appearance == "Light" else "#E8EEF5"

    @staticmethod
    def _normalize_appearance_mode(value: str) -> str:
        normalized = str(value).strip().lower()
        if normalized not in APPEARANCE_ID_TO_LABEL:
            return "system"
        return normalized

    @staticmethod
    def _to_bool(value: Any) -> bool:
        if isinstance(value, bool):
            return value
        return str(value).strip().lower() in {"1", "true", "yes", "on"}

    def _setup_keyboard_shortcuts(self) -> None:
        self.bind_all("<Control-p>", lambda event: self._handle_shortcut_action(event, self._preview_current))
        self.bind_all("<Control-s>", lambda event: self._handle_shortcut_action(event, self._save_current))
        self.bind_all("<Control-Shift-S>", lambda event: self._handle_shortcut_action(event, self._batch_save))

    def _handle_shortcut_action(self, _event: Any, action: Callable[[], None]) -> str:
        if self._is_modal_dialog_open():
            return "break"
        action()
        return "break"

    def _is_modal_dialog_open(self) -> bool:
        dialogs = [self._settings_dialog, self._preset_dialog, self._result_dialog]
        return any(dialog is not None and dialog.winfo_exists() for dialog in dialogs)

    def _register_tooltip(self, widget: Any, text: str) -> None:
        if widget is None:
            return
        try:
            self._tooltip_manager.register(widget, text)
        except Exception:
            logging.exception("Tooltip registration failed for widget %s", widget)

    def _register_segmented_value_tooltips(
        self,
        segmented: Any,
        text_by_value: Mapping[str, str],
    ) -> None:
        buttons_dict = getattr(segmented, "_buttons_dict", None)
        if not isinstance(buttons_dict, dict):
            return
        for value, text in text_by_value.items():
            button = buttons_dict.get(value)
            if button is None:
                continue
            self._register_tooltip(button, text)

    def _register_tooltip_by_name(self, attr_name: str, text: str) -> None:
        widget = getattr(self, attr_name, None)
        self._register_tooltip(widget, text)

    @staticmethod
    def _recent_setting_tooltip_text(entry: Mapping[str, Any]) -> str:
        used_at = str(entry.get("used_at", "")).strip()
        if used_at:
            return (
                "この設定を再適用します。\n"
                f"最終利用は {used_at} です。"
            )
        return "この設定を再適用します。"

    def _setup_tooltips(self) -> None:
        for attr_name, text in TOP_AND_PRESET_TOOLTIPS.items():
            self._register_tooltip_by_name(attr_name, text)

        for button, text in zip(self.mode_radio_buttons, SIZE_MODE_TOOLTIPS):
            self._register_tooltip(button, text)

        for attr_name, text in ENTRY_AND_ACTION_TOOLTIPS.items():
            self._register_tooltip_by_name(attr_name, text)

        for attr_name, text in ADVANCED_CONTROL_TOOLTIPS.items():
            self._register_tooltip_by_name(attr_name, text)

        self._register_segmented_value_tooltips(
            self.ui_mode_segment,
            UI_MODE_VALUE_TOOLTIPS,
        )
        self._register_segmented_value_tooltips(
            self.appearance_mode_segment,
            APPEARANCE_VALUE_TOOLTIPS,
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
                base_label = f"🔒 {base_label}"
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
            self.preset_var.set(current_label)
        else:
            self.preset_var.set(labels[0])

    def _set_selected_preset_label_by_id(self, preset_id: str) -> None:
        for label, mapped_id in self._preset_name_to_id.items():
            if mapped_id == preset_id:
                self.preset_var.set(label)
                return
        if self._preset_name_to_id:
            self.preset_var.set(next(iter(self._preset_name_to_id.keys())))
        else:
            self.preset_var.set(PRESET_NONE_LABEL)

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
        if output_label not in self._build_output_format_labels():
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

    def _on_preset_menu_changed(self, _value: str) -> None:
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
        preset_dialog.open_preset_manager_dialog(
            self,
            colors=METALLIC_COLORS,
            format_id_to_label=FORMAT_ID_TO_LABEL,
            exif_id_to_label=EXIF_ID_TO_LABEL,
            preset_none_label=PRESET_NONE_LABEL,
        )

    def _setup_ui(self):
        """UI要素をセットアップ。上部UI構築は専用モジュールに委譲する。"""
        topbar_layout.setup_ui(
            self,
            colors=METALLIC_COLORS,
            preset_none_label=PRESET_NONE_LABEL,
        )

    def _setup_settings_layers(self):
        """基本操作の下に設定サマリーと詳細設定（折りたたみ）を配置する。"""
        settings_header.setup_settings_layers(
            self,
            colors=METALLIC_COLORS,
            ui_mode_labels=list(UI_MODE_LABEL_TO_ID.keys()),
            appearance_labels=list(APPEARANCE_LABEL_TO_ID.keys()),
        )

    def _register_setting_watchers(self):
        settings_header.register_setting_watchers(self)

    def _on_setting_var_changed(self, *_args):
        settings_header.on_setting_var_changed(self, *_args)

    @staticmethod
    def _recent_setting_label_from_values(values: Mapping[str, Any]) -> str:
        return settings_header.recent_setting_label_from_values(
            values,
            merge_processing_values_fn=merge_processing_values,
            format_id_to_label=FORMAT_ID_TO_LABEL,
        )

    @staticmethod
    def _recent_settings_fingerprint(values: Mapping[str, Any]) -> str:
        return settings_header.recent_settings_fingerprint(
            values,
            merge_processing_values_fn=merge_processing_values,
        )

    @classmethod
    def _normalize_recent_settings_entries(cls, raw: Any) -> List[Dict[str, Any]]:
        return settings_header.normalize_recent_settings_entries(
            raw,
            recent_settings_max=RECENT_SETTINGS_MAX,
            merge_processing_values_fn=merge_processing_values,
            recent_settings_fingerprint_fn=cls._recent_settings_fingerprint,
            recent_setting_label_fn=cls._recent_setting_label_from_values,
        )

    def _recent_settings_entries(self) -> List[Dict[str, Any]]:
        return settings_header.recent_settings_entries(self)

    def _refresh_recent_settings_buttons(self) -> None:
        settings_header.refresh_recent_settings_buttons(self)

    def _apply_recent_setting(self, fingerprint: str) -> None:
        settings_header.apply_recent_setting(self, fingerprint)

    def _register_recent_setting_from_current(self) -> None:
        settings_header.register_recent_setting_from_current(self)

    @staticmethod
    def _topbar_density_for_width(window_width: int) -> str:
        return topbar_layout.topbar_density_for_width(window_width)

    @staticmethod
    def _batch_button_text_for_density(density: str) -> str:
        return topbar_layout.batch_button_text_for_density(density)

    def _select_button_text_for_state(self) -> str:
        return topbar_layout.select_button_text_for_state(self)

    def _apply_topbar_density(self, window_width: int) -> None:
        topbar_layout.apply_topbar_density(self, window_width, min_window_width=MIN_WINDOW_WIDTH)

    def _refresh_topbar_density(self) -> None:
        topbar_layout.refresh_topbar_density(self, min_window_width=MIN_WINDOW_WIDTH)

    def _ui_mode_id(self) -> str:
        return UI_MODE_LABEL_TO_ID.get(self.ui_mode_var.get(), "simple")

    def _is_pro_mode(self) -> bool:
        return self._ui_mode_id() == "pro"

    def _appearance_mode_id(self) -> str:
        return APPEARANCE_LABEL_TO_ID.get(self.appearance_mode_var.get(), "system")

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
        self._update_settings_summary()
        if self.current_index is not None:
            self._draw_previews(self.jobs[self.current_index])

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
        self.select_button.configure(text=self._select_button_text_for_state())
        if self._is_loading_files:
            self.select_button.configure(state="disabled")

        if pro_mode:
            if self.advanced_controls_frame.winfo_manager() != "pack":
                self.advanced_controls_frame.pack(side="top", fill="x", padx=10, pady=(0, 6))
            if self.codec_controls_frame.winfo_manager() != "pack":
                self.codec_controls_frame.pack(side="top", fill="x", padx=10, pady=(0, 6))
        else:
            self.advanced_controls_frame.pack_forget()
            self.codec_controls_frame.pack_forget()

        self._update_codec_controls_state()
        self._toggle_exif_edit_fields()
        self._apply_log_level()
        self._update_metadata_panel_state()
        self._update_empty_state_hint()
        self._refresh_recent_settings_buttons()

    def _update_settings_summary(self):
        changes: list[str] = []
        if self.output_format_var.get() != "自動":
            changes.append(f"形式: {self.output_format_var.get()}")
        if self.quality_var.get() != "85":
            changes.append(f"品質: {self.quality_var.get()}")
        if self.exif_mode_var.get() != "保持":
            changes.append(f"EXIF: {self.exif_mode_var.get()}")
        if self.remove_gps_var.get():
            changes.append("GPS削除")
        if self.dry_run_var.get():
            changes.append("ドライラン ON")
        format_id = FORMAT_LABEL_TO_ID.get(self.output_format_var.get(), "auto")
        if self._is_pro_mode() and format_id == "webp" and self.webp_method_var.get() != "6":
            changes.append(f"WEBP method {self.webp_method_var.get()}")
        if self._is_pro_mode() and format_id == "webp" and self.webp_lossless_var.get():
            changes.append("WEBP lossless")
        if self._is_pro_mode() and format_id == "avif" and self.avif_speed_var.get() != "6":
            changes.append(f"AVIF speed {self.avif_speed_var.get()}")
        if changes:
            summary = "設定: " + " / ".join(changes)
        else:
            summary = "設定: デフォルト"
        self.settings_summary_var.set(summary)
        self._update_session_summary()

    def _empty_state_text(self) -> str:
        lines = [
            "1. 画像を選択 または ドラッグ&ドロップ",
            "2. サイズ・形式を指定",
            "3. 保存 または 一括適用保存",
        ]
        if self._is_pro_mode():
            lines.append("プロ: フォルダー投入で再帰読込（jpg/jpeg/png）")
        lines.append(f"処理中は {OPERATION_ONLY_CANCEL_HINT}")
        return "\n".join(lines)

    def _update_empty_state_hint(self) -> None:
        if not hasattr(self, "empty_state_label"):
            return
        if self.jobs:
            if self.empty_state_label.winfo_manager():
                self.empty_state_label.pack_forget()
            return
        self.empty_state_label.configure(text=self._empty_state_text())
        if self.empty_state_label.winfo_manager() != "pack":
            self.empty_state_label.pack(fill="x", padx=8, pady=(8, 4))

    def _toggle_details_panel(self):
        self._set_details_panel_visibility(not self.details_expanded)

    def _set_details_panel_visibility(self, expanded: bool):
        self.details_expanded = expanded
        if expanded:
            pack_kwargs = {"side": "top", "fill": "x", "padx": 12, "pady": (0, 8)}
            if hasattr(self, "settings_header_frame") and self.settings_header_frame.winfo_exists():
                self.detail_settings_frame.pack(after=self.settings_header_frame, **pack_kwargs)
            else:
                self.detail_settings_frame.pack(**pack_kwargs)
            self.details_toggle_button.configure(text="詳細設定を隠す")
        else:
            self.detail_settings_frame.pack_forget()
            self.details_toggle_button.configure(text="詳細設定を表示")

    def _setup_entry_widgets(self, parent):
        """入力ウィジェットをセットアップ（実装は専用モジュールへ委譲）。"""
        topbar_layout.setup_entry_widgets(self, parent, colors=METALLIC_COLORS)

    def _schedule_auto_preview(self, *_args: Any) -> None:
        topbar_layout.schedule_auto_preview(self, *_args)

    def _auto_preview(self) -> None:
        topbar_layout.trigger_auto_preview(self)

    def _setup_action_buttons(self, parent):
        """アクションボタンをセットアップ（実装は専用モジュールへ委譲）。"""
        topbar_layout.setup_action_buttons(self, parent, colors=METALLIC_COLORS)

    def _setup_output_controls(self, parent):
        """保存関連の設定コントロールをセットアップ"""
        self.basic_controls_frame = customtkinter.CTkFrame(parent)
        self._style_card_frame(self.basic_controls_frame, corner_radius=10)
        self.basic_controls_frame.pack(side="top", fill="x", padx=10, pady=(10, 6))

        self.output_format_var = customtkinter.StringVar(value="自動")
        self.quality_var = customtkinter.StringVar(value="85")
        self.webp_method_var = customtkinter.StringVar(value="6")
        self.webp_lossless_var = customtkinter.BooleanVar(value=False)
        self.avif_speed_var = customtkinter.StringVar(value="6")
        self.dry_run_var = customtkinter.BooleanVar(value=False)
        self.verbose_log_var = customtkinter.BooleanVar(value=False)
        self.exif_mode_var = customtkinter.StringVar(value="保持")
        self.remove_gps_var = customtkinter.BooleanVar(value=False)

        customtkinter.CTkLabel(
            self.basic_controls_frame,
            text="出力形式",
            font=self.font_small,
            text_color=METALLIC_COLORS["text_secondary"],
        ).pack(side="left", padx=(10, 4), pady=8)
        self.output_format_menu = customtkinter.CTkOptionMenu(
            self.basic_controls_frame,
            variable=self.output_format_var,
            values=self._build_output_format_labels(),
            width=110,
            command=self._on_output_format_changed,
            font=self.font_small,
            fg_color=METALLIC_COLORS["bg_tertiary"],
            button_color=METALLIC_COLORS["primary"],
            button_hover_color=METALLIC_COLORS["hover"],
            text_color=METALLIC_COLORS["text_primary"],
            dropdown_fg_color=METALLIC_COLORS["bg_secondary"],
            dropdown_text_color=METALLIC_COLORS["text_primary"],
        )
        self.output_format_menu.pack(side="left", padx=(0, 12), pady=8)

        customtkinter.CTkLabel(
            self.basic_controls_frame,
            text="品質",
            font=self.font_small,
            text_color=METALLIC_COLORS["text_secondary"],
        ).pack(side="left", padx=(0, 4), pady=8)
        self.quality_menu = customtkinter.CTkOptionMenu(
            self.basic_controls_frame,
            variable=self.quality_var,
            values=QUALITY_VALUES,
            width=90,
            command=self._on_quality_changed,
            font=self.font_small,
            fg_color=METALLIC_COLORS["bg_tertiary"],
            button_color=METALLIC_COLORS["primary"],
            button_hover_color=METALLIC_COLORS["hover"],
            text_color=METALLIC_COLORS["text_primary"],
            dropdown_fg_color=METALLIC_COLORS["bg_secondary"],
            dropdown_text_color=METALLIC_COLORS["text_primary"],
        )
        self.quality_menu.pack(side="left", padx=(0, 12), pady=8)

        customtkinter.CTkLabel(
            self.basic_controls_frame,
            text="EXIF",
            font=self.font_small,
            text_color=METALLIC_COLORS["text_secondary"],
        ).pack(side="left", padx=(0, 4), pady=8)
        self.exif_mode_menu = customtkinter.CTkOptionMenu(
            self.basic_controls_frame,
            variable=self.exif_mode_var,
            values=list(EXIF_LABEL_TO_ID.keys()),
            width=90,
            command=self._on_exif_mode_changed,
            font=self.font_small,
            fg_color=METALLIC_COLORS["bg_tertiary"],
            button_color=METALLIC_COLORS["primary"],
            button_hover_color=METALLIC_COLORS["hover"],
            text_color=METALLIC_COLORS["text_primary"],
            dropdown_fg_color=METALLIC_COLORS["bg_secondary"],
            dropdown_text_color=METALLIC_COLORS["text_primary"],
        )
        self.exif_mode_menu.pack(side="left", padx=(0, 10), pady=8)

        self.remove_gps_check = customtkinter.CTkCheckBox(
            self.basic_controls_frame,
            text="GPS削除",
            variable=self.remove_gps_var,
            font=self.font_small,
            fg_color=METALLIC_COLORS["primary"],
            hover_color=METALLIC_COLORS["hover"],
            border_color=METALLIC_COLORS["border_medium"],
            text_color=METALLIC_COLORS["text_primary"],
        )
        self.remove_gps_check.pack(side="left", padx=(0, 10), pady=8)

        self.dry_run_check = customtkinter.CTkCheckBox(
            self.basic_controls_frame,
            text="ドライラン",
            variable=self.dry_run_var,
            font=self.font_small,
            fg_color=METALLIC_COLORS["primary"],
            hover_color=METALLIC_COLORS["hover"],
            border_color=METALLIC_COLORS["border_medium"],
            text_color=METALLIC_COLORS["text_primary"],
        )
        self.dry_run_check.pack(side="left", padx=(0, 12), pady=8)

        self.advanced_controls_frame = customtkinter.CTkFrame(parent)
        self._style_card_frame(self.advanced_controls_frame, corner_radius=10)
        self.advanced_controls_frame.pack(side="top", fill="x", padx=10, pady=(0, 6))

        self.verbose_log_check = customtkinter.CTkCheckBox(
            self.advanced_controls_frame,
            text="詳細ログ",
            variable=self.verbose_log_var,
            command=self._apply_log_level,
            font=self.font_small,
            fg_color=METALLIC_COLORS["primary"],
            hover_color=METALLIC_COLORS["hover"],
            border_color=METALLIC_COLORS["border_medium"],
            text_color=METALLIC_COLORS["text_primary"],
        )
        self.verbose_log_check.pack(side="left", padx=(10, 8), pady=8)
        self.exif_preview_button = customtkinter.CTkButton(
            self.advanced_controls_frame,
            text="EXIF差分",
            width=95,
            command=self._show_exif_preview_dialog,
            font=self.font_small,
        )
        self._style_tertiary_button(self.exif_preview_button)
        self.exif_preview_button.pack(side="left", padx=(0, 10), pady=8)

        self.open_log_folder_button = customtkinter.CTkButton(
            self.advanced_controls_frame,
            text="ログフォルダ",
            width=110,
            command=self._open_log_folder,
            font=self.font_small,
        )
        self._style_tertiary_button(self.open_log_folder_button)
        self.open_log_folder_button.pack(side="left", padx=(0, 10), pady=8)

        self.codec_controls_frame = customtkinter.CTkFrame(parent)
        self._style_card_frame(self.codec_controls_frame, corner_radius=10)
        self.codec_controls_frame.pack(side="top", fill="x", padx=10, pady=(0, 6))

        customtkinter.CTkLabel(
            self.codec_controls_frame,
            text="WEBP method",
            font=self.font_small,
            text_color=METALLIC_COLORS["text_secondary"],
        ).pack(side="left", padx=(10, 4), pady=8)
        self.webp_method_menu = customtkinter.CTkOptionMenu(
            self.codec_controls_frame,
            variable=self.webp_method_var,
            values=WEBP_METHOD_VALUES,
            width=80,
            command=self._on_webp_method_changed,
            font=self.font_small,
            fg_color=METALLIC_COLORS["bg_tertiary"],
            button_color=METALLIC_COLORS["primary"],
            button_hover_color=METALLIC_COLORS["hover"],
            text_color=METALLIC_COLORS["text_primary"],
            dropdown_fg_color=METALLIC_COLORS["bg_secondary"],
            dropdown_text_color=METALLIC_COLORS["text_primary"],
        )
        self.webp_method_menu.pack(side="left", padx=(0, 8), pady=8)

        self.webp_lossless_check = customtkinter.CTkCheckBox(
            self.codec_controls_frame,
            text="WEBP lossless",
            variable=self.webp_lossless_var,
            command=self._on_codec_setting_changed,
            font=self.font_small,
            fg_color=METALLIC_COLORS["primary"],
            hover_color=METALLIC_COLORS["hover"],
            border_color=METALLIC_COLORS["border_medium"],
            text_color=METALLIC_COLORS["text_primary"],
        )
        self.webp_lossless_check.pack(side="left", padx=(0, 14), pady=8)

        customtkinter.CTkLabel(
            self.codec_controls_frame,
            text="AVIF speed",
            font=self.font_small,
            text_color=METALLIC_COLORS["text_secondary"],
        ).pack(side="left", padx=(0, 4), pady=8)
        self.avif_speed_menu = customtkinter.CTkOptionMenu(
            self.codec_controls_frame,
            variable=self.avif_speed_var,
            values=AVIF_SPEED_VALUES,
            width=80,
            command=self._on_avif_speed_changed,
            font=self.font_small,
            fg_color=METALLIC_COLORS["bg_tertiary"],
            button_color=METALLIC_COLORS["primary"],
            button_hover_color=METALLIC_COLORS["hover"],
            text_color=METALLIC_COLORS["text_primary"],
            dropdown_fg_color=METALLIC_COLORS["bg_secondary"],
            dropdown_text_color=METALLIC_COLORS["text_primary"],
        )
        self.avif_speed_menu.pack(side="left", padx=(0, 8), pady=8)
        customtkinter.CTkLabel(
            self.codec_controls_frame,
            text="(低速=高品質)",
            font=self.font_small,
            text_color=METALLIC_COLORS["text_tertiary"],
        ).pack(side="left", pady=8)

        self._update_codec_controls_state()
        self._setup_exif_edit_fields(parent)

    def _setup_exif_edit_fields(self, parent):
        """EXIF編集フィールドをセットアップ（edit時のみ表示）。"""
        self.exif_edit_frame = customtkinter.CTkFrame(parent)
        self._style_card_frame(self.exif_edit_frame, corner_radius=10)

        self.exif_artist_var = customtkinter.StringVar(value="")
        self.exif_copyright_var = customtkinter.StringVar(value="")
        self.exif_user_comment_var = customtkinter.StringVar(value="")
        self.exif_datetime_original_var = customtkinter.StringVar(value="")

        customtkinter.CTkLabel(
            self.exif_edit_frame,
            text="撮影者",
            font=self.font_small,
            text_color=METALLIC_COLORS["text_secondary"],
        ).pack(side="left", padx=(10, 4), pady=8)
        self.exif_artist_entry = customtkinter.CTkEntry(
            self.exif_edit_frame,
            textvariable=self.exif_artist_var,
            width=124,
            font=self.font_small,
            fg_color=METALLIC_COLORS["input_bg"],
            border_color=METALLIC_COLORS["border_light"],
            text_color=METALLIC_COLORS["text_primary"],
            corner_radius=8,
        )
        self.exif_artist_entry.pack(side="left", padx=(0, 8), pady=8)

        customtkinter.CTkLabel(
            self.exif_edit_frame,
            text="著作権",
            font=self.font_small,
            text_color=METALLIC_COLORS["text_secondary"],
        ).pack(side="left", padx=(0, 4), pady=8)
        self.exif_copyright_entry = customtkinter.CTkEntry(
            self.exif_edit_frame,
            textvariable=self.exif_copyright_var,
            width=144,
            font=self.font_small,
            fg_color=METALLIC_COLORS["input_bg"],
            border_color=METALLIC_COLORS["border_light"],
            text_color=METALLIC_COLORS["text_primary"],
            corner_radius=8,
        )
        self.exif_copyright_entry.pack(side="left", padx=(0, 8), pady=8)

        customtkinter.CTkLabel(
            self.exif_edit_frame,
            text="コメント",
            font=self.font_small,
            text_color=METALLIC_COLORS["text_secondary"],
        ).pack(side="left", padx=(0, 4), pady=8)
        self.exif_comment_entry = customtkinter.CTkEntry(
            self.exif_edit_frame,
            textvariable=self.exif_user_comment_var,
            width=184,
            font=self.font_small,
            fg_color=METALLIC_COLORS["input_bg"],
            border_color=METALLIC_COLORS["border_light"],
            text_color=METALLIC_COLORS["text_primary"],
            corner_radius=8,
        )
        self.exif_comment_entry.pack(side="left", padx=(0, 8), pady=8)

        customtkinter.CTkLabel(
            self.exif_edit_frame,
            text="撮影日時",
            font=self.font_small,
            text_color=METALLIC_COLORS["text_secondary"],
        ).pack(side="left", padx=(0, 4), pady=8)
        self.exif_datetime_entry = customtkinter.CTkEntry(
            self.exif_edit_frame,
            textvariable=self.exif_datetime_original_var,
            width=150,
            placeholder_text="YYYY:MM:DD HH:MM:SS",
            font=self.font_small,
            fg_color=METALLIC_COLORS["input_bg"],
            border_color=METALLIC_COLORS["border_light"],
            text_color=METALLIC_COLORS["text_primary"],
            corner_radius=8,
        )
        self.exif_datetime_entry.pack(side="left", pady=8)

        self._toggle_exif_edit_fields()

    def _build_output_format_labels(self) -> list[str]:
        labels = ["自動", "JPEG", "PNG"]
        if "webp" in self.available_formats:
            labels.append("WEBP")
        if "avif" in self.available_formats:
            labels.append("AVIF")
        return labels

    def _on_quality_changed(self, value: str):
        try:
            raw = int(value)
        except ValueError:
            raw = 85
        normalized = str(normalize_quality(raw))
        if normalized != value:
            self.quality_var.set(normalized)
        if self.current_index is not None:
            self._draw_previews(self.jobs[self.current_index])

    def _on_output_format_changed(self, _value: str):
        self._update_codec_controls_state()
        if self.current_index is not None:
            self._draw_previews(self.jobs[self.current_index])

    def _on_exif_mode_changed(self, _value: str):
        self._toggle_exif_edit_fields()
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
        if self.current_index is not None:
            self._draw_previews(self.jobs[self.current_index])

    def _update_codec_controls_state(self):
        selected_id = FORMAT_LABEL_TO_ID.get(self.output_format_var.get(), "auto")
        webp_state = "normal" if selected_id == "webp" else "disabled"
        avif_state = "normal" if selected_id == "avif" else "disabled"
        self.webp_method_menu.configure(state=webp_state)
        self.webp_lossless_check.configure(state=webp_state)
        self.avif_speed_menu.configure(state=avif_state)

    def _toggle_exif_edit_fields(self):
        is_edit_mode = EXIF_LABEL_TO_ID.get(self.exif_mode_var.get(), "keep") == "edit"
        state = "normal" if is_edit_mode else "disabled"
        for entry in (
            self.exif_artist_entry,
            self.exif_copyright_entry,
            self.exif_comment_entry,
            self.exif_datetime_entry,
        ):
            entry.configure(state=state)

        gps_state = "disabled" if EXIF_LABEL_TO_ID.get(self.exif_mode_var.get(), "keep") == "remove" else "normal"
        if gps_state == "disabled":
            self.remove_gps_var.set(False)
        self.remove_gps_check.configure(state=gps_state)

        should_show_edit_fields = self._is_pro_mode() and is_edit_mode
        if should_show_edit_fields:
            if self.exif_edit_frame.winfo_manager() != "pack":
                self.exif_edit_frame.pack(side="top", fill="x", padx=10, pady=(0, 6))
        else:
            if self.exif_edit_frame.winfo_manager():
                self.exif_edit_frame.pack_forget()

    def _apply_log_level(self):
        level = logging.DEBUG if (self.verbose_log_var.get() and self._is_pro_mode()) else logging.INFO
        root_logger = logging.getLogger()
        root_logger.setLevel(level)
        self._ensure_run_log_handler()

    def _setup_main_layout(self):
        main_layout.setup_main_layout(
            self,
            colors=METALLIC_COLORS,
            default_preview=DEFAULT_PREVIEW,
        )

    def _setup_progress_bar_and_cancel(self):
        main_layout.setup_progress_bar_and_cancel(self, colors=METALLIC_COLORS)

    def _setup_status_bar(self):
        main_layout.setup_status_bar(self, colors=METALLIC_COLORS)

    def _show_operation_stage(self, stage_text: str) -> None:
        main_layout.show_operation_stage(
            self,
            stage_text,
            operation_only_cancel_hint=OPERATION_ONLY_CANCEL_HINT,
        )

    def _hide_operation_stage(self) -> None:
        main_layout.hide_operation_stage(self)

    @staticmethod
    def _shorten_path_for_summary(path_text: str, max_len: int = 46) -> str:
        return main_layout.shorten_path_for_summary(path_text, max_len=max_len)

    def _session_status_text(self) -> str:
        return main_layout.session_status_text(
            self,
            file_filter_label_to_id=FILE_FILTER_LABEL_TO_ID,
            file_filter_id_to_label=FILE_FILTER_ID_TO_LABEL,
        )

    def _update_session_summary(self) -> None:
        main_layout.update_session_summary(
            self,
            file_filter_label_to_id=FILE_FILTER_LABEL_TO_ID,
            file_filter_id_to_label=FILE_FILTER_ID_TO_LABEL,
        )

    def _refresh_status_indicators(self) -> None:
        main_layout.refresh_status_indicators(
            self,
            file_filter_label_to_id=FILE_FILTER_LABEL_TO_ID,
            file_filter_id_to_label=FILE_FILTER_ID_TO_LABEL,
        )

    def _update_action_hint(self) -> None:
        main_layout.update_action_hint(self)

    def _show_progress_with_cancel(
        self,
        cancel_text: str,
        cancel_command: Callable[[], None],
        initial_progress: float,
    ) -> None:
        main_layout.show_progress_with_cancel(
            self,
            cancel_text,
            cancel_command,
            initial_progress,
        )

    def _hide_progress_with_cancel(self) -> None:
        main_layout.hide_progress_with_cancel(self)

    def _build_operation_scope_hooks(self) -> OperationScopeHooks:
        return cast(
            OperationScopeHooks,
            main_layout.build_operation_scope_hooks(
                self,
                operation_scope_hooks_cls=OperationScopeHooks,
            ),
        )

    def _begin_operation_scope(
        self,
        *,
        stage_text: str,
        cancel_text: str,
        cancel_command: Callable[[], None],
        initial_progress: float,
    ) -> None:
        main_layout.begin_operation_scope(
            self,
            operation_scope_cls=OperationScope,
            operation_scope_hooks_cls=OperationScopeHooks,
            stage_text=stage_text,
            cancel_text=cancel_text,
            cancel_command=cancel_command,
            initial_progress=initial_progress,
        )

    def _set_operation_stage(self, stage_text: str) -> None:
        main_layout.set_operation_stage(self, stage_text)

    def _end_operation_scope(self) -> None:
        main_layout.end_operation_scope(self)

    def _setup_left_panel(self):
        main_layout.setup_left_panel(
            self,
            colors=METALLIC_COLORS,
            file_filter_labels=list(FILE_FILTER_LABEL_TO_ID.keys()),
        )

    def _setup_right_panel(self):
        main_layout.setup_right_panel(self, colors=METALLIC_COLORS)

    def _toggle_metadata_panel(self):
        main_layout.toggle_metadata_panel(self)

    def _set_metadata_panel_expanded(self, expanded: bool):
        main_layout.set_metadata_panel_expanded(self, expanded)

    def _set_metadata_text(self, text: str):
        main_layout.set_metadata_text(self, text)

    @staticmethod
    def _decode_exif_value(value: object) -> str:
        return main_layout.decode_exif_value(value)

    def _extract_metadata_text(self, job: ImageJob) -> str:
        return main_layout.extract_metadata_text(
            self,
            job,
            exif_gps_info_tag=EXIF_GPS_INFO_TAG,
            exif_preview_tags=EXIF_PREVIEW_TAGS,
        )

    def _update_metadata_preview(self, job: Optional[ImageJob]):
        main_layout.update_metadata_preview(self, job)

    def _update_metadata_panel_state(self):
        main_layout.update_metadata_panel_state(self)

    def _restore_settings(self):
        """保存された設定を復元"""
        # モード復元
        self.mode_var.set(self.settings["mode"])
        self.ui_mode_var.set(
            UI_MODE_ID_TO_LABEL.get(
                str(self.settings.get("ui_mode", "simple")),
                "簡易",
            )
        )
        saved_appearance = self._normalize_appearance_mode(self.settings.get("appearance_mode", "system"))
        self.appearance_mode_var.set(APPEARANCE_ID_TO_LABEL.get(saved_appearance, "システム"))
        
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
        if output_label not in self._build_output_format_labels():
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
        self._set_metadata_panel_expanded(metadata_panel_expanded)
        self._apply_user_appearance_mode(saved_appearance, redraw=False)
        self._apply_ui_mode()
        self._set_details_panel_visibility(details_expanded)
        self._refresh_topbar_density()
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
        if self._is_loading_files:
            self._file_load_cancel_event.set()
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
        messagebox.showinfo("EXIF差分プレビュー", self._format_exif_preview_message(job, preview, edit_values))

    @staticmethod
    def _trim_preview_text(value: Optional[str], max_len: int = 40) -> str:
        if value is None:
            return ""
        text = value.strip()
        if len(text) <= max_len:
            return text
        return f"{text[: max_len - 3]}..."

    def _format_exif_preview_message(
        self,
        job: ImageJob,
        preview: ExifPreview,
        edit_values: Optional[ExifEditValues],
    ) -> str:
        lines = [
            f"対象: {job.path.name}",
            f"モード: {EXIF_ID_TO_LABEL.get(preview.exif_mode, '保持')}",
            f"元EXIFタグ数: {preview.source_tag_count}",
            f"元GPS情報: {'あり' if preview.source_has_gps else 'なし'}",
        ]

        if preview.exif_mode == "remove":
            lines.append("保存時: EXIFを付与しません（全削除）")
        elif preview.exif_will_be_attached:
            lines.append("保存時: EXIFを付与します")
        else:
            lines.append("保存時: EXIFは付与されません")

        if preview.exif_mode != "remove":
            lines.append(f"GPS: {'削除予定' if preview.gps_removed else '保持予定'}")

        if preview.edited_fields:
            lines.append("編集予定項目:")
            label_map = {
                "Artist": "撮影者",
                "Copyright": "著作権",
                "DateTimeOriginal": "撮影日時",
                "UserComment": "コメント",
            }
            value_map = {
                "Artist": edit_values.artist if edit_values else "",
                "Copyright": edit_values.copyright_text if edit_values else "",
                "DateTimeOriginal": edit_values.datetime_original if edit_values else "",
                "UserComment": edit_values.user_comment if edit_values else "",
            }
            for key in preview.edited_fields:
                display = self._trim_preview_text(value_map.get(key))
                lines.append(f"- {label_map.get(key, key)}: {display}")
        elif preview.exif_mode == "edit":
            lines.append("編集予定項目: なし（入力値が空）")

        if preview.skipped_reason:
            lines.append(f"備考: {preview.skipped_reason}")
        if len(self.jobs) > 1:
            lines.append("注記: 一括保存時は画像ごとに元EXIFが異なるため結果が変わる可能性があります。")

        return "\n".join(lines)

    @staticmethod
    def _validate_exif_datetime(value: str) -> bool:
        try:
            datetime.strptime(value, "%Y:%m:%d %H:%M:%S")
            return True
        except ValueError:
            return False

    def _build_save_options(
        self,
        output_format: SaveFormat,
        exif_edit_values: Optional[ExifEditValues] = None,
    ) -> Optional[SaveOptions]:
        pro_mode = self._is_pro_mode()
        exif_mode = EXIF_LABEL_TO_ID.get(self.exif_mode_var.get(), "keep")
        edit_values = exif_edit_values
        if exif_mode == "edit" and edit_values is None:
            edit_values = self._current_exif_edit_values(show_warning=True, strict=True)
            if edit_values is None:
                return None
        return SaveOptions(
            output_format=output_format,
            quality=self._current_quality(),
            dry_run=self.dry_run_var.get(),
            exif_mode=exif_mode,  # type: ignore[arg-type]
            remove_gps=self.remove_gps_var.get(),
            exif_edit=edit_values if exif_mode == "edit" else None,
            verbose=self.verbose_log_var.get() if pro_mode else False,
            webp_method=self._current_webp_method() if pro_mode else 6,
            webp_lossless=self.webp_lossless_var.get() if pro_mode else False,
            avif_speed=self._current_avif_speed() if pro_mode else 6,
        )

    def _build_single_save_filetypes(self):
        filetypes = [("JPEG", "*.jpg *.jpeg"), ("PNG", "*.png")]
        if "webp" in self.available_formats:
            filetypes.append(("WEBP", "*.webp"))
        if "avif" in self.available_formats:
            filetypes.append(("AVIF", "*.avif"))
        filetypes.append(("All files", "*.*"))
        return filetypes

    def _build_unique_batch_base_path(
        self,
        output_dir: Path,
        stem: str,
        output_format: SaveFormat,
        dry_run: bool,
    ) -> Path:
        base = output_dir / f"{stem}_resized"
        if dry_run:
            return base

        candidate = base
        suffix_index = 1
        while destination_with_extension(candidate, output_format).exists():
            candidate = output_dir / f"{stem}_resized_{suffix_index}"
            suffix_index += 1
        return candidate

    @staticmethod
    def _exif_status_text(result: SaveResult) -> str:
        if result.exif_mode == "remove":
            exif_text = "EXIF: 削除"
        elif result.exif_fallback_without_metadata:
            exif_text = "EXIF: 付与不可（フォールバック保存）"
        elif result.exif_attached:
            exif_text = "EXIF: 付与"
        elif result.exif_requested and result.exif_skipped_reason:
            exif_text = f"EXIF: 未付与（{result.exif_skipped_reason}）"
        elif result.had_source_exif:
            exif_text = "EXIF: なし"
        else:
            exif_text = "EXIF: 元データなし"

        gps_text = " / GPS削除" if result.gps_removed else ""
        edit_text = f" / 編集:{len(result.edited_fields)}項目" if result.edited_fields else ""
        return f"{exif_text}{gps_text}{edit_text}"

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

        self.active_mode_frame = self.mode_frames[mode]
        self.active_mode_frame.pack(side="left")

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

    def _setup_drag_and_drop(self) -> None:
        input_sources.setup_drag_and_drop(
            self,
            tkdnd_available=TKDND_AVAILABLE,
            tkdnd_cls=TkinterDnD,
            dnd_files=DND_FILES,
        )

    @staticmethod
    def _dedupe_paths(paths: List[Path]) -> List[Path]:
        return input_sources.dedupe_paths(paths)

    @staticmethod
    def _is_selectable_input_file(path: Path) -> bool:
        return input_sources.is_selectable_input_file(
            path,
            selectable_input_extensions=SELECTABLE_INPUT_EXTENSIONS,
        )

    @staticmethod
    def _normalize_dropped_path_text(value: str) -> str:
        return input_sources.normalize_dropped_path_text(value)

    def _parse_drop_paths(self, raw_data: Any) -> List[Path]:
        return input_sources.parse_drop_paths(self, raw_data)

    def _on_drop_enter(self, _event: Any) -> str:
        return input_sources.on_drop_enter(COPY, _event)

    def _on_drop_position(self, _event: Any) -> str:
        return input_sources.on_drop_position(COPY, _event)

    def _on_drop_leave(self, _event: Any) -> None:
        return input_sources.on_drop_leave(_event)

    def _on_drop_files(self, event: Any) -> str:
        return input_sources.on_drop_files(
            self,
            event,
            copy_token=COPY,
            selectable_input_extensions=SELECTABLE_INPUT_EXTENSIONS,
        )

    def _handle_dropped_paths(self, dropped_paths: List[Path]) -> None:
        input_sources.handle_dropped_paths(
            self,
            dropped_paths,
            selectable_input_extensions=SELECTABLE_INPUT_EXTENSIONS,
        )

    def _start_drop_load_async(self, files: List[Path], dirs: List[Path]) -> None:
        input_sources.start_drop_load_async(self, files, dirs)

    @staticmethod
    def _scan_and_load_drop_items_worker(
        dropped_files: List[Path],
        dropped_dirs: List[Path],
        cancel_event: threading.Event,
        out_queue: "queue.Queue[Dict[str, Any]]",
    ) -> None:
        input_sources.scan_and_load_drop_items_worker(
            dropped_files,
            dropped_dirs,
            cancel_event,
            out_queue,
            selectable_input_extensions=SELECTABLE_INPUT_EXTENSIONS,
            recursive_extensions=PRO_MODE_RECURSIVE_INPUT_EXTENSIONS,
        )

    # -------------------- file selection -------------------------------
    def _select_files(self):
        input_sources.select_files(self)

    def _select_files_in_simple_mode(self, initial_dir: str) -> Tuple[List[Path], Optional[Path]]:
        return input_sources.select_files_in_simple_mode(initial_dir)

    def _select_files_in_pro_mode(self, initial_dir: str) -> Tuple[List[Path], Optional[Path], bool]:
        return input_sources.select_files_in_pro_mode(self, initial_dir)

    @staticmethod
    def _normalized_pro_input_mode(value: str) -> str:
        return input_sources.normalized_pro_input_mode(value)

    def _start_recursive_load_async(self, root_dir: Path) -> None:
        file_load_session.start_recursive_load_async(self, root_dir)

    def _start_retry_failed_load_async(self, paths: List[Path]) -> None:
        file_load_session.start_retry_failed_load_async(self, paths)

    def _begin_file_load_session(
        self,
        mode_label: str,
        root_dir: Optional[Path],
        clear_existing_jobs: bool,
    ) -> None:
        file_load_session.begin_file_load_session(
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
            self.batch_button,
            self.ui_mode_segment,
            self.appearance_mode_segment,
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
        widgets.extend(self.mode_radio_buttons)
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
            self._update_codec_controls_state()
            self._toggle_exif_edit_fields()
            self._update_settings_summary()
            self._refresh_recent_settings_buttons()
        self._refresh_status_indicators()

    @staticmethod
    def _scan_and_load_images_worker(
        root_dir: Path,
        cancel_event: threading.Event,
        out_queue: "queue.Queue[Dict[str, Any]]",
    ) -> None:
        file_load_session.scan_and_load_images_worker(
            root_dir,
            cancel_event,
            out_queue,
            recursive_extensions=PRO_MODE_RECURSIVE_INPUT_EXTENSIONS,
        )

    @staticmethod
    def _load_paths_worker(
        paths: List[Path],
        cancel_event: threading.Event,
        out_queue: "queue.Queue[Dict[str, Any]]",
    ) -> None:
        file_load_session.load_paths_worker(paths, cancel_event, out_queue)

    @staticmethod
    def _format_duration(seconds: float) -> str:
        return file_load_session.format_duration(seconds)

    def _format_path_for_display(self, path: Path) -> str:
        return file_load_session.format_path_for_display(self, path)

    def _loading_hint_text(self) -> str:
        return file_load_session.loading_hint_text(
            operation_only_cancel_hint=OPERATION_ONLY_CANCEL_HINT
        )

    def _loading_progress_status_text(self, latest_path: Optional[Path] = None, failed: bool = False) -> str:
        return file_load_session.loading_progress_status_text(
            self,
            operation_only_cancel_hint=OPERATION_ONLY_CANCEL_HINT,
            latest_path=latest_path,
            failed=failed,
        )

    def _poll_file_load_queue(self) -> None:
        file_load_session.poll_file_load_queue(self)

    def _handle_file_load_message(self, message: Dict[str, Any]) -> None:
        file_load_session.handle_file_load_message(
            self,
            message,
            operation_only_cancel_hint=OPERATION_ONLY_CANCEL_HINT,
            image_job_cls=ImageJob,
        )

    def _finish_recursive_load(self, canceled: bool) -> None:
        file_load_session.finish_recursive_load(self, canceled)

    def _cancel_file_loading(self) -> None:
        file_load_session.cancel_file_loading(self)

    def _copy_text_to_clipboard(self, text: str) -> bool:
        return result_dialog.copy_text_to_clipboard(self, text)

    def _build_failure_report_text(
        self,
        *,
        title: str,
        summary_text: str,
        failed_details: List[str],
    ) -> str:
        return result_dialog.build_failure_report_text(
            title=title,
            summary_text=summary_text,
            failed_details=failed_details,
        )

    @staticmethod
    def _failure_reason_group(detail_text: str) -> str:
        return result_dialog.failure_reason_group(detail_text)

    @classmethod
    def _group_failure_details(cls, failed_details: List[str]) -> Dict[str, int]:
        return result_dialog.group_failure_details(failed_details)

    @classmethod
    def _failure_center_text(cls, failed_details: List[str]) -> str:
        return result_dialog.failure_center_text(
            failed_details,
            file_load_failure_preview_limit=FILE_LOAD_FAILURE_PREVIEW_LIMIT,
        )

    def _show_operation_result_dialog(
        self,
        *,
        title: str,
        summary_text: str,
        failed_details: List[str],
        retry_callback: Optional[Callable[[], None]] = None,
    ) -> None:
        result_dialog.show_operation_result_dialog(
            self,
            colors=METALLIC_COLORS,
            file_load_failure_preview_limit=FILE_LOAD_FAILURE_PREVIEW_LIMIT,
            title=title,
            summary_text=summary_text,
            failed_details=failed_details,
            retry_callback=retry_callback,
        )

    def _reset_loaded_jobs(self) -> None:
        self.jobs.clear()
        self.current_index = None
        self._visible_job_indices = []
        for button in self.file_buttons:
            button.destroy()
        self.file_buttons = []
        self._clear_preview_panels()
        self._update_empty_state_hint()

    @staticmethod
    def _discover_recursive_image_paths(root_dir: Path) -> List[Path]:
        paths: List[Path] = []
        try:
            for dirpath, _dirnames, filenames in os.walk(root_dir, topdown=True):
                base_dir = Path(dirpath)
                for name in filenames:
                    if Path(name).suffix.lower() in PRO_MODE_RECURSIVE_INPUT_EXTENSIONS:
                        paths.append(base_dir / name)
        except OSError:
            logging.exception("Recursive scan failed: %s", root_dir)
            return []
        paths.sort(key=lambda p: str(p).lower())
        return paths

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
                messagebox.showerror("エラー", f"{path} の読み込みに失敗しました: {e}")
                continue
            self.jobs.append(ImageJob(path, img))

    def _on_file_filter_changed(self, _value: str) -> None:
        self._populate_listbox()

    def _job_passes_file_filter(self, job: ImageJob) -> bool:
        filter_label = self.file_filter_var.get() if hasattr(self, "file_filter_var") else "全件"
        filter_id = FILE_FILTER_LABEL_TO_ID.get(filter_label, "all")
        if filter_id == "failed":
            return job.last_process_state == "failed"
        if filter_id == "unprocessed":
            return job.last_process_state == "unprocessed"
        return True

    @staticmethod
    def _file_button_label(job: ImageJob) -> str:
        if job.last_process_state == "failed":
            return f"⚠ {job.path.name}"
        if job.last_process_state == "success":
            return f"✓ {job.path.name}"
        return job.path.name

    def _populate_listbox(self):
        for button in self.file_buttons:
            button.destroy()
        self.file_buttons = []
        self._visible_job_indices = []
        if not self.jobs:
            self._clear_preview_panels()
            self.status_var.set("有効な画像を読み込めませんでした")
            self._update_empty_state_hint()
            self._refresh_status_indicators()
            return

        for i, job in enumerate(self.jobs):
            if not self._job_passes_file_filter(job):
                continue
            button = customtkinter.CTkButton(
                self.file_list_frame, 
                text=self._file_button_label(job),
                command=lambda idx=i: self._on_select_change(idx),
                fg_color=METALLIC_COLORS["bg_tertiary"],
                hover_color=METALLIC_COLORS["accent_soft"],
                text_color=METALLIC_COLORS["text_primary"],
                border_width=1,
                border_color=METALLIC_COLORS["border_light"],
                corner_radius=8,
            )
            button.pack(fill="x", padx=8, pady=4)
            self._register_tooltip(button, f"この画像を選択します。\n{job.path}")
            self.file_buttons.append(button)
            self._visible_job_indices.append(i)
        self._update_empty_state_hint()
        if self._visible_job_indices:
            if self.current_index in self._visible_job_indices:
                self._on_select_change(self.current_index, force=True)
            else:
                self._on_select_change(self._visible_job_indices[0])
        else:
            self.status_var.set("フィルタ条件に一致する画像がありません。")
            self.empty_state_label.configure(text="フィルタ条件に一致する画像がありません。")
            if self.empty_state_label.winfo_manager() != "pack":
                self.empty_state_label.pack(fill="x", padx=8, pady=(8, 4))
        self._refresh_status_indicators()

    def _clear_preview_panels(self):
        self.current_index = None
        self._imgtk_org = None
        self._imgtk_resz = None
        self.canvas_org.delete("all")
        self.canvas_resz.delete("all")
        self.info_orig_var.set("--- x ---  ---")
        self.info_resized_var.set("--- x ---  ---  (---)")
        self.resized_title_label.configure(text="リサイズ後")
        self._update_metadata_preview(None)
        self._refresh_status_indicators()

    def _visible_button_pos_for_job_index(self, job_index: Optional[int]) -> Optional[int]:
        if job_index is None:
            return None
        try:
            return self._visible_job_indices.index(job_index)
        except ValueError:
            return None

    def _on_select_change(self, idx: Optional[int] = None, force: bool = False) -> None:
        """Handle file selection change."""
        if idx is None:
            if self._visible_job_indices:
                idx = self._visible_job_indices[0]
            else:
                idx = 0
        if idx >= len(self.jobs):
            return
        if self._visible_job_indices and idx not in self._visible_job_indices:
            return
        if (self.current_index == idx) and (not force):
            return

        # Update button highlights
        previous_pos = self._visible_button_pos_for_job_index(self.current_index)
        if previous_pos is not None and previous_pos < len(self.file_buttons):
            self.file_buttons[previous_pos].configure(
                fg_color=METALLIC_COLORS["bg_tertiary"],
                border_color=METALLIC_COLORS["border_light"],
                text_color=METALLIC_COLORS["text_primary"],
            )
        
        self.current_index = idx
        current_pos = self._visible_button_pos_for_job_index(idx)
        if current_pos is not None and current_pos < len(self.file_buttons):
            self.file_buttons[current_pos].configure(
                fg_color=METALLIC_COLORS["accent_soft"],
                border_color=METALLIC_COLORS["primary"],
                text_color=METALLIC_COLORS["text_primary"],
            )
        elif self.file_buttons and idx < len(self.file_buttons):
            self.file_buttons[idx].configure(
            fg_color=METALLIC_COLORS["accent_soft"],
            border_color=METALLIC_COLORS["primary"],
            text_color=METALLIC_COLORS["text_primary"],
            )

        # Update previews and info
        job = self.jobs[idx]
        now = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.status_var.set(f"[{now}] {job.path.name} を選択しました")
        logger.info(f"Selected: {job.path.name}")

        self._reset_zoom()
        self._draw_previews(job)
        self._update_metadata_preview(job)
        self._refresh_status_indicators()

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
        if self._is_loading_files:
            messagebox.showinfo("処理中", "画像の読み込み中です。完了またはキャンセル後に実行してください。")
            return
        if self.current_index is None:
            messagebox.showwarning("ファイル未選択", "ファイルを選択してください")
            return
        job = self.jobs[self.current_index]
        job.resized = self._process_image(job.image)
        self._draw_previews(job)

    def _save_current(self):
        if self._is_loading_files:
            messagebox.showinfo("処理中", "画像の読み込み中です。完了またはキャンセル後に実行してください。")
            return
        if self.current_index is None:
            messagebox.showwarning("ファイル未選択", "ファイルを選択してください")
            return

        job = self.jobs[self.current_index]
        # 直前に設定変更されていても、保存時は必ず最新設定で再計算する
        job.resized = self._process_image(job.image)
        if not job.resized:
            return

        output_format = self._resolve_output_format_for_image(job.image)
        ext_default = destination_with_extension(Path(f"{job.path.stem}_resized"), output_format).suffix
        initial_dir = (
            self.settings.get("last_output_dir")
            or self.settings.get("default_output_dir")
            or Path.home()
        )
        initial_file = f"{job.path.stem}_resized{ext_default}"

        save_path_str = filedialog.asksaveasfilename(
            title="名前を付けて保存",
            initialdir=str(initial_dir),
            initialfile=initial_file,
            filetypes=self._build_single_save_filetypes(),
            defaultextension=ext_default,
        )
        if not save_path_str:
            return

        save_path = Path(save_path_str)
        self.settings["last_output_dir"] = str(save_path.parent)
        options = self._build_save_options(output_format)
        if options is None:
            return
        result = save_image(
            source_image=job.image,
            resized_image=job.resized,
            output_path=save_path,
            options=options,
        )

        if not result.success:
            job.last_process_state = "failed"
            job.last_error_detail = result.error or "保存失敗"
            self._populate_listbox()
            messagebox.showerror("保存エラー", f"ファイルの保存に失敗しました:\n{result.error}")
            return

        job.last_process_state = "success"
        job.last_error_detail = None
        if result.dry_run:
            msg = f"ドライラン完了: {result.output_path.name} を生成予定です"
        else:
            msg = f"{result.output_path.name} を保存しました"
        msg = f"{msg}\n{self._exif_status_text(result)}"
        self._register_recent_setting_from_current()
        self._populate_listbox()
        self.status_var.set(msg)
        messagebox.showinfo("保存結果", msg)

    def _build_batch_save_options(self, reference_output_format: SaveFormat) -> Optional[SaveOptions]:
        exif_mode = EXIF_LABEL_TO_ID.get(self.exif_mode_var.get(), "keep")
        batch_exif_edit_values = (
            self._current_exif_edit_values(show_warning=True, strict=True) if exif_mode == "edit" else None
        )
        if exif_mode == "edit" and batch_exif_edit_values is None:
            return None
        return self._build_save_options(
            reference_output_format, exif_edit_values=batch_exif_edit_values
        )

    @staticmethod
    def _batch_run_mode_text(batch_options: SaveOptions) -> str:
        return "ドライラン（実ファイルは作成しません）" if batch_options.dry_run else "保存"

    def _batch_progress_status_text(
        self,
        *,
        done_count: int,
        total_count: int,
        processed_count: int,
        failed_count: int,
        elapsed_sec: float,
        current_file_name: str,
    ) -> str:
        if done_count <= 0 or total_count <= 0:
            return f"保存中: 0/{total_count}"
        speed = done_count / max(0.001, elapsed_sec)
        remaining_sec = max(0.0, (total_count - done_count) / max(speed, 0.001))
        remaining_text = self._format_duration(remaining_sec)
        return (
            f"保存中 {done_count}/{total_count} (成功{processed_count} 失敗{failed_count}) "
            f"/ 対象: {current_file_name} / 残り約{remaining_text} / {speed:.1f}件/秒"
        )

    def _confirm_batch_save(
        self,
        reference_job: ImageJob,
        reference_target: Tuple[int, int],
        reference_format_label: str,
        batch_options: SaveOptions,
        output_dir: Path,
    ) -> bool:
        return messagebox.askokcancel(
            "一括適用保存の確認",
            f"基準画像: {reference_job.path.name}\n"
            f"適用サイズ: {reference_target[0]} x {reference_target[1]} px\n"
            f"出力形式: {reference_format_label} / 品質: {self.quality_var.get()}\n"
            f"モード: {self._batch_run_mode_text(batch_options)}\n"
            f"EXIF: {self.exif_mode_var.get()} / GPS削除: {'ON' if self.remove_gps_var.get() else 'OFF'}\n"
            f"保存先: {output_dir}\n"
            f"対象枚数: {len(self.jobs)}枚\n\n"
            "読み込み済み全画像に同じ設定を適用して処理します。\n"
            "よろしいですか？",
        )

    def _select_batch_output_dir(self) -> Optional[Path]:
        initial_dir = (
            self.settings.get("last_output_dir")
            or self.settings.get("default_output_dir")
            or self.settings.get("last_input_dir")
            or Path.home()
        )
        output_dir_str = filedialog.askdirectory(title="保存先フォルダを選択", initialdir=str(initial_dir))
        if not output_dir_str:
            return None
        return Path(output_dir_str)

    def _prepare_batch_ui(self) -> None:
        self._cancel_batch = False
        self._begin_operation_scope(
            stage_text="保存中",
            cancel_text="キャンセル",
            cancel_command=self._cancel_active_operation,
            initial_progress=0.0,
        )
        self._refresh_status_indicators()

    def _process_single_batch_job(
        self,
        job: ImageJob,
        output_dir: Path,
        reference_target: Tuple[int, int],
        reference_output_format: SaveFormat,
        batch_options: SaveOptions,
        stats: BatchSaveStats,
    ) -> None:
        resized_img = self._resize_image_to_target(job.image, reference_target)
        if not resized_img:
            job.last_process_state = "failed"
            job.last_error_detail = "リサイズ失敗"
            stats.record_failure(job.path.name, "リサイズ失敗", file_path=job.path)
            return

        out_base = self._build_unique_batch_base_path(
            output_dir=output_dir,
            stem=job.path.stem,
            output_format=reference_output_format,
            dry_run=batch_options.dry_run,
        )
        result = save_image(
            source_image=job.image,
            resized_image=resized_img,
            output_path=out_base,
            options=batch_options,
        )
        if result.success:
            job.last_process_state = "success"
            job.last_error_detail = None
            stats.record_success(result)
            return

        error_detail = result.error or "保存処理で不明なエラー"
        job.last_process_state = "failed"
        job.last_error_detail = error_detail
        stats.record_failure(job.path.name, error_detail, file_path=job.path)
        logging.error(f"Failed to save {result.output_path}: {result.error}")

    def _run_batch_save(
        self,
        output_dir: Path,
        reference_target: Tuple[int, int],
        reference_output_format: SaveFormat,
        batch_options: SaveOptions,
        target_jobs: Optional[List[ImageJob]] = None,
    ) -> BatchSaveStats:
        stats = BatchSaveStats()
        jobs_to_process = list(target_jobs) if target_jobs is not None else list(self.jobs)
        total_files = len(jobs_to_process)
        for job in jobs_to_process:
            job.last_process_state = "unprocessed"
            job.last_error_detail = None
        self._prepare_batch_ui()
        started_at = time.monotonic()

        try:
            for i, job in enumerate(jobs_to_process):
                if self._cancel_batch:
                    break

                try:
                    self._process_single_batch_job(
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
                    self.progress_bar.set(done / total_files if total_files > 0 else 1.0)
                    self.status_var.set(
                        self._batch_progress_status_text(
                            done_count=done,
                            total_count=total_files,
                            processed_count=stats.processed_count,
                            failed_count=stats.failed_count,
                            elapsed_sec=time.monotonic() - started_at,
                            current_file_name=job.path.name,
                        )
                    )
                    self.update_idletasks()
        finally:
            self._end_operation_scope()
            self._populate_listbox()
            self._refresh_status_indicators()

        return stats

    def _build_batch_completion_message(
        self,
        stats: BatchSaveStats,
        reference_job: ImageJob,
        reference_target: Tuple[int, int],
        reference_format_label: str,
        batch_options: SaveOptions,
    ) -> str:
        total_files = len(self.jobs)
        if self._cancel_batch:
            msg = (
                f"一括処理がキャンセルされました。"
                f"({stats.processed_count}/{total_files}件完了)"
            )
        else:
            mode_text = "ドライラン" if batch_options.dry_run else "保存"
            msg = (
                f"一括処理完了。{stats.processed_count}/{total_files}件を{mode_text}しました。"
                f"\n失敗: {stats.failed_count}件 / EXIF付与: {stats.exif_applied_count}件 / EXIFフォールバック: {stats.exif_fallback_count}件 / GPS削除: {stats.gps_removed_count}件"
            )
            msg += (
                f"\n基準: {reference_job.path.name} / "
                f"{reference_target[0]}x{reference_target[1]} / {reference_format_label}"
            )
            if batch_options.dry_run:
                msg += f"\nドライラン件数: {stats.dry_run_count}件"
                msg += "\nドライランのため、実ファイルは作成していません。"
        return msg

    def _record_batch_run_summary(
        self,
        *,
        stats: BatchSaveStats,
        output_dir: Path,
        reference_job: ImageJob,
        reference_target: Tuple[int, int],
        reference_format_label: str,
        batch_options: SaveOptions,
    ) -> None:
        entry = {
            "timestamp": datetime.now().isoformat(timespec="seconds"),
            "mode": "dry-run" if batch_options.dry_run else "save",
            "cancelled": bool(self._cancel_batch),
            "output_dir": str(output_dir),
            "reference_file": reference_job.path.name,
            "reference_target": {
                "width": reference_target[0],
                "height": reference_target[1],
            },
            "reference_format": reference_format_label,
            "totals": {
                "selected_count": len(self.jobs),
                "processed_count": stats.processed_count,
                "failed_count": stats.failed_count,
                "dry_run_count": stats.dry_run_count,
                "exif_applied_count": stats.exif_applied_count,
                "exif_fallback_count": stats.exif_fallback_count,
                "gps_removed_count": stats.gps_removed_count,
            },
            "failed_files": list(stats.failed_details),
        }
        self._run_summary_payload["batch_runs"].append(entry)
        totals = self._run_summary_payload["totals"]
        totals["batch_run_count"] += 1
        totals["processed_count"] += stats.processed_count
        totals["failed_count"] += stats.failed_count
        totals["dry_run_count"] += stats.dry_run_count
        if self._cancel_batch:
            totals["cancelled_count"] += 1
        self._write_run_summary_safe()

    def _batch_save(self):
        if self._is_loading_files:
            messagebox.showinfo("処理中", "画像の読み込み中です。完了またはキャンセル後に実行してください。")
            return
        if not self.jobs:
            messagebox.showwarning("ファイル未選択", "ファイルが選択されていません")
            return

        reference = self._resolve_batch_reference()
        if reference is None:
            messagebox.showwarning("設定エラー", "基準画像の設定が無効です")
            return
        reference_job, reference_target, reference_output_format = reference
        reference_format_label = FORMAT_ID_TO_LABEL.get(
            reference_output_format, reference_output_format.upper()
        )
        batch_options = self._build_batch_save_options(reference_output_format)
        if batch_options is None:
            return

        output_dir = self._select_batch_output_dir()
        if output_dir is None:
            return
        self.settings["last_output_dir"] = str(output_dir)

        if not self._confirm_batch_save(
            reference_job=reference_job,
            reference_target=reference_target,
            reference_format_label=reference_format_label,
            batch_options=batch_options,
            output_dir=output_dir,
        ):
            return

        stats = self._run_batch_save(
            output_dir=output_dir,
            reference_target=reference_target,
            reference_output_format=reference_output_format,
            batch_options=batch_options,
        )
        self._record_batch_run_summary(
            stats=stats,
            output_dir=output_dir,
            reference_job=reference_job,
            reference_target=reference_target,
            reference_format_label=reference_format_label,
            batch_options=batch_options,
        )
        msg = self._build_batch_completion_message(
            stats=stats,
            reference_job=reference_job,
            reference_target=reference_target,
            reference_format_label=reference_format_label,
            batch_options=batch_options,
        )
        if stats.processed_count > 0:
            self._register_recent_setting_from_current()
        self.status_var.set(msg)
        retry_callback: Optional[Callable[[], None]] = None
        if stats.failed_paths and not self._cancel_batch:
            failed_path_set = {path for path in stats.failed_paths}

            def _retry_failed_batch_only() -> None:
                retry_jobs = [job for job in self.jobs if job.path in failed_path_set]
                if not retry_jobs:
                    messagebox.showinfo("再試行", "再試行対象の失敗ファイルが見つかりません。")
                    return
                retry_stats = self._run_batch_save(
                    output_dir=output_dir,
                    reference_target=reference_target,
                    reference_output_format=reference_output_format,
                    batch_options=batch_options,
                    target_jobs=retry_jobs,
                )
                retry_msg = (
                    f"失敗再試行完了。成功: {retry_stats.processed_count}件 / "
                    f"失敗: {retry_stats.failed_count}件 / 対象: {len(retry_jobs)}件"
                )
                self.status_var.set(retry_msg)
                self._show_operation_result_dialog(
                    title="失敗再試行結果",
                    summary_text=retry_msg,
                    failed_details=retry_stats.failed_details,
                    retry_callback=None,
                )

            retry_callback = _retry_failed_batch_only
        self._show_operation_result_dialog(
            title="一括処理結果",
            summary_text=msg,
            failed_details=stats.failed_details,
            retry_callback=retry_callback,
        )

    def _cancel_batch_save(self):
        self._cancel_batch = True
        self._set_operation_stage("キャンセル中")

    def _cancel_active_operation(self):
        if self._is_loading_files:
            self._cancel_file_loading()
            return
        self._cancel_batch_save()

    def _draw_previews(self, job: ImageJob):
        """Draw original and resized previews on canvases."""
        # Original
        self._imgtk_org = self._draw_image_on_canvas(self.canvas_org, job.image, is_resized=False)
        size = job.image.size
        self.info_orig_var.set(f"{size[0]} x {size[1]}  {Path(job.path).stat().st_size/1024:.1f}KB")

        # Resized
        if job.resized:
            self._imgtk_resz = self._draw_image_on_canvas(self.canvas_resz, job.resized, is_resized=True)
            size = job.resized.size
            
            # 出力設定に基づいたサイズ見積もり
            output_format = self._resolve_output_format_for_image(job.image)
            with io.BytesIO() as bio:
                save_img = job.resized
                if output_format in {"jpeg", "avif"} and save_img.mode in {"RGBA", "LA", "P"}:
                    save_img = save_img.convert("RGB")
                preview_kwargs = build_encoder_save_kwargs(
                    output_format=output_format,
                    quality=self._current_quality(),
                    webp_method=self._current_webp_method(),
                    webp_lossless=self.webp_lossless_var.get(),
                    avif_speed=self._current_avif_speed(),
                )
                try:
                    save_img.save(bio, **cast(Dict[str, Any], preview_kwargs))
                    kb = len(bio.getvalue()) / 1024
                except Exception:
                    kb = 0.0
            
            orig_w, orig_h = job.image.size
            pct = (size[0] * size[1]) / (orig_w * orig_h) * 100
            fmt_label = FORMAT_ID_TO_LABEL.get(output_format, "JPEG")
            self.info_resized_var.set(f"{size[0]} x {size[1]}  {kb:.1f}KB ({pct:.1f}%) [{fmt_label}]")
            self.resized_title_label.configure(text=f"リサイズ後 ({self._current_resize_settings_text()})")
        else:
            self.canvas_resz.delete("all")
            self.info_resized_var.set("--- x ---  ---  (---)")
            self.resized_title_label.configure(text="リサイズ後")

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
        
        disp = img.copy()
        new_size = (int(disp.width * zoom), int(disp.height * zoom))
        if new_size[0] <= 0 or new_size[1] <= 0:
            return None # Avoids errors with tiny images
        
        disp = disp.resize(new_size, Resampling.LANCZOS)
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

    def _open_settings_dialog(self) -> None:
        settings_dialog.open_settings_dialog(
            self,
            colors=METALLIC_COLORS,
            ui_mode_id_to_label=UI_MODE_ID_TO_LABEL,
            ui_mode_label_to_id=UI_MODE_LABEL_TO_ID,
            appearance_id_to_label=APPEARANCE_ID_TO_LABEL,
            appearance_label_to_id=APPEARANCE_LABEL_TO_ID,
            format_id_to_label=FORMAT_ID_TO_LABEL,
            pro_input_mode_id_to_label=PRO_INPUT_MODE_ID_TO_LABEL,
            pro_input_mode_label_to_id=PRO_INPUT_MODE_LABEL_TO_ID,
            preset_none_label=PRESET_NONE_LABEL,
            quality_values=QUALITY_VALUES,
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
        if self.current_index is not None:
            self._draw_previews(self.jobs[self.current_index])

    def _get_fit_zoom_ratio(self, canvas: customtkinter.CTkCanvas, is_resized: bool) -> float:
        """Calculates the zoom ratio to fit the image to the canvas."""
        if self.current_index is None:
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
        self._draw_previews(self.jobs[self.current_index])

    def _on_root_resize(self, _e):
        self._refresh_topbar_density()
        # redraw previews if zoom is 'Fit'
        if self._zoom_org is None or self._zoom_resz is None:
            if self.current_index is not None:
                self._draw_previews(self.jobs[self.current_index])

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
