"""
スレッドセーフなGUI操作のためのユーティリティモジュール
"""
from queue import Queue, Empty
import threading
from typing import Callable, Any, Tuple, Optional
import customtkinter as ctk
from dataclasses import dataclass
from enum import Enum

class MessageType(Enum):
    """メッセージタイプの定義"""
    LOG = "log"
    PROGRESS = "progress"
    ENABLE_BUTTON = "enable_button"
    DISABLE_BUTTON = "disable_button"
    UPDATE_LABEL = "update_label"
    UPDATE_ENTRY = "update_entry"
    SHOW_ERROR = "show_error"
    SHOW_INFO = "show_info"
    CUSTOM = "custom"

@dataclass
class ThreadMessage:
    """スレッド間メッセージ"""
    msg_type: MessageType
    data: Any
    callback: Optional[Callable] = None

class ThreadSafeGUI:
    """スレッドセーフなGUI操作のためのミックスインクラス"""
    
    def __init__(self):
        self.message_queue: Queue[ThreadMessage] = Queue()
        self.processing_lock = threading.Lock()
        self.cancel_event = threading.Event()
        self._queue_check_interval = 50  # ミリ秒
        
    def setup_thread_safety(self):
        """スレッドセーフティのセットアップ（__init__の後に呼ぶ）"""
        self._start_queue_checker()
    
    def _start_queue_checker(self):
        """キューチェッカーを開始"""
        self.after(self._queue_check_interval, self._check_queue)
    
    def _check_queue(self):
        """メッセージキューをチェック"""
        messages_processed = 0
        max_messages_per_check = 10  # 一度のチェックで処理する最大メッセージ数
        
        try:
            while messages_processed < max_messages_per_check:
                try:
                    message = self.message_queue.get_nowait()
                    self._process_queue_message(message)
                    messages_processed += 1
                except Empty:
                    break
        except Exception as e:
            print(f"キュー処理エラー: {e}")
        finally:
            self.after(self._queue_check_interval, self._check_queue)
    
    def _process_queue_message(self, message: ThreadMessage):
        """キューメッセージを処理"""
        try:
            if message.msg_type == MessageType.LOG:
                if hasattr(self, 'add_log_message'):
                    self.add_log_message(message.data)
            
            elif message.msg_type == MessageType.PROGRESS:
                if hasattr(self, 'progress_bar'):
                    self.progress_bar.set(message.data)
            
            elif message.msg_type == MessageType.ENABLE_BUTTON:
                widget = message.data
                if widget and hasattr(widget, 'configure'):
                    widget.configure(state="normal")
            
            elif message.msg_type == MessageType.DISABLE_BUTTON:
                widget = message.data
                if widget and hasattr(widget, 'configure'):
                    widget.configure(state="disabled")
            
            elif message.msg_type == MessageType.UPDATE_LABEL:
                widget, text = message.data
                if widget and hasattr(widget, 'configure'):
                    widget.configure(text=text)
            
            elif message.msg_type == MessageType.UPDATE_ENTRY:
                widget, text = message.data
                if widget and hasattr(widget, 'delete'):
                    widget.delete(0, "end")
                    widget.insert(0, text)
            
            elif message.msg_type == MessageType.CUSTOM:
                if message.callback:
                    message.callback(message.data)
            
        except Exception as e:
            print(f"メッセージ処理エラー: {e}")
    
    def thread_safe_call(self, msg_type: MessageType, data: Any, callback: Optional[Callable] = None):
        """スレッドセーフにGUI操作を実行"""
        message = ThreadMessage(msg_type, data, callback)
        self.message_queue.put(message)
    
    def thread_safe_log(self, message: str, is_error: bool = False, is_warning: bool = False):
        """スレッドセーフにログを追加"""
        log_data = {
            'message': message,
            'is_error': is_error,
            'is_warning': is_warning
        }
        self.thread_safe_call(MessageType.LOG, log_data)
    
    def thread_safe_progress(self, value: float):
        """スレッドセーフに進捗を更新"""
        self.thread_safe_call(MessageType.PROGRESS, value)
    
    def thread_safe_enable_button(self, button: ctk.CTkButton):
        """スレッドセーフにボタンを有効化"""
        self.thread_safe_call(MessageType.ENABLE_BUTTON, button)
    
    def thread_safe_disable_button(self, button: ctk.CTkButton):
        """スレッドセーフにボタンを無効化"""
        self.thread_safe_call(MessageType.DISABLE_BUTTON, button)
    
    def thread_safe_update_label(self, label: ctk.CTkLabel, text: str):
        """スレッドセーフにラベルを更新"""
        self.thread_safe_call(MessageType.UPDATE_LABEL, (label, text))
    
    def is_cancelled(self) -> bool:
        """処理がキャンセルされたかチェック"""
        return self.cancel_event.is_set()
    
    def request_cancel(self):
        """処理のキャンセルをリクエスト"""
        self.cancel_event.set()
    
    def reset_cancel(self):
        """キャンセル状態をリセット"""
        self.cancel_event.clear()
    
    def with_lock(self, func: Callable, *args, **kwargs) -> Any:
        """ロック付きで関数を実行"""
        with self.processing_lock:
            return func(*args, **kwargs)