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
import traceback
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Tuple
from tkinter import filedialog, messagebox

import customtkinter
from PIL import Image, ImageTk

# ヘルプコンテンツとダイアログをインポート
from karuku_resizer.help_content import HELP_CONTENT, STEP_DESCRIPTIONS
from karuku_resizer.help_dialog import HelpDialog

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
        self.default_settings = {
            "mode": "ratio",
            "ratio_value": "100",
            "width_value": "",
            "height_value": "",
            "last_input_dir": "",
            "last_output_dir": "",
            "window_geometry": "1200x800",
            "zoom_preference": "画面に合わせる"
        }
    
    def load_settings(self) -> dict:
        if not self.settings_file.exists():
            return self.default_settings.copy()
        
        try:
            with open(self.settings_file, 'r', encoding='utf-8') as f:
                settings = json.load(f)
                # デフォルト値とマージ
                merged = self.default_settings.copy()
                merged.update(settings)
                return merged
        except Exception:
            return self.default_settings.copy()
    
    def save_settings(self, settings: dict):
        try:
            with open(self.settings_file, 'w', encoding='utf-8') as f:
                json.dump(settings, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logging.error(f"設定保存エラー: {e}")


class ResizeApp(customtkinter.CTk):
    def __init__(self) -> None:
        super().__init__()

        # 設定マネージャー初期化
        self.settings_manager = SettingsManager()
        self.settings = self.settings_manager.load_settings()

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
        
        # catch Tkinter callback exceptions in debug mode
        if DEBUG:
            self.report_callback_exception = self._report_callback_exception
        
        # ウィンドウ閉じる時のイベント
        self.protocol("WM_DELETE_WINDOW", self._on_closing)

        self.jobs: List[ImageJob] = []
        self.current_index: Optional[int] = None
        self._cancel_batch = False

        self._setup_ui()
        self._restore_settings()
        
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
        self._setup_main_layout()

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
        try:
            geometry = self.settings.get("window_geometry", "1200x800")
            if geometry: 
                self.geometry(geometry)
            self.mode_var.set(self.settings.get("mode", "ratio"))
            self.pct_var.set(self.settings.get("ratio_value", "100"))
            self.w_var.set(self.settings.get("width_value", ""))
            self.h_var.set(self.settings.get("height_value", ""))
            self.zoom_var.set(self.settings.get("zoom_preference", "画面に合わせる"))
            self._update_mode()
        except Exception as e:
            logging.error(f"Failed to restore settings: {e}")
            # In case of corrupt settings, proceed with defaults
            pass

    def _save_current_settings(self):
        """現在の設定を保存"""
        self.settings.update({
            "mode": self.mode_var.get(),
            "ratio_value": self.pct_var.get(),
            "width_value": self.w_var.get(),
            "height_value": self.h_var.get(),
            "window_geometry": self.geometry(),
            "zoom_preference": self.zoom_var.get(),
            "last_input_dir": self.settings.get("last_input_dir"),
            "last_output_dir": self.settings.get("last_output_dir"),
        })
        self.settings_manager.save_settings(self.settings)

    def _on_closing(self):
        """アプリ終了時の処理"""
        self._save_current_settings()
        self.destroy()

    @staticmethod
    def _validate_int(text: str) -> bool:
        """Return True if text is empty or all digits."""
        return text == "" or text.isdigit()

    def _get_settings_summary(self):
        """Return (settings_text, fmt, target) for current UI selections."""
        mode = self.mode_var.get()
        settings_text = ""
        if mode == "ratio":
            pct = self.pct_var.get().strip() or "---"
            settings_text = f"倍率 {pct}%"
        elif mode == "width":
            w = self.w_var.get().strip() or "---"
            settings_text = f"幅 {w}px"
        elif mode == "height":
            h = self.h_var.get().strip() or "---"
            settings_text = f"高さ {h}px"
        elif mode == "fixed":
            w = self.w_var.get().strip() or "---"
            h = self.h_var.get().strip() or "---"
            settings_text = f"固定 {w}×{h}px"

        fmt = "JPEG"
        target = None
        if self.current_index is not None:
            job = self.jobs[self.current_index]
            if job.image.mode in ("RGBA", "LA") or "transparency" in job.image.info:
                fmt = "PNG"
            target = self._get_target(job.image.size)
        return settings_text, fmt, target

    def _report_callback_exception(self, exc, val, tb):
        messagebox.showerror("エラー", "".join(traceback.format_exception(exc, val, tb)))

    def _update_mode(self, _e=None):
        """UI state when the mode radio buttons are changed."""
        mode = self.mode_var.get()
        if self.active_mode_frame:
            self.active_mode_frame.pack_forget()
        self.active_mode_frame = self.mode_frames[mode]
        self.active_mode_frame.pack(side="left")
        if self.current_index is not None:
            self._preview_current()

    def _select_files(self):
        initial_dir = self.settings.get("last_input_dir") or Path.home()
        filepaths = filedialog.askopenfilenames(
            title="画像ファイルを選択",
            initialdir=str(initial_dir),
            filetypes=[
                ("Image files", "*.jpg *.jpeg *.png *.bmp *.gif *.tiff"),
                ("All files", "*.*"),
            ],
        )
        if not filepaths:
            return
        
        self.settings["last_input_dir"] = str(Path(filepaths[0]).parent)
        new_jobs = []
        for p in filepaths:
            try:
                new_jobs.append(ImageJob(path=Path(p), image=Image.open(p)))
            except Exception as e:
                logging.error(f"Failed to load image {p}: {e}")
                messagebox.showerror("画像読み込みエラー", f"{Path(p).name} を読み込めませんでした。\n{e}")
        
        self.jobs = new_jobs
        self._populate_listbox()
        if self.jobs:
            self._on_select_change(0)

    def _populate_listbox(self):
        for w in self.file_buttons:
            w.destroy()
        self.file_buttons.clear()
        for i, job in enumerate(self.jobs):
            btn = customtkinter.CTkButton(
                self.file_list_frame,
                text=job.path.name,
                command=lambda idx=i: self._on_select_change(idx),
                fg_color="transparent",
                text_color_disabled="gray",
                anchor="w",
                font=self.font_small
            )
            btn.pack(fill="x", expand=True)
            self.file_buttons.append(btn)

    def _on_select_change(self, idx: Optional[int] = None):
        """Handle file selection change."""
        if idx is None or not (0 <= idx < len(self.jobs)):
            self.current_index = None
            self.canvas_org.delete("all")
            self.canvas_resz.delete("all")
            self.info_orig_var.set("--- x ---  ---")
            self.info_resized_var.set("--- x ---  ---  (---)")
            return

        if self.current_index is not None:
            self.file_buttons[self.current_index].configure(font=self.font_small)
        
        self.current_index = idx
        job = self.jobs[idx]
        self.file_buttons[idx].configure(font=customtkinter.CTkFont(family="Yu Gothic UI", size=12, weight="bold"))
        
        self._reset_zoom()
        self._draw_previews(job)

    def _get_target(self, orig: Tuple[int, int]) -> Optional[Tuple[int, int]]:
        """Get target (w,h) from UI, returns None if invalid."""
        mode = self.mode_var.get()
        w_orig, h_orig = orig
        try:
            if mode == "ratio":
                pct = int(self.pct_var.get())
                if pct <= 0: return None
                return int(w_orig * pct / 100), int(h_orig * pct / 100)
            elif mode == "width":
                w = int(self.w_var.get())
                if w <= 0: return None
                return w, int(h_orig * w / w_orig)
            elif mode == "height":
                h = int(self.h_var.get())
                if h <= 0: return None
                return int(w_orig * h / h_orig), h
            elif mode == "fixed":
                w = int(self.w_var.get())
                h = int(self.h_var.get())
                if w <= 0 or h <= 0: return None
                return w, h
        except ValueError:
            return None 
        return None

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
        self._draw_previews(job)

    def _save_current(self):
        if self.current_index is None:
            messagebox.showwarning("ファイル未選択", "ファイルを選択してください")
            return
        
        job = self.jobs[self.current_index]
        if not job.resized:
            job.resized = self._process_image(job.image)
        if not job.resized:
            return

        _, fmt, _ = self._get_settings_summary()
        initial_dir = self.settings.get("last_output_dir") or Path.home()
        initial_file = f"{job.path.stem}_resized.{fmt.lower()}"
        
        save_path_str = filedialog.asksaveasfilename(
            title="名前を付けて保存",
            initialdir=str(initial_dir),
            initialfile=initial_file,
            filetypes=[
                ("JPEG", "*.jpg"),
                ("PNG", "*.png"),
                ("All files", "*.*"),
            ],
            defaultextension=f".{fmt.lower()}"
        )
        if not save_path_str:
            return

        save_path = Path(save_path_str)
        self.settings["last_output_dir"] = str(save_path.parent)
        
        try:
            job.resized.save(save_path, quality=95, optimize=True)
            self.status_var.set(f"{save_path.name} を保存しました")
        except Exception as e:
            messagebox.showerror("保存エラー", f"ファイルの保存に失敗しました:\n{e}")

    def _batch_save(self):
        if not self.jobs:
            messagebox.showwarning("ファイル未選択", "ファイルが選択されていません")
            return
        
        _, fmt, target = self._get_settings_summary()
        if not target:
            messagebox.showwarning("設定エラー", "リサイズ設定が無効です")
            return

        initial_dir = self.settings.get("last_output_dir") or self.settings.get("last_input_dir") or Path.home()
        output_dir_str = filedialog.askdirectory(title="保存先フォルダを選択", initialdir=str(initial_dir))
        if not output_dir_str:
            return

        output_dir = Path(output_dir_str)
        self.settings["last_output_dir"] = str(output_dir)

        # Show progress bar and cancel button
        progress_frame = customtkinter.CTkFrame(self)
        progress_frame.place(relx=0.5, rely=0.5, anchor="center")
        self.progress_bar = customtkinter.CTkProgressBar(progress_frame, width=400, height=20)
        self.progress_bar.pack(pady=10)
        self.cancel_button = customtkinter.CTkButton(progress_frame, text="キャンセル", width=100, command=self._cancel_batch_save)
        self.cancel_button.pack(pady=5)
        self.progress_bar.set(0)
        self._cancel_batch = False

        processed_count = 0
        total_files = len(self.jobs)
        
        for i, job in enumerate(self.jobs):
            if self._cancel_batch:
                break
            
            self.status_var.set(f"処理中: {i+1}/{total_files} - {job.path.name}")
            self.progress_bar.set((i + 1) / total_files)
            self.update_idletasks()
            
            try:
                resized_img = self._process_image(job.image)
                if resized_img:
                    out_name = f"{job.path.stem}_resized.{fmt.lower()}"
                    out_path = output_dir / out_name
                    resized_img.save(out_path, quality=95, optimize=True)
                    processed_count += 1
            except Exception as e:
                logging.error(f"Failed to save {job.path.name}: {e}")

        progress_frame.destroy()
        
        if self._cancel_batch:
            msg = f"一括処理がキャンセルされました。({processed_count}/{total_files}件完了)"
        else:
            msg = f"一括処理完了。{processed_count}/{total_files}件の画像を保存しました。"
        
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
        job.resized = self._process_image(job.image)
        if job.resized:
            self._imgtk_resz = self._draw_image_on_canvas(self.canvas_resz, job.resized, is_resized=True)
            size = job.resized.size
            with io.BytesIO() as bio:
                job.resized.save(bio, format="JPEG", quality=95)
                kb = len(bio.getvalue()) / 1024
            orig_w, orig_h = job.image.size
            pct = (size[0] * size[1]) / (orig_w * orig_h) * 100 if (orig_w * orig_h) > 0 else 0
            self.info_resized_var.set(f"{size[0]} x {size[1]}  {kb:.1f}KB ({pct:.1f}%)")
            self.resized_title_label.configure(text=f"リサイズ後 ({self._get_settings_summary()[0]})")
        else:
            self.canvas_resz.delete("all")
            self.info_resized_var.set("--- x ---  ---  (---)")
            self.resized_title_label.configure(text="リサイズ後")

    def _draw_image_on_canvas(self, canvas: customtkinter.CTkCanvas, img: Image.Image, is_resized: bool) -> Optional[ImageTk.PhotoImage]:
        canvas.delete("all")
        canvas_w, canvas_h = canvas.winfo_width(), canvas.winfo_height()
        if canvas_w <= 1 or canvas_h <= 1:
            return None

        zoom_attr = "_zoom_resz" if is_resized else "_zoom_org"
        zoom = getattr(self, zoom_attr)
        label = f"{int(zoom*100)}%" if zoom is not None else "画面に合わせる"

        if zoom is None:
            if img.width > 0 and img.height > 0:
                zoom = min(canvas_w / img.width, canvas_h / img.height)
            else:
                zoom = 1.0
            label = f"Fit ({int(zoom*100)}%)"

        disp = img.copy()
        new_size = (int(disp.width * zoom), int(disp.height * zoom))
        if new_size[0] <= 0 or new_size[1] <= 0:
            return None

        disp = disp.resize(new_size, Resampling.LANCZOS)
        imgtk = ImageTk.PhotoImage(disp)

        x = (canvas_w - new_size[0]) // 2
        y = (canvas_h - new_size[1]) // 2
        canvas.create_image(x, y, anchor="nw", image=imgtk)
        canvas.create_text(10, 10, text=label, anchor="nw", fill="white", font=self.font_small)
        return imgtk

    def _reset_zoom(self):
        """Resets the zoom level to 'Fit to Screen' in both state and UI."""
        self._zoom_org = None
        self._zoom_resz = None
        self.zoom_var.set("画面に合わせる")

    def _apply_zoom_selection(self, choice: str):
        """Applies the zoom level selected in the combobox."""
        if choice == "画面に合わせる":
            self._zoom_org = None
            self._zoom_resz = None
        else:
            # e.g. "100%" -> 1.0
            zoom_val = float(choice.replace("%", "")) / 100.0
            self._zoom_org = zoom_val
            self._zoom_resz = zoom_val
        
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

    def _show_help(self):
        """使い方ヘルプを表示する"""
        HelpDialog(self, title="使い方ガイド", help_content=HELP_CONTENT, step_descriptions=STEP_DESCRIPTIONS)
        # モード復元
        self.mode_var.set(self.settings["mode"])
        
        # 値復元
        self.pct_var.set(self.settings["ratio_value"])
        self.w_var.set(self.settings["width_value"])
        self.h_var.set(self.settings["height_value"])
        
        # ウィンドウサイズ復元
        try:
            self.geometry(self.settings["window_geometry"])
        except:
            self.geometry("1200x800")  # フォールバック
        
        # ズーム設定復元
        self.zoom_var.set(self.settings["zoom_preference"])
    
    def _save_current_settings(self):
        """現在の設定を保存"""
        self.settings.update({
            "mode": self.mode_var.get(),
            "ratio_value": self.pct_var.get(),
            "width_value": self.w_var.get(),
            "height_value": self.h_var.get(),
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

    def _get_settings_summary(self):
        """Return (settings_text, fmt, target) for current UI selections.

        settings_text: human-readable string such as "幅 800px".
        fmt: default output format (PNG if alpha channel else JPEG).
        target: tuple[int,int] desired size or None if invalid.
        """
        mode = self.mode_var.get()
        if mode == "ratio":
            pct = self.ratio_entry.get().strip() or "---"
            settings_text = f"倍率 {pct}%"
        elif mode == "width":
            w = self.entry_w_single.get().strip() or "---"
            settings_text = f"幅 {w}px"
        elif mode == "height":
            h = self.entry_h_single.get().strip() or "---"
            settings_text = f"高さ {h}px"
        else:  # fixed
            w = self.entry_w_fixed.get().strip() or "---"
            h = self.entry_h_fixed.get().strip() or "---"
            settings_text = f"固定 {w}×{h}px"

        # decide default format and calculate target using first image if any
        fmt = "JPEG"
        target = None
        if self.jobs:
            first_img = self.jobs[0].image
            fmt = "PNG" if ("A" in first_img.getbands() or first_img.mode in ("P", "1")) else "JPEG"
            target = self._get_target(first_img.size)
        return settings_text, fmt, target

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
            filetypes=[("画像", "*.png *.jpg *.jpeg *.webp"), ("すべて", "*.*")]
        )
        if not paths:
            return
            
        # ディレクトリを記憶
        self.settings["last_input_dir"] = str(Path(paths[0]).parent)
        
        self.jobs.clear()
        for p in paths:
            try:
                img = Image.open(p)
            except Exception as e:  # pragma: no cover
                messagebox.showerror("エラー", f"{p} の読み込みに失敗しました: {e}")
                continue
            self.jobs.append(ImageJob(Path(p), img))
        self._populate_listbox()
        if self.jobs:
            self._on_select_change()

    def _populate_listbox(self):
        for button in self.file_buttons:
            button.destroy()
        self.file_buttons = []
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
        self._update_info_labels(job.image, job.resized)    # --
    # ------------------ size calculation -----------------------------
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
        h = self._parse_positive(self.entry_h_fixed)
        if w is None or h is None:
            return None
        return w, h

    # -------------------- processing core ------------------------------
    def _process_image(self, img: Image.Image) -> Tuple[Image.Image, str]:
        target = self._get_target(img.size)
        # if no size specified yet, keep original dimensions
        if target is None:
            tw, th = img.size
        else:
            tw, th = target
        if (tw, th) != img.size:
            img = img.resize((tw, th), Resampling.LANCZOS)
        # choose PNG if image has alpha or is palette/bitmap
        fmt = "PNG" if ("A" in img.getbands() or img.mode in ("P", "1")) else "JPEG"
        return img, fmt

    # -------------------- preview / save -------------------------------
    def _preview_current(self):
        logging.debug('_preview_current called')
        if self.current_index is None:
            return
        job = self.jobs[self.current_index]

        try:
            job.resized, fmt = self._process_image(job.image)
        except ValueError:
            return  # validation error already shown
        self._draw_previews(job)
        self._update_info_labels(job.image, job.resized, fmt)
        self.status_var.set("プレビューを更新しました")

    def _save_current(self):
        if self.current_index is None:
            messagebox.showwarning("警告", "画像が選択されていません。")
            return
        job = self.jobs[self.current_index]

        # Process image if not already done
        if job.resized is None:
            try:
                job.resized, fmt = self._process_image(job.image)
            except ValueError as e:
                messagebox.showerror("設定エラー", f"画像の処理中にエラーが発生しました:\n{e}")
                return
        else:
            fmt = "PNG" if "A" in job.resized.getbands() else "JPEG"

        # Get details for confirmation
        new_dims = job.resized.size
        file_size = self._encoded_size_bytes(job.resized, fmt)
        file_size_str = self._format_bytes(file_size)

        # Get settings text using helper for consistency
        settings_text, _fmt_unused, _target_unused = self._get_settings_summary()

        # Show confirmation dialog
        confirm_msg = (
            f"以下の内容で画像を保存します。\n\n"
            f"設定: {settings_text}\n"
            f"出力サイズ: {new_dims[0]} × {new_dims[1]} px\n"
            f"形式: {fmt}\n"
            f"ファイルサイズ (推定): {file_size_str}\n\n"
            f"よろしいですか？"
        )
        if not messagebox.askyesno("保存の確認", confirm_msg):
            return

        # 前回の出力ディレクトリから開始
        initial_dir = self.settings.get("last_output_dir", "")

        # Get filename and save
        now = datetime.now().strftime("%Y%m%d_%H%M%S")
        initial_name = f"{now}_{job.path.name}"
        fname = filedialog.asksaveasfilename(
            title="画像を保存",
            initialdir=initial_dir,
            initialfile=initial_name,
            defaultextension="." + fmt.lower(),
            filetypes=[(fmt, "*.*")])
        if not fname:
            return
            
        # ディレクトリを記憶
        self.settings["last_output_dir"] = str(Path(fname).parent)
        
        self._save_image(job.resized, Path(fname), fmt)
        self.status_var.set(f"「{Path(fname).name}」を保存しました")
        messagebox.showinfo("保存", "保存が完了しました")

    def _batch_save(self):
        if not self.jobs:
            messagebox.showwarning("警告", "画像が選択されていません。")
            return

        num_files = len(self.jobs)
        settings_text, fmt, target = self._get_settings_summary()
        if target is None:
            messagebox.showerror("エラー", "リサイズ設定が無効です。数値を確認してください。")
            return

        # Use the first image for preview in confirmation
        first_job = self.jobs[0]
        new_dims = self._get_target(first_job.image.size)
        if not new_dims:
            messagebox.showerror("エラー", "最初画像のサイズ計算に失敗しました。")
            return

        try:
            # Create a temporary resized image for file size estimation
            temp_resized_img = first_job.image.copy()
            temp_resized_img.thumbnail(new_dims, Image.Resampling.LANCZOS)
            file_size_str = self._format_bytes(self._encoded_size_bytes(temp_resized_img, fmt))
        except Exception as e:
            messagebox.showerror("プレビューエラー", f"ファイルサイズ推定中にエラー: {e}")
            return

        # Show confirmation dialog
        confirm_msg = (
            f"{num_files}個の画像を一括保存します。\n\n"
            f"適用する設定: {settings_text}\n\n"
            f"--- 最初の画像の変換結果 (参考) ---\n"
            f"出力サイズ: {new_dims[0]} × {new_dims[1]} px\n"
            f"形式: {fmt}\n"
            f"ファイルサイズ (推定): {file_size_str}\n"
            f"-------------------------------------\n\n"
            f"よろしいですか？"
        )
        if not messagebox.askyesno("一括保存の確認", confirm_msg):
            return

        # Ask for output directory
        initial_dir = self.settings.get("last_output_dir", "")
        out_dir_name = filedialog.askdirectory(title="出力フォルダーを選択", initialdir=initial_dir)
        if not out_dir_name:
            return

        # ディレクトリを記憶
        self.settings["last_output_dir"] = out_dir_name

        out_dir = Path(out_dir_name)
        now = datetime.now().strftime("%Y%m%d_%H%M%S")
        errors = []

        # プログレスバーとキャンセルボタンを表示
        self.progress_bar.pack(side="bottom", fill="x", padx=10, pady=(0, 5))
        self.cancel_button.pack(side="bottom", pady=5)
        self.progress_bar.set(0)
        self._cancel_batch = False

        total_files = len(self.jobs)
        
        for i, job in enumerate(self.jobs):
            if self._cancel_batch:
                self.status_var.set("一括保存がキャンセルされました")
                break
                
            try:
                new_img = job.image.copy()
                new_img.thumbnail(target, Resampling.LANCZOS)
                new_name = f"{now}_{job.path.name}"
                out_path = out_dir / new_name
                self._save_image(new_img, out_path, fmt)
                
                # プログレス更新
                progress = (i + 1) / total_files
                self.progress_bar.set(progress)
                self.status_var.set(f"処理中... {i+1}/{total_files} ({int(progress*100)}%)")
                self.update()  # UI更新を強制
                
            except Exception as e:
                errors.append(f"{job.path.name}: {e}")

        # プログレスバーとキャンセルボタンを非表示
        self.progress_bar.pack_forget()
        self.cancel_button.pack_forget()

        if not self._cancel_batch:
            if errors:
                error_details = "\n".join(errors)
                messagebox.showwarning("一括保存エラー", f"{len(errors)}件の画像処理に失敗しました:\n\n{error_details[:1000]}")
            else:
                messagebox.showinfo("成功", f"{num_files}個の画像を正常に保存しました。")
                self.status_var.set(f"{num_files}個の画像を保存完了")

    def _cancel_batch_save(self):
        """一括保存をキャンセル"""
        self._cancel_batch = True
    # -
    # ------------------- Settings Management ---------------------------
    def _restore_settings(self):
        """保存された設定を復元"""
        # モード復元
        self.mode_var.set(self.settings["mode"])
        
        # 値復元
        self.pct_var.set(self.settings["ratio_value"])
        self.w_var.set(self.settings["width_value"])
        self.h_var.set(self.settings["height_value"])
        
        # ウィンドウサイズ復元
        try:
            self.geometry(self.settings["window_geometry"])
        except:
            self.geometry("1200x800")  # フォールバック
        
        # ズーム設定復元
        self.zoom_var.set(self.settings["zoom_preference"])
    
    def _save_current_settings(self):
        """現在の設定を保存"""
        self.settings.update({
            "mode": self.mode_var.get(),
            "ratio_value": self.pct_var.get(),
            "width_value": self.w_var.get(),
            "height_value": self.h_var.get(),
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

    def _get_settings_summary(self):
        """Return (settings_text, fmt, target) for current UI selections.

        settings_text: human-readable string such as "幅 800px".
        fmt: default output format (PNG if alpha channel else JPEG).
        target: tuple[int,int] desired size or None if invalid.
        """
        mode = self.mode_var.get()
        if mode == "ratio":
            pct = self.ratio_entry.get().strip() or "---"
            settings_text = f"倍率 {pct}%"
        elif mode == "width":
            w = self.entry_w_single.get().strip() or "---"
            settings_text = f"幅 {w}px"
        elif mode == "height":
            h = self.entry_h_single.get().strip() or "---"
            settings_text = f"高さ {h}px"
        else:  # fixed
            w = self.entry_w_fixed.get().strip() or "---"
            h = self.entry_h_fixed.get().strip() or "---"
            settings_text = f"固定 {w}×{h}px"

        # decide default format and calculate target using first image if any
        fmt = "JPEG"
        target = None
        if self.jobs:
            first_img = self.jobs[0].image
            fmt = "PNG" if ("A" in first_img.getbands() or first_img.mode in ("P", "1")) else "JPEG"
            target = self._get_target(first_img.size)
        return settings_text, fmt, target

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
            filetypes=[("画像", "*.png *.jpg *.jpeg *.webp"), ("すべて", "*.*")]
        )
        if not paths:
            return
            
        # ディレクトリを記憶
        self.settings["last_input_dir"] = str(Path(paths[0]).parent)
        
        self.jobs.clear()
        for p in paths:
            try:
                img = Image.open(p)
            except Exception as e:  # pragma: no cover
                messagebox.showerror("エラー", f"{p} の読み込みに失敗しました: {e}")
                continue
            self.jobs.append(ImageJob(Path(p), img))
        self._populate_listbox()
        if self.jobs:
            self._on_select_change()

    def _populate_listbox(self):
        for button in self.file_buttons:
            button.destroy()
        self.file_buttons = []
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
        self._update_info_labels(job.image, job.resized)    # 

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

        active_entries = self._entry_widgets[mode]

        try:
            if mode == "ratio":
                pct = int(self.pct_var.get())
                if pct <= 0: return None
                return int(w_orig * pct / 100), int(h_orig * pct / 100)

            elif mode == "width":
                w = int(self.w_var.get())
                if w <= 0: return None
                return w, int(h_orig * w / w_orig)

            elif mode == "height":
                h = int(self.h_var.get())
                if h <= 0: return None
                return int(w_orig * h / h_orig), h

            elif mode == "fixed":
                w = int(self.w_var.get())
                h = int(self.h_var.get())
                if w <= 0 or h <= 0: return None
                return w, h
        except ValueError:
            return None # Entry is not a valid int

        return None

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
            customtkinter.messagebox.showwarning("ファイル未選択", "ファイルを選択してください")
            return

        job = self.jobs[self.current_index]
        if not job.resized:
            job.resized = self._process_image(job.image)
        if not job.resized:
            return  # processing failed

        _, fmt, _ = self._get_settings_summary()
        initial_dir = self.settings.get("last_output_dir") or Path.home()
        initial_file = f"{job.path.stem}_resized.jpg"

        save_path_str = customtkinter.filedialog.asksaveasfilename(
            title="名前を付けて保存",
            initialdir=str(initial_dir),
            initialfile=initial_file,
            filetypes=[
                ("JPEG", "*.jpg"),
                ("PNG", "*.png"),
                ("All files", "*.*"),
            ],
            defaultextension=f".{fmt.lower()}"
        )
        if not save_path_str:
            return

        save_path = Path(save_path_str)
        self.settings["last_output_dir"] = str(save_path.parent)

        try:
            job.resized.save(save_path, quality=95, optimize=True)
            self.status_var.set(f"{save_path.name} を保存しました")
        except Exception as e:
            customtkinter.messagebox.showerror("保存エラー", f"ファイルの保存に失敗しました:\n{e}")

    def _batch_save(self):
        if not self.jobs:
            customtkinter.messagebox.showwarning("ファイル未選択", "ファイルが選択されていません")
            return

        _, fmt, target = self._get_settings_summary()
        if not target:
            customtkinter.messagebox.showwarning("設定エラー", "リサイズ設定が無効です")
            return

        initial_dir = self.settings.get("last_output_dir") or self.settings.get("last_input_dir") or Path.home()
        output_dir_str = customtkinter.filedialog.askdirectory(title="保存先フォルダを選択", initialdir=str(initial_dir))
        if not output_dir_str:
            return

        output_dir = Path(output_dir_str)
        self.settings["last_output_dir"] = str(output_dir)

        # --- Show progress bar and cancel button ---
        self.progress_bar.pack(side="bottom", fill="x", padx=10, pady=(0, 5))
        self.cancel_button.pack(side="bottom", pady=(0, 10))
        self.progress_bar.set(0)
        self._cancel_batch = False

        processed_count = 0
        total_files = len(self.jobs)

        for i, job in enumerate(self.jobs):
            if self._cancel_batch:
                break

            self.status_var.set(f"処理中: {i+1}/{total_files} - {job.path.name}")
            self.progress_bar.set((i + 1) / total_files)
            self.update_idletasks() # Force UI update

            resized_img = self._process_image(job.image)
            if resized_img:
                out_name = f"{job.path.stem}_resized.{fmt.lower()}"
                out_path = output_dir / out_name
                try:
                    resized_img.save(out_path, quality=95, optimize=True)
                    processed_count += 1
                except Exception as e:
                    logging.error(f"Failed to save {out_path}: {e}")

        # --- Hide progress bar and show result ---
        self.progress_bar.pack_forget()
        self.cancel_button.pack_forget()

        if self._cancel_batch:
            msg = f"一括処理がキャンセルされました。({processed_count}/{total_files}件完了)"
        else:
            msg = f"一括処理完了。{processed_count}/{total_files}件の画像を保存しました。"
        self.status_var.set(msg)
        customtkinter.messagebox.showinfo("完了", msg)

    def _cancel_batch_save(self):
        self._cancel_batch = True

    # -------------------- Preview drawing ----------------------------

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
            
            # Get byte size of resized image
            with io.BytesIO() as bio:
                job.resized.save(bio, format="JPEG", quality=95)
                kb = len(bio.getvalue()) / 1024
            
            orig_w, orig_h = job.image.size
            pct = (size[0] * size[1]) / (orig_w * orig_h) * 100
            self.info_resized_var.set(f"{size[0]} x {size[1]}  {kb:.1f}KB ({pct:.1f}%)")
            self.resized_title_label.configure(text=f"リサイズ後 ({self._get_settings_summary()[0]})")
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
        HelpDialog(self, title="使い方ガイド", help_content=HELP_CONTENT, step_descriptions=STEP_DESCRIPTIONS)


# ----------------------------------------------------------------------

def main():
    """Package entry point (CLI script)."""
    app = ResizeApp()
    app.mainloop()


if __name__ == "__main__":
    main()