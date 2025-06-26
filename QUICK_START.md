# KarukuResize クイックスタートガイド

このガイドでは、KarukuResizeをすぐに使い始める方法を説明します。

## 🚀 最速セットアップ

### Linux/macOS の場合
```bash
# 1. uvでプロジェクトをインストール
uv pip install -e .

# 2. テスト画像を作成（オプション）
python tests/create_test_images.py

# 3. 使い始める！
karukuresize-cli -s input -d output -w 1280 -q 85
```

### Windows/WSL2 の場合
- **WSL2でGUIを使いたい場合** → [Windowsガイド](./WINDOWS_GUIDE.md)を参照（Windows側で実行を推奨）
- **WSL2でCLIを使う場合** → 上記のLinux/macOSと同じ手順

## 📋 前提条件

- Python 3.12以上がインストールされていること
- uv（推奨）または pip が使用できること

## 🚀 セットアップ詳細

### 1. プロジェクトのインストール

```bash
# uvを使う場合（推奨）
uv pip install -e .

# または通常のpipを使う場合
pip install -e .
```

これにより、すべての依存関係が自動的にインストールされ、以下のコマンドが使用可能になります：
- `karukuresize-cli` - コマンドラインツール
- `karukuresize-gui` - GUIツール

### 2. テスト画像の準備（オプション）

テスト用の画像を自動生成できます：

```bash
python tests/create_test_images.py
```

これにより、`input`フォルダに5つのテスト画像が作成されます。

## 💻 CLI版の使い方

### 基本コマンド

インストール後は`karukuresize-cli`コマンドが使用できます：

```bash
karukuresize-cli -s 入力フォルダ -d 出力フォルダ [オプション]
```

直接Pythonスクリプトを実行することも可能です：

```bash
python resize_images.py -s 入力フォルダ -d 出力フォルダ [オプション]
```

### よく使うコマンド例

```bash
# 1. 基本的な使い方（幅1280px、品質85%）
karukuresize-cli -s input -d output -w 1280 -q 85

# 2. 高品質でリサイズ（幅1920px、品質95%）
karukuresize-cli -s input -d output -w 1920 -q 95

# 3. 小さくリサイズ（幅800px、品質80%）
karukuresize-cli -s input -d output -w 800 -q 80

# 4. ドライラン（実際に保存せず結果を確認）
karukuresize-cli -s input -d output -w 1280 --dry-run

# 5. デバッグモード（詳細なログを表示）
karukuresize-cli -s input -d output -w 1280 --debug
```

### オプション一覧

| オプション | 説明 | デフォルト |
|-----------|------|-----------|
| `-s, --source` | 入力フォルダパス | 必須 |
| `-d, --dest` | 出力フォルダパス | 必須 |
| `-w, --width` | リサイズ後の最大幅 | 1280 |
| `-q, --quality` | JPEG品質 (1-100) | 85 |
| `--dry-run` | 実際に保存せずシミュレート | False |
| `--resume` | 既存ファイルをスキップ | False |
| `--debug` | デバッグモード | False |

## 🖼️ GUI版の使い方

### 起動方法

インストール後は`karukuresize-gui`コマンドが使用できます：

```bash
karukuresize-gui
```

直接Pythonスクリプトを実行することも可能です：

```bash
python resize_images_gui.py
```

### GUI操作ガイド

#### 1️⃣ リサイズタブ（単一ファイル処理）

1. 「📁 参照」ボタンで画像ファイルを選択
2. 出力先を選択（オプション）
3. リサイズ設定を調整
   - リサイズモード（幅指定、高さ指定など）
   - リサイズ値
   - アスペクト比の維持
4. 出力形式を選択（JPEG/PNG/WEBP）
5. 品質を調整（スライダー）
6. 「🚀 処理開始」をクリック

#### 2️⃣ 一括処理タブ（フォルダ単位の処理）

1. 入力フォルダを選択
2. 出力フォルダを選択
3. リサイズ設定を調整
   - モード: 指定なし/幅を指定/高さを指定/縦横最大/パーセント指定
   - 値を入力（モードに応じて）
4. 圧縮設定を調整
   - 出力フォーマット
   - 品質設定
5. 「🚀 一括処理開始」をクリック

### リサイズモードの説明

| モード | 説明 | 値の例 |
|--------|------|--------|
| 指定なし | リサイズしない（圧縮のみ） | - |
| 幅を指定 | 指定した幅にリサイズ | 1280 |
| 高さを指定 | 指定した高さにリサイズ | 720 |
| 縦横最大 | 長辺を指定サイズに | 1920 |
| パーセント指定 | 元のサイズの指定％に | 50 |

## 📁 フォルダ構成

```
KarukuResize/
├── input/           # 処理する画像を入れるフォルダ
├── output/          # 処理後の画像が保存されるフォルダ
├── resize_images.py # CLIツール
└── resize_images_gui.py # GUIツール
```

## 🔧 トラブルシューティング

### Q: 「ModuleNotFoundError」が出る
A: プロジェクトが正しくインストールされているか確認してください：
```bash
# uvを使用
uv pip install -e .

# または pip を使用
pip install -e .
```

### Q: 日本語ファイル名が文字化けする
A: このツールは日本語ファイル名に対応しています。問題が続く場合は、ファイル名に特殊文字が含まれていないか確認してください。

### Q: 「Permission denied」エラーが出る
A: 出力フォルダへの書き込み権限があるか確認してください。

### Q: GUIが起動しない
A: customtkinterが正しくインストールされているか確認してください：
```bash
pip install --upgrade customtkinter
```

**WSL2を使用している場合**: [WSL2ガイド](./WSL2_GUIDE.md)を参照してください。CLI版の使用を推奨します。

## 🎯 よくある使用シーン

| やりたいこと | コマンド |
|------------|---------|
| Web用に最適化 | `karukuresize-cli -s input -d output -w 1280 -q 85` |
| 高品質で保存 | `karukuresize-cli -s input -d output -w 1920 -q 95` |
| サムネイル作成 | `karukuresize-cli -s input -d output -w 300 -q 90` |
| 容量を小さく | `karukuresize-cli -s input -d output -w 800 -q 70` |
| 実行前に確認 | `karukuresize-cli -s input -d output -w 1280 --dry-run` |

## 💡 使用例

### 例1: ブログ用に画像を最適化
```bash
# 幅1200px、品質85%でリサイズ
karukuresize-cli -s blog_images -d blog_optimized -w 1200 -q 85
```

### 例2: サムネイル作成
```bash
# 幅300px、品質90%でリサイズ
karukuresize-cli -s photos -d thumbnails -w 300 -q 90
```

### 例3: WebP形式への変換（GUI使用）
1. GUIを起動（`karukuresize-gui`）
2. 一括処理タブを選択
3. 出力フォーマットを「WEBP」に設定
4. 品質を調整（80-90推奨）
5. 処理開始

## 📚 詳細ドキュメント

- [インストール詳細](./INSTALLATION.md)
- [開発者向け情報](./docs/developer_guide.md)
- [API仕様](./docs/api_reference.md)

## 📞 サポート

問題が解決しない場合は、以下を確認してください：
- エラーメッセージの詳細
- 使用しているPythonのバージョン（`python --version`）
- 処理しようとしている画像の形式とサイズ