"""画像リサイズGUIアプリケーション"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from pathlib import Path
from dataclasses import dataclass
from typing import List, Optional

from PIL import Image, ImageTk

# Pillow 10以降のResamplingクラスに対応
try:
    from PIL.Image import Resampling
except ImportError:
    class _Resampling:  # type: ignore
        LANCZOS = Image.LANCZOS  # type: ignore
    Resampling = _Resampling()  # type: ignore


@dataclass
class ImageJob:
    """リサイズ対象の画像情報を保持するデータクラス"""
    path: Path
    image: Image.Image
    resized: Optional[Image.Image] = None


class ResizeApp(tk.Tk):
    ZOOM_LEVELS = ["画面に合わせる", "10%", "25%", "50%", "75%", "100%", "150%", "200%", "400%"]

    """アプリケーションのメインウィンドウ"""

    def __init__(self):
        super().__init__()
        self.title("画像リサイズツール")
        self.geometry("1200x800")

        # アプリケーションの状態を管理する変数
        self.jobs: list[ImageJob] = []
        self.current_index: int = 0
        self._zoom_org: float = 1.0
        self._zoom_resz: float = 1.0
        self._imgtk_org: ImageTk.PhotoImage | None = None
        self._imgtk_resz: ImageTk.PhotoImage | None = None

        # リサイズ設定
        self.resize_mode_var = tk.StringVar(value="ratio")
        self.ratio_var = tk.StringVar(value="50")
        self.width_var = tk.StringVar(value="800")
        self.height_var = tk.StringVar(value="600")

        # 表示設定
        self.zoom_var = tk.StringVar(value="100%")

        # 保存設定
        self.output_dir_var = tk.StringVar()
        self.suffix_var = tk.StringVar(value="_resized")
        self.format_var = tk.StringVar(value="元の形式を維持")

        # Pillowのリサンプリングフィルタ
        self.resample_filter = Resampling.LANCZOS

        # UIのセットアップ
        self._setup_ui()

    def _setup_ui(self):
        """UIのメインレイアウトを構築します。"""
        # メインフレーム
        main_frame = ttk.Frame(self, padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # 左側のコントロールパネル
        controls_frame = ttk.LabelFrame(main_frame, text="コントロール", padding=10)
        controls_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 10), anchor='n')

        # 右側のプレビューエリア
        preview_frame = ttk.Frame(main_frame)
        preview_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        # 各エリアのウィジェットを配置
        self._setup_controls(controls_frame)
        self._setup_previews(preview_frame)

    def _setup_controls(self, parent: ttk.Frame):
        """コントロールパネルのウィジェットを作成します。"""
        parent.columnconfigure(0, weight=1)

        # --- ファイル操作フレーム ---
        file_frame = ttk.LabelFrame(parent, text="ファイル")
        file_frame.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        file_frame.columnconfigure(1, weight=1)

        open_btn = ttk.Button(file_frame, text="画像を開く...", command=self._open_files)
        open_btn.grid(row=0, column=0, padx=5, pady=5)

        self.counter_var = tk.StringVar(value="0 / 0")
        counter_label = ttk.Label(file_frame, textvariable=self.counter_var)
        counter_label.grid(row=0, column=1, padx=5, pady=5, sticky="w")

        nav_frame = ttk.Frame(file_frame)
        nav_frame.grid(row=0, column=2, padx=5, pady=5, sticky="e")

        self.prev_btn = ttk.Button(nav_frame, text="← 前へ", command=self._prev_image, state=tk.DISABLED)
        self.prev_btn.pack(side=tk.LEFT)

        self.next_btn = ttk.Button(nav_frame, text="次へ →", command=self._next_image, state=tk.DISABLED)
        self.next_btn.pack(side=tk.LEFT, padx=(5, 0))

        # --- サイズ指定フレーム ---
        size_frame = ttk.LabelFrame(parent, text="サイズ指定")
        size_frame.grid(row=1, column=0, sticky="ew", pady=(0, 10))
        size_frame.columnconfigure(1, weight=1)

        # モード選択
        self.ratio_rb = ttk.Radiobutton(size_frame, text="比率 (%)", variable=self.resize_mode_var, value="ratio", command=self._update_resize_control_state)
        self.ratio_rb.grid(row=0, column=0, padx=5, pady=2, sticky="w")
        self.width_rb = ttk.Radiobutton(size_frame, text="幅 (px)", variable=self.resize_mode_var, value="width", command=self._update_resize_control_state)
        self.width_rb.grid(row=1, column=0, padx=5, pady=2, sticky="w")
        self.height_rb = ttk.Radiobutton(size_frame, text="高さ (px)", variable=self.resize_mode_var, value="height", command=self._update_resize_control_state)
        self.height_rb.grid(row=2, column=0, padx=5, pady=2, sticky="w")

        # 入力フィールド
        self.ratio_entry = ttk.Entry(size_frame, textvariable=self.ratio_var, width=10)
        self.ratio_entry.grid(row=0, column=1, padx=5, pady=2, sticky="w")
        self.width_entry = ttk.Entry(size_frame, textvariable=self.width_var, width=10)
        self.width_entry.grid(row=1, column=1, padx=5, pady=2, sticky="w")
        self.height_entry = ttk.Entry(size_frame, textvariable=self.height_var, width=10)
        self.height_entry.grid(row=2, column=1, padx=5, pady=2, sticky="w")

        apply_btn = ttk.Button(size_frame, text="適用", command=self._apply_resize)
        apply_btn.grid(row=3, column=0, columnspan=2, pady=5)

        self._update_resize_control_state() # 初期状態を設定

        # --- 表示設定フレーム ---
        display_frame = ttk.LabelFrame(parent, text="表示")
        display_frame.grid(row=2, column=0, sticky="ew", pady=(0, 10))

        zoom_label = ttk.Label(display_frame, text="ズーム:")
        zoom_label.grid(row=0, column=0, padx=5, pady=5, sticky="w")

        self.zoom_combo = ttk.Combobox(
            display_frame,
            textvariable=self.zoom_var,
            values=self.ZOOM_LEVELS,
            width=15
        )
        self.zoom_combo.grid(row=0, column=1, padx=5, pady=5, sticky="w")
        self.zoom_combo.bind("<<ComboboxSelected>>", self._apply_zoom_selection)
        self.zoom_combo.bind("<Return>", self._apply_zoom_selection)


        zoom_in_btn = ttk.Button(display_frame, text="＋", command=self._zoom_in, width=3)
        zoom_in_btn.grid(row=0, column=2, padx=(5, 0), pady=5)
        zoom_out_btn = ttk.Button(display_frame, text="－", command=self._zoom_out, width=3)
        zoom_out_btn.grid(row=0, column=3, padx=(5, 0), pady=5)

        # --- 保存フレーム ---
        save_frame = ttk.LabelFrame(parent, text="保存")
        save_frame.grid(row=3, column=0, sticky="ew", pady=(0, 10))
        save_frame.columnconfigure(1, weight=1)

        dir_label = ttk.Label(save_frame, text="出力先:")
        dir_label.grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.dir_entry = ttk.Entry(save_frame, textvariable=self.output_dir_var, state="readonly")
        self.dir_entry.grid(row=0, column=1, padx=5, pady=5, sticky="ew")
        dir_btn = ttk.Button(save_frame, text="参照...", command=self._select_output_dir)
        dir_btn.grid(row=0, column=2, padx=5, pady=5)

        suffix_label = ttk.Label(save_frame, text="接尾辞:")
        suffix_label.grid(row=1, column=0, padx=5, pady=5, sticky="w")
        suffix_entry = ttk.Entry(save_frame, textvariable=self.suffix_var)
        suffix_entry.grid(row=1, column=1, padx=5, pady=5, sticky="w")

        format_label = ttk.Label(save_frame, text="形式:")
        format_label.grid(row=2, column=0, padx=5, pady=5, sticky="w")
        self.format_combo = ttk.Combobox(
            save_frame,
            textvariable=self.format_var,
            values=["元の形式を維持", "JPEG", "PNG", "WEBP"],
            width=15,
            state="readonly"
        )
        self.format_combo.grid(row=2, column=1, padx=5, pady=5, sticky="w")

        self.save_current_btn = ttk.Button(save_frame, text="この画像を保存", command=self._save_current_image, state=tk.DISABLED)
        self.save_current_btn.grid(row=3, column=0, columnspan=3, padx=5, pady=5, sticky="ew")
        self.save_all_btn = ttk.Button(save_frame, text="リサイズ済みをすべて保存", command=self._save_all_images, state=tk.DISABLED)
        self.save_all_btn.grid(row=4, column=0, columnspan=3, padx=5, pady=5, sticky="ew")


    def _setup_previews(self, parent: ttk.Frame):
        """プレビューエリアのウィジェットを作成します。"""
        parent.columnconfigure(0, weight=1)
        parent.columnconfigure(1, weight=1)
        parent.rowconfigure(0, weight=1)

        # オリジナル画像プレビュー
        org_frame = ttk.LabelFrame(parent, text="オリジナル")
        org_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 5))
        org_frame.rowconfigure(0, weight=1)
        org_frame.columnconfigure(0, weight=1)

        self.canvas_org = tk.Canvas(org_frame, bg="#f0f0f0")
        self.canvas_org.grid(row=0, column=0, sticky="nsew")

        org_v_scroll = ttk.Scrollbar(org_frame, orient=tk.VERTICAL, command=self.canvas_org.yview)
        org_v_scroll.grid(row=0, column=1, sticky="ns")
        org_h_scroll = ttk.Scrollbar(org_frame, orient=tk.HORIZONTAL, command=self.canvas_org.xview)
        org_h_scroll.grid(row=1, column=0, sticky="ew")
        self.canvas_org.configure(yscrollcommand=org_v_scroll.set, xscrollcommand=org_h_scroll.set)

        # リサイズ後画像プレビュー
        resz_frame = ttk.LabelFrame(parent, text="リサイズ後")
        resz_frame.grid(row=0, column=1, sticky="nsew", padx=(5, 0))
        resz_frame.rowconfigure(0, weight=1)
        resz_frame.columnconfigure(0, weight=1)

        self.canvas_resz = tk.Canvas(resz_frame, bg="#f0f0f0")
        self.canvas_resz.grid(row=0, column=0, sticky="nsew")

        resz_v_scroll = ttk.Scrollbar(resz_frame, orient=tk.VERTICAL, command=self.canvas_resz.yview)
        resz_v_scroll.grid(row=0, column=1, sticky="ns")
        resz_h_scroll = ttk.Scrollbar(resz_frame, orient=tk.HORIZONTAL, command=self.canvas_resz.xview)
        resz_h_scroll.grid(row=1, column=0, sticky="ew")
        self.canvas_resz.configure(yscrollcommand=resz_v_scroll.set, xscrollcommand=resz_h_scroll.set)



    def _open_files(self):
        """ファイルダイアログを開き、画像ファイルを読み込みます。"""
        filepaths = filedialog.askopenfilenames(
            title="リサイズする画像を選択",
            filetypes=[("画像ファイル", "*.jpg *.jpeg *.png *.bmp *.gif *.tiff *.webp"),
                       ("すべてのファイル", "*.*")]
        )
        if not filepaths:
            return

        self.jobs = []
        for path_str in filepaths:
            try:
                img = Image.open(path_str)
                # 標準的でないモードの画像をRGBに変換
                if img.mode not in ('L', 'RGB', 'RGBA'):
                    img = img.convert('RGB')
                self.jobs.append(ImageJob(path=Path(path_str), image=img))
            except Exception as e:
                messagebox.showerror("読み込みエラー", f"画像の読み込みに失敗しました: {path_str}\n{e}")

        if self.jobs:
            self.current_index = 0
            self._display_current_image()
        else:
            self._clear_previews()

        self._update_navigation()

    def _prev_image(self, event=None):
        """前の画像に切り替えます。"""
        if self.current_index > 0:
            self.current_index -= 1
            self._display_current_image()
            self._update_navigation()

    def _next_image(self, event=None):
        """次の画像に切り替えます。"""
        if self.current_index < len(self.jobs) - 1:
            self.current_index += 1
            self._display_current_image()
            self._update_navigation()

    def _update_navigation(self):
        """ナビゲーションボタンの状態とカウンターを更新します。"""
        num_jobs = len(self.jobs)
        if num_jobs > 0:
            self.counter_var.set(f"{self.current_index + 1} / {num_jobs}")
            self.prev_btn.config(state=tk.NORMAL if self.current_index > 0 else tk.DISABLED)
            self.next_btn.config(state=tk.NORMAL if self.current_index < num_jobs - 1 else tk.DISABLED)
        else:
            self.counter_var.set("0 / 0")
            self.prev_btn.config(state=tk.DISABLED)
            self.next_btn.config(state=tk.DISABLED)

    def _draw_previews(self, job: ImageJob):
        """指定されたImageJobをプレビューに描画します。"""
        zoom_pct_org = int(self._zoom_org * 100)
        # Keep a reference to the image to prevent it from being garbage collected
        self._imgtk_org = self._draw_on_canvas(
            self.canvas_org, job.image, self._zoom_org, f"{zoom_pct_org}%"
        )

        if job.resized is not None:
            zoom_pct_resz = int(self._zoom_resz * 100)
            self._imgtk_resz = self._draw_on_canvas(
                self.canvas_resz, job.resized, self._zoom_resz, f"{zoom_pct_resz}%"
            )
        else:
            self.canvas_resz.delete("all")
            self._imgtk_resz = None

    def _draw_on_canvas(self, canvas: tk.Canvas, img: Image.Image, zoom: float, label: str) -> ImageTk.PhotoImage:
        """指定されたキャンバスに画像をズームして描画し、ラベルを追加します。"""
        disp_img = img.copy()
        disp_img = disp_img.resize(
            (int(disp_img.width * zoom), int(disp_img.height * zoom)),
            self.resample_filter
        )
        imgtk = ImageTk.PhotoImage(disp_img)

        canvas.delete("all")
        canvas.create_image(0, 0, anchor="nw", image=imgtk)
        canvas.config(scrollregion=(0, 0, disp_img.width, disp_img.height))

        # ズーム率表示用の半透明バー
        bar_h = 28
        canvas.create_rectangle(0, 0, disp_img.width, bar_h, fill="#000", stipple="gray25", outline="")
        canvas.create_text(10, bar_h // 2, anchor="w", text=label, fill="white", font=("Yu Gothic UI", 14, "bold"))

        return imgtk

    def _display_current_image(self):
        """現在の画像をプレビューに表示します。"""
        if not self.jobs:
            self._clear_previews()
            return
        
        job = self.jobs[self.current_index]
        self._draw_previews(job)
        self._update_save_button_state()

    def _clear_previews(self):
        """プレビューキャンバスをクリアします。"""
        self.canvas_org.delete("all")
        self.canvas_resz.delete("all")
        self._update_save_button_state()


    def _update_resize_control_state(self):
        """リサイズモードの変更に応じて入力フィールドの有効/無効を切り替えます。"""
        mode = self.resize_mode_var.get()
        self.ratio_entry.config(state=tk.NORMAL if mode == "ratio" else tk.DISABLED)
        self.width_entry.config(state=tk.NORMAL if mode == "width" else tk.DISABLED)
        self.height_entry.config(state=tk.NORMAL if mode == "height" else tk.DISABLED)

    def _apply_resize(self):
        """現在選択されている画像にリサイズを適用します。"""
        if not self.jobs:
            messagebox.showwarning("警告", "画像が開かれていません。")
            return
        
        job = self.jobs[self.current_index]
        mode = self.resize_mode_var.get()
        original_size = job.image.size
        new_size = None

        try:
            if mode == "ratio":
                ratio = int(self.ratio_var.get())
                if ratio <= 0:
                    raise ValueError("比率は1以上の整数で指定してください。")
                new_w = int(original_size[0] * ratio / 100)
                new_h = int(original_size[1] * ratio / 100)
                new_size = (new_w, new_h)
            elif mode == "width":
                new_w = int(self.width_var.get())
                if new_w <= 0:
                    raise ValueError("幅は1以上の整数で指定してください。")
                ratio = new_w / original_size[0]
                new_h = int(original_size[1] * ratio)
                new_size = (new_w, new_h)
            elif mode == "height":
                new_h = int(self.height_var.get())
                if new_h <= 0:
                    raise ValueError("高さは1以上の整数で指定してください。")
                ratio = new_h / original_size[1]
                new_w = int(original_size[0] * ratio)
                new_size = (new_w, new_h)

            if new_size and new_size[0] > 0 and new_size[1] > 0:
                resized_img = job.image.resize(new_size, self.resample_filter)
                job.resized = resized_img
                self._draw_previews(job)
                self._update_save_button_state()
            else:
                raise ValueError("リサイズ後のサイズが0以下になります。")

        except ValueError as e:
            messagebox.showerror("入力エラー", str(e))
        except Exception as e:
            messagebox.showerror("リサイズエラー", f"リサイズ処理中にエラーが発生しました。\n{e}")


    def _apply_zoom_selection(self, event=None):
        """ズーム選択コンボボックスの変更を適用します。"""
        sel = self.zoom_var.get()
        
        if sel == "画面に合わせる":
            self._fit_to_screen()
        else:
            try:
                if sel.endswith('%'):
                    factor = float(sel.rstrip('%')) / 100.0
                else:
                    factor = float(sel)
                
                if factor <= 0:
                    raise ValueError("ズーム率は正の数である必要があります。")
                
                self._zoom_org = self._zoom_resz = factor
            except ValueError:
                messagebox.showwarning("入力エラー", "有効なズーム率(例: 50% または 0.5)を入力してください。")
                self._update_zoom_display() # 表示を元に戻す
                return

        if self.jobs:
            self._display_current_image()

    def _fit_to_screen(self):
        """画像をキャンバスにフィットさせるズーム率を計算して適用します。"""
        if not self.jobs:
            self._zoom_org = self._zoom_resz = 1.0
            return

        job = self.jobs[self.current_index]
        
        # オリジナル画像
        canvas_w = self.canvas_org.winfo_width()
        canvas_h = self.canvas_org.winfo_height()
        img_w, img_h = job.image.size
        if canvas_w > 1 and canvas_h > 1 and img_w > 0 and img_h > 0:
            w_ratio = (canvas_w - 10) / img_w
            h_ratio = (canvas_h - 10) / img_h
            self._zoom_org = min(w_ratio, h_ratio)
        else:
            self._zoom_org = 1.0 # デフォルト

        # リサイズ後画像
        if job.resized:
            canvas_w = self.canvas_resz.winfo_width()
            canvas_h = self.canvas_resz.winfo_height()
            img_w, img_h = job.resized.size
            if canvas_w > 1 and canvas_h > 1 and img_w > 0 and img_h > 0:
                w_ratio = (canvas_w - 10) / img_w
                h_ratio = (canvas_h - 10) / img_h
                self._zoom_resz = min(w_ratio, h_ratio)
            else:
                self._zoom_resz = 1.0
        else:
            self._zoom_resz = self._zoom_org

    def _update_zoom_display(self):
        """現在のズーム率をコンボボックスに表示します。"""
        if self._zoom_org == self._zoom_resz:
            zoom_pct = int(self._zoom_org * 100)
            self.zoom_var.set(f"{zoom_pct}%")
        else:
            self.zoom_var.set("画面に合わせる")

    def _zoom_in(self):
        """ズームインします。"""
        current_zoom = self._zoom_org
        numeric_levels = [float(z.rstrip('%'))/100.0 for z in self.ZOOM_LEVELS if z != "画面に合わせる"]
        
        next_levels = [level for level in numeric_levels if level > current_zoom]
        if next_levels:
            new_zoom = min(next_levels)
        else:
            new_zoom = max(numeric_levels)
        
        self._zoom_org = self._zoom_resz = new_zoom
        self._update_zoom_display()
        if self.jobs:
            self._display_current_image()

    def _zoom_out(self):
        """ズームアウトします。"""
        current_zoom = self._zoom_org
        numeric_levels = [float(z.rstrip('%'))/100.0 for z in self.ZOOM_LEVELS if z != "画面に合わせる"]

        prev_levels = [level for level in numeric_levels if level < current_zoom]
        if prev_levels:
            new_zoom = max(prev_levels)
        else:
            new_zoom = min(numeric_levels)

        self._zoom_org = self._zoom_resz = new_zoom
        self._update_zoom_display()
        if self.jobs:
            self._display_current_image()


    def _select_output_dir(self):
        """出力ディレクトリを選択するダイアログを開きます。"""
        dir_path = filedialog.askdirectory(title="出力先フォルダを選択")
        if dir_path:
            self.output_dir_var.set(dir_path)

    def _save_current_image(self):
        """現在表示しているリサイズ済み画像を保存します。"""
        if not self.jobs or self.jobs[self.current_index].resized is None:
            messagebox.showwarning("保存不可", "リサイズ済みの画像がありません。")
            return
        
        if self._save_image(self.jobs[self.current_index]):
            messagebox.showinfo("完了", "画像を保存しました。")

    def _save_all_images(self):
        """リサイズ済みのすべての画像を保存します。"""
        resized_jobs = [job for job in self.jobs if job.resized is not None]
        if not resized_jobs:
            messagebox.showwarning("保存不可", "リサイズ済みの画像がありません。")
            return

        if messagebox.askokcancel("確認", f"{len(resized_jobs)}個のファイルを保存しますか？"):
            saved_count = 0
            for job in resized_jobs:
                if self._save_image(job):
                    saved_count += 1
            
            messagebox.showinfo("完了", f"{saved_count}個のファイルの保存が完了しました。")

    def _save_image(self, job: ImageJob) -> bool:
        """指定されたImageJobを保存します。"""
        output_dir = self.output_dir_var.get()
        if not output_dir:
            messagebox.showerror("エラー", "出力先フォルダが指定されていません。")
            return False
        
        output_path = Path(output_dir)
        if not output_path.is_dir():
            messagebox.showerror("エラー", "指定された出力先は有効なフォルダではありません。")
            return False

        suffix = self.suffix_var.get()
        original_path = job.path
        new_filename = f"{original_path.stem}{suffix}{original_path.suffix}"
        save_path = output_path / new_filename

        output_format = self.format_var.get()
        save_kwargs = {}
        
        try:
            img_to_save = job.resized
            if img_to_save is None:
                return False

            if output_format == "JPEG":
                if img_to_save.mode == 'RGBA':
                    bg = Image.new("RGB", img_to_save.size, (255, 255, 255))
                    bg.paste(img_to_save, mask=img_to_save.split()[3])
                    img_to_save = bg
                save_kwargs['quality'] = 95
                save_path = save_path.with_suffix(".jpg")
            elif output_format == "PNG":
                save_path = save_path.with_suffix(".png")
            elif output_format == "WEBP":
                save_kwargs['quality'] = 90
                save_path = save_path.with_suffix(".webp")
            elif output_format == "元の形式を維持":
                if original_path.suffix.lower() in ['.jpg', '.jpeg']:
                    if img_to_save.mode == 'RGBA':
                        bg = Image.new("RGB", img_to_save.size, (255, 255, 255))
                        bg.paste(img_to_save, mask=img_to_save.split()[3])
                        img_to_save = bg
                    save_kwargs['quality'] = 95
                elif original_path.suffix.lower() == '.webp':
                    save_kwargs['quality'] = 90

            if save_path.exists():
                if not messagebox.askyesno("上書き確認", f"ファイルは既に存在します:\n{save_path}\n上書きしますか？"):
                    return False
            
            img_to_save.save(save_path, **save_kwargs)
            return True

        except Exception as e:
            messagebox.showerror("保存エラー", f"ファイルの保存中にエラーが発生しました:\n{save_path}\n{e}")
            return False

    def _update_save_button_state(self):
        """保存ボタンの状態を更新します。"""
        any_resized = any(job.resized is not None for job in self.jobs)
        self.save_all_btn.config(state=tk.NORMAL if any_resized else tk.DISABLED)

        current_resized = self.jobs and self.current_index < len(self.jobs) and self.jobs[self.current_index].resized is not None
        self.save_current_btn.config(state=tk.NORMAL if current_resized else tk.DISABLED)


if __name__ == "__main__":
    app = ResizeApp()
    app.mainloop()
