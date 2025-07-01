"""
統計タブのViewModel
"""
from typing import Optional, Dict, Any, List, Tuple
from datetime import datetime, timedelta, date
from pathlib import Path
import sys

# プロジェクトルートをPythonパスに追加
project_root = Path(__file__).parent.parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from .base_view_model import BaseViewModel
from ...services.history_service import HistoryService


class StatisticsViewModel(BaseViewModel):
    """統計機能のViewModel"""
    
    def __init__(self, history_service: Optional[HistoryService] = None):
        super().__init__()
        self.history_service = history_service or HistoryService()
        self._statistics_data: Dict[str, Any] = {}
        
    def initialize(self) -> None:
        """初期化処理"""
        self.period_filter = "week"  # デフォルトは週間
        self.load_statistics()
        self._is_initialized = True
        
    def cleanup(self) -> None:
        """クリーンアップ処理"""
        self.unbind_all()
    
    # プロパティ
    @property
    def period_filter(self) -> str:
        """期間フィルタ（today, week, month, year, all）"""
        return self._get_property("period_filter", "week")
    
    @period_filter.setter
    def period_filter(self, value: str) -> None:
        self._set_property("period_filter", value)
    
    @property
    def statistics_data(self) -> Dict[str, Any]:
        """統計データ"""
        return self._statistics_data.copy()
    
    @property
    def total_processed(self) -> int:
        """総処理数"""
        return self._statistics_data.get("total_count", 0)
    
    @property
    def success_rate(self) -> float:
        """成功率"""
        return self._statistics_data.get("success_rate", 0.0)
    
    @property
    def total_size_saved(self) -> int:
        """総削減サイズ（バイト）"""
        return self._statistics_data.get("total_size_saved", 0)
    
    @property
    def average_size_reduction(self) -> float:
        """平均サイズ削減率"""
        return self._statistics_data.get("average_size_reduction", 0.0)
    
    @property
    def daily_data(self) -> List[Tuple[date, Dict[str, Any]]]:
        """日別データ"""
        daily_stats = self._statistics_data.get("daily_stats", {})
        return sorted(daily_stats.items())
    
    @property
    def resize_mode_distribution(self) -> Dict[str, int]:
        """リサイズモードの分布"""
        return self._statistics_data.get("resize_modes", {})
    
    @property
    def output_format_distribution(self) -> Dict[str, int]:
        """出力フォーマットの分布"""
        return self._statistics_data.get("output_formats", {})
    
    # メソッド
    def load_statistics(self) -> None:
        """統計データを読み込む"""
        try:
            # 期間を計算
            after_date, before_date = self._calculate_period_dates()
            
            # 統計データを取得
            self._statistics_data = self.history_service.get_statistics(
                after_date=after_date,
                before_date=before_date
            )
            
            # データ読み込み完了を通知
            self._notify("statistics_loaded", self._statistics_data)
            
            self.log_message(f"統計データを読み込みました: {self.period_filter}")
            
        except Exception as e:
            self.error_message = f"統計データの読み込みに失敗しました: {str(e)}"
            self.log_message(f"統計読み込みエラー: {e}", "error")
    
    def refresh(self) -> None:
        """統計データをリフレッシュ"""
        self.load_statistics()
    
    def change_period(self, period: str) -> None:
        """期間を変更"""
        if period in ["today", "week", "month", "year", "all"]:
            self.period_filter = period
            self.load_statistics()
    
    def get_chart_data(self, chart_type: str) -> Dict[str, Any]:
        """グラフ用のデータを取得"""
        if chart_type == "daily_trend":
            return self._get_daily_trend_data()
        elif chart_type == "size_reduction":
            return self._get_size_reduction_data()
        elif chart_type == "resize_modes":
            return self._get_resize_modes_data()
        elif chart_type == "output_formats":
            return self._get_output_formats_data()
        elif chart_type == "processing_time":
            return self._get_processing_time_data()
        else:
            return {}
    
    def export_statistics(self, file_path: str, format_type: str = "csv") -> None:
        """統計データをエクスポート"""
        try:
            path = Path(file_path)
            
            if format_type == "csv":
                self._export_to_csv(path)
            elif format_type == "json":
                self._export_to_json(path)
            else:
                raise ValueError(f"サポートされていないフォーマット: {format_type}")
            
            self.log_message(f"統計データをエクスポートしました: {path.name}")
            self._notify("export_completed", str(path))
            
        except Exception as e:
            self.error_message = f"エクスポートに失敗しました: {str(e)}"
    
    # プライベートメソッド
    def _calculate_period_dates(self) -> Tuple[Optional[datetime], Optional[datetime]]:
        """期間フィルタから日付範囲を計算"""
        now = datetime.now()
        before_date = now
        
        if self.period_filter == "today":
            after_date = now.replace(hour=0, minute=0, second=0, microsecond=0)
        elif self.period_filter == "week":
            after_date = now - timedelta(days=7)
        elif self.period_filter == "month":
            after_date = now - timedelta(days=30)
        elif self.period_filter == "year":
            after_date = now - timedelta(days=365)
        else:  # all
            after_date = None
            before_date = None
        
        return after_date, before_date
    
    def _get_daily_trend_data(self) -> Dict[str, Any]:
        """日別トレンドデータを取得"""
        daily_stats = self._statistics_data.get("daily_stats", {})
        
        # 日付順にソート
        sorted_days = sorted(daily_stats.keys())
        
        dates = []
        counts = []
        success_counts = []
        size_saved = []
        
        for day in sorted_days:
            stats = daily_stats[day]
            dates.append(day)
            counts.append(stats.get("count", 0))
            success_counts.append(stats.get("success", 0))
            size_saved.append(stats.get("size_saved", 0) / (1024 * 1024))  # MB単位
        
        return {
            "dates": dates,
            "total_counts": counts,
            "success_counts": success_counts,
            "size_saved_mb": size_saved
        }
    
    def _get_size_reduction_data(self) -> Dict[str, Any]:
        """サイズ削減データを取得"""
        return {
            "total_original_size": self._statistics_data.get("total_original_size", 0),
            "total_output_size": self._statistics_data.get("total_output_size", 0),
            "total_saved": self._statistics_data.get("total_size_saved", 0),
            "average_reduction_percent": self._statistics_data.get("average_size_reduction", 0)
        }
    
    def _get_resize_modes_data(self) -> Dict[str, Any]:
        """リサイズモード分布データを取得"""
        modes = self._statistics_data.get("resize_modes", {})
        
        # 表示名に変換
        from ..utils.constants import ResizeMode
        labels = []
        values = []
        
        for mode, count in modes.items():
            display_name = ResizeMode.get_display_name(mode)
            labels.append(display_name)
            values.append(count)
        
        return {
            "labels": labels,
            "values": values
        }
    
    def _get_output_formats_data(self) -> Dict[str, Any]:
        """出力フォーマット分布データを取得"""
        formats = self._statistics_data.get("output_formats", {})
        
        # 表示名に変換
        from ..utils.constants import OutputFormat
        labels = []
        values = []
        
        for fmt, count in formats.items():
            display_name = OutputFormat.get_display_name(fmt)
            labels.append(display_name)
            values.append(count)
        
        return {
            "labels": labels,
            "values": values
        }
    
    def _get_processing_time_data(self) -> Dict[str, Any]:
        """処理時間データを取得"""
        avg_time = self._statistics_data.get("average_processing_time", 0)
        
        # 日別の平均処理時間を計算（実装は簡略化）
        daily_stats = self._statistics_data.get("daily_stats", {})
        
        return {
            "average_time": avg_time,
            "daily_average": {}  # TODO: 日別平均を計算
        }
    
    def _export_to_csv(self, path: Path) -> None:
        """CSVにエクスポート"""
        import csv
        
        with open(path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            
            # ヘッダー
            writer.writerow(["統計情報", f"期間: {self.period_filter}"])
            writer.writerow([])
            
            # 基本統計
            writer.writerow(["指標", "値"])
            writer.writerow(["総処理数", self.total_processed])
            writer.writerow(["成功率", f"{self.success_rate:.1f}%"])
            writer.writerow(["総削減サイズ", f"{self.total_size_saved / (1024*1024*1024):.2f} GB"])
            writer.writerow(["平均削減率", f"{self.average_size_reduction:.1f}%"])
            writer.writerow([])
            
            # 日別データ
            writer.writerow(["日付", "処理数", "成功数", "削減サイズ(MB)"])
            for day, stats in self.daily_data:
                writer.writerow([
                    day.strftime("%Y-%m-%d"),
                    stats.get("count", 0),
                    stats.get("success", 0),
                    f"{stats.get('size_saved', 0) / (1024*1024):.1f}"
                ])
    
    def _export_to_json(self, path: Path) -> None:
        """JSONにエクスポート"""
        import json
        
        export_data = {
            "period": self.period_filter,
            "generated_at": datetime.now().isoformat(),
            "statistics": self._statistics_data
        }
        
        # 日付をシリアライズ可能な形式に変換
        if "daily_stats" in export_data["statistics"]:
            daily_stats = {}
            for day, stats in export_data["statistics"]["daily_stats"].items():
                daily_stats[day.isoformat() if hasattr(day, 'isoformat') else str(day)] = stats
            export_data["statistics"]["daily_stats"] = daily_stats
        
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, ensure_ascii=False, indent=2)