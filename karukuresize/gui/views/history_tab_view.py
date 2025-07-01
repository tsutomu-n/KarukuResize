"""
履歴タブのView
"""
import customtkinter as ctk
from tkinter import filedialog, messagebox
from pathlib import Path
from datetime import datetime
from typing import Optional, List
import sys

# プロジェクトルートをPythonパスに追加
project_root = Path(__file__).parent.parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from .base_view import BaseView
from ..view_models.history_view_model import HistoryViewModel
from ..utils.ui_builders import UIBuilder
from ..utils.constants import FONT, THEME, UI
from history_manager import HistoryEntry
from history_viewer import HistoryViewer


class HistoryTabView(BaseView):
    """履歴タブのView"""
    
    def __init__(self, parent, view_model: Optional[HistoryViewModel] = None, resize_view_model=None):
        # ViewModelがない場合は作成
        if view_model is None:
            view_model = HistoryViewModel()
        
        # リサイズViewModelへの参照を保持（再処理用）
        self.resize_view_model = resize_view_model
        
        super().__init__(parent, view_model)
        
    def _create_widgets(self) -> None:
        """ウィジェットを作成"""
        # メインコンテナ
        self.main_container = ctk.CTkFrame(self, fg_color="transparent")
        
        # ツールバー
        self._create_toolbar()
        
        # 履歴ビューワー（既存のウィジェットを使用）
        self.history_viewer = HistoryViewer(
            self.main_container,
            self.view_model.history_manager
        )
        
        # 統計パネル
        self._create_stats_panel()
        
    def _layout_widgets(self) -> None:
        """ウィジェットを配置"""
        self.main_container.pack(fill="both", expand=True)
        
        # ツールバー
        self.toolbar.pack(fill="x", padx=UI.PADDING_MEDIUM, pady=(UI.PADDING_MEDIUM, 0))
        
        # 履歴ビューワー
        self.history_viewer.pack(
            fill="both", 
            expand=True, 
            padx=UI.PADDING_MEDIUM, 
            pady=UI.PADDING_MEDIUM
        )
        
        # 統計パネル
        self.stats_panel.pack(
            fill="x", 
            padx=UI.PADDING_MEDIUM, 
            pady=(0, UI.PADDING_MEDIUM)
        )
    
    def _create_toolbar(self) -> None:
        """ツールバーを作成"""
        self.toolbar = ctk.CTkFrame(
            self.main_container,
            height=40,
            corner_radius=UI.CORNER_RADIUS,
            border_width=UI.BORDER_WIDTH,
            border_color=THEME.BORDER_COLOR
        )
        
        # 左側のコントロール（検索）
        left_frame = ctk.CTkFrame(self.toolbar, fg_color="transparent")
        left_frame.pack(side="left", padx=UI.PADDING_MEDIUM, pady=UI.PADDING_SMALL, fill="x", expand=True)
        
        # 検索エントリ
        ctk.CTkLabel(
            left_frame,
            text="検索:",
            font=ctk.CTkFont(size=FONT.SIZE_NORMAL),
            text_color=THEME.TEXT_PRIMARY
        ).pack(side="left", padx=(0, UI.PADDING_SMALL))
        
        self.search_entry = ctk.CTkEntry(
            left_frame,
            placeholder_text="ファイル名で検索...",
            font=ctk.CTkFont(size=FONT.SIZE_NORMAL),
            height=UI.ENTRY_HEIGHT,
            width=200
        )
        self.search_entry.pack(side="left", padx=(0, UI.PADDING_SMALL))
        self.search_entry.bind("<Return>", lambda e: self._on_search())
        self.search_entry.bind("<KeyRelease>", self._on_search_changed)
        
        # 検索ボタン
        self.search_btn = UIBuilder.create_button(
            left_frame,
            "検索",
            self._on_search,
            variant="secondary",
            width=60
        )
        self.search_btn.pack(side="left")
        
        # フィルター
        filter_frame = ctk.CTkFrame(left_frame, fg_color="transparent")
        filter_frame.pack(side="left", padx=(UI.PADDING_LARGE, 0))
        
        # 成功のみフィルター
        self.success_only_var = ctk.BooleanVar(value=False)
        self.success_only_check = UIBuilder.create_checkbox(
            filter_frame,
            "成功のみ",
            self.success_only_var,
            self._on_filter_changed
        )
        self.success_only_check.pack(side="left", padx=(0, UI.PADDING_MEDIUM))
        
        # 期間フィルター
        ctk.CTkLabel(
            filter_frame,
            text="期間:",
            font=ctk.CTkFont(size=FONT.SIZE_NORMAL),
            text_color=THEME.TEXT_PRIMARY
        ).pack(side="left", padx=(0, UI.PADDING_SMALL))
        
        self.period_var = ctk.StringVar(value="all")
        self.period_menu = UIBuilder.create_option_menu(
            filter_frame,
            self.period_var,
            ["すべて", "今日", "今週", "今月"],
            self._on_period_changed,
            width=100
        )
        self.period_menu.pack(side="left")
        
        # 右側のコントロール（アクション）
        right_frame = ctk.CTkFrame(self.toolbar, fg_color="transparent")
        right_frame.pack(side="right", padx=UI.PADDING_MEDIUM, pady=UI.PADDING_SMALL)
        
        # エクスポートボタン
        self.export_btn = UIBuilder.create_button(
            right_frame,
            "エクスポート",
            self._on_export,
            variant="secondary",
            width=100
        )
        self.export_btn.pack(side="left", padx=(0, UI.PADDING_SMALL))
        
        # リフレッシュボタン
        self.refresh_btn = UIBuilder.create_button(
            right_frame,
            "更新",
            self._on_refresh,
            variant="secondary",
            width=60
        )
        self.refresh_btn.pack(side="left", padx=(0, UI.PADDING_SMALL))
        
        # クリアボタン
        self.clear_btn = UIBuilder.create_button(
            right_frame,
            "履歴クリア",
            self._on_clear_all,
            variant="danger",
            width=100
        )
        self.clear_btn.pack(side="left")
    
    def _create_stats_panel(self) -> None:
        """統計パネルを作成"""
        self.stats_panel = ctk.CTkFrame(
            self.main_container,
            height=60,
            corner_radius=UI.CORNER_RADIUS,
            border_width=UI.BORDER_WIDTH,
            border_color=THEME.BORDER_COLOR
        )
        
        # 統計情報フレーム
        stats_container = ctk.CTkFrame(self.stats_panel, fg_color="transparent")
        stats_container.pack(fill="x", expand=True, padx=UI.PADDING_MEDIUM, pady=UI.PADDING_SMALL)
        
        # 総数
        total_frame = ctk.CTkFrame(stats_container, fg_color="transparent")
        total_frame.pack(side="left", fill="x", expand=True)
        
        self.total_label = ctk.CTkLabel(
            total_frame,
            text="0",
            font=ctk.CTkFont(size=FONT.SIZE_HEADING, weight=FONT.WEIGHT_BOLD),
            text_color=THEME.TEXT_PRIMARY
        )
        self.total_label.pack()
        
        ctk.CTkLabel(
            total_frame,
            text="総処理数",
            font=ctk.CTkFont(size=FONT.SIZE_SMALL),
            text_color=THEME.TEXT_SECONDARY
        ).pack()
        
        # セパレーター
        sep1 = ctk.CTkFrame(stats_container, width=1, height=40, fg_color=THEME.BORDER_COLOR)
        sep1.pack(side="left", padx=UI.PADDING_MEDIUM)
        
        # 成功数
        success_frame = ctk.CTkFrame(stats_container, fg_color="transparent")
        success_frame.pack(side="left", fill="x", expand=True)
        
        self.success_label = ctk.CTkLabel(
            success_frame,
            text="0",
            font=ctk.CTkFont(size=FONT.SIZE_HEADING, weight=FONT.WEIGHT_BOLD),
            text_color=THEME.SUCCESS
        )
        self.success_label.pack()
        
        ctk.CTkLabel(
            success_frame,
            text="成功",
            font=ctk.CTkFont(size=FONT.SIZE_SMALL),
            text_color=THEME.TEXT_SECONDARY
        ).pack()
        
        # セパレーター
        sep2 = ctk.CTkFrame(stats_container, width=1, height=40, fg_color=THEME.BORDER_COLOR)
        sep2.pack(side="left", padx=UI.PADDING_MEDIUM)
        
        # 削減サイズ
        saved_frame = ctk.CTkFrame(stats_container, fg_color="transparent")
        saved_frame.pack(side="left", fill="x", expand=True)
        
        self.saved_label = ctk.CTkLabel(
            saved_frame,
            text="0 MB",
            font=ctk.CTkFont(size=FONT.SIZE_HEADING, weight=FONT.WEIGHT_BOLD),
            text_color=THEME.ACCENT
        )
        self.saved_label.pack()
        
        ctk.CTkLabel(
            saved_frame,
            text="総削減サイズ",
            font=ctk.CTkFont(size=FONT.SIZE_SMALL),
            text_color=THEME.TEXT_SECONDARY
        ).pack()
    
    def _setup_bindings(self) -> None:
        """ViewModelとのバインディングを設定"""
        super()._setup_bindings()
        
        if self.view_model:
            # 追加のバインディング
            self._bind_property("history_loaded", self._on_history_loaded)
            self._bind_property("entry_deleted", self._on_entry_deleted)
            self._bind_property("history_cleared", self._on_history_cleared)
            self._bind_property("export_completed", self._on_export_completed)
            self._bind_property("reprocess_requested", self._on_reprocess_requested)
            
            # 初期化
            if not self.view_model.is_initialized:
                self.view_model.initialize()
        
        # 履歴ビューワーのイベントをバインド
        # （既存のHistoryViewerウィジェットは独自のイベント処理を持つ）
        # 必要に応じて、カスタムイベントをバインド
    
    # イベントハンドラ
    def _on_search(self) -> None:
        """検索実行"""
        if self.view_model:
            self.view_model.load_history()
    
    def _on_search_changed(self, event) -> None:
        """検索テキスト変更"""
        if self.view_model:
            self.view_model.search_query = self.search_entry.get()
    
    def _on_filter_changed(self) -> None:
        """フィルター変更"""
        if self.view_model:
            self.view_model.filter_success_only = self.success_only_var.get()
            self.view_model.load_history()
    
    def _on_period_changed(self, value: str) -> None:
        """期間フィルター変更"""
        if self.view_model:
            # 表示名から実際の値に変換
            period_map = {
                "すべて": "all",
                "今日": "today",
                "今週": "week",
                "今月": "month"
            }
            self.view_model.filter_period = period_map.get(value, "all")
            self.view_model.load_history()
    
    def _on_export(self) -> None:
        """エクスポート"""
        # エクスポート形式を選択するダイアログ
        export_format = messagebox.askquestion(
            "エクスポート形式",
            "CSV形式でエクスポートしますか？\n「いいえ」を選択するとJSON形式でエクスポートします。"
        )
        
        if export_format == "yes":
            file_path = filedialog.asksaveasfilename(
                title="CSVファイルの保存",
                defaultextension=".csv",
                filetypes=[("CSVファイル", "*.csv"), ("すべてのファイル", "*.*")]
            )
            if file_path and self.view_model:
                self.view_model.export_to_csv(file_path)
        else:
            file_path = filedialog.asksaveasfilename(
                title="JSONファイルの保存",
                defaultextension=".json",
                filetypes=[("JSONファイル", "*.json"), ("すべてのファイル", "*.*")]
            )
            if file_path and self.view_model:
                self.view_model.export_to_json(file_path)
    
    def _on_refresh(self) -> None:
        """リフレッシュ"""
        if self.view_model:
            self.view_model.refresh()
    
    def _on_clear_all(self) -> None:
        """すべての履歴をクリア"""
        result = messagebox.askyesno(
            "確認",
            "すべての履歴を削除しますか？\nこの操作は取り消せません。"
        )
        if result and self.view_model:
            self.view_model.clear_all_history()
    
    # ViewModelからの通知
    def _on_history_loaded(self, entries: List[HistoryEntry]) -> None:
        """履歴読み込み完了"""
        # 統計情報を更新
        if self.view_model:
            stats = self.view_model.get_statistics()
            
            self.total_label.configure(text=str(stats["total_count"]))
            self.success_label.configure(text=str(stats["success_count"]))
            
            # サイズを読みやすい形式に変換
            saved_bytes = stats["total_size_saved"]
            if saved_bytes >= 1024 * 1024 * 1024:  # GB
                saved_text = f"{saved_bytes / (1024 * 1024 * 1024):.1f} GB"
            elif saved_bytes >= 1024 * 1024:  # MB
                saved_text = f"{saved_bytes / (1024 * 1024):.1f} MB"
            elif saved_bytes >= 1024:  # KB
                saved_text = f"{saved_bytes / 1024:.1f} KB"
            else:
                saved_text = f"{saved_bytes} B"
            
            self.saved_label.configure(text=saved_text)
    
    def _on_entry_deleted(self, entry_id: int) -> None:
        """エントリ削除完了"""
        # 履歴ビューワーを更新
        if hasattr(self.history_viewer, '_load_history'):
            self.history_viewer._load_history()
    
    def _on_history_cleared(self, _) -> None:
        """履歴クリア完了"""
        # 履歴ビューワーを更新
        if hasattr(self.history_viewer, '_load_history'):
            self.history_viewer._load_history()
        
        # 統計をリセット
        self.total_label.configure(text="0")
        self.success_label.configure(text="0")
        self.saved_label.configure(text="0 MB")
    
    def _on_export_completed(self, file_path: str) -> None:
        """エクスポート完了"""
        self.show_info_dialog(
            "エクスポート完了",
            f"履歴データをエクスポートしました:\n{Path(file_path).name}"
        )
    
    def _on_reprocess_requested(self, data: dict) -> None:
        """再処理リクエスト"""
        if self.resize_view_model:
            # リサイズタブに設定を反映
            source_path = data.get("source_path", "")
            settings = data.get("settings", {})
            
            # ファイルパスを設定
            self.resize_view_model.input_path = source_path
            
            # 設定を適用
            if "resize_mode" in settings:
                self.resize_view_model.resize_mode = settings["resize_mode"]
            if "resize_value" in settings:
                self.resize_view_model.resize_value = settings["resize_value"]
            if "quality" in settings:
                self.resize_view_model.quality = settings["quality"]
            if "output_format" in settings:
                self.resize_view_model.output_format = settings["output_format"]
            
            # タブを切り替える（親ウィンドウで処理）
            self._notify("switch_to_resize_tab", None)