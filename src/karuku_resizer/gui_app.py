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
import tkinter as tk
import logging
import traceback
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from tkinter import filedialog, messagebox, ttk
from typing import List, Optional, Tuple

from PIL import Image, ImageTk
import tkinter.font as tkfont

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

# -------------------- UI color constants --------------------
UI_COLORS = {
    "primary": "#0078d4",
    "success": "#2e7d32",
    "danger": "#d32f2f",
    "active": "#dbeafe",  # light blue for current task
    "inactive": "white",
    "text_inactive": "#999999",
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

class ResizeApp(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        # -------------------- フォント設定 --------------------
        jp_font = ("Yu Gothic UI", 16)
        default_font = tkfont.nametofont("TkDefaultFont")
        default_font.config(family=jp_font[0], size=jp_font[1])
        self.option_add("*Font", jp_font)

        self.title("画像リサイズツール (DEBUG)" if DEBUG else "画像リサイズツール")
        # catch Tkinter callback exceptions in debug mode
        if DEBUG:
            self.report_callback_exception = self._report_callback_exception
        # 画面解像度に合わせてウィンドウサイズを調整
        screen_w = self.winfo_screenwidth()
        screen_h = self.winfo_screenheight()
        win_w = max(900, int(screen_w * 0.8))
        win_h = max(560, int(screen_h * 0.8))
        self.geometry(f"{win_w}x{win_h}")

        # -------------------- Step indicator -------------------
        self._step_labels: list[dict[str, tk.Widget]] = []
        self._create_step_indicator()
        self.minsize(900, 560)

        self.jobs: List[ImageJob] = []
        self.current_index: Optional[int] = None

        # -------------------- UI top bar --------------------------------
        top = tk.Frame(self)
        top.pack(side=tk.TOP, fill=tk.X, padx=4, pady=4)

        tk.Button(top, text="📂 画像を選択", command=self._select_files).pack(side=tk.LEFT)
        tk.Button(top, text="❓ 使い方", command=self._show_help).pack(side=tk.LEFT, padx=4)

        # Mode radio buttons
        self.mode_var = tk.StringVar(value="ratio")
        modes = [
            ("比率 %", "ratio"),
            ("幅 px", "width"),
            ("高さ px", "height"),
            ("幅×高", "fixed"),
        ]
        for text, val in modes:
            tk.Radiobutton(top, text=text, variable=self.mode_var, value=val, command=self._update_mode).pack(side=tk.LEFT, padx=2)

        # --- Container for mode-specific input widgets ---
        self.mode_options_container = tk.Frame(top)
        self.mode_options_container.pack(side=tk.LEFT, padx=4)

        vcmd = (self.register(self._validate_int), "%P")

        # --- Create widgets and frames for each mode ---
        self.pct_var = tk.StringVar()
        self.w_var = tk.StringVar()
        self.h_var = tk.StringVar()

        # Ratio Mode
        frame_ratio = tk.Frame(self.mode_options_container)
        self.entry_pct = tk.Entry(frame_ratio, textvariable=self.pct_var, width=5, validate="key", validatecommand=vcmd)
        self.entry_pct.pack(side=tk.LEFT)
        tk.Label(frame_ratio, text="%").pack(side=tk.LEFT)

        # Width Mode
        frame_width = tk.Frame(self.mode_options_container)
        self.entry_w_single = tk.Entry(frame_width, textvariable=self.w_var, width=6, validate="key", validatecommand=vcmd)
        self.entry_w_single.pack(side=tk.LEFT)
        tk.Label(frame_width, text="px").pack(side=tk.LEFT)

        # Height Mode
        frame_height = tk.Frame(self.mode_options_container)
        self.entry_h_single = tk.Entry(frame_height, textvariable=self.h_var, width=6, validate="key", validatecommand=vcmd)
        self.entry_h_single.pack(side=tk.LEFT)
        tk.Label(frame_height, text="px").pack(side=tk.LEFT)

        # Fixed Mode
        frame_fixed = tk.Frame(self.mode_options_container)
        self.entry_w_fixed = tk.Entry(frame_fixed, textvariable=self.w_var, width=6, validate="key", validatecommand=vcmd)
        self.entry_w_fixed.pack(side=tk.LEFT)
        tk.Label(frame_fixed, text="×").pack(side=tk.LEFT)
        self.entry_h_fixed = tk.Entry(frame_fixed, textvariable=self.h_var, width=6, validate="key", validatecommand=vcmd)
        self.entry_h_fixed.pack(side=tk.LEFT)
        tk.Label(frame_fixed, text="px").pack(side=tk.LEFT)

        # --- Group frames and entries for easy management ---
        self.mode_frames = {
            "ratio": frame_ratio,
            "width": frame_width,
            "height": frame_height,
            "fixed": frame_fixed,
        }
        self.active_mode_frame: Optional[tk.Frame] = None

        self._all_entries = [
            self.entry_pct,
            self.entry_w_single, self.entry_h_single,
            self.entry_w_fixed, self.entry_h_fixed
        ]
        self._entry_widgets = {
            "ratio": [self.entry_pct],
            "width": [self.entry_w_single],
            "height": [self.entry_h_single],
            "fixed": [self.entry_w_fixed, self.entry_h_fixed],
        }

        tk.Button(top, text="🔄 プレビュー", command=self._preview_current).pack(side=tk.LEFT, padx=4)
        tk.Button(top, text="💾 保存", command=self._save_current).pack(side=tk.LEFT)
        tk.Button(top, text="📁 一括保存", command=self._batch_save).pack(side=tk.LEFT)

        # Zoom combobox
        self.zoom_var = tk.StringVar(value="画面に合わせる")
        zoom_cb = ttk.Combobox(top, textvariable=self.zoom_var, values=["画面に合わせる", "100%", "200%", "300%"], width=14, state="readonly")
        zoom_cb.bind("<<ComboboxSelected>>", self._apply_zoom_selection)
        zoom_cb.pack(side=tk.LEFT, padx=4)

        # -------------------- Status Bar ----------------------------------
        self.status_var = tk.StringVar(value="準備完了")
        status_bar = tk.Label(self, textvariable=self.status_var, relief=tk.SUNKEN, anchor='w', padx=4)
        status_bar.pack(side=tk.TOP, fill=tk.X, padx=4, pady=(0, 4))

        # -------------------- Main Layout Panes ---------------------------
        main_pane = tk.PanedWindow(self, orient=tk.HORIZONTAL, sashrelief=tk.RAISED, bg="#f0f0f0")
        main_pane.pack(fill=tk.BOTH, expand=True, padx=4, pady=4)

        # --- Left Pane (Listbox) ---
        list_frame = tk.Frame(main_pane)
        self.listbox = tk.Listbox(list_frame, width=28, exportselection=False)
        self.listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        yscroll = tk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.listbox.yview)
        yscroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.listbox.config(yscrollcommand=yscroll.set)
        self.listbox.bind("<<ListboxSelect>>", self._on_select_change)
        main_pane.add(list_frame, width=250, stretch="never")

        # --- Right Pane (Previews) ---
        preview_pane = tk.PanedWindow(main_pane, orient=tk.VERTICAL, sashrelief=tk.RAISED)
        main_pane.add(preview_pane, stretch="always")

        # Original Preview
        self.lf_original = tk.LabelFrame(preview_pane, text="オリジナル", padx=5, pady=5)
        self.canvas_org = tk.Canvas(self.lf_original, bg="#ddd")
        self.canvas_org.pack(expand=True, fill=tk.BOTH)
        self.info_orig_var = tk.StringVar(value="--- x ---  ---")
        tk.Label(self.lf_original, textvariable=self.info_orig_var, justify=tk.LEFT).pack(side=tk.BOTTOM, fill=tk.X)
        preview_pane.add(self.lf_original, stretch="always")

        # Resized Preview
        self.lf_resized = tk.LabelFrame(preview_pane, text="変換後プレビュー", padx=5, pady=5)
        self.canvas_resz = tk.Canvas(self.lf_resized, bg="#ddd")
        self.canvas_resz.pack(expand=True, fill=tk.BOTH)
        self.info_resz_var = tk.StringVar(value="--- x ---  ---  (---)")
        tk.Label(self.lf_resized, textvariable=self.info_resz_var, justify=tk.LEFT).pack(side=tk.BOTTOM, fill=tk.X)
        preview_pane.add(self.lf_resized, stretch="always")

        self.bind("<Configure>", self._on_root_resize)
        self._last_canvas_size: Tuple[int, int] = (DEFAULT_PREVIEW, DEFAULT_PREVIEW)

        # Interactions
        self.canvas_org.bind("<Double-Button-1>", lambda _e: self._open_full_preview(False))
        self.canvas_resz.bind("<Double-Button-1>", lambda _e: self._open_full_preview(True))
        # Zoom wheel
        for widget, is_resized in ((self.canvas_org, False), (self.canvas_resz, True)):
            widget.bind("<MouseWheel>", lambda e, r=is_resized: self._on_zoom(e, r))
            widget.bind("<Button-4>", lambda e, r=is_resized: self._on_zoom(e, r, delta=120))
            widget.bind("<Button-5>", lambda e, r=is_resized: self._on_zoom(e, r, delta=-120))
            # drag to pan
            widget.bind("<ButtonPress-1>", lambda e, c=widget: c.scan_mark(e.x, e.y))
            widget.bind("<B1-Motion>",   lambda e, c=widget: c.scan_dragto(e.x, e.y, gain=1))



        # Runtime vars
        self._imgtk_org: Optional[ImageTk.PhotoImage] = None
        self._imgtk_resz: Optional[ImageTk.PhotoImage] = None
        self._full_imgs: list[ImageTk.PhotoImage] = []
        self._zoom_org: Optional[float] = None
        self._zoom_resz: Optional[float] = None

        self.after(0, self._update_mode)  # set initial enable states
        logging.debug('ResizeApp initialized')

    # -------------------- validation helpers ---------------------------
    @staticmethod
    def _validate_int(text: str) -> bool:
        """Return True if text is empty or all digits."""
        return text == "" or text.isdigit()

    def _parse_positive(self, entry: tk.Entry, name: str, low: int, high: int) -> Optional[int]:
        val = entry.get().strip()
        if not val:
            return None
        num = int(val)
        if not (low <= num <= high):
            messagebox.showwarning("入力エラー", f"{name} は {low}-{high} の整数で入力してください")
            entry.focus_set()
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
            pct = self.entry_pct.get().strip() or "---"
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

    # -------------------- mode handling --------------------------------
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
        self.active_mode_frame.pack(side=tk.LEFT)

        # --- Highlight active entries ---
        for w in self._all_entries:
            w.config(bg="white")
        for w in self._entry_widgets[mode]:
            w.config(bg="#E0FFFF")  # LightCyan

        # Set step 2 if not already there
        # set focus to first active entry
        actives = self._entry_widgets.get(mode, [])
        if actives:
            actives[0].focus_set()
        # move to step 2 only if image(s) loaded
        if self.jobs:
            self._set_step(2)

    # -------------------- file selection -------------------------------
    def _select_files(self):
        paths = filedialog.askopenfilenames(title="画像を選択", filetypes=[("画像", "*.png *.jpg *.jpeg *.webp"), ("すべて", "*.*")])
        if not paths:
            return
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
            self._set_step(1)
            self._on_select_change()

    def _populate_listbox(self):
        self.listbox.delete(0, tk.END)
        for job in self.jobs:
            self.listbox.insert(tk.END, job.path.name)
        if self.jobs:
            self.listbox.selection_set(0)

    # -------------------- size calculation -----------------------------
    def _get_target(self, orig: Tuple[int, int]) -> Optional[Tuple[int, int]]:
        mode = self.mode_var.get()
        ow, oh = orig
        if mode == "ratio":
            pct = self._parse_positive(self.entry_pct, "倍率", 1, 1000)
            if pct is None:
                return None
            return int(ow * pct / 100), int(oh * pct / 100)
        if mode == "width":
            w = self._parse_positive(self.entry_w_single, "幅", 1, 10000)
            if w is None:
                return None
            return w, int(oh * w / ow)
        if mode == "height":
            h = self._parse_positive(self.entry_h_single, "高さ", 1, 10000)
            if h is None:
                return None
            return int(ow * h / oh), h
        # fixed
        w = self._parse_positive(self.entry_w_fixed, "幅", 1, 10000)
        h = self._parse_positive(self.entry_h_fixed, "高さ", 1, 10000)
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
        if not self.jobs:
            return
        idx = self.listbox.curselection()
        if idx:
            self.current_index = int(idx[0])
        job = self.jobs[self.current_index]
        try:
            job.resized, fmt = self._process_image(job.image)
        except ValueError:
            return  # validation error already shown
        self._draw_previews(job)
        self._update_info_labels(job.image, job.resized, fmt)
        self.status_var.set("プレビューを更新しました")
        self._set_step(3)

    def _save_current(self):
        if not self.jobs:
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

        # Get filename and save
        now = datetime.now().strftime("%Y%m%d_%H%M%S")
        initial_name = f"{now}_{job.path.name}"
        fname = filedialog.asksaveasfilename(
            title="画像を保存",
            initialfile=initial_name,
            defaultextension="." + fmt.lower(),
            filetypes=[(fmt, "*.*")])
        if not fname:
            return
        self._save_image(job.resized, Path(fname), fmt)
        self.status_var.set(f"「{Path(fname).name}」を保存しました")
        messagebox.showinfo("保存", "保存が完了しました")
        self._set_step(4)

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
        out_dir_name = filedialog.askdirectory(title="出力フォルダーを選択")
        if not out_dir_name:
            return

        out_dir = Path(out_dir_name)
        now = datetime.now().strftime("%Y%m%d_%H%M%S")
        errors = []

        for job in self.jobs:
            try:
                new_img = job.image.copy()
                new_img.thumbnail(target, Resampling.LANCZOS)
                new_name = f"{now}_{job.path.name}"
                out_path = out_dir / new_name
                self._save_image(new_img, out_path, fmt)
            except Exception as e:
                errors.append(f"{job.path.name}: {e}")

        if errors:
            error_details = "\n".join(errors)
            # Consider writing to a log file for long error lists
            messagebox.showwarning("一括保存エラー", f"{len(errors)}件の画像処理に失敗しました:\n\n{error_details[:1000]}")
        else:
            messagebox.showinfo("成功", f"{num_files}個の画像を正常に保存しました。")
        self._set_step(4)

    # -------------------- helpers --------------------------------------
    def _save_image(self, img: Image.Image, path: Path, fmt: str):
        if fmt == "JPEG" and img.mode in ("RGBA", "P"):
            img = img.convert("RGB")
        kwargs = {"quality": 90} if fmt == "JPEG" else {}
        img.save(path, fmt, **kwargs)

    @staticmethod
    def _encoded_size_bytes(img: Image.Image, fmt: str) -> int:
        buff = io.BytesIO()
        params = {"format": fmt, "quality": 90} if fmt == "JPEG" else {"format": fmt}
        tmp = img
        if fmt == "JPEG" and img.mode not in ("RGB", "L", "CMYK"):
            tmp = img.convert("RGB")
        tmp.save(buff, **params)
        return len(buff.getvalue())

    @staticmethod
    def _format_bytes(size_bytes: int) -> str:
        if size_bytes < 1024:
            return f"{size_bytes} B"
        elif size_bytes < 1024**2:
            return f"{size_bytes / 1024:.1f} KB"
        elif size_bytes < 1024**3:
            return f"{size_bytes / 1024**2:.1f} MB"
        else:
            return f"{size_bytes / 1024**3:.1f} GB"

    def _update_info_labels(self, orig_img: Optional[Image.Image], new_img: Optional[Image.Image] = None, new_fmt: Optional[str] = None):
        """Update the info labels below the preview images."""
        if orig_img:
            orig_size_str = f"{orig_img.width}x{orig_img.height}"
            orig_fmt_str = orig_img.format or 'N/A'
            self.info_orig_var.set(f"{orig_size_str}  {orig_fmt_str}")
        else:
            self.info_orig_var.set("--- x ---  ---")

        if new_img and new_fmt:
            try:
                size_str = self._format_bytes(self._encoded_size_bytes(new_img, new_fmt))
                self.info_resz_var.set(f"{new_img.width}x{new_img.height}  {new_fmt}  ({size_str})")
            except Exception:
                self.info_resz_var.set("エラー: 保存形式を確認")
        else:
            self.info_resz_var.set("--- x ---  ---  (---)")

    # -------------------- preview drawing & zoom helpers --------------------
    def _draw_previews(self, job: ImageJob):
        """Redraw both canvases according to current zoom levels."""
        # original image
        self._imgtk_org = self._draw_on_canvas(
            self.canvas_org,
            job.image,
            self._zoom_org,
            f"{int(self._zoom_org * 100)}%" if self._zoom_org is not None else "Fit",
        )

        # resized image (only if preview generated)
        if job.resized is not None:
            self._imgtk_resz = self._draw_on_canvas(
                self.canvas_resz,
                job.resized,
                self._zoom_resz,
                f"{int(self._zoom_resz * 100)}%" if self._zoom_resz is not None else "Fit",
            )
        else:
            # Clear the resized canvas if there's no resized image
            self.canvas_resz.delete("all")
            self._imgtk_resz = None

    def _draw_on_canvas(
        self,
        canvas: tk.Canvas,
        img: Image.Image,
        zoom: Optional[float],
        label: str,
    ) -> Optional[ImageTk.PhotoImage]:
        """Draw `img` scaled by [zoom](cci:1://file:///c:/Users/tn/c_projects/KarukuResize/resize_images_gui_validated.py:563:4-594:58) onto [canvas](cci:1://file:///c:/Users/tn/c_projects/KarukuResize/resize_images_gui_validated.py:499:4-511:20) and overlay zoom label."""
        canvas.delete("all")
        if not img:
            return None

        # If zoom is None, calculate fit-to-screen zoom factor
        if zoom is None:
            canvas_w, canvas_h = canvas.winfo_width(), canvas.winfo_height()
            if img.width > 0 and img.height > 0:
                zoom = min(canvas_w / img.width, canvas_h / img.height)
            else:
                zoom = 1.0  # Fallback for zero-sized images
            label = f"Fit ({int(zoom*100)}%)"

        disp = img.copy()
        new_size = (int(disp.width * zoom), int(disp.height * zoom))
        if new_size[0] <= 0 or new_size[1] <= 0:
            return None # Don't draw if image is invisible

        disp = disp.resize(new_size, Resampling.LANCZOS)
        imgtk = ImageTk.PhotoImage(disp)

        canvas_w = canvas.winfo_width()
        canvas_h = canvas.winfo_height()
        canvas.create_image(canvas_w // 2, canvas_h // 2, image=imgtk, anchor='center')
        canvas.config(scrollregion=(0, 0, disp.width, disp.height))

        # semi-transparent zoom bar (28px) at top
        bar_h = 28
        canvas.create_rectangle(
            0, 0, disp.width, bar_h,
            fill="#000000", stipple="gray25", outline="",
        )
        canvas.create_text(
            10, bar_h // 2, anchor="w", text=label,
            fill="white", font=("Yu Gothic UI", 14, "bold"),
        )
        return imgtk

    # -------------------- zoom & events --------------------------------
    def _reset_zoom(self):
        """Resets the zoom level to 'Fit to Screen' in both state and UI."""
        if hasattr(self, 'zoom_combo') and self.zoom_combo:
            self.zoom_var.set(self.zoom_combo["values"][0]) # Set to "画面に合わせる"
        self._zoom_org = None
        self._zoom_resz = None

    def _apply_zoom_selection(self, _e=None):
        if self.current_index is None:
            return

        zoom_str = self.zoom_var.get()
        if "画面に合わせる" in zoom_str:
            # reset to fit
            self._zoom_org = None
            self._zoom_resz = None
        else:
            try:
                zoom_factor = int(zoom_str.replace("%", "")) / 100.0
                if zoom_factor <= 0:
                    raise ValueError
                self._zoom_org = zoom_factor
                self._zoom_resz = zoom_factor
            except Exception:
                messagebox.showerror("ズームエラー", "ズーム倍率の解析に失敗しました。")
                return

        # redraw both canvases with new zoom factors
        if self.jobs:
            self._draw_previews(self.jobs[self.current_index])

    def _on_zoom(self, event, is_resized: bool):
        if not self.jobs:
            return

        current_zoom = self._zoom_resz if is_resized else self._zoom_org
        if current_zoom is None:
            canvas = self.canvas_resz if is_resized else self.canvas_org
            img = self.jobs[self.current_index].resized if is_resized else self.jobs[self.current_index].image
            if img and img.width > 0 and img.height > 0:
                canvas_w, canvas_h = canvas.winfo_width(), canvas.winfo_height()
                current_zoom = min(canvas_w / img.width, canvas_h / img.height)
            else:
                current_zoom = 1.0

        delta = 0.02 if event.state & 0x0004 else 0.1
        if event.delta < 0 or event.num == 5:
            delta *= -1

        new_zoom = max(0.05, current_zoom + delta)

        if is_resized:
            self._zoom_resz = new_zoom
        else:
            self._zoom_org = new_zoom

        self.zoom_var.set(f"{new_zoom*100:.0f}%")
        self._draw_previews(self.jobs[self.current_index])

    def _on_root_resize(self, _e):
        new_size = (self.canvas_org.winfo_width(), self.canvas_org.winfo_height())
        if new_size != self._last_canvas_size and self.jobs:
            self._last_canvas_size = new_size
            if self._zoom_org is None or self._zoom_resz is None:
                self._draw_previews(self.jobs[self.current_index])

    def _on_select_change(self, _e=None):
        logging.debug('_on_select_change triggered')
        sel = self.listbox.curselection()
        if not sel:
            self.lf_resized.config(text="変換後プレビュー")
            self._update_info_labels(None, None)
            if hasattr(self, '_imgtk_resz'):
                self.canvas_resz.delete("all")
                self._imgtk_resz = None
            return

        idx = sel[0]
        if idx == self.current_index and _e is not None:
            return

        self.current_index = idx
        job = self.jobs[self.current_index]

        now = datetime.now().strftime("%Y%m%d_%H%M%S")
        new_name = f"{now}_{job.path.name}"
        self.lf_resized.config(text=f"変換後: {new_name}")

        job.resized = None
        self._reset_zoom()
        self._draw_previews(job)
        self._update_info_labels(job.image)
        self.status_var.set(f"「{job.path.name}」を選択中")
        self._set_step(2)

    def _open_full_preview(self, is_resized: bool):
        if self.current_index is None:
            return

        job = self.jobs[self.current_index]
        base_img = job.resized if is_resized and job.resized is not None else job.image

        if is_resized and base_img is job.image:
            self._preview_current()
    
    def _create_step_indicator(self):
        """ステップインジケーターを作成（プレースホルダー）"""
        pass
        
    def _set_step(self, step: int):
        """ステップを設定（プレースホルダー）"""
        pass

    def _show_help(self):
        """使い方ヘルプを表示する"""
        help_dialog = HelpDialog(self, HELP_CONTENT)
        help_dialog.show()


# ----------------------------------------------------------------------

def main() -> None:
    """Package entry point (CLI script)."""
    ResizeApp().mainloop()


if __name__ == "__main__":
    main()