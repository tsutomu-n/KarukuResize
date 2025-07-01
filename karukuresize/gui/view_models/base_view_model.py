"""
ViewModelの基底クラス
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Callable, Optional
import threading
from datetime import datetime


class Observable:
    """観察可能なプロパティを持つクラス"""
    
    def __init__(self):
        self._observers: Dict[str, List[Callable]] = {}
        self._properties: Dict[str, Any] = {}
        self._lock = threading.Lock()
    
    def bind(self, property_name: str, callback: Callable) -> None:
        """プロパティの変更を監視"""
        with self._lock:
            if property_name not in self._observers:
                self._observers[property_name] = []
            if callback not in self._observers[property_name]:
                self._observers[property_name].append(callback)
    
    def unbind(self, property_name: str, callback: Callable) -> None:
        """監視を解除"""
        with self._lock:
            if property_name in self._observers and callback in self._observers[property_name]:
                self._observers[property_name].remove(callback)
                if not self._observers[property_name]:
                    del self._observers[property_name]
    
    def unbind_all(self, property_name: Optional[str] = None) -> None:
        """すべての監視を解除"""
        with self._lock:
            if property_name:
                if property_name in self._observers:
                    del self._observers[property_name]
            else:
                self._observers.clear()
    
    def _notify(self, property_name: str, value: Any) -> None:
        """プロパティ変更を通知"""
        observers = []
        with self._lock:
            if property_name in self._observers:
                observers = self._observers[property_name].copy()
        
        # ロックの外でコールバックを実行
        for callback in observers:
            try:
                callback(value)
            except Exception as e:
                print(f"Observer callback error: {e}")
    
    def _get_property(self, name: str, default: Any = None) -> Any:
        """プロパティを取得"""
        with self._lock:
            return self._properties.get(name, default)
    
    def _set_property(self, name: str, value: Any) -> None:
        """プロパティを設定"""
        with self._lock:
            old_value = self._properties.get(name)
            if old_value != value:
                self._properties[name] = value
        
        # 値が変更された場合のみ通知
        if old_value != value:
            self._notify(name, value)


class BaseViewModel(Observable, ABC):
    """ViewModelの基底クラス"""
    
    def __init__(self):
        super().__init__()
        self._is_initialized = False
    
    # 共通プロパティ
    @property
    def is_busy(self) -> bool:
        """処理中フラグ"""
        return self._get_property("is_busy", False)
    
    @is_busy.setter
    def is_busy(self, value: bool) -> None:
        self._set_property("is_busy", value)
    
    @property
    def error_message(self) -> str:
        """エラーメッセージ"""
        return self._get_property("error_message", "")
    
    @error_message.setter
    def error_message(self, value: str) -> None:
        self._set_property("error_message", value)
    
    @property
    def status_message(self) -> str:
        """ステータスメッセージ"""
        return self._get_property("status_message", "")
    
    @status_message.setter
    def status_message(self, value: str) -> None:
        self._set_property("status_message", value)
    
    @property
    def progress(self) -> float:
        """進捗（0.0 - 1.0）"""
        return self._get_property("progress", 0.0)
    
    @progress.setter
    def progress(self, value: float) -> None:
        # 0.0 - 1.0の範囲に制限
        value = max(0.0, min(1.0, value))
        self._set_property("progress", value)
    
    @property
    def is_initialized(self) -> bool:
        """初期化済みフラグ"""
        return self._is_initialized
    
    # 抽象メソッド
    @abstractmethod
    def initialize(self) -> None:
        """初期化処理"""
        pass
    
    @abstractmethod
    def cleanup(self) -> None:
        """クリーンアップ処理"""
        pass
    
    # ヘルパーメソッド
    def log_message(self, message: str, level: str = "info") -> None:
        """ログメッセージを通知"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = {
            "timestamp": timestamp,
            "level": level,
            "message": message
        }
        self._notify("log_message", log_entry)
    
    def clear_error(self) -> None:
        """エラーメッセージをクリア"""
        self.error_message = ""
    
    def reset_progress(self) -> None:
        """進捗をリセット"""
        self.progress = 0.0
    
    def validate(self) -> bool:
        """検証処理（サブクラスでオーバーライド）"""
        return True