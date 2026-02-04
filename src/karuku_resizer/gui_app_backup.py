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
import logging
import platform
import traceback
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Tuple

import customtkinter
import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image, ImageTk, ImageOps
from PIL.Image import Resampling

# ヘルプコンテンツとダイアログをインポート
from karuku_resizer.constants import HELP_CONTENT, STEP_DESCRIPTIONS
from karuku_resizer.help_dialog import HelpDialog

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

logger = logging.getLogger(__name__)

class ResizeApp(customtkinter.CTk):
    def __init__(self) -> None:
        super().__init__()

        # --- Theme --- 
        customtkinter.set_appearance_mode("dark")
        customtkinter.set_default_color_theme("blue")
        self.configure(bg="#2B2B2B")

        # -------------------- フォント設定 --------------------
        self.font_default = customtkinter.CTkFont(family="Yu Gothic UI", size=14, weight="normal")
        self.font_small = customtkinter.CTkFont(family="Yu Gothic UI", size=12, weight="normal")

        self.title("画像リサイズツール (DEBUG)" if DEBUG else "画像リサイズツール")
        # catch Tkinter callback exceptions in debug mode
        if DEBUG:
            self.report_callback_exception = self._report_callback_exception
        # 画面解像度に合わせてウィンドウサイズを調整
        screen_w = self.winfo_screenwidth()
        screen_h = self.winfo_screenheight()

        self.jobs: List[ImageJob] = []
        self.current_index: Optional[int] = None

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

        # Size entry fields
        self.entry_frame = customtkinter.CTkFrame(top, fg_color="transparent")
        self.entry_frame.pack(side="left", padx=10)

        vcmd = (self.register(self._validate_int), "%P")

        # --- Create widgets and frames for each mode ---
        self.pct_var = customtkinter.StringVar(value="100")
        self.w_var = customtkinter.StringVar()
        self.h_var = customtkinter.StringVar()

        vcmd = (self.register(self._validate_int), "%P")

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

        customtkinter.CTkButton(top, text="🔄 プレビュー", width=110, command=self._preview_current).pack(side="left", padx=(0, 10))
        customtkinter.CTkButton(top, text="💾 保存", width=90, command=self._save_current).pack(side="left")
        customtkinter.CTkButton(top, text="📁 一括保存", width=100, command=self._batch_save).pack(side="left", padx=10)

        # Zoom combobox
        self.zoom_var = customtkinter.StringVar(value="画面に合わせる")
        self.zoom_cb = customtkinter.CTkComboBox(top, variable=self.zoom_var, values=["画面に合わせる", "100%", "200%", "300%"], width=140, state="readonly", command=self._apply_zoom_selection, font=self.font_default)
        self.zoom_cb.pack(side="left", padx=4)

        # -------------------- Progress Bar --------------------------------
        self.progress_bar = customtkinter.CTkProgressBar(self, height=20)
        self.progress_bar.set(0)
        # This widget is managed by pack/pack_forget in _batch_save

        # -------------------- Status bar --------------------------------
        self.status_var = customtkinter.StringVar(value="画像を選択してください")
        self.status_label = customtkinter.CTkLabel(self, textvariable=self.status_var, anchor='w', font=self.font_default)
        self.status_label.pack(side="bottom", fill="x", padx=10, pady=5)

        # -------------------- Main Layout using Grid ---------------------------
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(1, weight=1)

        # --- Left Pane (File List) ---
        self.file_list_frame = customtkinter.CTkScrollableFrame(self, label_text="ファイルリスト", label_font=self.font_small, width=250)
        self.file_list_frame.grid(row=1, column=0, padx=(10, 5), pady=10, sticky="nswe")
        self.file_buttons: List[customtkinter.CTkButton] = []

        # --- Right Pane (Previews) ---
        preview_pane = customtkinter.CTkFrame(self, fg_color="transparent")
        preview_pane.grid(row=1, column=1, padx=(5, 10), pady=10, sticky="nswe")
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

        self.bind("<Configure>", self._on_root_resize)
        self._last_canvas_size: Tuple[int, int] = (DEFAULT_PREVIEW, DEFAULT_PREVIEW)

        # Interactions
        self.canvas_org.bind("<MouseWheel>", lambda e: self._on_zoom(e, is_resized=False))
        self.canvas_resz.bind("<MouseWheel>", lambda e: self._on_zoom(e, is_resized=True))
        self.canvas_org.bind("<ButtonPress-1>", lambda e: self.canvas_org.scan_mark(e.x, e.y))
        self.canvas_org.bind("<B1-Motion>",   lambda e: self.canvas_org.scan_dragto(e.x, e.y, gain=1))
        self.canvas_resz.bind("<ButtonPress-1>", lambda e: self.canvas_resz.scan_mark(e.x, e.y))
        self.canvas_resz.bind("<B1-Motion>",   lambda e: self.canvas_resz.scan_dragto(e.x, e.y, gain=1))

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
        self.active_mode_frame.pack(side="left")

        # --- Enable/disable entries based on mode ---
        actives = self._entry_widgets.get(mode, [])
        for entry in self._all_entries:
            if entry in actives:
                entry.configure(state="normal")
            else:
                entry.configure(state="disabled")

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
        for button in self.file_buttons:
            button.destroy()
        self.file_buttons = []
        for job in self.jobs:
            button = customtkinter.CTkButton(self.file_list_frame, text=job.path.name, command=lambda idx=self.jobs.index(job): self._on_select_change(idx))
            button.pack(fill="x", padx=10, pady=5)
            self.file_buttons.append(button)
        if self.jobs:
            self.file_buttons[0].configure(fg_color=customtkinter.ThemeManager.theme["CTkButton"]["hover_color"])

    # -------------------- size calculation -----------------------------
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
        self.status_var.set("ファイルを選択しました")

    def _save_current(self) -> None:
        """Save the currently selected and processed image."""
        if self.current_index is None or not self.jobs:
            messagebox.showwarning("注意", "画像が選択されていません。")
            return

{{ ... }}
        job = self.jobs[self.current_index]
        if not job.resized:
            self._preview_current() # Process if not already done
        if not job.resized:  # Still no resized image after attempting to process
            return

        _, fmt, _ = self._get_settings_summary()
        initial_name = f"{job.path.stem}_resized.{fmt.lower()}"
        save_path_str = filedialog.asksaveasfilename(
            title="名前を付けて保存",
            initialfile=initial_name,
            filetypes=[(f"{fmt} ファイル", f"*.{fmt.lower()}"), ("すべてのファイル", "*.*")]
        )
        if not save_path_str:
            return

        save_path = Path(save_path_str)
        try:
            self._save_image(job.resized, save_path, fmt)
            now = datetime.now().strftime("%Y%m%d_%H%M%S")
            self.status_var.set(f"[{now}] {save_path.name} を保存しました")
            logger.info(f"Saved single image to {save_path}")
            messagebox.showinfo("成功", f"{save_path.name} を保存しました。")
        except Exception as e:
            logger.error(f"Error saving single image: {e}", exc_info=True)
            messagebox.showerror("エラー", f"画像の保存中にエラーが発生しました。\n{e}")

    def _batch_save(self) -> None:
        """Save all processed images to a selected directory."""
        if not self.jobs:
            messagebox.showwarning("注意", "画像がありません。")
            return

        if messagebox.askokcancel("一括保存の確認", f"{len(self.jobs)}個の画像を保存しますか？"):
            out_dir_str = filedialog.askdirectory(title="保存先フォルダを選択")
            if not out_dir_str:
                return
            out_dir = Path(out_dir_str)

            self.progress_bar.pack(pady=10, padx=10, fill="x")
            self.progress_bar.set(0)

            processed_count = 0
            try:
                for i, job in enumerate(self.jobs):
                    self.status_var.set(f"{i + 1}/{len(self.jobs)}: {job.path.name} を処理中...")
                    self.update_idletasks()  # Force UI update

                    processed_result = self._process_image(job.image)
                    if processed_result:
                        resized_img, fmt = processed_result
                        job.resized = resized_img
                        out_path = out_dir / f"{job.path.stem}_resized.{fmt.lower()}"
                        self._save_image(job.resized, out_path, fmt)
                        processed_count += 1
                    else:
                        logger.warning(f"Skipping {job.path.name} due to processing error.")
                    
                    progress = (i + 1) / len(self.jobs)
                    self.progress_bar.set(progress)

            finally:
                self.progress_bar.pack_forget()
                self.status_var.set(f"{processed_count}/{len(self.jobs)} 個の画像を保存しました。")
                messagebox.showinfo("完了", f"{processed_count}個の画像を {out_dir} に保存しました。")

    def _save_image(self, img: Image.Image, path: Path, fmt: str) -> None:
        """Helper to save an image to disk with appropriate settings."""
        if fmt == "JPEG":
            if img.mode in ('RGBA', 'P'):
                img = img.convert('RGB')
            img.save(path, "jpeg", quality=95, optimize=True, progressive=True)
        else:  # PNG or other formats
            img.save(path, fmt)

    def _update_info_labels(
        self, orig_img: Optional[Image.Image], new_img: Optional[Image.Image] = None, new_fmt: Optional[str] = None
    ) -> None:
        """Update the info labels below the preview images."""
        if orig_img:
            orig_size_str = f"{orig_img.width}x{orig_img.height}"
            self.info_orig_var.set(f"元の画像: {orig_size_str}")
        else:
            self.info_orig_var.set("元の画像:")

        if new_img and new_fmt:
            new_size_str = f"{new_img.width}x{new_img.height}"
            try:
                size_bytes = self._encoded_size_bytes(new_img, new_fmt)
                size_str = self._format_bytes(size_bytes)
                self.info_resize_var.set(f"変換後: {new_size_str} ({size_str})")
            except Exception as e:
                logger.error(f"Could not get encoded size: {e}")
                self.info_resize_var.set(f"変換後: {new_size_str} (サイズ不明)")
        else:
            self.info_resize_var.set("変換後:")

    def _encoded_size_bytes(self, img: Image.Image, fmt: str) -> int:
        """Return size of image in bytes after encoding to `fmt`."""
        with io.BytesIO() as f:
            save_fmt = "jpeg" if fmt == "JPEG" else fmt
            save_img = img
            if fmt == "JPEG" and img.mode in ('RGBA', 'P'):
                save_img = img.convert('RGB')
            save_img.save(f, save_fmt)
            return f.tell()

    def _format_bytes(self, size_bytes: int) -> str:
        if size_bytes < 1024:
            return f"{size_bytes} B"
        elif size_bytes < 1024**2:
            return f"{size_bytes/1024:.1f} KB"
        else:
            return f"{size_bytes/1024**2:.1f} MB"

    def _draw_previews(self, job: ImageJob) -> None:
        """Redraw both canvases according to current zoom levels."""
        self._draw_on_canvas(self.canvas_org, job.image, self._zoom_org, "元の画像")

        if job.resized:
            self._draw_on_canvas(self.canvas_resz, job.resized, self._zoom_resz, "変換後")
        else:
            self.canvas_resz.delete("all")
            self.canvas_resz.create_text(
                self.canvas_resz.winfo_width() / 2,
                self.canvas_resz.winfo_height() / 2,
                text="プレビューなし",
                fill=UI_COLORS["text_inactive"],
                font=self.font_default,
            )

    def _draw_on_canvas(
        self,
        canvas: customtkinter.CTkCanvas,
        img: Image.Image,
        zoom: Optional[float],
        label: str,
    ) -> None:
        """Draw `img` scaled by zoom onto canvas and overlay zoom label."""
        canvas.delete("all")
        canvas_w, canvas_h = canvas.winfo_width(), canvas.winfo_height()

        if zoom is None:
            zoom = self._get_fit_zoom_ratio(canvas, img)

        disp_w, disp_h = int(img.width * zoom), int(img.height * zoom)

        if disp_w > 0 and disp_h > 0:
            resample_filter = Resampling.LANCZOS if zoom < 1.0 else Resampling.BICUBIC
            disp_img = img.resize((disp_w, disp_h), resample_filter)
            photo_img = ImageTk.PhotoImage(disp_img)
            
            x_pos = (canvas_w - disp_w) / 2
            y_pos = (canvas_h - disp_h) / 2
            canvas.create_image(x_pos, y_pos, anchor="nw", image=photo_img)
            canvas.image = photo_img  # type: ignore

        zoom_pct = int(zoom * 100)
        full_label = f"{label} ({zoom_pct}%)"
        canvas.create_text(10, 10, text=full_label, anchor="nw", fill="white", font=self.font_small)

    def _reset_zoom(self):
        """Reset zoom levels to fit-to-screen."""
        self._zoom_org = None
        self._zoom_resz = None
        self.zoom_var.set("フィット")
        if self.current_index is not None:
            self._draw_previews(self.jobs[self.current_index])

    def _apply_zoom_selection(self, choice: str):
        """Applies the zoom level selected in the combobox."""
        if self.current_index is None:
            return

        if "フィット" in choice:
            self._reset_zoom()
            return
        try:
            zoom_factor = int(choice.replace("%", "")) / 100.0
            if zoom_factor <= 0:
                raise ValueError
            self._zoom_org = zoom_factor
            self._zoom_resz = zoom_factor
        except (ValueError, TypeError):
            messagebox.showerror("ズームエラー", "無効なズーム倍率です。")
            self.zoom_var.set("フィット") # Reset on error
            self._reset_zoom()
            return
        
        self._draw_previews(self.jobs[self.current_index])

    def _get_fit_zoom_ratio(self, canvas: customtkinter.CTkCanvas, img: Optional[Image.Image]) -> float:
        """Calculate the zoom ratio to fit the image within the canvas."""
        if not img or img.width == 0 or img.height == 0:
            return 1.0
        
        canvas_w, canvas_h = canvas.winfo_width(), canvas.winfo_height()
        if canvas_w <= 1 or canvas_h <= 1: # Canvas not yet realized
            return 1.0
            
        return min(canvas_w / img.width, canvas_h / img.height)

    def _on_zoom(self, event, is_resized: bool):
        if self.current_index is None:
            return
        current_zoom = self._zoom_resz if is_resized else self._zoom_org

        job = self.jobs[self.current_index]
        img = job.resized if is_resized and job.resized else job.image

        if current_zoom is None:
            canvas = self.canvas_resz if is_resized else self.canvas_org
            current_zoom = self._get_fit_zoom_ratio(canvas, img)

        # Determine the scroll direction
        y_scroll_amount = event.delta
        if platform.system() == "Darwin":  # macOS
            y_scroll_amount *= -1

        if y_scroll_amount > 0:
            new_zoom = current_zoom * ZOOM_STEP
        else:
            new_zoom = current_zoom / ZOOM_STEP

        new_zoom = max(MIN_ZOOM, min(new_zoom, MAX_ZOOM))

        if is_resized:
            self._zoom_resz = new_zoom
        else:
            self._zoom_org = new_zoom
        self.zoom_var.set(f"{new_zoom*100:.0f}%")
        self._draw_previews(self.jobs[self.current_index])

    def _on_root_resize(self, _e):
        # Redraw previews on resize only if zoom is set to 'fit'
        if self.current_index is not None and (self._zoom_org is None or self._zoom_resz is None):
             self._draw_previews(self.jobs[self.current_index])

    def _on_select_change(self, idx: Optional[int] = None) -> None:
        """Handle file selection change."""
        if idx is None:
            idx = 0
        if self.current_index == idx or not (0 <= idx < len(self.jobs)):
            return

        # Update button highlights
        if self.current_index is not None:
            self.file_buttons[self.current_index].configure(fg_color=customtkinter.ThemeManager.theme["CTkButton"]["fg_color"])
        
        self.current_index = idx
        self.file_buttons[idx].configure(fg_color=UI_COLORS['active'])

        # Update previews and info
        job = self.jobs[idx]
        now = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.status_var.set(f"[{now}] {job.path.name} を選択しました")
        logger.info(f"Selected: {job.path.name}")

        self._reset_zoom()
        self._preview_current()

    def _show_help(self):
        """Display the help dialog."""
        help_dialog = HelpDialog(self, help_content=HELP_CONTENT)
        self.wait_window(help_dialog)


# ----------------------------------------------------------------------

def main() -> None:
    """Package entry point (CLI script)."""
    ResizeApp().mainloop()


if __name__ == "__main__":
    main()