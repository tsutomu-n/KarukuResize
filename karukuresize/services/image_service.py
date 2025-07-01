"""
画像処理サービス
"""
import sys
from pathlib import Path
from typing import Optional, List, Callable
import time

# プロジェクトルートをPythonパスに追加
project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from resize_core import resize_and_compress_image
from karukuresize.models.resize_settings import ResizeSettings, ProcessingResult


class ImageService:
    """画像処理を行うサービスクラス"""
    
    def __init__(self):
        self._cancel_requested = False
    
    def process_image(
        self,
        source_path: str,
        output_directory: str,
        settings: ResizeSettings,
        progress_callback: Optional[Callable[[float], None]] = None
    ) -> ProcessingResult:
        """単一の画像を処理"""
        start_time = time.time()
        source_path = Path(source_path)
        output_dir = Path(output_directory)
        
        # 入力検証
        if not source_path.exists():
            return ProcessingResult(
                success=False,
                source_path=source_path,
                error_message="入力ファイルが存在しません"
            )
        
        if not output_dir.exists():
            return ProcessingResult(
                success=False,
                source_path=source_path,
                error_message="出力ディレクトリが存在しません"
            )
        
        try:
            # 元のファイルサイズを取得
            original_size = source_path.stat().st_size
            
            # 出力ファイル名を生成
            output_path = self._generate_output_path(
                source_path, output_dir, settings
            )
            
            # 既存ファイルチェック
            if output_path.exists() and not settings.overwrite:
                return ProcessingResult(
                    success=False,
                    source_path=source_path,
                    error_message="出力ファイルが既に存在します"
                )
            
            # resize_coreを使用して画像を処理
            # output_formatをformatパラメータに渡す
            format_param = "original"
            if settings.output_format != "original":
                format_param = settings.output_format
            
            result = resize_and_compress_image(
                source_path=str(source_path),
                dest_path=str(output_path),
                resize_mode=settings.resize_mode,
                resize_value=settings.resize_value,
                quality=settings.quality,
                format=format_param,
                exif_handling="keep" if settings.preserve_metadata else "remove",
                lanczos_filter=settings.lanczos_filter,
                progressive=settings.progressive,
                optimize=settings.optimize,
                webp_lossless=settings.webp_lossless
            )
            
            # 戻り値を処理（メモリベースと互換性のため）
            if len(result) == 2:
                success, error_msg = result
            else:
                success = result[0] if len(result) > 0 else False
                error_msg = None
            
            if not success:
                return ProcessingResult(
                    success=False,
                    source_path=source_path,
                    error_message=error_msg if error_msg else "不明なエラー"
                )
            
            # 処理後のファイルサイズを取得
            output_size = output_path.stat().st_size if output_path.exists() else 0
            
            # 処理時間を計算
            processing_time = time.time() - start_time
            
            return ProcessingResult(
                success=True,
                source_path=source_path,
                output_path=output_path,
                processing_time=processing_time,
                original_size=original_size,
                output_size=output_size
            )
            
        except Exception as e:
            return ProcessingResult(
                success=False,
                source_path=source_path,
                error_message=str(e),
                processing_time=time.time() - start_time
            )
    
    def process_batch(
        self,
        source_directory: str,
        output_directory: str,
        settings: ResizeSettings,
        progress_callback: Optional[Callable[[int, int], None]] = None,
        result_callback: Optional[Callable[[ProcessingResult], None]] = None
    ) -> List[ProcessingResult]:
        """複数の画像を一括処理"""
        source_dir = Path(source_directory)
        results = []
        
        # 画像ファイルを収集
        image_files = self._collect_image_files(source_dir, settings)
        total_files = len(image_files)
        
        if total_files == 0:
            return results
        
        # 各ファイルを処理
        for index, image_file in enumerate(image_files):
            if self._cancel_requested:
                break
            
            # 進捗通知
            if progress_callback:
                progress_callback(index + 1, total_files)
            
            # 画像を処理
            result = self.process_image(
                str(image_file),
                output_directory,
                settings
            )
            
            results.append(result)
            
            # 結果通知
            if result_callback:
                result_callback(result)
        
        return results
    
    def cancel_processing(self):
        """処理をキャンセル"""
        self._cancel_requested = True
    
    def reset_cancel(self):
        """キャンセル状態をリセット"""
        self._cancel_requested = False
    
    def _generate_output_path(
        self,
        source_path: Path,
        output_dir: Path,
        settings: ResizeSettings
    ) -> Path:
        """出力ファイルパスを生成"""
        # ファイル名を構築
        stem = source_path.stem
        
        # プレフィックスとサフィックスを適用
        new_stem = f"{settings.prefix}{stem}{settings.suffix}"
        
        # 拡張子を決定
        if settings.output_format == "original":
            extension = source_path.suffix
        else:
            extension = f".{settings.output_format}"
        
        # 出力パスを構築
        output_path = output_dir / f"{new_stem}{extension}"
        
        return output_path
    
    def _collect_image_files(
        self,
        source_dir: Path,
        settings: ResizeSettings
    ) -> List[Path]:
        """指定ディレクトリから画像ファイルを収集"""
        image_files = []
        
        # サポートする拡張子
        if hasattr(settings, 'extensions'):
            extensions = settings.extensions
        else:
            extensions = {'.jpg', '.jpeg', '.png', '.webp', '.bmp', '.gif'}
        
        # 再帰的に検索するかどうか
        recursive = hasattr(settings, 'recursive') and settings.recursive
        
        if recursive:
            pattern = "**/*"
        else:
            pattern = "*"
        
        # ファイルを収集
        for file_path in source_dir.glob(pattern):
            if file_path.is_file() and file_path.suffix.lower() in extensions:
                image_files.append(file_path)
        
        # 最大ファイル数で制限
        if hasattr(settings, 'max_files'):
            image_files = image_files[:settings.max_files]
        
        return image_files