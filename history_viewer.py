"""
処理履歴ビューワー
"""
import customtkinter as ctk
from tkinter import messagebox, filedialog
from history_manager import HistoryManager, HistoryEntry
from datetime import datetime
from pathlib import Path
from typing import List, Optional
import json


class HistoryViewer(ctk.CTkFrame):
    """履歴ビューワーウィジェット"""
    
    def __init__(self, master, history_manager: HistoryManager, **kwargs):
        super().__init__(master, **kwargs)
        
        self.history_manager = history_manager
        self.current_entries: List[HistoryEntry] = []
        self.selected_entry: Optional[HistoryEntry] = None
        
        self._setup_ui()
        self._load_history()
        
    def _setup_ui(self):
        """UIをセットアップ"""
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        
        # ツールバー
        toolbar = ctk.CTkFrame(self)
        toolbar.grid(row=0, column=0, sticky="ew", padx=5, pady=5)
        toolbar.grid_columnconfigure(3, weight=1)
        
        # 検索
        ctk.CTkLabel(toolbar, text="検索:").grid(row=0, column=0, padx=5)
        self.search_entry = ctk.CTkEntry(toolbar, width=200)
        self.search_entry.grid(row=0, column=1, padx=5)
        self.search_entry.bind("<Return>", lambda e: self._load_history())
        
        ctk.CTkButton(
            toolbar,
            text="検索",
            command=self._load_history,
            width=60
        ).grid(row=0, column=2, padx=5)
        
        # フィルター
        self.success_only_var = ctk.BooleanVar(value=False)
        ctk.CTkCheckBox(
            toolbar,
            text="成功のみ",
            variable=self.success_only_var,
            command=self._load_history
        ).grid(row=0, column=4, padx=5)
        
        # エクスポートボタン
        export_menu = ctk.CTkOptionMenu(
            toolbar,
            values=["CSV", "JSON"],
            command=self._export_history,
            width=100
        )
        export_menu.set("エクスポート")
        export_menu.grid(row=0, column=5, padx=5)
        
        # 更新ボタン
        ctk.CTkButton(
            toolbar,
            text="更新",
            command=self._load_history,
            width=60
        ).grid(row=0, column=6, padx=5)
        
        # リストフレーム
        list_frame = ctk.CTkFrame(self)
        list_frame.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)
        list_frame.grid_columnconfigure(0, weight=1)
        list_frame.grid_rowconfigure(0, weight=1)
        
        # 履歴リスト（スクロール可能）
        self.history_list = ctk.CTkScrollableFrame(list_frame)
        self.history_list.grid(row=0, column=0, sticky="nsew")
        self.history_list.grid_columnconfigure(0, weight=1)
        
        # 詳細パネル
        self.detail_frame = ctk.CTkFrame(self, height=150)
        self.detail_frame.grid(row=2, column=0, sticky="ew", padx=5, pady=5)
        self.detail_frame.grid_columnconfigure(1, weight=1)
        self.detail_frame.grid_propagate(False)
        
        self._create_detail_panel()
        
    def _create_detail_panel(self):
        """詳細パネルを作成"""
        # タイトル
        title_label = ctk.CTkLabel(
            self.detail_frame,
            text="詳細情報",
            font=("", 14, "bold")
        )
        title_label.grid(row=0, column=0, columnspan=2, padx=10, pady=5, sticky="w")
        
        # 詳細情報ラベル
        self.detail_labels = {}
        labels = [
            ("source_path", "ソース:"),
            ("dest_path", "出力:"),
            ("dimensions", "サイズ変更:"),
            ("compression", "圧縮:"),
            ("processing_time", "処理時間:"),
            ("timestamp", "処理日時:")
        ]
        
        for i, (key, text) in enumerate(labels):
            row = i + 1
            ctk.CTkLabel(self.detail_frame, text=text).grid(
                row=row, column=0, padx=10, pady=2, sticky="w"
            )
            label = ctk.CTkLabel(self.detail_frame, text="", anchor="w")
            label.grid(row=row, column=1, padx=10, pady=2, sticky="ew")
            self.detail_labels[key] = label
            
    def _load_history(self):
        """履歴を読み込む"""
        search_term = self.search_entry.get()
        success_only = self.success_only_var.get()
        
        self.current_entries = self.history_manager.get_entries(
            limit=500,
            success_only=success_only,
            search_term=search_term if search_term else None
        )
        
        self._display_history()
        
    def _display_history(self):
        """履歴を表示"""
        # 既存のアイテムをクリア
        for widget in self.history_list.winfo_children():
            widget.destroy()
            
        if not self.current_entries:
            no_data_label = ctk.CTkLabel(
                self.history_list,
                text="履歴データがありません",
                font=("", 14)
            )
            no_data_label.grid(row=0, column=0, pady=50)
            return
            
        # ヘッダー
        header_frame = ctk.CTkFrame(self.history_list, fg_color="gray30")
        header_frame.grid(row=0, column=0, sticky="ew", pady=(0, 5))
        header_frame.grid_columnconfigure(1, weight=1)
        
        headers = [
            ("状態", 60),
            ("ファイル名", 200),
            ("圧縮率", 80),
            ("処理日時", 150),
            ("アクション", 100)
        ]
        
        for i, (text, width) in enumerate(headers):
            label = ctk.CTkLabel(
                header_frame,
                text=text,
                font=("", 12, "bold"),
                width=width
            )
            label.grid(row=0, column=i, padx=5, pady=5, sticky="w")
            
        # エントリー
        for i, entry in enumerate(self.current_entries):
            self._create_history_item(entry, i + 1)
            
    def _create_history_item(self, entry: HistoryEntry, row: int):
        """履歴アイテムを作成"""
        # 背景色を交互に変更
        bg_color = "gray20" if row % 2 == 0 else "transparent"
        
        item_frame = ctk.CTkFrame(self.history_list, fg_color=bg_color)
        item_frame.grid(row=row, column=0, sticky="ew", pady=1)
        item_frame.grid_columnconfigure(1, weight=1)
        
        # クリックイベント
        item_frame.bind("<Button-1>", lambda e, entry=entry: self._select_entry(entry))
        
        # 状態
        status_text = "✅" if entry.success else "❌"
        status_label = ctk.CTkLabel(item_frame, text=status_text, width=60)
        status_label.grid(row=0, column=0, padx=5, pady=5)
        status_label.bind("<Button-1>", lambda e, entry=entry: self._select_entry(entry))
        
        # ファイル名
        filename = Path(entry.source_path).name
        file_label = ctk.CTkLabel(
            item_frame,
            text=filename,
            width=200,
            anchor="w"
        )
        file_label.grid(row=0, column=1, padx=5, pady=5, sticky="w")
        file_label.bind("<Button-1>", lambda e, entry=entry: self._select_entry(entry))
        
        # 圧縮率
        compression_text = f"{entry.compression_ratio:.1f}%"
        compression_label = ctk.CTkLabel(
            item_frame,
            text=compression_text,
            width=80
        )
        compression_label.grid(row=0, column=2, padx=5, pady=5)
        compression_label.bind("<Button-1>", lambda e, entry=entry: self._select_entry(entry))
        
        # 処理日時
        timestamp = datetime.fromisoformat(entry.timestamp)
        time_text = timestamp.strftime("%Y/%m/%d %H:%M")
        time_label = ctk.CTkLabel(
            item_frame,
            text=time_text,
            width=150
        )
        time_label.grid(row=0, column=3, padx=5, pady=5)
        time_label.bind("<Button-1>", lambda e, entry=entry: self._select_entry(entry))
        
        # アクションボタン
        action_frame = ctk.CTkFrame(item_frame, fg_color="transparent")
        action_frame.grid(row=0, column=4, padx=5, pady=5)
        
        if entry.success and Path(entry.dest_path).exists():
            ctk.CTkButton(
                action_frame,
                text="再処理",
                command=lambda e=entry: self._reprocess_entry(e),
                width=80,
                height=24
            ).pack()
            
    def _select_entry(self, entry: HistoryEntry):
        """エントリーを選択"""
        self.selected_entry = entry
        self._update_detail_panel()
        
    def _update_detail_panel(self):
        """詳細パネルを更新"""
        if not self.selected_entry:
            return
            
        entry = self.selected_entry
        
        # ソースパス
        self.detail_labels["source_path"].configure(
            text=entry.source_path
        )
        
        # 出力パス
        self.detail_labels["dest_path"].configure(
            text=entry.dest_path
        )
        
        # サイズ変更
        self.detail_labels["dimensions"].configure(
            text=f"{entry.source_dimensions} → {entry.dest_dimensions}"
        )
        
        # 圧縮
        size_before = self._format_size(entry.source_size)
        size_after = self._format_size(entry.dest_size)
        self.detail_labels["compression"].configure(
            text=f"{size_before} → {size_after} ({entry.compression_ratio:.1f}%削減)"
        )
        
        # 処理時間
        self.detail_labels["processing_time"].configure(
            text=f"{entry.processing_time:.2f}秒"
        )
        
        # タイムスタンプ
        timestamp = datetime.fromisoformat(entry.timestamp)
        self.detail_labels["timestamp"].configure(
            text=timestamp.strftime("%Y年%m月%d日 %H:%M:%S")
        )
        
    def _format_size(self, size_bytes: int) -> str:
        """サイズをフォーマット"""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.1f} TB"
        
    def _reprocess_entry(self, entry: HistoryEntry):
        """エントリーを再処理"""
        # 設定を取得
        settings = entry.get_settings_dict()
        
        # 親ウィジェットのメソッドを呼び出し（実装は親側で）
        if hasattr(self.master, 'reprocess_from_history'):
            self.master.reprocess_from_history(entry.source_path, settings)
            
    def _export_history(self, format: str):
        """履歴をエクスポート"""
        if format == "エクスポート":
            return
            
        if format == "CSV":
            filepath = filedialog.asksaveasfilename(
                title="履歴をCSVでエクスポート",
                defaultextension=".csv",
                filetypes=[("CSVファイル", "*.csv")]
            )
            
            if filepath:
                if self.history_manager.export_to_csv(Path(filepath), self.current_entries):
                    messagebox.showinfo("成功", "履歴をCSVでエクスポートしました")
                else:
                    messagebox.showerror("エラー", "エクスポートに失敗しました")
                    
        elif format == "JSON":
            filepath = filedialog.asksaveasfilename(
                title="履歴をJSONでエクスポート",
                defaultextension=".json",
                filetypes=[("JSONファイル", "*.json")]
            )
            
            if filepath:
                if self.history_manager.export_to_json(Path(filepath), self.current_entries):
                    messagebox.showinfo("成功", "履歴をJSONでエクスポートしました")
                else:
                    messagebox.showerror("エラー", "エクスポートに失敗しました")