# Context7調査メモ

## 1. 取得対象
1. CustomTkinter（`/tomschimansky/customtkinter`）
2. Pillow（`/python-pillow/pillow`）

## 2. 取得要点

### 2.1 CustomTkinter
- `set_appearance_mode("System"|"Dark"|"Light")` はランタイム変更可能。
- `get_appearance_mode()` で現在モード取得可能。
- tuple colorは appearance mode に連動して自動適用。
- 本計画への意味:
  - GUI内切替UI追加の技術障壁は低い。
  - 既存の色定義（tuple）を活かせる。

### 2.2 Pillow
- `getexif()` と `ExifTags` によるメタデータ取得が基本手段。
- `save(..., exif=...)` でEXIF保存が可能（特にJPEGは明示記載）。
- TIFF/GPS IFDアクセスに `get_ifd` を利用可能。
- 本計画への意味:
  - プロモードの「読み取り表示」は既存依存だけで実装可能。
  - 書き込み系は既存パイプラインを再利用する方針が妥当。

## 3. 補足
- Context7の結果は、最終的に公式ドキュメントURLで照合して利用する。
