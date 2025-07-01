"""
履歴タブのViewModel
"""
from typing import Optional, List, Dict, Any
from pathlib import Path
from datetime import datetime, timedelta
import sys

# プロジェクトルートをPythonパスに追加
project_root = Path(__file__).parent.parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from .base_view_model import BaseViewModel
from history_manager import HistoryManager, HistoryEntry


class HistoryViewModel(BaseViewModel):
    """履歴機能のViewModel"""
    
    def __init__(self, history_manager: Optional[HistoryManager] = None):
        super().__init__()
        self.history_manager = history_manager or HistoryManager()
        self._entries: List[HistoryEntry] = []
        
    def initialize(self) -> None:
        """初期化処理"""
        self.load_history()
        self._is_initialized = True
        
    def cleanup(self) -> None:
        """クリーンアップ処理"""
        self.unbind_all()
    
    # プロパティ
    @property
    def entries(self) -> List[HistoryEntry]:
        """履歴エントリのリスト"""
        return self._entries.copy()
    
    @property
    def search_query(self) -> str:
        """検索クエリ"""
        return self._get_property("search_query", "")
    
    @search_query.setter
    def search_query(self, value: str) -> None:
        self._set_property("search_query", value)
    
    @property
    def filter_success_only(self) -> bool:
        """成功のみフィルタ"""
        return self._get_property("filter_success_only", False)
    
    @filter_success_only.setter
    def filter_success_only(self, value: bool) -> None:
        self._set_property("filter_success_only", value)
    
    @property
    def filter_period(self) -> str:
        """期間フィルタ"""
        return self._get_property("filter_period", "all")
    
    @filter_period.setter
    def filter_period(self, value: str) -> None:
        self._set_property("filter_period", value)
    
    @property
    def selected_entry(self) -> Optional[HistoryEntry]:
        """選択されたエントリ"""
        return self._get_property("selected_entry", None)
    
    @selected_entry.setter
    def selected_entry(self, value: Optional[HistoryEntry]) -> None:
        self._set_property("selected_entry", value)
    
    @property
    def total_count(self) -> int:
        """総エントリ数"""
        return len(self._entries)
    
    @property
    def success_count(self) -> int:
        """成功エントリ数"""
        return sum(1 for entry in self._entries if entry.success)
    
    @property
    def total_size_saved(self) -> int:
        """総削減サイズ（バイト）"""
        total = 0
        for entry in self._entries:
            if entry.success and entry.original_size and entry.output_size:
                saved = entry.original_size - entry.output_size
                if saved > 0:
                    total += saved
        return total
    
    # メソッド
    def load_history(self, limit: int = 1000) -> None:
        """履歴を読み込む"""
        try:
            # フィルタを適用して履歴を取得
            search = self.search_query if self.search_query else None
            success_only = self.filter_success_only
            
            # 期間フィルタを適用
            after_date = None
            if self.filter_period == "today":
                after_date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
            elif self.filter_period == "week":
                after_date = datetime.now() - timedelta(days=7)
            elif self.filter_period == "month":
                after_date = datetime.now() - timedelta(days=30)
            
            # 履歴を取得
            self._entries = self.history_manager.get_entries(
                limit=limit,
                search=search,
                success_only=success_only,
                after_date=after_date
            )
            
            # 履歴更新を通知
            self._notify("history_loaded", self._entries)
            
            self.log_message(f"履歴を読み込みました: {len(self._entries)}件")
            
        except Exception as e:
            self.error_message = f"履歴の読み込みに失敗しました: {str(e)}"
            self.log_message(f"履歴読み込みエラー: {e}", "error")
    
    def refresh(self) -> None:
        """履歴をリフレッシュ"""
        self.load_history()
    
    def clear_filters(self) -> None:
        """フィルタをクリア"""
        self.search_query = ""
        self.filter_success_only = False
        self.filter_period = "all"
        self.load_history()
    
    def delete_entry(self, entry_id: int) -> None:
        """エントリを削除"""
        try:
            self.history_manager.delete_entry(entry_id)
            # リストから削除
            self._entries = [e for e in self._entries if e.id != entry_id]
            # 削除を通知
            self._notify("entry_deleted", entry_id)
            self.log_message(f"履歴エントリを削除しました: ID {entry_id}")
            
        except Exception as e:
            self.error_message = f"エントリの削除に失敗しました: {str(e)}"
    
    def clear_all_history(self) -> None:
        """すべての履歴をクリア"""
        try:
            self.history_manager.clear_all()
            self._entries = []
            self._notify("history_cleared", None)
            self.log_message("すべての履歴をクリアしました")
            
        except Exception as e:
            self.error_message = f"履歴のクリアに失敗しました: {str(e)}"
    
    def export_to_csv(self, file_path: str) -> None:
        """CSVにエクスポート"""
        try:
            path = Path(file_path)
            self.history_manager.export_to_csv(str(path))
            self.log_message(f"履歴をCSVにエクスポートしました: {path.name}")
            self._notify("export_completed", str(path))
            
        except Exception as e:
            self.error_message = f"CSVエクスポートに失敗しました: {str(e)}"
    
    def export_to_json(self, file_path: str) -> None:
        """JSONにエクスポート"""
        try:
            path = Path(file_path)
            self.history_manager.export_to_json(str(path))
            self.log_message(f"履歴をJSONにエクスポートしました: {path.name}")
            self._notify("export_completed", str(path))
            
        except Exception as e:
            self.error_message = f"JSONエクスポートに失敗しました: {str(e)}"
    
    def get_entry_details(self, entry: HistoryEntry) -> Dict[str, Any]:
        """エントリの詳細情報を取得"""
        details = {
            "id": entry.id,
            "timestamp": entry.timestamp,
            "source_path": entry.source_path,
            "output_path": entry.output_path,
            "success": entry.success,
            "error_message": entry.error_message,
            "settings": entry.settings,
            "original_size": entry.original_size,
            "output_size": entry.output_size,
            "processing_time": entry.processing_time
        }
        
        # サイズ削減情報を追加
        if entry.original_size and entry.output_size:
            reduction = entry.original_size - entry.output_size
            reduction_percent = (reduction / entry.original_size) * 100
            details["size_reduction"] = reduction
            details["size_reduction_percent"] = reduction_percent
        
        return details
    
    def reprocess_entry(self, entry: HistoryEntry) -> None:
        """エントリを再処理"""
        if not entry.source_path or not Path(entry.source_path).exists():
            self.error_message = "ソースファイルが見つかりません"
            return
        
        # 再処理リクエストを通知
        reprocess_data = {
            "source_path": entry.source_path,
            "settings": entry.settings
        }
        self._notify("reprocess_requested", reprocess_data)
        self.log_message(f"再処理をリクエストしました: {Path(entry.source_path).name}")
    
    def get_statistics(self) -> Dict[str, Any]:
        """統計情報を取得"""
        stats = {
            "total_count": self.total_count,
            "success_count": self.success_count,
            "failure_count": self.total_count - self.success_count,
            "total_size_saved": self.total_size_saved,
            "average_processing_time": 0.0,
            "most_used_settings": {}
        }
        
        # 平均処理時間を計算
        processing_times = [e.processing_time for e in self._entries if e.processing_time]
        if processing_times:
            stats["average_processing_time"] = sum(processing_times) / len(processing_times)
        
        # 最も使用された設定を分析
        resize_modes = {}
        output_formats = {}
        
        for entry in self._entries:
            if entry.settings:
                mode = entry.settings.get("resize_mode", "unknown")
                fmt = entry.settings.get("output_format", "unknown")
                
                resize_modes[mode] = resize_modes.get(mode, 0) + 1
                output_formats[fmt] = output_formats.get(fmt, 0) + 1
        
        if resize_modes:
            stats["most_used_settings"]["resize_mode"] = max(resize_modes, key=resize_modes.get)
        if output_formats:
            stats["most_used_settings"]["output_format"] = max(output_formats, key=output_formats.get)
        
        return stats