"""
メインウィンドウ
"""
import customtkinter as ctk
from pathlib import Path
import sys

# プロジェクトルートをPythonパスに追加
project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from .views.resize_tab_view import ResizeTabView
from .view_models.resize_view_model import ResizeViewModel
from ..services.image_service import ImageService
from .utils.constants import WINDOW, THEME, FONT


class MainWindow(ctk.CTk):
    """メインウィンドウクラス"""
    
    def __init__(self):
        super().__init__()
        
        # ウィンドウ設定
        self.title(WINDOW.TITLE)
        self.geometry(f"{WINDOW.DEFAULT_WIDTH}x{WINDOW.DEFAULT_HEIGHT}")
        self.minsize(WINDOW.MIN_WIDTH, WINDOW.MIN_HEIGHT)
        
        # テーマ設定
        self.configure(fg_color=THEME.BG_PRIMARY)
        
        # サービスの初期化
        self.image_service = ImageService()
        
        # ViewModelの初期化
        self.resize_view_model = ResizeViewModel(self.image_service)
        
        # UIの構築
        self._create_widgets()
        
        # ViewModelの初期化
        self.resize_view_model.initialize()
        
        # ウィンドウを中央に配置
        self._center_window()
        
        # ウィンドウクローズイベント
        self.protocol("WM_DELETE_WINDOW", self.on_closing)
    
    def _create_widgets(self):
        """ウィジェットを作成"""
        # メインコンテナ
        main_container = ctk.CTkFrame(self, fg_color="transparent")
        main_container.pack(fill="both", expand=True)
        
        # タブビュー
        self.tab_view = ctk.CTkTabview(
            main_container,
            corner_radius=10
        )
        self.tab_view.pack(fill="both", expand=True, padx=20, pady=20)
        
        # タブのフォント設定を試みる
        self._configure_tab_font()
        
        # リサイズタブ
        resize_tab = self.tab_view.add("画像リサイズ")
        self.resize_view = ResizeTabView(resize_tab, self.resize_view_model)
        self.resize_view.pack(fill="both", expand=True)
        
        # 他のタブ（将来の拡張用）
        # プレビュータブ、履歴タブ、統計タブなどを追加可能
    
    def _configure_tab_font(self):
        """タブのフォント設定"""
        try:
            # CustomTkinterの内部実装に依存する部分
            if hasattr(self.tab_view, "_segmented_button") and self.tab_view._segmented_button:
                self.tab_view._segmented_button.configure(
                    font=ctk.CTkFont(size=FONT.SIZE_HEADING, weight=FONT.WEIGHT_BOLD),
                    text_color=(THEME.TEXT_PRIMARY, "#FFFFFF"),
                    fg_color=THEME.BG_SECONDARY,
                    selected_color=THEME.ACCENT,
                    selected_hover_color=THEME.ACCENT_HOVER,
                    unselected_hover_color="#DEE2E6"
                )
        except Exception as e:
            print(f"タブフォント設定エラー: {e}")
    
    def _center_window(self):
        """ウィンドウを中央に配置"""
        self.update_idletasks()
        width = self.winfo_width()
        height = self.winfo_height()
        x = (self.winfo_screenwidth() // 2) - (width // 2)
        y = (self.winfo_screenheight() // 2) - (height // 2)
        self.geometry(f"{width}x{height}+{x}+{y}")
    
    def on_closing(self):
        """ウィンドウを閉じるとき"""
        # クリーンアップ
        if hasattr(self, 'resize_view'):
            self.resize_view.cleanup()
        self.destroy()


def main():
    """アプリケーションのエントリーポイント"""
    # テーマ設定
    ctk.set_appearance_mode("light")
    
    # カスタムテーマファイルが存在する場合は使用
    theme_path = Path(__file__).parent.parent.parent / "karuku_light_theme.json"
    if theme_path.exists():
        ctk.set_default_color_theme(str(theme_path))
    else:
        ctk.set_default_color_theme("blue")
    
    # アプリケーション起動
    app = MainWindow()
    app.mainloop()


if __name__ == "__main__":
    main()