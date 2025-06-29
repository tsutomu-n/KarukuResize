"""
完全版メインウィンドウ（すべての機能を統合）
"""
import customtkinter as ctk
from pathlib import Path
import sys
from tkinter import filedialog, messagebox

# プロジェクトルートをPythonパスに追加
project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from .views.resize_tab_view import ResizeTabView
from .views.preview_tab_view import PreviewTabView
from .views.history_tab_view import HistoryTabView
from .views.statistics_tab_view import StatisticsTabView

from .view_models.resize_view_model import ResizeViewModel
from .view_models.preview_view_model import PreviewViewModel
from .view_models.history_view_model import HistoryViewModel
from .view_models.statistics_view_model import StatisticsViewModel

from ..services.image_service import ImageService
from ..services.history_service import HistoryService
from ..services.preset_service import PresetService
from ..services.settings_service import SettingsService

from .utils.constants import WINDOW, THEME, FONT


class MainWindowComplete(ctk.CTk):
    """完全版メインウィンドウクラス"""
    
    def __init__(self):
        super().__init__()
        
        # ウィンドウ設定
        self.title(WINDOW.TITLE)
        
        # サービスの初期化
        self.image_service = ImageService()
        self.history_service = HistoryService()
        self.preset_service = PresetService()
        self.settings_service = SettingsService()
        
        # 保存された設定を読み込む
        self._load_window_settings()
        
        # テーマ設定
        self.configure(fg_color=THEME.BG_PRIMARY)
        
        # ViewModelの初期化
        self.resize_view_model = ResizeViewModel(self.image_service)
        self.preview_view_model = PreviewViewModel(self.image_service)
        self.history_view_model = HistoryViewModel(self.history_service.history_manager)
        self.statistics_view_model = StatisticsViewModel(self.history_service)
        
        # UIの構築
        self._create_widgets()
        self._create_menu_bar()
        
        # ViewModelの初期化と設定の適用
        self._initialize_view_models()
        
        # ViewModels間の連携を設定
        self._setup_view_model_connections()
        
        # ウィンドウクローズイベント
        self.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        # キーボードショートカットを設定
        self._setup_keyboard_shortcuts()
    
    def _load_window_settings(self):
        """ウィンドウ設定を読み込む"""
        window_settings = self.settings_service.get_window_settings()
        
        width = window_settings.get("window_width", WINDOW.DEFAULT_WIDTH)
        height = window_settings.get("window_height", WINDOW.DEFAULT_HEIGHT)
        x = window_settings.get("window_x")
        y = window_settings.get("window_y")
        
        if x is not None and y is not None:
            self.geometry(f"{width}x{height}+{x}+{y}")
        else:
            self.geometry(f"{width}x{height}")
            self.after(100, self._center_window)
        
        self.minsize(WINDOW.MIN_WIDTH, WINDOW.MIN_HEIGHT)
    
    def _save_window_settings(self):
        """ウィンドウ設定を保存"""
        # ウィンドウの位置とサイズを取得
        self.update_idletasks()
        width = self.winfo_width()
        height = self.winfo_height()
        x = self.winfo_x()
        y = self.winfo_y()
        
        self.settings_service.save_window_settings(width, height, x, y)
    
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
        self._create_statistics_tab()
    
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
    
    def _create_statistics_tab(self):
        """統計タブを作成"""
        stats_tab = self.tab_view.add("統計")
        self.stats_view = StatisticsTabView(stats_tab, self.statistics_view_model)
        self.stats_view.pack(fill="both", expand=True)
    
    def _create_menu_bar(self):
        """メニューバーを作成"""
        import tkinter as tk
        
        menubar = tk.Menu(self)
        self.configure(menu=menubar)
        
        # ファイルメニュー
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="ファイル", menu=file_menu)
        file_menu.add_command(label="開く...", command=self._on_open_file, accelerator="Ctrl+O")
        file_menu.add_command(label="フォルダを開く...", command=self._on_open_folder, accelerator="Ctrl+Shift+O")
        file_menu.add_separator()
        
        # 最近使用したファイル
        recent_menu = tk.Menu(file_menu, tearoff=0)
        file_menu.add_cascade(label="最近使用したファイル", menu=recent_menu)
        self._update_recent_menu(recent_menu)
        
        file_menu.add_separator()
        file_menu.add_command(label="設定をエクスポート...", command=self._on_export_settings)
        file_menu.add_command(label="設定をインポート...", command=self._on_import_settings)
        file_menu.add_separator()
        file_menu.add_command(label="終了", command=self.on_closing, accelerator="Ctrl+Q")
        
        # 編集メニュー
        edit_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="編集", menu=edit_menu)
        edit_menu.add_command(label="プリセット管理...", command=self._on_manage_presets)
        edit_menu.add_command(label="プリセットをインポート...", command=self._on_import_presets)
        edit_menu.add_command(label="プリセットをエクスポート...", command=self._on_export_presets)
        
        # 表示メニュー
        view_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="表示", menu=view_menu)
        
        # テーマメニュー
        self.theme_var = tk.StringVar(value=self.settings_service.get_ui_settings().theme)
        theme_menu = tk.Menu(view_menu, tearoff=0)
        view_menu.add_cascade(label="テーマ", menu=theme_menu)
        theme_menu.add_radiobutton(label="ライトモード", variable=self.theme_var, value="light", command=lambda: self._change_theme("light"))
        theme_menu.add_radiobutton(label="ダークモード", variable=self.theme_var, value="dark", command=lambda: self._change_theme("dark"))
        theme_menu.add_radiobutton(label="システム設定に従う", variable=self.theme_var, value="system", command=lambda: self._change_theme("system"))
        
        view_menu.add_separator()
        view_menu.add_command(label="リサイズ", command=lambda: self.tab_view.set("画像リサイズ"), accelerator="Ctrl+1")
        view_menu.add_command(label="プレビュー", command=lambda: self.tab_view.set("プレビュー"), accelerator="Ctrl+2")
        view_menu.add_command(label="履歴", command=lambda: self.tab_view.set("履歴"), accelerator="Ctrl+3")
        view_menu.add_command(label="統計", command=lambda: self.tab_view.set("統計"), accelerator="Ctrl+4")
        
        # ツールメニュー
        tools_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="ツール", menu=tools_menu)
        tools_menu.add_command(label="最近のファイルをクリア", command=self._on_clear_recent)
        tools_menu.add_command(label="設定をリセット", command=self._on_reset_settings)
        
        # ヘルプメニュー
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="ヘルプ", menu=help_menu)
        help_menu.add_command(label="使い方", command=self._on_show_help, accelerator="F1")
        help_menu.add_command(label="ショートカットキー", command=self._on_show_shortcuts)
        help_menu.add_separator()
        help_menu.add_command(label="バージョン情報", command=self._on_show_about)
        
        # メニューの参照を保存
        self.recent_menu = recent_menu
    
    def _update_recent_menu(self, menu):
        """最近使用したファイルメニューを更新"""
        menu.delete(0, tk.END)
        
        recent_inputs = self.settings_service.get_recent_inputs()
        if recent_inputs:
            for path in recent_inputs[:10]:  # 最大10件
                menu.add_command(
                    label=Path(path).name,
                    command=lambda p=path: self._open_recent_file(p)
                )
        else:
            menu.add_command(label="(なし)", state="disabled")
    
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
    
    def _initialize_view_models(self):
        """ViewModelを初期化し、設定を適用"""
        # 各ViewModelを初期化
        self.resize_view_model.initialize()
        self.preview_view_model.initialize()
        self.history_view_model.initialize()
        self.statistics_view_model.initialize()
        
        # 保存された設定を適用
        resize_settings = self.settings_service.get_resize_settings()
        self.resize_view_model.resize_mode = resize_settings.mode
        self.resize_view_model.resize_value = resize_settings.value
        self.resize_view_model.quality = resize_settings.quality
        self.resize_view_model.output_format = resize_settings.output_format
        self.resize_view_model.maintain_aspect_ratio = resize_settings.maintain_aspect_ratio
        self.resize_view_model.preserve_metadata = (resize_settings.exif_handling == "keep")
        self.resize_view_model.prefix = resize_settings.prefix
        self.resize_view_model.suffix = resize_settings.suffix
    
    def _setup_view_model_connections(self):
        """ViewModels間の連携を設定"""
        # リサイズ処理完了時に履歴を追加
        self.resize_view_model.bind("processing_completed", self._on_processing_completed)
        self.resize_view_model.bind("batch_completed", self._on_batch_completed)
        
        # 履歴からの再処理リクエスト
        self.history_view.bind("switch_to_resize_tab", lambda _: self.tab_view.set("画像リサイズ"))
        
        # 設定変更時に保存
        for prop in ["resize_mode", "resize_value", "quality", "output_format", 
                     "maintain_aspect_ratio", "preserve_metadata", "prefix", "suffix"]:
            self.resize_view_model.bind(prop, lambda _: self._save_resize_settings())
    
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
        
        # 統計タブが選択されたら更新
        if current_tab == "統計":
            self.statistics_view_model.refresh()
    
    # メニューイベントハンドラ
    def _on_open_file(self):
        """ファイルを開く"""
        filename = filedialog.askopenfilename(
            title="画像ファイルを選択",
            filetypes=[
                ("画像ファイル", "*.jpg *.jpeg *.png *.gif *.bmp *.tiff *.webp"),
                ("すべてのファイル", "*.*")
            ]
        )
        if filename:
            self.resize_view_model.input_path = filename
            self.resize_view_model.processing_mode = "single"
            self.settings_service.add_recent_input(filename)
            self._update_recent_menu(self.recent_menu)
            self.tab_view.set("画像リサイズ")
    
    def _on_open_folder(self):
        """フォルダを開く"""
        dirname = filedialog.askdirectory(title="フォルダを選択")
        if dirname:
            self.resize_view_model.input_path = dirname
            self.resize_view_model.processing_mode = "batch"
            self.settings_service.add_recent_input(dirname)
            self._update_recent_menu(self.recent_menu)
            self.tab_view.set("画像リサイズ")
    
    def _open_recent_file(self, path):
        """最近使用したファイルを開く"""
        if Path(path).exists():
            if Path(path).is_file():
                self.resize_view_model.processing_mode = "single"
            else:
                self.resize_view_model.processing_mode = "batch"
            self.resize_view_model.input_path = path
            self.tab_view.set("画像リサイズ")
        else:
            messagebox.showerror("エラー", f"ファイルが見つかりません:\n{path}")
    
    def _on_export_settings(self):
        """設定をエクスポート"""
        file_path = filedialog.asksaveasfilename(
            title="設定のエクスポート",
            defaultextension=".json",
            filetypes=[("JSONファイル", "*.json"), ("すべてのファイル", "*.*")]
        )
        if file_path:
            try:
                self.settings_service.export_settings(file_path)
                messagebox.showinfo("完了", "設定をエクスポートしました")
            except Exception as e:
                messagebox.showerror("エラー", f"エクスポートに失敗しました:\n{str(e)}")
    
    def _on_import_settings(self):
        """設定をインポート"""
        file_path = filedialog.askopenfilename(
            title="設定のインポート",
            filetypes=[("JSONファイル", "*.json"), ("すべてのファイル", "*.*")]
        )
        if file_path:
            try:
                self.settings_service.import_settings(file_path)
                self._initialize_view_models()  # 設定を再適用
                messagebox.showinfo("完了", "設定をインポートしました")
            except Exception as e:
                messagebox.showerror("エラー", f"インポートに失敗しました:\n{str(e)}")
    
    def _on_manage_presets(self):
        """プリセット管理"""
        from preset_dialog import PresetManagerDialog
        dialog = PresetManagerDialog(self, self.preset_service.preset_manager)
        
        def on_preset_selected(preset_data):
            self.resize_view_model.apply_preset(preset_data.to_dict())
        
        dialog.on_preset_selected = on_preset_selected
        self.wait_window(dialog)
    
    def _on_import_presets(self):
        """プリセットをインポート"""
        file_path = filedialog.askopenfilename(
            title="プリセットのインポート",
            filetypes=[("JSONファイル", "*.json"), ("すべてのファイル", "*.*")]
        )
        if file_path:
            try:
                count = self.preset_service.import_presets(file_path)
                messagebox.showinfo("完了", f"{count}個のプリセットをインポートしました")
            except Exception as e:
                messagebox.showerror("エラー", f"インポートに失敗しました:\n{str(e)}")
    
    def _on_export_presets(self):
        """プリセットをエクスポート"""
        file_path = filedialog.asksaveasfilename(
            title="プリセットのエクスポート",
            defaultextension=".json",
            filetypes=[("JSONファイル", "*.json"), ("すべてのファイル", "*.*")]
        )
        if file_path:
            try:
                self.preset_service.export_presets(file_path)
                messagebox.showinfo("完了", "プリセットをエクスポートしました")
            except Exception as e:
                messagebox.showerror("エラー", f"エクスポートに失敗しました:\n{str(e)}")
    
    def _on_clear_recent(self):
        """最近のファイルをクリア"""
        result = messagebox.askyesno("確認", "最近使用したファイルの履歴をクリアしますか？")
        if result:
            self.settings_service.clear_recent_files()
            self._update_recent_menu(self.recent_menu)
    
    def _on_reset_settings(self):
        """設定をリセット"""
        result = messagebox.askyesno(
            "確認", 
            "すべての設定をデフォルトに戻しますか？\nこの操作は取り消せません。"
        )
        if result:
            self.settings_service.reset_to_defaults()
            self._initialize_view_models()
            messagebox.showinfo("完了", "設定をリセットしました")
    
    def _on_show_help(self):
        """ヘルプを表示"""
        messagebox.showinfo(
            "使い方",
            "KarukuResize - 画像リサイズ・圧縮ツール\n\n"
            "【基本的な使い方】\n"
            "1. 「画像リサイズ」タブで画像またはフォルダを選択\n"
            "2. リサイズと圧縮の設定を調整\n"
            "3. 「プレビュー」タブで結果を確認\n"
            "4. 「処理開始」ボタンで実行\n\n"
            "【プリセット機能】\n"
            "よく使う設定をプリセットとして保存できます。\n"
            "編集メニューから「プリセット管理」を選択してください。\n\n"
            "【履歴と統計】\n"
            "処理した画像の履歴と統計情報を確認できます。\n"
            "履歴から再処理することも可能です。"
        )
    
    def _on_show_shortcuts(self):
        """ショートカットキーを表示"""
        messagebox.showinfo(
            "ショートカットキー",
            "【ショートカットキー一覧】\n\n"
            "Ctrl+O: ファイルを開く\n"
            "Ctrl+Shift+O: フォルダを開く\n"
            "Ctrl+S: 処理開始（リサイズタブ選択時）\n"
            "Ctrl+Q: アプリケーション終了\n\n"
            "Escape: 処理キャンセル\n"
            "F1: ヘルプを表示\n"
            "F9: プリセット管理\n\n"
            "Ctrl+1: リサイズタブへ切り替え\n"
            "Ctrl+2: プレビュータブへ切り替え\n"
            "Ctrl+3: 履歴タブへ切り替え\n"
            "Ctrl+4: 統計タブへ切り替え"
        )
    
    def _on_show_about(self):
        """バージョン情報を表示"""
        messagebox.showinfo(
            "バージョン情報",
            "KarukuResize v1.0.0\n\n"
            "完全リファクタリング版\n"
            "MVVMアーキテクチャ採用\n\n"
            "日本語対応の画像リサイズ・圧縮ツール\n"
            "「軽く」画像を処理します\n\n"
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
            # 履歴と統計を更新
            self.history_view_model.refresh()
            self.statistics_view_model.refresh()
    
    def _on_batch_completed(self, results):
        """バッチ処理完了時"""
        # 各結果を履歴に追加
        for result in results:
            self.history_service.add_processing_result(
                source_path=str(result.source_path),
                output_path=str(result.output_path) if result.output_path else None,
                success=result.success,
                settings=self.resize_view_model._get_current_settings().to_dict(),
                original_size=result.original_size,
                output_size=result.output_size,
                processing_time=result.processing_time
            )
        # 履歴と統計を更新
        self.history_view_model.refresh()
        self.statistics_view_model.refresh()
    
    def _save_resize_settings(self):
        """リサイズ設定を保存"""
        resize_settings = self.settings_service.get_resize_settings()
        resize_settings.mode = self.resize_view_model.resize_mode
        resize_settings.value = self.resize_view_model.resize_value
        resize_settings.quality = self.resize_view_model.quality
        resize_settings.output_format = self.resize_view_model.output_format
        resize_settings.maintain_aspect_ratio = self.resize_view_model.maintain_aspect_ratio
        resize_settings.exif_handling = "keep" if self.resize_view_model.preserve_metadata else "remove"
        resize_settings.prefix = self.resize_view_model.prefix
        resize_settings.suffix = self.resize_view_model.suffix
        
        self.settings_service.save_resize_settings(resize_settings)
    
    def _setup_keyboard_shortcuts(self):
        """キーボードショートカットを設定"""
        # ファイル操作
        self.bind("<Control-o>", lambda e: self._on_open_file())
        self.bind("<Control-O>", lambda e: self._on_open_folder())
        self.bind("<Control-q>", lambda e: self.on_closing())
        self.bind("<Control-Q>", lambda e: self.on_closing())
        
        # タブ切り替え
        self.bind("<Control-Key-1>", lambda e: self.tab_view.set("画像リサイズ"))
        self.bind("<Control-Key-2>", lambda e: self.tab_view.set("プレビュー"))
        self.bind("<Control-Key-3>", lambda e: self.tab_view.set("履歴"))
        self.bind("<Control-Key-4>", lambda e: self.tab_view.set("統計"))
        
        # 処理開始（リサイズタブが選択されている場合のみ）
        self.bind("<Control-s>", self._on_start_processing_shortcut)
        self.bind("<Control-S>", self._on_start_processing_shortcut)
        
        # キャンセル
        self.bind("<Escape>", self._on_cancel_processing_shortcut)
        
        # ヘルプ
        self.bind("<F1>", lambda e: self._on_show_help())
        
        # プリセット管理
        self.bind("<F9>", lambda e: self._on_manage_presets())
    
    def _on_start_processing_shortcut(self, event):
        """処理開始ショートカット"""
        if self.tab_view.get() == "画像リサイズ" and hasattr(self, 'resize_view'):
            # リサイズタブが選択されている場合のみ処理開始
            if self.resize_view_model.validate():
                self.resize_view_model.start_processing()
    
    def _on_cancel_processing_shortcut(self, event):
        """処理キャンセルショートカット"""
        if hasattr(self, 'resize_view_model') and self.resize_view_model.is_busy:
            self.resize_view_model.cancel_processing()
    
    def _change_theme(self, theme: str):
        """テーマを変更"""
        if theme == "system":
            # システム設定に従う
            try:
                import darkdetect
                actual_theme = "dark" if darkdetect.isDark() else "light"
            except:
                actual_theme = "light"
        else:
            actual_theme = theme
        
        # CustomTkinterのテーマを設定
        ctk.set_appearance_mode(actual_theme)
        
        # 設定を保存
        ui_settings = self.settings_service.get_ui_settings()
        ui_settings.theme = theme
        self.settings_service.save_ui_settings(ui_settings)
    
    def on_closing(self):
        """ウィンドウを閉じるとき"""
        # ウィンドウ設定を保存
        self._save_window_settings()
        
        # クリーンアップ
        if hasattr(self, 'resize_view'):
            self.resize_view.cleanup()
        if hasattr(self, 'preview_view'):
            self.preview_view.cleanup()
        if hasattr(self, 'history_view'):
            self.history_view.cleanup()
        if hasattr(self, 'stats_view'):
            self.stats_view.cleanup()
        
        self.destroy()


def main():
    """アプリケーションのエントリーポイント"""
    # 設定サービスを初期化してテーマを読み込む
    from ..services.settings_service import SettingsService
    settings_service = SettingsService()
    ui_settings = settings_service.get_ui_settings()
    theme = ui_settings.theme
    
    if theme == "system":
        # システム設定に従う
        try:
            import darkdetect
            actual_theme = "dark" if darkdetect.isDark() else "light"
        except:
            actual_theme = "light"
    else:
        actual_theme = theme
    
    # テーマ設定
    ctk.set_appearance_mode(actual_theme)
    
    # カスタムテーマファイルが存在する場合は使用
    theme_path = Path(__file__).parent.parent.parent / "karuku_light_theme.json"
    if theme_path.exists():
        ctk.set_default_color_theme(str(theme_path))
    else:
        ctk.set_default_color_theme("blue")
    
    # アプリケーション起動
    app = MainWindowComplete()
    app.mainloop()


if __name__ == "__main__":
    main()