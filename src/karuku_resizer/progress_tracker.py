"""
進捗トラッキングのためのユーティリティモジュール
"""
import time
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Callable
from datetime import datetime, timedelta
import threading

@dataclass
class ProgressItem:
    """進捗アイテム"""
    name: str
    total: int
    current: int = 0
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    status: str = "pending"  # pending, processing, completed, failed
    error_message: Optional[str] = None
    
    @property
    def progress_percentage(self) -> float:
        """進捗率を取得"""
        if self.total == 0:
            return 0.0
        return min(100.0, (self.current / self.total) * 100)
    
    @property
    def elapsed_time(self) -> Optional[timedelta]:
        """経過時間を取得"""
        if not self.start_time:
            return None
        end = self.end_time or datetime.now()
        return end - self.start_time
    
    @property
    def estimated_remaining_time(self) -> Optional[timedelta]:
        """残り時間の推定"""
        if not self.start_time or self.current == 0:
            return None
        
        elapsed = self.elapsed_time
        if not elapsed:
            return None
            
        rate = self.current / elapsed.total_seconds()
        if rate == 0:
            return None
            
        remaining_items = self.total - self.current
        remaining_seconds = remaining_items / rate
        
        return timedelta(seconds=remaining_seconds)
    
    def start(self):
        """処理開始"""
        self.start_time = datetime.now()
        self.status = "processing"
        
    def update(self, current: int):
        """進捗更新"""
        self.current = min(current, self.total)
        
    def complete(self):
        """処理完了"""
        self.current = self.total
        self.end_time = datetime.now()
        self.status = "completed"
        
    def fail(self, error_message: str):
        """処理失敗"""
        self.end_time = datetime.now()
        self.status = "failed"
        self.error_message = error_message


@dataclass
class BatchProgress:
    """バッチ処理の進捗"""
    total_files: int
    completed_files: int = 0
    failed_files: int = 0
    skipped_files: int = 0
    items: List[ProgressItem] = field(default_factory=list)
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    
    @property
    def processed_files(self) -> int:
        """処理済みファイル数"""
        return self.completed_files + self.failed_files + self.skipped_files
    
    @property
    def overall_progress(self) -> float:
        """全体の進捗率"""
        if self.total_files == 0:
            return 0.0
        return (self.processed_files / self.total_files) * 100
    
    @property
    def success_rate(self) -> float:
        """成功率"""
        if self.processed_files == 0:
            return 0.0
        return (self.completed_files / self.processed_files) * 100
    
    @property
    def elapsed_time(self) -> Optional[timedelta]:
        """経過時間"""
        if not self.start_time:
            return None
        end = self.end_time or datetime.now()
        return end - self.start_time
    
    @property
    def estimated_remaining_time(self) -> Optional[timedelta]:
        """残り時間の推定"""
        if not self.start_time or self.processed_files == 0:
            return None
            
        elapsed = self.elapsed_time
        if not elapsed:
            return None
            
        rate = self.processed_files / elapsed.total_seconds()
        if rate == 0:
            return None
            
        remaining_files = self.total_files - self.processed_files
        remaining_seconds = remaining_files / rate
        
        return timedelta(seconds=remaining_seconds)
    
    def add_item(self, item: ProgressItem):
        """アイテムを追加"""
        self.items.append(item)
        
    def get_current_item(self) -> Optional[ProgressItem]:
        """現在処理中のアイテムを取得"""
        for item in self.items:
            if item.status == "processing":
                return item
        return None


class ProgressTracker:
    """進捗トラッカー"""
    
    def __init__(self):
        self.batch_progress: Optional[BatchProgress] = None
        self.callbacks: Dict[str, List[Callable]] = {
            'on_start': [],
            'on_update': [],
            'on_item_complete': [],
            'on_item_fail': [],
            'on_complete': [],
            'on_cancel': []
        }
        self._lock = threading.Lock()
        
    def register_callback(self, event: str, callback: Callable):
        """コールバックを登録"""
        if event in self.callbacks:
            self.callbacks[event].append(callback)
            
    def start_batch(self, total_files: int):
        """バッチ処理を開始"""
        with self._lock:
            self.batch_progress = BatchProgress(
                total_files=total_files,
                start_time=datetime.now()
            )
            self._trigger_callbacks('on_start', self.batch_progress)
            
    def start_item(self, name: str, total_steps: int = 1) -> ProgressItem:
        """アイテムの処理を開始"""
        with self._lock:
            if not self.batch_progress:
                raise RuntimeError("バッチ処理が開始されていません")
                
            item = ProgressItem(name=name, total=total_steps)
            item.start()
            self.batch_progress.add_item(item)
            self._trigger_callbacks('on_update', self.batch_progress, item)
            return item
            
    def update_item(self, item: ProgressItem, current: int):
        """アイテムの進捗を更新"""
        with self._lock:
            item.update(current)
            self._trigger_callbacks('on_update', self.batch_progress, item)
            
    def complete_item(self, item: ProgressItem):
        """アイテムの処理を完了"""
        with self._lock:
            item.complete()
            if self.batch_progress:
                self.batch_progress.completed_files += 1
            self._trigger_callbacks('on_item_complete', item)
            self._trigger_callbacks('on_update', self.batch_progress, item)
            
    def fail_item(self, item: ProgressItem, error_message: str):
        """アイテムの処理を失敗"""
        with self._lock:
            item.fail(error_message)
            if self.batch_progress:
                self.batch_progress.failed_files += 1
            self._trigger_callbacks('on_item_fail', item, error_message)
            self._trigger_callbacks('on_update', self.batch_progress, item)
            
    def skip_item(self, name: str, reason: str):
        """アイテムをスキップ"""
        with self._lock:
            if self.batch_progress:
                self.batch_progress.skipped_files += 1
                # スキップアイテムも記録
                item = ProgressItem(name=name, total=1)
                item.status = "skipped"
                item.error_message = reason
                self.batch_progress.add_item(item)
                self._trigger_callbacks('on_update', self.batch_progress, item)
                
    def complete_batch(self):
        """バッチ処理を完了"""
        with self._lock:
            if self.batch_progress:
                self.batch_progress.end_time = datetime.now()
                self._trigger_callbacks('on_complete', self.batch_progress)
                
    def cancel_batch(self):
        """バッチ処理をキャンセル"""
        with self._lock:
            if self.batch_progress:
                self.batch_progress.end_time = datetime.now()
                self._trigger_callbacks('on_cancel', self.batch_progress)
                
    def get_status_text(self) -> str:
        """ステータステキストを取得"""
        with self._lock:
            if not self.batch_progress:
                return "待機中"
                
            bp = self.batch_progress
            
            # 基本情報
            status_parts = [
                f"進捗: {bp.processed_files}/{bp.total_files} ({bp.overall_progress:.1f}%)",
                f"成功: {bp.completed_files}",
                f"失敗: {bp.failed_files}",
                f"スキップ: {bp.skipped_files}"
            ]
            
            # 経過時間
            if bp.elapsed_time:
                elapsed = self._format_timedelta(bp.elapsed_time)
                status_parts.append(f"経過: {elapsed}")
                
            # 残り時間
            if bp.estimated_remaining_time:
                remaining = self._format_timedelta(bp.estimated_remaining_time)
                status_parts.append(f"残り: {remaining}")
                
            return " | ".join(status_parts)
            
    def _format_timedelta(self, td: timedelta) -> str:
        """timedelta を読みやすい形式に変換"""
        total_seconds = int(td.total_seconds())
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        seconds = total_seconds % 60
        
        if hours > 0:
            return f"{hours}時間{minutes}分"
        elif minutes > 0:
            return f"{minutes}分{seconds}秒"
        else:
            return f"{seconds}秒"
            
    def _trigger_callbacks(self, event: str, *args):
        """コールバックをトリガー"""
        for callback in self.callbacks.get(event, []):
            try:
                callback(*args)
            except Exception as e:
                print(f"コールバックエラー ({event}): {e}")