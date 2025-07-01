"""
統計タブのView
"""
import customtkinter as ctk
from tkinter import filedialog
from pathlib import Path
from typing import Optional
import sys

# プロジェクトルートをPythonパスに追加
project_root = Path(__file__).parent.parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from .base_view import BaseView
from ..view_models.statistics_view_model import StatisticsViewModel
from ..utils.ui_builders import UIBuilder
from ..utils.constants import FONT, THEME, UI
from statistics_viewer import StatisticsViewer


class StatisticsTabView(BaseView):
    """統計タブのView"""
    
    def __init__(self, parent, view_model: Optional[StatisticsViewModel] = None):
        # ViewModelがない場合は作成
        if view_model is None:
            view_model = StatisticsViewModel()
        
        super().__init__(parent, view_model)
        
    def _create_widgets(self) -> None:
        """ウィジェットを作成"""
        # メインコンテナ
        self.main_container = ctk.CTkFrame(self, fg_color="transparent")
        
        # ヘッダー（期間選択とアクション）
        self._create_header()
        
        # サマリーカード
        self._create_summary_cards()
        
        # 統計ビューワー（既存のウィジェットを使用）
        self.stats_viewer = StatisticsViewer(self.main_container)
        
    def _layout_widgets(self) -> None:
        """ウィジェットを配置"""
        self.main_container.pack(fill="both", expand=True)
        
        # ヘッダー
        self.header.pack(fill="x", padx=UI.PADDING_MEDIUM, pady=(UI.PADDING_MEDIUM, 0))
        
        # サマリーカード
        self.summary_container.pack(
            fill="x", 
            padx=UI.PADDING_MEDIUM, 
            pady=UI.PADDING_MEDIUM
        )
        
        # 統計ビューワー
        self.stats_viewer.pack(
            fill="both", 
            expand=True, 
            padx=UI.PADDING_MEDIUM, 
            pady=(0, UI.PADDING_MEDIUM)
        )
    
    def _create_header(self) -> None:
        """ヘッダーを作成"""
        self.header = ctk.CTkFrame(
            self.main_container,
            height=50,
            corner_radius=UI.CORNER_RADIUS,
            border_width=UI.BORDER_WIDTH,
            border_color=THEME.BORDER_COLOR
        )
        
        # タイトル
        title_label = ctk.CTkLabel(
            self.header,
            text="📊 処理統計",
            font=ctk.CTkFont(size=FONT.SIZE_HEADING, weight=FONT.WEIGHT_BOLD),
            text_color=THEME.TEXT_PRIMARY
        )
        title_label.pack(side="left", padx=UI.PADDING_LARGE, pady=UI.PADDING_MEDIUM)
        
        # 右側のコントロール
        right_frame = ctk.CTkFrame(self.header, fg_color="transparent")
        right_frame.pack(side="right", padx=UI.PADDING_MEDIUM, pady=UI.PADDING_SMALL)
        
        # エクスポートボタン
        self.export_btn = UIBuilder.create_button(
            right_frame,
            "エクスポート",
            self._on_export,
            variant="secondary",
            width=100
        )
        self.export_btn.pack(side="right", padx=(UI.PADDING_SMALL, 0))
        
        # リフレッシュボタン
        self.refresh_btn = UIBuilder.create_button(
            right_frame,
            "更新",
            self._on_refresh,
            variant="secondary",
            width=60
        )
        self.refresh_btn.pack(side="right", padx=(UI.PADDING_SMALL, 0))
        
        # 期間選択
        period_frame = ctk.CTkFrame(right_frame, fg_color="transparent")
        period_frame.pack(side="right", padx=(0, UI.PADDING_LARGE))
        
        ctk.CTkLabel(
            period_frame,
            text="期間:",
            font=ctk.CTkFont(size=FONT.SIZE_NORMAL),
            text_color=THEME.TEXT_PRIMARY
        ).pack(side="left", padx=(0, UI.PADDING_SMALL))
        
        self.period_var = ctk.StringVar(value="今週")
        self.period_menu = UIBuilder.create_option_menu(
            period_frame,
            self.period_var,
            ["今日", "今週", "今月", "今年", "すべて"],
            self._on_period_changed,
            width=100
        )
        self.period_menu.pack(side="left")
    
    def _create_summary_cards(self) -> None:
        """サマリーカードを作成"""
        self.summary_container = ctk.CTkFrame(
            self.main_container,
            fg_color="transparent"
        )
        
        # カードのグリッド配置
        cards = [
            {
                "title": "総処理数",
                "value": "0",
                "unit": "件",
                "color": THEME.ACCENT,
                "icon": "📁"
            },
            {
                "title": "成功率",
                "value": "0",
                "unit": "%",
                "color": THEME.SUCCESS,
                "icon": "✅"
            },
            {
                "title": "総削減サイズ",
                "value": "0",
                "unit": "MB",
                "color": THEME.WARNING,
                "icon": "💾"
            },
            {
                "title": "平均削減率",
                "value": "0",
                "unit": "%",
                "color": THEME.ACCENT,
                "icon": "📊"
            }
        ]
        
        self.summary_cards = {}
        
        for i, card_data in enumerate(cards):
            card = self._create_summary_card(
                self.summary_container,
                card_data["title"],
                card_data["value"],
                card_data["unit"],
                card_data["color"],
                card_data["icon"]
            )
            card.pack(side="left", fill="both", expand=True, padx=(0 if i == 0 else UI.PADDING_SMALL, 0))
            
            # カードの参照を保存
            self.summary_cards[card_data["title"]] = {
                "value_label": card.value_label,
                "unit_label": card.unit_label
            }
    
    def _create_summary_card(
        self, 
        parent: ctk.CTkFrame, 
        title: str, 
        value: str, 
        unit: str,
        color: str,
        icon: str
    ) -> ctk.CTkFrame:
        """サマリーカードを作成"""
        card = ctk.CTkFrame(
            parent,
            corner_radius=UI.CORNER_RADIUS,
            border_width=UI.BORDER_WIDTH,
            border_color=THEME.BORDER_COLOR,
            height=100
        )
        
        # コンテンツ
        content = ctk.CTkFrame(card, fg_color="transparent")
        content.pack(fill="both", expand=True, padx=UI.PADDING_MEDIUM, pady=UI.PADDING_MEDIUM)
        
        # タイトル行
        title_frame = ctk.CTkFrame(content, fg_color="transparent")
        title_frame.pack(fill="x")
        
        ctk.CTkLabel(
            title_frame,
            text=icon,
            font=ctk.CTkFont(size=20),
            text_color=color
        ).pack(side="left")
        
        ctk.CTkLabel(
            title_frame,
            text=title,
            font=ctk.CTkFont(size=FONT.SIZE_SMALL),
            text_color=THEME.TEXT_SECONDARY
        ).pack(side="left", padx=(UI.PADDING_SMALL, 0))
        
        # 値
        value_frame = ctk.CTkFrame(content, fg_color="transparent")
        value_frame.pack(fill="x", pady=(UI.PADDING_SMALL, 0))
        
        card.value_label = ctk.CTkLabel(
            value_frame,
            text=value,
            font=ctk.CTkFont(size=24, weight=FONT.WEIGHT_BOLD),
            text_color=color
        )
        card.value_label.pack(side="left")
        
        card.unit_label = ctk.CTkLabel(
            value_frame,
            text=unit,
            font=ctk.CTkFont(size=FONT.SIZE_NORMAL),
            text_color=THEME.TEXT_SECONDARY
        )
        card.unit_label.pack(side="left", padx=(UI.PADDING_SMALL, 0))
        
        return card
    
    def _setup_bindings(self) -> None:
        """ViewModelとのバインディングを設定"""
        super()._setup_bindings()
        
        if self.view_model:
            # 追加のバインディング
            self._bind_property("statistics_loaded", self._on_statistics_loaded)
            self._bind_property("export_completed", self._on_export_completed)
            
            # 初期化
            if not self.view_model.is_initialized:
                self.view_model.initialize()
    
    # イベントハンドラ
    def _on_period_changed(self, value: str) -> None:
        """期間変更"""
        if self.view_model:
            # 表示名から実際の値に変換
            period_map = {
                "今日": "today",
                "今週": "week",
                "今月": "month",
                "今年": "year",
                "すべて": "all"
            }
            self.view_model.change_period(period_map.get(value, "week"))
    
    def _on_refresh(self) -> None:
        """リフレッシュ"""
        if self.view_model:
            self.view_model.refresh()
    
    def _on_export(self) -> None:
        """エクスポート"""
        # エクスポート形式を選択
        from tkinter import messagebox
        export_format = messagebox.askquestion(
            "エクスポート形式",
            "CSV形式でエクスポートしますか？\n「いいえ」を選択するとJSON形式でエクスポートします。"
        )
        
        if export_format == "yes":
            file_path = filedialog.asksaveasfilename(
                title="統計データの保存（CSV）",
                defaultextension=".csv",
                filetypes=[("CSVファイル", "*.csv"), ("すべてのファイル", "*.*")]
            )
            if file_path and self.view_model:
                self.view_model.export_statistics(file_path, "csv")
        else:
            file_path = filedialog.asksaveasfilename(
                title="統計データの保存（JSON）",
                defaultextension=".json",
                filetypes=[("JSONファイル", "*.json"), ("すべてのファイル", "*.*")]
            )
            if file_path and self.view_model:
                self.view_model.export_statistics(file_path, "json")
    
    # ViewModelからの通知
    def _on_statistics_loaded(self, statistics_data: dict) -> None:
        """統計データ読み込み完了"""
        if not self.view_model:
            return
        
        # サマリーカードを更新
        self._update_summary_cards()
        
        # 統計ビューワーにデータを設定
        if hasattr(self.stats_viewer, 'update_data'):
            # 日別データを取得
            chart_data = self.view_model.get_chart_data("daily_trend")
            
            # 履歴エントリ形式に変換（StatisticsViewerの期待する形式）
            entries = []
            daily_data = self.view_model.daily_data
            
            # StatisticsViewerの update_data メソッドを呼び出す
            self.stats_viewer.update_data(entries)
            
            # グラフデータを個別に設定（必要に応じて）
            self._update_charts()
    
    def _update_summary_cards(self) -> None:
        """サマリーカードを更新"""
        if not self.view_model:
            return
        
        # 総処理数
        total = self.view_model.total_processed
        self.summary_cards["総処理数"]["value_label"].configure(text=str(total))
        
        # 成功率
        success_rate = self.view_model.success_rate
        self.summary_cards["成功率"]["value_label"].configure(text=f"{success_rate:.1f}")
        
        # 総削減サイズ
        saved_bytes = self.view_model.total_size_saved
        if saved_bytes >= 1024 * 1024 * 1024:  # GB
            saved_value = f"{saved_bytes / (1024 * 1024 * 1024):.1f}"
            saved_unit = "GB"
        elif saved_bytes >= 1024 * 1024:  # MB
            saved_value = f"{saved_bytes / (1024 * 1024):.1f}"
            saved_unit = "MB"
        else:  # KB
            saved_value = f"{saved_bytes / 1024:.1f}"
            saved_unit = "KB"
        
        self.summary_cards["総削減サイズ"]["value_label"].configure(text=saved_value)
        self.summary_cards["総削減サイズ"]["unit_label"].configure(text=saved_unit)
        
        # 平均削減率
        avg_reduction = self.view_model.average_size_reduction
        self.summary_cards["平均削減率"]["value_label"].configure(text=f"{avg_reduction:.1f}")
    
    def _update_charts(self) -> None:
        """グラフを更新"""
        if not self.view_model or not hasattr(self.stats_viewer, '_update_charts'):
            return
        
        # StatisticsViewerの期待する形式でデータを準備
        stats_data = {
            "processing_count_by_day": {},
            "size_reduction_by_day": {},
            "format_distribution": self.view_model.output_format_distribution,
            "resize_mode_distribution": self.view_model.resize_mode_distribution
        }
        
        # 日別データを変換
        for day, data in self.view_model.daily_data:
            day_str = day.strftime("%Y-%m-%d")
            stats_data["processing_count_by_day"][day_str] = data.get("count", 0)
            stats_data["size_reduction_by_day"][day_str] = data.get("size_saved", 0) / (1024 * 1024)  # MB
        
        # プライベートメソッドを直接呼び出す（統合のため）
        if hasattr(self.stats_viewer, 'stats_data'):
            self.stats_viewer.stats_data = stats_data
            self.stats_viewer._update_charts()
    
    def _on_export_completed(self, file_path: str) -> None:
        """エクスポート完了"""
        self.show_info_dialog(
            "エクスポート完了",
            f"統計データをエクスポートしました:\n{Path(file_path).name}"
        )