# GUI統合プラン - Phase 3

## 概要
Phase 3で作成した各モジュールをresize_images_gui.pyに統合するための計画書です。

## 主な変更点

### 1. インポートの追加
```python
from image_preview import ImagePreviewWidget, ComparisonPreviewWidget
from preset_manager import PresetManager, PresetData
from history_manager import HistoryManager
from statistics_viewer import StatisticsViewer, StatisticsDialog
from preset_dialog import PresetManagerDialog
from history_viewer import HistoryViewer
```

### 2. メニューバーの追加
```python
def _create_menu_bar(self):
    """メニューバーを作成"""
    self.menubar = tk.Menu(self)
    self.configure(menu=self.menubar)
    
    # ファイルメニュー
    file_menu = tk.Menu(self.menubar, tearoff=0)
    self.menubar.add_cascade(label="ファイル", menu=file_menu)
    file_menu.add_command(label="開く...", command=self.browse_input)
    file_menu.add_separator()
    file_menu.add_command(label="設定を保存", command=self.save_settings)
    file_menu.add_command(label="設定を読み込む", command=self.load_settings)
    file_menu.add_separator()
    file_menu.add_command(label="終了", command=self.on_window_close)
    
    # 編集メニュー
    edit_menu = tk.Menu(self.menubar, tearoff=0)
    self.menubar.add_cascade(label="編集", menu=edit_menu)
    edit_menu.add_command(label="プリセット管理...", command=self.open_preset_manager)
    
    # 表示メニュー
    view_menu = tk.Menu(self.menubar, tearoff=0)
    self.menubar.add_cascade(label="表示", menu=view_menu)
    view_menu.add_command(label="統計...", command=self.open_statistics)
    
    # ヘルプメニュー
    help_menu = tk.Menu(self.menubar, tearoff=0)
    self.menubar.add_cascade(label="ヘルプ", menu=help_menu)
    help_menu.add_command(label="使い方", command=self.show_help)
    help_menu.add_command(label="バージョン情報", command=self.show_about)
```

### 3. タブ構造の拡張
```python
# 既存のタブ
self.tab_resize = self.tab_view.add("画像リサイズ")

# 新しいタブ
self.tab_preview = self.tab_view.add("プレビュー")
self.tab_history = self.tab_view.add("履歴")
self.tab_stats = self.tab_view.add("統計")
```

### 4. プレビュータブの実装
```python
def _create_preview_tab(self):
    """プレビュータブを作成"""
    # 比較プレビューウィジェット
    self.comparison_preview = ComparisonPreviewWidget(self.tab_preview)
    self.comparison_preview.pack(fill="both", expand=True, padx=10, pady=10)
    
    # ファイル選択時に自動プレビュー
    self.comparison_preview.before_preview.on_image_loaded = self._on_preview_loaded
```

### 5. 履歴タブの実装
```python
def _create_history_tab(self):
    """履歴タブを作成"""
    self.history_viewer = HistoryViewer(
        self.tab_history,
        self.history_manager
    )
    self.history_viewer.pack(fill="both", expand=True, padx=10, pady=10)
```

### 6. 統計タブの実装
```python
def _create_stats_tab(self):
    """統計タブを作成"""
    self.stats_viewer = StatisticsViewer(self.tab_stats)
    self.stats_viewer.pack(fill="both", expand=True, padx=10, pady=10)
    
    # 初期データ読み込み
    self._update_statistics()
```

### 7. プリセット統合
```python
# リサイズタブにプリセット選択を追加
preset_frame = ctk.CTkFrame(self.resize_tab_content)
preset_frame.grid(...)

ctk.CTkLabel(preset_frame, text="プリセット:").pack(side="left")

self.preset_var = ctk.StringVar(value="カスタム")
self.preset_menu = ctk.CTkOptionMenu(
    preset_frame,
    variable=self.preset_var,
    values=["カスタム"] + self.preset_manager.get_preset_names(),
    command=self._on_preset_selected
)
self.preset_menu.pack(side="left", padx=5)

ctk.CTkButton(
    preset_frame,
    text="管理",
    command=self.open_preset_manager,
    width=60
).pack(side="left")
```

### 8. 履歴記録の統合
```python
def _execute_resize_in_thread(self, ...):
    """既存のリサイズ処理メソッドを拡張"""
    start_time = time.time()
    
    try:
        # 既存の処理...
        
        # 成功時に履歴を記録
        if success:
            processing_time = time.time() - start_time
            
            self.history_manager.add_entry(
                source_path=source_path,
                dest_path=dest_path,
                source_size=source_size,
                dest_size=dest_size,
                source_dimensions=(original_width, original_height),
                dest_dimensions=(new_width, new_height),
                settings={
                    'resize_mode': core_resize_mode,
                    'resize_value': resize_value,
                    'quality': quality,
                    # ... その他の設定
                },
                success=True,
                processing_time=processing_time
            )
            
            # 統計を更新
            self._update_statistics()
```

### 9. イベントハンドラ
```python
def _on_preset_selected(self, preset_name: str):
    """プリセット選択時"""
    if preset_name == "カスタム":
        return
        
    preset = self.preset_manager.get_preset(preset_name)
    if preset:
        self._apply_preset(preset)
        
def _apply_preset(self, preset: PresetData):
    """プリセットを適用"""
    # 各UIコンポーネントに値を設定
    self.resize_mode_var.set(preset.resize_mode)
    self.resize_value_entry.delete(0, "end")
    self.resize_value_entry.insert(0, str(preset.resize_value))
    # ... その他の設定

def reprocess_from_history(self, source_path: str, settings: dict):
    """履歴から再処理"""
    # ファイルパスと設定を適用
    self.input_entry.delete(0, "end")
    self.input_entry.insert(0, source_path)
    
    # 設定を適用
    # ...
    
    # プレビュータブに切り替え
    self.tab_view.set("プレビュー")
```

### 10. 初期化の更新
```python
def __init__(self):
    # 既存の初期化...
    
    # 新しいマネージャーを初期化
    self.preset_manager = PresetManager()
    self.preset_manager.load()
    
    self.history_manager = HistoryManager()
    
    # メニューバーを作成
    self._create_menu_bar()
    
    # 新しいタブを作成
    self._create_preview_tab()
    self._create_history_tab()
    self._create_stats_tab()
```

## 実装の優先順位

1. **高優先度**
   - メニューバーの追加
   - プリセット選択UI
   - 履歴記録機能

2. **中優先度**
   - プレビュータブ
   - 履歴タブ
   - 統計タブ

3. **低優先度**
   - 細かいUI調整
   - パフォーマンス最適化

## 注意事項

- 既存の機能を壊さないよう、段階的に実装
- 各タブは遅延読み込みでパフォーマンスを確保
- エラーハンドリングを適切に実装
- 日本語UIの一貫性を保つ