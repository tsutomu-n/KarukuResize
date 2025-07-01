#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
KarukuResize ミニマル版 - シンプルで使いやすい画像圧縮ツール
Before/After比較を中心としたユーザーフレンドリーなUI
"""

import customtkinter as ctk
from tkinter import filedialog, messagebox
import tkinter as tk
from pathlib import Path
from PIL import Image, ImageTk
import threading
import time
import io
import os
import sys

# tkinterdnd2のインポート（オプション）
try:
    from tkinterdnd2 import DND_FILES, TkinterDnD
    TKDND_AVAILABLE = True
except ImportError:
    TKDND_AVAILABLE = False
    print("注意: tkinterdnd2が利用できません。ドラッグ&ドロップは無効です。")

# プロジェクトのresize_coreをインポート
try:
    from resize_core import resize_and_compress_image, format_file_size
except ImportError:
    print("エラー: resize_core.pyが見つかりません")
    sys.exit(1)

# 日本語フォント設定をインポート
try:
    from japanese_font_utils import JapaneseFontManager
    JAPANESE_FONT_AVAILABLE = True
except ImportError:
    JAPANESE_FONT_AVAILABLE = False
    print("注意: japanese_font_utilsが利用できません。デフォルトフォントを使用します。")

# カスタムフォント設定
ctk.set_appearance_mode("light")
ctk.set_default_color_theme("blue")


class ComparisonCanvas(ctk.CTkFrame):
    """Before/After比較表示用のカンバス"""
    
    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        
        self.configure(fg_color="#f0f0f0")
        
        # フォントマネージャーを初期化
        if JAPANESE_FONT_AVAILABLE:
            self.font_manager = JapaneseFontManager()
            self.font_family = self.font_manager.selected_font
        else:
            self.font_family = ""
        
        # 画像表示用Canvas（スクロールバー付き）
        self.canvas_frame = ctk.CTkFrame(self, fg_color="#f0f0f0")
        self.canvas_frame.pack(fill="both", expand=True)
        
        self.canvas = tk.Canvas(self.canvas_frame, highlightthickness=0, bg="#f0f0f0")
        
        # スクロールバー
        self.h_scrollbar = tk.Scrollbar(self.canvas_frame, orient="horizontal", command=self.canvas.xview)
        self.v_scrollbar = tk.Scrollbar(self.canvas_frame, orient="vertical", command=self.canvas.yview)
        self.canvas.configure(xscrollcommand=self.h_scrollbar.set, yscrollcommand=self.v_scrollbar.set)
        
        # 初期配置（スクロールバーは非表示）
        self.canvas.pack(fill="both", expand=True)
        
        # スプリッターの位置（0.0-1.0）
        self.split_position = 0.5
        
        # 画像データ
        self.before_image = None
        self.after_image = None
        self.before_size = 0
        self.after_size = 0
        
        # ズーム関連
        self.zoom_level = 1.0  # 1.0 = 100%
        self.fit_mode = True  # True: フィット表示, False: 実寸表示
        self.pan_start_x = 0
        self.pan_start_y = 0
        self.view_x = 0
        self.view_y = 0
        
        # 拡大鏡
        self.magnifier_size = 150
        self.magnifier_scale = 2.0
        self.magnifier_active = False
        
        # イベントバインド
        self.canvas.bind("<Button-1>", self.on_click)
        self.canvas.bind("<B1-Motion>", self.on_drag)
        self.canvas.bind("<Configure>", self.on_resize)
        self.canvas.bind("<Double-Button-1>", self.on_double_click)
        self.canvas.bind("<MouseWheel>", self.on_mousewheel)
        self.canvas.bind("<Button-4>", self.on_mousewheel)  # Linux
        self.canvas.bind("<Button-5>", self.on_mousewheel)  # Linux
        self.canvas.bind("<Button-3>", self.on_right_click)  # 右クリック
        self.canvas.bind("<Motion>", self.on_motion)
        self.canvas.bind("<Control-Motion>", self.on_ctrl_motion)
        self.canvas.bind("<Control-ButtonRelease-1>", self.on_ctrl_release)
        
        # 右クリックメニュー
        self.create_context_menu()
        
        # 初期メッセージ
        self.show_placeholder()
    
    def create_context_menu(self):
        """右クリックメニューを作成"""
        self.context_menu = tk.Menu(self.canvas, tearoff=0)
        self.context_menu.add_command(label="50%", command=lambda: self.set_zoom(0.5))
        self.context_menu.add_command(label="75%", command=lambda: self.set_zoom(0.75))
        self.context_menu.add_command(label="100%", command=lambda: self.set_zoom(1.0))
        self.context_menu.add_command(label="150%", command=lambda: self.set_zoom(1.5))
        self.context_menu.add_command(label="200%", command=lambda: self.set_zoom(2.0))
        self.context_menu.add_separator()
        self.context_menu.add_command(label="画面に合わせる", command=self.fit_to_window)
    
    def show_placeholder(self):
        """プレースホルダーメッセージを表示"""
        self.canvas.delete("all")
        width = self.canvas.winfo_width()
        height = self.canvas.winfo_height()
        if width > 1 and height > 1:
            self.canvas.create_text(
                width // 2, height // 2,
                text="画像をドラッグ&ドロップ\nまたは「ファイルを選択」",
                font=(self.font_family, 16),
                fill="#999999",
                anchor="center",
                justify="center"
            )
    
    def set_images(self, before_path=None, after_image=None, after_size=None, after_path=None):
        """画像をセット"""
        print(f"ComparisonCanvas.set_images called: before_path={before_path}, after_image={after_image}, after_size={after_size}, after_path={after_path}")
        
        if before_path:
            try:
                self.before_image = Image.open(before_path)
                self.before_size = Path(before_path).stat().st_size
                print(f"  before_image loaded: size={self.before_image.size}")
            except Exception as e:
                print(f"画像読み込みエラー: {e}")
                return
        
        if after_image is not None:
            self.after_image = after_image
            self.after_size = after_size
            print(f"  after_image set: {self.after_image}, size={self.after_image.size if self.after_image else 'None'}")
        elif after_path:
            try:
                self.after_image = Image.open(after_path)
                self.after_size = Path(after_path).stat().st_size if after_path else after_size
                print(f"  after_image loaded from path: size={self.after_image.size}")
            except Exception as e:
                print(f"After画像読み込みエラー: {e}")
        
        print(f"  before_image: {self.before_image}, after_image: {self.after_image}")
        self.update_display()
    
    def update_display(self):
        """表示を更新"""
        print(f"ComparisonCanvas.update_display called: before_image={self.before_image}, after_image={self.after_image}")
        self.canvas.delete("all")
        
        if not self.before_image:
            print("  No before_image, showing placeholder")
            self.show_placeholder()
            return
        
        # Canvas のサイズを取得
        canvas_width = self.canvas.winfo_width()
        canvas_height = self.canvas.winfo_height()
        
        if canvas_width <= 1 or canvas_height <= 1:
            return
        
        # 元画像のサイズ
        img_width, img_height = self.before_image.size
        
        # スケールの計算
        if self.fit_mode:
            # フィットモード：キャンバスに収まるように
            scale = min(canvas_width / img_width, (canvas_height - 60) / img_height) * 0.9
            self.zoom_level = scale
        else:
            # 実寸モード：ズームレベルを使用
            scale = self.zoom_level
        
        new_width = int(img_width * scale)
        new_height = int(img_height * scale)
        
        # スクロール領域の設定
        self.canvas.configure(scrollregion=(0, 0, max(new_width, canvas_width), max(new_height + 60, canvas_height)))
        
        # スクロールバーの表示/非表示
        if new_width > canvas_width:
            self.h_scrollbar.pack(side="bottom", fill="x")
            self.canvas.pack(side="left", fill="both", expand=True)
        else:
            self.h_scrollbar.pack_forget()
            
        if new_height + 60 > canvas_height:
            self.v_scrollbar.pack(side="right", fill="y")
            self.canvas.pack(side="left", fill="both", expand=True)
        else:
            self.v_scrollbar.pack_forget()
        
        # 中央に配置するためのオフセット（フィットモードの場合）
        if self.fit_mode or (new_width <= canvas_width and new_height <= canvas_height):
            x_offset = max((canvas_width - new_width) // 2, 0)
            y_offset = max((canvas_height - new_height - 60) // 2, 0)
        else:
            x_offset = self.view_x
            y_offset = self.view_y
        
        # Before画像を表示
        before_resized = self.before_image.resize((new_width, new_height), Image.Resampling.LANCZOS)
        self.before_photo = ImageTk.PhotoImage(before_resized)
        
        # After画像がある場合は合成
        if self.after_image:
            print(f"  Displaying after_image: size={self.after_image.size}, mode={self.after_image.mode}")
            after_resized = self.after_image.resize((new_width, new_height), Image.Resampling.LANCZOS)
            self.after_photo = ImageTk.PhotoImage(after_resized)
            print(f"  after_photo created: {self.after_photo}")
            
            # スプリット位置でマスク
            split_x = int(new_width * self.split_position)
            
            # Before側（左）
            self.canvas.create_image(x_offset, y_offset, anchor="nw", image=self.before_photo)
            
            # After側（右）をクリッピング
            if split_x < new_width:
                # 白い背景で右側を覆う
                self.canvas.create_rectangle(
                    x_offset + split_x, y_offset,
                    x_offset + new_width, y_offset + new_height,
                    fill="#f0f0f0", outline=""
                )
                # After画像を表示
                self.canvas.create_image(x_offset, y_offset, anchor="nw", image=self.after_photo)
                # 左側をマスク
                self.canvas.create_rectangle(
                    x_offset, y_offset,
                    x_offset + split_x, y_offset + new_height,
                    fill="#f0f0f0", outline=""
                )
                # Before画像を再度表示（左側のみ）
                self.canvas.create_image(x_offset, y_offset, anchor="nw", image=self.before_photo)
                
            # スプリッターライン
            self.canvas.create_line(
                x_offset + split_x, y_offset - 10,
                x_offset + split_x, y_offset + new_height + 10,
                fill="#4A90E2", width=3
            )
            
            # ドラッグハンドル
            handle_y = y_offset + new_height // 2
            self.canvas.create_oval(
                x_offset + split_x - 10, handle_y - 10,
                x_offset + split_x + 10, handle_y + 10,
                fill="#4A90E2", outline="white", width=2
            )
            
            # 矢印
            self.canvas.create_text(
                x_offset + split_x, handle_y,
                text="◀ ▶", fill="white", font=(self.font_family, 12, "bold")
            )
        else:
            # Before画像のみ表示
            self.canvas.create_image(x_offset, y_offset, anchor="nw", image=self.before_photo)
        
        # テキスト表示領域の背景（オプション）
        text_y = y_offset + new_height + 40
        
        # ファイルサイズと画像サイズ表示
        before_text = f"元画像: {format_file_size(self.before_size)} ({img_width}×{img_height})"
        self.canvas.create_text(
            x_offset + 10, text_y,
            text=before_text, anchor="w", font=(self.font_family, 12), fill="#333"
        )
        
        if self.after_image and self.after_size:
            reduction = (1 - self.after_size / self.before_size) * 100
            after_width, after_height = self.after_image.size
            after_text = f"圧縮後: {format_file_size(self.after_size)} ({after_width}×{after_height}) -{reduction:.1f}%"
            color = "#22C55E" if reduction > 50 else "#3B82F6" if reduction > 20 else "#EF4444"
            self.canvas.create_text(
                x_offset + new_width - 10, text_y,
                text=after_text, anchor="e", font=(self.font_family, 12, "bold"), fill=color
            )
        
        # ズームレベル表示
        zoom_text = f"ズーム: {int(self.zoom_level * 100)}%"
        self.canvas.create_text(
            canvas_width // 2, text_y,
            text=zoom_text, anchor="center", font=(self.font_family, 11), fill="#666"
        )
    
    def on_click(self, event):
        """クリック時の処理"""
        if self.fit_mode:
            # フィットモードではスプリッター操作
            self.update_split_position(event.x)
        else:
            # ズームモードではパン開始
            self.pan_start_x = event.x
            self.pan_start_y = event.y
            self.canvas.configure(cursor="fleur")  # 手のひらカーソル
    
    def on_drag(self, event):
        """ドラッグ時の処理"""
        if self.fit_mode:
            # フィットモードではスプリッター操作
            self.update_split_position(event.x)
        else:
            # ズームモードではパン
            dx = event.x - self.pan_start_x
            dy = event.y - self.pan_start_y
            self.canvas.xview_scroll(-dx, "units")
            self.canvas.yview_scroll(-dy, "units")
            self.pan_start_x = event.x
            self.pan_start_y = event.y
    
    def update_split_position(self, x):
        """スプリット位置を更新"""
        width = self.canvas.winfo_width()
        if width > 1:
            self.split_position = max(0.0, min(1.0, x / width))
            self.update_display()
    
    def on_resize(self, event):
        """リサイズ時の処理"""
        self.update_display()
    
    def on_double_click(self, event):
        """ダブルクリック時の処理"""
        if self.fit_mode:
            # 100%表示に切り替え
            self.fit_mode = False
            self.zoom_level = 1.0
        else:
            # フィット表示に切り替え
            self.fit_mode = True
        self.update_display()
    
    def on_mousewheel(self, event):
        """マウスホイール時の処理"""
        # ズーム率の計算
        if event.delta > 0 or event.num == 4:  # 上スクロール
            factor = 1.1
        else:  # 下スクロール
            factor = 0.9
        
        # ズームレベルを更新（10%〜300%の範囲）
        new_zoom = self.zoom_level * factor
        if 0.1 <= new_zoom <= 3.0:
            self.zoom_level = new_zoom
            self.fit_mode = False
            self.update_display()
    
    def on_right_click(self, event):
        """右クリック時の処理"""
        self.context_menu.post(event.x_root, event.y_root)
    
    def set_zoom(self, level):
        """ズームレベルを設定"""
        self.zoom_level = level
        self.fit_mode = False
        self.update_display()
    
    def fit_to_window(self):
        """画面に合わせる"""
        self.fit_mode = True
        self.update_display()
    
    def on_motion(self, event):
        """マウス移動時の処理"""
        if not self.fit_mode:
            self.canvas.configure(cursor="arrow")
    
    def on_ctrl_motion(self, event):
        """Ctrl+マウス移動時の処理（拡大鏡）"""
        if self.before_image and not self.fit_mode:
            self.magnifier_active = True
            self.show_magnifier(event.x, event.y)
    
    def on_ctrl_release(self, event):
        """Ctrl離した時の処理"""
        if self.magnifier_active:
            self.magnifier_active = False
            self.canvas.delete("magnifier")
    
    def show_magnifier(self, x, y):
        """拡大鏡を表示（改善版）"""
        self.canvas.delete("magnifier")
        
        if not self.before_image:
            return
        
        # キャンバス上の座標を画像座標に変換
        canvas_width = self.canvas.winfo_width()
        canvas_height = self.canvas.winfo_height()
        img_width, img_height = self.before_image.size
        
        # 現在の表示スケール
        scale = self.zoom_level
        new_width = int(img_width * scale)
        new_height = int(img_height * scale)
        
        # オフセット
        if self.fit_mode or (new_width <= canvas_width and new_height <= canvas_height):
            x_offset = max((canvas_width - new_width) // 2, 0)
            y_offset = max((canvas_height - new_height - 60) // 2, 0)
        else:
            # スクロール位置を考慮
            x_offset = -self.canvas.canvasx(0)
            y_offset = -self.canvas.canvasy(0)
        
        # 画像上の座標（より正確な計算）
        img_x = (x - x_offset) / scale
        img_y = (y - y_offset) / scale
        
        # 境界チェック
        if img_x < 0 or img_x >= img_width or img_y < 0 or img_y >= img_height:
            return
        
        # 拡大鏡のサイズ（画像座標）
        mag_size = self.magnifier_size / (scale * self.magnifier_scale)
        
        # 切り取り範囲
        left = max(0, int(img_x - mag_size / 2))
        top = max(0, int(img_y - mag_size / 2))
        right = min(img_width, int(img_x + mag_size / 2))
        bottom = min(img_height, int(img_y + mag_size / 2))
        
        if right > left and bottom > top:
            # Before/After両方の画像を切り取り
            crop_before = self.before_image.crop((left, top, right, bottom))
            
            # スプリット位置を考慮してBefore/Afterを表示
            if self.after_image and hasattr(self, 'split_position'):
                crop_after = self.after_image.crop((left, top, right, bottom))
                
                # 拡大画像を作成
                mag_img = Image.new('RGB', (self.magnifier_size, self.magnifier_size))
                
                # Before部分（左側）
                split_x_mag = int(self.magnifier_size * self.split_position)
                before_resized = crop_before.resize(
                    (self.magnifier_size, self.magnifier_size), 
                    Image.Resampling.LANCZOS  # より高品質
                )
                after_resized = crop_after.resize(
                    (self.magnifier_size, self.magnifier_size), 
                    Image.Resampling.LANCZOS
                )
                
                # 合成
                mag_img.paste(before_resized.crop((0, 0, split_x_mag, self.magnifier_size)), (0, 0))
                mag_img.paste(after_resized.crop((split_x_mag, 0, self.magnifier_size, self.magnifier_size)), (split_x_mag, 0))
                
                # スプリットライン
                self.magnifier_photo = ImageTk.PhotoImage(mag_img)
            else:
                # Beforeのみ
                crop_before = crop_before.resize(
                    (self.magnifier_size, self.magnifier_size), 
                    Image.Resampling.LANCZOS
                )
                self.magnifier_photo = ImageTk.PhotoImage(crop_before)
            
            # 拡大鏡の位置調整（画面端では内側に表示）
            mag_x = x
            mag_y = y
            if x + self.magnifier_size // 2 > canvas_width - 10:
                mag_x = canvas_width - self.magnifier_size // 2 - 10
            elif x - self.magnifier_size // 2 < 10:
                mag_x = self.magnifier_size // 2 + 10
            if y + self.magnifier_size // 2 > canvas_height - 10:
                mag_y = canvas_height - self.magnifier_size // 2 - 10
            elif y - self.magnifier_size // 2 < 10:
                mag_y = self.magnifier_size // 2 + 10
            
            # 拡大鏡の背景（角丸風）
            self.canvas.create_oval(
                mag_x - self.magnifier_size // 2 - 3,
                mag_y - self.magnifier_size // 2 - 3,
                mag_x + self.magnifier_size // 2 + 3,
                mag_y + self.magnifier_size // 2 + 3,
                fill="white", outline="black", width=2, tags="magnifier"
            )
            
            # 拡大画像を表示
            self.canvas.create_image(
                mag_x, mag_y, anchor="center", 
                image=self.magnifier_photo, tags="magnifier"
            )
            
            # スプリットライン（拡大鏡内）
            if self.after_image:
                split_x_mag = int(self.magnifier_size * self.split_position)
                self.canvas.create_line(
                    mag_x - self.magnifier_size // 2 + split_x_mag,
                    mag_y - self.magnifier_size // 2,
                    mag_x - self.magnifier_size // 2 + split_x_mag,
                    mag_y + self.magnifier_size // 2,
                    fill="#4A90E2", width=2, tags="magnifier"
                )
            
            # クロスヘア
            self.canvas.create_line(
                mag_x - self.magnifier_size // 2 + 10, mag_y,
                mag_x + self.magnifier_size // 2 - 10, mag_y,
                fill="red", width=1, tags="magnifier"
            )
            self.canvas.create_line(
                mag_x, mag_y - self.magnifier_size // 2 + 10,
                mag_x, mag_y + self.magnifier_size // 2 - 10,
                fill="red", width=1, tags="magnifier"
            )
            
            # 座標情報（デバッグ用、後で削除可）
            info_text = f"({int(img_x)}, {int(img_y)})"
            self.canvas.create_text(
                mag_x, mag_y + self.magnifier_size // 2 + 15,
                text=info_text, font=(self.font_family, 10), fill="black", tags="magnifier"
            )


class MinimalResizeApp(ctk.CTk if not TKDND_AVAILABLE else TkinterDnD.Tk):
    """ミニマル版リサイズアプリケーション"""
    
    def __init__(self):
        super().__init__()
        
        self.title("KarukuResize - 画像を軽く")
        self.geometry("800x600")
        self.minsize(600, 400)
        
        # 変数の初期化
        self.input_path = None
        self.input_files = []  # バッチ処理用のファイルリスト
        self.quality = 85
        self.output_format = "original"  # 出力形式
        self.resize_mode = "none"  # リサイズモード
        self.resize_width = 800  # デフォルト幅
        self.target_size_kb = 0  # 目標ファイルサイズ（KB）、0は無制限
        self.processing = False
        self.cancel_requested = False  # キャンセルフラグ
        self.processed_count = 0  # 処理済みファイル数
        self.failed_count = 0  # 失敗ファイル数
        
        # フォントマネージャーを初期化
        if JAPANESE_FONT_AVAILABLE:
            self.font_manager = JapaneseFontManager()
        
        # UIを構築
        self.setup_ui()
        
        # ドラッグ&ドロップを設定
        self.setup_drag_drop()
        
        # キーボードショートカットを設定
        self.setup_keyboard_shortcuts()
    
    def setup_ui(self):
        """UIをセットアップ"""
        # メインコンテナ
        main_container = ctk.CTkFrame(self, fg_color="transparent")
        main_container.pack(fill="both", expand=True, padx=20, pady=20)
        
        # タイトル
        if JAPANESE_FONT_AVAILABLE:
            title_font = ctk.CTkFont(family=self.font_manager.selected_font, size=24, weight="bold")
        else:
            title_font = ctk.CTkFont(size=24, weight="bold")
            
        title_label = ctk.CTkLabel(
            main_container,
            text="画像を軽く、品質はそのまま",
            font=title_font
        )
        title_label.pack(pady=(0, 20))
        
        # 比較キャンバス
        self.comparison = ComparisonCanvas(main_container, height=300)
        self.comparison.pack(fill="both", expand=True, pady=(0, 20))
        
        # コントロールフレーム
        control_frame = ctk.CTkFrame(main_container, fg_color="transparent")
        control_frame.pack(fill="x")
        
        # 品質スライダー
        quality_frame = ctk.CTkFrame(control_frame, fg_color="transparent")
        quality_frame.pack(fill="x", pady=(0, 20))
        
        # 日本語フォントを取得
        if JAPANESE_FONT_AVAILABLE:
            label_font = ctk.CTkFont(family=self.font_manager.selected_font, size=14)
            button_font = ctk.CTkFont(family=self.font_manager.selected_font, size=14)
            small_font = ctk.CTkFont(family=self.font_manager.selected_font, size=12)
        else:
            label_font = ctk.CTkFont(size=14)
            button_font = ctk.CTkFont(size=14)
            small_font = ctk.CTkFont(size=12)
        
        ctk.CTkLabel(
            quality_frame,
            text="品質:",
            font=label_font
        ).pack(side="left", padx=(0, 10))
        
        self.quality_slider = ctk.CTkSlider(
            quality_frame,
            from_=1,
            to=100,
            number_of_steps=99,
            command=self.on_quality_change
        )
        self.quality_slider.set(85)
        self.quality_slider.pack(side="left", fill="x", expand=True, padx=(0, 10))
        
        self.quality_label = ctk.CTkLabel(
            quality_frame,
            text="85%",
            font=ctk.CTkFont(family=self.font_manager.selected_font if JAPANESE_FONT_AVAILABLE else "", size=14, weight="bold"),
            width=50
        )
        self.quality_label.pack(side="left", padx=(0, 10))
        
        # プレビューボタン
        self.preview_button = ctk.CTkButton(
            quality_frame,
            text="🔄 プレビュー",
            command=self.generate_preview_manual,
            font=small_font,
            height=30,
            width=100,
            state="disabled",
            fg_color="#9CA3AF",
            hover_color="#9CA3AF"
        )
        self.preview_button.pack(side="left")
        
        # 形式選択フレーム
        format_frame = ctk.CTkFrame(control_frame, fg_color="transparent")
        format_frame.pack(fill="x", pady=(0, 10))
        
        ctk.CTkLabel(
            format_frame,
            text="形式:",
            font=label_font
        ).pack(side="left", padx=(0, 10))
        
        self.format_var = ctk.StringVar(value="元の形式")
        self.format_menu = ctk.CTkOptionMenu(
            format_frame,
            values=["元の形式", "JPEG", "PNG", "WebP"],
            variable=self.format_var,
            command=self.on_format_change,
            width=120
        )
        self.format_menu.pack(side="left")
        
        # リサイズ設定フレーム
        resize_frame = ctk.CTkFrame(control_frame, fg_color="transparent")
        resize_frame.pack(fill="x", pady=(0, 20))
        
        ctk.CTkLabel(
            resize_frame,
            text="サイズ:",
            font=label_font
        ).pack(side="left", padx=(0, 10))
        
        self.resize_var = ctk.StringVar(value="変更しない")
        self.resize_menu = ctk.CTkOptionMenu(
            resize_frame,
            values=["変更しない", "幅を指定"],
            variable=self.resize_var,
            command=self.on_resize_change,
            width=120
        )
        self.resize_menu.pack(side="left", padx=(0, 10))
        
        # 幅入力フィールド（最初は非表示）
        self.width_entry = ctk.CTkEntry(
            resize_frame,
            placeholder_text="800",
            width=80,
            font=label_font
        )
        self.width_entry.insert(0, "800")  # デフォルト値を設定
        # 幅変更時のコールバックを設定
        self.width_entry.bind('<KeyRelease>', self.on_width_change)
        self.width_entry.bind('<FocusOut>', self.on_width_change)
        # 最初は非表示
        
        self.width_label = ctk.CTkLabel(
            resize_frame,
            text="px",
            font=label_font
        )
        # 最初は非表示
        
        # ボタンフレーム
        button_frame = ctk.CTkFrame(control_frame, fg_color="transparent")
        button_frame.pack(fill="x")
        
        # ファイル選択ボタン
        self.select_button = ctk.CTkButton(
            button_frame,
            text="📂 ファイルを選択",
            command=self.select_file,
            font=button_font,
            height=40,
            fg_color="#3B82F6",
            hover_color="#2563EB"
        )
        self.select_button.pack(side="left", padx=(0, 10))
        
        # 保存先ボタン（小さめ）
        self.output_button = ctk.CTkButton(
            button_frame,
            text="📁 保存先",
            command=self.select_output,
            font=small_font,
            height=40,
            width=100,
            fg_color="#6B7280",
            hover_color="#4B5563"
        )
        self.output_button.pack(side="left", padx=(0, 10))
        
        # 目標サイズ入力（オプション）
        self.size_frame = ctk.CTkFrame(button_frame, fg_color="transparent")
        self.size_frame.pack(side="left", padx=(10, 0))
        
        ctk.CTkLabel(
            self.size_frame,
            text="目標:",
            font=small_font
        ).pack(side="left", padx=(0, 5))
        
        self.target_size_entry = ctk.CTkEntry(
            self.size_frame,
            placeholder_text="KB",
            width=60,
            font=small_font
        )
        self.target_size_entry.pack(side="left")
        
        # 目標サイズ変更時のコールバック
        self.target_size_entry.bind('<KeyRelease>', self.on_target_size_change)
        self.target_size_entry.bind('<FocusOut>', self.on_target_size_change)
        
        ctk.CTkLabel(
            self.size_frame,
            text="KB以下",
            font=small_font
        ).pack(side="left", padx=(2, 0))
        
        # スペーサー
        ctk.CTkFrame(button_frame, fg_color="transparent").pack(side="left", fill="x", expand=True)
        
        # 圧縮開始ボタン
        self.compress_button = ctk.CTkButton(
            button_frame,
            text="✨ 処理開始",
            command=self.start_compression,
            font=ctk.CTkFont(family=self.font_manager.selected_font if JAPANESE_FONT_AVAILABLE else "", size=16, weight="bold"),
            height=40,
            width=150,
            state="disabled",
            fg_color="#D1D5DB",  # 無効時は薄いグレー
            hover_color="#D1D5DB",
            text_color="#9CA3AF"
        )
        self.compress_button.pack(side="right")
        
        # プログレスバー（最初は非表示）
        self.progress_bar = ctk.CTkProgressBar(main_container)
        self.progress_bar.set(0)
        # プログレスバーは最初は表示しない
        
        # ステータスラベル
        self.status_label = ctk.CTkLabel(
            main_container,
            text="📌 ステップ1: 画像ファイルを選択してください",
            font=small_font,
            text_color="#F59E0B"  # オレンジで目立たせる
        )
        self.status_label.pack(pady=(10, 0))
        
        # ヒントラベル（小さめ）
        self.hint_label = ctk.CTkLabel(
            main_container,
            text="ドラッグ&ドロップまたは「ファイルを選択」ボタンをクリック",
            font=ctk.CTkFont(family=self.font_manager.selected_font if JAPANESE_FONT_AVAILABLE else "", size=11),
            text_color="#9CA3AF"
        )
        self.hint_label.pack(pady=(2, 0))
        
        # ズーム操作ヒント
        self.zoom_hint_label = ctk.CTkLabel(
            main_container,
            text="🔍 ダブルクリック: 100%/フィット切替 | マウスホイール: ズーム | Ctrl+マウス: 拡大鏡",
            font=ctk.CTkFont(family=self.font_manager.selected_font if JAPANESE_FONT_AVAILABLE else "", size=10),
            text_color="#9CA3AF"
        )
        # 画像読み込み後に表示
        
        # 品質警告ラベル（低品質時のみ表示）
        self.quality_warning_label = ctk.CTkLabel(
            main_container,
            text="⚠️ 品質が非常に低く設定されています。画質が大幅に劣化します。",
            font=ctk.CTkFont(family=self.font_manager.selected_font if JAPANESE_FONT_AVAILABLE else "", size=11),
            text_color="#EF4444"
        )
        # 初期は非表示
        
        # PNG形式警告ラベル
        self.png_format_label = ctk.CTkLabel(
            main_container,
            text="ℹ️ PNG形式は可逆圧縮のため、品質設定は効果がありません。",
            font=ctk.CTkFont(family=self.font_manager.selected_font if JAPANESE_FONT_AVAILABLE else "", size=11),
            text_color="#3B82F6"
        )
        # 初期は非表示
    
    def setup_drag_drop(self):
        """ドラッグ&ドロップの設定"""
        # tkinterdnd2が利用可能な場合のみ設定
        if TKDND_AVAILABLE:
            try:
                self.comparison.canvas.drop_target_register(DND_FILES)
                self.comparison.canvas.dnd_bind("<<Drop>>", self.on_drop)
            except Exception as e:
                print(f"ドラッグ&ドロップの設定に失敗: {e}")
    
    def on_drop(self, event):
        """ドロップ時の処理"""
        files = self.tk.splitlist(event.data)
        if files:
            if len(files) == 1:
                # 単一ファイル
                self.load_file(files[0])
            else:
                # 複数ファイル
                self.load_files(files)
    
    def select_file(self):
        """ファイル選択ダイアログ（複数選択対応）"""
        file_paths = filedialog.askopenfilenames(
            title="画像を選択（複数選択可）",
            filetypes=[
                ("画像ファイル", "*.jpg *.jpeg *.png *.webp"),
                ("すべてのファイル", "*.*")
            ]
        )
        if file_paths:
            if len(file_paths) == 1:
                # 単一ファイルモード
                self.load_file(file_paths[0])
            else:
                # バッチ処理モード
                self.load_files(file_paths)
    
    def load_file(self, file_path):
        """ファイルを読み込み"""
        self.input_path = file_path
        self.comparison.set_images(before_path=file_path)
        
        # ボタンを有効化して色を変更
        self.compress_button.configure(
            state="normal",
            fg_color="#3B82F6",  # 鮮やかな青
            hover_color="#2563EB",  # ホバー時は濃い青
            text_color="white"
        )
        
        # プレビューボタンを有効化
        self.preview_button.configure(
            state="normal",
            fg_color="#10B981",
            hover_color="#059669"
        )
        
        # ステータス更新
        self.status_label.configure(
            text=f"✅ 選択済み: {Path(file_path).name}",
            text_color="#22C55E"  # 緑で成功を示す
        )
        self.hint_label.configure(
            text="📌 ステップ2: 必要に応じて品質・形式・サイズを調整し、処理開始をクリック"
        )
        
        # ズーム操作ヒントを表示
        self.zoom_hint_label.pack(pady=(2, 0))
        
        # バッチモードフラグをクリア
        self.input_files = []
        
        # 軽量プレビューを生成
        self.generate_preview_light()
    
    def load_files(self, file_paths):
        """複数ファイルを読み込み（バッチ処理）"""
        self.input_files = list(file_paths)
        self.input_path = None  # 単一ファイルモードをクリア
        
        # UIを更新
        self.comparison.show_placeholder()
        
        # ボタンを有効化
        self.compress_button.configure(
            state="normal",
            fg_color="#3B82F6",
            hover_color="#2563EB",
            text_color="white"
        )
        
        # プレビューボタンを無効化（バッチモード）
        self.preview_button.configure(
            state="disabled",
            fg_color="#9CA3AF",
            hover_color="#9CA3AF"
        )
        
        # ステータス更新
        self.status_label.configure(
            text=f"✅ {len(self.input_files)}個のファイルを選択しました",
            text_color="#22C55E"
        )
        self.hint_label.configure(
            text="📌 バッチ処理モード: 処理開始をクリックして一括処理を開始"
        )
        
        # ズーム操作ヒントを非表示
        self.zoom_hint_label.pack_forget()
        
        # ファイルリストを表示
        self.show_file_list()
    
    def show_file_list(self):
        """選択されたファイルのリストを表示"""
        # ComparisonCanvasの代わりにファイルリストを表示
        if hasattr(self, 'file_list_frame'):
            self.file_list_frame.destroy()
        
        self.file_list_frame = ctk.CTkFrame(self.comparison.canvas_frame)
        self.file_list_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # ヘッダー
        header_label = ctk.CTkLabel(
            self.file_list_frame,
            text=f"選択されたファイル ({len(self.input_files)}個)",
            font=ctk.CTkFont(family=self.font_manager.selected_font if JAPANESE_FONT_AVAILABLE else "", size=14, weight="bold")
        )
        header_label.pack(pady=(0, 10))
        
        # スクロール可能なリスト
        self.file_listbox = ctk.CTkTextbox(
            self.file_list_frame,
            height=250,
            font=ctk.CTkFont(family=self.font_manager.selected_font if JAPANESE_FONT_AVAILABLE else "", size=12)
        )
        self.file_listbox.pack(fill="both", expand=True)
        
        # ファイルリストを表示
        total_size = 0
        for i, file_path in enumerate(self.input_files, 1):
            path = Path(file_path)
            size = path.stat().st_size
            total_size += size
            self.file_listbox.insert("end", f"{i}. {path.name} ({format_file_size(size)})\n")
        
        self.file_listbox.configure(state="disabled")
        
        # 合計サイズ表示
        total_label = ctk.CTkLabel(
            self.file_list_frame,
            text=f"合計サイズ: {format_file_size(total_size)}",
            font=ctk.CTkFont(family=self.font_manager.selected_font if JAPANESE_FONT_AVAILABLE else "", size=12)
        )
        total_label.pack(pady=(10, 0))
    
    def select_output(self):
        """出力先を選択"""
        if not self.input_path:
            return
        
        input_path = Path(self.input_path)
        
        # 出力形式に応じた拡張子を決定
        if self.output_format != "original":
            ext_map = {"jpeg": ".jpg", "png": ".png", "webp": ".webp"}
            new_ext = ext_map.get(self.output_format, input_path.suffix)
            initial_name = f"{input_path.stem}_compressed{new_ext}"
        else:
            initial_name = f"{input_path.stem}_compressed{input_path.suffix}"
        
        output_path = filedialog.asksaveasfilename(
            title="保存先を選択",
            defaultextension=input_path.suffix,
            initialfile=initial_name,
            filetypes=[
                ("JPEG", "*.jpg"),
                ("PNG", "*.png"),
                ("WebP", "*.webp"),
                ("元の形式", f"*{input_path.suffix}")
            ]
        )
        
        if output_path:
            self.output_path = output_path
            self.hint_label.configure(
                text=f"💾 保存先: {Path(output_path).name}",
                text_color="#3B82F6"  # 青で情報表示
            )
    
    def on_quality_change(self, value):
        """品質スライダー変更時"""
        self.quality = int(value)
        self.quality_label.configure(text=f"{self.quality}%")
        
        # 品質警告の表示/非表示
        if self.quality <= 10:
            self.quality_warning_label.pack(pady=(5, 0))
        else:
            self.quality_warning_label.pack_forget()
        
        # プレビューを更新（遅延実行）
        if hasattr(self, '_preview_timer'):
            self.after_cancel(self._preview_timer)
        self._preview_timer = self.after(500, self.generate_preview)
    
    def on_format_change(self, value):
        """形式選択変更時"""
        format_map = {
            "元の形式": "original",
            "JPEG": "jpeg",
            "PNG": "png",
            "WebP": "webp"
        }
        self.output_format = format_map.get(value, "original")
        
        # PNG形式の警告表示
        if self.output_format == "png" or (self.output_format == "original" and self.input_path and self.input_path.lower().endswith('.png')):
            self.png_format_label.pack(pady=(5, 0))
        else:
            self.png_format_label.pack_forget()
        
        self.generate_preview()
    
    def on_resize_change(self, value):
        """リサイズモード変更時"""
        if value == "変更しない":
            self.resize_mode = "none"
            # 幅入力を非表示
            self.width_entry.pack_forget()
            self.width_label.pack_forget()
        else:
            self.resize_mode = "width"
            # 幅入力を表示
            self.width_entry.pack(side="left", padx=(0, 5))
            self.width_label.pack(side="left")
            # 幅変更時のコールバックを設定
            self.width_entry.bind('<KeyRelease>', self.on_width_change)
        self.generate_preview()
    
    def on_width_change(self, event):
        """幅入力変更時"""
        try:
            self.resize_width = int(self.width_entry.get())
            # プレビューを更新（遅延実行）
            if hasattr(self, '_width_timer'):
                self.after_cancel(self._width_timer)
            self._width_timer = self.after(500, self.generate_preview)
        except ValueError:
            # 無効な入力は無視
            pass
    
    def on_target_size_change(self, event):
        """目標サイズ変更時"""
        if self.input_path and not self.processing:
            # 遅延実行でプレビューを更新
            if hasattr(self, '_target_size_timer'):
                self.after_cancel(self._target_size_timer)
            self._target_size_timer = self.after(1000, self.generate_preview_light)
    
    def generate_preview_light(self):
        """軽量プレビューを生成（画像選択直後）"""
        if not self.input_path or self.processing:
            return
        
        # 別スレッドで実行
        thread = threading.Thread(target=self._generate_preview_thread, args=(False,), daemon=True)
        thread.start()
    
    def generate_preview_manual(self):
        """手動プレビューを生成（詳細・目標サイズ対応）"""
        if not self.input_path or self.processing:
            return
        
        # プレビューボタンの状態を変更
        self.preview_button.configure(
            text="⏳ 生成中...",
            state="disabled",
            fg_color="#6B7280"
        )
        
        # 別スレッドで実行
        thread = threading.Thread(target=self._generate_preview_thread, args=(True,), daemon=True)
        thread.start()
    
    def generate_preview(self):
        """既存のプレビュー生成（互換性のため）"""
        self.generate_preview_light()
    
    def _generate_preview_thread(self, detailed=False):
        """プレビュー生成スレッド"""
        start_time = time.time()
        preview_info = {}
        
        try:
            # 元画像を読み込み
            source_image = Image.open(self.input_path)
            original_size = Path(self.input_path).stat().st_size
            
            # 目標サイズを取得
            target_size_kb = 0
            if detailed:
                try:
                    target_size_text = self.target_size_entry.get().strip()
                    if target_size_text:
                        target_size_kb = int(target_size_text)
                except ValueError:
                    pass
            
            # 出力フォーマットを決定
            if self.output_format == "original":
                # 品質が50以下の場合、PNGでもJPEGでプレビューして品質劣化を見せる
                if self.input_path.lower().endswith('.png') and self.quality > 50:
                    output_format = "png"
                elif self.input_path.lower().endswith('.webp'):
                    output_format = "webp"
                else:
                    # デフォルトはJPEG（品質の違いが見えやすい）
                    output_format = "jpeg"
            else:
                output_format = self.output_format
            
            # リサイズ値を取得
            resize_value = None
            if self.resize_mode == "width":
                # 入力フィールドから最新の値を取得
                try:
                    if self.width_entry.get():
                        resize_value = int(self.width_entry.get())
                    else:
                        resize_value = self.resize_width if hasattr(self, 'resize_width') else 800
                except ValueError:
                    resize_value = self.resize_width if hasattr(self, 'resize_width') else 800
            
            # 目標サイズが設定されている場合は品質自動調整
            if detailed and target_size_kb > 0:
                result = self._generate_preview_with_target_size(
                    source_image, target_size_kb, output_format, resize_value
                )
                if result:
                    after_image, after_size, optimized_quality, process_time = result
                    preview_info = {
                        "optimized_quality": optimized_quality,
                        "target_achieved": after_size <= target_size_kb * 1024,
                        "process_time": process_time
                    }
                else:
                    raise Exception("目標サイズでのプレビュー生成に失敗")
            else:
                # 通常のプレビュー
                output_buffer = io.BytesIO()
                
                # パラメータの設定
                actual_resize_mode = "none" if self.resize_mode == "none" else "width"
                actual_resize_value = resize_value if self.resize_mode == "width" and resize_value else None
                
                # デバッグ情報を出力
                print(f"プレビュー処理: resize_mode={self.resize_mode} → {actual_resize_mode}, resize_value={resize_value} → {actual_resize_value}, quality={self.quality}, format={output_format}")
                
                # メモリベース処理を実行
                success, error_msg = resize_and_compress_image(
                    source_image=source_image,
                    output_buffer=output_buffer,
                    resize_mode=actual_resize_mode,
                    resize_value=actual_resize_value,
                    quality=self.quality,
                    output_format=output_format,
                    optimize=True
                )
                
                if success:
                    # バッファのデータを保持
                    image_data = output_buffer.getvalue()
                    after_size = len(image_data)
                    
                    # 独立したバッファから画像を開く
                    output_buffer.seek(0)
                    after_image = Image.open(output_buffer)
                    # 画像データを完全にメモリに読み込む
                    after_image.load()
                    # さらに安全のため、独立したコピーを作成
                    after_image = after_image.copy()
                    
                    preview_info = {
                        "process_time": time.time() - start_time
                    }
                    print(f"プレビュー成功: サイズ={after_size}bytes, 処理時間={preview_info['process_time']:.2f}秒")
                    print(f"  after_image: {after_image}, size={after_image.size}, mode={after_image.mode}")
                else:
                    error_detail = f"プレビュー生成に失敗: {error_msg or 'Unknown error'}"
                    print(f"エラー詳細: resize_mode={actual_resize_mode}, resize_value={actual_resize_value}, error={error_msg}")
                    raise Exception(error_detail)
            
            # 詳細情報の計算
            reduction = (1 - after_size / original_size) * 100
            preview_info.update({
                "original_size": original_size,
                "after_size": after_size,
                "reduction": reduction,
                "original_dimensions": source_image.size,
                "after_dimensions": after_image.size,
                "format": output_format.upper()
            })
            
            # UIを更新
            self.after(0, lambda: self._update_preview_ui(
                after_image, after_size, preview_info, detailed
            ))
            
        except Exception as e:
            error_msg = str(e)
            print(f"プレビューエラー（詳細）: {error_msg}")
            
            # フォールバック: 一時ファイルを使った処理を試行
            if detailed:
                try:
                    fallback_result = self._generate_preview_fallback(source_image, preview_info.get("original_size", 0))
                    if fallback_result:
                        after_image, after_size, fallback_info = fallback_result
                        fallback_info["process_time"] = time.time() - start_time
                        self.after(0, lambda: self._update_preview_ui(after_image, after_size, fallback_info, detailed))
                        return
                except Exception as fallback_error:
                    print(f"フォールバック処理も失敗: {fallback_error}")
            
            self.after(0, lambda: self._handle_preview_error(error_msg, detailed))
    
    def _generate_preview_fallback(self, source_image, original_size):
        """フォールバック: 一時ファイルを使ったプレビュー生成"""
        import tempfile
        import os
        
        try:
            # RGBA画像をRGBに変換
            if source_image.mode == 'RGBA':
                rgb_image = Image.new('RGB', source_image.size, (255, 255, 255))
                rgb_image.paste(source_image, mask=source_image.split()[3])
                source_image = rgb_image
            elif source_image.mode not in ('RGB', 'L'):
                source_image = source_image.convert('RGB')
            
            # 一時ファイルを作成
            with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as temp_input:
                source_image.save(temp_input.name, 'JPEG', quality=95)
                temp_input_path = temp_input.name
            
            with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as temp_output:
                temp_output_path = temp_output.name
            
            # ファイルベース処理を実行
            if self.resize_mode == "width" and hasattr(self, 'resize_width'):
                result = resize_and_compress_image(
                    source_path=temp_input_path,
                    dest_path=temp_output_path,
                    target_width=self.resize_width,
                    quality=self.quality,
                    format=self.output_format if self.output_format != "original" else "jpeg"
                )
            else:
                result = resize_and_compress_image(
                    source_path=temp_input_path,
                    dest_path=temp_output_path,
                    quality=self.quality,
                    format=self.output_format if self.output_format != "original" else "jpeg"
                )
            
            if result and result[0]:  # 成功
                # 結果画像を読み込み
                after_image = Image.open(temp_output_path)
                after_size = Path(temp_output_path).stat().st_size
                
                # 情報を計算
                reduction = (1 - after_size / original_size) * 100 if original_size > 0 else 0
                fallback_info = {
                    "original_size": original_size,
                    "after_size": after_size,
                    "reduction": reduction,
                    "original_dimensions": source_image.size,
                    "after_dimensions": after_image.size,
                    "format": "JPEG (フォールバック)",
                    "fallback": True
                }
                
                return after_image, after_size, fallback_info
            
        except Exception as e:
            print(f"フォールバック処理エラー: {e}")
        finally:
            # 一時ファイルを削除
            try:
                if 'temp_input_path' in locals():
                    os.unlink(temp_input_path)
                if 'temp_output_path' in locals():
                    os.unlink(temp_output_path)
            except:
                pass
        
        return None
    
    def _generate_preview_with_target_size(self, source_image, target_size_kb, output_format, resize_value):
        """目標サイズに合わせてプレビューを生成"""
        target_bytes = target_size_kb * 1024
        min_quality = 10
        max_quality = 95
        best_quality = self.quality
        best_result = None
        
        start_time = time.time()
        
        for attempt in range(7):  # 最大7回試行
            output_buffer = io.BytesIO()
            
            # パラメータの設定
            actual_resize_mode = "none" if self.resize_mode == "none" else "width"
            actual_resize_value = resize_value if self.resize_mode == "width" and resize_value else None
            
            # メモリベース処理を実行
            success, _ = resize_and_compress_image(
                source_image=source_image,
                output_buffer=output_buffer,
                resize_mode=actual_resize_mode,
                resize_value=actual_resize_value,
                quality=best_quality,
                output_format=output_format,
                optimize=True
            )
            
            if success:
                size = len(output_buffer.getvalue())
                
                if size <= target_bytes or attempt == 6:  # 目標達成または最終試行
                    output_buffer.seek(0)
                    after_image = Image.open(output_buffer)
                    # 画像データを完全にメモリに読み込む
                    after_image.load()
                    # 独立したコピーを作成
                    after_image = after_image.copy()
                    process_time = time.time() - start_time
                    return after_image, size, best_quality, process_time
                
                # 二分探索で品質を調整
                if size > target_bytes:
                    max_quality = best_quality - 1
                else:
                    min_quality = best_quality + 1
                
                best_quality = (min_quality + max_quality) // 2
                
                if best_quality < 10:
                    break
        
        return None
    
    def _update_preview_ui(self, after_image, after_size, info, detailed):
        """プレビューUIを更新"""
        # デバッグ情報
        print(f"_update_preview_ui called: after_image={after_image}, after_size={after_size}")
        if after_image:
            print(f"  after_image details: size={after_image.size}, mode={after_image.mode}")
        
        # 画像を表示
        self.comparison.set_images(
            after_image=after_image,
            after_size=after_size
        )
        
        # 詳細プレビューの場合は追加情報を表示
        if detailed:
            self._show_preview_details(info)
            
            # プレビューボタンを復元
            self.preview_button.configure(
                text="✅ 完了",
                state="normal",
                fg_color="#10B981"
            )
            
            # 2秒後にボタンテキストを戻す
            self.after(2000, lambda: self.preview_button.configure(text="🔄 プレビュー"))
    
    def _handle_preview_error(self, error_msg, detailed):
        """プレビューエラーを処理"""
        print(f"プレビューエラー: {error_msg}")
        
        if detailed:
            # プレビューボタンを復元
            self.preview_button.configure(
                text="❌ エラー",
                state="normal",
                fg_color="#EF4444"
            )
            
            # 2秒後にボタンテキストを戻す
            self.after(2000, lambda: self.preview_button.configure(
                text="🔄 プレビュー",
                fg_color="#10B981"
            ))
    
    def _show_preview_details(self, info):
        """プレビューの詳細情報を表示"""
        details = []
        
        # 基本情報
        details.append(f"📏 {info['original_dimensions'][0]}×{info['original_dimensions'][1]} → {info['after_dimensions'][0]}×{info['after_dimensions'][1]}")
        details.append(f"💾 {format_file_size(info['original_size'])} → {format_file_size(info['after_size'])} (-{info['reduction']:.1f}%)")
        details.append(f"🎨 形式: {info['format']} | ⏱️ {info['process_time']:.2f}秒")
        
        # 最適化情報
        if 'optimized_quality' in info:
            details.append(f"🎯 最適品質: {info['optimized_quality']}%")
            if info['target_achieved']:
                details.append("✅ 目標サイズ達成")
            else:
                details.append("⚠️ 目標サイズ未達成")
        
        # フォールバック情報
        if info.get('fallback'):
            details.append("🔄 フォールバック処理")
        
        # ヒントラベルに詳細情報を表示
        detail_text = " | ".join(details)
        self.hint_label.configure(
            text=detail_text,
            text_color="#3B82F6"
        )
    
    def start_compression(self):
        """圧縮を開始"""
        if self.processing:
            return
        
        # 単一ファイルかバッチ処理かを判定
        if self.input_path:
            # 単一ファイルモード
            self._start_single_compression()
        elif self.input_files:
            # バッチ処理モード
            self._start_batch_compression()
        else:
            return
    
    def _start_single_compression(self):
        """単一ファイルの圧縮を開始"""
        
        # 出力先が未設定の場合はデフォルトを使用
        if not hasattr(self, 'output_path'):
            input_path = Path(self.input_path)
            if self.output_format != "original":
                ext_map = {"jpeg": ".jpg", "png": ".png", "webp": ".webp"}
                new_ext = ext_map.get(self.output_format, input_path.suffix)
                self.output_path = str(input_path.parent / f"{input_path.stem}_compressed{new_ext}")
            else:
                self.output_path = str(input_path.parent / f"{input_path.stem}_compressed{input_path.suffix}")
        
        # 目標サイズを取得
        try:
            target_size_text = self.target_size_entry.get().strip()
            if target_size_text:
                self.target_size_kb = int(target_size_text)
            else:
                self.target_size_kb = 0
        except ValueError:
            self.target_size_kb = 0
        
        self.processing = True
        self.compress_button.configure(
            state="disabled", 
            text="処理中...",
            fg_color="#D1D5DB",
            hover_color="#D1D5DB",
            text_color="#9CA3AF"
        )
        self.progress_bar.pack(fill="x", pady=(10, 0))
        self.progress_bar.set(0.5)
        
        # ステータス更新
        self.status_label.configure(
            text="⏳ 処理中です...",
            text_color="#3B82F6"
        )
        self.hint_label.configure(text="")
        
        # 別スレッドで実行
        thread = threading.Thread(target=self._compress_thread, daemon=True)
        thread.start()
    
    def _compress_thread(self):
        """圧縮処理スレッド"""
        try:
            # 出力フォーマットを決定
            format_for_core = "original"
            if self.output_format != "original":
                format_for_core = self.output_format
            
            # パラメータの統一設定
            actual_resize_mode = "none" if self.resize_mode == "none" else "width"
            actual_resize_value = None
            
            if self.resize_mode == "width":
                # 入力フィールドから最新の値を取得
                try:
                    if self.width_entry.get():
                        actual_resize_value = int(self.width_entry.get())
                    else:
                        actual_resize_value = self.resize_width if hasattr(self, 'resize_width') else 800
                except ValueError:
                    actual_resize_value = self.resize_width if hasattr(self, 'resize_width') else 800
            
            print(f"実圧縮処理: resize_mode={self.resize_mode} → {actual_resize_mode}, resize_value={actual_resize_value}")
            
            # 統一されたパラメータで圧縮実行
            result = resize_and_compress_image(
                source_path=self.input_path,
                dest_path=self.output_path,
                resize_mode=actual_resize_mode,
                resize_value=actual_resize_value,
                quality=self.quality,
                format=format_for_core
            )
            
            success = result[0] if result else False
            
            if success:
                # 成功
                original_size = Path(self.input_path).stat().st_size
                compressed_size = Path(self.output_path).stat().st_size
                reduction = (1 - compressed_size / original_size) * 100
                
                self.after(0, lambda: self.on_compression_complete(
                    True,
                    f"圧縮完了！ {format_file_size(original_size)} → {format_file_size(compressed_size)} (-{reduction:.1f}%)"
                ))
            else:
                self.after(0, lambda: self.on_compression_complete(
                    False,
                    "圧縮に失敗しました"
                ))
                
        except Exception as e:
            error_msg = str(e)
            self.after(0, lambda: self.on_compression_complete(
                False,
                f"エラー: {error_msg}"
            ))
    
    def on_compression_complete(self, success, message):
        """圧縮完了時の処理"""
        self.processing = False
        self.compress_button.configure(
            state="normal", 
            text="✨ 処理開始",
            fg_color="#3B82F6",
            hover_color="#2563EB",
            text_color="white"
        )
        self.progress_bar.pack_forget()
        
        if success:
            self.status_label.configure(text=message, text_color="#22C55E")
            self.hint_label.configure(
                text="🎉 処理が完了しました！別の画像を処理する場合は、新しいファイルを選択してください",
                text_color="#22C55E"
            )
            # 保存先を開くか確認（Windows以外も対応）
            if messagebox.askyesno("完了", f"{message}\n\n保存先フォルダを開きますか？"):
                output_dir = Path(self.output_path).parent
                if sys.platform == "win32":
                    os.startfile(output_dir)
                elif sys.platform == "darwin":  # macOS
                    os.system(f"open '{output_dir}'")
                else:  # Linux
                    os.system(f"xdg-open '{output_dir}'")
        else:
            self.status_label.configure(text=message, text_color="#EF4444")
            self.hint_label.configure(
                text="エラーが発生しました。設定を確認してもう一度お試しください",
                text_color="#EF4444"
            )
            messagebox.showerror("エラー", message)
    
    def _start_batch_compression(self):
        """バッチ処理を開始"""
        # 目標サイズを取得
        try:
            target_size_text = self.target_size_entry.get().strip()
            if target_size_text:
                self.target_size_kb = int(target_size_text)
            else:
                self.target_size_kb = 0
        except ValueError:
            self.target_size_kb = 0
        
        self.processing = True
        self.cancel_requested = False
        self.processed_count = 0
        self.failed_count = 0
        
        # UIを更新
        self.compress_button.configure(
            state="normal",  # キャンセル可能
            text="⏸ キャンセル",
            fg_color="#EF4444",
            hover_color="#DC2626",
            text_color="white",
            command=self.cancel_batch_process
        )
        
        self.progress_bar.pack(fill="x", pady=(10, 0))
        self.progress_bar.set(0)
        
        # ステータス更新
        self.status_label.configure(
            text="⏳ バッチ処理中...",
            text_color="#3B82F6"
        )
        
        # 出力先フォルダを選択
        output_dir = filedialog.askdirectory(
            title="出力先フォルダを選択",
            initialdir=Path(self.input_files[0]).parent
        )
        
        if not output_dir:
            self.on_batch_complete(False, "出力先が選択されませんでした")
            return
        
        self.output_dir = output_dir
        
        # 別スレッドで実行
        thread = threading.Thread(target=self._batch_process_thread, daemon=True)
        thread.start()
    
    def cancel_batch_process(self):
        """バッチ処理をキャンセル"""
        self.cancel_requested = True
        self.compress_button.configure(
            text="キャンセル中...",
            state="disabled"
        )
    
    def _batch_process_thread(self):
        """バッチ処理スレッド"""
        results = []
        total_files = len(self.input_files)
        
        for i, file_path in enumerate(self.input_files):
            if self.cancel_requested:
                break
            
            # 進捗更新
            progress = i / total_files
            self.after(0, lambda p=progress, idx=i+1: self._update_batch_progress(p, idx, total_files))
            
            try:
                # ファイルごとに処理
                input_path = Path(file_path)
                
                # 出力ファイル名を生成
                if self.output_format != "original":
                    ext_map = {"jpeg": ".jpg", "png": ".png", "webp": ".webp"}
                    new_ext = ext_map.get(self.output_format, input_path.suffix)
                    output_path = Path(self.output_dir) / f"{input_path.stem}_compressed{new_ext}"
                else:
                    output_path = Path(self.output_dir) / f"{input_path.stem}_compressed{input_path.suffix}"
                
                # 圧縮処理
                success = self._process_single_file(str(input_path), str(output_path))
                
                if success:
                    self.processed_count += 1
                    results.append({"file": input_path.name, "status": "成功"})
                else:
                    self.failed_count += 1
                    results.append({"file": input_path.name, "status": "失敗"})
                    
            except Exception as e:
                self.failed_count += 1
                results.append({"file": Path(file_path).name, "status": f"エラー: {str(e)}"})
        
        # 完了処理
        self.after(0, lambda: self.on_batch_complete(True, results))
    
    def _process_single_file(self, input_path, output_path):
        """単一ファイルを処理（目標サイズ対応）"""
        if self.target_size_kb > 0:
            # 目標サイズが指定されている場合は品質を自動調整
            return self._process_with_target_size(input_path, output_path)
        else:
            # 通常の処理
            format_for_core = "original"
            if self.output_format != "original":
                format_for_core = self.output_format
            
            # リサイズ値を取得
            if self.resize_mode == "width":
                resize_value = self.resize_width if hasattr(self, 'resize_width') else 800
                result = resize_and_compress_image(
                    source_path=input_path,
                    dest_path=output_path,
                    target_width=resize_value,
                    quality=self.quality,
                    format=format_for_core
                )
            else:
                # リサイズしない場合はtarget_widthを指定しない
                result = resize_and_compress_image(
                    source_path=input_path,
                    dest_path=output_path,
                    quality=self.quality,
                    format=format_for_core
                )
            
            return result[0] if result else False
    
    def _process_with_target_size(self, input_path, output_path):
        """目標サイズに合わせて品質を自動調整して処理"""
        target_bytes = self.target_size_kb * 1024
        best_quality = self.quality
        
        # 二分探索で最適な品質を見つける
        min_quality = 10
        max_quality = 95
        
        for _ in range(5):  # 最大5回試行
            temp_buffer = io.BytesIO()
            
            # テスト圧縮
            source_image = Image.open(input_path)
            
            format_for_core = "original"
            if self.output_format != "original":
                format_for_core = self.output_format
            
            success, _ = resize_and_compress_image(
                source_image=source_image,
                output_buffer=temp_buffer,
                resize_mode=self.resize_mode,
                resize_value=self.resize_width if self.resize_mode == "width" else None,
                quality=best_quality,
                output_format=format_for_core,
                optimize=True
            )
            
            if success:
                size = len(temp_buffer.getvalue())
                if size <= target_bytes:
                    # 目標サイズ以下なら保存
                    with open(output_path, 'wb') as f:
                        f.write(temp_buffer.getvalue())
                    return True
                else:
                    # 品質を下げる
                    max_quality = best_quality - 1
                    best_quality = (min_quality + max_quality) // 2
                    
                    if best_quality < 10:
                        # 最低品質でも大きすぎる場合
                        with open(output_path, 'wb') as f:
                            f.write(temp_buffer.getvalue())
                        return True
        
        return False
    
    def _update_batch_progress(self, progress, current, total):
        """バッチ処理の進捗を更新"""
        self.progress_bar.set(progress)
        self.status_label.configure(
            text=f"⏳ 処理中... ({current}/{total})",
            text_color="#3B82F6"
        )
    
    def on_batch_complete(self, success, results):
        """バッチ処理完了時の処理"""
        self.processing = False
        
        # UIをリセット
        self.compress_button.configure(
            state="normal",
            text="✨ 処理開始",
            fg_color="#3B82F6",
            hover_color="#2563EB",
            text_color="white",
            command=self.start_compression
        )
        self.progress_bar.pack_forget()
        
        if success and isinstance(results, list):
            # 結果サマリーを表示
            message = f"バッチ処理が完了しました！\n\n"
            message += f"処理済み: {self.processed_count}個\n"
            message += f"失敗: {self.failed_count}個"
            
            if self.cancel_requested:
                message += f"\nキャンセル: {len(self.input_files) - self.processed_count - self.failed_count}個"
            
            self.status_label.configure(
                text=f"✅ 完了: {self.processed_count}個成功, {self.failed_count}個失敗",
                text_color="#22C55E" if self.failed_count == 0 else "#F59E0B"
            )
            
            # 詳細結果を表示
            if messagebox.askyesno("処理完了", f"{message}\n\n詳細を表示しますか？"):
                self._show_batch_results(results)
            
            # 出力フォルダを開くか確認
            if self.processed_count > 0 and messagebox.askyesno("フォルダを開く", "出力先フォルダを開きますか？"):
                if sys.platform == "win32":
                    os.startfile(self.output_dir)
                elif sys.platform == "darwin":
                    os.system(f"open '{self.output_dir}'")
                else:
                    os.system(f"xdg-open '{self.output_dir}'")
        else:
            self.status_label.configure(
                text="❌ バッチ処理が失敗しました",
                text_color="#EF4444"
            )
            if isinstance(results, str):
                messagebox.showerror("エラー", results)
    
    def _show_batch_results(self, results):
        """バッチ処理の詳細結果を表示"""
        # 結果ウィンドウを作成
        result_window = ctk.CTkToplevel(self)
        result_window.title("処理結果")
        result_window.geometry("600x400")
        
        # タイトル
        title_label = ctk.CTkLabel(
            result_window,
            text="バッチ処理結果",
            font=ctk.CTkFont(size=16, weight="bold")
        )
        title_label.pack(pady=(10, 5))
        
        # 結果リスト
        result_text = ctk.CTkTextbox(result_window, height=300)
        result_text.pack(fill="both", expand=True, padx=20, pady=10)
        
        for i, result in enumerate(results, 1):
            status_emoji = "✅" if result["status"] == "成功" else "❌"
            result_text.insert("end", f"{i}. {status_emoji} {result['file']} - {result['status']}\n")
        
        result_text.configure(state="disabled")
        
        # 閉じるボタン
        close_button = ctk.CTkButton(
            result_window,
            text="閉じる",
            command=result_window.destroy
        )
        close_button.pack(pady=10)
    
    def setup_keyboard_shortcuts(self):
        """キーボードショートカットを設定"""
        # Ctrl+O: ファイル選択
        self.bind("<Control-o>", lambda e: self.select_file())
        
        # Ctrl+S: 処理開始
        self.bind("<Control-s>", lambda e: self.start_compression() if not self.processing else None)
        
        # Ctrl+Q: アプリ終了
        self.bind("<Control-q>", lambda e: self.quit())
        
        # Escape: キャンセル
        self.bind("<Escape>", lambda e: self.cancel_batch_process() if self.processing else None)
        
        # フォーカスを確保
        self.focus_set()


def main():
    """メイン関数"""
    # Windows環境でのDPI設定
    if sys.platform == "win32":
        try:
            from ctypes import windll
            windll.shcore.SetProcessDpiAwareness(1)
        except:
            pass
    
    app = MinimalResizeApp()
    app.mainloop()


if __name__ == "__main__":
    main()