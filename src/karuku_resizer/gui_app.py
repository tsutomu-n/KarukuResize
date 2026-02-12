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
import threading
import time
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from tkinter import filedialog, messagebox

import customtkinter
from PIL import Image, ImageOps, ImageTk

# ヘルプコンテンツとダイアログをインポート
from karuku_resizer.help_content import HELP_CONTENT, STEP_DESCRIPTIONS
from karuku_resizer.help_dialog import HelpDialog
from karuku_resizer.image_save_pipeline import (
    ExifEditValues,
    SaveOptions,
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

# Pillow ≥10 moves resampling constants to Image.Resampling
try:
    from PIL.Image import Resampling
except ImportError:  # Pillow<10 fallback
    class _Resampling:  # type: ignore
        LANCZOS = Image.LANCZOS  # type: ignore

    Resampling = _Resampling()  # type: ignore

DEFAULT_PREVIEW = 480

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
FILE_LOAD_FAILURE_PREVIEW_LIMIT = 20

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


@dataclass
class ImageJob:
    path: Path
    image: Image.Image
    resized: Optional[Image.Image] = None  # cache of last processed result
    metadata_loaded: bool = False
    metadata_text: str = ""
    metadata_error: Optional[str] = None


@dataclass
class BatchSaveStats:
    processed_count: int = 0
    failed_count: int = 0
    dry_run_count: int = 0
    exif_applied_count: int = 0
    exif_fallback_count: int = 0
    gps_removed_count: int = 0
    failed_details: List[str] = field(default_factory=list)

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

    def record_failure(self, file_name: str, detail: str) -> None:
        self.failed_count += 1
        self.failed_details.append(f"{file_name}: {detail}")


DEBUG = False
# ログディレクトリを確実に作成
_LOG_DIR = Path(__file__).resolve().parent.parent / "logs"
_LOG_DIR.mkdir(parents=True, exist_ok=True)
if DEBUG:
    logging.basicConfig(level=logging.DEBUG,
                        format='%(asctime)s %(levelname)s %(message)s',
                        handlers=[logging.FileHandler(_LOG_DIR / 'karuku_debug.log', encoding='utf-8'),
                                  logging.StreamHandler()])

logger = logging.getLogger(__name__)


class SettingsManager:
    """設定ファイル管理クラス"""
    def __init__(self, settings_file: str = "karuku_settings.json"):
        self.settings_file = Path(settings_file)

    def load_settings(self) -> dict:
        """設定ファイルを読み込む"""
        defaults = self._default_settings()
        if self.settings_file.exists():
            try:
                with open(self.settings_file, "r", encoding="utf-8") as f:
                    loaded = json.load(f)
                    if isinstance(loaded, dict):
                        defaults.update(loaded)
            except Exception as e:
                logging.error(f"Failed to load settings: {e}")
        return defaults

    def save_settings(self, settings: dict) -> None:
        """設定ファイルを保存する"""
        try:
            with open(self.settings_file, "w", encoding="utf-8") as f:
                json.dump(settings, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logging.error(f"Failed to save settings: {e}")

    @staticmethod
    def _default_settings() -> dict:
        """デフォルト設定を返す"""
        return {
            "mode": "ratio",
            "ui_mode": "simple",
            "appearance_mode": "system",
            "ratio_value": "100",
            "width_value": "",
            "height_value": "",
            "quality": "85",
            "output_format": "auto",
            "webp_method": "6",
            "webp_lossless": False,
            "avif_speed": "6",
            "dry_run": False,
            "verbose_logging": False,
            "exif_mode": "keep",
            "remove_gps": False,
            "exif_artist": "",
            "exif_copyright": "",
            "exif_user_comment": "",
            "exif_datetime_original": "",
            "details_expanded": False,
            "metadata_panel_expanded": False,
            "window_geometry": "1200x800",
            "zoom_preference": "画面に合わせる",
            "last_input_dir": "",
            "last_output_dir": "",
            "pro_input_mode": "recursive",
        }


class ResizeApp(customtkinter.CTk):
    def __init__(self) -> None:
        super().__init__()

        # 設定マネージャー初期化
        self.settings_manager = SettingsManager()
        self.settings = self.settings_manager.load_settings()
        self.available_formats = supported_output_formats()

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

        # 例外を握りつぶさず、GUI上で明示してログへ残す
        self.report_callback_exception = self._report_callback_exception
        
        # ウィンドウ閉じる時のイベント
        self.protocol("WM_DELETE_WINDOW", self._on_closing)

        self.jobs: List[ImageJob] = []
        self.current_index: Optional[int] = None
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

        self._setup_ui()
        self._restore_settings()
        self._apply_log_level()
        
        self.after(0, self._update_mode)  # set initial enable states
        logging.debug('ResizeApp initialized')

    def _style_primary_button(self, button: customtkinter.CTkButton) -> None:
        button.configure(
            fg_color=METALLIC_COLORS["primary"],
            hover_color=METALLIC_COLORS["hover"],
            text_color=METALLIC_COLORS["text_primary"],
            corner_radius=10,
            border_width=0,
        )

    def _style_secondary_button(self, button: customtkinter.CTkButton) -> None:
        button.configure(
            fg_color=METALLIC_COLORS["bg_tertiary"],
            hover_color=METALLIC_COLORS["accent_soft"],
            text_color=METALLIC_COLORS["text_primary"],
            border_width=1,
            border_color=METALLIC_COLORS["border_light"],
            corner_radius=10,
        )

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

    def _setup_ui(self):
        """UI要素をセットアップ"""
        # -------------------- UI top bar --------------------------------
        top = customtkinter.CTkFrame(self)
        self._style_card_frame(top)
        top.pack(side="top", fill="x", padx=12, pady=(8, 6))

        self.select_button = customtkinter.CTkButton(
            top, text="📂 画像を選択", width=128, command=self._select_files, font=self.font_default
        )
        self._style_primary_button(self.select_button)
        self.select_button.pack(side="left", padx=(8, 6), pady=8)
        self.help_button = customtkinter.CTkButton(
            top, text="❓ 使い方", width=108, command=self._show_help, font=self.font_default
        )
        self._style_secondary_button(self.help_button)
        self.help_button.pack(side="left", padx=(0, 10), pady=8)

        # Spacer to push subsequent widgets to the right
        spacer = customtkinter.CTkFrame(top, fg_color="transparent")
        spacer.pack(side="left", expand=True)

        # Mode radio buttons
        self.mode_var = customtkinter.StringVar(value="ratio")
        self.mode_radio_buttons: List[customtkinter.CTkRadioButton] = []
        modes = [
            ("比率 %", "ratio"),
            ("幅 px", "width"),
            ("高さ px", "height"),
            ("幅×高", "fixed"),
        ]
        for text, val in modes:
            mode_radio = customtkinter.CTkRadioButton(
                top,
                text=text,
                variable=self.mode_var,
                value=val,
                command=self._update_mode,
                font=self.font_default,
                fg_color=METALLIC_COLORS["primary"],
                hover_color=METALLIC_COLORS["hover"],
                border_color=METALLIC_COLORS["border_medium"],
                text_color=METALLIC_COLORS["text_primary"],
            )
            mode_radio.pack(side="left", padx=(0, 4))
            self.mode_radio_buttons.append(mode_radio)

        self._setup_entry_widgets(top)
        self._setup_action_buttons(top)
        self._setup_settings_layers()
        self._setup_main_layout()

    def _setup_settings_layers(self):
        """基本操作の下に設定サマリーと詳細設定（折りたたみ）を配置する。"""
        self.settings_header_frame = customtkinter.CTkFrame(self)
        self._style_card_frame(self.settings_header_frame, corner_radius=12)
        self.settings_header_frame.pack(side="top", fill="x", padx=12, pady=(0, 6))

        self.settings_summary_var = customtkinter.StringVar(value="")
        self.settings_summary_label = customtkinter.CTkLabel(
            self.settings_header_frame,
            textvariable=self.settings_summary_var,
            anchor="w",
            font=self.font_small,
            text_color=METALLIC_COLORS["text_secondary"],
        )
        self.settings_summary_label.pack(side="left", fill="x", expand=True, padx=(10, 0), pady=8)

        self.ui_mode_var = customtkinter.StringVar(value="簡易")
        self.ui_mode_segment = customtkinter.CTkSegmentedButton(
            self.settings_header_frame,
            values=list(UI_MODE_LABEL_TO_ID.keys()),
            variable=self.ui_mode_var,
            command=self._on_ui_mode_changed,
            width=120,
            font=self.font_small,
            selected_color=METALLIC_COLORS["primary"],
            selected_hover_color=METALLIC_COLORS["hover"],
            unselected_color=METALLIC_COLORS["bg_tertiary"],
            unselected_hover_color=METALLIC_COLORS["accent_soft"],
            text_color=METALLIC_COLORS["text_primary"],
        )
        self.ui_mode_segment.pack(side="right", padx=(0, 8), pady=8)

        self.appearance_mode_var = customtkinter.StringVar(value="システム")
        self.appearance_mode_segment = customtkinter.CTkSegmentedButton(
            self.settings_header_frame,
            values=list(APPEARANCE_LABEL_TO_ID.keys()),
            variable=self.appearance_mode_var,
            command=self._on_appearance_mode_changed,
            width=180,
            font=self.font_small,
            selected_color=METALLIC_COLORS["primary"],
            selected_hover_color=METALLIC_COLORS["hover"],
            unselected_color=METALLIC_COLORS["bg_tertiary"],
            unselected_hover_color=METALLIC_COLORS["accent_soft"],
            text_color=METALLIC_COLORS["text_primary"],
        )
        self.appearance_mode_segment.pack(side="right", padx=(0, 8), pady=8)

        self.details_toggle_button = customtkinter.CTkButton(
            self.settings_header_frame,
            text="詳細設定を表示",
            width=140,
            command=self._toggle_details_panel,
            font=self.font_small,
        )
        self._style_secondary_button(self.details_toggle_button)
        self.details_toggle_button.pack(side="right", padx=(0, 6), pady=8)

        self.detail_settings_frame = customtkinter.CTkFrame(self)
        self._style_card_frame(self.detail_settings_frame, corner_radius=12)
        self._setup_output_controls(self.detail_settings_frame)
        self._register_setting_watchers()
        self._apply_ui_mode()
        self._update_settings_summary()
        self._set_details_panel_visibility(False)

    def _register_setting_watchers(self):
        for var in (
            self.output_format_var,
            self.quality_var,
            self.webp_method_var,
            self.webp_lossless_var,
            self.avif_speed_var,
            self.exif_mode_var,
            self.remove_gps_var,
            self.dry_run_var,
        ):
            var.trace_add("write", self._on_setting_var_changed)

    def _on_setting_var_changed(self, *_args):
        self._update_settings_summary()

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
        self.select_button.configure(
            text="📂 画像/フォルダを選択" if pro_mode else "📂 画像を選択"
        )
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

    def _update_settings_summary(self):
        mode_label = self.ui_mode_var.get()
        appearance_label = self.appearance_mode_var.get()
        format_id = FORMAT_LABEL_TO_ID.get(self.output_format_var.get(), "auto")
        codec_summary = ""
        if self._is_pro_mode() and format_id == "webp":
            codec_summary = (
                f" / WEBP method {self.webp_method_var.get()} "
                f"(lossless {'ON' if self.webp_lossless_var.get() else 'OFF'})"
            )
        elif self._is_pro_mode() and format_id == "avif":
            codec_summary = f" / AVIF speed {self.avif_speed_var.get()}"

        summary = (
            f"現在設定: {mode_label}モード / テーマ {appearance_label} / 形式 {self.output_format_var.get()} / 品質 {self.quality_var.get()} / "
            f"EXIF {self.exif_mode_var.get()} / GPS削除 {'ON' if self.remove_gps_var.get() else 'OFF'} / "
            f"ドライラン {'ON' if self.dry_run_var.get() else 'OFF'}{codec_summary}"
        )
        self.settings_summary_var.set(summary)

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
        """入力ウィジェットをセットアップ"""
        # Size entry fields
        self.entry_frame = customtkinter.CTkFrame(parent, fg_color="transparent")
        self.entry_frame.pack(side="left", padx=(8, 10))

        vcmd = (self.register(self._validate_int), "%P")

        # --- Create widgets and frames for each mode ---
        self.pct_var = customtkinter.StringVar(value="100")
        self.w_var = customtkinter.StringVar()
        self.h_var = customtkinter.StringVar()

        # Ratio Mode
        frame_ratio = customtkinter.CTkFrame(self.entry_frame, fg_color="transparent")
        self.ratio_entry = customtkinter.CTkEntry(
            frame_ratio,
            textvariable=self.pct_var,
            width=54,
            validate="key",
            validatecommand=vcmd,
            font=self.font_default,
            fg_color=METALLIC_COLORS["input_bg"],
            border_color=METALLIC_COLORS["border_light"],
            text_color=METALLIC_COLORS["text_primary"],
            corner_radius=8,
        )
        self.ratio_entry.pack(side="left")
        customtkinter.CTkLabel(
            frame_ratio, text="%", font=self.font_default, text_color=METALLIC_COLORS["text_secondary"]
        ).pack(side="left")

        # Width Mode
        frame_width = customtkinter.CTkFrame(self.entry_frame, fg_color="transparent")
        self.entry_w_single = customtkinter.CTkEntry(
            frame_width,
            textvariable=self.w_var,
            width=64,
            validate="key",
            validatecommand=vcmd,
            fg_color=METALLIC_COLORS["input_bg"],
            border_color=METALLIC_COLORS["border_light"],
            text_color=METALLIC_COLORS["text_primary"],
            corner_radius=8,
        )
        self.entry_w_single.pack(side="left")
        customtkinter.CTkLabel(
            frame_width, text="px", font=self.font_default, text_color=METALLIC_COLORS["text_secondary"]
        ).pack(side="left")

        # Height Mode
        frame_height = customtkinter.CTkFrame(self.entry_frame, fg_color="transparent")
        self.entry_h_single = customtkinter.CTkEntry(
            frame_height,
            textvariable=self.h_var,
            width=64,
            validate="key",
            validatecommand=vcmd,
            fg_color=METALLIC_COLORS["input_bg"],
            border_color=METALLIC_COLORS["border_light"],
            text_color=METALLIC_COLORS["text_primary"],
            corner_radius=8,
        )
        self.entry_h_single.pack(side="left")
        customtkinter.CTkLabel(
            frame_height, text="px", font=self.font_default, text_color=METALLIC_COLORS["text_secondary"]
        ).pack(side="left")

        # Fixed Mode
        frame_fixed = customtkinter.CTkFrame(self.entry_frame, fg_color="transparent")
        self.entry_w_fixed = customtkinter.CTkEntry(
            frame_fixed,
            textvariable=self.w_var,
            width=64,
            validate="key",
            validatecommand=vcmd,
            fg_color=METALLIC_COLORS["input_bg"],
            border_color=METALLIC_COLORS["border_light"],
            text_color=METALLIC_COLORS["text_primary"],
            corner_radius=8,
        )
        self.entry_w_fixed.pack(side="left")
        customtkinter.CTkLabel(
            frame_fixed, text="×", font=self.font_default, text_color=METALLIC_COLORS["text_secondary"]
        ).pack(side="left")
        self.entry_h_fixed = customtkinter.CTkEntry(
            frame_fixed,
            textvariable=self.h_var,
            width=64,
            validate="key",
            validatecommand=vcmd,
            fg_color=METALLIC_COLORS["input_bg"],
            border_color=METALLIC_COLORS["border_light"],
            text_color=METALLIC_COLORS["text_primary"],
            corner_radius=8,
        )
        self.entry_h_fixed.pack(side="left")
        customtkinter.CTkLabel(
            frame_fixed, text="px", font=self.font_default, text_color=METALLIC_COLORS["text_secondary"]
        ).pack(side="left")

        # --- Group frames and entries for easy management ---
        self.mode_frames = {
            "ratio": frame_ratio,
            "width": frame_width,
            "height": frame_height,
            "fixed": frame_fixed,
        }
        self.active_mode_frame: Optional[customtkinter.CTkFrame] = None

        self._all_entries = [
            self.ratio_entry,
            self.entry_w_single, self.entry_h_single,
            self.entry_w_fixed, self.entry_h_fixed
        ]
        self._entry_widgets = {
            "ratio": [self.ratio_entry],
            "width": [self.entry_w_single],
            "height": [self.entry_h_single],
            "fixed": [self.entry_w_fixed, self.entry_h_fixed],
        }

    def _setup_action_buttons(self, parent):
        """アクションボタンをセットアップ"""
        self.preview_button = customtkinter.CTkButton(
            parent, text="🔄 プレビュー", width=110, command=self._preview_current,
            font=self.font_default
        )
        self._style_primary_button(self.preview_button)
        self.preview_button.pack(side="left", padx=(0, 8), pady=8)
        
        self.save_button = customtkinter.CTkButton(
            parent, text="💾 保存", width=90, command=self._save_current,
            font=self.font_default
        )
        self._style_primary_button(self.save_button)
        self.save_button.pack(side="left", pady=8)
        
        self.batch_button = customtkinter.CTkButton(
            parent, text="📁 一括適用保存", width=120, command=self._batch_save,
            font=self.font_default
        )
        self._style_primary_button(self.batch_button)
        self.batch_button.pack(side="left", padx=8, pady=8)

        # Zoom combobox
        self.zoom_var = customtkinter.StringVar(value="画面に合わせる")
        self.zoom_cb = customtkinter.CTkComboBox(
            parent,
            variable=self.zoom_var,
            values=["画面に合わせる", "100%", "200%", "300%"],
            width=140,
            state="readonly",
            command=self._apply_zoom_selection,
            font=self.font_default,
            fg_color=METALLIC_COLORS["bg_tertiary"],
            border_color=METALLIC_COLORS["border_light"],
            button_color=METALLIC_COLORS["primary"],
            button_hover_color=METALLIC_COLORS["hover"],
            text_color=METALLIC_COLORS["text_primary"],
            dropdown_fg_color=METALLIC_COLORS["bg_secondary"],
            dropdown_text_color=METALLIC_COLORS["text_primary"],
        )
        self.zoom_cb.pack(side="left", padx=(4, 8), pady=8)

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
        self._style_secondary_button(self.exif_preview_button)
        self.exif_preview_button.pack(side="left", padx=(0, 10), pady=8)

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

        log_path = _LOG_DIR / "karuku_gui.log"
        has_file_handler = any(
            isinstance(h, logging.FileHandler) and Path(h.baseFilename) == log_path
            for h in root_logger.handlers
        )
        if not has_file_handler:
            handler = logging.FileHandler(log_path, encoding="utf-8")
            handler.setFormatter(
                logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s")
            )
            root_logger.addHandler(handler)

    def _setup_main_layout(self):
        """メインレイアウトをセットアップ"""
        self._setup_progress_bar_and_cancel()
        self._setup_status_bar()

        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(1, weight=1)

        self._setup_left_panel()
        self._setup_right_panel()

        # Bind events and initialize runtime variables
        self.bind("<Configure>", self._on_root_resize)
        self._last_canvas_size: Tuple[int, int] = (DEFAULT_PREVIEW, DEFAULT_PREVIEW)
        self._imgtk_org: Optional[ImageTk.PhotoImage] = None
        self._imgtk_resz: Optional[ImageTk.PhotoImage] = None
        self._zoom_org: Optional[float] = None
        self._zoom_resz: Optional[float] = None


    def _setup_progress_bar_and_cancel(self):
        """プログレスバーとキャンセルボタンをセットアップ"""
        self.progress_bar = customtkinter.CTkProgressBar(
            self,
            width=400,
            height=20,
            fg_color=METALLIC_COLORS["bg_tertiary"],
            progress_color=METALLIC_COLORS["primary"],
        )
        self.progress_bar.set(0)
        self.progress_bar.pack_forget()  # 初期は非表示

        self.cancel_button = customtkinter.CTkButton(
            self, text="キャンセル", width=100, command=self._cancel_active_operation
        )
        self._style_secondary_button(self.cancel_button)
        self.cancel_button.pack_forget()  # 初期は非表示

    def _setup_status_bar(self):
        """ステータスバーをセットアップ"""
        self.status_var = customtkinter.StringVar(value="準備完了")
        self.status_label = customtkinter.CTkLabel(
            self,
            textvariable=self.status_var,
            anchor='w',
            font=self.font_default,
            text_color=METALLIC_COLORS["text_secondary"],
            fg_color=METALLIC_COLORS["bg_secondary"],
            corner_radius=10,
            padx=10,
        )
        self.status_label.pack(side="bottom", fill="x", padx=12, pady=(0, 8))

    def _setup_left_panel(self):
        """左側のパネル（ファイルリスト）をセットアップ"""
        # Create main content frame
        self.main_content = customtkinter.CTkFrame(self, fg_color="transparent")
        self.main_content.pack(fill="both", expand=True, padx=12, pady=8)
        
        self.file_list_frame = customtkinter.CTkScrollableFrame(
            self.main_content,
            label_text="ファイルリスト",
            label_font=self.font_small,
            width=250,
            fg_color=METALLIC_COLORS["bg_secondary"],
            border_width=1,
            border_color=METALLIC_COLORS["border_light"],
            label_fg_color=METALLIC_COLORS["bg_tertiary"],
            label_text_color=METALLIC_COLORS["text_secondary"],
            corner_radius=12,
        )
        self.file_list_frame.pack(side="left", fill="y", padx=(0, 6))
        self.file_buttons: List[customtkinter.CTkButton] = []

    def _setup_right_panel(self):
        """右側のパネル（プレビュー）をセットアップ"""
        preview_pane = customtkinter.CTkFrame(self.main_content, fg_color="transparent")
        preview_pane.pack(side="right", fill="both", expand=True, padx=(5, 0))
        preview_pane.grid_rowconfigure(0, weight=1)
        preview_pane.grid_rowconfigure(1, weight=1)
        preview_pane.grid_rowconfigure(2, weight=0)
        preview_pane.grid_columnconfigure(0, weight=1)

        # Original Preview
        frame_original = customtkinter.CTkFrame(preview_pane, corner_radius=12)
        self._style_card_frame(frame_original, corner_radius=12)
        frame_original.grid(row=0, column=0, sticky="nswe", pady=(0, 5))
        frame_original.grid_rowconfigure(1, weight=1)
        frame_original.grid_columnconfigure(0, weight=1)
        customtkinter.CTkLabel(
            frame_original,
            text="オリジナル",
            font=self.font_default,
            text_color=METALLIC_COLORS["text_secondary"],
        ).grid(row=0, column=0, sticky="w", padx=10, pady=(8, 0))
        self.canvas_org = customtkinter.CTkCanvas(frame_original, bg=self._canvas_background_color(), highlightthickness=0)
        self.canvas_org.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)
        self.info_orig_var = customtkinter.StringVar(value="--- x ---  ---")
        customtkinter.CTkLabel(
            frame_original,
            textvariable=self.info_orig_var,
            justify="left",
            font=self.font_small,
            text_color=METALLIC_COLORS["text_tertiary"],
        ).grid(row=2, column=0, sticky="ew", padx=10, pady=(0, 8))

        # Resized Preview
        self.lf_resized = customtkinter.CTkFrame(preview_pane, corner_radius=12)
        self._style_card_frame(self.lf_resized, corner_radius=12)
        self.lf_resized.grid(row=1, column=0, sticky="nswe", pady=(5, 0))
        self.lf_resized.grid_rowconfigure(1, weight=1)
        self.lf_resized.grid_columnconfigure(0, weight=1)
        self.resized_title_label = customtkinter.CTkLabel(
            self.lf_resized,
            text="リサイズ後",
            font=self.font_default,
            text_color=METALLIC_COLORS["text_secondary"],
        )
        self.resized_title_label.grid(row=0, column=0, sticky="w", padx=10, pady=(8, 0))
        self.canvas_resz = customtkinter.CTkCanvas(self.lf_resized, bg=self._canvas_background_color(), highlightthickness=0)
        self.canvas_resz.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)
        self.info_resized_var = customtkinter.StringVar(value="--- x ---  ---  (---)")
        customtkinter.CTkLabel(
            self.lf_resized,
            textvariable=self.info_resized_var,
            justify="left",
            font=self.font_small,
            text_color=METALLIC_COLORS["text_tertiary"],
        ).grid(row=2, column=0, sticky="ew", padx=10, pady=(0, 8))

        # Canvas Interactions
        self.canvas_org.bind("<MouseWheel>", lambda e: self._on_zoom(e, is_resized=False))
        self.canvas_resz.bind("<MouseWheel>", lambda e: self._on_zoom(e, is_resized=True))
        self.canvas_org.bind("<ButtonPress-1>", lambda e: self.canvas_org.scan_mark(e.x, e.y))
        self.canvas_org.bind("<B1-Motion>",   lambda e: self.canvas_org.scan_dragto(e.x, e.y, gain=1))
        self.canvas_resz.bind("<ButtonPress-1>", lambda e: self.canvas_resz.scan_mark(e.x, e.y))
        self.canvas_resz.bind("<B1-Motion>",   lambda e: self.canvas_resz.scan_dragto(e.x, e.y, gain=1))

        # Metadata preview (pro mode only)
        self.metadata_frame = customtkinter.CTkFrame(preview_pane, corner_radius=12)
        self._style_card_frame(self.metadata_frame, corner_radius=12)
        self.metadata_frame.grid(row=2, column=0, sticky="ew", pady=(6, 0))

        self.metadata_header_frame = customtkinter.CTkFrame(self.metadata_frame, fg_color="transparent")
        self.metadata_header_frame.pack(side="top", fill="x", padx=8, pady=(8, 4))

        self.metadata_title_label = customtkinter.CTkLabel(
            self.metadata_header_frame,
            text="メタデータ（プロ）",
            font=self.font_default,
            text_color=METALLIC_COLORS["text_secondary"],
        )
        self.metadata_title_label.pack(side="left")

        self.metadata_toggle_button = customtkinter.CTkButton(
            self.metadata_header_frame,
            text="表示",
            width=80,
            command=self._toggle_metadata_panel,
            font=self.font_small,
        )
        self._style_secondary_button(self.metadata_toggle_button)
        self.metadata_toggle_button.pack(side="right")

        self.metadata_status_var = customtkinter.StringVar(value="画像を選択するとメタデータを表示できます")
        self.metadata_status_label = customtkinter.CTkLabel(
            self.metadata_frame,
            textvariable=self.metadata_status_var,
            anchor="w",
            justify="left",
            font=self.font_small,
            text_color=METALLIC_COLORS["text_tertiary"],
        )
        self.metadata_status_label.pack(side="top", fill="x", padx=10, pady=(0, 4))

        self.metadata_textbox = customtkinter.CTkTextbox(
            self.metadata_frame,
            height=120,
            corner_radius=8,
            border_width=1,
            border_color=METALLIC_COLORS["border_light"],
            fg_color=METALLIC_COLORS["input_bg"],
            text_color=METALLIC_COLORS["text_primary"],
            font=self.font_small,
            wrap="word",
        )
        self.metadata_expanded = False
        self._set_metadata_panel_expanded(False)
        self._set_metadata_text("（プロモードで表示可能）")

    def _toggle_metadata_panel(self):
        self._set_metadata_panel_expanded(not self.metadata_expanded)

    def _set_metadata_panel_expanded(self, expanded: bool):
        self.metadata_expanded = expanded
        if expanded:
            if self.metadata_textbox.winfo_manager() != "pack":
                self.metadata_textbox.pack(side="top", fill="x", padx=10, pady=(0, 10))
            self.metadata_toggle_button.configure(text="隠す")
        else:
            if self.metadata_textbox.winfo_manager():
                self.metadata_textbox.pack_forget()
            self.metadata_toggle_button.configure(text="表示")

    def _set_metadata_text(self, text: str):
        self.metadata_textbox.configure(state="normal")
        self.metadata_textbox.delete("1.0", "end")
        self.metadata_textbox.insert("1.0", text)
        self.metadata_textbox.configure(state="disabled")

    @staticmethod
    def _decode_exif_value(value: object) -> str:
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
            parts = [ResizeApp._decode_exif_value(v) for v in value]
            return ", ".join(p for p in parts if p)
        return str(value).strip()

    def _extract_metadata_text(self, job: ImageJob) -> str:
        if job.metadata_loaded:
            return job.metadata_text

        try:
            with Image.open(job.path) as src:
                exif = src.getexif()
            has_exif = bool(exif)
            tag_count = len(exif)
            try:
                gps_ifd = exif.get_ifd(EXIF_GPS_INFO_TAG)
                has_gps = bool(gps_ifd)
            except Exception:
                has_gps = EXIF_GPS_INFO_TAG in exif

            lines = [
                f"EXIF: {'あり' if has_exif else 'なし'}",
                f"タグ数: {tag_count}",
                f"GPS: {'あり' if has_gps else 'なし'}",
            ]
            for label, tag_id in EXIF_PREVIEW_TAGS:
                text = self._decode_exif_value(exif.get(tag_id))
                if text:
                    lines.append(f"{label}: {self._trim_preview_text(text, max_len=80)}")

            if not has_exif:
                lines.append("元画像にEXIFメタデータはありません。")
            job.metadata_text = "\n".join(lines)
            job.metadata_error = None
        except Exception as exc:
            job.metadata_error = str(exc)
            job.metadata_text = "メタデータの取得に失敗しました。"

        job.metadata_loaded = True
        return job.metadata_text

    def _update_metadata_preview(self, job: Optional[ImageJob]):
        if not hasattr(self, "metadata_status_var"):
            return
        if job is None:
            self.metadata_status_var.set("画像を選択するとメタデータを表示できます")
            self._set_metadata_text("（画像未選択）")
            return

        metadata_text = self._extract_metadata_text(job)
        if job.metadata_error:
            self.metadata_status_var.set(f"メタデータ: 取得失敗 ({job.path.name})")
        else:
            self.metadata_status_var.set(f"メタデータ: {job.path.name}")
        self._set_metadata_text(metadata_text)

    def _update_metadata_panel_state(self):
        if not hasattr(self, "metadata_frame"):
            return
        if self._is_pro_mode():
            if self.metadata_frame.winfo_manager() != "grid":
                self.metadata_frame.grid()
            selected_job = None
            if self.current_index is not None and self.current_index < len(self.jobs):
                selected_job = self.jobs[self.current_index]
            self._update_metadata_preview(selected_job)
        else:
            if self.metadata_frame.winfo_manager():
                self.metadata_frame.grid_remove()

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
        self.remove_gps_var.set(bool(self.settings.get("remove_gps", False)))
        self.exif_artist_var.set(str(self.settings.get("exif_artist", "")))
        self.exif_copyright_var.set(str(self.settings.get("exif_copyright", "")))
        self.exif_user_comment_var.set(str(self.settings.get("exif_user_comment", "")))
        self.exif_datetime_original_var.set(str(self.settings.get("exif_datetime_original", "")))
        self.dry_run_var.set(bool(self.settings.get("dry_run", False)))
        self.verbose_log_var.set(bool(self.settings.get("verbose_logging", False)))
        details_expanded = self.settings.get("details_expanded", False)
        if not isinstance(details_expanded, bool):
            details_expanded = str(details_expanded).lower() in {"1", "true", "yes", "on"}
        metadata_panel_expanded = self.settings.get("metadata_panel_expanded", False)
        if not isinstance(metadata_panel_expanded, bool):
            metadata_panel_expanded = str(metadata_panel_expanded).lower() in {"1", "true", "yes", "on"}

        # ウィンドウサイズ復元
        try:
            self.geometry(self.settings["window_geometry"])
        except Exception:
            self.geometry("1200x800")  # フォールバック
        
        # ズーム設定復元
        self.zoom_var.set(self.settings["zoom_preference"])
        self._set_metadata_panel_expanded(metadata_panel_expanded)
        self._apply_user_appearance_mode(saved_appearance, redraw=False)
        self._apply_ui_mode()
        self._set_details_panel_visibility(details_expanded)
        self._update_settings_summary()
    
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
            "details_expanded": self.details_expanded,
            "metadata_panel_expanded": self.metadata_expanded,
            "window_geometry": self.geometry(),
            "zoom_preference": self.zoom_var.get(),
            "pro_input_mode": self._normalized_pro_input_mode(
                str(self.settings.get("pro_input_mode", "recursive"))
            ),
        })
        self.settings_manager.save_settings(self.settings)
    
    def _on_closing(self):
        """アプリ終了時の処理"""
        if self._is_loading_files:
            self._file_load_cancel_event.set()
        self._save_current_settings()
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

    def _resolve_output_format_for_image(self, source_image: Image.Image) -> str:
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

    def _current_exif_edit_values(self, show_warning: bool = True) -> ExifEditValues:
        datetime_text = self.exif_datetime_original_var.get().strip()
        if datetime_text and not self._validate_exif_datetime(datetime_text):
            if show_warning:
                messagebox.showwarning(
                    "EXIF日時形式",
                    "撮影日時は YYYY:MM:DD HH:MM:SS 形式で入力してください",
                )
            datetime_text = ""
            self.exif_datetime_original_var.set("")

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

    def _build_save_options(self, output_format: str, exif_edit_values: Optional[ExifEditValues] = None) -> SaveOptions:
        pro_mode = self._is_pro_mode()
        exif_mode = EXIF_LABEL_TO_ID.get(self.exif_mode_var.get(), "keep")
        edit_values = exif_edit_values
        if exif_mode == "edit" and edit_values is None:
            edit_values = self._current_exif_edit_values(show_warning=True)
        return SaveOptions(
            output_format=output_format,  # type: ignore[arg-type]
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

    def _build_unique_batch_base_path(self, output_dir: Path, stem: str, output_format: str, dry_run: bool) -> Path:
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

    # -------------------- file selection -------------------------------
    def _select_files(self):
        if self._is_loading_files:
            messagebox.showinfo("処理中", "現在、画像読み込み処理中です。完了またはキャンセル後に再実行してください。")
            return

        initial_dir = self.settings.get("last_input_dir", "")
        if self._is_pro_mode():
            paths, remembered_dir, started_async = self._select_files_in_pro_mode(initial_dir)
            if started_async:
                return
        else:
            paths, remembered_dir = self._select_files_in_simple_mode(initial_dir)
        if not paths:
            return

        if remembered_dir is not None:
            self.settings["last_input_dir"] = str(remembered_dir)

        self._load_selected_paths(paths)
        self._populate_listbox()

    def _select_files_in_simple_mode(self, initial_dir: str) -> Tuple[List[Path], Optional[Path]]:
        selected = filedialog.askopenfilenames(
            title="画像を選択",
            initialdir=initial_dir,
            filetypes=[("画像", "*.png *.jpg *.jpeg *.webp *.avif"), ("すべて", "*.*")],
        )
        if not selected:
            return [], None
        paths = [Path(p) for p in selected]
        return paths, paths[0].parent

    def _select_files_in_pro_mode(self, initial_dir: str) -> Tuple[List[Path], Optional[Path], bool]:
        saved_mode = self._normalized_pro_input_mode(str(self.settings.get("pro_input_mode", "recursive")))
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
            self.settings["pro_input_mode"] = "files"
            paths, remembered_dir = self._select_files_in_simple_mode(initial_dir)
            return paths, remembered_dir, False

        self.settings["pro_input_mode"] = "recursive"
        root_dir_str = filedialog.askdirectory(
            title="対象フォルダーを選択（再帰）",
            initialdir=initial_dir,
        )
        if not root_dir_str:
            return [], None, False

        root_dir = Path(root_dir_str)
        self._start_recursive_load_async(root_dir)
        return [], root_dir, True

    @staticmethod
    def _normalized_pro_input_mode(value: str) -> str:
        normalized = value.strip().lower()
        if normalized in {"recursive", "files"}:
            return normalized
        return "recursive"

    def _start_recursive_load_async(self, root_dir: Path) -> None:
        self._begin_file_load_session(mode_label="再帰読み込み", root_dir=root_dir, clear_existing_jobs=True)
        self._is_loading_files = True
        self.status_var.set(
            f"再帰探索開始: {root_dir} / 読み込み中は他操作を無効化（中止可）"
        )

        worker = threading.Thread(
            target=self._scan_and_load_images_worker,
            args=(root_dir, self._file_load_cancel_event, self._file_load_queue),
            daemon=True,
            name="karuku-recursive-loader",
        )
        worker.start()
        self._file_load_after_id = self.after(40, self._poll_file_load_queue)

    def _start_retry_failed_load_async(self, paths: List[Path]) -> None:
        unique_paths = list(dict.fromkeys(paths))
        if not unique_paths:
            return

        self._begin_file_load_session(
            mode_label="失敗再試行",
            root_dir=self._file_load_root_dir,
            clear_existing_jobs=False,
        )
        self.status_var.set(
            f"失敗再試行開始: 対象 {len(unique_paths)}件 / 読み込み中は他操作を無効化（中止可）"
        )
        worker = threading.Thread(
            target=self._load_paths_worker,
            args=(unique_paths, self._file_load_cancel_event, self._file_load_queue),
            daemon=True,
            name="karuku-retry-loader",
        )
        worker.start()
        self._file_load_after_id = self.after(40, self._poll_file_load_queue)

    def _begin_file_load_session(
        self,
        mode_label: str,
        root_dir: Optional[Path],
        clear_existing_jobs: bool,
    ) -> None:
        if clear_existing_jobs:
            self._reset_loaded_jobs()
        if root_dir is not None:
            self.settings["last_input_dir"] = str(root_dir)
        self._is_loading_files = True
        self._file_load_cancel_event = threading.Event()
        self._file_load_queue = queue.Queue(maxsize=8)
        self._file_load_after_id = None
        self._file_load_total_candidates = 0
        self._file_load_loaded_count = 0
        self._file_load_failed_details = []
        self._file_load_failed_paths = []
        self._file_scan_pulse = 0.0
        self._file_scan_started_at = time.monotonic()
        self._file_load_started_at = 0.0
        self._file_load_mode_label = mode_label
        self._file_load_root_dir = root_dir

        self._set_interactive_controls_enabled(False)
        self._prepare_file_loading_ui()

    def _prepare_file_loading_ui(self) -> None:
        self.progress_bar.pack(side="bottom", fill="x", padx=10, pady=(0, 5))
        self.cancel_button.configure(text="読み込み中止", command=self._cancel_file_loading)
        self.cancel_button.pack(side="bottom", pady=(0, 10))
        self.progress_bar.set(0.05)

    def _set_interactive_controls_enabled(self, enabled: bool) -> None:
        state = "normal" if enabled else "disabled"
        widgets = [
            self.select_button,
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
            self.webp_method_menu,
            self.webp_lossless_check,
            self.avif_speed_menu,
            self.zoom_cb,
        ]
        widgets.extend(self.mode_radio_buttons)
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

    @staticmethod
    def _scan_and_load_images_worker(
        root_dir: Path,
        cancel_event: threading.Event,
        out_queue: "queue.Queue[Dict[str, Any]]",
    ) -> None:
        try:
            candidates: List[Path] = []
            detected = 0
            for dirpath, _dirnames, filenames in os.walk(root_dir, topdown=True):
                if cancel_event.is_set():
                    out_queue.put({"type": "done", "canceled": True})
                    return
                base_dir = Path(dirpath)
                for name in filenames:
                    if cancel_event.is_set():
                        out_queue.put({"type": "done", "canceled": True})
                        return
                    suffix = Path(name).suffix.lower()
                    if suffix in PRO_MODE_RECURSIVE_INPUT_EXTENSIONS:
                        candidates.append(base_dir / name)
                        detected += 1
                        if detected % 40 == 0:
                            out_queue.put({"type": "scan_progress", "count": detected})

            candidates.sort(key=lambda p: str(p).lower())
            out_queue.put({"type": "scan_done", "total": len(candidates)})

            for index, path in enumerate(candidates, start=1):
                if cancel_event.is_set():
                    out_queue.put({"type": "done", "canceled": True})
                    return
                try:
                    with Image.open(path) as opened:
                        opened.load()
                        img = ImageOps.exif_transpose(opened)
                    out_queue.put({"type": "loaded", "path": path, "image": img, "index": index})
                except Exception as e:
                    out_queue.put({"type": "load_error", "path": path, "error": str(e), "index": index})

            out_queue.put({"type": "done", "canceled": cancel_event.is_set()})
        except Exception as e:
            out_queue.put({"type": "fatal", "error": str(e)})
            out_queue.put({"type": "done", "canceled": cancel_event.is_set()})

    @staticmethod
    def _load_paths_worker(
        paths: List[Path],
        cancel_event: threading.Event,
        out_queue: "queue.Queue[Dict[str, Any]]",
    ) -> None:
        try:
            out_queue.put({"type": "scan_done", "total": len(paths)})
            for index, path in enumerate(paths, start=1):
                if cancel_event.is_set():
                    out_queue.put({"type": "done", "canceled": True})
                    return
                try:
                    with Image.open(path) as opened:
                        opened.load()
                        img = ImageOps.exif_transpose(opened)
                    out_queue.put({"type": "loaded", "path": path, "image": img, "index": index})
                except Exception as e:
                    out_queue.put({"type": "load_error", "path": path, "error": str(e), "index": index})

            out_queue.put({"type": "done", "canceled": cancel_event.is_set()})
        except Exception as e:
            out_queue.put({"type": "fatal", "error": str(e)})
            out_queue.put({"type": "done", "canceled": cancel_event.is_set()})

    @staticmethod
    def _format_duration(seconds: float) -> str:
        whole = max(0, int(seconds))
        if whole < 60:
            return f"{whole}秒"
        minutes, sec = divmod(whole, 60)
        if minutes < 60:
            return f"{minutes}分{sec:02d}秒"
        hours, minutes = divmod(minutes, 60)
        return f"{hours}時間{minutes:02d}分"

    def _format_path_for_display(self, path: Path) -> str:
        if self._file_load_root_dir is not None:
            try:
                return path.relative_to(self._file_load_root_dir).as_posix()
            except ValueError:
                pass
        return str(path)

    def _loading_hint_text(self) -> str:
        return "読み込み中は他操作を無効化（中止可）"

    def _loading_progress_status_text(self, latest_path: Optional[Path] = None, failed: bool = False) -> str:
        total = self._file_load_total_candidates
        loaded = self._file_load_loaded_count
        failed_count = len(self._file_load_failed_details)
        done_count = loaded + failed_count
        path_text = ""
        if latest_path is not None:
            path_text = self._format_path_for_display(latest_path)

        remaining_text = "算出中"
        if self._file_load_started_at > 0 and total > 0 and done_count > 0:
            elapsed = max(0.001, time.monotonic() - self._file_load_started_at)
            speed = done_count / elapsed
            if speed > 0:
                remaining_sec = max(0.0, (total - done_count) / speed)
                remaining_text = self._format_duration(remaining_sec)

        prefix = f"{self._file_load_mode_label}: 読込中 {done_count}/{total} (成功{loaded} 失敗{failed_count})"
        if path_text:
            action = "失敗" if failed else "処理"
            prefix += f" / {action}: {path_text}"
        return f"{prefix} / 残り約{remaining_text} / {self._loading_hint_text()}"

    def _poll_file_load_queue(self) -> None:
        if not self._is_loading_files:
            self._file_load_after_id = None
            return

        handled = 0
        while handled < 30:
            try:
                message = self._file_load_queue.get_nowait()
            except queue.Empty:
                break
            handled += 1
            self._handle_file_load_message(message)
            if not self._is_loading_files:
                break

        if self._is_loading_files:
            self._file_load_after_id = self.after(40, self._poll_file_load_queue)
        else:
            self._file_load_after_id = None

    def _handle_file_load_message(self, message: Dict[str, Any]) -> None:
        msg_type = str(message.get("type", ""))
        if msg_type == "scan_progress":
            detected = int(message.get("count", 0))
            self._file_scan_pulse = (self._file_scan_pulse + 0.08) % 1.0
            self.progress_bar.set(max(0.05, self._file_scan_pulse))
            elapsed_text = self._format_duration(time.monotonic() - self._file_scan_started_at)
            self.status_var.set(
                f"{self._file_load_mode_label}: 探索中 {detected} 件検出 / 経過{elapsed_text} / {self._loading_hint_text()}"
            )
            return

        if msg_type == "scan_done":
            self._file_load_total_candidates = int(message.get("total", 0))
            self._file_load_started_at = time.monotonic()
            if self._file_load_total_candidates == 0:
                self.progress_bar.set(1.0)
                self.status_var.set(
                    f"{self._file_load_mode_label}: 対象画像（jpg/jpeg/png）は0件でした"
                )
            else:
                self.progress_bar.set(0)
                self.status_var.set(
                    f"{self._file_load_mode_label}: 読込開始 0/{self._file_load_total_candidates} / {self._loading_hint_text()}"
                )
            return

        if msg_type == "loaded":
            path = Path(str(message.get("path", "")))
            image = message.get("image")
            if isinstance(image, Image.Image):
                self.jobs.append(ImageJob(path, image))
            self._file_load_loaded_count += 1
            total = self._file_load_total_candidates
            done_count = self._file_load_loaded_count + len(self._file_load_failed_details)
            if total > 0:
                self.progress_bar.set(min(1.0, done_count / total))
                self.status_var.set(self._loading_progress_status_text(latest_path=path, failed=False))
            else:
                self.status_var.set(
                    f"{self._file_load_mode_label}: 読込中 / 処理: {self._format_path_for_display(path)} / {self._loading_hint_text()}"
                )
            return

        if msg_type == "load_error":
            path = Path(str(message.get("path", "")))
            error = str(message.get("error", "読み込み失敗"))
            display_path = self._format_path_for_display(path)
            self._file_load_failed_details.append(f"{display_path}: {error}")
            self._file_load_failed_paths.append(path)
            total = self._file_load_total_candidates
            done_count = self._file_load_loaded_count + len(self._file_load_failed_details)
            if total > 0:
                self.progress_bar.set(min(1.0, done_count / total))
                self.status_var.set(self._loading_progress_status_text(latest_path=path, failed=True))
            return

        if msg_type == "fatal":
            error = str(message.get("error", "不明なエラー"))
            self._file_load_failed_details.append(f"致命的エラー: {error}")
            logging.error("Fatal error in recursive loader: %s", error)
            return

        if msg_type == "done":
            canceled = bool(message.get("canceled", False))
            self._finish_recursive_load(canceled=canceled)

    def _finish_recursive_load(self, canceled: bool) -> None:
        retry_paths = list(self._file_load_failed_paths)
        self._is_loading_files = False
        if self._file_load_after_id is not None:
            try:
                self.after_cancel(self._file_load_after_id)
            except Exception:
                pass
            self._file_load_after_id = None

        self.progress_bar.pack_forget()
        self.cancel_button.pack_forget()
        self.cancel_button.configure(text="キャンセル", command=self._cancel_active_operation)
        self._set_interactive_controls_enabled(True)

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
            msg = f"{self._file_load_mode_label}完了。成功: {loaded}件 / 失敗: {failed}件 / 対象: {total}件"
        if self._file_load_failed_details:
            preview = self._file_load_failed_details[:FILE_LOAD_FAILURE_PREVIEW_LIMIT]
            msg += "\n失敗詳細:"
            for detail in preview:
                msg += f"\n- {detail}"
            if len(self._file_load_failed_details) > len(preview):
                msg += f"\n- ...ほか {len(self._file_load_failed_details) - len(preview)} 件"
        self.status_var.set(msg)
        if (not canceled) and retry_paths:
            retry = messagebox.askyesno("読込結果", f"{msg}\n\n失敗のみ再試行しますか？")
            if retry:
                self._start_retry_failed_load_async(retry_paths)
                return
        messagebox.showinfo("読込結果", msg)

    def _cancel_file_loading(self) -> None:
        if not self._is_loading_files:
            return
        self._file_load_cancel_event.set()
        self.status_var.set(f"{self._file_load_mode_label}: キャンセル中...")

    def _reset_loaded_jobs(self) -> None:
        self.jobs.clear()
        self.current_index = None
        for button in self.file_buttons:
            button.destroy()
        self.file_buttons = []
        self._clear_preview_panels()

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

    def _populate_listbox(self):
        for button in self.file_buttons:
            button.destroy()
        self.file_buttons = []
        if not self.jobs:
            self._clear_preview_panels()
            self.status_var.set("有効な画像を読み込めませんでした")
            return

        for i, job in enumerate(self.jobs):
            button = customtkinter.CTkButton(
                self.file_list_frame, 
                text=job.path.name, 
                command=lambda idx=i: self._on_select_change(idx),
                fg_color=METALLIC_COLORS["bg_tertiary"],
                hover_color=METALLIC_COLORS["accent_soft"],
                text_color=METALLIC_COLORS["text_primary"],
                border_width=1,
                border_color=METALLIC_COLORS["border_light"],
                corner_radius=8,
            )
            button.pack(fill="x", padx=8, pady=4)
            self.file_buttons.append(button)
        if self.jobs:
            self._on_select_change(0)

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

    def _on_select_change(self, idx: Optional[int] = None) -> None:
        """Handle file selection change."""
        if idx is None:
            idx = 0
        if self.current_index == idx or idx >= len(self.jobs):
            return

        # Update button highlights
        if self.current_index is not None and self.current_index < len(self.file_buttons):
            self.file_buttons[self.current_index].configure(
                fg_color=METALLIC_COLORS["bg_tertiary"],
                border_color=METALLIC_COLORS["border_light"],
                text_color=METALLIC_COLORS["text_primary"],
            )
        
        self.current_index = idx
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

    def _resolve_batch_reference(self) -> Optional[Tuple[ImageJob, Tuple[int, int], str]]:
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
        initial_dir = self.settings.get("last_output_dir") or Path.home()
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
        result = save_image(
            source_image=job.image,
            resized_image=job.resized,
            output_path=save_path,
            options=options,
        )

        if not result.success:
            messagebox.showerror("保存エラー", f"ファイルの保存に失敗しました:\n{result.error}")
            return

        if result.dry_run:
            msg = f"ドライラン完了: {result.output_path.name} を生成予定です"
        else:
            msg = f"{result.output_path.name} を保存しました"
        msg = f"{msg}\n{self._exif_status_text(result)}"
        self.status_var.set(msg)
        messagebox.showinfo("保存結果", msg)

    def _build_batch_save_options(self, reference_output_format: str) -> SaveOptions:
        exif_mode = EXIF_LABEL_TO_ID.get(self.exif_mode_var.get(), "keep")
        batch_exif_edit_values = (
            self._current_exif_edit_values(show_warning=True) if exif_mode == "edit" else None
        )
        return self._build_save_options(
            reference_output_format, exif_edit_values=batch_exif_edit_values
        )

    @staticmethod
    def _batch_run_mode_text(batch_options: SaveOptions) -> str:
        return "ドライラン（実ファイルは作成しません）" if batch_options.dry_run else "保存"

    def _confirm_batch_save(
        self,
        reference_job: ImageJob,
        reference_target: Tuple[int, int],
        reference_format_label: str,
        batch_options: SaveOptions,
    ) -> bool:
        return messagebox.askokcancel(
            "一括適用保存の確認",
            f"基準画像: {reference_job.path.name}\n"
            f"適用サイズ: {reference_target[0]} x {reference_target[1]} px\n"
            f"出力形式: {reference_format_label}\n"
            f"モード: {self._batch_run_mode_text(batch_options)}\n\n"
            f"読み込み中の {len(self.jobs)} 枚すべてに同じ設定を適用して処理します。",
        )

    def _select_batch_output_dir(self) -> Optional[Path]:
        initial_dir = self.settings.get("last_output_dir") or self.settings.get("last_input_dir") or Path.home()
        output_dir_str = filedialog.askdirectory(title="保存先フォルダを選択", initialdir=str(initial_dir))
        if not output_dir_str:
            return None
        return Path(output_dir_str)

    def _prepare_batch_ui(self) -> None:
        self.progress_bar.pack(side="bottom", fill="x", padx=10, pady=(0, 5))
        self.cancel_button.configure(text="キャンセル", command=self._cancel_active_operation)
        self.cancel_button.pack(side="bottom", pady=(0, 10))
        self.progress_bar.set(0)
        self._cancel_batch = False

    def _process_single_batch_job(
        self,
        job: ImageJob,
        output_dir: Path,
        reference_target: Tuple[int, int],
        reference_output_format: str,
        batch_options: SaveOptions,
        stats: BatchSaveStats,
    ) -> None:
        resized_img = self._resize_image_to_target(job.image, reference_target)
        if not resized_img:
            stats.record_failure(job.path.name, "リサイズ失敗")
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
            stats.record_success(result)
            return

        error_detail = result.error or "保存処理で不明なエラー"
        stats.record_failure(job.path.name, error_detail)
        logging.error(f"Failed to save {result.output_path}: {result.error}")

    def _run_batch_save(
        self,
        output_dir: Path,
        reference_target: Tuple[int, int],
        reference_output_format: str,
        batch_options: SaveOptions,
    ) -> BatchSaveStats:
        stats = BatchSaveStats()
        total_files = len(self.jobs)
        self._prepare_batch_ui()

        try:
            for i, job in enumerate(self.jobs):
                if self._cancel_batch:
                    break

                self.status_var.set(f"処理中: {i+1}/{total_files} - {job.path.name}")
                self.progress_bar.set((i + 1) / total_files)
                self.update_idletasks()

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
                    stats.record_failure(job.path.name, f"例外 {e}")
                    logging.exception("Unexpected error during batch save: %s", job.path)
        finally:
            self.progress_bar.pack_forget()
            self.cancel_button.pack_forget()

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

        if stats.failed_details:
            preview_lines = stats.failed_details[:5]
            msg += "\n失敗詳細:"
            for detail in preview_lines:
                msg += f"\n- {detail}"
            if len(stats.failed_details) > len(preview_lines):
                msg += f"\n- ...ほか {len(stats.failed_details) - len(preview_lines)} 件"
        return msg

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

        if not self._confirm_batch_save(
            reference_job=reference_job,
            reference_target=reference_target,
            reference_format_label=reference_format_label,
            batch_options=batch_options,
        ):
            return

        output_dir = self._select_batch_output_dir()
        if output_dir is None:
            return
        self.settings["last_output_dir"] = str(output_dir)

        stats = self._run_batch_save(
            output_dir=output_dir,
            reference_target=reference_target,
            reference_output_format=reference_output_format,
            batch_options=batch_options,
        )
        msg = self._build_batch_completion_message(
            stats=stats,
            reference_job=reference_job,
            reference_target=reference_target,
            reference_format_label=reference_format_label,
            batch_options=batch_options,
        )
        self.status_var.set(msg)
        messagebox.showinfo("完了", msg)

    def _cancel_batch_save(self):
        self._cancel_batch = True

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
                    output_format=output_format,  # type: ignore[arg-type]
                    quality=self._current_quality(),
                    webp_method=self._current_webp_method(),
                    webp_lossless=self.webp_lossless_var.get(),
                    avif_speed=self._current_avif_speed(),
                )
                try:
                    save_img.save(bio, **preview_kwargs)
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
        # redraw previews if zoom is 'Fit'
        if self._zoom_org is None or self._zoom_resz is None:
            if self.current_index is not None:
                self._draw_previews(self.jobs[self.current_index])

# ----------------------------------------------------------------------

def main():
    """Package entry point (CLI script)."""
    app = ResizeApp()
    app.mainloop()


if __name__ == "__main__":
    main()
