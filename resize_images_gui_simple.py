"""Simple Tkinter-based Image Resizer GUI for KarukuResize.

This standalone lightweight GUI intentionally avoids the customtkinter-based
large application.  It demonstrates basic resize / batch features while keeping
code compact and easy to extend.

Usage (local):
    python resize_images_gui_simple.py

Requirements:
    - Python 3.12+
    - Pillow (already listed in pyproject.toml).  Install via:
        uv add pillow   # if not yet present

The file does *not* import the big KarukuResize modules; it works independently
so it is safe to place alongside the existing codebase.
"""
from __future__ import annotations

import itertools
import tkinter as tk
from dataclasses import dataclass
from pathlib import Path
from tkinter import filedialog, messagebox, ttk
from typing import List, Optional

from PIL import Image, ImageTk

# Pillow >=10 moves resampling constants under Image.Resampling
try:
    from PIL.Image import Resampling
except ImportError:  # Pillow<10 fallback
    class _Resampling:  # type: ignore
        NEAREST = Image.NEAREST  # type: ignore
        BILINEAR = Image.BILINEAR  # type: ignore
        BICUBIC = Image.BICUBIC  # type: ignore
        LANCZOS = Image.LANCZOS  # type: ignore

    Resampling = _Resampling()  # type: ignore

ALG_MAP = {
    "NEAREST": Resampling.NEAREST,
    "BILINEAR": Resampling.BILINEAR,
    "BICUBIC": Resampling.BICUBIC,
    "LANCZOS": Resampling.LANCZOS,
}

DEFAULT_PREVIEW = 480  # initial size
ZOOM_STEP = 1.1
MIN_ZOOM = 0.2
MAX_ZOOM = 5.0


@dataclass
class ImageJob:
    """Holds information about a single source image and its resized version."""

    path: Path
    image: Image.Image  # original (full resolution)
    resized: Optional[Image.Image] = None  # last preview / saved result


class ResizeApp(tk.Tk):
    """Very lightweight image resizer GUI."""

    def __init__(self) -> None:
        super().__init__()
        self.title("Simple Image Resizer")
        self.geometry("980x540")
        self.minsize(900, 540)

        self.jobs: List[ImageJob] = []
        self.current_index: int | None = None  # no image selected yet

        # ------------------------ UI -----------------------------------
        top_bar = tk.Frame(self)
        top_bar.pack(side=tk.TOP, fill=tk.X, padx=4, pady=4)

        tk.Button(top_bar, text="📂 Select Images", command=self.select_files).pack(
            side=tk.LEFT
        )

        # Width / Height / Scale inputs
        self.width_var = tk.StringVar()
        self.height_var = tk.StringVar()
        self.scale_var = tk.StringVar()

        tk.Label(top_bar, text="W").pack(side=tk.LEFT)
        self._entry_w = tk.Entry(top_bar, textvariable=self.width_var, width=6)
        self._entry_w.pack(side=tk.LEFT)
        tk.Label(top_bar, text="H").pack(side=tk.LEFT)
        self._entry_h = tk.Entry(top_bar, textvariable=self.height_var, width=6)
        self._entry_h.pack(side=tk.LEFT)
        tk.Label(top_bar, text="% ").pack(side=tk.LEFT)
        self._entry_s = tk.Entry(top_bar, textvariable=self.scale_var, width=5)
        self._entry_s.pack(side=tk.LEFT)

        # --- Easy mode toggle ---
        self.easy_mode_var = tk.BooleanVar(value=True)
        tk.Checkbutton(top_bar, text="Easy", variable=self.easy_mode_var, command=self._update_mode).pack(side=tk.LEFT, padx=6)
        # Resolution choice (only in easy mode)
        self.easy_res_var = tk.StringVar(value="1080p")
        self.res_cb = ttk.Combobox(top_bar, textvariable=self.easy_res_var, values=["1080p", "1440p"], width=6, state="readonly")
        self.res_cb.pack(side=tk.LEFT)

        # Resampling algorithm selector
        self.alg_var = tk.StringVar(value="BICUBIC")
        ttk.Combobox(
            top_bar,
            textvariable=self.alg_var,
            values=list(ALG_MAP.keys()),
            width=10,
            state="readonly",
        ).pack(side=tk.LEFT, padx=4)

        # Output format selector
        self.fmt_var = tk.StringVar(value="JPEG")
        ttk.Combobox(
            top_bar,
            textvariable=self.fmt_var,
            values=["JPEG", "PNG", "WEBP"],
            width=7,
            state="readonly",
        ).pack(side=tk.LEFT)

        # Control buttons
        tk.Button(top_bar, text="🔎 Preview", command=self.preview_current).pack(
            side=tk.LEFT, padx=5
        )
        tk.Button(top_bar, text="💾 Save Current", command=self.save_current).pack(
            side=tk.LEFT
        )
        tk.Button(top_bar, text="📁 Batch Save", command=self.batch_save).pack(
            side=tk.LEFT
        )

        # Zoom selection combobox
        self.zoom_var = tk.StringVar(value="Fit")
        zoom_cb = ttk.Combobox(
            top_bar,
            textvariable=self.zoom_var,
            values=["Fit", "1x", "2x", "3x"],
            width=4,
            state="readonly",
        )
        zoom_cb.pack(side=tk.LEFT, padx=4)
        zoom_cb.bind("<<ComboboxSelected>>", self._apply_zoom_selection)

        # call mode update once
        self.after(0, self._update_mode)

        # Left listbox for loaded images
        list_frame = tk.Frame(self)
        list_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(4,0))
        self.listbox = tk.Listbox(list_frame, width=28, height=25, exportselection=False)
        self.listbox.pack(side=tk.LEFT, fill=tk.Y)
        yscroll = tk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.listbox.yview)
        yscroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.listbox.config(yscrollcommand=yscroll.set)
        self.listbox.bind("<<ListboxSelect>>", self._on_select_change)

        # Canvas previews (original left, resized right)
        self.canvas_org = tk.Canvas(self, bg="#ddd", width=DEFAULT_PREVIEW, height=DEFAULT_PREVIEW)
        self.canvas_org.pack(side=tk.LEFT, expand=True, padx=4, pady=4, fill=tk.BOTH)
        self.canvas_resz = tk.Canvas(self, bg="#ddd", width=DEFAULT_PREVIEW, height=DEFAULT_PREVIEW)
        self.canvas_resz.pack(side=tk.LEFT, expand=True, padx=4, pady=4, fill=tk.BOTH)

        # Track window resize to redraw
        self.bind("<Configure>", self._on_root_resize)
        self._last_canvas_size: tuple[int,int] = (DEFAULT_PREVIEW, DEFAULT_PREVIEW)

        # --- Interaction bindings ---
        self.canvas_org.bind("<Double-Button-1>", lambda _e: self._open_full_preview(False))
        self.canvas_resz.bind("<Double-Button-1>", lambda _e: self._open_full_preview(True))
        # Wheel (Windows/macOS)
        self.canvas_org.bind("<MouseWheel>", lambda e: self._on_zoom(e, False))
        self.canvas_resz.bind("<MouseWheel>", lambda e: self._on_zoom(e, True))
        # Wheel (Linux X11)
        self.canvas_org.bind("<Button-4>", lambda e: self._on_zoom(e, False, delta=120))
        self.canvas_org.bind("<Button-5>", lambda e: self._on_zoom(e, False, delta=-120))
        self.canvas_resz.bind("<Button-4>", lambda e: self._on_zoom(e, True, delta=120))
        self.canvas_resz.bind("<Button-5>", lambda e: self._on_zoom(e, True, delta=-120))

        # Keep references to PhotoImage objects (prevent GC)
        self._imgtk_org: Optional[ImageTk.PhotoImage] = None
        self._imgtk_resz: Optional[ImageTk.PhotoImage] = None
        # Store PhotoImage for full previews so windows stay alive
        self._full_imgs: list[ImageTk.PhotoImage] = []
        # Zoom factors
        self._zoom_org = 1.0
        self._zoom_resz = 1.0

    # ---------------------- helpers ------------------------------------
    def _update_mode(self):
        """Enable/disable manual size widgets when Easy mode toggles."""
        easy = self.easy_mode_var.get()
        state_entries = "disabled" if easy else "normal"
        for ent in (self._entry_w, self._entry_h, self._entry_s):
            ent.configure(state=state_entries)
        # resolution combobox only active in easy mode
        self.res_cb.configure(state="readonly" if easy else "disabled")
        # no need to redraw here

    def _populate_listbox(self):
        self.listbox.delete(0, tk.END)
        for job in self.jobs:
            self.listbox.insert(tk.END, job.path.name)
        if self.jobs:
            self.listbox.selection_set(0)
            self.current_index = 0

    def _on_select_change(self, _e):
        if not self.listbox.curselection():
            return
        idx = int(self.listbox.curselection()[0])
        if idx != self.current_index:
            self.current_index = idx
            self.preview_job(self.jobs[idx])

    def select_files(self) -> None:
        paths = filedialog.askopenfilenames(
            title="Select images",
            filetypes=[("Images", "*.png *.jpg *.jpeg *.webp"), ("All", "*.*")],
        )
        if not paths:
            return
        # Clear previous and load images
        self.jobs = []
        for p in paths:
            try:
                img = Image.open(p)
            except Exception as e:  # pragma: no cover
                messagebox.showerror("Error", f"Failed to load {p}: {e}")
                continue
            self.jobs.append(ImageJob(Path(p), img))

        self._populate_listbox()
        if self.jobs:
            self.preview_job(self.jobs[0])

    # ------------------------------------------------------------------
    def _draw_on_canvas(self, canvas: tk.Canvas, img: Image.Image, zoom: float, label: str) -> ImageTk.PhotoImage:
        cw = max(canvas.winfo_width(), 1)
        ch = max(canvas.winfo_height(), 1)
        disp = img.copy()
        w, h = disp.size
        disp = disp.resize((int(w * zoom), int(h * zoom)), Resampling.LANCZOS)
        # Limit to canvas size
        disp.thumbnail((cw, ch))
        imgtk = ImageTk.PhotoImage(disp)
        canvas.delete("all")
        canvas.create_image(cw // 2, ch // 2, image=imgtk)
        canvas.create_text(10, 10, anchor="nw", text=label, fill="black")
        return imgtk

    def preview_job(self, job: ImageJob) -> None:
        """Render original and (if any) resized preview for a single ImageJob."""

        # Original
        self._imgtk_org = self._draw_on_canvas(
            self.canvas_org,
            job.image,
            self._zoom_org,
            f"Original\n{job.image.size[0]}×{job.image.size[1]}  zoom×{self._zoom_org:.2f}",
        )

        # Resized or placeholder
        if job.resized:
            self._imgtk_resz = self._draw_on_canvas(
                self.canvas_resz,
                job.resized,
                self._zoom_resz,
                f"Resized\n{job.resized.size[0]}×{job.resized.size[1]}  zoom×{self._zoom_resz:.2f}",
            )
            self.canvas_resz.create_text(
                10,
                10,
                anchor="nw",
                text=f"Resized\n{job.resized.size[0]}×{job.resized.size[1]}",
                fill="black",
            )
        else:
            self.canvas_resz.create_text(
                self.canvas_resz.winfo_width() // 2 or 1,
                self.canvas_resz.winfo_height() // 2 or 1,
            text="<No preview>",
            fill="gray",
        )
    # ------------------------------------------------------------------
    def preview_current(self) -> None:
        if not self.jobs:
            return
        job = self.jobs[self.current_index]
        if self.easy_mode_var.get():
            job.resized, _ = self._easy_convert(job.image)
        else:
            dims = self._parse_dims()
            if dims is None:
                return
            w, h, scale = dims
            new_size = self._calc_new_size(job.image.size, w, h, scale)
            resample = ALG_MAP[self.alg_var.get()]
            job.resized = job.image.resize(new_size, resample)
        self.preview_job(job)

    # ------------------------------------------------------------------
    def save_current(self) -> None:
        if not self.jobs:
            return
        job = self.jobs[self.current_index]
        if job.resized is None:
            messagebox.showinfo("Save", "Preview first!")
            return
        fname = filedialog.asksaveasfilename(
            title="Save image",
            defaultextension="." + self.fmt_var.get().lower(),
            filetypes=[(self.fmt_var.get(), "*.*")],
        )
        if not fname:
            return
        if self.easy_mode_var.get():
            resized, fmt = self._easy_convert(job.image if job.resized is None else job.resized)
            out_path = Path(fname)
            self._save_image(resized, out_path, fmt)
        else:
            resized = job.resized if job.resized else job.image
            out_path = Path(fname)
            self._save_image(resized, out_path)
        messagebox.showinfo("Save", "Saved!")

    # ------------------------------------------------------------------
    # --- zoom controls restored --------------------------------------
    def _apply_zoom_selection(self, _e=None):
        sel = self.zoom_var.get()
        if sel == "Fit":
            self._zoom_org = self._zoom_resz = 1.0
        else:
            factor = float(sel.replace("x", ""))
            self._zoom_org = self._zoom_resz = factor
        if self.jobs and self.current_index is not None:
            self.preview_job(self.jobs[self.current_index])

    def _on_root_resize(self, _e):
        new_size = (self.canvas_org.winfo_width(), self.canvas_org.winfo_height())
        if new_size != self._last_canvas_size and self.jobs and self.current_index is not None:
            self._last_canvas_size = new_size
            self.preview_job(self.jobs[self.current_index])

    def _on_zoom(self, event, is_resized: bool, *, delta: int | None = None) -> None:
        d = (event.delta if delta is None else delta)
        step = ZOOM_STEP if d > 0 else 1 / ZOOM_STEP
        if is_resized:
            self._zoom_resz = min(max(self._zoom_resz * step, MIN_ZOOM), MAX_ZOOM)
        else:
            self._zoom_org = min(max(self._zoom_org * step, MIN_ZOOM), MAX_ZOOM)
        if self.jobs and self.current_index is not None:
            self.preview_job(self.jobs[self.current_index])

    # ------------------------------------------------------------------
    def _open_full_preview(self, is_resized: bool) -> None:
        """Open a new window showing the selected image at max feasible size."""
        if not self.jobs:
            return
        job = self.jobs[self.current_index]
        img = job.resized if is_resized and job.resized else job.image
        # Fit to screen (leave small margin)
        sw, sh = self.winfo_screenwidth() - 100, self.winfo_screenheight() - 100
        iw, ih = img.size
        scale = min(sw / iw, sh / ih, 1.0)
        if scale < 1.0:
            disp_img = img.resize((int(iw * scale), int(ih * scale)), Resampling.LANCZOS)
        else:
            disp_img = img
        win = tk.Toplevel(self)
        win.title("Full Preview - Resized" if is_resized else "Full Preview - Original")
        canvas = tk.Canvas(win, width=disp_img.width, height=disp_img.height)
        canvas.pack()
        imgtk = ImageTk.PhotoImage(disp_img)
        self._full_imgs.append(imgtk)  # keep ref
        canvas.create_image(disp_img.width // 2, disp_img.height // 2, image=imgtk)

    # ------------------------------------------------------------------
    def batch_save(self) -> None:
        if not self.jobs:
            return
        out_dir_name = filedialog.askdirectory(title="Select output folder")
        if not out_dir_name:
            return
        out_dir = Path(out_dir_name)
        if self.easy_mode_var.get():
            for i, job in enumerate(self.jobs):
                job.resized, fmt = self._easy_convert(job.image)
                out_path = self._easy_target_path(out_dir, job, i)
                self._save_image(job.resized, out_path, fmt)
        else:
            dims = self._parse_dims()
            if dims is None:
                return
            w, h, scale = dims
            resample = ALG_MAP[self.alg_var.get()]
            for i, job in enumerate(self.jobs):
                new_size = self._calc_new_size(job.image.size, w, h, scale)
                job.resized = job.image.resize(new_size, resample)
                out_path = out_dir / f"{job.path.stem}_resized_{i + 1}.{self.fmt_var.get().lower()}"
                self._save_image(job.resized, out_path)

        messagebox.showinfo("Batch", "All images saved!")

# ... (rest of the code remains the same)
    def _parse_dims(self) -> Optional[tuple[Optional[int], Optional[int], Optional[int]]]:
        """Return (w,h,scale) or None with warning dialog."""

        def _to_int(s: str) -> Optional[int]:
            s = s.strip()
            return int(s) if s.isdigit() else None

        w = _to_int(self.width_var.get())
        h = _to_int(self.height_var.get())
        scale = _to_int(self.scale_var.get())
        if not any([w, h, scale]):
            messagebox.showwarning("Size", "Set width / height or scale %")
            return None
        return w, h, scale

    # ------------------------------------------------------------------
    # Easy mode helpers
    def _easy_convert(self, img: Image.Image) -> tuple[Image.Image, str]:
        """Resize keeping aspect so *long* edge matches preset; pick format."""
        target_long = 1920 if self.easy_res_var.get() == "1080p" else 2560
        w, h = img.size
        long_edge = max(w, h)
        if long_edge > target_long:
            scale = target_long / long_edge
            new_size = (int(w * scale), int(h * scale))
            resized = img.resize(new_size, Resampling.LANCZOS)
        else:
            resized = img.copy()
        fmt = "PNG" if ("A" in img.getbands()) else "JPEG"
        return resized, fmt

    def _easy_target_path(self, out_dir: Path, job: "ImageJob", idx: int) -> Path:
        fmt = "png" if ("A" in job.image.getbands()) else "jpg"
        suffix = "_easy" + ("1080" if self.easy_res_var.get()=="1080p" else "1440")
        return out_dir / f"{job.path.stem}{suffix}_{idx+1}.{fmt}"

    # ------------------------------------------------------------------
    @staticmethod
    def _calc_new_size(
        orig: tuple[int, int], w: Optional[int], h: Optional[int], scale: Optional[int]
    ) -> tuple[int, int]:
        ow, oh = orig
        if scale:
            return (int(ow * scale / 100), int(oh * scale / 100))
        if w and h:
            return (w, h)
        if w:
            return (w, int(oh * w / ow))
        if h:
            return (int(ow * h / oh), h)
        return orig

    def _save_image(self, img: Image.Image, path: Path, fmt_override: str | None = None) -> None:
        fmt = (fmt_override or self.fmt_var.get()).upper()
        if fmt == "JPEG" and img.mode in ("RGBA", "P"):
            img = img.convert("RGB")
        try:
            img.save(path, fmt)
        except Exception as e:  # pragma: no cover
            messagebox.showerror("Save Error", f"Failed to save {path}: {e}")


# ----------------------------------------------------------------------
if __name__ == "__main__":
    ResizeApp().mainloop()
