#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
KarukuResize ミニマル版（リファクタリング版）
シンプルで使いやすい画像圧縮ツール - 改良版
"""

import customtkinter as ctk
from tkinter import filedialog, messagebox
import tkinter as tk
from pathlib import Path
from PIL import Image
import threading
import logging
import time
import os

# --- Debug logging setup ---
DEBUG_MODE = os.getenv("KARUKU_DEBUG") == "1"
logging.basicConfig(
    level=logging.DEBUG if DEBUG_MODE else logging.INFO,
    format="%(asctime)s [%(threadName)s] %(levelname)s: %(message)s",
)
log = logging.getLogger("preview")

def _d(msg: str, *args):
    if DEBUG_MODE:
        log.debug(msg, *args)
import sys

# tkinterdnd2のインポート（オプション）
try:
    from tkinterdnd2 import DND_FILES, TkinterDnD
    TKDND_AVAILABLE = True
except ImportError:
    TKDND_AVAILABLE = False
    print("注意: tkinterdnd2が利用できません。ドラッグ&ドロップは無効です。")

# プロジェクトのモジュールをインポート
from resize_core import format_file_size
from japanese_font_utils import JapaneseFontManager

# リファクタリングで追加したモジュール
from image_processing_config import ImageProcessingConfig, ConfigManager
from ui_parameter_extractor import UIParameterExtractor
from image_processor_controller import ImageProcessorController, ProcessingResult

# 日本語フォント設定
try:
    JAPANESE_FONT_AVAILABLE = True
except ImportError:
    JAPANESE_FONT_AVAILABLE = False
    print("注意: japanese_font_utilsが利用できません。デフォルトフォントを使用します。")

# カスタムフォント設定
ctk.set_appearance_mode("light")
ctk.set_default_color_theme("blue")


class UIComponents:
    """UI要素を管理するコンテナクラス"""
    
    def __init__(self):
        # メインコンテナ
        self.main_container = None
        
        # 比較表示
        self.comparison = None
        
        # コントロール要素
        self.quality_slider = None
        self.quality_label = None
        self.format_var = None
        self.format_menu = None
        self.resize_var = None
        self.resize_menu = None
        self.width_entry = None
        self.width_label = None
        self.target_size_entry = None
        
        # ボタン
        self.select_button = None
        self.output_button = None
        self.preview_button = None
        self.compress_button = None
        
        # ステータス表示
        self.status_label = None
        self.hint_label = None
        self.zoom_hint_label = None
        self.progress_bar = None
        
        # 警告ラベル
        self.quality_warning_label = None
        self.png_format_label = None
        
        # バッチ処理UI
        self.file_list_frame = None
        self.batch_progress_label = None
        self.cancel_button = None
    
    def get_widget_dict(self):
        """UIParameterExtractor用のウィジェット辞書を返す"""
        return {
            "quality_slider": self.quality_slider,
            "format_var": self.format_var,
            "resize_var": self.resize_var,
            "width_entry": self.width_entry,
            "target_size_entry": self.target_size_entry
        }


class MinimalResizeAppRefactored(ctk.CTk if not TKDND_AVAILABLE else TkinterDnD.Tk):
    """リファクタリングされたミニマル画像圧縮アプリケーション"""
    
    def __init__(self):
        super().__init__()
        
        # ウィンドウ設定
        self.title("KarukuResize - 画像を軽く")
        self.geometry("900x600")
        self.minsize(800, 500)
        
        # 設定とコンポーネントの初期化
        self.config_manager = ConfigManager()
        self.config = self.config_manager.config
        self.param_extractor = UIParameterExtractor(self.config)
        self.processor = ImageProcessorController(self.config, self.param_extractor)
        
        # UI要素コンテナ
        self.ui = UIComponents()
        
        # 状態管理
        self.input_path = None
        self.input_files = []  # バッチ処理用
        self.output_path = None
        self.processing = False
        self.cancel_requested = False
        
        # フォントマネージャー
        if JAPANESE_FONT_AVAILABLE:
            self.font_manager = JapaneseFontManager()
        
        # UIを構築
        self._build_ui()
        
        # ドラッグ&ドロップとショートカットの設定
        self._setup_drag_drop()
        self._setup_keyboard_shortcuts()
        
        # 最後に使用したパスを復元
        if self.config.last_input_path and Path(self.config.last_input_path).exists():
            self.load_file(self.config.last_input_path)
        
        # ウィンドウクローズ時の処理
        self.protocol("WM_DELETE_WINDOW", self._on_closing)
    
    def _build_ui(self):
        """UIを構築"""
        # メインコンテナ
        self.ui.main_container = ctk.CTkFrame(self, fg_color="transparent")
        self.ui.main_container.pack(fill="both", expand=True, padx=20, pady=20)
        
        # タイトル
        self._create_title()
        
        # 比較キャンバス（既存のComparisonCanvasを使用）
        from resize_images_gui_minimal import ComparisonCanvas
        self.ui.comparison = ComparisonCanvas(self.ui.main_container, height=300)
        self.ui.comparison.pack(fill="both", expand=True, pady=(0, 20))
        
        # コントロールパネル
        self._create_control_panel()
        
        # ステータスバー
        self._create_status_bar()
    
    def _create_title(self):
        """タイトルラベルを作成"""
        if JAPANESE_FONT_AVAILABLE:
            title_font = ctk.CTkFont(family=self.font_manager.selected_font, size=24, weight="bold")
        else:
            title_font = ctk.CTkFont(size=24, weight="bold")
        
        title_label = ctk.CTkLabel(
            self.ui.main_container,
            text="画像を軽く、品質はそのまま",
            font=title_font
        )
        title_label.pack(pady=(0, 20))
    
    def _create_control_panel(self):
        """コントロールパネルを作成"""
        control_frame = ctk.CTkFrame(self.ui.main_container, fg_color="transparent")
        control_frame.pack(fill="x", pady=(0, 10))
        
        # フォント設定
        if JAPANESE_FONT_AVAILABLE:
            label_font = ctk.CTkFont(family=self.font_manager.selected_font, size=14)
            button_font = ctk.CTkFont(family=self.font_manager.selected_font, size=14, weight="bold")
            small_font = ctk.CTkFont(family=self.font_manager.selected_font, size=12)
        else:
            label_font = ctk.CTkFont(size=14)
            button_font = ctk.CTkFont(size=14)
            small_font = ctk.CTkFont(size=12)
        
        # 品質設定
        self._create_quality_controls(control_frame, label_font, small_font)
        
        # 形式選択
        self._create_format_controls(control_frame, label_font)
        
        # リサイズ設定
        self._create_resize_controls(control_frame, label_font)
        
        # ボタン類
        self._create_buttons(control_frame, button_font, small_font)
    
    def _create_quality_controls(self, parent, label_font, small_font):
        """品質コントロールを作成"""
        quality_frame = ctk.CTkFrame(parent, fg_color="transparent")
        quality_frame.pack(fill="x", pady=(0, 10))
        
        ctk.CTkLabel(quality_frame, text="品質:", font=label_font).pack(side="left", padx=(0, 10))
        
        self.ui.quality_slider = ctk.CTkSlider(
            quality_frame,
            from_=1,
            to=100,
            number_of_steps=99,
            command=self._on_quality_change
        )
        self.ui.quality_slider.set(self.config.quality)
        self.ui.quality_slider.pack(side="left", fill="x", expand=True, padx=(0, 10))
        
        self.ui.quality_label = ctk.CTkLabel(
            quality_frame,
            text=f"{self.config.quality}%",
            font=ctk.CTkFont(family=self.font_manager.selected_font if JAPANESE_FONT_AVAILABLE else "", size=14, weight="bold"),
            width=50
        )
        self.ui.quality_label.pack(side="left", padx=(0, 10))
        
        # プレビューボタン
        self.ui.preview_button = ctk.CTkButton(
            quality_frame,
            text="🔄 プレビュー",
            command=self._generate_preview_manual,
            font=small_font,
            height=30,
            width=100,
            state="disabled",
            fg_color="#9CA3AF",
            hover_color="#9CA3AF"
        )
        self.ui.preview_button.pack(side="left")
    
    def _create_format_controls(self, parent, label_font):
        """形式選択コントロールを作成"""
        format_frame = ctk.CTkFrame(parent, fg_color="transparent")
        format_frame.pack(fill="x", pady=(0, 10))
        
        ctk.CTkLabel(format_frame, text="形式:", font=label_font).pack(side="left", padx=(0, 10))
        
        self.ui.format_var = ctk.StringVar(value="元の形式")
        self.ui.format_menu = ctk.CTkOptionMenu(
            format_frame,
            values=["元の形式", "JPEG", "PNG", "WebP"],
            variable=self.ui.format_var,
            command=self._on_format_change,
            width=120
        )
        self.ui.format_menu.pack(side="left")
    
    def _create_resize_controls(self, parent, label_font):
        """リサイズコントロールを作成"""
        resize_frame = ctk.CTkFrame(parent, fg_color="transparent")
        resize_frame.pack(fill="x", pady=(0, 20))
        
        ctk.CTkLabel(resize_frame, text="サイズ:", font=label_font).pack(side="left", padx=(0, 10))
        
        resize_mode_map = {"none": "変更しない", "width": "幅を指定"}
        self.ui.resize_var = ctk.StringVar(value=resize_mode_map.get(self.config.resize_mode, "変更しない"))
        self.ui.resize_menu = ctk.CTkOptionMenu(
            resize_frame,
            values=["変更しない", "幅を指定"],
            variable=self.ui.resize_var,
            command=self._on_resize_change,
            width=120
        )
        self.ui.resize_menu.pack(side="left", padx=(0, 10))
        
        # 幅入力フィールド
        self.ui.width_entry = ctk.CTkEntry(
            resize_frame,
            placeholder_text=str(self.config.DEFAULT_WIDTH),
            width=80,
            font=label_font
        )
        self.ui.width_entry.insert(0, str(self.config.resize_width))
        self.ui.width_entry.bind('<KeyRelease>', self._on_width_change)
        self.ui.width_entry.bind('<FocusOut>', self._on_width_change)
        
        self.ui.width_label = ctk.CTkLabel(resize_frame, text="px", font=label_font)
        
        # 初期表示状態を設定
        if self.config.resize_mode == "width":
            self.ui.width_entry.pack(side="left", padx=(0, 5))
            self.ui.width_label.pack(side="left")
    
    def _create_buttons(self, parent, button_font, small_font):
        """ボタン類を作成"""
        button_frame = ctk.CTkFrame(parent, fg_color="transparent")
        button_frame.pack(fill="x")
        
        # ファイル選択ボタン
        self.ui.select_button = ctk.CTkButton(
            button_frame,
            text="📂 ファイルを選択",
            command=self._select_file,
            font=button_font,
            height=40,
            fg_color="#3B82F6",
            hover_color="#2563EB"
        )
        self.ui.select_button.pack(side="left", padx=(0, 10))
        
        # 保存先ボタン
        self.ui.output_button = ctk.CTkButton(
            button_frame,
            text="📁 保存先",
            command=self._select_output,
            font=small_font,
            height=40,
            width=100,
            fg_color="#6B7280",
            hover_color="#4B5563"
        )
        self.ui.output_button.pack(side="left", padx=(0, 10))
        
        # 目標サイズ入力
        self._create_target_size_input(button_frame, small_font)
        
        # スペーサー
        ctk.CTkFrame(button_frame, fg_color="transparent").pack(side="left", fill="x", expand=True)
        
        # 圧縮開始ボタン
        self.ui.compress_button = ctk.CTkButton(
            button_frame,
            text="✨ 処理開始",
            command=self._start_compression,
            font=ctk.CTkFont(family=self.font_manager.selected_font if JAPANESE_FONT_AVAILABLE else "", size=16, weight="bold"),
            height=40,
            width=150,
            state="disabled",
            fg_color="#D1D5DB",
            hover_color="#D1D5DB",
            text_color="#9CA3AF"
        )
        self.ui.compress_button.pack(side="right")
    
    def _create_target_size_input(self, parent, small_font):
        """目標サイズ入力を作成"""
        size_frame = ctk.CTkFrame(parent, fg_color="transparent")
        size_frame.pack(side="left", padx=(10, 0))
        
        ctk.CTkLabel(size_frame, text="目標:", font=small_font).pack(side="left", padx=(0, 5))
        
        self.ui.target_size_entry = ctk.CTkEntry(
            size_frame,
            placeholder_text="KB",
            width=60,
            font=small_font
        )
        self.ui.target_size_entry.pack(side="left")
        self.ui.target_size_entry.bind('<KeyRelease>', self._on_target_size_change)
        self.ui.target_size_entry.bind('<FocusOut>', self._on_target_size_change)
        
        if self.config.target_size_kb > 0:
            self.ui.target_size_entry.insert(0, str(self.config.target_size_kb))
        
        ctk.CTkLabel(size_frame, text="KB以下", font=small_font).pack(side="left", padx=(2, 0))
    
    def _create_status_bar(self):
        """ステータスバーを作成"""
        # プログレスバー（最初は非表示）
        self.ui.progress_bar = ctk.CTkProgressBar(self.ui.main_container)
        self.ui.progress_bar.set(0)
        
        # ステータスラベル
        self.ui.status_label = ctk.CTkLabel(
            self.ui.main_container,
            text="📌 ステップ1: 画像ファイルを選択してください",
            font=ctk.CTkFont(family=self.font_manager.selected_font if JAPANESE_FONT_AVAILABLE else "", size=12),
            text_color="#F59E0B"
        )
        self.ui.status_label.pack(pady=(10, 0))
        
        # ヒントラベル
        self.ui.hint_label = ctk.CTkLabel(
            self.ui.main_container,
            text="ドラッグ&ドロップまたは「ファイルを選択」ボタンをクリック",
            font=ctk.CTkFont(family=self.font_manager.selected_font if JAPANESE_FONT_AVAILABLE else "", size=11),
            text_color="#9CA3AF"
        )
        self.ui.hint_label.pack(pady=(2, 0))
        
        # ズーム操作ヒント
        self.ui.zoom_hint_label = ctk.CTkLabel(
            self.ui.main_container,
            text="🔍 ダブルクリック: 100%/フィット切替 | マウスホイール: ズーム | Ctrl+マウス: 拡大鏡",
            font=ctk.CTkFont(family=self.font_manager.selected_font if JAPANESE_FONT_AVAILABLE else "", size=10),
            text_color="#9CA3AF"
        )
        
        # 警告ラベル
        self._create_warning_labels()
    
    def _create_warning_labels(self):
        """警告ラベルを作成"""
        # 品質警告ラベル
        self.ui.quality_warning_label = ctk.CTkLabel(
            self.ui.main_container,
            text="⚠️ 品質が非常に低く設定されています。画質が大幅に劣化します。",
            font=ctk.CTkFont(family=self.font_manager.selected_font if JAPANESE_FONT_AVAILABLE else "", size=11),
            text_color="#EF4444"
        )
        
        # PNG形式警告ラベル
        self.ui.png_format_label = ctk.CTkLabel(
            self.ui.main_container,
            text="ℹ️ PNG形式は可逆圧縮のため、品質設定は効果がありません。",
            font=ctk.CTkFont(family=self.font_manager.selected_font if JAPANESE_FONT_AVAILABLE else "", size=11),
            text_color="#3B82F6"
        )
    
    # === イベントハンドラ ===
    
    def _on_quality_change(self, value):
        """品質スライダー変更時"""
        self.config.quality = int(value)
        self.ui.quality_label.configure(text=f"{self.config.quality}%")
        
        # 品質警告の表示/非表示
        if self.config.quality <= 10:
            self.ui.quality_warning_label.pack(pady=(5, 0))
        else:
            self.ui.quality_warning_label.pack_forget()
        
        # プレビューを更新（遅延実行）
        self._schedule_preview_update()
    
    def _on_format_change(self, value):
        """形式選択変更時"""
        self.config.output_format = self.param_extractor.get_output_format(self.ui.format_var)
        
        # PNG形式の警告表示
        if self.config.output_format == "png" or (self.config.output_format == "original" and self.input_path and self.input_path.lower().endswith('.png')):
            self.ui.png_format_label.pack(pady=(5, 0))
        else:
            self.ui.png_format_label.pack_forget()
        
        self._generate_preview()
    
    def _on_resize_change(self, value):
        """リサイズモード変更時"""
        self.config.resize_mode = self.param_extractor.get_resize_mode(self.ui.resize_var)
        
        if self.config.resize_mode == "none":
            # 幅入力を非表示
            self.ui.width_entry.pack_forget()
            self.ui.width_label.pack_forget()
        else:
            # 幅入力を表示
            self.ui.width_entry.pack(side="left", padx=(0, 5))
            self.ui.width_label.pack(side="left")
        
        self._generate_preview()
    
    def _on_width_change(self, event):
        """幅入力変更時"""
        # パラメータ抽出器を使って値を取得
        self.config.resize_width = self.param_extractor.get_resize_value(
            self.config.resize_mode,
            self.ui.width_entry,
            self.config.DEFAULT_WIDTH
        ) or self.config.DEFAULT_WIDTH
        
        # プレビューを更新（遅延実行）
        self._schedule_preview_update(delay=500)
    
    def _on_target_size_change(self, event):
        """目標サイズ変更時"""
        self.config.target_size_kb = self.param_extractor.get_target_size_kb(self.ui.target_size_entry)
        
        if self.input_path and not self.processing:
            # 遅延実行でプレビューを更新
            self._schedule_preview_update(delay=1000, light=True)
    
    # === ファイル操作 ===
    
    def _select_file(self):
        """ファイル選択ダイアログを表示"""
        file_paths = filedialog.askopenfilenames(
            title="画像ファイルを選択",
            filetypes=[
                ("画像ファイル", "*.jpg *.jpeg *.png *.webp"),
                ("すべてのファイル", "*.*")
            ]
        )
        if file_paths:
            if len(file_paths) == 1:
                self.load_file(file_paths[0])
            else:
                self._load_files(file_paths)
    
    def load_file(self, file_path):
        """ファイルを読み込み"""
        self.input_path = file_path
        self.config.last_input_path = file_path
        self.ui.comparison.set_images(before_path=file_path)
        
        # ボタンを有効化
        self._enable_controls()
        
        # ステータス更新
        self.ui.status_label.configure(
            text=f"✅ 選択済み: {Path(file_path).name}",
            text_color="#22C55E"
        )
        self.ui.hint_label.configure(
            text="📌 ステップ2: 必要に応じて品質・形式・サイズを調整し、処理開始をクリック"
        )
        
        # ズーム操作ヒントを表示
        self.ui.zoom_hint_label.pack(pady=(2, 0))
        
        # バッチモードフラグをクリア
        self.input_files = []
        
        # 軽量プレビューを生成
        self._generate_preview_light()
    
    def _load_files(self, file_paths):
        """複数ファイルを読み込み（バッチ処理）"""
        self.input_files = list(file_paths)
        self.input_path = None
        
        # UIを更新
        self.ui.comparison.show_placeholder()
        
        # ボタンを有効化
        self.ui.compress_button.configure(
            state="normal",
            fg_color="#3B82F6",
            hover_color="#2563EB",
            text_color="white"
        )
        
        # プレビューボタンを無効化（バッチモード）
        self.ui.preview_button.configure(
            state="disabled",
            fg_color="#9CA3AF",
            hover_color="#9CA3AF"
        )
        
        # ステータス更新
        self.ui.status_label.configure(
            text=f"✅ {len(self.input_files)}個のファイルを選択しました",
            text_color="#22C55E"
        )
        self.ui.hint_label.configure(
            text="📌 バッチ処理モード: 処理開始をクリックして一括処理を開始"
        )
        
        # ズーム操作ヒントを非表示
        self.ui.zoom_hint_label.pack_forget()
    
    def _select_output(self):
        """出力先を選択"""
        if not self.input_path:
            return
        
        input_path = Path(self.input_path)
        initial_name = input_path.stem + "_compressed" + input_path.suffix
        
        output_path = filedialog.asksaveasfilename(
            title="保存先を選択",
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
            self.config.last_output_path = str(Path(output_path).parent)
            self.ui.hint_label.configure(
                text=f"💾 保存先: {Path(output_path).name}",
                text_color="#3B82F6"
            )
    
    # === プレビュー処理 ===
    
    def _generate_preview_light(self):
        """軽量プレビューを生成（画像選択直後）"""
        if not self.input_path or self.processing:
            return
        
        thread = threading.Thread(
            target=self._generate_preview_thread,
            args=(False,),
            daemon=True
        )
        thread.start()
    
    def _generate_preview_manual(self):
        """手動プレビューを生成（詳細・目標サイズ対応）"""
        if not self.input_path or self.processing:
            return
        
        # プレビューボタンを無効化
        self.ui.preview_button.configure(state="disabled", text="処理中...")
        
        thread = threading.Thread(
            target=self._generate_preview_thread,
            args=(True,),
            daemon=True
        )
        thread.start()
    
    def _generate_preview(self):
        """自動プレビューを生成"""
        if not self.input_path or self.processing:
            return
        
        self._generate_preview_light()
    
    def _generate_preview_thread(self, detailed=False):
        _d("=== _generate_preview_thread start detailed=%s path=%s", detailed, self.input_path)
        """プレビュー生成スレッド"""
        try:
            # 進捗通知
            def progress_callback(msg):
                print(f"プレビュー処理: {msg}")
            
            # プレビュー処理を実行
            _d("calling process_preview")
            result = self.processor.process_preview(
                self.input_path,
                self.ui.get_widget_dict(),
                detailed=detailed,
                progress_callback=progress_callback
            )
            
            if result.success:
                # UIを更新
                self.after(0, lambda: self._update_preview_ui(result))
            else:
                # エラー処理
                self.after(0, lambda: self._handle_preview_error(result.error_message, detailed))
                
        except Exception as e:
            error_msg = str(e)
            self.after(0, lambda: self._handle_preview_error(error_msg, detailed))

    
    def _update_preview_ui(self, result: ProcessingResult):
        """プレビューUIを更新"""
        _d("_update_preview_ui result keys=%s", list(result.data.keys()))
        # 画像を表示
        self.ui.comparison.set_images(
            before_path=self.input_path,
            after_image=result.data.get("after_image"),
            after_size=result.data.get("after_size", 0)
        )

        # 詳細情報がある場合
        if "optimized_quality" in result.data:
            quality = result.data["optimized_quality"]
            target_achieved = result.data.get("target_achieved", False)
            if target_achieved:
                message = f"✅ 目標達成: 品質{quality}%で目標サイズ以下"
                color = "#22C55E"
            else:
                message = f"⚠️ 品質{quality}%が限界（未達）"
                color = "#F59E0B"
            self.ui.hint_label.configure(text=message, text_color=color)

        # プレビューボタンを再度有効化
        self.ui.preview_button.configure(state="normal", text="🔄 プレビュー")

    # ---- エラーハンドラ ----
    def _handle_preview_error(self, error_msg, detailed):
        """プレビューエラーをハンドル"""
        print(f"プレビューエラー: {error_msg}")
        
        if detailed:
            messagebox.showerror("プレビューエラー", f"プレビューの生成に失敗しました:\n{error_msg}")
        
        # プレビューボタンを再度有効化
        self.ui.preview_button.configure(state="normal", text="🔄 プレビュー")
    
    # === 圧縮処理 ===
    
    def _start_compression(self):
        """圧縮処理を開始"""
        if self.processing:
            return
        
        # バッチ処理モードかチェック
        if self.input_files:
            self._start_batch_process()
        else:
            self._start_single_compression()
    
    def _start_single_compression(self):
        """単一ファイルの圧縮を開始"""
        # バリデーション
        is_valid, error_msg = self.param_extractor.validate_input_output_paths(
            self.input_path,
            self.output_path
        )
        
        if not is_valid:
            messagebox.showerror("エラー", error_msg)
            return
        
        # 出力パスが未設定の場合は自動生成
        if not self.output_path:
            input_path = Path(self.input_path)
            self.output_path = str(input_path.parent / f"{input_path.stem}_compressed{input_path.suffix}")
        
        # 処理開始
        self.processing = True
        self.ui.compress_button.configure(
            state="disabled",
            text="処理中...",
            fg_color="#9CA3AF"
        )
        self.ui.progress_bar.pack(pady=(10, 0))
        self.ui.progress_bar.set(0.5)
        
        # 別スレッドで実行
        thread = threading.Thread(target=self._compress_worker, daemon=True)
        thread.start()
    
    def _compress_worker(self):
        """圧縮処理ワーカー"""
        try:
            # 設定を更新
            self.param_extractor.update_config_from_ui(self.ui.get_widget_dict())
            
            # 進捗通知
            def progress_callback(msg):
                print(f"圧縮処理: {msg}")
            
            # 圧縮処理を実行
            result = self.processor.process_compression(
                self.input_path,
                self.output_path,
                self.ui.get_widget_dict(),
                progress_callback=progress_callback
            )
            
            # UI更新
            self.after(0, lambda: self._on_compression_complete(result))
            
        except Exception as e:
            result = ProcessingResult(
                success=False,
                message=f"エラー: {str(e)}"
            )
            self.after(0, lambda: self._on_compression_complete(result))
    
    def _on_compression_complete(self, result: ProcessingResult):
        """圧縮完了時の処理"""
        self.processing = False
        self.ui.compress_button.configure(
            state="normal",
            text="✨ 処理開始",
            fg_color="#3B82F6",
            hover_color="#2563EB",
            text_color="white"
        )
        self.ui.progress_bar.pack_forget()
        
        # 結果を表示
        if result.success:
            self.ui.status_label.configure(
                text=result.message,
                text_color="#22C55E"
            )
            
            # 圧縮後の画像でプレビューを更新
            self.ui.comparison.set_images(
                before_path=self.input_path,
                after_path=self.output_path
            )
        else:
            self.ui.status_label.configure(
                text=result.message,
                text_color="#EF4444"
            )
            messagebox.showerror("圧縮エラー", result.message)
    
    # === バッチ処理 ===
    
    def _start_batch_process(self):
        """バッチ処理を開始"""
        # 出力ディレクトリを選択
        output_dir = filedialog.askdirectory(
            title="出力フォルダを選択",
            initialdir=str(Path(self.input_files[0]).parent)
        )
        
        if not output_dir:
            return
        
        # 処理開始
        self.processing = True
        self.cancel_requested = False
        
        # UIを更新
        self._show_batch_progress_ui()
        
        # 別スレッドで実行
        thread = threading.Thread(
            target=self._batch_process_worker,
            args=(output_dir,),
            daemon=True
        )
        thread.start()
    
    def _batch_process_worker(self, output_dir):
        """バッチ処理ワーカー"""
        try:
            # 設定を更新
            self.param_extractor.update_config_from_ui(self.ui.get_widget_dict())
            
            # 進捗コールバック
            def progress_callback(current, total, message):
                progress = current / total
                self.after(0, lambda: self._update_batch_progress(progress, message))
            
            # キャンセルチェック
            def cancel_check():
                return self.cancel_requested
            
            # バッチ処理を実行
            result = self.processor.process_batch(
                self.input_files,
                output_dir,
                self.ui.get_widget_dict(),
                progress_callback=progress_callback,
                cancel_check=cancel_check
            )
            
            # UI更新
            self.after(0, lambda: self._on_batch_complete(result))
            
        except Exception as e:
            result = ProcessingResult(
                success=False,
                message=f"バッチ処理エラー: {str(e)}"
            )
            self.after(0, lambda: self._on_batch_complete(result))
    
    def _show_batch_progress_ui(self):
        """バッチ処理の進捗UIを表示"""
        # 既存のファイルリストフレームを非表示
        if hasattr(self.ui, 'file_list_frame') and self.ui.file_list_frame:
            self.ui.file_list_frame.pack_forget()
        
        # プログレスバーを表示
        self.ui.progress_bar.pack(pady=(10, 0))
        self.ui.progress_bar.set(0)
        
        # バッチ進捗ラベル
        if not hasattr(self.ui, 'batch_progress_label'):
            self.ui.batch_progress_label = ctk.CTkLabel(
                self.ui.main_container,
                text="処理中...",
                font=ctk.CTkFont(family=self.font_manager.selected_font if JAPANESE_FONT_AVAILABLE else "", size=12)
            )
        self.ui.batch_progress_label.pack(pady=(5, 0))
        
        # キャンセルボタン
        if not hasattr(self.ui, 'cancel_button'):
            self.ui.cancel_button = ctk.CTkButton(
                self.ui.main_container,
                text="キャンセル",
                command=self._cancel_batch_process,
                width=100,
                height=30
            )
        self.ui.cancel_button.pack(pady=(5, 0))
        
        # ボタンを無効化
        self.ui.compress_button.configure(state="disabled")
    
    def _update_batch_progress(self, progress, message):
        """バッチ処理の進捗を更新"""
        self.ui.progress_bar.set(progress)
        self.ui.batch_progress_label.configure(text=message)
    
    def _cancel_batch_process(self):
        """バッチ処理をキャンセル"""
        self.cancel_requested = True
        self.ui.cancel_button.configure(state="disabled", text="キャンセル中...")
    
    def _on_batch_complete(self, result: ProcessingResult):
        """バッチ処理完了時の処理"""
        self.processing = False
        
        # UIを元に戻す
        self.ui.progress_bar.pack_forget()
        if hasattr(self.ui, 'batch_progress_label'):
            self.ui.batch_progress_label.pack_forget()
        if hasattr(self.ui, 'cancel_button'):
            self.ui.cancel_button.pack_forget()
        
        # ボタンを有効化
        self.ui.compress_button.configure(
            state="normal",
            text="✨ 処理開始",
            fg_color="#3B82F6",
            hover_color="#2563EB",
            text_color="white"
        )
        
        # 結果を表示
        self.ui.status_label.configure(
            text=result.message,
            text_color="#22C55E" if result.success else "#EF4444"
        )
        
        # 詳細な結果をメッセージボックスで表示
        if result.data.get("cancelled"):
            messagebox.showinfo("処理キャンセル", result.message)
        else:
            messagebox.showinfo("バッチ処理完了", result.message)
    
    # === ユーティリティメソッド ===
    
    def _enable_controls(self):
        """コントロールを有効化"""
        self.ui.compress_button.configure(
            state="normal",
            fg_color="#3B82F6",
            hover_color="#2563EB",
            text_color="white"
        )
        
        self.ui.preview_button.configure(
            state="normal",
            fg_color="#10B981",
            hover_color="#059669"
        )
    
    def _schedule_preview_update(self, delay=500, light=False):
        """プレビュー更新をスケジュール（遅延実行）"""
        # 既存のタイマーをキャンセル
        if hasattr(self, '_preview_timer'):
            self.after_cancel(self._preview_timer)
        
        # 新しいタイマーを設定
        if light:
            self._preview_timer = self.after(delay, self._generate_preview_light)
        else:
            self._preview_timer = self.after(delay, self._generate_preview)
    
    def _setup_drag_drop(self):
        """ドラッグ&ドロップの設定"""
        if TKDND_AVAILABLE:
            try:
                self.ui.comparison.canvas.drop_target_register(DND_FILES)
                self.ui.comparison.canvas.dnd_bind("<<Drop>>", self._on_drop)
            except Exception as e:
                print(f"ドラッグ&ドロップの設定に失敗: {e}")
    
    def _on_drop(self, event):
        """ドロップ時の処理"""
        files = self.tk.splitlist(event.data)
        if files:
            if len(files) == 1:
                self.load_file(files[0])
            else:
                self._load_files(files)
    
    def _setup_keyboard_shortcuts(self):
        """キーボードショートカットの設定"""
        self.bind("<Control-o>", lambda e: self._select_file())
        self.bind("<Control-s>", lambda e: self._start_compression() if not self.processing else None)
        self.bind("<Control-q>", lambda e: self._on_closing())
        self.bind("<F5>", lambda e: self._generate_preview_manual() if self.input_path else None)
    
    def _on_closing(self):
        """ウィンドウクローズ時の処理"""
        # 設定を保存
        self.config_manager.save()
        
        # ウィンドウを閉じる
        self.destroy()


def main():
    """メインエントリーポイント"""
    app = MinimalResizeAppRefactored()
    app.mainloop()


if __name__ == "__main__":
    main()