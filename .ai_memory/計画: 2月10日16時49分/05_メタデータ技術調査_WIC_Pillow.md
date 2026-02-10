# メタデータ技術調査（WIC / Pillow）

## 1. 調査目的
- GUIに追加するメタデータ編集機能の「実装可能範囲」を事実ベースで確定する。
- 形式差・ライブラリ差による非対応ケースを事前に把握する。

## 2. 主要調査結果（要約）

### 2.1 Pillow観点
1. `Image.getexif()` でEXIFを取得・編集できる。
2. `Image.save(..., exif=bytes)` で保存時にEXIF付与できる。
3. JPEGの保存オプションは `quality`（推奨上限95）、`optimize`、`progressive` などが利用可能。
4. 形式ごとの対応可否は実行環境依存があるため、実行時判定が必要。
5. XMP/ICC も保存オプションで扱える余地がある（今後拡張候補）。

### 2.2 WIC観点（Windowsメタデータ体系）
1. Photo Metadata Policy で共通プロパティ名を通じて項目を扱える。
2. GPS、撮影日時、著作権、キーワード、カメラ情報などの代表項目を体系化できる。
3. 既知ハンドラがないメタデータは編集不可（保持のみ等の扱いになる）。

## 3. 実装計画に直結する示唆
1. GUI項目は WIC の共通項目カテゴリを参考に設計すると整理しやすい。
2. ただし実装エンジンは Pillow 中心なので、編集可能タグを先に明示する必要がある。
3. 「全項目を自由編集」は初回対象にしない（UI複雑化と不整合リスクが高い）。

## 4. 現行コードとの整合
- 既存 `image_save_pipeline.py` は EXIF編集4項目を実装済み。
- 拡張は次の方向が自然:
  1. 編集項目の追加
  2. `ExifEditValues` の拡張
  3. タグ変換ロジックの責務分離

## 5. 推奨する段階的項目セット

### 5.1 第1段階（簡易モードでも意味がある項目）
1. DateTaken（撮影日時）
2. Author（撮影者）
3. Copyright（著作権）
4. Title
5. Comment
6. Keywords
7. GPS（緯度/経度/高度）

### 5.2 第2段階（プロモード追加）
1. Camera Manufacturer / Model
2. Lens Manufacturer / Model
3. ISO
4. ExposureTime
5. FNumber
6. FocalLength
7. Orientation

### 5.3 第3段階（任意）
1. WhiteBalance
2. MeteringMode
3. LightSource
4. Flash
5. Saturation / Contrast / Sharpness

## 6. 技術制約の明文化（実装時にUIへ反映すべき事項）
1. 入力形式と出力形式で、メタデータの保持・再付与の挙動は同一ではない。
2. EXIF付与失敗時のフォールバック保存（メタデータなし）は現行実装の重要仕様。
3. 「編集不可項目」はUI側で明示し、保存失敗扱いにしない。

## 7. 今回の方針への反映
1. 初回実装は「簡易/プロ分離 + 第1段階項目」を主軸にする。
2. 第2段階以降は内部モデルの拡張が済んでから順次追加する。

## 8. 参照（調査元）
1. https://learn.microsoft.com/ja-jp/windows/win32/wic/-wic-native-image-format-metadata-queries
2. https://learn.microsoft.com/en-us/windows/win32/wic/-wic-photopropsystems
3. https://learn.microsoft.com/en-us/windows/win32/wic/-wic-photoprop-system-photo-datetaken
4. https://learn.microsoft.com/en-us/windows/win32/wic/-wic-photoprop-system-gps-latitude
5. https://learn.microsoft.com/en-us/windows/win32/wic/-wic-codec-metadatahandlers
6. https://github.com/python-pillow/pillow/blob/main/docs/handbook/image-file-formats.rst
7. https://github.com/python-pillow/pillow/blob/main/docs/releasenotes/8.3.0.rst
8. https://github.com/python-pillow/pillow/blob/main/docs/releasenotes/9.4.0.rst
9. https://github.com/python-pillow/pillow/blob/main/docs/releasenotes/11.0.0.rst
