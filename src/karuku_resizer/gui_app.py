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
import platform
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Tuple
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
    destination_with_extension,
    normalize_quality,
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

# -------------------- Metallic Ultra Dark color constants --------------------
METALLIC_COLORS = {
    # 主要カラー
    "primary": "#A8A8A8",           # メインのシルバーグレー
    "hover": "#C0C0C0",             # ホバー時の明るいシルバー
    "light": "#1A1A1A",             # アクセント背景
    "pressed": "#909090",           # プレス時の暗いシルバー
    
    # テキスト色
    "text_primary": "#FFFFFF",      # メインテキスト - 白
    "text_secondary": "#C0C0C0",    # セカンダリテキスト
    "text_tertiary": "#808080",     # 第三テキスト
    
    # 背景カラー
    "bg_primary": "#0A0A0A",        # 最も暗い背景
    "bg_secondary": "#1D1D1D",      # セカンダリ背景
    "bg_tertiary": "#262626",       # 第三背景
    
    # ボーダー・枠線
    "border_light": "#333333",      # Light Border
    "border_medium": "#404040",     # Medium Border
    
    # 状態色
    "success": "#3C9F40",           # 緑系
    "warning": "#EF8800",           # オレンジ系
    "error": "#E43326",             # 赤系
}
ZOOM_STEP = 1.1
MIN_ZOOM = 0.2
MAX_ZOOM = 10.0
QUALITY_VALUES = [str(v) for v in range(5, 101, 5)]

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


@dataclass
class ImageJob:
    path: Path
    image: Image.Image
    resized: Optional[Image.Image] = None  # cache of last processed result


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
            "ratio_value": "100",
            "width_value": "",
            "height_value": "",
            "quality": "85",
            "output_format": "auto",
            "dry_run": False,
            "verbose_logging": False,
            "exif_mode": "keep",
            "remove_gps": False,
            "exif_artist": "",
            "exif_copyright": "",
            "exif_user_comment": "",
            "exif_datetime_original": "",
            "details_expanded": False,
            "window_geometry": "1200x800",
            "zoom_preference": "画面に合わせる",
            "last_input_dir": "",
            "last_output_dir": "",
        }


class ResizeApp(customtkinter.CTk):
    def __init__(self) -> None:
        super().__init__()

        # 設定マネージャー初期化
        self.settings_manager = SettingsManager()
        self.settings = self.settings_manager.load_settings()
        self.available_formats = supported_output_formats()

        # --- Metallic Ultra Dark Theme --- 
        customtkinter.set_appearance_mode("dark")
        customtkinter.set_default_color_theme("blue")

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

        self._setup_ui()
        self._restore_settings()
        self._apply_log_level()
        
        self.after(0, self._update_mode)  # set initial enable states
        logging.debug('ResizeApp initialized')

    def _setup_ui(self):
        """UI要素をセットアップ"""
        # -------------------- UI top bar --------------------------------
        top = customtkinter.CTkFrame(self, fg_color="transparent")
        top.pack(side="top", fill="x", padx=10, pady=5)

        customtkinter.CTkButton(top, text="📂 画像を選択", width=120, command=self._select_files, font=self.font_default).pack(side="left")
        customtkinter.CTkButton(top, text="❓ 使い方", width=100, command=self._show_help, font=self.font_default).pack(side="left", padx=10)

        # Spacer to push subsequent widgets to the right
        spacer = customtkinter.CTkFrame(top, fg_color="transparent")
        spacer.pack(side="left", expand=True)

        # Mode radio buttons
        self.mode_var = customtkinter.StringVar(value="ratio")
        modes = [
            ("比率 %", "ratio"),
            ("幅 px", "width"),
            ("高さ px", "height"),
            ("幅×高", "fixed"),
        ]
        for text, val in modes:
            customtkinter.CTkRadioButton(top, text=text, variable=self.mode_var, value=val, command=self._update_mode, font=self.font_default).pack(side="left")

        self._setup_entry_widgets(top)
        self._setup_action_buttons(top)
        self._setup_settings_layers()
        self._setup_main_layout()

    def _setup_settings_layers(self):
        """基本操作の下に設定サマリーと詳細設定（折りたたみ）を配置する。"""
        self.settings_header_frame = customtkinter.CTkFrame(self, fg_color="transparent")
        self.settings_header_frame.pack(side="top", fill="x", padx=10, pady=(0, 4))

        self.settings_summary_var = customtkinter.StringVar(value="")
        self.settings_summary_label = customtkinter.CTkLabel(
            self.settings_header_frame,
            textvariable=self.settings_summary_var,
            anchor="w",
            font=self.font_small,
        )
        self.settings_summary_label.pack(side="left", fill="x", expand=True)

        self.details_toggle_button = customtkinter.CTkButton(
            self.settings_header_frame,
            text="詳細設定を表示",
            width=140,
            command=self._toggle_details_panel,
            font=self.font_small,
        )
        self.details_toggle_button.pack(side="right")

        self.detail_settings_frame = customtkinter.CTkFrame(self, fg_color="transparent")
        self._setup_output_controls(self.detail_settings_frame)
        self._register_setting_watchers()
        self._update_settings_summary()
        self._set_details_panel_visibility(False)

    def _register_setting_watchers(self):
        for var in (
            self.output_format_var,
            self.quality_var,
            self.exif_mode_var,
            self.remove_gps_var,
            self.dry_run_var,
        ):
            var.trace_add("write", self._on_setting_var_changed)

    def _on_setting_var_changed(self, *_args):
        self._update_settings_summary()

    def _update_settings_summary(self):
        summary = (
            f"現在設定: 形式 {self.output_format_var.get()} / 品質 {self.quality_var.get()} / "
            f"EXIF {self.exif_mode_var.get()} / GPS削除 {'ON' if self.remove_gps_var.get() else 'OFF'} / "
            f"ドライラン {'ON' if self.dry_run_var.get() else 'OFF'}"
        )
        self.settings_summary_var.set(summary)

    def _toggle_details_panel(self):
        self._set_details_panel_visibility(not self.details_expanded)

    def _set_details_panel_visibility(self, expanded: bool):
        self.details_expanded = expanded
        if expanded:
            pack_kwargs = {"side": "top", "fill": "x", "padx": 10, "pady": (0, 6)}
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
        self.entry_frame.pack(side="left", padx=10)

        vcmd = (self.register(self._validate_int), "%P")

        # --- Create widgets and frames for each mode ---
        self.pct_var = customtkinter.StringVar(value="100")
        self.w_var = customtkinter.StringVar()
        self.h_var = customtkinter.StringVar()

        # Ratio Mode
        frame_ratio = customtkinter.CTkFrame(self.entry_frame)
        self.ratio_entry = customtkinter.CTkEntry(frame_ratio, textvariable=self.pct_var, width=50, validate="key", validatecommand=vcmd, font=self.font_default)
        self.ratio_entry.pack(side="left")
        customtkinter.CTkLabel(frame_ratio, text="%", font=self.font_default).pack(side="left")

        # Width Mode
        frame_width = customtkinter.CTkFrame(self.entry_frame)
        self.entry_w_single = customtkinter.CTkEntry(frame_width, textvariable=self.w_var, width=60, validate="key", validatecommand=vcmd)
        self.entry_w_single.pack(side="left")
        customtkinter.CTkLabel(frame_width, text="px", font=self.font_default).pack(side="left")

        # Height Mode
        frame_height = customtkinter.CTkFrame(self.entry_frame)
        self.entry_h_single = customtkinter.CTkEntry(frame_height, textvariable=self.h_var, width=60, validate="key", validatecommand=vcmd)
        self.entry_h_single.pack(side="left")
        customtkinter.CTkLabel(frame_height, text="px", font=self.font_default).pack(side="left")

        # Fixed Mode
        frame_fixed = customtkinter.CTkFrame(self.entry_frame)
        self.entry_w_fixed = customtkinter.CTkEntry(frame_fixed, textvariable=self.w_var, width=60, validate="key", validatecommand=vcmd)
        self.entry_w_fixed.pack(side="left")
        customtkinter.CTkLabel(frame_fixed, text="×", font=self.font_default).pack(side="left")
        self.entry_h_fixed = customtkinter.CTkEntry(frame_fixed, textvariable=self.h_var, width=60, validate="key", validatecommand=vcmd)
        self.entry_h_fixed.pack(side="left")
        customtkinter.CTkLabel(frame_fixed, text="px", font=self.font_default).pack(side="left")

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
        customtkinter.CTkButton(
            parent, text="🔄 プレビュー", width=110, command=self._preview_current,
            fg_color=METALLIC_COLORS["primary"], hover_color=METALLIC_COLORS["hover"],
            corner_radius=8, font=self.font_default
        ).pack(side="left", padx=(0, 10))
        
        customtkinter.CTkButton(
            parent, text="💾 保存", width=90, command=self._save_current,
            fg_color=METALLIC_COLORS["primary"], hover_color=METALLIC_COLORS["hover"],
            corner_radius=8, font=self.font_default
        ).pack(side="left")
        
        customtkinter.CTkButton(
            parent, text="📁 一括保存", width=100, command=self._batch_save,
            fg_color=METALLIC_COLORS["primary"], hover_color=METALLIC_COLORS["hover"],
            corner_radius=8, font=self.font_default
        ).pack(side="left", padx=10)

        # Zoom combobox
        self.zoom_var = customtkinter.StringVar(value="画面に合わせる")
        self.zoom_cb = customtkinter.CTkComboBox(parent, variable=self.zoom_var, values=["画面に合わせる", "100%", "200%", "300%"], width=140, state="readonly", command=self._apply_zoom_selection, font=self.font_default)
        self.zoom_cb.pack(side="left", padx=4)

    def _setup_output_controls(self, parent):
        """保存関連の設定コントロールをセットアップ"""
        controls = customtkinter.CTkFrame(parent, fg_color="transparent")
        controls.pack(side="top", fill="x", padx=10, pady=(0, 6))

        self.output_format_var = customtkinter.StringVar(value="自動")
        self.quality_var = customtkinter.StringVar(value="85")
        self.dry_run_var = customtkinter.BooleanVar(value=False)
        self.verbose_log_var = customtkinter.BooleanVar(value=False)
        self.exif_mode_var = customtkinter.StringVar(value="保持")
        self.remove_gps_var = customtkinter.BooleanVar(value=False)

        customtkinter.CTkLabel(controls, text="出力形式", font=self.font_small).pack(side="left", padx=(0, 4))
        self.output_format_menu = customtkinter.CTkOptionMenu(
            controls,
            variable=self.output_format_var,
            values=self._build_output_format_labels(),
            width=110,
            command=self._on_output_format_changed,
            font=self.font_small,
        )
        self.output_format_menu.pack(side="left", padx=(0, 12))

        customtkinter.CTkLabel(controls, text="品質", font=self.font_small).pack(side="left", padx=(0, 4))
        self.quality_menu = customtkinter.CTkOptionMenu(
            controls,
            variable=self.quality_var,
            values=QUALITY_VALUES,
            width=90,
            command=self._on_quality_changed,
            font=self.font_small,
        )
        self.quality_menu.pack(side="left", padx=(0, 12))

        customtkinter.CTkLabel(controls, text="EXIF", font=self.font_small).pack(side="left", padx=(0, 4))
        self.exif_mode_menu = customtkinter.CTkOptionMenu(
            controls,
            variable=self.exif_mode_var,
            values=list(EXIF_LABEL_TO_ID.keys()),
            width=90,
            command=self._on_exif_mode_changed,
            font=self.font_small,
        )
        self.exif_mode_menu.pack(side="left", padx=(0, 10))

        self.remove_gps_check = customtkinter.CTkCheckBox(
            controls,
            text="GPS削除",
            variable=self.remove_gps_var,
            font=self.font_small,
        )
        self.remove_gps_check.pack(side="left", padx=(0, 10))

        self.dry_run_check = customtkinter.CTkCheckBox(
            controls,
            text="ドライラン",
            variable=self.dry_run_var,
            font=self.font_small,
        )
        self.dry_run_check.pack(side="left", padx=(0, 10))

        self.verbose_log_check = customtkinter.CTkCheckBox(
            controls,
            text="詳細ログ",
            variable=self.verbose_log_var,
            command=self._apply_log_level,
            font=self.font_small,
        )
        self.verbose_log_check.pack(side="left")
        self.exif_preview_button = customtkinter.CTkButton(
            controls,
            text="EXIF差分",
            width=95,
            command=self._show_exif_preview_dialog,
            font=self.font_small,
        )
        self.exif_preview_button.pack(side="left", padx=(10, 0))
        self._setup_exif_edit_fields(parent)

    def _setup_exif_edit_fields(self, parent):
        """EXIF編集フィールドをセットアップ（edit時のみ表示）。"""
        self.exif_edit_frame = customtkinter.CTkFrame(parent, fg_color="transparent")
        self.exif_edit_frame.pack(side="top", fill="x", padx=10, pady=(0, 6))

        self.exif_artist_var = customtkinter.StringVar(value="")
        self.exif_copyright_var = customtkinter.StringVar(value="")
        self.exif_user_comment_var = customtkinter.StringVar(value="")
        self.exif_datetime_original_var = customtkinter.StringVar(value="")

        customtkinter.CTkLabel(self.exif_edit_frame, text="撮影者", font=self.font_small).pack(side="left", padx=(0, 4))
        self.exif_artist_entry = customtkinter.CTkEntry(
            self.exif_edit_frame, textvariable=self.exif_artist_var, width=120, font=self.font_small
        )
        self.exif_artist_entry.pack(side="left", padx=(0, 8))

        customtkinter.CTkLabel(self.exif_edit_frame, text="著作権", font=self.font_small).pack(side="left", padx=(0, 4))
        self.exif_copyright_entry = customtkinter.CTkEntry(
            self.exif_edit_frame, textvariable=self.exif_copyright_var, width=140, font=self.font_small
        )
        self.exif_copyright_entry.pack(side="left", padx=(0, 8))

        customtkinter.CTkLabel(self.exif_edit_frame, text="コメント", font=self.font_small).pack(side="left", padx=(0, 4))
        self.exif_comment_entry = customtkinter.CTkEntry(
            self.exif_edit_frame, textvariable=self.exif_user_comment_var, width=180, font=self.font_small
        )
        self.exif_comment_entry.pack(side="left", padx=(0, 8))

        customtkinter.CTkLabel(self.exif_edit_frame, text="撮影日時", font=self.font_small).pack(side="left", padx=(0, 4))
        self.exif_datetime_entry = customtkinter.CTkEntry(
            self.exif_edit_frame,
            textvariable=self.exif_datetime_original_var,
            width=150,
            placeholder_text="YYYY:MM:DD HH:MM:SS",
            font=self.font_small,
        )
        self.exif_datetime_entry.pack(side="left")

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
        if self.current_index is not None:
            self._draw_previews(self.jobs[self.current_index])

    def _on_exif_mode_changed(self, _value: str):
        self._toggle_exif_edit_fields()

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

    def _apply_log_level(self):
        level = logging.DEBUG if self.verbose_log_var.get() else logging.INFO
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
        self.progress_bar = customtkinter.CTkProgressBar(self, width=400, height=20)
        self.progress_bar.set(0)
        self.progress_bar.pack_forget()  # 初期は非表示

        self.cancel_button = customtkinter.CTkButton(self, text="キャンセル", width=100, command=self._cancel_batch_save)
        self.cancel_button.pack_forget()  # 初期は非表示

    def _setup_status_bar(self):
        """ステータスバーをセットアップ"""
        self.status_var = customtkinter.StringVar(value="準備完了")
        self.status_label = customtkinter.CTkLabel(self, textvariable=self.status_var, anchor='w', font=self.font_default)
        self.status_label.pack(side="bottom", fill="x", padx=10, pady=5)

    def _setup_left_panel(self):
        """左側のパネル（ファイルリスト）をセットアップ"""
        # Create main content frame
        self.main_content = customtkinter.CTkFrame(self, fg_color="transparent")
        self.main_content.pack(fill="both", expand=True, padx=10, pady=10)
        
        self.file_list_frame = customtkinter.CTkScrollableFrame(self.main_content, label_text="ファイルリスト", label_font=self.font_small, width=250)
        self.file_list_frame.pack(side="left", fill="y", padx=(0, 5))
        self.file_buttons: List[customtkinter.CTkButton] = []

    def _setup_right_panel(self):
        """右側のパネル（プレビュー）をセットアップ"""
        preview_pane = customtkinter.CTkFrame(self.main_content, fg_color="transparent")
        preview_pane.pack(side="right", fill="both", expand=True, padx=(5, 0))
        preview_pane.grid_rowconfigure(0, weight=1)
        preview_pane.grid_rowconfigure(1, weight=1)
        preview_pane.grid_columnconfigure(0, weight=1)

        # Original Preview
        frame_original = customtkinter.CTkFrame(preview_pane, corner_radius=10)
        frame_original.grid(row=0, column=0, sticky="nswe", pady=(0, 5))
        frame_original.grid_rowconfigure(1, weight=1)
        frame_original.grid_columnconfigure(0, weight=1)
        customtkinter.CTkLabel(frame_original, text="オリジナル", font=self.font_default).grid(row=0, column=0, sticky="w", padx=10, pady=(5,0))
        self.canvas_org = customtkinter.CTkCanvas(frame_original, bg="#2B2B2B", highlightthickness=0)
        self.canvas_org.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)
        self.info_orig_var = customtkinter.StringVar(value="--- x ---  ---")
        customtkinter.CTkLabel(frame_original, textvariable=self.info_orig_var, justify="left", font=self.font_small).grid(row=2, column=0, sticky="ew", padx=10, pady=5)

        # Resized Preview
        self.lf_resized = customtkinter.CTkFrame(preview_pane, corner_radius=10)
        self.lf_resized.grid(row=1, column=0, sticky="nswe", pady=(5, 0))
        self.lf_resized.grid_rowconfigure(1, weight=1)
        self.lf_resized.grid_columnconfigure(0, weight=1)
        self.resized_title_label = customtkinter.CTkLabel(self.lf_resized, text="リサイズ後", font=self.font_default)
        self.resized_title_label.grid(row=0, column=0, sticky="w", padx=10, pady=(5,0))
        self.canvas_resz = customtkinter.CTkCanvas(self.lf_resized, bg="#2B2B2B", highlightthickness=0)
        self.canvas_resz.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)
        self.info_resized_var = customtkinter.StringVar(value="--- x ---  ---  (---)")
        customtkinter.CTkLabel(self.lf_resized, textvariable=self.info_resized_var, justify="left", font=self.font_small).grid(row=2, column=0, sticky="ew", padx=10, pady=5)

        # Canvas Interactions
        self.canvas_org.bind("<MouseWheel>", lambda e: self._on_zoom(e, is_resized=False))
        self.canvas_resz.bind("<MouseWheel>", lambda e: self._on_zoom(e, is_resized=True))
        self.canvas_org.bind("<ButtonPress-1>", lambda e: self.canvas_org.scan_mark(e.x, e.y))
        self.canvas_org.bind("<B1-Motion>",   lambda e: self.canvas_org.scan_dragto(e.x, e.y, gain=1))
        self.canvas_resz.bind("<ButtonPress-1>", lambda e: self.canvas_resz.scan_mark(e.x, e.y))
        self.canvas_resz.bind("<B1-Motion>",   lambda e: self.canvas_resz.scan_dragto(e.x, e.y, gain=1))

    def _restore_settings(self):
        """保存された設定を復元"""
        # モード復元
        self.mode_var.set(self.settings["mode"])
        
        # 値復元
        self.pct_var.set(self.settings["ratio_value"])
        self.w_var.set(self.settings["width_value"])
        self.h_var.set(self.settings["height_value"])
        try:
            saved_quality = int(self.settings.get("quality", "85"))
        except (TypeError, ValueError):
            saved_quality = 85
        self.quality_var.set(str(normalize_quality(saved_quality)))
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

        # ウィンドウサイズ復元
        try:
            self.geometry(self.settings["window_geometry"])
        except Exception:
            self.geometry("1200x800")  # フォールバック
        
        # ズーム設定復元
        self.zoom_var.set(self.settings["zoom_preference"])
        self._apply_log_level()
        self._toggle_exif_edit_fields()
        self._set_details_panel_visibility(details_expanded)
        self._update_settings_summary()
    
    def _save_current_settings(self):
        """現在の設定を保存"""
        self.settings.update({
            "mode": self.mode_var.get(),
            "ratio_value": self.pct_var.get(),
            "width_value": self.w_var.get(),
            "height_value": self.h_var.get(),
            "quality": self.quality_var.get(),
            "output_format": FORMAT_LABEL_TO_ID.get(self.output_format_var.get(), "auto"),
            "exif_mode": EXIF_LABEL_TO_ID.get(self.exif_mode_var.get(), "keep"),
            "remove_gps": self.remove_gps_var.get(),
            "exif_artist": self.exif_artist_var.get(),
            "exif_copyright": self.exif_copyright_var.get(),
            "exif_user_comment": self.exif_user_comment_var.get(),
            "exif_datetime_original": self.exif_datetime_original_var.get(),
            "dry_run": self.dry_run_var.get(),
            "verbose_logging": self.verbose_log_var.get(),
            "details_expanded": self.details_expanded,
            "window_geometry": self.geometry(),
            "zoom_preference": self.zoom_var.get()
        })
        self.settings_manager.save_settings(self.settings)
    
    def _on_closing(self):
        """アプリ終了時の処理"""
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
            verbose=self.verbose_log_var.get(),
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
        # 前回のディレクトリから開始
        initial_dir = self.settings.get("last_input_dir", "")
        
        paths = filedialog.askopenfilenames(
            title="画像を選択", 
            initialdir=initial_dir,
            filetypes=[("画像", "*.png *.jpg *.jpeg *.webp *.avif"), ("すべて", "*.*")]
        )
        if not paths:
            return
            
        # ディレクトリを記憶
        self.settings["last_input_dir"] = str(Path(paths[0]).parent)

        # 新規選択として状態を初期化する
        self.jobs.clear()
        self.current_index = None
        for p in paths:
            try:
                with Image.open(p) as opened:
                    opened.load()
                    # EXIF Orientationを正規化して表示/処理を統一する。
                    img = ImageOps.exif_transpose(opened)
            except Exception as e:  # pragma: no cover
                messagebox.showerror("エラー", f"{p} の読み込みに失敗しました: {e}")
                continue
            self.jobs.append(ImageJob(Path(p), img))
        self._populate_listbox()

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
                command=lambda idx=i: self._on_select_change(idx)
            )
            button.pack(fill="x", padx=10, pady=5)
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

    def _on_select_change(self, idx: Optional[int] = None) -> None:
        """Handle file selection change."""
        if idx is None:
            idx = 0
        if self.current_index == idx or idx >= len(self.jobs):
            return

        # Update button highlights
        if self.current_index is not None and self.current_index < len(self.file_buttons):
            self.file_buttons[self.current_index].configure(fg_color=customtkinter.ThemeManager.theme["CTkButton"]["fg_color"])
        
        self.current_index = idx
        self.file_buttons[idx].configure(fg_color=customtkinter.ThemeManager.theme["CTkButton"]["hover_color"])

        # Update previews and info
        job = self.jobs[idx]
        now = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.status_var.set(f"[{now}] {job.path.name} を選択しました")
        logger.info(f"Selected: {job.path.name}")

        self._reset_zoom()
        self._draw_previews(job)

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

    def _preview_current(self):
        if self.current_index is None:
            messagebox.showwarning("ファイル未選択", "ファイルを選択してください")
            return
        job = self.jobs[self.current_index]
        job.resized = self._process_image(job.image)
        self._draw_previews(job)

    def _save_current(self):
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

    def _batch_save(self):
        if not self.jobs:
            messagebox.showwarning("ファイル未選択", "ファイルが選択されていません")
            return

        _, _, target = self._get_settings_summary()
        if not target:
            messagebox.showwarning("設定エラー", "リサイズ設定が無効です")
            return

        initial_dir = self.settings.get("last_output_dir") or self.settings.get("last_input_dir") or Path.home()
        output_dir_str = filedialog.askdirectory(title="保存先フォルダを選択", initialdir=str(initial_dir))
        if not output_dir_str:
            return

        output_dir = Path(output_dir_str)
        self.settings["last_output_dir"] = str(output_dir)

        self.progress_bar.pack(side="bottom", fill="x", padx=10, pady=(0, 5))
        self.cancel_button.pack(side="bottom", pady=(0, 10))
        self.progress_bar.set(0)
        self._cancel_batch = False

        processed_count = 0
        failed_count = 0
        dry_run_count = 0
        exif_applied_count = 0
        exif_fallback_count = 0
        gps_removed_count = 0
        total_files = len(self.jobs)
        exif_mode = EXIF_LABEL_TO_ID.get(self.exif_mode_var.get(), "keep")
        batch_exif_edit_values = (
            self._current_exif_edit_values(show_warning=True) if exif_mode == "edit" else None
        )

        for i, job in enumerate(self.jobs):
            if self._cancel_batch:
                break

            self.status_var.set(f"処理中: {i+1}/{total_files} - {job.path.name}")
            self.progress_bar.set((i + 1) / total_files)
            self.update_idletasks()

            resized_img = self._process_image(job.image)
            if resized_img:
                output_format = self._resolve_output_format_for_image(job.image)
                options = self._build_save_options(output_format, exif_edit_values=batch_exif_edit_values)
                out_base = self._build_unique_batch_base_path(
                    output_dir=output_dir,
                    stem=job.path.stem,
                    output_format=output_format,
                    dry_run=options.dry_run,
                )
                result = save_image(
                    source_image=job.image,
                    resized_image=resized_img,
                    output_path=out_base,
                    options=options,
                )
                if result.success:
                    processed_count += 1
                    if result.dry_run:
                        dry_run_count += 1
                    if result.exif_attached:
                        exif_applied_count += 1
                    if result.exif_fallback_without_metadata:
                        exif_fallback_count += 1
                    if result.gps_removed:
                        gps_removed_count += 1
                else:
                    failed_count += 1
                    logging.error(f"Failed to save {result.output_path}: {result.error}")
            else:
                failed_count += 1

        self.progress_bar.pack_forget()
        self.cancel_button.pack_forget()

        if self._cancel_batch:
            msg = (
                f"一括処理がキャンセルされました。"
                f"({processed_count}/{total_files}件完了)"
            )
        else:
            mode_text = "ドライラン" if self.dry_run_var.get() else "保存"
            msg = (
                f"一括処理完了。{processed_count}/{total_files}件を{mode_text}しました。"
                f"\n失敗: {failed_count}件 / EXIF付与: {exif_applied_count}件 / EXIFフォールバック: {exif_fallback_count}件 / GPS削除: {gps_removed_count}件"
            )
            if self.dry_run_var.get():
                msg += f"\nドライラン件数: {dry_run_count}件"
        self.status_var.set(msg)
        messagebox.showinfo("完了", msg)

    def _cancel_batch_save(self):
        self._cancel_batch = True

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
            quality = self._current_quality()
            with io.BytesIO() as bio:
                preview_kwargs: dict[str, object] = {}
                save_img = job.resized
                if output_format in {"jpeg", "avif"} and save_img.mode in {"RGBA", "LA", "P"}:
                    save_img = save_img.convert("RGB")
                if output_format == "jpeg":
                    preview_kwargs = {"format": "JPEG", "quality": min(quality, 95), "optimize": True}
                elif output_format == "png":
                    preview_kwargs = {
                        "format": "PNG",
                        "optimize": True,
                        "compress_level": int(round((100 - quality) / 100 * 9)),
                    }
                elif output_format == "webp":
                    preview_kwargs = {"format": "WEBP", "quality": quality, "method": 6}
                else:
                    preview_kwargs = {"format": "AVIF", "quality": quality}
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
        canvas.create_text(10, 10, text=label, anchor="nw", fill="white", font=self.font_small)
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
