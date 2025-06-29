"""
ViewModelの単体テスト
"""
import unittest
from pathlib import Path
import sys
import tempfile
import shutil

# プロジェクトルートをPythonパスに追加
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from karukuresize.gui.view_models.resize_view_model import ResizeViewModel
from karukuresize.gui.view_models.preview_view_model import PreviewViewModel
from karukuresize.gui.view_models.history_view_model import HistoryViewModel
from karukuresize.gui.view_models.statistics_view_model import StatisticsViewModel
from karukuresize.models.resize_settings import ResizeSettings
from karukuresize.services.image_service import ImageService
from karukuresize.services.history_service import HistoryService


class TestResizeViewModel(unittest.TestCase):
    """ResizeViewModelのテスト"""
    
    def setUp(self):
        """テストのセットアップ"""
        self.view_model = ResizeViewModel()
        self.view_model.initialize()
        
        # テスト用の一時ディレクトリ
        self.test_dir = tempfile.mkdtemp()
        self.test_output_dir = Path(self.test_dir) / "output"
        self.test_output_dir.mkdir()
    
    def tearDown(self):
        """テストのクリーンアップ"""
        self.view_model.cleanup()
        shutil.rmtree(self.test_dir)
    
    def test_initialization(self):
        """初期化のテスト"""
        self.assertTrue(self.view_model.is_initialized)
        self.assertEqual(self.view_model.processing_mode, "single")
        self.assertEqual(self.view_model.resize_mode, "longest_side")
        self.assertEqual(self.view_model.quality, 85)
    
    def test_property_changes(self):
        """プロパティ変更の通知テスト"""
        # コールバックが呼ばれたかを追跡
        called = {"count": 0, "value": None}
        
        def on_quality_changed(value):
            called["count"] += 1
            called["value"] = value
        
        # プロパティ変更を監視
        self.view_model.bind("quality", on_quality_changed)
        
        # 品質を変更
        self.view_model.quality = 90
        
        # コールバックが呼ばれたことを確認
        self.assertEqual(called["count"], 1)
        self.assertEqual(called["value"], 90)
        self.assertEqual(self.view_model.quality, 90)
    
    def test_validation(self):
        """バリデーションのテスト"""
        # 無効な入力パス
        self.view_model.input_path = "/nonexistent/file.jpg"
        self.assertFalse(self.view_model.validate())
        self.assertNotEqual(self.view_model.error_message, "")
        
        # 有効な設定
        self.view_model.input_path = __file__  # このテストファイル自体を使用
        self.view_model.output_directory = str(self.test_output_dir)
        self.assertTrue(self.view_model.validate())
        self.assertEqual(self.view_model.error_message, "")
    
    def test_settings_update(self):
        """設定更新のテスト"""
        # 初期値を確認
        initial_settings = self.view_model._get_current_settings()
        self.assertEqual(initial_settings.resize_mode, "longest_side")
        
        # リサイズモードを変更
        self.view_model.resize_mode = "width"
        
        # 設定が更新されたことを確認
        updated_settings = self.view_model._get_current_settings()
        self.assertEqual(updated_settings.resize_mode, "width")
    
    def test_preset_application(self):
        """プリセット適用のテスト"""
        preset_data = {
            "resize_mode": "percentage",
            "resize_value": 50,
            "quality": 70,
            "output_format": "jpeg"
        }
        
        self.view_model.apply_preset(preset_data)
        
        self.assertEqual(self.view_model.resize_mode, "percentage")
        self.assertEqual(self.view_model.resize_value, 50)
        self.assertEqual(self.view_model.quality, 70)
        self.assertEqual(self.view_model.output_format, "jpeg")


class TestPreviewViewModel(unittest.TestCase):
    """PreviewViewModelのテスト"""
    
    def setUp(self):
        """テストのセットアップ"""
        self.view_model = PreviewViewModel()
        self.view_model.initialize()
    
    def tearDown(self):
        """テストのクリーンアップ"""
        self.view_model.cleanup()
    
    def test_zoom_functionality(self):
        """ズーム機能のテスト"""
        # 初期ズームレベル
        self.assertEqual(self.view_model.zoom_level, 1.0)
        
        # ズームイン
        self.view_model.zoom_in()
        self.assertEqual(self.view_model.zoom_level, 1.5)
        
        # ズームアウト
        self.view_model.zoom_out()
        self.assertEqual(self.view_model.zoom_level, 1.0)
        
        # リセット
        self.view_model.zoom_level = 2.0
        self.view_model.reset_zoom()
        self.assertEqual(self.view_model.zoom_level, 1.0)
    
    def test_zoom_limits(self):
        """ズーム制限のテスト"""
        # 最大値を超える設定
        self.view_model.zoom_level = 5.0
        self.assertEqual(self.view_model.zoom_level, 4.0)
        
        # 最小値を下回る設定
        self.view_model.zoom_level = 0.05
        self.assertEqual(self.view_model.zoom_level, 0.1)


class TestHistoryViewModel(unittest.TestCase):
    """HistoryViewModelのテスト"""
    
    def setUp(self):
        """テストのセットアップ"""
        # テスト用の履歴サービス
        self.test_db = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        self.history_service = HistoryService(self.test_db.name)
        
        # ViewModelを作成
        self.view_model = HistoryViewModel(self.history_service.history_manager)
        self.view_model.initialize()
        
        # テストデータを追加
        self._add_test_data()
    
    def tearDown(self):
        """テストのクリーンアップ"""
        self.view_model.cleanup()
        Path(self.test_db.name).unlink()
    
    def _add_test_data(self):
        """テストデータを追加"""
        for i in range(5):
            self.history_service.add_processing_result(
                source_path=f"/test/image{i}.jpg",
                output_path=f"/test/output{i}.jpg",
                success=i % 2 == 0,  # 偶数は成功
                settings={"resize_mode": "width", "resize_value": 800},
                original_size=1000000,
                output_size=500000,
                processing_time=1.5
            )
    
    def test_load_history(self):
        """履歴読み込みのテスト"""
        # 履歴を読み込む
        self.view_model.load_history()
        
        # エントリ数を確認
        self.assertEqual(len(self.view_model.entries), 5)
        self.assertEqual(self.view_model.total_count, 5)
        self.assertEqual(self.view_model.success_count, 3)  # 0, 2, 4が成功
    
    def test_filter_success_only(self):
        """成功フィルタのテスト"""
        # 成功のみフィルタを有効化
        self.view_model.filter_success_only = True
        self.view_model.load_history()
        
        # 成功エントリのみになることを確認
        self.assertEqual(len(self.view_model.entries), 3)
        for entry in self.view_model.entries:
            self.assertTrue(entry.success)
    
    def test_search_functionality(self):
        """検索機能のテスト"""
        # 検索クエリを設定
        self.view_model.search_query = "image2"
        self.view_model.load_history()
        
        # 検索結果を確認
        self.assertEqual(len(self.view_model.entries), 1)
        self.assertIn("image2", self.view_model.entries[0].source_path)
    
    def test_statistics_calculation(self):
        """統計計算のテスト"""
        stats = self.view_model.get_statistics()
        
        self.assertEqual(stats["total_count"], 5)
        self.assertEqual(stats["success_count"], 3)
        self.assertEqual(stats["failure_count"], 2)
        self.assertEqual(stats["total_size_saved"], 1500000)  # 3成功 × 500KB


class TestStatisticsViewModel(unittest.TestCase):
    """StatisticsViewModelのテスト"""
    
    def setUp(self):
        """テストのセットアップ"""
        # テスト用の履歴サービス
        self.test_db = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        self.history_service = HistoryService(self.test_db.name)
        
        # ViewModelを作成
        self.view_model = StatisticsViewModel(self.history_service)
        
        # テストデータを追加
        self._add_test_data()
        
        # 初期化
        self.view_model.initialize()
    
    def tearDown(self):
        """テストのクリーンアップ"""
        self.view_model.cleanup()
        Path(self.test_db.name).unlink()
    
    def _add_test_data(self):
        """テストデータを追加"""
        # 異なるリサイズモードとフォーマットでデータを追加
        modes = ["width", "height", "longest_side", "width", "longest_side"]
        formats = ["jpeg", "png", "webp", "jpeg", "jpeg"]
        
        for i in range(5):
            self.history_service.add_processing_result(
                source_path=f"/test/image{i}.jpg",
                output_path=f"/test/output{i}.jpg",
                success=True,
                settings={
                    "resize_mode": modes[i],
                    "output_format": formats[i]
                },
                original_size=1000000,
                output_size=600000,
                processing_time=1.0
            )
    
    def test_period_filtering(self):
        """期間フィルタのテスト"""
        # 週間フィルタ（デフォルト）
        self.assertEqual(self.view_model.period_filter, "week")
        self.view_model.load_statistics()
        
        # 統計データが読み込まれたことを確認
        self.assertEqual(self.view_model.total_processed, 5)
        self.assertEqual(self.view_model.success_rate, 100.0)
    
    def test_distribution_calculation(self):
        """分布計算のテスト"""
        self.view_model.load_statistics()
        
        # リサイズモードの分布
        resize_modes = self.view_model.resize_mode_distribution
        self.assertEqual(resize_modes.get("width", 0), 2)
        self.assertEqual(resize_modes.get("longest_side", 0), 2)
        self.assertEqual(resize_modes.get("height", 0), 1)
        
        # 出力フォーマットの分布
        formats = self.view_model.output_format_distribution
        self.assertEqual(formats.get("jpeg", 0), 3)
        self.assertEqual(formats.get("png", 0), 1)
        self.assertEqual(formats.get("webp", 0), 1)
    
    def test_size_reduction_calculation(self):
        """サイズ削減計算のテスト"""
        self.view_model.load_statistics()
        
        # 総削減サイズ
        total_saved = self.view_model.total_size_saved
        self.assertEqual(total_saved, 2000000)  # 5 × 400KB
        
        # 平均削減率
        avg_reduction = self.view_model.average_size_reduction
        self.assertEqual(avg_reduction, 40.0)  # 40%削減


if __name__ == "__main__":
    unittest.main()