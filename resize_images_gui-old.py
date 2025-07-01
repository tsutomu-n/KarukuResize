import customtkinter as ctk
from tkinter import filedialog
import tkinter as tk
from pathlib import Path
from PIL import Image
import traceback
import threading
import time
from typing import Optional, Union, Tuple

# --- Debug logging setup ---
import os, sys, logging
DEBUG_MODE = os.getenv("KARUKU_DEBUG") == "1"
logging.basicConfig(
    level=logging.DEBUG if DEBUG_MODE else logging.INFO,
    format="%(asctime)s [%(threadName)s] %(levelname)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
log = logging.getLogger("preview")

def _d(msg: str, *args):
    """簡易デバッグラッパー (KARUKU_DEBUG=1 のときのみ出力)"""
    if DEBUG_MODE:
        log.debug(msg, *args)


# 新しいモジュールをインポート
try:
    from error_handler import ErrorHandler
    from validators import PathValidator, ValueValidator
    from thread_safe_gui import ThreadSafeGUI, MessageType
    from drag_drop_handler import DragDropHandler, DragDropArea, TKDND_AVAILABLE
    from progress_tracker import ProgressTracker, ProgressItem
    from settings_manager import SettingsManager
    from error_dialog import ErrorDialog, show_error_with_details
except ImportError as e:
    print(f"警告: 追加モジュールのインポートに失敗しました: {e}")
    # フォールバック実装
    class ErrorHandler:
        @staticmethod
        def get_user_friendly_message(error, **kwargs):
            return str(error)
        @staticmethod
        def get_suggestions(error):
            return []
    class PathValidator:
        @staticmethod
        def validate_safe_path(path_str):
            return Path(path_str)
        @staticmethod
        def is_image_file(filepath):
            return Path(filepath).suffix.lower() in {'.jpg', '.jpeg', '.png', '.webp', '.bmp', '.gif'}
    class ValueValidator:
        @staticmethod
        def validate_resize_value(value, mode):
            return int(value) if value else 0
    class ThreadSafeGUI:
        pass
    TKDND_AVAILABLE = False
    class DragDropArea(ctk.CTkFrame):
        pass
    class ProgressTracker:
        pass
    class SettingsManager:
        pass

# Phase 3の新しいモジュールをインポート
try:
    from image_preview import ImagePreviewWidget, ComparisonPreviewWidget
    from preset_manager import PresetManager, PresetData
    from history_manager import HistoryManager
    from statistics_viewer import StatisticsViewer, StatisticsDialog
    from preset_dialog import PresetManagerDialog
    from history_viewer import HistoryViewer
    PHASE3_AVAILABLE = True
except ImportError as e:
    print(f"警告: Phase 3モジュールのインポートに失敗しました: {e}")
    PHASE3_AVAILABLE = False

# 日本語フォント設定モジュールをインポート
try:
    from japanese_font_utils import get_normal_font, get_button_font, get_heading_font
except ImportError:
    # フォールバック用の簡易フォント設定
    def get_normal_font():
        return {"family": "", "size": 11}

    def get_button_font():
        return {"family": "", "size": 11, "weight": "bold"}

    def get_heading_font():
        return {"family": "", "size": 13, "weight": "bold"}


try:
    from resize_core import (
        resize_and_compress_image,
        get_destination_path,
        sanitize_filename,
        format_file_size,
        find_image_files,
        get_japanese_error_message,
    )
except ImportError:

    def resize_and_compress_image(*args, **kwargs):
        print("ダミー: resize_and_compress_image")
        return (
            True,    # success
            False,   # skipped (元のサイズを維持したか)
            50,      # new_size_kb
        )

    def get_destination_path(source_path, source_dir, dest_dir):
        print("ダミー: get_destination_path")
        return Path(dest_dir) / Path(source_path).name

    def sanitize_filename(filename):
        print("ダミー: sanitize_filename")
        return filename

    def format_file_size(size_in_bytes):
        for unit in ["B", "KB", "MB", "GB"]:
            if size_in_bytes < 1024.0 or unit == "GB":
                break
            size_in_bytes /= 1024.0
        return f"{size_in_bytes:.1f} {unit}"

    def find_image_files(directory, extensions=None, include_subdirs=True):
        print("ダミー: find_image_files")
        return []

    def get_japanese_error_message(error):
        print("ダミー: get_japanese_error_message")
        return f"エラー: {str(error)}"

class LazyTabManager:
    """タブの遅延読み込みを管理するクラス"""
    
    def __init__(self, app):
        self.app = app
        self.loaded_tabs = set()
        self.tab_initializers = {}
    
    def register_tab(self, tab_name: str, initializer_func):
        """タブと初期化関数を登録"""
        self.tab_initializers[tab_name] = initializer_func
    
    def load_tab_if_needed(self, tab_name: str):
        """必要に応じてタブを読み込む"""
        if tab_name not in self.loaded_tabs and tab_name in self.tab_initializers:
            try:
                self.tab_initializers[tab_name]()
                self.loaded_tabs.add(tab_name)
                self.app.add_log_message(f"タブ「{tab_name}」を読み込みました")
            except Exception as e:
                error_msg = f"タブ「{tab_name}」の読み込みに失敗しました: {str(e)}"
                self.app.add_log_message(error_msg)
                print(f"タブ読み込みエラー: {e}")
                traceback.print_exc()
    
    def reset_tab(self, tab_name: str):
        """タブの読み込み状態をリセット"""
        if tab_name in self.loaded_tabs:
            self.loaded_tabs.remove(tab_name)


class App(ctk.CTk, ThreadSafeGUI):
    def __init__(self):
        # すべての属性を最初に初期化（エラー防止）
        self.preset_manager = None
        self.history_manager = None
        self.progress_tracker = None
        self.settings_manager = None
        self.lazy_tab_manager = None
        self.drag_drop_area = None
        self.drag_drop_handler = None
        self.resize_value_unit_label = None
        self.resize_quality_text_label = None
        self.resize_quality_slider = None
        self.resize_quality_value_label = None
        self.resize_start_button = None
        self.resize_cancel_button = None
        self.cancel_requested = False
        self.processing_thread = None
        self.thread_lock = threading.Lock()
        self.thread_lock = threading.Lock()  # スレッドセーフティ用のロック
        
        # 親クラスの初期化
        try:
            ctk.CTk.__init__(self)
        except Exception as e:
            print(f"CTk初期化エラー: {e}")
            
        try:
            ThreadSafeGUI.__init__(self)
        except Exception as e:
            print(f"ThreadSafeGUI初期化エラー: {e}")
        
        self.title("画像処理ツール")

        # ウィンドウサイズを設定
        self.geometry("1200x1000")  # デフォルトサイズを拡大
        self.minsize(1000, 900)  # 最小サイズも拡大して全内容が表示されるように

        # ウィンドウの背景色を設定（ライトモード用）
        self.configure(fg_color="#F8F9FA")

        # フレームの拡大性を確保するためにgridを設定
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # フォント設定の初期化
        self.normal_font = ctk.CTkFont(size=15)
        self.button_font = ctk.CTkFont(size=15, weight="bold")
        self.heading_font = ctk.CTkFont(size=18, weight="bold")
        self.small_font = ctk.CTkFont(size=13)

        # 先にログとプログレスバーのフレームを作成
        self.main_frame = ctk.CTkFrame(self, corner_radius=0, fg_color="transparent")
        self.main_frame.pack(fill="both", expand=True, padx=20, pady=20)

        self.main_frame.grid_rowconfigure(0, weight=1)
        self.main_frame.grid_rowconfigure(1, weight=0)
        self.main_frame.grid_columnconfigure(0, weight=1)

        # LazyTabManagerを早期に初期化
        self.lazy_tab_manager = LazyTabManager(self)

        # ログとプログレスバーを先に初期化
        self.log_progress_frame = ctk.CTkFrame(
            self.main_frame, corner_radius=10, border_width=1, border_color="#E9ECEF"
        )
        self.log_progress_frame.grid(row=1, column=0, sticky="ew", pady=(10, 0))
        self.log_progress_frame.grid_columnconfigure(0, weight=1)

        # ログタイトル
        log_title = ctk.CTkLabel(self.log_progress_frame, text="📋 処理ログ", font=self.heading_font, anchor="w")
        log_title.grid(row=0, column=0, sticky="w", padx=10, pady=(10, 5))

        self.log_textbox = ctk.CTkTextbox(
            self.log_progress_frame,
            height=140,
            corner_radius=6,
            wrap="word",
            state="disabled",
            font=self.normal_font,
            border_width=1,
            border_color="#E9ECEF",
        )
        self.log_textbox.grid(row=1, column=0, sticky="nsew", padx=10, pady=(0, 5))

        self.progress_bar = ctk.CTkProgressBar(
            self.log_progress_frame, corner_radius=6, height=8, progress_color="#5B5FCF"
        )
        self.progress_bar.grid(row=2, column=0, sticky="ew", padx=10, pady=(0, 10))

        # タブを作成
        self.tab_view = ctk.CTkTabview(self.main_frame)
        self.tab_view.grid(row=0, column=0, sticky="nsew", pady=(0, 10))

        # タブビューのフォント設定と色設定
        try:
            # 内部的なセグメントボタンにアクセスしてフォントとテキストカラーを設定
            if hasattr(self.tab_view, "_segmented_button") and self.tab_view._segmented_button:
                self.tab_view._segmented_button.configure(
                    font=self.heading_font,
                    text_color=("#212529", "#FFFFFF"),  # (非選択タブのテキスト色, 選択タブのテキスト色)
                    fg_color="#E9ECEF",  # 非選択タブの背景色（薄いグレー）
                    selected_color="#6C63FF",  # 選択タブの背景色（紫）
                    selected_hover_color="#5A52D5",  # 選択タブのホバー時の背景色
                    unselected_hover_color="#DEE2E6",  # 非選択タブのホバー時の背景色
                )
            else:
                # Fallback or log if _segmented_button is not available as expected
                print("Debug: _segmented_button not found or is None, cannot set tab font directly.")
        except Exception as e:
            print(f"タブフォント設定エラー(改): {e}")

        # タブを追加
        self.tab_resize = self.tab_view.add("画像リサイズ")
        
        # Phase 3の新しいタブを追加（PHASE3_AVAILABLEの場合のみ）
        if PHASE3_AVAILABLE:
            self.tab_preview = self.tab_view.add("プレビュー")
            self.tab_history = self.tab_view.add("履歴")
            self.tab_stats = self.tab_view.add("統計")
            
            # タブ切り替えイベントを設定
            self.tab_view.configure(command=self._on_tab_changed)
            
            # 遅延読み込みタブを登録
            self.lazy_tab_manager.register_tab("プレビュー", self._init_preview_tab)
            self.lazy_tab_manager.register_tab("履歴", self._init_history_tab)
            self.lazy_tab_manager.register_tab("統計", self._init_statistics_tab)

        # 変数は既に初期化済み

        # Phase 3のマネージャーを初期化（タブ作成前に必要）
        if PHASE3_AVAILABLE:
            try:
                self.preset_manager = PresetManager()
                self.preset_manager.load()
                self.history_manager = HistoryManager()
            except Exception as e:
                print(f"Phase 3マネージャー初期化エラー: {e}")
                self.preset_manager = None
                self.history_manager = None

        # ログ初期化完了後にタブの中身を作成
        self.create_tab_content_frames()

        # 初期化完了後に初期状態を設定
        self.add_log_message("アプリケーションを初期化しました")

        # リサイズタブの初期値を設定
        if hasattr(self, "resize_mode_var"):
            self.on_resize_mode_change(self.resize_mode_var.get())
        if hasattr(self, "resize_output_format_var"):
            self.on_output_format_change(self.resize_output_format_var.get())
        if hasattr(self, "resize_enable_compression_var"):
            self.update_resize_compression_settings_state()

        # ウィンドウを中央に配置
        self.center_window()
        
        # スレッドセーフティのセットアップ
        self.setup_thread_safety()
        
        # 進捗トラッカーと設定マネージャーを初期化
        self.progress_tracker = ProgressTracker() if 'ProgressTracker' in globals() else None
        self.settings_manager = SettingsManager() if 'SettingsManager' in globals() else None
        
        
        # メニューバーを作成
        self._create_menu_bar()
        
        # キーボードショートカットを設定
        self._setup_keyboard_shortcuts()
        
        # 設定を読み込む
        if self.settings_manager:
            self.load_settings()
            
        # 初期状態でボタン検証を実行
        self.after(100, self.validate_start_button)

    def _select_file(
        self,
        entry_widget,
        title="ファイルを選択",
        filetypes=(
            ("画像ファイル", "*.jpg *.jpeg *.png *.gif *.bmp *.tiff"),
            ("すべてのファイル", "*.*"),
        ),
    ):
        filepath = filedialog.askopenfilename(title=title, filetypes=filetypes)
        if filepath:
            entry_widget.delete(0, "end")
            entry_widget.insert(0, filepath)
            self.add_log_message(f"ファイル選択: {filepath}")

    def _select_directory(self, entry_widget, title="フォルダを選択"):
        """ディレクトリ選択ダイアログを表示し、選択されたパスをエントリーに設定する"""
        dirpath = filedialog.askdirectory(title=title)
        if dirpath:
            entry_widget.delete(0, "end")
            entry_widget.insert(0, dirpath)
            self.add_log_message(f"フォルダ選択: {dirpath}")

    def browse_input(self):
        """処理モードに応じて入力を選択"""
        if self.processing_mode_var.get() == "single":
            # 単一ファイルモード
            filetypes = [("画像ファイル", "*.jpg;*.jpeg;*.png;*.webp;*.bmp;*.gif"), ("すべてのファイル", "*.*")]
            filename = filedialog.askopenfilename(title="入力ファイルを選択", filetypes=filetypes)
            if filename:
                self.input_entry.delete(0, "end")
                self.input_entry.insert(0, filename)
                self.add_log_message(f"ファイル選択: {filename}")
                # 最近使用したファイルに追加
                if self.settings_manager:
                    self.settings_manager.add_recent_input(filename)
                # 開始ボタンの状態を更新
                self.validate_start_button()
                
                # プレビュータブが存在し、選択されている場合はプレビューを更新
                if (hasattr(self, 'tab_view') and hasattr(self, 'comparison_preview') and 
                    self.tab_view.get() == "プレビュー"):
                    self.comparison_preview.load_before_image(filename)
                    self._update_original_image_info(filename)
                    self.after(500, self._update_preview_after)
        else:
            # フォルダ一括処理モード
            dirpath = filedialog.askdirectory(title="入力フォルダを選択")
            if dirpath:
                self.input_entry.delete(0, "end")
                self.input_entry.insert(0, dirpath)
                self.add_log_message(f"フォルダ選択: {dirpath}")
                # 最近使用したフォルダに追加
                if self.settings_manager:
                    self.settings_manager.add_recent_input(dirpath)
                # 開始ボタンの状態を更新
                self.validate_start_button()
                
                # バッチモードの場合はプレビューは更新しない（単一ファイルではないため）

    def browse_output_dir(self):
        """出力先フォルダを選択"""
        self._select_directory(self.output_dir_entry, title="出力先フォルダを選択")
        # 開始ボタンの状態を更新
        self.validate_start_button()
    
    def on_files_dropped(self, files: list):
        """ファイルがドロップされたときの処理"""
        try:
            if not files:
                return
                
            # 処理モードに応じて処理を分岐
            if hasattr(self, 'processing_mode_var') and self.processing_mode_var.get() == "single":
                # 単一ファイルモード：最初のファイルのみ使用
                file_path = str(files[0])
                if hasattr(self, 'input_entry'):
                    self.input_entry.delete(0, "end")
                    self.input_entry.insert(0, file_path)
                self.add_log_message(f"ファイルドロップ: {file_path}")
                if self.settings_manager:
                    self.settings_manager.add_recent_input(file_path)
            else:
                # バッチモード：親フォルダを使用
                parent_dir = str(Path(files[0]).parent)
                if hasattr(self, 'input_entry'):
                    self.input_entry.delete(0, "end")
                    self.input_entry.insert(0, parent_dir)
                self.add_log_message(f"フォルダドロップ: {parent_dir} ({len(files)}ファイル)")
        except Exception as e:
            self.add_log_message(f"ファイルドロップエラー: {str(e)}")
        
        # ドラッグ&ドロップエリアの状態を更新
        if hasattr(self, 'drag_drop_area'):
            self.drag_drop_area.update_status(f"✅ {len(files)}ファイルを読み込みました")
            
        # 開始ボタンの状態を更新
        self.validate_start_button()
        
        # 単一ファイルモードでプレビュータブが選択されている場合はプレビューを更新
        if (hasattr(self, 'processing_mode_var') and self.processing_mode_var.get() == "single" and
            hasattr(self, 'tab_view') and hasattr(self, 'comparison_preview') and 
            self.tab_view.get() == "プレビュー" and files):
            file_path = str(files[0])
            if Path(file_path).is_file():
                self.comparison_preview.load_before_image(file_path)
                self._update_original_image_info(file_path)
                self.after(500, self._update_preview_after)
    
    def load_settings(self):
        """設定を読み込む"""
        if not self.settings_manager:
            return
            
        settings = self.settings_manager.load()
        
        # リサイズ設定を適用
        resize_settings = settings.resize
        
        # モード設定
        mode_map = {
            "none": "リサイズなし",
            "width": "幅を指定",
            "height": "高さを指定",
            "longest_side": "縦横最大",
            "percentage": "パーセント"
        }
        if resize_settings.mode in mode_map and hasattr(self, 'resize_mode_var'):
            self.resize_mode_var.set(mode_map[resize_settings.mode])
            
        # 値設定
        if hasattr(self, 'resize_value_entry'):
            self.resize_value_entry.delete(0, "end")
            self.resize_value_entry.insert(0, str(resize_settings.value))
            
        # 品質設定
        if hasattr(self, 'resize_quality_var'):
            self.resize_quality_var.set(resize_settings.quality)
            
        # フォーマット設定
        format_map = {
            "jpeg": "JPEG",
            "png": "PNG",
            "webp": "WEBP"
        }
        if resize_settings.format in format_map and hasattr(self, 'resize_output_format_var'):
            self.resize_output_format_var.set(format_map[resize_settings.format])
            
        # UI設定を適用
        ui_settings = settings.ui
        if ui_settings.window_width and ui_settings.window_height:
            self.geometry(f"{ui_settings.window_width}x{ui_settings.window_height}")
            
        self.add_log_message("設定を読み込みました")
    
    def save_settings(self):
        """設定を保存する"""
        if not self.settings_manager:
            return
            
        # リサイズ設定を更新
        mode_map = {
            "リサイズなし": "none",
            "幅を指定": "width",
            "高さを指定": "height",
            "縦横最大": "longest_side",
            "パーセント": "percentage"
        }
        
        if hasattr(self, 'resize_mode_var'):
            mode = mode_map.get(self.resize_mode_var.get(), "longest_side")
            self.settings_manager.update_resize_settings(mode=mode)
            
        if hasattr(self, 'resize_value_entry'):
            try:
                value = int(self.resize_value_entry.get() or "1920")
                self.settings_manager.update_resize_settings(value=value)
            except ValueError:
                pass
                
        if hasattr(self, 'resize_quality_var'):
            self.settings_manager.update_resize_settings(quality=int(self.resize_quality_var.get()))
            
        if hasattr(self, 'resize_output_format_var'):
            format_map = {"JPEG": "jpeg", "PNG": "png", "WEBP": "webp"}
            format_val = format_map.get(self.resize_output_format_var.get(), "jpeg")
            self.settings_manager.update_resize_settings(format=format_val)
            
        # UI設定を更新
        self.settings_manager.update_ui_settings(
            window_width=self.winfo_width(),
            window_height=self.winfo_height()
        )
        
        # 保存
        if self.settings_manager.save():
            self.add_log_message("設定を保存しました")
        else:
            self.add_log_message("設定の保存に失敗しました", is_error=True)
    
    def on_processing_mode_change(self):
        """処理モードが変更されたときの処理"""
        mode = self.processing_mode_var.get()
        
        # 入力ラベルとプレースホルダーを更新
        if mode == "single":
            self.input_label.configure(text="入力ファイル:")
            self.input_entry.configure(placeholder_text="画像ファイルを選択してください...")
            if hasattr(self, "start_button"):
                self.start_button.configure(text="処理開始")
        else:
            self.input_label.configure(text="入力フォルダ:")
            self.input_entry.configure(placeholder_text="処理するフォルダを選択してください...")
            if hasattr(self, "start_button"):
                self.start_button.configure(text="一括処理開始")
        
        # 入力をクリア
        self.input_entry.delete(0, "end")
        
        # サブフォルダ処理オプションの表示/非表示
        if hasattr(self, "include_subdirs_checkbox"):
            if mode == "batch":
                self.include_subdirs_checkbox.grid()
            else:
                self.include_subdirs_checkbox.grid_remove()
        
        self.add_log_message(f"処理モード変更: {'単一ファイル' if mode == 'single' else 'フォルダ一括処理'}")
        
        # 開始ボタンの状態を更新
        self.validate_start_button()

    def on_output_format_change(self, selected_format):
        # ログメッセージは初期化完了後のみ表示
        if hasattr(self, "log_textbox") and self.log_textbox is not None:
            self.add_log_message(f"出力フォーマット変更: {selected_format}")
        show_quality = selected_format in ["JPEG", "WEBP"]

        if self.resize_quality_text_label:
            if show_quality:
                self.resize_quality_text_label.grid()
            else:
                self.resize_quality_text_label.grid_remove()

        if self.resize_quality_slider:
            if show_quality:
                self.resize_quality_slider.grid()
            else:
                self.resize_quality_slider.grid_remove()

        if self.resize_quality_value_label:
            if show_quality:
                self.resize_quality_value_label.grid()
                self.update_quality_label(self.resize_quality_var.get())
            else:
                self.resize_quality_value_label.grid_remove()

    def update_quality_label(self, value):
        if self.resize_quality_value_label:
            self.resize_quality_value_label.configure(text=f"{int(value)}")

    def on_resize_mode_change(self, selected_mode):
        # ログメッセージは初期化完了後のみ表示
        if hasattr(self, "log_textbox") and self.log_textbox is not None:
            self.add_log_message(f"リサイズモード変更: {selected_mode}")
        
        # リサイズなしモードの場合
        if selected_mode == "リサイズなし":
            if hasattr(self, "resize_value_entry"):
                self.resize_value_entry.configure(state="disabled")
                self.resize_value_entry.delete(0, "end")
            if hasattr(self, "resize_value_unit_label"):
                self.resize_value_unit_label.configure(text="")
            if hasattr(self, "resize_aspect_ratio_checkbox"):
                self.resize_aspect_ratio_checkbox.configure(state="disabled")
        else:
            if hasattr(self, "resize_value_entry"):
                self.resize_value_entry.configure(state="normal")
            if hasattr(self, "resize_aspect_ratio_checkbox"):
                self.resize_aspect_ratio_checkbox.configure(state="normal")
            
            if hasattr(self, "resize_value_unit_label") and self.resize_value_unit_label:
                if selected_mode == "パーセント":
                    self.resize_value_unit_label.configure(text="%")
                else:
                    self.resize_value_unit_label.configure(text="px")

        if hasattr(self, "resize_value_entry") and selected_mode != "リサイズなし":
            self.resize_value_entry.delete(0, "end")

    def update_resize_compression_settings_state(self):
        """圧縮設定の有効/無効を切り替える"""
        enable_compression = self.resize_enable_compression_var.get()
        state = "normal" if enable_compression else "disabled"
        
        # 圧縮関連のUI要素の状態を更新
        if hasattr(self, "resize_target_size_label"):
            self.resize_target_size_label.configure(state=state)
        if hasattr(self, "resize_target_size_entry"):
            self.resize_target_size_entry.configure(state=state)
        if hasattr(self, "resize_balance_label"):
            self.resize_balance_label.configure(state=state)
        if hasattr(self, "resize_balance_slider"):
            self.resize_balance_slider.configure(state=state)
        if hasattr(self, "resize_balance_value_label"):
            self.resize_balance_value_label.configure(state=state)
            
        self.add_log_message(f"圧縮設定: {'有効' if enable_compression else '無効'}")

    def update_balance_label(self, value):
        """バランススライダーの値に応じてラベルを更新"""
        int_value = int(value)
        if int_value <= 3:
            text = "サイズ優先"
        elif int_value >= 8:
            text = "品質優先"
        else:
            text = "バランス"
        
        if hasattr(self, "resize_balance_value_label"):
            self.resize_balance_value_label.configure(text=f"{text} ({int_value})")

    def create_tab_content_frames(self):
        self.resize_tab_content = ctk.CTkFrame(self.tab_resize, corner_radius=0, fg_color="transparent")
        self.resize_tab_content.pack(fill="both", expand=True)

        self.resize_tab_content.grid_columnconfigure(0, weight=0)
        self.resize_tab_content.grid_columnconfigure(1, weight=1)
        self.resize_tab_content.grid_columnconfigure(2, weight=0)

        current_row = 0

        # ラベルでタイトル（アイコン付き）
        title_label = ctk.CTkLabel(
            self.resize_tab_content, text="🖼️ 画像リサイズ", font=self.heading_font, text_color="#212529"
        )
        title_label.grid(row=current_row, column=0, columnspan=3, padx=10, pady=(0, 20), sticky="w")
        current_row += 1

        # 処理モード選択
        mode_frame = ctk.CTkFrame(self.resize_tab_content, corner_radius=10, border_width=1, border_color="#E9ECEF")
        mode_frame.grid(row=current_row, column=0, columnspan=3, padx=10, pady=(0, 20), sticky="ew")
        mode_frame.grid_columnconfigure(1, weight=1)
        mode_frame.grid_columnconfigure(2, weight=1)
        
        ctk.CTkLabel(mode_frame, text="処理モード:", font=self.normal_font, text_color="#212529").grid(
            row=0, column=0, padx=(10, 5), pady=10, sticky="w"
        )
        
        self.processing_mode_var = ctk.StringVar(value="single")
        
        self.single_mode_radio = ctk.CTkRadioButton(
            mode_frame, text="単一ファイル", variable=self.processing_mode_var, value="single",
            command=self.on_processing_mode_change, font=self.normal_font
        )
        self.single_mode_radio.grid(row=0, column=1, padx=10, pady=10, sticky="w")
        
        self.batch_mode_radio = ctk.CTkRadioButton(
            mode_frame, text="フォルダ一括処理", variable=self.processing_mode_var, value="batch",
            command=self.on_processing_mode_change, font=self.normal_font
        )
        self.batch_mode_radio.grid(row=0, column=2, padx=10, pady=10, sticky="w")
        
        current_row += 1

        # 入力選択（モードに応じて変化）
        self.input_label = ctk.CTkLabel(self.resize_tab_content, text="入力ファイル:", font=self.normal_font, text_color="#212529")
        self.input_label.grid(row=current_row, column=0, padx=(10, 5), pady=15, sticky="w")
        
        self.input_entry = ctk.CTkEntry(
            self.resize_tab_content,
            font=self.normal_font,
            corner_radius=6,
            border_width=2,
            border_color="#CED4DA",
            placeholder_text="画像ファイルを選択してください...",
        )
        self.input_entry.grid(row=current_row, column=1, padx=5, pady=15, sticky="ew")
        
        self.input_button = ctk.CTkButton(
            self.resize_tab_content,
            text="📁 参照",
            command=self.browse_input,
            width=100,
            height=36,
            font=self.normal_font,
            corner_radius=6,
            fg_color="#6C63FF",
            hover_color="#5A52D5",
            text_color="#FFFFFF",
        )
        self.input_button.grid(row=current_row, column=2, padx=5, pady=15)
        current_row += 1
        
        # ドラッグ&ドロップエリア（常に表示、機能はTKDND_AVAILABLEに依存）
        try:
            self.drag_drop_area = DragDropArea(
                self.resize_tab_content,
                on_drop=self.on_files_dropped,
                file_filter=lambda p: PathValidator.is_image_file(p)
            )
            self.drag_drop_area.grid(row=current_row, column=0, columnspan=3, padx=10, pady=(0, 15), sticky="ew")
            self.drag_drop_area.configure(height=80)
            # クリックイベントを設定
            self.drag_drop_area._on_click = lambda e: self.browse_input()
        except Exception as e:
            print(f"DragDropArea作成エラー: {e}")
            self.drag_drop_area = None
        current_row += 1

        ctk.CTkLabel(self.resize_tab_content, text="出力先フォルダ:", font=self.normal_font, text_color="#212529").grid(
            row=current_row, column=0, padx=(10, 5), pady=15, sticky="w"
        )

        self.output_dir_entry = ctk.CTkEntry(
            self.resize_tab_content,
            font=self.normal_font,
            corner_radius=6,
            border_width=2,
            border_color="#CED4DA",
            placeholder_text="出力先フォルダを選択してください...",
        )
        self.output_dir_entry.grid(row=current_row, column=1, padx=5, pady=15, sticky="ew")

        self.output_dir_button = ctk.CTkButton(
            self.resize_tab_content,
            text="📁 参照",
            command=self.browse_output_dir,
            width=100,
            height=36,
            font=self.normal_font,
            corner_radius=6,
            fg_color="#6C63FF",
            hover_color="#5A52D5",
            text_color="#FFFFFF",
        )
        self.output_dir_button.grid(row=current_row, column=2, padx=5, pady=15)
        current_row += 1
        
        # 入力検証のためのバインディング
        self.input_entry.bind('<KeyRelease>', lambda e: self.validate_start_button())
        self.output_dir_entry.bind('<KeyRelease>', lambda e: self.validate_start_button())
        
        # サブフォルダ処理オプション（バッチモードのみ表示）
        self.include_subdirs_var = ctk.BooleanVar(value=False)
        self.include_subdirs_checkbox = ctk.CTkCheckBox(
            self.resize_tab_content,
            text="サブフォルダも処理する",
            variable=self.include_subdirs_var,
            font=self.normal_font,
            text_color="#212529",
            corner_radius=6,
            fg_color="#6C63FF",
            hover_color="#5A52D5"
        )
        self.include_subdirs_checkbox.grid(row=current_row, column=1, padx=5, pady=(0, 15), sticky="w")
        self.include_subdirs_checkbox.grid_remove()  # 初期状態では非表示
        current_row += 1

        # プリセット選択フレーム（Phase 3）
        if PHASE3_AVAILABLE and hasattr(self, 'preset_manager') and self.preset_manager:
            preset_frame = ctk.CTkFrame(
                self.resize_tab_content, corner_radius=10, fg_color="#FFFFFF", border_width=1, border_color="#DEE2E6"
            )
            preset_frame.grid(row=current_row, column=0, columnspan=3, padx=10, pady=(10, 10), sticky="ew")
            preset_frame.grid_columnconfigure(1, weight=1)
            
            # プリセットラベル
            ctk.CTkLabel(
                preset_frame, 
                text="📋 プリセット:", 
                font=self.normal_font, 
                text_color="#212529"
            ).grid(row=0, column=0, padx=(20, 5), pady=15, sticky="w")
            
            # プリセット選択メニュー
            self.preset_var = ctk.StringVar(value="カスタム")
            preset_names = ["カスタム"] + self.preset_manager.get_preset_names()
            self.preset_menu = ctk.CTkOptionMenu(
                preset_frame,
                variable=self.preset_var,
                values=preset_names,
                command=self._on_preset_selected,
                font=self.normal_font,
                width=300,
                height=36,
                corner_radius=6,
                fg_color="#F8F9FA",
                button_color="#6C63FF",
                button_hover_color="#5A52D5",
                dropdown_fg_color="#FFFFFF",
                dropdown_text_color="#212529",
                dropdown_hover_color="#E9ECEF"
            )
            self.preset_menu.grid(row=0, column=1, padx=5, pady=15, sticky="ew")
            
            # プリセット管理ボタン
            ctk.CTkButton(
                preset_frame,
                text="管理",
                command=self.open_preset_manager,
                width=80,
                height=36,
                font=self.normal_font,
                corner_radius=6,
                fg_color="#6C63FF",
                hover_color="#5A52D5",
                text_color="#FFFFFF"
            ).grid(row=0, column=2, padx=5, pady=15)
            
            current_row += 1

        # リサイズ設定フレーム
        resize_settings_frame = ctk.CTkFrame(
            self.resize_tab_content, corner_radius=10, fg_color="#FFFFFF", border_width=1, border_color="#DEE2E6"
        )
        resize_settings_frame.grid(row=current_row, column=0, columnspan=3, padx=10, pady=(20, 10), sticky="ew")
        resize_settings_frame.grid_columnconfigure(1, weight=1)

        # リサイズ設定のタイトル
        resize_settings_title = ctk.CTkLabel(
            resize_settings_frame, text="⚙️ リサイズ設定", font=ctk.CTkFont(size=16, weight="bold"), text_color="#212529"
        )
        resize_settings_title.grid(row=0, column=0, columnspan=3, padx=20, pady=(15, 20), sticky="w")

        rs_current_row = 1

        # モード選択
        ctk.CTkLabel(resize_settings_frame, text="モード:", font=self.normal_font, text_color="#212529").grid(
            row=rs_current_row, column=0, padx=(20, 5), pady=10, sticky="w"
        )
        mode_frame = ctk.CTkFrame(resize_settings_frame, fg_color="transparent")
        mode_frame.grid(row=rs_current_row, column=1, columnspan=2, padx=5, pady=10, sticky="ew")

        self.resize_mode_var = ctk.StringVar(value="幅を指定")
        resize_modes = [
            ("リサイズなし", "リサイズなし"),
            ("幅を指定", "幅を指定"),
            ("高さを指定", "高さを指定"),
            ("縦横最大", "縦横最大"),
            ("パーセント", "パーセント"),
        ]

        for i, (text, value) in enumerate(resize_modes):
            radio = ctk.CTkRadioButton(
                mode_frame,
                text=text,
                variable=self.resize_mode_var,
                value=value,
                command=lambda mode=value: self.on_resize_mode_change(mode),
                font=self.normal_font,
                fg_color="#6C63FF",
                hover_color="#5A52D5",
                border_color="#CED4DA",
            )
            # 2列表示にする
            row = i // 3
            col = i % 3
            radio.grid(row=row, column=col, padx=(0, 10), pady=(0, 5), sticky="w")
        rs_current_row += 1

        # リサイズ値入力部分のフレームを作成
        resize_value_frame = ctk.CTkFrame(resize_settings_frame, fg_color="transparent")
        resize_value_frame.grid(row=rs_current_row, column=0, columnspan=3, padx=20, pady=10, sticky="w")

        ctk.CTkLabel(resize_value_frame, text="値:", font=self.normal_font, text_color="#212529").pack(
            side="left", padx=(0, 5)
        )

        self.resize_value_entry = ctk.CTkEntry(
            resize_value_frame,
            font=self.normal_font,
            width=100,
            corner_radius=6,
            border_width=2,
            border_color="#CED4DA",
            placeholder_text="数値を入力",
        )
        
        # リサイズ値変更時のプレビュー更新を設定
        def on_resize_value_change(event):
            if (hasattr(self, 'tab_view') and hasattr(self, 'comparison_preview') and 
                self.tab_view.get() == "プレビュー"):
                # 1秒遅延でプレビューを更新（タイピング中の頻繁な更新を避ける）
                self.after(1000, self._update_preview_after)
                
        self.resize_value_entry.bind('<KeyRelease>', on_resize_value_change)
        self.resize_value_entry.pack(side="left", padx=(0, 5))

        self.resize_value_unit_label = ctk.CTkLabel(
            resize_value_frame, text="px", font=self.normal_font, text_color="#212529"
        )
        self.resize_value_unit_label.pack(side="left")
        rs_current_row += 1

        self.resize_aspect_ratio_var = ctk.BooleanVar(value=True)
        self.resize_aspect_ratio_checkbox = ctk.CTkCheckBox(
            resize_settings_frame,
            text="アスペクト比を維持する",
            variable=self.resize_aspect_ratio_var,
            font=self.normal_font,
            fg_color="#6C63FF",
            hover_color="#5A52D5",
            border_color="#CED4DA",
        )
        self.resize_aspect_ratio_checkbox.grid(row=rs_current_row, column=0, columnspan=3, padx=20, pady=10, sticky="w")
        rs_current_row += 1

        ctk.CTkLabel(resize_settings_frame, text="出力フォーマット:", font=self.normal_font, text_color="#212529").grid(
            row=rs_current_row, column=0, padx=5, pady=10, sticky="w"
        )
        self.resize_output_format_options = [
            "元のフォーマットを維持",
            "PNG",
            "JPEG",
            "WebP",
        ]
        self.resize_output_format_var = ctk.StringVar(value=self.resize_output_format_options[0])
        self.resize_output_format_menu = ctk.CTkOptionMenu(
            resize_settings_frame,
            values=self.resize_output_format_options,
            variable=self.resize_output_format_var,
            command=self.on_output_format_change,
            font=self.normal_font,
            dropdown_font=self.normal_font,
        )
        self.resize_output_format_menu.grid(row=rs_current_row, column=1, columnspan=2, padx=5, pady=10, sticky="ew")
        rs_current_row += 1

        # EXIF Handling Option
        ctk.CTkLabel(resize_settings_frame, text="EXIF情報:", font=self.normal_font, text_color="#212529").grid(
            row=rs_current_row, column=0, padx=5, pady=10, sticky="w"
        )
        self.exif_handling_options = ["EXIFを保持", "EXIFを削除"]
        self.exif_handling_var = ctk.StringVar(value=self.exif_handling_options[0])
        self.exif_handling_menu = ctk.CTkOptionMenu(
            resize_settings_frame,
            values=self.exif_handling_options,
            variable=self.exif_handling_var,
            font=self.normal_font,
            dropdown_font=self.normal_font,
        )
        self.exif_handling_menu.grid(row=rs_current_row, column=1, columnspan=2, padx=5, pady=10, sticky="ew")
        rs_current_row += 1

        self.resize_quality_text_label = ctk.CTkLabel(
            resize_settings_frame, text="品質 (JPEG/WEBP):", font=self.normal_font, text_color="#212529"
        )
        self.resize_quality_text_label.grid(row=rs_current_row, column=0, padx=5, pady=10, sticky="w")
        self.resize_quality_var = ctk.IntVar(value=85)
        self.resize_quality_slider = ctk.CTkSlider(
            resize_settings_frame,
            from_=1,
            to=100,
            number_of_steps=99,
            variable=self.resize_quality_var,
            command=self.update_quality_label,
            progress_color="#6C63FF",
            button_color="#6C63FF",
            button_hover_color="#5A52D5",
        )
        self.resize_quality_slider.grid(row=rs_current_row, column=1, padx=5, pady=10, sticky="ew")
        self.resize_quality_value_label = ctk.CTkLabel(
            resize_settings_frame,
            text=str(self.resize_quality_var.get()),
            font=self.normal_font,
        )
        self.resize_quality_value_label.grid(row=rs_current_row, column=2, padx=(5, 10), pady=10, sticky="w")
        rs_current_row += 1

        current_row += 1  # resize_settings_frame の分

        # 圧縮設定フレーム
        compress_settings_frame = ctk.CTkFrame(
            self.resize_tab_content, corner_radius=10, fg_color="#FFFFFF", border_width=1, border_color="#DEE2E6"
        )
        compress_settings_frame.grid(row=current_row, column=0, columnspan=3, padx=10, pady=(10, 10), sticky="ew")
        compress_settings_frame.grid_columnconfigure(1, weight=1)

        # 圧縮設定のタイトル
        compress_settings_title = ctk.CTkLabel(
            compress_settings_frame, text="🗜️ 圧縮設定", font=ctk.CTkFont(size=16, weight="bold"), text_color="#212529"
        )
        compress_settings_title.grid(row=0, column=0, columnspan=3, padx=20, pady=(15, 20), sticky="w")

        cs_current_row = 1

        # 圧縮を有効にするチェックボックス
        self.resize_enable_compression_var = ctk.BooleanVar(value=True)
        self.resize_enable_compression_checkbox = ctk.CTkCheckBox(
            compress_settings_frame,
            text="圧縮を有効にする",
            variable=self.resize_enable_compression_var,
            command=self.update_resize_compression_settings_state,
            font=self.normal_font,
            fg_color="#6C63FF",
            hover_color="#5A52D5",
            border_color="#CED4DA",
        )
        self.resize_enable_compression_checkbox.grid(row=cs_current_row, column=0, columnspan=3, padx=20, pady=10, sticky="w")
        cs_current_row += 1

        # ファイルサイズ目標（オプション）
        self.resize_target_size_label = ctk.CTkLabel(
            compress_settings_frame, text="目標ファイルサイズ:", font=self.normal_font, text_color="#212529"
        )
        self.resize_target_size_label.grid(row=cs_current_row, column=0, padx=(20, 5), pady=10, sticky="w")
        
        target_size_frame = ctk.CTkFrame(compress_settings_frame, fg_color="transparent")
        target_size_frame.grid(row=cs_current_row, column=1, columnspan=2, padx=5, pady=10, sticky="ew")
        
        self.resize_target_size_entry = ctk.CTkEntry(
            target_size_frame,
            font=self.normal_font,
            width=100,
            corner_radius=6,
            border_width=2,
            border_color="#CED4DA",
            placeholder_text="KB単位",
        )
        
        # 目標サイズ変更時のプレビュー更新を設定
        def on_target_size_change(event):
            if (hasattr(self, 'tab_view') and hasattr(self, 'comparison_preview') and 
                self.tab_view.get() == "プレビュー"):
                # 1秒遅延でプレビューを更新
                self.after(1000, self._update_preview_after)
                
        self.resize_target_size_entry.bind('<KeyRelease>', on_target_size_change)
        self.resize_target_size_entry.pack(side="left", padx=(0, 5))
        
        ctk.CTkLabel(
            target_size_frame, text="KB (オプション)", font=self.normal_font, text_color="#212529"
        ).pack(side="left")
        cs_current_row += 1

        # バランススライダー（サイズと品質のバランス）
        self.resize_balance_label = ctk.CTkLabel(
            compress_settings_frame, text="サイズ/品質バランス:", font=self.normal_font, text_color="#212529"
        )
        self.resize_balance_label.grid(row=cs_current_row, column=0, padx=(20, 5), pady=10, sticky="w")
        
        balance_frame = ctk.CTkFrame(compress_settings_frame, fg_color="transparent")
        balance_frame.grid(row=cs_current_row, column=1, columnspan=2, padx=5, pady=10, sticky="ew")
        
        self.resize_balance_var = ctk.IntVar(value=5)
        self.resize_balance_slider = ctk.CTkSlider(
            balance_frame,
            from_=1,
            to=10,
            number_of_steps=9,
            variable=self.resize_balance_var,
            command=self.update_balance_label,
            progress_color="#6C63FF",
            button_color="#6C63FF",
            button_hover_color="#5A52D5",
            width=300,
        )
        self.resize_balance_slider.pack(side="left", padx=(0, 10))
        
        self.resize_balance_value_label = ctk.CTkLabel(
            balance_frame,
            text="バランス",
            font=self.normal_font,
        )
        self.resize_balance_value_label.pack(side="left")
        cs_current_row += 1

        current_row += 1  # compress_settings_frame の分

        # ファイル名設定フレーム
        filename_settings_frame = ctk.CTkFrame(
            self.resize_tab_content, corner_radius=10, fg_color="#FFFFFF", border_width=1, border_color="#DEE2E6"
        )
        filename_settings_frame.grid(row=current_row, column=0, columnspan=3, padx=10, pady=(10, 10), sticky="ew")
        filename_settings_frame.grid_columnconfigure(1, weight=1)

        # ファイル名設定のタイトル
        filename_settings_title = ctk.CTkLabel(
            filename_settings_frame, text="📝 ファイル名設定", font=ctk.CTkFont(size=16, weight="bold"), text_color="#212529"
        )
        filename_settings_title.grid(row=0, column=0, columnspan=3, padx=20, pady=(15, 20), sticky="w")

        fs_current_row = 1

        # プレフィックス
        ctk.CTkLabel(
            filename_settings_frame, text="プレフィックス:", font=self.normal_font, text_color="#212529"
        ).grid(row=fs_current_row, column=0, padx=(20, 5), pady=10, sticky="w")
        
        self.resize_prefix_entry = ctk.CTkEntry(
            filename_settings_frame,
            font=self.normal_font,
            corner_radius=6,
            border_width=2,
            border_color="#CED4DA",
            placeholder_text="ファイル名の先頭に追加（オプション）",
        )
        self.resize_prefix_entry.grid(row=fs_current_row, column=1, columnspan=2, padx=5, pady=10, sticky="ew")
        fs_current_row += 1

        # サフィックス
        ctk.CTkLabel(
            filename_settings_frame, text="サフィックス:", font=self.normal_font, text_color="#212529"
        ).grid(row=fs_current_row, column=0, padx=(20, 5), pady=10, sticky="w")
        
        self.resize_suffix_entry = ctk.CTkEntry(
            filename_settings_frame,
            font=self.normal_font,
            corner_radius=6,
            border_width=2,
            border_color="#CED4DA",
            placeholder_text="ファイル名の末尾に追加（デフォルト: _resized）",
        )
        self.resize_suffix_entry.grid(row=fs_current_row, column=1, columnspan=2, padx=5, pady=10, sticky="ew")
        self.resize_suffix_entry.insert(0, "_resized")  # デフォルト値
        fs_current_row += 1

        current_row += 1  # filename_settings_frame の分

        action_buttons_frame = ctk.CTkFrame(self.resize_tab_content, fg_color="transparent")
        action_buttons_frame.grid(row=current_row, column=0, columnspan=3, padx=10, pady=(10, 0), sticky="ew")
        action_buttons_frame.grid_columnconfigure(0, weight=1)
        action_buttons_frame.grid_columnconfigure(1, weight=0)  # Start button column
        action_buttons_frame.grid_columnconfigure(2, weight=0)  # Cancel button column
        action_buttons_frame.grid_columnconfigure(3, weight=1)

        self.start_button = ctk.CTkButton(
            action_buttons_frame,
            text="🚀 処理開始",
            command=self.start_process,
            width=150,
            height=42,
            font=self.button_font,
            fg_color="#6C63FF",
            hover_color="#5A52D5",
            text_color="#FFFFFF",
            corner_radius=8,
        )
        self.start_button.grid(row=0, column=1, padx=5, pady=10)
        # 初期状態では無効化
        self.start_button.configure(state="disabled")

        self.cancel_button = ctk.CTkButton(
            action_buttons_frame,
            text="⏹ 中断",
            command=self.request_cancel_processing,
            state="disabled",
            width=130,
            height=42,
            font=self.button_font,
            fg_color="#DC3545",
            hover_color="#C82333",
            text_color="#FFFFFF",
            text_color_disabled="#FFFFFF",
            corner_radius=8,
        )
        self.cancel_button.grid(row=0, column=2, padx=5, pady=10)
        current_row += 1

        # バッチ処理タブの初期化が必要な場合は、別の場所で実装
        
        # 以下はバッチ処理のコードですが、batch_process_content_frameが未定義のためコメントアウト
        '''
        # --- 区切り線 ---
        self.batch_separator1 = ctk.CTkFrame(
            self.batch_process_content_frame, fg_color="#E9ECEF", height=2, corner_radius=1
        )
        self.batch_separator1.grid(row=3, column=0, columnspan=3, sticky="ew", pady=10)

        # --- リサイズ設定フレーム ---
        batch_resize_settings_outer_frame = ctk.CTkFrame(
            self.batch_process_content_frame,
            corner_radius=10,
            fg_color="#FFFFFF",
            border_width=1,
            border_color="#DEE2E6",
        )
        batch_resize_settings_outer_frame.grid(row=3, column=0, columnspan=3, padx=10, pady=(10, 10), sticky="ew")
        batch_resize_settings_outer_frame.grid_columnconfigure(0, weight=1)  # ラベル用に左寄せ
        batch_resize_settings_outer_frame.grid_columnconfigure(1, weight=1)  # ウィジェット用に拡張

        # リサイズ設定タイトル
        batch_resize_title = ctk.CTkLabel(
            batch_resize_settings_outer_frame,
            text="⚙️ リサイズ設定",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color="#212529",
        )
        batch_resize_title.grid(row=0, column=0, columnspan=2, padx=20, pady=(15, 10), sticky="w")

        # モード設定
        mode_label = ctk.CTkLabel(
            batch_resize_settings_outer_frame, text="モード:", font=self.normal_font, text_color="#212529"
        )
        mode_label.grid(row=1, column=0, padx=(20, 5), pady=10, sticky="w")

        mode_frame = ctk.CTkFrame(batch_resize_settings_outer_frame, fg_color="transparent")
        mode_frame.grid(row=1, column=1, padx=5, pady=10, sticky="ew")

        self.batch_resize_mode_var = ctk.StringVar(value="指定なし")
        self.batch_resize_modes = ["指定なし", "幅を指定", "高さを指定", "縦横最大", "パーセント指定"]
        self.batch_radio_buttons_resize_mode = []
        for i, mode_text in enumerate(self.batch_resize_modes):
            radio_button = ctk.CTkRadioButton(
                mode_frame,
                text=mode_text,
                variable=self.batch_resize_mode_var,
                value=mode_text,
                font=self.normal_font,
                command=self.update_batch_resize_value_unit_label,
                radiobutton_width=20,
                radiobutton_height=20,
                border_width_checked=2,
                border_width_unchecked=2,
                fg_color="#6C63FF",
                hover_color="#5A52D5",
            )
            # 2列で表示 (i % 2 で列インデックス、 i // 2 で行インデックス)
            radio_button.grid(row=(i // 3), column=(i % 3), padx=5, pady=5, sticky="w")
            self.batch_radio_buttons_resize_mode.append(radio_button)

        # 値設定
        value_label = ctk.CTkLabel(
            batch_resize_settings_outer_frame, text="値:", font=self.normal_font, text_color="#212529"
        )
        value_label.grid(row=2, column=0, padx=(20, 5), pady=10, sticky="w")

        batch_resize_value_frame = ctk.CTkFrame(batch_resize_settings_outer_frame, fg_color="transparent")
        batch_resize_value_frame.grid(row=2, column=1, padx=5, pady=10, sticky="ew")

        self.batch_resize_value_var = ctk.StringVar(value="1000")
        self.entry_batch_resize_value = ctk.CTkEntry(
            batch_resize_value_frame,
            textvariable=self.batch_resize_value_var,
            font=self.normal_font,
            width=120,  # 少し幅を広げる
            corner_radius=6,
            border_width=2,
            border_color="#CED4DA",
            placeholder_text="数値を入力",
        )
        self.entry_batch_resize_value.pack(side="left", padx=(0, 5))

        self.batch_resize_value_unit_label = ctk.CTkLabel(
            batch_resize_value_frame, text="px", font=self.normal_font, text_color="#212529"
        )
        self.batch_resize_value_unit_label.pack(side="left", padx=(0, 5))

        # アスペクト比を維持
        self.batch_keep_aspect_ratio_var = ctk.BooleanVar(value=True)
        self.checkbox_batch_keep_aspect_ratio = ctk.CTkCheckBox(
            batch_resize_settings_outer_frame,
            text="アスペクト比を維持",
            variable=self.batch_keep_aspect_ratio_var,
            font=self.normal_font,
            checkbox_width=20,
            checkbox_height=20,
            corner_radius=6,
            border_width=2,
            fg_color="#6C63FF",
            hover_color="#5A52D5",
        )
        self.checkbox_batch_keep_aspect_ratio.grid(row=3, column=0, columnspan=2, padx=20, pady=(10, 15), sticky="w")

        self.update_batch_resize_value_unit_label()  # 初期単位表示

        # --- 区切り線 ---
        self.batch_separator2 = ctk.CTkFrame(
            self.batch_process_content_frame, fg_color="#E9ECEF", height=2, corner_radius=1
        )
        self.batch_separator2.grid(row=10, column=0, columnspan=3, sticky="ew", pady=10)

        # --- 圧縮設定 ---
        self.label_batch_compress_settings = ctk.CTkLabel(
            self.batch_process_content_frame, text="圧縮設定", font=self.heading_font
        )
        self.label_batch_compress_settings.grid(row=11, column=0, columnspan=3, pady=(0, 5), sticky="w")

        # 圧縮を有効にするか
        self.batch_enable_compression_var = ctk.BooleanVar(value=True)  # デフォルトは有効
        self.checkbox_batch_enable_compression = ctk.CTkCheckBox(
            self.batch_process_content_frame,
            text="圧縮設定を有効にする",
            variable=self.batch_enable_compression_var,
            font=self.normal_font,
            command=self.update_batch_compression_settings_state,
            fg_color="#5B5FCF",
            border_color="#E9ECEF",
            hover_color="#4B4FBF",
        )
        self.checkbox_batch_enable_compression.grid(row=12, column=0, columnspan=3, padx=5, pady=5, sticky="w")

        # 出力フォーマット
        self.label_batch_output_format = ctk.CTkLabel(
            self.batch_process_content_frame,
            text="出力フォーマット:",
            font=self.normal_font,
        )
        self.label_batch_output_format.grid(row=13, column=0, padx=(0, 5), pady=5, sticky="w")

        self.batch_output_format_var = ctk.StringVar(value="オリジナルを維持")
        self.batch_output_formats = ["オリジナルを維持", "JPEG", "PNG", "WEBP"]
        self.optionmenu_batch_output_format = ctk.CTkOptionMenu(
            self.batch_process_content_frame,
            variable=self.batch_output_format_var,
            values=self.batch_output_formats,
            font=self.normal_font,
            command=self.update_batch_quality_settings_visibility,  # コマンド追加
        )
        self.optionmenu_batch_output_format.grid(row=13, column=1, columnspan=2, padx=5, pady=5, sticky="ew")

        # --- JPEG 品質設定 (最初は非表示) ---
        self.label_batch_jpeg_quality = ctk.CTkLabel(
            self.batch_process_content_frame, text="JPEG品質:", font=self.normal_font
        )
        self.batch_jpeg_quality_var = ctk.IntVar(value=85)
        self.slider_batch_jpeg_quality = ctk.CTkSlider(
            self.batch_process_content_frame,
            from_=1,
            to=100,
            number_of_steps=99,
            variable=self.batch_jpeg_quality_var,
            command=lambda x: self.label_batch_jpeg_quality_value.configure(text=f"{int(x)}"),
            progress_color="#5B5FCF",
            button_color="#5B5FCF",
            button_hover_color="#4B4FBF",
        )
        self.label_batch_jpeg_quality_value = ctk.CTkLabel(
            self.batch_process_content_frame,
            text=f"{self.batch_jpeg_quality_var.get()}",
            font=self.normal_font,
            width=30,
        )

        # --- WEBP 品質設定 (最初は非表示) ---
        self.label_batch_webp_quality = ctk.CTkLabel(
            self.batch_process_content_frame, text="WEBP品質:", font=self.normal_font
        )
        self.batch_webp_quality_var = ctk.IntVar(value=85)
        self.slider_batch_webp_quality = ctk.CTkSlider(
            self.batch_process_content_frame,
            from_=1,
            to=100,
            number_of_steps=99,
            variable=self.batch_webp_quality_var,
            command=lambda x: self.label_batch_webp_quality_value.configure(text=f"{int(x)}"),
            progress_color="#5B5FCF",
            button_color="#5B5FCF",
            button_hover_color="#4B4FBF",
        )
        self.label_batch_webp_quality_value = ctk.CTkLabel(
            self.batch_process_content_frame,
            text=f"{self.batch_webp_quality_var.get()}",
            font=self.normal_font,
            width=30,
        )
        self.batch_webp_lossless_var = ctk.BooleanVar(value=False)
        self.checkbox_batch_webp_lossless = ctk.CTkCheckBox(
            self.batch_process_content_frame,
            text="ロスレス圧縮",
            variable=self.batch_webp_lossless_var,
            font=self.normal_font,
            command=self.update_batch_webp_lossless_state,
            fg_color="#5B5FCF",
            border_color="#E9ECEF",
            hover_color="#4B4FBF",
        )

        self.update_batch_compression_settings_state()  # 初期状態設定 (これにより品質設定も更新される)

        # --- 区切り線 ---
        self.batch_separator3 = ctk.CTkFrame(
            self.batch_process_content_frame, fg_color="#E9ECEF", height=2, corner_radius=1
        )
        self.batch_separator3.grid(row=17, column=0, columnspan=3, sticky="ew", pady=10)

        # --- その他設定 ---
        self.label_batch_other_settings = ctk.CTkLabel(
            self.batch_process_content_frame, text="その他設定", font=self.heading_font
        )
        self.label_batch_other_settings.grid(row=18, column=0, columnspan=3, pady=(0, 5), sticky="w")  # rowは適宜調整

        # EXIF情報
        self.label_batch_exif = ctk.CTkLabel(self.batch_process_content_frame, text="EXIF情報:", font=self.normal_font)
        self.label_batch_exif.grid(row=19, column=0, padx=(0, 5), pady=5, sticky="w")  # rowは適宜調整
        self.batch_exif_handling_var = ctk.StringVar(value="保持する")
        self.batch_exif_options = ["保持する", "削除する", "保持（回転情報のみ削除）"]
        self.optionmenu_batch_exif_handling = ctk.CTkOptionMenu(
            self.batch_process_content_frame,
            variable=self.batch_exif_handling_var,
            values=self.batch_exif_options,
            font=self.normal_font,
        )
        self.optionmenu_batch_exif_handling.grid(
            row=19, column=1, columnspan=2, padx=5, pady=5, sticky="ew"
        )  # rowは適宜調整

        # ファイル命名規則
        self.label_batch_prefix = ctk.CTkLabel(
            self.batch_process_content_frame,
            text="ﾌｧｲﾙ名ﾌﾟﾚﾌｨｯｸｽ:",
            font=self.normal_font,
        )
        self.label_batch_prefix.grid(row=20, column=0, padx=(0, 5), pady=5, sticky="w")  # rowは適宜調整
        self.batch_prefix_var = ctk.StringVar(value="")
        self.entry_batch_prefix = ctk.CTkEntry(
            self.batch_process_content_frame,
            textvariable=self.batch_prefix_var,
            font=self.normal_font,
            corner_radius=6,
            border_width=1,
            border_color="#E9ECEF",
            placeholder_text="プレフィックスを入力（オプション）",
        )
        self.entry_batch_prefix.grid(row=20, column=1, columnspan=2, padx=5, pady=5, sticky="ew")  # rowは適宜調整

        self.label_batch_suffix = ctk.CTkLabel(
            self.batch_process_content_frame,
            text="ﾌｧｲﾙ名ｻﾌｨｯｸｽ:",
            font=self.normal_font,
        )
        self.label_batch_suffix.grid(row=21, column=0, padx=(0, 5), pady=5, sticky="w")  # rowは適宜調整
        self.batch_suffix_var = ctk.StringVar(value="_processed")
        self.entry_batch_suffix = ctk.CTkEntry(
            self.batch_process_content_frame,
            textvariable=self.batch_suffix_var,
            font=self.normal_font,
            corner_radius=6,
            border_width=1,
            border_color="#E9ECEF",
        )
        self.entry_batch_suffix.grid(row=21, column=1, columnspan=2, padx=5, pady=5, sticky="ew")  # rowは適宜調整

        # サブフォルダの処理
        self.batch_process_subfolders_var = ctk.BooleanVar(value=True)
        self.checkbox_batch_process_subfolders = ctk.CTkCheckBox(
            self.batch_process_content_frame,
            text="サブフォルダも処理する",
            variable=self.batch_process_subfolders_var,
            font=self.normal_font,
            fg_color="#5B5FCF",
            border_color="#E9ECEF",
            hover_color="#4B4FBF",
        )
        self.checkbox_batch_process_subfolders.grid(
            row=22, column=0, columnspan=3, padx=5, pady=10, sticky="w"
        )  # rowは適宜調整

        # 一括処理ボタンのフレーム
        batch_action_frame = ctk.CTkFrame(self.batch_process_content_frame, fg_color="transparent")
        batch_action_frame.grid(row=23, column=0, columnspan=3, padx=10, pady=(20, 10), sticky="ew")
        batch_action_frame.grid_columnconfigure(0, weight=1)
        batch_action_frame.grid_columnconfigure(1, weight=0)
        batch_action_frame.grid_columnconfigure(2, weight=0)
        batch_action_frame.grid_columnconfigure(3, weight=1)

        # 一括処理開始ボタン
        self.batch_start_button = ctk.CTkButton(
            batch_action_frame,
            text="🚀 一括処理開始",
            command=self.start_batch_process,
            width=160,
            height=42,
            font=self.button_font,
            fg_color="#6C63FF",
            hover_color="#5A52D5",
            text_color="#FFFFFF",
            corner_radius=8,
        )
        self.batch_start_button.grid(row=0, column=1, padx=5, pady=5)

        # 一括処理中断ボタン
        self.batch_cancel_button = ctk.CTkButton(
            batch_action_frame,
            text="⏹ 中断",
            command=self.cancel_batch_process,
            state="disabled",
            width=120,
            height=36,
            font=self.button_font,
            fg_color="#DC3545",
            hover_color="#C82333",
            text_color="#FFFFFF",
            text_color_disabled="#FFFFFF",
            corner_radius=8,
        )
        self.batch_cancel_button.grid(row=0, column=2, padx=5, pady=5)
        '''


    def add_log_message(self, message, is_warning=False, is_error=False):
        # log_textboxがまだ初期化されていない場合は何もしない
        if not hasattr(self, "log_textbox") or self.log_textbox is None:
            print(f"ログメッセージ（表示不可）: {message}")
            return
        
        # メッセージが辞書形式の場合（スレッドセーフ呼び出し）
        if isinstance(message, dict):
            actual_message = message.get('message', '')
            is_warning = message.get('is_warning', False)
            is_error = message.get('is_error', False)
        else:
            actual_message = message

        try:
            self.log_textbox.configure(state="normal")
            if is_warning:
                self.log_textbox.insert("end", f"[警告] {actual_message}\n", "warning")
            elif is_error:
                self.log_textbox.insert("end", f"[エラー] {actual_message}\n", "error")
            else:
                self.log_textbox.insert("end", f"{actual_message}\n")
            self.log_textbox.configure(state="disabled")
            self.log_textbox.see("end")
        except Exception as e:
            print(f"ログ表示エラー: {e} - メッセージ: {actual_message}")

    def update_progress(self, value, pulse=False):
        """
        進捗バーを更新する

        Args:
            value: 0.0-1.0の間の進捗値
            pulse: Trueの場合、パルスモードを使用（処理中アニメーション）
        """
        if pulse:
            # パルスモードの場合、少し値を変動させて動きを演出
            current = self.progress_bar.get()
            # 0.45-0.55の間で値を変動させる
            if current < 0.45 or current > 0.55:
                self.progress_bar.set(0.5)
            else:
                # 少しずつ値を変更して動きを作る
                delta = 0.01
                new_value = current + delta if current < 0.55 else current - delta
                self.progress_bar.set(new_value)
        else:
            # 通常モード
            self.progress_bar.set(value)

    def validate_start_button(self):
        """入力と出力が両方指定されているか確認し、開始ボタンの状態を更新"""
        if not hasattr(self, 'start_button') or not self.start_button:
            return
            
        # 処理モードを取得
        mode = self.processing_mode_var.get()
        
        # 入力と出力の値を取得
        input_value = self.input_entry.get().strip() if hasattr(self, 'input_entry') else ""
        output_value = self.output_dir_entry.get().strip() if hasattr(self, 'output_dir_entry') else ""
        
        # バッチモードの場合は、バッチ用のエントリをチェック
        if mode == "batch" and hasattr(self, 'entry_batch_input_folder') and hasattr(self, 'entry_batch_output_folder'):
            batch_input = self.entry_batch_input_folder.get().strip()
            batch_output = self.entry_batch_output_folder.get().strip()
            # バッチモードでは専用の入力欄をチェック
            if batch_input and batch_output:
                self.start_button.configure(state="normal")
            else:
                self.start_button.configure(state="disabled")
        else:
            # 単一ファイルモードでは通常のエントリをチェック
            if input_value and output_value:
                self.start_button.configure(state="normal")
            else:
                self.start_button.configure(state="disabled")
    
    def center_window(self):
        """Windows環境でも正しく動作するよう修正した中央配置メソッド"""
        self.update_idletasks()

        # サイズが小さすぎる場合は最小値を適用
        width = max(self.winfo_width(), 1000)
        height = max(self.winfo_height(), 900)

        x = (self.winfo_screenwidth() // 2) - (width // 2)
        y = (self.winfo_screenheight() // 2) - (height // 2)

        # 位置とサイズを設定
        self.geometry(f"{width}x{height}+{x}+{y}")

        # 再度サイズを確定させる
        self.update_idletasks()

    def start_process(self):
        """処理モードに応じて単一ファイル処理またはバッチ処理を開始"""
        mode = self.processing_mode_var.get()
        
        if mode == "single":
            self.add_log_message("単一ファイル処理を開始します...")
        else:
            self.add_log_message("フォルダ一括処理を開始します...")
            
        if self.start_button:
            self.start_button.configure(state="disabled")
        if self.cancel_button:
            self.cancel_button.configure(state="normal")
        self.update_progress(0.1)
        
        # 設定を保存
        if self.settings_manager:
            self.save_settings()
        
        # モードに応じて処理を分岐
        if mode == "single":
            self.process_single_file()
        else:
            self.process_batch_folder()
    
    def process_single_file(self):
        """単一ファイル処理の実行"""

        input_file_str = self.input_entry.get()
        output_dir_str = self.output_dir_entry.get()
        resize_mode_gui = self.resize_mode_var.get()
        resize_value_str = self.resize_value_entry.get()
        keep_aspect_ratio = self.resize_aspect_ratio_var.get()
        output_format_gui = self.resize_output_format_var.get()
        quality = self.resize_quality_var.get()
        exif_handling_gui = self.exif_handling_var.get()  # Get EXIF handling option
        
        # 圧縮設定を取得
        enable_compression = self.resize_enable_compression_var.get()
        target_size_str = self.resize_target_size_entry.get().strip()
        balance = self.resize_balance_var.get()
        
        # ファイル名設定を取得
        prefix = self.resize_prefix_entry.get().strip()
        suffix = self.resize_suffix_entry.get().strip()

        if not input_file_str:
            self.add_log_message("エラー: 入力ファイルが選択されていません。ファイルを選択してください。", is_error=True)
            self.finish_process(success=False)
            return
        
        # パスの安全性を検証
        try:
            source_file_path = PathValidator.validate_safe_path(input_file_str)
            if not PathValidator.is_image_file(source_file_path):
                self.add_log_message(f"エラー: 選択されたファイルは対応している画像形式ではありません: {source_file_path.suffix}", is_error=True)
                self.finish_process(success=False)
                return
        except ValueError as e:
            error_msg = ErrorHandler.get_user_friendly_message(e, filepath=input_file_str)
            self.add_log_message(error_msg, is_error=True)
            self.finish_process(success=False)
            return

        core_output_format = {
            "JPEG": "jpeg",
            "PNG": "png",
            "WebP": "webp",
            "入力と同じ": "same",
            "元のフォーマットを維持": "same",
        }.get(output_format_gui, "same")
        
        # デバッグログ
        self.add_log_message(f"選択された出力フォーマット: {output_format_gui} → {core_output_format}")

        exif_map = {"EXIFを保持": "keep", "EXIFを削除": "remove"}
        core_exif_handling = exif_map.get(exif_handling_gui, "keep")

        if not input_file_str or not output_dir_str:
            self.add_log_message(
                "エラー: 入力ファイルまたは出力ディレクトリが指定されていません。",
                is_error=True,
            )
            self.finish_process(success=False, message="入力または出力先が未指定")
            return

        output_directory = Path(output_dir_str)
        if not output_directory.is_dir():
            try:
                output_directory.mkdir(parents=True, exist_ok=True)
                self.add_log_message(f"出力ディレクトリを作成しました: {output_directory}")
            except OSError as e_os:
                self.add_log_message(
                    f"エラー: 出力ディレクトリの作成に失敗しました: {output_directory} ({e_os})",
                    is_error=True,
                )
                self.finish_process(success=False, message="出力ディレクトリ作成失敗")
                return

        file_stem = source_file_path.stem
        original_suffix = source_file_path.suffix

        if core_output_format == "jpeg":
            new_suffix = ".jpg"
        elif core_output_format == "png":
            new_suffix = ".png"
        elif core_output_format == "webp":
            new_suffix = ".webp"
        elif core_output_format == "same":
            new_suffix = original_suffix
        else:
            new_suffix = original_suffix
            self.add_log_message(
                f"警告: 不明な出力フォーマット '{core_output_format}'。元の拡張子 '{original_suffix}' を使用します。",
                is_warning=True,
            )

        # ファイル名にプレフィックスとサフィックスを適用
        new_filename = f"{prefix}{file_stem}{suffix}{new_suffix}"
        dest_path = output_directory / new_filename
        
        # デバッグログ
        self.add_log_message(f"出力ファイル名: {new_filename} (拡張子: {new_suffix})")

        resize_mode_map = {
            "リサイズなし": "none",
            "パーセント": "percentage",
            "幅を指定": "width",
            "高さを指定": "height",
            "縦横最大": "longest_side",
        }
        core_resize_mode = resize_mode_map.get(resize_mode_gui, "width")

        try:
            # リサイズモードに応じた検証
            if core_resize_mode != "none" and resize_value_str:
                if core_resize_mode == "percentage":
                    resize_value_parsed = ValueValidator.validate_percentage(resize_value_str)
                else:
                    resize_value_parsed = ValueValidator.validate_resize_value(resize_value_str, core_resize_mode)
            else:
                resize_value_parsed = 0
        except ValueError as e:
            error_msg = ErrorHandler.get_user_friendly_message(e, value=resize_value_str)
            self.add_log_message(error_msg, is_error=True)
            self.finish_process(success=False, message="リサイズ値が不正")
            return

        try:
            quality_parsed = ValueValidator.validate_quality(quality) if quality else 85
        except ValueError as e:
            error_msg = ErrorHandler.get_user_friendly_message(e, value=quality)
            self.add_log_message(error_msg, is_error=True)
            self.finish_process(success=False, message="品質値が不正")
            return

        try:
            self.processing_thread = threading.Thread(
                target=self._execute_resize_in_thread,
                args=(
                    source_file_path,
                    dest_path,
                    core_resize_mode,
                    resize_value_parsed,
                    keep_aspect_ratio,
                    core_output_format,
                    quality_parsed,
                    core_exif_handling,
                    enable_compression,
                    target_size_str,
                    balance,
                ),
            )
            self.processing_thread.start()
        except Exception as e:
            self.add_log_message(f"画像処理の開始中に予期せぬエラーが発生しました: {e}", is_error=True)
            # エラーダイアログを表示
            if 'show_error_with_details' in globals():
                show_error_with_details(self, e, "画像処理")
            else:
                tb_str = traceback.format_exc()
                self.add_log_message(f"トレースバック:\n{tb_str}", is_error=True)
            self.finish_process(success=False, message=str(e))

    def request_cancel_processing(self):
        with self.thread_lock:
            self.cancel_requested = True
        self.add_log_message("中断リクエストを受け付けました。現在の処理ステップが完了次第、停止します。")
        # 中断ボタンは finish_process で無効化される

    def _execute_resize_in_thread(
        self,
        source_path,
        dest_path,
        core_resize_mode,
        resize_value,
        keep_aspect_ratio,
        core_output_format,
        quality,
        exif_handling,
        enable_compression,
        target_size_str,
        balance,
    ):
        try:
            self.add_log_message("画像処理スレッドを開始しました...")

            with self.thread_lock:
                if self.cancel_requested:
                    self.after(
                        0,
                        lambda: self.add_log_message("処理が中断されました (スレッド開始直後)。", is_warning=True),
                    )
                    self.after(
                        0,
                        lambda: self.finish_process(success=False, message="処理がユーザーによって中断されました。"),
                    )
                    return

            # 処理開始時刻を記録
            start_time = time.time()
            
            try:
                img = Image.open(source_path)
                original_width, original_height = img.size
                original_size = source_path.stat().st_size
            except FileNotFoundError:
                self.after(
                    0,
                    lambda: self.add_log_message(
                        f"エラー: 入力ファイルが見つかりません: {source_path}",
                        is_error=True,
                    ),
                )
                self.after(
                    0,
                    lambda: self.finish_process(success=False, message="入力ファイルが見つかりません。"),
                )
                return
            except Exception as e:
                self.after(
                    0,
                    lambda e=e: self.add_log_message(
                        f"エラー: 画像ファイルを開けません: {source_path} ({e})",
                        is_error=True,
                    ),
                )
                self.after(
                    0,
                    lambda e=e: self.finish_process(success=False, message="画像ファイルを開けません。"),
                )
                return

            with self.thread_lock:
                if self.cancel_requested:
                    self.after(
                        0,
                        lambda: self.add_log_message("処理が中断されました (画像読み込み後)。", is_warning=True),
                    )
                    self.after(
                        0,
                        lambda: self.finish_process(success=False, message="処理がユーザーによって中断されました。"),
                    )
                    return

            calculated_target_width = 0
            if core_resize_mode == "none":
                # リサイズなしの場合は元のサイズを維持
                calculated_target_width = original_width
                self.after(
                    0,
                    lambda: self.add_log_message("リサイズなしモード - 圧縮のみ実行します。"),
                )
            elif core_resize_mode == "width":
                calculated_target_width = resize_value
            elif core_resize_mode == "percentage":
                calculated_target_width = int(original_width * (resize_value / 100))
            elif core_resize_mode == "height":
                if keep_aspect_ratio:
                    calculated_target_width = int(original_width * (resize_value / original_height))
                else:
                    # アスペクト比を維持しない場合、resize_coreは幅と高さの両方を必要とするが、
                    # GUIからは一方しか指定できるため、ここでは元の幅を維持し高さを変更する挙動を想定する。
                    # ただし、resize_and_compress_image は target_width のみを取るため、
                    # このケースは resize_core 側で適切に扱われるか、GUIの仕様を見直す必要がある。
                    # 現状では、アスペクト比非維持の高さ指定は期待通りに動作しない可能性がある。
                    calculated_target_width = original_width  # 元の幅を維持
                    # target_height = resize_value # この値は resize_and_compress_image に直接渡せない
                    self.after(
                        0,
                        lambda: self.add_log_message(
                            "警告: 高さ指定でアスペクト比を維持しない場合、resize_coreの現在の仕様では期待通りに動作しない可能性があります。"
                            "コア関数は目標幅のみを受け取ります。",
                            is_warning=True,
                        ),
                    )
            elif core_resize_mode == "longest_side":
                # 縦横最大モードの場合
                if original_width > original_height:
                    calculated_target_width = resize_value
                else:
                    calculated_target_width = int(original_width * (resize_value / original_height))

            if calculated_target_width <= 0 and core_resize_mode != "none":
                self.after(
                    0,
                    lambda: self.add_log_message(
                        f"エラー: 計算された目標幅が無効です ({calculated_target_width}px)。入力値を確認してください。",
                        is_error=True,
                    ),
                )
                self.after(
                    0,
                    lambda: self.finish_process(success=False, message="目標幅の計算結果が無効です。"),
                )
                return

            self.after(0, lambda: self.update_progress(0.5))

            with self.thread_lock:
                should_cancel = self.cancel_requested
            if should_cancel:  # Check before core processing
                self.after(
                    0,
                    lambda: self.add_log_message("処理が中断されました (コア処理開始前)。", is_warning=True),
                )
                self.after(
                    0,
                    lambda: self.finish_process(success=False, message="処理がユーザーによって中断されました。"),
                )
                return

            # 目標ファイルサイズの処理
            target_size_kb = None
            if enable_compression and target_size_str:
                try:
                    target_size_kb = int(target_size_str)
                    self.after(
                        0,
                        lambda: self.add_log_message(f"目標ファイルサイズ: {target_size_kb} KB"),
                    )
                except ValueError:
                    self.after(
                        0,
                        lambda: self.add_log_message(
                            f"警告: 目標ファイルサイズ '{target_size_str}' は無効な値です。無視します。",
                            is_warning=True,
                        ),
                    )

            # resize_and_compress_image を呼び出す
            # 圧縮が無効の場合は品質100で処理
            effective_quality = quality if enable_compression else 100
            
            # デバッグ用ログ
            self.add_log_message(f"resize_and_compress_image パラメータ:")
            self.add_log_message(f"  - format: {core_output_format}")
            self.add_log_message(f"  - quality: {effective_quality}")
            self.add_log_message(f"  - dest_path: {dest_path}")
            
            success, skipped, new_size_kb = resize_and_compress_image(
                source_path=source_path,
                dest_path=dest_path,
                target_width=calculated_target_width,
                quality=effective_quality,
                format=core_output_format,
                exif_handling=exif_handling,
                balance=balance if enable_compression else 10,  # 圧縮無効時は品質優先
                webp_lossless=False,
                dry_run=False,  # dry_run はGUIの主要機能ではないためFalse固定
                # 新しいパラメータを追加
                resize_mode=core_resize_mode,
                resize_value=resize_value,
                lanczos_filter=True,  # 高品質フィルタを使用
                progressive=False,  # プログレッシブJPEGは無効
                optimize=True,  # 最適化を有効化
            )

            with self.thread_lock:
                should_cancel = self.cancel_requested
            if should_cancel:
                self.after(
                    0,
                    lambda: self.add_log_message("処理が中断されました (コア処理後)。", is_warning=True),
                )
                self.after(
                    0,
                    lambda: self.finish_process(success=False, message="処理がユーザーによって中断されました。"),
                )
                return

            self.after(0, lambda: self.update_progress(0.9))

            if success:
                # 処理時間を計算
                processing_time = time.time() - start_time
                
                # 新しい画像の情報を取得
                if dest_path.exists():
                    dest_size = dest_path.stat().st_size
                    try:
                        dest_img = Image.open(dest_path)
                        dest_width, dest_height = dest_img.size
                        dest_img.close()
                    except Exception:
                        dest_width, dest_height = 0, 0
                else:
                    dest_size = 0
                    dest_width, dest_height = 0, 0
                
                # 履歴に記録（Phase 3）
                if self.history_manager and not skipped:
                    try:
                        self.history_manager.add_entry(
                            source_path=source_path,
                            dest_path=dest_path,
                            source_size=original_size,
                            dest_size=dest_size,
                            source_dimensions=(original_width, original_height),
                            dest_dimensions=(dest_width, dest_height),
                            settings={
                                'resize_mode': core_resize_mode,
                                'resize_value': resize_value,
                                'keep_aspect_ratio': keep_aspect_ratio,
                                'output_format': core_output_format,
                                'quality': quality,
                                'exif_handling': exif_handling,
                                'enable_compression': enable_compression,
                                'target_size_kb': int(target_size_str) if target_size_str else None,
                                'balance': balance
                            },
                            success=True,
                            processing_time=processing_time
                        )
                    except Exception as e:
                        print(f"履歴記録エラー: {e}")
                
                if skipped:
                    self.after(
                        0,
                        lambda: self.add_log_message(
                            f"画像は既に最適化されているか、設定より小さいためスキップされました: {dest_path.name}",
                            is_warning=True,
                        ),
                    )
                else:
                    size_info = f" (サイズ: {new_size_kb} KB)" if new_size_kb is not None else ""
                    self.after(
                        0,
                        lambda: self.add_log_message(f"画像処理成功: {dest_path.name}{size_info}"),
                    )
                self.after(
                    0,
                    lambda: self.finish_process(success=True, message="画像処理が正常に完了しました。"),
                )
            else:
                self.after(
                    0,
                    lambda: self.add_log_message(f"画像処理失敗: {dest_path.name}", is_error=True),
                )
                self.after(
                    0,
                    lambda: self.finish_process(success=False, message="画像処理中にエラーが発生しました。"),
                )

        except Exception as e:
            # get_japanese_error_messageを使用して日本語エラーメッセージを取得
            japanese_error_msg = get_japanese_error_message(e)
            detailed_error_message = f"画像処理スレッドでエラーが発生しました: {japanese_error_msg}"
            tb_str = traceback.format_exc()
            self.after(
                0,
                lambda: self.add_log_message(detailed_error_message, is_error=True),
            )
            self.after(
                0,
                lambda: self.add_log_message(f"詳細情報:\n{tb_str}", is_error=True),
            )
            self.after(
                0,
                lambda: self.finish_process(success=False, message=japanese_error_msg),
            )

    def cancel_resize_process(self):
        self.add_log_message("リサイズ処理を中断しています...")
        with self.thread_lock:
            self.cancel_requested = True

        # スレッドは自然に終了するのを待つ
        # 本格的な実装では、もっと洗練された中断機構が必要

    def finish_process(self, success=True, message="処理完了"):
        if success:
            self.add_log_message(f"完了: {message}")
            self.update_progress(1)
        else:
            self.add_log_message(f"エラー/中断: {message}")
            self.update_progress(0)

        if self.start_button:
            self.start_button.configure(state="normal")
        if self.cancel_button:
            self.cancel_button.configure(state="disabled")
        with self.thread_lock:
            self.cancel_requested = False  # 念のため再度リセット
    
    def process_batch_folder(self):
        """フォルダ一括処理の実行"""
        input_folder_str = self.input_entry.get()
        output_dir_str = self.output_dir_entry.get()
        include_subdirs = self.include_subdirs_var.get()
        
        if not input_folder_str or not output_dir_str:
            self.add_log_message("エラー: 入力フォルダまたは出力フォルダが指定されていません。", is_error=True)
            self.finish_process(success=False)
            return
            
        # パラメータを収集
        params = {
            'input_folder': input_folder_str,
            'output_folder': output_dir_str,
            'include_subdirs': include_subdirs,
            'resize_mode': self.resize_mode_var.get(),
            'resize_value': self.resize_value_entry.get(),
            'keep_aspect_ratio': self.resize_aspect_ratio_var.get(),
            'output_format': self.resize_output_format_var.get(),
            'quality': self.resize_quality_var.get(),
            'exif_handling': self.exif_handling_var.get(),
            'enable_compression': self.resize_enable_compression_var.get(),
            'target_size': self.resize_target_size_entry.get().strip(),
            'balance': self.resize_balance_var.get(),
            'prefix': self.resize_prefix_entry.get().strip(),
            'suffix': self.resize_suffix_entry.get().strip()
        }
        
        # ワーカースレッドで処理を実行
        self.processing_thread = threading.Thread(target=self.batch_worker, args=(params,), daemon=True)
        self.processing_thread.start()


    def batch_worker(self, params):
        """バッチ処理のワーカースレッド"""
        try:
            # パラメータを展開
            input_folder = params["input_folder"]
            output_folder = params["output_folder"]
            include_subdirs = params["include_subdirs"]
            resize_mode = params["resize_mode"]
            resize_value = params["resize_value"]
            keep_aspect_ratio = params["keep_aspect_ratio"]
            enable_compression = params["enable_compression"]
            output_format = params["output_format"]
            quality = params["quality"]
            exif_handling = params["exif_handling"]
            target_size = params["target_size"]
            balance = params["balance"]
            prefix = params["prefix"]
            suffix = params["suffix"]
            
            # 画像ファイルを検索
            self.after(0, lambda: self.add_log_message("画像ファイルを検索中..."))
            image_files = find_image_files(input_folder)
            
            if not image_files:
                self.after(0, lambda: self.add_log_message("処理対象の画像ファイルが見つかりませんでした。", is_warning=True))
                self.after(0, lambda: self.finish_process(success=False))
                return
                
            total_files = len(image_files)
            self.after(0, lambda: self.add_log_message(f"処理対象: {total_files} ファイル"))
            
            # 進捗トラッカーを開始
            if self.progress_tracker:
                self.progress_tracker.start_batch(total_files)
                # 進捗更新コールバックを登録
                self.progress_tracker.register_callback('on_update', 
                    lambda bp, item: self.after(0, lambda: self._update_progress_display(bp, item)))
            
            # 処理カウンタの初期化
            processed_count = 0
            skipped_count = 0
            error_count = 0
            total_size_before = 0
            total_size_after = 0
            
            # 各画像ファイルを処理
            for idx, source_path in enumerate(image_files):
                # 中断リクエストのチェック
                with self.thread_lock:
                    if self.cancel_requested:
                        self.after(0, lambda: self.add_log_message("ユーザーによる中断リクエストにより処理を停止します", is_warning=True))
                        break
                    
                # 進捗の更新
                progress = (idx) / total_files
                self.after(0, lambda p=progress: self.progress_bar.set(p))
                
                # 進捗トラッカーでアイテムを開始
                if self.progress_tracker:
                    progress_item = self.progress_tracker.start_item(source_path.name)
                
                # ファイル情報をログに表示
                self.after(0, lambda p=source_path, i=idx+1, t=total_files: 
                    self.add_log_message(f"[{i}/{t}] 処理中: {p.name}"))
                
                try:
                    # 処理開始時刻を記録
                    item_start_time = time.time()
                    
                    # 元のファイルサイズを取得
                    file_size_before = source_path.stat().st_size
                    total_size_before += file_size_before
                    
                    # 出力パスを生成
                    dest_path = get_destination_path(source_path, input_folder, output_folder)
                    
                    # 出力フォーマットが指定されている場合は拡張子を変更
                    if output_format:
                        dest_path = dest_path.with_suffix(f".{output_format.lower()}")
                    
                    # 出力ディレクトリが存在しない場合は作成
                    dest_path.parent.mkdir(parents=True, exist_ok=True)
                    
                    # リサイズ値の設定（リサイズモードに応じて）
                    if resize_mode == "width":
                        target_width = int(resize_value)
                    elif resize_mode == "height":
                        # 高さ指定の場合は、アスペクト比から幅を計算
                        img = Image.open(source_path)
                        aspect_ratio = img.width / img.height
                        target_width = int(int(resize_value) * aspect_ratio)
                    elif resize_mode == "longest_side":
                        # 長辺指定の場合
                        img = Image.open(source_path)
                        if img.width > img.height:
                            target_width = int(resize_value)
                        else:
                            aspect_ratio = img.width / img.height
                            target_width = int(int(resize_value) * aspect_ratio)
                    elif resize_mode == "percentage":
                        # パーセンテージ指定の場合
                        img = Image.open(source_path)
                        target_width = int(img.width * float(resize_value) / 100)
                    else:
                        # リサイズなしの場合は元の幅を使用
                        img = Image.open(source_path)
                        target_width = img.width
                    
                    # 品質設定の決定
                    # qualityパラメータは既に渡されているのでそのまま使用
                    
                    # 画像をリサイズ・圧縮
                    success, skipped, new_size_kb = resize_and_compress_image(
                        source_path=source_path,
                        dest_path=dest_path,
                        target_width=target_width,
                        quality=quality,
                        format=output_format.lower() if output_format else "original",
                        exif_handling="keep",
                        balance=5,
                        webp_lossless=False,  # TODO: UIから設定可能にする
                        dry_run=False,
                        # 新しいパラメータ
                        resize_mode=resize_mode,
                        resize_value=resize_value,
                        lanczos_filter=True,
                        progressive=False,
                        optimize=False
                    )
                    
                    
                    if success and not skipped:  # 成功した場合
                        processed_count += 1
                        
                        # 新しいファイルサイズを取得
                        if dest_path.exists():
                            file_size_after = dest_path.stat().st_size
                            total_size_after += file_size_after
                            size_reduction = ((file_size_before - file_size_after) / file_size_before * 100) if file_size_before > 0 else 0
                            
                            # 画像サイズの情報を取得
                            img_before = Image.open(source_path)
                            img_after = Image.open(dest_path)
                            
                            # 処理時間を計算
                            processing_time = time.time() - item_start_time
                            
                            # 履歴に記録（Phase 3）
                            if self.history_manager:
                                try:
                                    self.history_manager.add_entry(
                                        source_path=source_path,
                                        dest_path=dest_path,
                                        source_size=file_size_before,
                                        dest_size=file_size_after,
                                        source_dimensions=(img_before.width, img_before.height),
                                        dest_dimensions=(img_after.width, img_after.height),
                                        settings={
                                            'resize_mode': resize_mode,
                                            'resize_value': resize_value,
                                            'keep_aspect_ratio': keep_aspect_ratio,
                                            'output_format': output_format,
                                            'quality': quality,
                                            'exif_handling': exif_handling,
                                            'enable_compression': enable_compression,
                                            'target_size_kb': int(target_size) if target_size else None,
                                            'balance': balance
                                        },
                                        success=True,
                                        processing_time=processing_time
                                    )
                                except Exception as e:
                                    print(f"履歴記録エラー: {e}")
                            
                            self.after(0, lambda ob=img_before.size, na=img_after.size, s=size_reduction: 
                                self.add_log_message(f"  ✓ サイズ: {ob[0]}x{ob[1]} → {na[0]}x{na[1]} (ファイルサイズ {s:.1f}% 削減)"))
                    else:
                        skipped_count += 1
                        self.after(0, lambda: self.add_log_message("  - スキップ: 処理できませんでした", is_warning=True))
                        
                except Exception as e:
                    error_count += 1
                    japanese_error_msg = get_japanese_error_message(e)
                    self.after(0, lambda msg=japanese_error_msg: self.add_log_message(f"  ✗ エラー: {msg}", is_error=True))
                    
            # 最終進捗を100%に
            self.after(0, lambda: self.progress_bar.set(1.0))
            
            # 処理結果のサマリー
            self.after(0, lambda: self.add_log_message("=" * 50))
            self.after(0, lambda: self.add_log_message("処理完了"))
            self.after(0, lambda: self.add_log_message(f"成功: {processed_count} ファイル"))
            if skipped_count > 0:
                self.after(0, lambda: self.add_log_message(f"スキップ: {skipped_count} ファイル", is_warning=True))
            if error_count > 0:
                self.after(0, lambda: self.add_log_message(f"エラー: {error_count} ファイル", is_error=True))
                
            # ファイルサイズの削減量を表示
            if total_size_before > 0 and total_size_after > 0:
                total_reduction = ((total_size_before - total_size_after) / total_size_before * 100)
                self.after(0, lambda: self.add_log_message(
                    f"総ファイルサイズ: {format_file_size(total_size_before)} → {format_file_size(total_size_after)} ({total_reduction:.1f}% 削減)"
                ))
                
            # 処理完了
            success = error_count == 0 and processed_count > 0
            self.after(0, lambda: self.finish_batch_process(success=success))
            
        except Exception as e:
            japanese_error_msg = get_japanese_error_message(e)
            self.after(0, lambda msg=japanese_error_msg: self.add_log_message(f"バッチ処理中にエラーが発生しました: {msg}", is_error=True))
            self.after(0, lambda: self.finish_batch_process(success=False))
            
    def finish_batch_process(self, success=True):
        """バッチ処理の終了処理"""
        # UIの状態を元に戻す
        self.start_button.configure(state="normal")
        self.cancel_button.configure(state="disabled")
        with self.thread_lock:
            self.cancel_requested = False
        
        if success:
            self.add_log_message("✅ 一括処理が正常に完了しました")
        else:
            self.add_log_message("❌ 一括処理が中断またはエラーで終了しました", is_error=True)

    def cancel_batch_process(self):
        """一括処理を中断"""
        with self.thread_lock:
            self.cancel_requested = True
        self.add_log_message("一括処理の中断をリクエストしました...")
        self.cancel_button.configure(state="disabled")
    
    def _update_progress_display(self, batch_progress, current_item=None):
        """進捗表示を更新"""
        if self.progress_tracker:
            status_text = self.progress_tracker.get_status_text()
            # ステータステキストをログに表示（既存メッセージを上書き）
            # TODO: より洗練された進捗表示の実装
            
    def on_window_close(self):
        """ウィンドウが閉じられる時の処理"""
        # 設定を保存
        if self.settings_manager:
            self.save_settings()
        # ウィンドウを破棄
        self.destroy()
    
    def _create_menu_bar(self):
        """メニューバーを作成"""
        if not PHASE3_AVAILABLE:
            return
            
        self.menubar = tk.Menu(self)
        self.configure(menu=self.menubar)
        
        # ファイルメニュー
        file_menu = tk.Menu(self.menubar, tearoff=0)
        self.menubar.add_cascade(label="ファイル", menu=file_menu)
        file_menu.add_command(label="開く...", command=self.browse_input, accelerator="Ctrl+O")
        file_menu.add_separator()
        file_menu.add_command(label="設定を保存", command=self.save_settings)
        file_menu.add_command(label="設定を読み込む", command=self.load_settings)
        file_menu.add_separator()
        file_menu.add_command(label="終了", command=self.on_window_close, accelerator="Ctrl+Q")
        
        # 編集メニュー
        edit_menu = tk.Menu(self.menubar, tearoff=0)
        self.menubar.add_cascade(label="編集", menu=edit_menu)
        edit_menu.add_command(label="プリセット管理...", command=self.open_preset_manager)
        
        # 表示メニュー
        view_menu = tk.Menu(self.menubar, tearoff=0)
        self.menubar.add_cascade(label="表示", menu=view_menu)
        
        # テーマメニュー
        theme_menu = tk.Menu(view_menu, tearoff=0)
        view_menu.add_cascade(label="テーマ", menu=theme_menu)
        
        self.theme_var = tk.StringVar(value=self.settings_manager.get_ui_settings().theme if self.settings_manager else "light")
        theme_menu.add_radiobutton(label="ライトモード", variable=self.theme_var, value="light", command=lambda: self.change_theme("light"))
        theme_menu.add_radiobutton(label="ダークモード", variable=self.theme_var, value="dark", command=lambda: self.change_theme("dark"))
        theme_menu.add_radiobutton(label="システム設定に従う", variable=self.theme_var, value="system", command=lambda: self.change_theme("system"))
        
        view_menu.add_separator()
        view_menu.add_command(label="統計...", command=self.open_statistics)
        
        # ヘルプメニュー
        help_menu = tk.Menu(self.menubar, tearoff=0)
        self.menubar.add_cascade(label="ヘルプ", menu=help_menu)
        help_menu.add_command(label="使い方", command=self.show_help, accelerator="F1")
        help_menu.add_command(label="ショートカットキー", command=self.show_shortcuts)
        help_menu.add_separator()
        help_menu.add_command(label="バージョン情報", command=self.show_about)
    
    def open_preset_manager(self):
        """プリセットマネージャーを開く"""
        if not self.preset_manager:
            return
            
        dialog = PresetManagerDialog(self, self.preset_manager)
        dialog.on_preset_selected = self._apply_preset
        self.wait_window(dialog)
        
        # プリセットメニューを更新
        if hasattr(self, 'preset_menu'):
            self._update_preset_menu()
    
    def _setup_keyboard_shortcuts(self):
        """キーボードショートカットを設定"""
        # ファイル操作
        self.bind("<Control-o>", lambda e: self.browse_input())
        self.bind("<Control-q>", lambda e: self.on_window_close())
        self.bind("<Control-Q>", lambda e: self.on_window_close())
        
        # 処理開始（リサイズタブ選択時のみ）
        self.bind("<Control-s>", self._on_start_processing_shortcut)
        self.bind("<Control-S>", self._on_start_processing_shortcut)
        
        # キャンセル
        self.bind("<Escape>", self._on_cancel_processing_shortcut)
        
        # ヘルプ
        self.bind("<F1>", lambda e: self.show_help())
        
        # プリセット管理
        if PHASE3_AVAILABLE:
            self.bind("<F9>", lambda e: self.open_preset_manager())
            
            # タブ切り替え
            self.bind("<Control-Key-1>", lambda e: self.tab_view.set("画像リサイズ"))
            self.bind("<Control-Key-2>", lambda e: self.tab_view.set("プレビュー"))
            self.bind("<Control-Key-3>", lambda e: self.tab_view.set("履歴"))
            self.bind("<Control-Key-4>", lambda e: self.tab_view.set("統計"))
    
    def _on_start_processing_shortcut(self, event):
        """処理開始ショートカット"""
        if self.tab_view.get() == "画像リサイズ":
            # リサイズタブが選択されている場合のみ処理開始
            self.process_images_with_progress()
    
    def _on_cancel_processing_shortcut(self, event):
        """処理キャンセルショートカット"""
        if hasattr(self, 'cancel_requested'):
            self.cancel_requested = True
            self.add_log_message("処理をキャンセルしています...")
    
    def show_shortcuts(self):
        """ショートカットキーを表示"""
        shortcuts_text = """【キーボードショートカット一覧】

ファイル操作:
  Ctrl+O - ファイル/フォルダを開く
  Ctrl+Q - アプリケーション終了

処理:
  Ctrl+S - 処理開始（リサイズタブ選択時）
  Escape - 処理キャンセル

ヘルプ:
  F1 - ヘルプを表示
  F9 - プリセット管理

タブ切り替え:
  Ctrl+1 - 画像リサイズタブ
  Ctrl+2 - プレビュータブ
  Ctrl+3 - 履歴タブ
  Ctrl+4 - 統計タブ"""
        
        messagebox.showinfo("ショートカットキー", shortcuts_text)
    
    def change_theme(self, theme: str):
        """テーマを変更"""
        if theme == "system":
            # システム設定に従う
            import darkdetect
            try:
                if darkdetect.isDark():
                    actual_theme = "dark"
                else:
                    actual_theme = "light"
            except:
                # darkdetectが利用できない場合はライトモードをデフォルトに
                actual_theme = "light"
        else:
            actual_theme = theme
        
        # CustomTkinterのテーマを設定
        ctk.set_appearance_mode(actual_theme)
        
        # 設定を保存
        if self.settings_manager:
            self.settings_manager.update_ui_settings(theme=theme)
            self.settings_manager.save()
        
        self.add_log_message(f"テーマを{theme}に変更しました")
    
    def open_statistics(self):
        """統計ダイアログを開く"""
        if not self.history_manager:
            return
            
        dialog = StatisticsDialog(self, self.history_manager)
        self.wait_window(dialog)
    
    def show_help(self):
        """ヘルプを表示"""
        from tkinter import messagebox
        messagebox.showinfo(
            "使い方",
            "KarukuResize - 画像リサイズ・圧縮ツール\n\n"
            "1. 処理モードを選択（単一ファイル/フォルダ一括処理）\n"
            "2. 入力ファイル/フォルダを選択\n"
            "3. 出力先フォルダを選択\n"
            "4. リサイズ・圧縮設定を調整\n"
            "5. 処理開始ボタンをクリック\n\n"
            "詳細はプロジェクトのREADMEをご覧ください。"
        )
    
    def show_about(self):
        """バージョン情報を表示"""
        from tkinter import messagebox
        messagebox.showinfo(
            "バージョン情報",
            "KarukuResize v0.2.1\n\n"
            "日本語対応の画像リサイズ・圧縮ツール\n"
            "軽く（かるく）画像を処理します\n\n"
            "© 2024 KarukuResize Project"
        )
    
    def _on_preset_selected(self, preset_name: str):
        """プリセット選択時"""
        if preset_name == "カスタム":
            return
            
        if not self.preset_manager:
            return
            
        preset = self.preset_manager.get_preset(preset_name)
        if preset:
            self._apply_preset(preset)
    
    def _apply_preset(self, preset: PresetData):
        """プリセットを適用"""
        # リサイズモード
        mode_map = {
            "none": "リサイズなし",
            "width": "幅を指定",
            "height": "高さを指定",
            "longest_side": "縦横最大",
            "percentage": "パーセント"
        }
        if preset.resize_mode in mode_map and hasattr(self, 'resize_mode_var'):
            self.resize_mode_var.set(mode_map[preset.resize_mode])
            self.on_resize_mode_change(mode_map[preset.resize_mode])
        
        # リサイズ値
        if hasattr(self, 'resize_value_entry'):
            self.resize_value_entry.delete(0, "end")
            self.resize_value_entry.insert(0, str(preset.resize_value))
        
        # アスペクト比
        if hasattr(self, 'resize_aspect_ratio_var'):
            self.resize_aspect_ratio_var.set(preset.maintain_aspect_ratio)
        
        # 出力フォーマット
        format_map = {
            "original": "オリジナル",
            "jpeg": "JPEG",
            "png": "PNG",
            "webp": "WEBP"
        }
        if preset.output_format in format_map and hasattr(self, 'resize_output_format_var'):
            self.resize_output_format_var.set(format_map[preset.output_format])
            self.on_output_format_change(format_map[preset.output_format])
        
        # 品質
        if hasattr(self, 'resize_quality_var'):
            self.resize_quality_var.set(preset.quality)
            if hasattr(self, 'resize_quality_slider'):
                self.resize_quality_slider.set(preset.quality)
        
        # メタデータ保持
        if hasattr(self, 'exif_handling_var'):
            self.exif_handling_var.set("keep" if preset.preserve_metadata else "remove")
        
        # 圧縮設定
        if hasattr(self, 'resize_enable_compression_var'):
            self.resize_enable_compression_var.set(preset.enable_compression)
            self.update_resize_compression_settings_state()
        
        # 目標サイズ
        if preset.target_size_kb and hasattr(self, 'resize_target_size_entry'):
            self.resize_target_size_entry.delete(0, "end")
            self.resize_target_size_entry.insert(0, str(preset.target_size_kb))
        
        # バランス
        if hasattr(self, 'resize_balance_var'):
            self.resize_balance_var.set(preset.balance)
            if hasattr(self, 'resize_balance_slider'):
                self.resize_balance_slider.set(preset.balance)
        
        # ファイル名設定
        if hasattr(self, 'resize_prefix_entry'):
            self.resize_prefix_entry.delete(0, "end")
            self.resize_prefix_entry.insert(0, preset.prefix)
        
        if hasattr(self, 'resize_suffix_entry'):
            self.resize_suffix_entry.delete(0, "end")
            self.resize_suffix_entry.insert(0, preset.suffix)
        
        self.add_log_message(f"プリセット '{preset.name}' を適用しました")
    
    def _update_preset_menu(self):
        """プリセットメニューを更新"""
        if not PHASE3_AVAILABLE or not self.preset_manager or not hasattr(self, 'preset_menu'):
            return
            
        preset_names = ["カスタム"] + self.preset_manager.get_preset_names()
        self.preset_menu.configure(values=preset_names)
    
    def _on_tab_changed(self):
        """タブが変更されたときの処理"""
        current_tab = self.tab_view.get()
        
        # 遅延読み込みの実行
        self.lazy_tab_manager.load_tab_if_needed(current_tab)
        
        # タブ切り替え時の描画遅延を解消
        self.update_idletasks()
    
    def _init_preview_tab(self):
        """プレビュータブを初期化"""
        if not PHASE3_AVAILABLE:
            return
            
        # 比較プレビューウィジェットを作成
        self.comparison_preview = ComparisonPreviewWidget(self.tab_preview)
        self.comparison_preview.pack(fill="both", expand=True, padx=10, pady=10)
        
        # ファイル選択時に自動プレビュー更新するためのコールバック設定
        # 現在の入力ファイルでプレビューを更新
        if hasattr(self, 'input_entry') and self.input_entry.get():
            input_path = self.input_entry.get()
            if Path(input_path).exists() and Path(input_path).is_file():
                self.comparison_preview.load_before_image(input_path)
                
                # 元画像の情報を表示
                self._update_original_image_info(input_path)
                
                # 現在の設定でアフタープレビューを生成
                self._update_preview_after()
                
        # 設定変更時のプレビュー自動更新を設定
        self._setup_preview_auto_update()
    
    def _init_history_tab(self):
        """履歴タブを初期化"""
        if not PHASE3_AVAILABLE or not self.history_manager:
            return
            
        # 履歴ビューワーを作成
        self.history_viewer = HistoryViewer(
            self.tab_history,
            self.history_manager
        )
        self.history_viewer.pack(fill="both", expand=True, padx=10, pady=10)
        
        # 履歴からの再処理機能を有効化
        if hasattr(self.tab_history, 'master'):
            # 親ウィジェット（self）のメソッドとして再処理機能を提供
            self.tab_history.master.reprocess_from_history = self.reprocess_from_history
    
    def _init_statistics_tab(self):
        """統計タブを初期化"""
        if not PHASE3_AVAILABLE or not self.history_manager:
            return
            
        # 統計ビューワーを作成
        self.stats_viewer = StatisticsViewer(self.tab_stats)
        self.stats_viewer.pack(fill="both", expand=True, padx=10, pady=10)
        
        # 初期データ読み込み
        self._update_statistics()
    
    def _update_preview_after(self):
        """プレビューのアフター画像を更新"""
        if not hasattr(self, 'comparison_preview'):
            return
            
        # 入力画像がない場合は何もしない
        input_path = self.input_entry.get().strip()
        if not input_path or not Path(input_path).exists():
            return
            
        # ローディング表示
        if hasattr(self, 'comparison_preview'):
            # アフタープレビューにローディングメッセージを表示
            self.comparison_preview.after_preview.clear()
            
        # 別スレッドでプレビューを生成
        threading.Thread(target=self._generate_preview_async, args=(input_path,), daemon=True).start()
    
    def _generate_preview_async(self, input_path: str):
        """非同期でプレビューを生成"""
        _d("=== _generate_preview_async start === input_path=%s", input_path)
        try:
            from PIL import Image
            import io
            
            # 現在の設定を取得
            resize_mode_gui = self.resize_mode_var.get()
            resize_value_str = self.resize_value_entry.get().strip()
            keep_aspect_ratio = self.resize_aspect_ratio_var.get()
            output_format_gui = self.resize_output_format_var.get()
            quality = self.resize_quality_var.get()
            exif_handling_gui = self.exif_handling_var.get()
            enable_compression = self.resize_enable_compression_var.get()
            balance = self.resize_balance_var.get()
            
            # GUI値をcore形式に変換
            resize_mode_map = {
                "リサイズなし": "none",
                "パーセント": "percentage",
                "幅を指定": "width",
                "高さを指定": "height",
                "縦横最大": "longest_side",
            }
            core_resize_mode = resize_mode_map.get(resize_mode_gui, "width")
            
            # リサイズ値を取得
            resize_value = 800  # デフォルト値
            if resize_value_str:
                try:
                    resize_value = int(resize_value_str)
                except ValueError:
                    pass
            
            # 出力フォーマット変換
            format_map = {
                "JPEG": "jpeg",
                "PNG": "png", 
                "WebP": "webp",
                "元のフォーマットを維持": "same",
                "入力と同じ": "same"
            }
            core_output_format = format_map.get(output_format_gui, "same")
            
            # EXIF処理変換
            exif_map = {"EXIFを保持": "keep", "EXIFを削除": "remove"}
            core_exif_handling = exif_map.get(exif_handling_gui, "keep")
            
            # 元画像を読み込み
            source_image = Image.open(input_path)
            original_width, original_height = source_image.size
            
            # リサイズ値を計算
            if core_resize_mode == "none":
                calculated_resize_value = original_width
            elif core_resize_mode == "width":
                calculated_resize_value = resize_value
            elif core_resize_mode == "height":
                if keep_aspect_ratio:
                    calculated_resize_value = int(original_width * (resize_value / original_height))
                else:
                    calculated_resize_value = original_width
            elif core_resize_mode == "percentage":
                calculated_resize_value = int(original_width * (resize_value / 100))
            elif core_resize_mode == "longest_side":
                if original_width > original_height:
                    calculated_resize_value = resize_value
                else:
                    calculated_resize_value = int(original_width * (resize_value / original_height))
            else:
                calculated_resize_value = resize_value
                
            # 出力バッファを作成
            output_buffer = io.BytesIO()
            
            # メモリベースの画像処理を実行
            effective_quality = quality if enable_compression else 100
            success, error_msg = resize_and_compress_image(
                source_image=source_image,
                output_buffer=output_buffer,
                resize_mode=core_resize_mode,
                resize_value=calculated_resize_value,
                quality=effective_quality,
                output_format=core_output_format if core_output_format != "same" else "jpeg",
                exif_handling=core_exif_handling,
                lanczos_filter=True,
                progressive=False,
                optimize=True,
                webp_lossless=False
            )
            
            if success:
                # バッファから画像を読み込み
                output_buffer.seek(0)
                preview_image = Image.open(output_buffer)
                
                # 変換後の詳細情報を計算
                preview_info = {
                    'original_size': (original_width, original_height),
                    'converted_size': preview_image.size,
                    'original_file_size': Path(input_path).stat().st_size,
                    'converted_file_size': len(output_buffer.getvalue()),
                    'original_format': source_image.format or "Unknown",
                    'converted_format': core_output_format.upper() if core_output_format != "same" else source_image.format,
                    'quality': effective_quality,
                    'resize_mode': core_resize_mode,
                    'resize_value': calculated_resize_value
                }
                
                # 圧縮率を計算
                reduction_rate = (1 - preview_info['converted_file_size'] / preview_info['original_file_size']) * 100
                preview_info['reduction_rate'] = reduction_rate
                
                # 一時ファイルに保存してプレビューウィジェットで表示
                import tempfile
                import uuid
                
                temp_dir = Path(tempfile.gettempdir())
                temp_filename = f"preview_{uuid.uuid4().hex}.png"
                temp_path = temp_dir / temp_filename
                
                # PNGとして保存（プレビュー用）
                preview_image.save(temp_path, format='PNG')
                
                # メインスレッドでUI更新（情報も含める）
                self.after(0, lambda: self._update_preview_ui(temp_path, preview_info))
                
            else:
                # エラーの場合
                self.after(0, lambda: self.add_log_message(f"プレビュー生成エラー: {error_msg}", is_warning=True))
                
        except Exception as e:
            # エラーログ
            self.after(0, lambda: self.add_log_message(f"プレビュー生成中にエラーが発生: {str(e)}", is_warning=True))
            
    def _update_preview_ui(self, preview_path: Path, preview_info: dict = None):
        """プレビューUIを更新"""
        _d("=== _update_preview_ui start === path=%s exists=%s", preview_path, preview_path.exists())
        try:
            if hasattr(self, 'comparison_preview'):
                self.comparison_preview.load_after_image(preview_path)
                
                # 変換情報を表示
                if preview_info:
                    self._update_conversion_info(preview_info)
                
            # 一時ファイルを削除（少し遅らせて削除）
            def cleanup_temp_file():
                try:
                    if preview_path.exists():
                        preview_path.unlink()
                except:
                    pass
                    
            self.after(5000, cleanup_temp_file)  # 5秒後に削除
            
        except Exception as e:
            self.add_log_message(f"プレビューUI更新エラー: {str(e)}", is_warning=True)
    
    def _update_conversion_info(self, info: dict):
        """変換情報を表示エリアに更新"""
        try:
            if not hasattr(self, 'comparison_preview'):
                return
                
            # ファイルサイズを読みやすい形式に変換
            def format_file_size(size_bytes):
                for unit in ['B', 'KB', 'MB', 'GB']:
                    if size_bytes < 1024.0:
                        return f"{size_bytes:.1f} {unit}"
                    size_bytes /= 1024.0
                return f"{size_bytes:.1f} GB"
            
            # ビフォー情報
            original_size_text = f"{info['original_size'][0]} × {info['original_size'][1]} px"
            original_file_size_text = format_file_size(info['original_file_size'])
            before_text = f"元画像: {original_size_text}\n{original_file_size_text}, {info['original_format']}"
            
            # アフター情報
            converted_size_text = f"{info['converted_size'][0]} × {info['converted_size'][1]} px"
            converted_file_size_text = format_file_size(info['converted_file_size'])
            reduction_text = f"({info['reduction_rate']:+.1f}%)" if info['reduction_rate'] != 0 else ""
            after_text = f"変換後: {converted_size_text}\n{converted_file_size_text}, {info['converted_format']} {reduction_text}"
            
            # 設定情報
            resize_mode_names = {
                'none': 'なし',
                'width': '幅指定',
                'height': '高さ指定',
                'percentage': 'パーセント',
                'longest_side': '長辺指定'
            }
            resize_mode_display = resize_mode_names.get(info['resize_mode'], info['resize_mode'])
            settings_text = f"品質: {info['quality']}, リサイズ: {resize_mode_display}"
            if info['resize_mode'] != 'none':
                unit = '%' if info['resize_mode'] == 'percentage' else 'px'
                settings_text += f" ({info['resize_value']}{unit})"
            
            # ラベルを更新
            self.comparison_preview.before_label.configure(text=f"変換前\n{before_text}")
            self.comparison_preview.after_label.configure(text=f"変換後\n{after_text}\n{settings_text}")
            
        except Exception as e:
            print(f"変換情報更新エラー: {e}")
    
    def _update_original_image_info(self, input_path: str):
        """元画像の情報を表示"""
        try:
            if not hasattr(self, 'comparison_preview'):
                return
                
            from PIL import Image
            
            # 元画像の情報を取得
            source_image = Image.open(input_path)
            original_width, original_height = source_image.size
            original_file_size = Path(input_path).stat().st_size
            original_format = source_image.format or "Unknown"
            
            # ファイルサイズを読みやすい形式に変換
            def format_file_size(size_bytes):
                for unit in ['B', 'KB', 'MB', 'GB']:
                    if size_bytes < 1024.0:
                        return f"{size_bytes:.1f} {unit}"
                    size_bytes /= 1024.0
                return f"{size_bytes:.1f} GB"
            
            # ビフォー情報
            original_size_text = f"{original_width} × {original_height} px"
            original_file_size_text = format_file_size(original_file_size)
            before_text = f"元画像: {original_size_text}\n{original_file_size_text}, {original_format}"
            
            # ビフォーラベルを更新
            self.comparison_preview.before_label.configure(text=f"変換前\n{before_text}")
            
            # アフターラベルをリセット
            self.comparison_preview.after_label.configure(text="変換後\n設定を変更してプレビューを確認")
            
        except Exception as e:
            print(f"元画像情報更新エラー: {e}")
    
    def _setup_preview_auto_update(self):
        """プレビュー自動更新の設定"""
        try:
            # リサイズモード変更時
            if hasattr(self, 'resize_mode_var'):
                def on_resize_mode_change_with_preview(*args):
                    self.on_resize_mode_change(self.resize_mode_var.get())
                    # プレビュータブが選択されている場合のみ更新
                    if hasattr(self, 'tab_view') and self.tab_view.get() == "プレビュー":
                        self.after(500, self._update_preview_after)  # 500ms遅延で更新
                        
                self.resize_mode_var.trace('w', on_resize_mode_change_with_preview)
            
            # 品質変更時
            if hasattr(self, 'resize_quality_var'):
                def on_quality_change(*args):
                    if hasattr(self, 'tab_view') and self.tab_view.get() == "プレビュー":
                        self.after(500, self._update_preview_after)
                        
                self.resize_quality_var.trace('w', on_quality_change)
            
            # 出力フォーマット変更時
            if hasattr(self, 'resize_output_format_var'):
                def on_format_change(*args):
                    if hasattr(self, 'tab_view') and self.tab_view.get() == "プレビュー":
                        self.after(500, self._update_preview_after)
                        
                self.resize_output_format_var.trace('w', on_format_change)
                
            # 圧縮設定変更時
            if hasattr(self, 'resize_enable_compression_var'):
                def on_compression_change(*args):
                    if hasattr(self, 'tab_view') and self.tab_view.get() == "プレビュー":
                        self.after(500, self._update_preview_after)
                        
                self.resize_enable_compression_var.trace('w', on_compression_change)
                
            # バランス変更時
            if hasattr(self, 'resize_balance_var'):
                def on_balance_change(*args):
                    if hasattr(self, 'tab_view') and self.tab_view.get() == "プレビュー":
                        self.after(1000, self._update_preview_after)  # バランスは1秒遅延
                        
                self.resize_balance_var.trace('w', on_balance_change)
                
        except Exception as e:
            print(f"プレビュー自動更新設定エラー: {e}")
    
    def _update_statistics(self):
        """統計情報を更新"""
        if not hasattr(self, 'stats_viewer') or not self.history_manager:
            return
            
        # 履歴から統計データを生成
        entries = self.history_manager.get_entries(limit=1000)
        self.stats_viewer.update_data(entries)
    
    def reprocess_from_history(self, source_path: str, settings: dict):
        """履歴から再処理を実行"""
        # ファイルパスを設定
        self.input_entry.delete(0, "end")
        self.input_entry.insert(0, source_path)
        
        # 設定を適用
        if 'resize_mode' in settings and hasattr(self, 'resize_mode_var'):
            self.resize_mode_var.set(settings['resize_mode'])
            self.on_resize_mode_change(settings['resize_mode'])
            
        if 'resize_value' in settings and hasattr(self, 'resize_value_entry'):
            self.resize_value_entry.delete(0, "end")
            self.resize_value_entry.insert(0, str(settings['resize_value']))
            
        if 'quality' in settings and hasattr(self, 'resize_quality_var'):
            self.resize_quality_var.set(settings['quality'])
            if hasattr(self, 'resize_quality_slider'):
                self.resize_quality_slider.set(settings['quality'])
        
        # プレビュータブに切り替え
        if hasattr(self, 'tab_view'):
            self.tab_view.set("プレビュー")
        
        self.add_log_message(f"履歴から設定を読み込みました: {Path(source_path).name}")


def main():
    # 設定マネージャーを初期化して、保存されているテーマを読み込む
    settings_manager = SettingsManager() if 'SettingsManager' in globals() else None
    if settings_manager:
        settings_manager.load()
        theme = settings_manager.get_ui_settings().theme
        
        if theme == "system":
            # システム設定に従う
            try:
                import darkdetect
                if darkdetect.isDark():
                    ctk.set_appearance_mode("dark")
                else:
                    ctk.set_appearance_mode("light")
            except:
                ctk.set_appearance_mode("light")
        else:
            ctk.set_appearance_mode(theme)
    else:
        # デフォルトはライトモード
        ctk.set_appearance_mode("light")

    # カスタムテーマを適用
    theme_path = Path(__file__).parent / "karuku_light_theme.json"
    if theme_path.exists():
        ctk.set_default_color_theme(str(theme_path))
    else:
        ctk.set_default_color_theme("blue")

    app = App()
    # ウィンドウクローズイベントを設定
    app.protocol("WM_DELETE_WINDOW", app.on_window_close)
    app.mainloop()


if __name__ == "__main__":
    main()
