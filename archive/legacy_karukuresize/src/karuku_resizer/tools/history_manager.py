"""
処理履歴管理のモジュール
"""
import sqlite3
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
import json
import threading
from contextlib import contextmanager

@dataclass
class HistoryEntry:
    """履歴エントリ"""
    id: Optional[int] = None
    timestamp: str = ""
    source_path: str = ""
    dest_path: str = ""
    source_size: int = 0  # bytes
    dest_size: int = 0    # bytes
    source_dimensions: str = ""  # "width x height"
    dest_dimensions: str = ""    # "width x height"
    settings: str = "{}"  # JSON string
    success: bool = True
    error_message: str = ""
    processing_time: float = 0.0  # seconds
    
    @property
    def compression_ratio(self) -> float:
        """圧縮率を計算"""
        if self.source_size > 0:
            return ((self.source_size - self.dest_size) / self.source_size) * 100
        return 0.0
        
    @property
    def size_reduction(self) -> int:
        """サイズ削減量"""
        return self.source_size - self.dest_size
        
    def get_settings_dict(self) -> Dict[str, Any]:
        """設定を辞書として取得"""
        try:
            return json.loads(self.settings)
        except Exception:
            return {}


class HistoryManager:
    """履歴マネージャー"""
    
    def __init__(self, db_path: Optional[Path] = None):
        """
        Args:
            db_path: データベースファイルのパス
        """
        self.db_path = db_path or self._get_default_db_path()
        self._lock = threading.Lock()
        self._init_database()
        
    def _get_default_db_path(self) -> Path:
        """デフォルトのデータベースパスを取得"""
        import os
        if os.name == 'nt':  # Windows
            app_data = os.environ.get('APPDATA', '')
            if app_data:
                base_dir = Path(app_data) / 'KarukuResize'
            else:
                base_dir = Path.home() / '.karukuresize'
        else:  # Unix/Linux/Mac
            config_home = os.environ.get('XDG_CONFIG_HOME', '')
            if config_home:
                base_dir = Path(config_home) / 'karukuresize'
            else:
                base_dir = Path.home() / '.config' / 'karukuresize'
                
        base_dir.mkdir(parents=True, exist_ok=True)
        return base_dir / 'history.db'
        
    @contextmanager
    def _get_connection(self):
        """データベース接続を取得"""
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()
            
    def _init_database(self):
        """データベースを初期化"""
        with self._lock:
            with self._get_connection() as conn:
                conn.execute('''
                    CREATE TABLE IF NOT EXISTS history (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        timestamp TEXT NOT NULL,
                        source_path TEXT NOT NULL,
                        dest_path TEXT NOT NULL,
                        source_size INTEGER NOT NULL,
                        dest_size INTEGER NOT NULL,
                        source_dimensions TEXT NOT NULL,
                        dest_dimensions TEXT NOT NULL,
                        settings TEXT NOT NULL,
                        success BOOLEAN NOT NULL,
                        error_message TEXT,
                        processing_time REAL NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                # インデックスを作成
                conn.execute('''
                    CREATE INDEX IF NOT EXISTS idx_timestamp 
                    ON history(timestamp DESC)
                ''')
                conn.execute('''
                    CREATE INDEX IF NOT EXISTS idx_source_path 
                    ON history(source_path)
                ''')
                conn.execute('''
                    CREATE INDEX IF NOT EXISTS idx_success 
                    ON history(success)
                ''')
                
                conn.commit()
                
    def add_entry(
        self,
        source_path: Path,
        dest_path: Path,
        source_size: int,
        dest_size: int,
        source_dimensions: Tuple[int, int],
        dest_dimensions: Tuple[int, int],
        settings: Dict[str, Any],
        success: bool = True,
        error_message: str = "",
        processing_time: float = 0.0
    ) -> Optional[int]:
        """履歴エントリを追加"""
        with self._lock:
            with self._get_connection() as conn:
                try:
                    cursor = conn.execute('''
                        INSERT INTO history (
                            timestamp, source_path, dest_path,
                            source_size, dest_size,
                            source_dimensions, dest_dimensions,
                            settings, success, error_message, processing_time
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        datetime.now().isoformat(),
                        str(source_path),
                        str(dest_path),
                        source_size,
                        dest_size,
                        f"{source_dimensions[0]}x{source_dimensions[1]}",
                        f"{dest_dimensions[0]}x{dest_dimensions[1]}",
                        json.dumps(settings, ensure_ascii=False),
                        success,
                        error_message,
                        processing_time
                    ))
                    conn.commit()
                    return cursor.lastrowid
                except Exception as e:
                    print(f"履歴追加エラー: {e}")
                    return None
                    
    def get_entries(
        self,
        limit: int = 100,
        offset: int = 0,
        success_only: bool = False,
        search_term: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[HistoryEntry]:
        """履歴エントリを取得"""
        with self._lock:
            with self._get_connection() as conn:
                query = "SELECT * FROM history WHERE 1=1"
                params = []
                
                if success_only:
                    query += " AND success = 1"
                    
                if search_term:
                    query += " AND (source_path LIKE ? OR dest_path LIKE ?)"
                    params.extend([f"%{search_term}%", f"%{search_term}%"])
                    
                if start_date:
                    query += " AND timestamp >= ?"
                    params.append(start_date.isoformat())
                    
                if end_date:
                    query += " AND timestamp <= ?"
                    params.append(end_date.isoformat())
                    
                query += " ORDER BY timestamp DESC LIMIT ? OFFSET ?"
                params.extend([limit, offset])
                
                cursor = conn.execute(query, params)
                entries = []
                
                for row in cursor:
                    entries.append(HistoryEntry(
                        id=row['id'],
                        timestamp=row['timestamp'],
                        source_path=row['source_path'],
                        dest_path=row['dest_path'],
                        source_size=row['source_size'],
                        dest_size=row['dest_size'],
                        source_dimensions=row['source_dimensions'],
                        dest_dimensions=row['dest_dimensions'],
                        settings=row['settings'],
                        success=bool(row['success']),
                        error_message=row['error_message'] or "",
                        processing_time=row['processing_time']
                    ))
                    
                return entries
                
    def get_entry_by_id(self, entry_id: int) -> Optional[HistoryEntry]:
        """IDで履歴エントリを取得"""
        with self._lock:
            with self._get_connection() as conn:
                cursor = conn.execute(
                    "SELECT * FROM history WHERE id = ?",
                    (entry_id,)
                )
                row = cursor.fetchone()
                
                if row:
                    return HistoryEntry(
                        id=row['id'],
                        timestamp=row['timestamp'],
                        source_path=row['source_path'],
                        dest_path=row['dest_path'],
                        source_size=row['source_size'],
                        dest_size=row['dest_size'],
                        source_dimensions=row['source_dimensions'],
                        dest_dimensions=row['dest_dimensions'],
                        settings=row['settings'],
                        success=bool(row['success']),
                        error_message=row['error_message'] or "",
                        processing_time=row['processing_time']
                    )
                return None
                
    def get_statistics(self, days: int = 30) -> Dict[str, Any]:
        """統計情報を取得"""
        with self._lock:
            with self._get_connection() as conn:
                start_date = (datetime.now() - timedelta(days=days)).isoformat()
                
                # 基本統計
                cursor = conn.execute('''
                    SELECT 
                        COUNT(*) as total_count,
                        SUM(CASE WHEN success = 1 THEN 1 ELSE 0 END) as success_count,
                        SUM(source_size) as total_source_size,
                        SUM(dest_size) as total_dest_size,
                        AVG(processing_time) as avg_processing_time
                    FROM history
                    WHERE timestamp >= ?
                ''', (start_date,))
                
                row = cursor.fetchone()
                
                stats = {
                    'total_count': row['total_count'] or 0,
                    'success_count': row['success_count'] or 0,
                    'failure_count': (row['total_count'] or 0) - (row['success_count'] or 0),
                    'total_source_size': row['total_source_size'] or 0,
                    'total_dest_size': row['total_dest_size'] or 0,
                    'total_saved_size': (row['total_source_size'] or 0) - (row['total_dest_size'] or 0),
                    'avg_processing_time': row['avg_processing_time'] or 0,
                    'success_rate': 0.0
                }
                
                if stats['total_count'] > 0:
                    stats['success_rate'] = (stats['success_count'] / stats['total_count']) * 100
                    
                # 日別統計
                cursor = conn.execute('''
                    SELECT 
                        DATE(timestamp) as date,
                        COUNT(*) as count,
                        SUM(source_size - dest_size) as saved_size
                    FROM history
                    WHERE timestamp >= ? AND success = 1
                    GROUP BY DATE(timestamp)
                    ORDER BY date
                ''', (start_date,))
                
                daily_stats = []
                for row in cursor:
                    daily_stats.append({
                        'date': row['date'],
                        'count': row['count'],
                        'saved_size': row['saved_size'] or 0
                    })
                    
                stats['daily_stats'] = daily_stats
                
                return stats
                
    def delete_old_entries(self, days: int = 90) -> int:
        """古い履歴を削除"""
        with self._lock:
            with self._get_connection() as conn:
                cutoff_date = (datetime.now() - timedelta(days=days)).isoformat()
                cursor = conn.execute(
                    "DELETE FROM history WHERE timestamp < ?",
                    (cutoff_date,)
                )
                conn.commit()
                return cursor.rowcount
                
    def clear_all(self) -> bool:
        """全履歴を削除"""
        with self._lock:
            with self._get_connection() as conn:
                try:
                    conn.execute("DELETE FROM history")
                    conn.commit()
                    return True
                except Exception as e:
                    print(f"履歴削除エラー: {e}")
                    return False
                    
    def export_to_csv(self, filepath: Path, entries: Optional[List[HistoryEntry]] = None) -> bool:
        """履歴をCSVにエクスポート"""
        try:
            import csv
            
            if entries is None:
                entries = self.get_entries(limit=10000)  # 最大10000件
                
            with open(filepath, 'w', newline='', encoding='utf-8-sig') as f:
                writer = csv.writer(f)
                
                # ヘッダー
                writer.writerow([
                    '処理日時', 'ソースファイル', '出力ファイル',
                    'ソースサイズ', '出力サイズ', '圧縮率(%)',
                    'ソース解像度', '出力解像度', '処理時間(秒)',
                    '成功', 'エラーメッセージ'
                ])
                
                # データ
                for entry in entries:
                    writer.writerow([
                        entry.timestamp,
                        entry.source_path,
                        entry.dest_path,
                        entry.source_size,
                        entry.dest_size,
                        f"{entry.compression_ratio:.1f}",
                        entry.source_dimensions,
                        entry.dest_dimensions,
                        f"{entry.processing_time:.2f}",
                        '成功' if entry.success else '失敗',
                        entry.error_message
                    ])
                    
            return True
            
        except Exception as e:
            print(f"CSVエクスポートエラー: {e}")
            return False
            
    def export_to_json(self, filepath: Path, entries: Optional[List[HistoryEntry]] = None) -> bool:
        """履歴をJSONにエクスポート"""
        try:
            if entries is None:
                entries = self.get_entries(limit=10000)  # 最大10000件
                
            data = {
                'export_date': datetime.now().isoformat(),
                'total_entries': len(entries),
                'entries': [asdict(entry) for entry in entries]
            }
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
                
            return True
            
        except Exception as e:
            print(f"JSONエクスポートエラー: {e}")
            return False
