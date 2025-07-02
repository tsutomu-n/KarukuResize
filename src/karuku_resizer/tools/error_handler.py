"""
エラーハンドリングのためのユーティリティモジュール
"""
from pathlib import Path
from typing import Optional, Dict, Any
import logging

class ErrorHandler:
    """統一的なエラーハンドリングクラス"""
    
    ERROR_MESSAGES = {
        FileNotFoundError: "ファイルが見つかりません: {filepath}",
        PermissionError: "ファイルへのアクセス権限がありません: {filepath}",
        ValueError: "無効な値が入力されました: {value}",
        MemoryError: "メモリ不足です。より小さな画像で試してください",
        OSError: "システムエラーが発生しました: {error}",
        IOError: "ファイルの読み書きエラー: {filepath}",
        KeyError: "設定項目が見つかりません: {key}",
        TypeError: "型が正しくありません: {expected_type}",
        AttributeError: "属性が見つかりません: {attribute}",
        RuntimeError: "実行時エラー: {error}",
    }
    
    @classmethod
    def get_user_friendly_message(cls, error: Exception, **kwargs) -> str:
        """ユーザーフレンドリーなエラーメッセージを取得"""
        error_type = type(error)
        template = cls.ERROR_MESSAGES.get(error_type, "予期しないエラー: {error}")
        
        # kwargsにerrorが含まれていない場合は追加
        if 'error' not in kwargs:
            kwargs['error'] = str(error)
        
        try:
            return template.format(**kwargs)
        except KeyError:
            # フォーマット失敗時はシンプルなメッセージを返す
            return f"{error_type.__name__}: {str(error)}"
    
    @classmethod
    def get_suggestions(cls, error: Exception) -> list[str]:
        """エラーに対する解決策の提案を取得"""
        suggestions = {
            FileNotFoundError: [
                "ファイルパスが正しいか確認してください",
                "ファイルが移動または削除されていないか確認してください",
                "ファイル名に誤字がないか確認してください"
            ],
            PermissionError: [
                "ファイルが他のプログラムで開かれていないか確認してください",
                "ファイルの読み取り専用属性を解除してください",
                "管理者権限でアプリケーションを実行してみてください"
            ],
            ValueError: [
                "入力値が正しい形式か確認してください",
                "数値の範囲が適切か確認してください",
                "必須項目が全て入力されているか確認してください"
            ],
            MemoryError: [
                "より小さな画像で試してください",
                "他のアプリケーションを終了してメモリを解放してください",
                "システムの仮想メモリ設定を確認してください"
            ],
            OSError: [
                "ディスクの空き容量を確認してください",
                "ファイルシステムのエラーをチェックしてください",
                "ウイルス対策ソフトが干渉していないか確認してください"
            ]
        }
        
        return suggestions.get(type(error), ["エラーログを確認してください", "アプリケーションを再起動してください"])
    
    @classmethod
    def log_error(cls, error: Exception, context: Optional[Dict[str, Any]] = None):
        """エラーをログに記録"""
        logging.error(f"Error type: {type(error).__name__}")
        logging.error(f"Error message: {str(error)}")
        if context:
            logging.error(f"Context: {context}")
        logging.exception("Stack trace:")