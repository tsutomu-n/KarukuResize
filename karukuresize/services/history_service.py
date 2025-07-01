"""
履歴管理サービス
"""
from pathlib import Path
from typing import Optional, List, Dict, Any
from datetime import datetime
import sys

# プロジェクトルートをPythonパスに追加
project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from history_manager import HistoryManager, HistoryEntry


class HistoryService:
    """履歴管理を行うサービスクラス"""
    
    def __init__(self, db_path: Optional[str] = None):
        self.history_manager = HistoryManager(db_path)
    
    def add_processing_result(
        self,
        source_path: str,
        output_path: Optional[str],
        success: bool,
        settings: Dict[str, Any],
        error_message: Optional[str] = None,
        original_size: Optional[int] = None,
        output_size: Optional[int] = None,
        processing_time: Optional[float] = None
    ) -> None:
        """処理結果を履歴に追加"""
        self.history_manager.add_entry(
            source_path=source_path,
            output_path=output_path,
            success=success,
            settings=settings,
            error_message=error_message,
            original_size=original_size,
            output_size=output_size,
            processing_time=processing_time
        )
    
    def get_recent_entries(
        self,
        limit: int = 100,
        success_only: bool = False
    ) -> List[HistoryEntry]:
        """最近のエントリを取得"""
        return self.history_manager.get_entries(
            limit=limit,
            success_only=success_only
        )
    
    def search_entries(
        self,
        query: str,
        limit: int = 100
    ) -> List[HistoryEntry]:
        """エントリを検索"""
        return self.history_manager.get_entries(
            search=query,
            limit=limit
        )
    
    def get_entries_by_period(
        self,
        after_date: datetime,
        before_date: Optional[datetime] = None,
        limit: int = 1000
    ) -> List[HistoryEntry]:
        """期間でエントリを取得"""
        return self.history_manager.get_entries(
            after_date=after_date,
            before_date=before_date,
            limit=limit
        )
    
    def get_statistics(
        self,
        after_date: Optional[datetime] = None,
        before_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """統計情報を取得"""
        entries = self.history_manager.get_entries(
            after_date=after_date,
            before_date=before_date,
            limit=10000  # 統計用に多めに取得
        )
        
        # 基本統計
        total_count = len(entries)
        success_count = sum(1 for e in entries if e.success)
        failure_count = total_count - success_count
        
        # サイズ統計
        total_original_size = 0
        total_output_size = 0
        total_size_saved = 0
        
        for entry in entries:
            if entry.success and entry.original_size and entry.output_size:
                total_original_size += entry.original_size
                total_output_size += entry.output_size
                saved = entry.original_size - entry.output_size
                if saved > 0:
                    total_size_saved += saved
        
        # 処理時間統計
        processing_times = [e.processing_time for e in entries if e.processing_time]
        avg_processing_time = sum(processing_times) / len(processing_times) if processing_times else 0
        
        # 設定統計
        resize_modes = {}
        output_formats = {}
        
        for entry in entries:
            if entry.settings:
                mode = entry.settings.get("resize_mode", "unknown")
                fmt = entry.settings.get("output_format", "unknown")
                
                resize_modes[mode] = resize_modes.get(mode, 0) + 1
                output_formats[fmt] = output_formats.get(fmt, 0) + 1
        
        # 日別統計
        daily_stats = {}
        for entry in entries:
            date = entry.timestamp.date()
            if date not in daily_stats:
                daily_stats[date] = {"count": 0, "success": 0, "size_saved": 0}
            
            daily_stats[date]["count"] += 1
            if entry.success:
                daily_stats[date]["success"] += 1
                if entry.original_size and entry.output_size:
                    saved = entry.original_size - entry.output_size
                    if saved > 0:
                        daily_stats[date]["size_saved"] += saved
        
        return {
            "total_count": total_count,
            "success_count": success_count,
            "failure_count": failure_count,
            "success_rate": (success_count / total_count * 100) if total_count > 0 else 0,
            "total_original_size": total_original_size,
            "total_output_size": total_output_size,
            "total_size_saved": total_size_saved,
            "average_size_reduction": (
                (total_size_saved / total_original_size * 100) 
                if total_original_size > 0 else 0
            ),
            "average_processing_time": avg_processing_time,
            "resize_modes": resize_modes,
            "output_formats": output_formats,
            "daily_stats": daily_stats
        }
    
    def delete_entry(self, entry_id: int) -> None:
        """エントリを削除"""
        self.history_manager.delete_entry(entry_id)
    
    def clear_all(self) -> None:
        """すべての履歴をクリア"""
        self.history_manager.clear_all()
    
    def export_to_csv(self, file_path: str) -> None:
        """CSVにエクスポート"""
        self.history_manager.export_to_csv(file_path)
    
    def export_to_json(self, file_path: str) -> None:
        """JSONにエクスポート"""
        self.history_manager.export_to_json(file_path)