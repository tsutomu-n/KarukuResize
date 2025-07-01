"""
拡張版メインウィンドウ（すべてのタブを含む）
"""
import customtkinter as ctk
from pathlib import Path
import sys

# プロジェクトルートをPythonパスに追加
project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from .views.resize_tab_view import ResizeTabView
from .views.preview_tab_view import PreviewTabView
from .views.history_tab_view import HistoryTabView

from .view_models.resize_view_model import ResizeViewModel
from .view_models.preview_view_model import PreviewViewModel
from .view_models.history_view_model import HistoryViewModel

from ..services.image_service import ImageService
from ..services.history_service import HistoryService
from preset_manager import PresetManager

from .utils.constants import WINDOW, THEME, FONT


class MainWindowExtended(ctk.CTk):
    """拡張版メインウィンドウクラス"""
    
    def __init__(self):
        super().__init__()
        
        # ウィンドウ設定
        self.title(WINDOW.TITLE)
        self.geometry(f"{WINDOW.DEFAULT_WIDTH}x{WINDOW.DEFAULT_HEIGHT}")
        self.minsize(WINDOW.MIN_WIDTH, WINDOW.MIN_HEIGHT)
        
        # テーマ設定
        self.configure(fg_color=THEME.BG_PRIMARY)
        
        # サービスとマネージャーの初期化
        self.image_service = ImageService()
        self.history_service = HistoryService()
        self.preset_manager = PresetManager()
        self.preset_manager.load()
        
        # ViewModelの初期化
        self.resize_view_model = ResizeViewModel(self.image_service)
        self.preview_view_model = PreviewViewModel(self.image_service)
        self.history_view_model = HistoryViewModel(self.history_service.history_manager)
        
        # UIの構築
        self._create_widgets()
        self._create_menu_bar()
        
        # ViewModelの初期化
        self.resize_view_model.initialize()
        self.preview_view_model.initialize()
        self.history_view_model.initialize()
        
        # ViewModels間の連携を設定
        self._setup_view_model_connections()
        
        # ウィンドウを中央に配置
        self._center_window()
        
        # ウィンドウクローズイベント
        self.protocol("WM_DELETE_WINDOW", self.on_closing)
    
    def _create_widgets(self):
        """ウィジェットを作成"""
        # メインコンテナ
        main_container = ctk.CTkFrame(self, fg_color="transparent")
        main_container.pack(fill="both", expand=True)
        
        # タブビュー
        self.tab_view = ctk.CTkTabview(
            main_container,
            corner_radius=10,
            command=self._on_tab_changed
        )
        self.tab_view.pack(fill="both", expand=True, padx=20, pady=20)
        
        # タブのフォント設定を試みる
        self._configure_tab_font()
        
        # 各タブを作成
        self._create_resize_tab()
        self._create_preview_tab()
        self._create_history_tab()
        self._create_stats_tab()
    
    def _create_resize_tab(self):
        """リサイズタブを作成"""
        resize_tab = self.tab_view.add("画像リサイズ")
        self.resize_view = ResizeTabView(resize_tab, self.resize_view_model)
        self.resize_view.pack(fill="both", expand=True)
    
    def _create_preview_tab(self):
        """プレビュータブを作成"""
        preview_tab = self.tab_view.add("プレビュー")
        self.preview_view = PreviewTabView(
            preview_tab, 
            self.preview_view_model,
            self.resize_view_model
        )
        self.preview_view.pack(fill="both", expand=True)
    
    def _create_history_tab(self):
        """履歴タブを作成"""
        history_tab = self.tab_view.add("履歴")
        self.history_view = HistoryTabView(
            history_tab,
            self.history_view_model,
            self.resize_view_model
        )
        self.history_view.pack(fill="both", expand=True)
    
    def _create_stats_tab(self):
        """統計タブを作成"""
        stats_tab = self.tab_view.add("統計")
        # 統計タブは後で実装
        stats_label = ctk.CTkLabel(
            stats_tab,
            text="統計機能は開発中です",
            font=ctk.CTkFont(size=FONT.SIZE_HEADING),
            text_color=THEME.TEXT_SECONDARY
        )
        stats_label.place(relx=0.5, rely=0.5, anchor="center")
    
    def _create_menu_bar(self):
        """メニューバーを作成"""
        # tkinterのメニューバーを使用（CustomTkinterはネイティブメニューをサポートしていない）
        import tkinter as tk
        
        menubar = tk.Menu(self)
        self.configure(menu=menubar)
        
        # ファイルメニュー
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="ファイル", menu=file_menu)
        file_menu.add_command(label="開く...", command=self._on_open_file)
        file_menu.add_separator()
        file_menu.add_command(label="設定を保存", command=self._on_save_settings)
        file_menu.add_command(label="設定を読み込む", command=self._on_load_settings)
        file_menu.add_separator()
        file_menu.add_command(label="終了", command=self.on_closing)
        
        # 編集メニュー
        edit_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="編集", menu=edit_menu)
        edit_menu.add_command(label="プリセット管理...", command=self._on_manage_presets)
        
        # 表示メニュー
        view_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="表示", menu=view_menu)
        view_menu.add_command(label="統計...", command=self._on_show_statistics)
        
        # ヘルプメニュー
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="ヘルプ", menu=help_menu)
        help_menu.add_command(label="使い方", command=self._on_show_help)
        help_menu.add_command(label="バージョン情報", command=self._on_show_about)
    
    def _configure_tab_font(self):
        """タブのフォント設定"""
        try:
            if hasattr(self.tab_view, "_segmented_button") and self.tab_view._segmented_button:
                self.tab_view._segmented_button.configure(
                    font=ctk.CTkFont(size=FONT.SIZE_HEADING, weight=FONT.WEIGHT_BOLD),
                    text_color=(THEME.TEXT_PRIMARY, "#FFFFFF"),
                    fg_color=THEME.BG_SECONDARY,
                    selected_color=THEME.ACCENT,
                    selected_hover_color=THEME.ACCENT_HOVER,
                    unselected_hover_color="#DEE2E6"
                )
        except Exception as e:
            print(f"タブフォント設定エラー: {e}")
    
    def _setup_view_model_connections(self):
        """ViewModels間の連携を設定"""
        # リサイズ処理完了時に履歴を追加
        self.resize_view_model.bind("processing_completed", self._on_processing_completed)
        self.resize_view_model.bind("batch_completed", self._on_batch_completed)
        
        # 履歴からの再処理リクエスト
        self.history_view.bind("switch_to_resize_tab", lambda _: self.tab_view.set("画像リサイズ"))
    
    def _center_window(self):
        """ウィンドウを中央に配置"""
        self.update_idletasks()
        width = self.winfo_width()
        height = self.winfo_height()
        x = (self.winfo_screenwidth() // 2) - (width // 2)
        y = (self.winfo_screenheight() // 2) - (height // 2)
        self.geometry(f"{width}x{height}+{x}+{y}")
    
    def _on_tab_changed(self):
        """タブが変更されたとき"""
        current_tab = self.tab_view.get()
        print(f"タブが変更されました: {current_tab}")
    
    # メニューイベントハンドラ
    def _on_open_file(self):
        """ファイルを開く"""
        from tkinter import filedialog
        filename = filedialog.askopenfilename(
            title="画像ファイルを選択",
            filetypes=[
                ("画像ファイル", "*.jpg *.jpeg *.png *.gif *.bmp *.tiff *.webp"),
                ("すべてのファイル", "*.*")
            ]
        )
        if filename:
            self.resize_view_model.input_path = filename
            self.tab_view.set("画像リサイズ")
    
    def _on_save_settings(self):
        """設定を保存"""
        # 設定保存機能の実装
        from tkinter import messagebox
        messagebox.showinfo("設定保存", "設定保存機能は開発中です")
    
    def _on_load_settings(self):
        """設定を読み込む"""
        # 設定読み込み機能の実装
        from tkinter import messagebox
        messagebox.showinfo("設定読み込み", "設定読み込み機能は開発中です")
    
    def _on_manage_presets(self):
        """プリセット管理"""
        # プリセット管理ダイアログの表示
        from preset_dialog import PresetManagerDialog
        dialog = PresetManagerDialog(self, self.preset_manager)
        
        def on_preset_selected(preset_data):
            self.resize_view_model.apply_preset(preset_data.to_dict())
        
        dialog.on_preset_selected = on_preset_selected
        self.wait_window(dialog)
    
    def _on_show_statistics(self):
        """統計を表示"""
        self.tab_view.set("統計")
    
    def _on_show_help(self):
        """ヘルプを表示"""
        from tkinter import messagebox
        messagebox.showinfo(
            "使い方",
            "KarukuResize - 画像リサイズ・圧縮ツール\n\n"
            "1. 「画像リサイズ」タブで画像と設定を選択\n"
            "2. 「プレビュー」タブで結果を確認\n"
            "3. 「処理開始」ボタンで実行\n"
            "4. 「履歴」タブで過去の処理を確認\n\n"
            "詳細はプロジェクトのREADMEをご覧ください。"
        )
    
    def _on_show_about(self):
        """バージョン情報を表示"""
        from tkinter import messagebox
        messagebox.showinfo(
            "バージョン情報",
            "KarukuResize v0.3.0\n\n"
            "MVVMアーキテクチャ版\n"
            "日本語対応の画像リサイズ・圧縮ツール\n\n"
            "© 2024 KarukuResize Project"
        )
    
    # ViewModelイベントハンドラ
    def _on_processing_completed(self, result):
        """処理完了時"""
        # 履歴に追加
        if result.success:
            self.history_service.add_processing_result(
                source_path=str(result.source_path),
                output_path=str(result.output_path) if result.output_path else None,
                success=result.success,
                settings=self.resize_view_model._get_current_settings().to_dict(),
                original_size=result.original_size,
                output_size=result.output_size,
                processing_time=result.processing_time
            )
            # 履歴を更新
            self.history_view_model.refresh()
    
    def _on_batch_completed(self, results):
        """バッチ処理完了時"""
        # 各結果を履歴に追加
        for result in results:
            if result.success:
                self.history_service.add_processing_result(
                    source_path=str(result.source_path),
                    output_path=str(result.output_path) if result.output_path else None,
                    success=result.success,
                    settings=self.resize_view_model._get_current_settings().to_dict(),
                    original_size=result.original_size,
                    output_size=result.output_size,
                    processing_time=result.processing_time
                )
        # 履歴を更新
        self.history_view_model.refresh()
    
    def on_closing(self):
        """ウィンドウを閉じるとき"""
        # クリーンアップ
        if hasattr(self, 'resize_view'):
            self.resize_view.cleanup()
        if hasattr(self, 'preview_view'):
            self.preview_view.cleanup()
        if hasattr(self, 'history_view'):
            self.history_view.cleanup()
        
        self.destroy()


def main():
    """アプリケーションのエントリーポイント"""
    # テーマ設定
    ctk.set_appearance_mode("light")
    
    # カスタムテーマファイルが存在する場合は使用
    theme_path = Path(__file__).parent.parent.parent / "karuku_light_theme.json"
    if theme_path.exists():
        ctk.set_default_color_theme(str(theme_path))
    else:
        ctk.set_default_color_theme("blue")
    
    # アプリケーション起動
    app = MainWindowExtended()
    app.mainloop()


if __name__ == "__main__":
    main()