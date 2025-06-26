# karukuresize Squoosh機能拡張実装計画

[GoogleChromeLabs/squoosh \| DeepWiki](https://deepwiki.com/GoogleChromeLabs/squoosh)

## 概要

karukuresizeツールにGoogleChrome Labsの[Squoosh](https://github.com/GoogleChromeLabs/squoosh)で採用されている高度な画像圧縮機能を導入することで、より効率的な画像サイズ削減を実現する計画のだ。

## 拡張の目的

1. 現在のPillowベースの圧縮処理よりも高い圧縮率を実現する
2. WebP、AVIF、MozJPEGなど最新の画像フォーマットと最適化アルゴリズムを導入する
3. 画像品質を維持しながらファイルサイズを大幅に削減する
4. CLI/GUI両方のインターフェースでこれらの機能を提供する

## Squooshの主要コーデック分析

### コーデック優先順位（圧縮効率と互換性の観点）

1. **MozJPEG**
   - 互換性: すべてのブラウザとデバイスでサポート（標準JPEG）
   - 圧縮効率: 標準JPEGより約10-20%効率的
   - 品質設定（0-100）、ベースラインモード、プログレッシブモードをサポート
   - **実装優先度: 最高**（互換性と圧縮効率のバランスが最適）

2. **WebP**
   - 互換性: 主要なモダンブラウザでサポート
   - 圧縮効率: JPEGより約25-35%効率的
   - ロスレスとロッシーの両方をサポート、アルファチャンネル対応
   - **実装優先度: 高**（良好な互換性と優れた圧縮率）

3. **OxiPNG**
   - 互換性: すべてのブラウザとデバイスでサポート（標準PNG）
   - 圧縮効率: 標準PNGより効率的（ロスレス最適化）
   - **実装優先度: 中**（透過画像の最適化に有用）

4. **AVIF**
   - 互換性: 最新ブラウザのみ（Chrome、Firefox、Safari）
   - 圧縮効率: WebPより20-30%効率的
   - 高度な機能（HDR、ワイドカラー）
   - **実装優先度: 低〜中**（互換性の制約があるが、最高の圧縮効率）

### 実装アプローチ（ネイティブバインディング vs サブプロセス）

各コーデックで最適な実装方法を選択するのだ：

1. **MozJPEG**
   - 推奨: ネイティブバインディング（pymozjpeg）
   - 理由: 高いパフォーマンスが必要、頻繁に使用される
   - フォールバック: コマンドラインツール（mozjpeg）

2. **WebP**
   - 推奨: Pillowの組み込みサポート
   - 理由: 安定性とパフォーマンスのバランスが良い
   - 備考: 高度なオプションは、Pillowを通じて提供

3. **OxiPNG**
   - 推奨: サブプロセス呼び出し（oxipng CLIツール）
   - 理由: 安定性重視、クラッシュがメインプロセスに影響しない

4. **AVIF**
   - 推奨: ネイティブバインディング（pillow-avif-plugin）
   - フォールバック: libavifのコマンドラインツール

## メモリ・パフォーマンス特性

各コーデックのリソース要件とパフォーマンス特性のだ：

| コーデック | メモリ消費量 | 処理時間 | 最適化レベル |
|:----------|:-----------|:--------|:------------|
| MozJPEG   | 入力画像の約1.5〜2倍 | 中 | 品質設定が高いほど増加 |
| WebP      | 入力画像の約1.5〜2倍 | 中 | メソッド設定に依存 |
| OxiPNG    | 入力画像の約2〜3倍 | 高 | 最適化レベルに大きく依存 |
| AVIF      | 入力画像の約2〜3倍 | 最高 | 速度設定が低いほど大幅に増加 |

## 実装計画（フェーズ別）

### フェーズ1: プロジェクト基盤とコーデック準備（3日間）

1. **プロジェクト構造と依存関係の更新**
   - pyproject.tomlの作成（uvを使用）
   - 必要なライブラリ追加（pymozjpeg, pillow-avif-plugin等）
   - コーデックアダプタインターフェースの設計

2. **コーデックレジストリの実装**
   - コーデック抽象クラスの定義
   - 動的なコーデック検出と登録メカニズム
   - フォールバック機構の実装

### フェーズ2: 優先コーデック実装（5日間）

1. **MozJPEGアダプタ（最優先）**
   - ネイティブバインディング実装
   - サブプロセスフォールバック実装
   - テスト・最適化

2. **WebPアダプタ**
   - Pillowベースの実装
   - 高度なオプション対応
   - テスト・最適化

3. **OxiPNGアダプタ**
   - サブプロセス実装
   - 最適化レベル・オプション設定
   - テスト・最適化

### フェーズ3: コア機能拡張（4日間）

1. **resize_core.pyの拡張**
   - 新しいコーデック対応機能の追加
   - 処理パイプラインの最適化
   - コーデックオプション処理

2. **画像処理バッチ機能の強化**
   - 並列処理の最適化
   - メモリ管理機能導入
   - 大量画像処理の効率化

### フェーズ4: CLI/GUIの強化（3日間）

1. **CLIオプションの拡張**
   - コーデック選択オプション追加
   - コーデック固有パラメータ対応
   - ヘルプ情報の充実化

2. **GUI拡張**
   - 新しいコーデックオプション用UI追加
   - パラメータ調整スライダー・チェックボックス
   - プリセット機能の実装

### フェーズ5: パフォーマンス最適化（3日間）

1. **メモリ使用効率の改善**
   - メモリモニター実装
   - 自動リソース最適化機能
   - 一時ファイル活用戦略

2. **進行状況トラッキングの改善**
   - タスク管理システム実装
   - 統計情報と推定残り時間
   - 処理の一時停止・再開機能

### フェーズ6: テストおよび文書化（2日間）

1. **テスト実装**
   - 単体テスト作成
   - コーデック機能テスト
   - エラー処理テスト

2. **ドキュメント作成**
   - ユーザーガイド更新
   - コーデック別推奨設定
   - APIドキュメント

## コード設計詳細

### コーデックアダプタインターフェース

```python
# codecs/base.py
from abc import ABC, abstractmethod
from enum import Enum, auto
from typing import Optional, Dict, Any, Tuple
from pathlib import Path
from PIL import Image

class CodecType(Enum):
    STANDARD = auto()  # PILベース標準処理
    MOZJPEG = auto()   # MozJPEG
    WEBP = auto()      # WebP
    AVIF = auto()      # AVIF
    OXIPNG = auto()    # OxiPNG

class CodecAdapter(ABC):
    """画像コーデックの抽象アダプタクラス"""

    @classmethod
    @abstractmethod
    def is_available(cls) -> bool:
        """コーデックが利用可能か確認"""
        pass

    @classmethod
    @abstractmethod
    def get_supported_formats(cls) -> list[str]:
        """サポートする入力フォーマットリスト"""
        pass

    @classmethod
    @abstractmethod
    def get_default_options(cls) -> Dict[str, Any]:
        """デフォルトオプション"""
        pass

    @abstractmethod
    def encode(self, img: Image.Image, output_path: Path, options: Dict[str, Any]) -> Tuple[bool, int]:
        """画像をエンコード"""
        pass
```

### コア処理拡張

```python
# resize_core.py の拡張部分
from codecs import CodecRegistry, CodecType

def resize_and_compress_image(source_path, dest_path, target_width: int, quality: int,
                      format: str = 'original', keep_exif: bool = True,
                      balance: int = 5, webp_lossless: bool = False,
                      codec_type: str = 'standard', codec_options: dict = None,
                      dry_run: bool = False):
    # 既存コード...

    # 高度なコーデックを使用する場合の処理
    selected_codec = None

    if codec_type != 'standard' and not dry_run:
        try:
            codec_enum = CodecType[codec_type.upper()]

            # コーデックの登録と取得
            if CodecRegistry.register(codec_enum):
                adapter_class = CodecRegistry.get(codec_enum)
                if adapter_class:
                    selected_codec = adapter_class()
        except (KeyError, ValueError):
            logger.warning(f"不明なコーデックタイプ: {codec_type}")

    # 標準処理またはコーデック処理
    # ...
```

## 期待される効果

1. **ファイルサイズの削減率向上**
   - JPEG画像: 現行比10-30%削減
   - PNG画像: 現行比10-25%削減
   - WebP使用時: 現行比25-40%削減

2. **処理オプションの柔軟性向上**
   - コーデック別の詳細設定が可能に
   - 用途に応じた最適化プリセット
   - カスタム圧縮パラメータ

3. **最新フォーマットのサポート**
   - WebP、AVIF等の次世代フォーマット対応
   - 将来的なJPEG XL等への拡張容易化

## 実装スケジュール

- **フェーズ1（基盤整備）**: 2025年4月29日〜5月1日
- **フェーズ2（コーデック実装）**: 5月2日〜5月6日
- **フェーズ3（コア機能拡張）**: 5月7日〜5月10日
- **フェーズ4（UI拡張）**: 5月11日〜5月13日
- **フェーズ5（最適化）**: 5月14日〜5月16日
- **フェーズ6（テスト・文書）**: 5月17日〜5月18日

**完了予定**: 2025年5月18日

## 参考資料

- [Squoosh GitHub リポジトリ](https://github.com/GoogleChromeLabs/squoosh)
- [libSquoosh の概要 | Blog | web.dev](https://web.dev/blog/introducing-libsquoosh?hl=ja)
- [MozJPEG リポジトリ](https://github.com/mozilla/mozjpeg)
- [OxiPNG リポジトリ](https://github.com/shssoichiro/oxipng)

## 追加技術的考慮事項

Squoosh実装から学ぶべき重要な技術的側面を計画に反映させるのだ。

### 1. 並列処理アーキテクチャの最適化

SquooshはWeb WorkersとWebAssemblyスレッドプールを活用して並列処理を実現しているのだ。この知見を活かし、Pythonでの実装には以下の最適化を取り入れるのだ：

```python
# 並列処理アーキテクチャの実装例
import multiprocessing
import concurrent.futures
from typing import List, Callable, Any

class ParallelProcessor:
    """画像処理の並列実行を管理するクラス"""

    def __init__(self, max_workers: int = None):
        """
        並列処理マネージャーの初期化

        Args:
            max_workers: 最大ワーカー数（None=CPUコア数の75%を使用）
        """
        if max_workers is None:
            # CPUコア数の75%を使用（最小2）- Squooshの考え方を応用
            self.max_workers = max(2, (multiprocessing.cpu_count() * 3) // 4)
        else:
            self.max_workers = max_workers

    def process_batch(self, items: List[Any], process_func: Callable[[Any], Any]) -> List[Any]:
        """
        アイテムのバッチを並列処理

        Args:
            items: 処理するアイテムのリスト
            process_func: 各アイテムに適用する関数

        Returns:
            処理結果のリスト
        """
        # マルチプロセスプールを使用（GILの制約を回避）
        with concurrent.futures.ProcessPoolExecutor(max_workers=self.max_workers) as executor:
            results = list(executor.map(process_func, items))

        return results
```

### 2. メモリ管理の強化

Squooshは大きな画像処理時のメモリオーバーフローを防ぐための複数の技術を実装しているのだ。これを参考に、以下のメモリ管理強化を行うのだ：

- **段階的処理パイプライン**: デコード→前処理→リサイズ→エンコードの各ステップでメモリを解放
- **スキャンライン処理**: 大きな画像を一度に全てメモリに読み込まない処理方法の実装
- **条件付き前処理**: 必要な場合のみ追加メモリを使用する最適化

```python
# メモリ効率良い画像処理の例
import os
import gc
import psutil
import numpy as np
from PIL import Image
from pathlib import Path

class MemoryEfficientImageProcessor:
    """メモリ効率の良い画像処理を提供するクラス"""

    @staticmethod
    def process_large_image(input_path: Path, output_path: Path,
                          process_func: Callable[[np.ndarray], np.ndarray],
                          max_memory_mb: int = 1024) -> bool:
        """大きな画像を効率的に処理する"""
        try:
            # 入力画像情報の取得（完全に読み込まずに）
            with Image.open(input_path) as img:
                width, height = img.size
                mode = img.mode

                # 必要なメモリを推定
                estimated_memory = width * height * len(mode) * 4  # 32bit浮動小数点を想定
                estimated_memory_mb = estimated_memory / (1024 * 1024)

                if estimated_memory_mb > max_memory_mb:
                    # 分割処理が必要
                    return MemoryEfficientImageProcessor._process_by_chunks(
                        input_path, output_path, process_func, max_memory_mb
                    )
                else:
                    # 一度に処理可能
                    img_array = np.array(img)
                    result_array = process_func(img_array)

                    # 結果を保存
                    result_img = Image.fromarray(result_array)
                    result_img.save(output_path)

                    # メモリ解放を明示的に行う
                    del img_array
                    del result_array
                    gc.collect()

                    return True
        except Exception as e:
            logger.error(f"画像処理エラー: {e}")
            return False
```

### 3. ハードウェア最適化の検出と活用

SquooshはSIMDなどのハードウェア最適化機能を検出し、最適な実装を選択しているのだ。Pythonでも同様のアプローチを採用するのだ：

- **NumPyのSIMD最適化活用**: NumPyの内部最適化を最大限に活用
- **Numba/Cythonによる最適化**: パフォーマンスクリティカルな部分はNumbaデコレータやCythonで実装
- **プラットフォーム検出**: 実行環境のCPU機能を検出し、最適な実装を選択

```python
# ハードウェア最適化検出の例
import platform
import subprocess
from enum import Enum, auto

class HardwareFeatures(Enum):
    AVX = auto()
    AVX2 = auto()
    SSE4 = auto()
    NEON = auto()  # ARM

class OptimizationDetector:
    """ハードウェア最適化機能の検出とコーデック選択"""

    @staticmethod
    def detect_simd_features() -> set:
        """利用可能なSIMD命令セットを検出"""
        features = set()
        system = platform.system()
        machine = platform.machine()

        if system == "Linux":
            try:
                # /proc/cpuinfoからフラグを読み取る
                with open('/proc/cpuinfo', 'r') as f:
                    for line in f:
                        if line.startswith('flags'):
                            flags = line.split(':')[1].strip().split()
                            if 'avx' in flags:
                                features.add(HardwareFeatures.AVX)
                            if 'avx2' in flags:
                                features.add(HardwareFeatures.AVX2)
                            if 'sse4_1' in flags and 'sse4_2' in flags:
                                features.add(HardwareFeatures.SSE4)
                            break
            except:
                pass
        # 他のプラットフォーム検出...

        return features
```

### 4. エラー処理とフォールバック機構

コーデック処理失敗時の堅牢なフォールバック戦略も重要なのだ：

- **段階的フォールバック**: 高度なコーデックから標準実装へのフォールバック
- **エラー回復**: 部分処理成功の場合の結果保存と処理再開
- **診断情報**: 詳細なエラー情報の記録とログ出力

## 実装優先順位の再考

Squooshの技術的詳細を踏まえて、実装優先順位を以下のように調整するのだ：

1. **基盤クラスの実装** (フェーズ1の一部として)
   - 並列処理フレームワーク
   - メモリ効率の良い画像処理基盤
   - ハードウェア最適化検出

2. **MozJPEG実装とテスト** (最優先コーデック)
   - ネイティブバインディングとサブプロセスの両方の実装
   - 大規模画像の処理テスト

3. **コア処理パイプラインの最適化**
   - メモリ使用効率の向上
   - 段階的処理の導入
   - 並列処理の組み込み

これらの技術的側面を実装計画に組み込むことで、karukuresizeはSquooshと同等の高性能な画像圧縮・最適化機能を提供できるようになるのだ。特に大量画像の処理や高解像度画像の扱いにおいて、大幅なパフォーマンス向上が期待できるのだ。
