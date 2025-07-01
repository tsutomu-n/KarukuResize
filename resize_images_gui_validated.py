"""Validated simple image resizer GUI.

This version streamlines the UI so the user only chooses **how to specify size**
(ratio%, width, height, or explicit both).  All algorithm/format decisions are
handled automatically for best quality.

Usage:
    uv run python resize_images_gui_validated.py
"""
from __future__ import annotations

import io
import tkinter as tk
from dataclasses import dataclass
from pathlib import Path
from tkinter import filedialog, messagebox, ttk
from typing import List, Optional, Tuple

from PIL import Image, ImageTk
import tkinter.font as tkfont

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


class ResizeApp(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        # -------------------- フォント設定 --------------------
        jp_font = ("Yu Gothic UI", 16)
        default_font = tkfont.nametofont("TkDefaultFont")
        default_font.config(family=jp_font[0], size=jp_font[1])
        self.option_add("*Font", jp_font)

        self.title("画像リサイズツール")
        # 画面解像度に合わせて十分なサイズで起動
        screen_w = self.winfo_screenwidth()
        screen_h = self.winfo_screenheight()
        if screen_w >= 1600 and screen_h >= 900:
            # フルHD級なら中央寄せ 1400x850
            self.geometry("1400x850")
        else:
            # 小さい解像度でも要素が収まる最小サイズ
            self.geometry("1200x750")

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

        # Entry fields
        vcmd = (self.register(self._validate_int), "%P")
        self.pct_var = tk.StringVar()
        self.entry_pct = tk.Entry(top, textvariable=self.pct_var, width=5, validate="key", validatecommand=vcmd)
        self.entry_pct.pack(side=tk.LEFT)
        tk.Label(top, text="%  ").pack(side=tk.LEFT)

        self.w_var = tk.StringVar()
        self.entry_w = tk.Entry(top, textvariable=self.w_var, width=6, validate="key", validatecommand=vcmd)
        self.entry_w.pack(side=tk.LEFT)
        tk.Label(top, text="×").pack(side=tk.LEFT)
        self.h_var = tk.StringVar()
        self.entry_h = tk.Entry(top, textvariable=self.h_var, width=6, validate="key", validatecommand=vcmd)
        self.entry_h.pack(side=tk.LEFT)

        # maintain entry collections for highlight
        self._all_entries = [self.entry_pct, self.entry_w, self.entry_h]
        self._entry_widgets = {
            "ratio": [self.entry_pct],
            "width": [self.entry_w],
            "height": [self.entry_h],
            "fixed": [self.entry_w, self.entry_h],
        }

        tk.Button(top, text="🔄 プレビュー", command=self._preview_current).pack(side=tk.LEFT, padx=4)
        tk.Button(top, text="💾 保存", command=self._save_current).pack(side=tk.LEFT)
        tk.Button(top, text="📁 一括保存", command=self._batch_save).pack(side=tk.LEFT)

        # -------------------- Size info label ---------------------------
        self.info_var = tk.StringVar()
        tk.Label(self, textvariable=self.info_var, font=("Helvetica", 11, "bold"), fg="#2563EB").pack(side=tk.TOP, fill=tk.X, pady=(0, 2))

        # Zoom combobox
        self.zoom_var = tk.StringVar(value="画面に合わせる")
        zoom_cb = ttk.Combobox(top, textvariable=self.zoom_var, values=["画面に合わせる", "100%", "200%", "300%"], width=14, state="readonly")
        zoom_cb.bind("<<ComboboxSelected>>", self._apply_zoom_selection)
        zoom_cb.pack(side=tk.LEFT, padx=4)

        # -------------------- Listbox -----------------------------------
        list_frame = tk.Frame(self)
        list_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(4, 0))
        self.listbox = tk.Listbox(list_frame, width=28, height=28, exportselection=False)
        self.listbox.pack(side=tk.LEFT, fill=tk.Y)
        yscroll = tk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.listbox.yview)
        yscroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.listbox.config(yscrollcommand=yscroll.set)
        self.listbox.bind("<<ListboxSelect>>", self._on_select_change)

        # -------------------- Preview canvases --------------------------
        self.canvas_org = tk.Canvas(self, bg="#ddd", width=DEFAULT_PREVIEW, height=DEFAULT_PREVIEW)
        self.canvas_org.pack(side=tk.LEFT, expand=True, fill=tk.BOTH, padx=4, pady=4)
        self.canvas_resz = tk.Canvas(self, bg="#ddd", width=DEFAULT_PREVIEW, height=DEFAULT_PREVIEW)
        self.canvas_resz.pack(side=tk.LEFT, expand=True, fill=tk.BOTH, padx=4, pady=4)

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

        # Status bar
        self.status_var = tk.StringVar()
        status = tk.Label(self, textvariable=self.status_var, relief=tk.SUNKEN, anchor="w")
        status.pack(side=tk.BOTTOM, fill=tk.X)

        # Runtime vars
        self._imgtk_org: Optional[ImageTk.PhotoImage] = None
        self._imgtk_resz: Optional[ImageTk.PhotoImage] = None
        self._full_imgs: list[ImageTk.PhotoImage] = []
        self._zoom_org = 1.0
        self._zoom_resz = 1.0

        self.after(0, self._update_mode)  # set initial enable states

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

    # -------------------- mode handling --------------------------------
    def _update_mode(self):
        mode = self.mode_var.get()
        # first disable all
        for e in self._all_entries:
            e.config(state="disabled", bg=UI_COLORS["inactive"],
                     disabledbackground=UI_COLORS["inactive"],
                     disabledforeground=UI_COLORS["text_inactive"],
                     highlightthickness=0)
        # enable & highlight active
        for e in self._entry_widgets.get(mode, []):
            e.config(state="normal", bg="white", fg="black", insertbackground="black",
                     highlightbackground=UI_COLORS["primary"], highlightcolor=UI_COLORS["primary"], highlightthickness=2)
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
            self._preview_current()

    def _populate_listbox(self):
        self.listbox.delete(0, tk.END)
        for job in self.jobs:
            self.listbox.insert(tk.END, job.path.name)
        if self.jobs:
            self.listbox.selection_set(0)
            self.current_index = 0

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
            w = self._parse_positive(self.entry_w, "幅", 1, 10000)
            if w is None:
                return None
            return w, int(oh * w / ow)
        if mode == "height":
            h = self._parse_positive(self.entry_h, "高さ", 1, 10000)
            if h is None:
                return None
            return int(ow * h / oh), h
        # fixed
        w = self._parse_positive(self.entry_w, "幅", 1, 10000)
        h = self._parse_positive(self.entry_h, "高さ", 1, 10000)
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
        self._update_status(job.resized, fmt)
        self._update_info(job, job.resized, fmt)
        self._set_step(3)

    def _save_current(self):
        if not self.jobs:
            return
        job = self.jobs[self.current_index]
        if job.resized is None:
            try:
                job.resized, fmt = self._process_image(job.image)
            except ValueError:
                return
        else:
            fmt = "PNG" if "A" in job.resized.getbands() else "JPEG"
        fname = filedialog.asksaveasfilename(title="画像を保存", defaultextension="." + fmt.lower(), filetypes=[(fmt, "*.*")])
        if not fname:
            return
        self._save_image(job.resized, Path(fname), fmt)
        messagebox.showinfo("保存", "保存が完了しました")
        self._set_step(4)

    def _batch_save(self):
        if not self.jobs:
            return
        out_dir_name = filedialog.askdirectory(title="出力フォルダーを選択")
        if not out_dir_name:
            return
        out_dir = Path(out_dir_name)
        for i, job in enumerate(self.jobs):
            img, fmt = self._process_image(job.image)
            job.resized = img
            out_path = out_dir / f"{job.path.stem}_resized_{i+1}.{fmt.lower()}"
            self._save_image(img, out_path, fmt)
        messagebox.showinfo("一括保存", "すべての画像を保存しました")
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

    def _update_status(self, img: Image.Image, fmt: str):
        size_kb = self._encoded_size_bytes(img, fmt) // 1024
        self.status_var.set(f"{img.width}×{img.height}  / {fmt} / {size_kb} KB")

    # prominent label
    def _update_info(self, job: ImageJob, new_img: Image.Image, new_fmt: str):
        try:
            orig_bytes = job.path.stat().st_size
        except OSError:
            orig_bytes = 0
        orig_kb = orig_bytes // 1024 if orig_bytes else 0
        orig_fmt = (job.image.format or job.path.suffix.lstrip('.').upper() or 'N/A')
        new_bytes = self._encoded_size_bytes(new_img, new_fmt)
        new_kb = new_bytes // 1024
        ratio = (new_bytes / orig_bytes * 100) if orig_bytes else 0
        self.info_var.set(
            f"オリジナル: {job.image.width}×{job.image.height} {orig_fmt} {orig_kb}KB   →   "
            f"変換: {new_img.width}×{new_img.height} {new_fmt} {new_kb}KB  ({ratio:.0f}%)"
        )

    # -------------------- preview drawing & zoom helpers --------------------
    def _draw_previews(self, job: ImageJob):
        """Redraw both canvases according to current zoom levels."""
        # original image
        zoom_pct_org = int(self._zoom_org * 100)
        self._imgtk_org = self._draw_on_canvas(
            self.canvas_org,
            job.image,
            self._zoom_org,
            f"{zoom_pct_org}%",
        )

        # resized image (only if preview generated)
        if job.resized is not None:
            zoom_pct_resz = int(self._zoom_resz * 100)
            self._imgtk_resz = self._draw_on_canvas(
                self.canvas_resz,
                job.resized,
                self._zoom_resz,
                f"{zoom_pct_resz}%",
            )
        else:
            self._imgtk_resz = None

    def _draw_on_canvas(
        self,
        canvas: tk.Canvas,
        img: Image.Image,
        zoom: float,
        label: str,
    ) -> ImageTk.PhotoImage:
        """Draw `img` scaled by `zoom` onto `canvas` and overlay zoom label."""
        disp = img.copy()
        disp = disp.resize(
            (int(disp.width * zoom), int(disp.height * zoom)), Resampling.LANCZOS
        )
        imgtk = ImageTk.PhotoImage(disp)

        # clear and place image
        canvas.delete("all")
        canvas.create_image(0, 0, anchor="nw", image=imgtk)
        canvas.config(scrollregion=(0, 0, disp.width, disp.height))

        # semi-transparent zoom bar (28px) at top
        bar_h = 28
        canvas.create_rectangle(
            0,
            0,
            disp.width,
            bar_h,
            fill="#000000",
            stipple="gray25",
            outline="",
        )
        canvas.create_text(
            10,
            bar_h // 2,
            anchor="w",
            text=label,
            fill="white",
            font=("Yu Gothic UI", 14, "bold"),
        )
        return imgtk

    # -------------------- zoom & events --------------------------------
    def _draw_previews(self, job: ImageJob):
        """Redraw both canvases according to current zoom levels"""
        # original image
        zoom_pct_org = int(self._zoom_org * 100)
        self._imgtk_org = self._draw_on_canvas(
            self.canvas_org, job.image, self._zoom_org, f"{zoom_pct_org}%"
        )

        # resized image (may be None before preview)
        if job.resized is not None:
            zoom_pct_resz = int(self._zoom_resz * 100)
            self._imgtk_resz = self._draw_on_canvas(
                self.canvas_resz, job.resized, self._zoom_resz, f"{zoom_pct_resz}%"
            )
        else:
            self._imgtk_resz = None
 = int(self._zoom_org * 100)
            self._imgtk_org = self._draw_on_canvas(self.canvas_org, job.image, self._zoom_org, f"{zoom_pct_org}%")
 = int(self._zoom_resz * 100)
        self._imgtk_resz = self._draw_on_canvas(self.canvas_resz, job.resized, self._zoom_resz, f"{zoom_pct_resz}%")


    def _draw_on_canvas(self, canvas: tk.Canvas, img: Image.Image, zoom: float, label: str) -> ImageTk.PhotoImage:
        disp = img.copy()
        disp = disp.resize((int(disp.width * zoom), int(disp.height * zoom)), Resampling.LANCZOS)
        imgtk = ImageTk.PhotoImage(disp)
        canvas.delete("all")
    # place at top-left so scrollregion works
        canvas.create_image(0, 0, anchor="nw", image=imgtk)
        canvas.config(scrollregion=(0, 0, disp.width, disp.height))
    # semi-transparent black bar (stipple) + white zoom text
        bar_h = 28
        canvas.create_rectangle(0, 0, disp.width, bar_h, fill="#000", stipple="gray25", outline="")
        canvas.create_text(10, bar_h//2, anchor="w", text=label, fill="white", font=("Yu Gothic UI", 14, "bold"))
        return imgtk

    # -------------------- zoom & events --------------------------------
    def _apply_zoom_selection(self, _e=None):
        sel = self.zoom_var.get()
        if sel == "画面に合わせる":
            self._zoom_org = self._zoom_resz = 1.0
        else:
            if sel.endswith("%"):
                factor = float(sel.rstrip("%")) / 100.0
            else:
                factor = float(sel.replace("x", ""))
            self._zoom_org = self._zoom_resz = factor

        if self.jobs:
            self._draw_previews(self.jobs[self.current_index])

    def _on_zoom(self, event, is_resized: bool, *, delta: int | None = None):
        d = event.delta if delta is None else delta
        step = ZOOM_STEP if d > 0 else 1 / ZOOM_STEP
        if is_resized:
            self._zoom_resz = min(max(self._zoom_resz * step, MIN_ZOOM), MAX_ZOOM)
        else:
            self._zoom_org = min(max(self._zoom_org * step, MIN_ZOOM), MAX_ZOOM)
        if self.jobs:
            self._draw_previews(self.jobs[self.current_index])

    def _on_root_resize(self, _e):
        new_size = (self.canvas_org.winfo_width(), self.canvas_org.winfo_height())
        if new_size != self._last_canvas_size and self.jobs:
            self._last_canvas_size = new_size
            self._draw_previews(self.jobs[self.current_index])

    def _on_select_change(self, _e):
        if not self.listbox.curselection():
            return
        idx = int(self.listbox.curselection()[0])
        if idx != self.current_index:
            self.current_index = idx
            self._preview_current()

    def _open_full_preview(self, is_resized: bool):
        """Open a scrollable preview window that can show images larger than the screen."""
        if not self.jobs:
            return
        job = self.jobs[self.current_index]
        img = job.resized if is_resized and job.resized else job.image

        # Build window with scrollbars
        win = tk.Toplevel(self)
        win.title("Resized Preview" if is_resized else "Original Preview")

        canvas = tk.Canvas(win, bg="black")
        hbar = tk.Scrollbar(win, orient="horizontal", command=canvas.xview)
        vbar = tk.Scrollbar(win, orient="vertical",   command=canvas.yview)
        canvas.configure(xscrollcommand=hbar.set, yscrollcommand=vbar.set)

        # Layout: canvas fills, scrollbars bottom/right
        canvas.grid(row=0, column=0, sticky="nsew")
        vbar.grid(row=0, column=1, sticky="ns")
        hbar.grid(row=1, column=0, sticky="ew")
        win.rowconfigure(0, weight=1)
        win.columnconfigure(0, weight=1)

        # Put image at (0,0) anchor nw, allow scrolling
        imgtk = ImageTk.PhotoImage(img)
        self._full_imgs.append(imgtk)
        canvas.create_image(0, 0, anchor="nw", image=imgtk)
        canvas.config(scrollregion=(0, 0, img.width, img.height))

        # Optional: click-drag to pan faster
        canvas.bind("<ButtonPress-1>", lambda e: canvas.scan_mark(e.x, e.y))
        canvas.bind("<B1-Motion>",   lambda e: canvas.scan_dragto(e.x, e.y, gain=1))


    # -------------------- step indicator helpers ------------------

    def _create_step_indicator(self):
        frame = tk.Frame(self, bg="#f8f9fa")
        frame.pack(side=tk.TOP, fill="x", pady=(4, 0))
        steps = ["画像を選ぶ", "サイズを決める", "確認する", "保存する"]
        for i, text in enumerate(steps, 1):
            cont = tk.Frame(frame, bg="white", relief="solid", borderwidth=1)
            cont.pack(side="left", expand=True, fill="x", padx=6, pady=4)
            num = tk.Label(cont, text=str(i), font=("Arial", 11, "bold"), bg="white", width=2)
            num.pack(side="left", padx=(6, 4), pady=4)
            lbl = tk.Label(cont, text=text, font=("Arial", 10), bg="white")
            lbl.pack(side="left", padx=(0, 6), pady=4)
            self._step_labels.append({"container": cont, "num": num, "text": lbl})
        self._set_step(0)

    def _set_step(self, done: int):
        """Update indicator. `done` = number of steps already完了 (0-4)."""
        for idx, s in enumerate(self._step_labels, 1):
            cont, num, lbl = s["container"], s["num"], s["text"]
            if idx <= done:  # completed
                cont.config(bg=UI_COLORS["primary"], relief="raised")
                num.config(bg=UI_COLORS["primary"], fg="white")
                lbl.config(bg=UI_COLORS["primary"], fg="white")
            elif idx == done + 1:  # current task
                cont.config(bg=UI_COLORS["active"], relief="solid")
                num.config(bg=UI_COLORS["active"], fg=UI_COLORS["primary"])
                lbl.config(bg=UI_COLORS["active"], fg=UI_COLORS["primary"])
            else:  # not reached
                cont.config(bg=UI_COLORS["inactive"], relief="solid")
                num.config(bg=UI_COLORS["inactive"], fg=UI_COLORS["text_inactive"])
                lbl.config(bg=UI_COLORS["inactive"], fg=UI_COLORS["text_inactive"])

# ----------------------------------------------------------------------
if __name__ == "__main__":
    ResizeApp().mainloop()
