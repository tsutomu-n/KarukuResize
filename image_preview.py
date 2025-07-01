"""
画像プレビュー機能のモジュール
"""
import customtkinter as ctk
from PIL import Image, ImageTk
from pathlib import Path
import threading
from typing import Optional, Tuple, Callable
from dataclasses import dataclass
import math

@dataclass
class ImageInfo:
    """画像情報を保持するデータクラス"""
    path: Path
    size: Tuple[int, int]  # (width, height)
    file_size: int  # bytes
    format: str
    mode: str  # RGB, RGBA, etc.
    has_exif: bool
    
    @property
    def size_text(self) -> str:
        """サイズを読みやすい形式で返す"""
        return f"{self.size[0]} × {self.size[1]} px"
    
    @property
    def file_size_text(self) -> str:
        """ファイルサイズを読みやすい形式で返す"""
        size = self.file_size
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024.0:
                return f"{size:.1f} {unit}"
            size /= 1024.0
        return f"{size:.1f} GB"


class ImagePreviewWidget(ctk.CTkFrame):
    """画像プレビューウィジェット"""
    
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        
        # 設定
        self.max_preview_size = (800, 600)
        self.zoom_levels = [0.1, 0.25, 0.5, 0.75, 1.0, 1.5, 2.0, 3.0, 4.0]
        self.current_zoom_index = 4  # 1.0 = 100%
        
        # 状態
        self.original_image: Optional[Image.Image] = None
        self.display_image: Optional[ImageTk.PhotoImage] = None
        self.image_info: Optional[ImageInfo] = None
        self.pan_start_x = 0
        self.pan_start_y = 0
        self.canvas_offset_x = 0
        self.canvas_offset_y = 0
        
        # コールバック
        self.on_image_loaded: Optional[Callable[[ImageInfo], None]] = None
        
        self._setup_ui()
        
    def _setup_ui(self):
        """UIをセットアップ"""
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)
        
        # キャンバス
        self.canvas = ctk.CTkCanvas(
            self,
            bg='#2B2B2B',
            highlightthickness=0
        )
        self.canvas.grid(row=0, column=0, sticky="nsew", padx=2, pady=2)
        
        # コントロールパネル
        self.control_panel = ctk.CTkFrame(self, height=40)
        self.control_panel.grid(row=1, column=0, sticky="ew", padx=2, pady=2)
        self.control_panel.grid_columnconfigure(1, weight=1)
        
        # ズームコントロール
        zoom_frame = ctk.CTkFrame(self.control_panel, fg_color="transparent")
        zoom_frame.grid(row=0, column=0, padx=5, pady=5)
        
        self.zoom_out_btn = ctk.CTkButton(
            zoom_frame,
            text="−",
            width=30,
            height=30,
            command=self.zoom_out
        )
        self.zoom_out_btn.pack(side="left", padx=2)
        
        self.zoom_label = ctk.CTkLabel(
            zoom_frame,
            text="100%",
            width=60
        )
        self.zoom_label.pack(side="left", padx=5)
        
        self.zoom_in_btn = ctk.CTkButton(
            zoom_frame,
            text="＋",
            width=30,
            height=30,
            command=self.zoom_in
        )
        self.zoom_in_btn.pack(side="left", padx=2)
        
        self.fit_btn = ctk.CTkButton(
            zoom_frame,
            text="フィット",
            width=60,
            height=30,
            command=self.fit_to_window
        )
        self.fit_btn.pack(side="left", padx=10)
        
        # 情報ラベル
        self.info_label = ctk.CTkLabel(
            self.control_panel,
            text="画像が読み込まれていません",
            anchor="e"
        )
        self.info_label.grid(row=0, column=1, padx=10, pady=5, sticky="e")
        
        # マウスイベントのバインド
        self.canvas.bind("<Button-1>", self._on_canvas_click)
        self.canvas.bind("<B1-Motion>", self._on_canvas_drag)
        self.canvas.bind("<MouseWheel>", self._on_mouse_wheel)
        self.canvas.bind("<Button-4>", self._on_mouse_wheel)  # Linux
        self.canvas.bind("<Button-5>", self._on_mouse_wheel)  # Linux
        
    def load_image(self, image_path: Path):
        """画像を読み込む"""
        threading.Thread(
            target=self._load_image_thread,
            args=(image_path,),
            daemon=True
        ).start()
        
    def _load_image_thread(self, image_path: Path):
        """画像読み込みスレッド"""
        try:
            # 画像を開く
            image = Image.open(image_path)
            
            # EXIF情報の確認
            has_exif = hasattr(image, '_getexif') and image._getexif() is not None
            
            # 画像情報を作成
            info = ImageInfo(
                path=image_path,
                size=image.size,
                file_size=image_path.stat().st_size,
                format=image.format or "Unknown",
                mode=image.mode,
                has_exif=has_exif
            )
            
            # RGBに変換（表示用）
            if image.mode not in ('RGB', 'RGBA'):
                image = image.convert('RGB')
                
            # メインスレッドで更新
            self.after(0, lambda: self._update_image(image, info))
            
        except Exception as e:
            self.after(0, lambda: self._show_error(f"画像の読み込みエラー: {str(e)}"))
            
    def _update_image(self, image: Image.Image, info: ImageInfo):
        """画像を更新"""
        self.original_image = image
        self.image_info = info
        
        # 情報ラベルを更新
        self.info_label.configure(
            text=f"{info.size_text} | {info.file_size_text} | {info.format}"
        )
        
        # 初期表示（フィット）
        self.fit_to_window()
        
        # コールバック呼び出し
        if self.on_image_loaded:
            self.on_image_loaded(info)
            
    def _show_error(self, message: str):
        """エラー表示"""
        self.canvas.delete("all")
        self.canvas.create_text(
            self.canvas.winfo_width() // 2,
            self.canvas.winfo_height() // 2,
            text=message,
            fill="red",
            font=("", 12)
        )
        self.info_label.configure(text="エラー")
        
    def zoom_in(self):
        """ズームイン"""
        if self.current_zoom_index < len(self.zoom_levels) - 1:
            self.current_zoom_index += 1
            self._update_display()
            
    def zoom_out(self):
        """ズームアウト"""
        if self.current_zoom_index > 0:
            self.current_zoom_index -= 1
            self._update_display()
            
    def fit_to_window(self):
        """ウィンドウにフィット"""
        if not self.original_image:
            return
            
        # キャンバスサイズを取得
        self.canvas.update_idletasks()
        canvas_width = self.canvas.winfo_width()
        canvas_height = self.canvas.winfo_height()
        
        if canvas_width <= 1 or canvas_height <= 1:
            return
            
        # フィットするズームレベルを計算
        img_width, img_height = self.original_image.size
        zoom_x = canvas_width / img_width
        zoom_y = canvas_height / img_height
        zoom = min(zoom_x, zoom_y) * 0.95  # 少し余白を持たせる
        
        # 最も近いズームレベルを選択
        closest_index = 0
        min_diff = float('inf')
        for i, level in enumerate(self.zoom_levels):
            diff = abs(level - zoom)
            if diff < min_diff:
                min_diff = diff
                closest_index = i
                
        self.current_zoom_index = closest_index
        self.canvas_offset_x = 0
        self.canvas_offset_y = 0
        self._update_display()
        
    def _update_display(self):
        """表示を更新"""
        if not self.original_image:
            return
            
        # 現在のズームレベル
        zoom = self.zoom_levels[self.current_zoom_index]
        self.zoom_label.configure(text=f"{int(zoom * 100)}%")
        
        # リサイズ
        new_width = int(self.original_image.width * zoom)
        new_height = int(self.original_image.height * zoom)
        
        # 画像をリサイズ
        if zoom < 1.0:
            resized = self.original_image.resize(
                (new_width, new_height),
                Image.Resampling.LANCZOS
            )
        else:
            resized = self.original_image.resize(
                (new_width, new_height),
                Image.Resampling.NEAREST
            )
            
        # PhotoImageに変換
        self.display_image = ImageTk.PhotoImage(resized)
        
        # キャンバスをクリア
        self.canvas.delete("all")
        
        # 画像を表示
        canvas_width = self.canvas.winfo_width()
        canvas_height = self.canvas.winfo_height()
        x = (canvas_width // 2) + self.canvas_offset_x
        y = (canvas_height // 2) + self.canvas_offset_y
        
        self.canvas.create_image(x, y, image=self.display_image, anchor="center")
        
    def _on_canvas_click(self, event):
        """キャンバスクリック時"""
        self.pan_start_x = event.x
        self.pan_start_y = event.y
        self.canvas.configure(cursor="fleur")  # 手のひらカーソル
        
    def _on_canvas_drag(self, event):
        """キャンバスドラッグ時"""
        if self.display_image:
            dx = event.x - self.pan_start_x
            dy = event.y - self.pan_start_y
            
            self.canvas_offset_x += dx
            self.canvas_offset_y += dy
            
            self.pan_start_x = event.x
            self.pan_start_y = event.y
            
            self._update_display()
            
    def _on_mouse_wheel(self, event):
        """マウスホイール時"""
        # Windowsとmacの場合
        if event.delta:
            if event.delta > 0:
                self.zoom_in()
            else:
                self.zoom_out()
        # Linuxの場合
        elif event.num == 4:
            self.zoom_in()
        elif event.num == 5:
            self.zoom_out()
            
    def clear(self):
        """画像をクリア"""
        self.original_image = None
        self.display_image = None
        self.image_info = None
        self.canvas.delete("all")
        self.info_label.configure(text="画像が読み込まれていません")
        self.zoom_label.configure(text="100%")
        self.current_zoom_index = 4
        self.canvas_offset_x = 0
        self.canvas_offset_y = 0


class ComparisonPreviewWidget(ctk.CTkFrame):
    """ビフォー/アフター比較プレビューウィジェット"""
    
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)
        
        # ビフォープレビュー
        self.before_frame = ctk.CTkFrame(self)
        self.before_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 2))
        
        self.before_label = ctk.CTkLabel(
            self.before_frame,
            text="変換前",
            font=("", 12, "bold"),
            height=80,
            justify="left",
            anchor="nw"
        )
        self.before_label.pack(pady=5, fill="x")
        
        self.before_preview = ImagePreviewWidget(self.before_frame)
        self.before_preview.pack(fill="both", expand=True, padx=5, pady=(0, 5))
        
        # アフタープレビュー
        self.after_frame = ctk.CTkFrame(self)
        self.after_frame.grid(row=0, column=1, sticky="nsew", padx=(2, 0))
        
        self.after_label = ctk.CTkLabel(
            self.after_frame,
            text="変換後",
            font=("", 12, "bold"),
            height=80,
            justify="left",
            anchor="nw"
        )
        self.after_label.pack(pady=5, fill="x")
        
        self.after_preview = ImagePreviewWidget(self.after_frame)
        self.after_preview.pack(fill="both", expand=True, padx=5, pady=(0, 5))
        
        # 同期ズーム設定
        self.sync_zoom = True
        self._setup_sync()
        
    def _setup_sync(self):
        """プレビューの同期設定"""
        # ズーム同期
        original_zoom_in = self.before_preview.zoom_in
        original_zoom_out = self.before_preview.zoom_out
        
        def sync_zoom_in():
            original_zoom_in()
            if self.sync_zoom and self.after_preview.original_image:
                self.after_preview.current_zoom_index = self.before_preview.current_zoom_index
                self.after_preview._update_display()
                
        def sync_zoom_out():
            original_zoom_out()
            if self.sync_zoom and self.after_preview.original_image:
                self.after_preview.current_zoom_index = self.before_preview.current_zoom_index
                self.after_preview._update_display()
                
        self.before_preview.zoom_in = sync_zoom_in
        self.before_preview.zoom_out = sync_zoom_out
        
    def load_before_image(self, image_path: Path):
        """変換前画像を読み込む"""
        self.before_preview.load_image(image_path)
        
    def load_after_image(self, image_path: Path):
        """変換後画像を読み込む"""
        self.after_preview.load_image(image_path)
        
    def clear(self):
        """両方のプレビューをクリア"""
        self.before_preview.clear()
        self.after_preview.clear()