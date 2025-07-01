"""
統計情報表示のモジュール
"""
import customtkinter as ctk
from typing import Dict, Any, List
import matplotlib
matplotlib.use('TkAgg')
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
import numpy as np

# 日本語フォントの設定
plt.rcParams['font.sans-serif'] = ['Hiragino Sans', 'Yu Gothic', 'Meirio', 'Takao', 'IPAexGothic', 'IPAPGothic', 'VL PGothic', 'Noto Sans CJK JP']
plt.rcParams['axes.unicode_minus'] = False


class StatisticsViewer(ctk.CTkFrame):
    """統計情報ビューワー"""
    
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        
        self.stats_data: Dict[str, Any] = {}
        self._setup_ui()
        
    def _setup_ui(self):
        """UIをセットアップ"""
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        
        # ヘッダー
        header_frame = ctk.CTkFrame(self)
        header_frame.grid(row=0, column=0, sticky="ew", padx=10, pady=(10, 5))
        header_frame.grid_columnconfigure(1, weight=1)
        
        title_label = ctk.CTkLabel(
            header_frame,
            text="📊 処理統計",
            font=("", 20, "bold")
        )
        title_label.grid(row=0, column=0, padx=10, pady=10, sticky="w")
        
        # 期間選択
        period_frame = ctk.CTkFrame(header_frame, fg_color="transparent")
        period_frame.grid(row=0, column=1, padx=10, pady=10, sticky="e")
        
        ctk.CTkLabel(period_frame, text="期間:").pack(side="left", padx=5)
        
        self.period_var = ctk.StringVar(value="30")
        period_menu = ctk.CTkOptionMenu(
            period_frame,
            variable=self.period_var,
            values=["7", "30", "90", "365"],
            command=self._on_period_change,
            width=80
        )
        period_menu.pack(side="left", padx=5)
        
        ctk.CTkLabel(period_frame, text="日間").pack(side="left")
        
        # メインコンテンツ
        self.content_frame = ctk.CTkScrollableFrame(self)
        self.content_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=5)
        self.content_frame.grid_columnconfigure(0, weight=1)
        self.content_frame.grid_columnconfigure(1, weight=1)
        
        # サマリーカード
        self.summary_frame = ctk.CTkFrame(self.content_frame)
        self.summary_frame.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 10))
        
        self._create_summary_cards()
        
        # グラフエリア
        self.chart_frame = ctk.CTkFrame(self.content_frame)
        self.chart_frame.grid(row=1, column=0, columnspan=2, sticky="nsew")
        self.chart_frame.grid_columnconfigure(0, weight=1)
        self.chart_frame.grid_columnconfigure(1, weight=1)
        
    def _create_summary_cards(self):
        """サマリーカードを作成"""
        cards_data = [
            ("処理ファイル数", "total_count", "#1E88E5", "📁"),
            ("成功率", "success_rate", "#43A047", "✅"),
            ("総削減容量", "total_saved_size", "#E53935", "💾"),
            ("平均処理時間", "avg_processing_time", "#FB8C00", "⏱️")
        ]
        
        for i, (title, key, color, icon) in enumerate(cards_data):
            card = self._create_stat_card(title, key, color, icon)
            card.grid(row=0, column=i, padx=5, pady=5, sticky="nsew")
            self.summary_frame.grid_columnconfigure(i, weight=1)
            
    def _create_stat_card(self, title: str, data_key: str, color: str, icon: str) -> ctk.CTkFrame:
        """統計カードを作成"""
        card = ctk.CTkFrame(self.summary_frame, corner_radius=10)
        card.grid_columnconfigure(0, weight=1)
        
        # アイコンとタイトル
        header = ctk.CTkFrame(card, fg_color="transparent")
        header.grid(row=0, column=0, padx=15, pady=(10, 5), sticky="w")
        
        ctk.CTkLabel(header, text=icon, font=("", 24)).pack(side="left", padx=(0, 5))
        ctk.CTkLabel(header, text=title, font=("", 12)).pack(side="left")
        
        # 値
        value_label = ctk.CTkLabel(
            card,
            text="--",
            font=("", 24, "bold"),
            text_color=color
        )
        value_label.grid(row=1, column=0, padx=15, pady=(0, 10))
        
        # データキーを保存
        setattr(self, f"{data_key}_label", value_label)
        
        return card
        
    def update_statistics(self, stats: Dict[str, Any]):
        """統計情報を更新"""
        self.stats_data = stats
        
        # サマリーカードを更新
        self._update_summary_cards()
        
        # グラフを更新
        self._update_charts()
        
    def _update_summary_cards(self):
        """サマリーカードを更新"""
        if hasattr(self, 'total_count_label'):
            self.total_count_label.configure(
                text=f"{self.stats_data.get('total_count', 0):,}"
            )
            
        if hasattr(self, 'success_rate_label'):
            rate = self.stats_data.get('success_rate', 0)
            self.success_rate_label.configure(text=f"{rate:.1f}%")
            
        if hasattr(self, 'total_saved_size_label'):
            saved = self.stats_data.get('total_saved_size', 0)
            self.total_saved_size_label.configure(
                text=self._format_size(saved)
            )
            
        if hasattr(self, 'avg_processing_time_label'):
            avg_time = self.stats_data.get('avg_processing_time', 0)
            self.avg_processing_time_label.configure(
                text=f"{avg_time:.1f}秒"
            )
            
    def _update_charts(self):
        """グラフを更新"""
        # 既存のグラフをクリア
        for widget in self.chart_frame.winfo_children():
            widget.destroy()
            
        daily_stats = self.stats_data.get('daily_stats', [])
        if not daily_stats:
            no_data_label = ctk.CTkLabel(
                self.chart_frame,
                text="データがありません",
                font=("", 16)
            )
            no_data_label.grid(row=0, column=0, columnspan=2, pady=50)
            return
            
        # 日別処理数グラフ
        daily_chart = self._create_daily_chart(daily_stats)
        daily_chart.grid(row=0, column=0, padx=5, pady=5, sticky="nsew")
        
        # 累積削減容量グラフ
        cumulative_chart = self._create_cumulative_chart(daily_stats)
        cumulative_chart.grid(row=0, column=1, padx=5, pady=5, sticky="nsew")
        
    def _create_daily_chart(self, daily_stats: List[Dict]) -> ctk.CTkFrame:
        """日別処理数グラフを作成"""
        frame = ctk.CTkFrame(self.chart_frame)
        
        # データ準備
        dates = [datetime.fromisoformat(stat['date']) for stat in daily_stats]
        counts = [stat['count'] for stat in daily_stats]
        
        # グラフ作成
        fig = Figure(figsize=(5, 4), dpi=80, facecolor='#212121')
        ax = fig.add_subplot(111)
        ax.set_facecolor('#212121')
        
        # 棒グラフ
        ax.bar(dates, counts, color='#1E88E5', alpha=0.8)
        
        # スタイル設定
        ax.set_title('日別処理ファイル数', color='white', fontsize=14, pad=10)
        ax.set_xlabel('日付', color='white')
        ax.set_ylabel('ファイル数', color='white')
        ax.tick_params(colors='white')
        ax.spines['bottom'].set_color('white')
        ax.spines['left'].set_color('white')
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        
        # X軸の日付フォーマット
        if len(dates) > 7:
            ax.xaxis.set_major_locator(plt.MaxNLocator(7))
        fig.autofmt_xdate()
        
        # グリッド
        ax.grid(True, alpha=0.3, color='white', linestyle='--')
        
        # キャンバスに埋め込み
        canvas = FigureCanvasTkAgg(fig, frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True)
        
        return frame
        
    def _create_cumulative_chart(self, daily_stats: List[Dict]) -> ctk.CTkFrame:
        """累積削減容量グラフを作成"""
        frame = ctk.CTkFrame(self.chart_frame)
        
        # データ準備
        dates = [datetime.fromisoformat(stat['date']) for stat in daily_stats]
        saved_sizes = [stat['saved_size'] for stat in daily_stats]
        cumulative_sizes = np.cumsum(saved_sizes)
        
        # グラフ作成
        fig = Figure(figsize=(5, 4), dpi=80, facecolor='#212121')
        ax = fig.add_subplot(111)
        ax.set_facecolor('#212121')
        
        # 線グラフ
        ax.plot(dates, cumulative_sizes / (1024**3), color='#E53935', linewidth=2, marker='o', markersize=4)
        ax.fill_between(dates, 0, cumulative_sizes / (1024**3), alpha=0.3, color='#E53935')
        
        # スタイル設定
        ax.set_title('累積削減容量', color='white', fontsize=14, pad=10)
        ax.set_xlabel('日付', color='white')
        ax.set_ylabel('容量 (GB)', color='white')
        ax.tick_params(colors='white')
        ax.spines['bottom'].set_color('white')
        ax.spines['left'].set_color('white')
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        
        # X軸の日付フォーマット
        if len(dates) > 7:
            ax.xaxis.set_major_locator(plt.MaxNLocator(7))
        fig.autofmt_xdate()
        
        # グリッド
        ax.grid(True, alpha=0.3, color='white', linestyle='--')
        
        # キャンバスに埋め込み
        canvas = FigureCanvasTkAgg(fig, frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True)
        
        return frame
        
    def _format_size(self, size_bytes: int) -> str:
        """サイズをフォーマット"""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.1f} PB"
        
    def _on_period_change(self, value: str):
        """期間が変更された時"""
        # 親ウィジェットに通知（実装は親側で）
        if hasattr(self.master, 'on_stats_period_change'):
            self.master.on_stats_period_change(int(value))


class StatisticsDialog(ctk.CTkToplevel):
    """統計ダイアログ"""
    
    def __init__(self, parent, history_manager):
        super().__init__(parent)
        
        self.history_manager = history_manager
        self.title("処理統計")
        self.geometry("900x600")
        self.minsize(800, 500)
        
        # ウィンドウを中央に配置
        self.transient(parent)
        
        # 統計ビューワー
        self.stats_viewer = StatisticsViewer(self)
        self.stats_viewer.pack(fill="both", expand=True)
        
        # 初期データ読み込み
        self._load_statistics(30)
        
    def _load_statistics(self, days: int):
        """統計情報を読み込む"""
        stats = self.history_manager.get_statistics(days=days)
        self.stats_viewer.update_statistics(stats)
        
    def on_stats_period_change(self, days: int):
        """統計期間が変更された時"""
        self._load_statistics(days)