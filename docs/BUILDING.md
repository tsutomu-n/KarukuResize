# KarukuResize ビルドガイド

このドキュメントでは、KarukuResizeをPyInstallerを使用して実行可能ファイルにビルドする方法を説明します。

## 前提条件

- Python 3.12以上
- Git
- 各プラットフォーム固有の要件（下記参照）

### Windows
- Windows 10/11
- Visual Studio Build Tools（オプション、一部の依存関係で必要な場合）

### macOS
- macOS 10.15以上
- Xcode Command Line Tools

### Linux
- 最新のディストリビューション（Ubuntu 20.04以上推奨）
- python3-tk, python3-dev パッケージ
- 日本語フォント（fonts-noto-cjk推奨）

## ビルド手順

### 1. リポジトリのクローン

```bash
git clone https://github.com/yourusername/KarukuResize.git
cd KarukuResize
```

### 2. 依存関係のインストール

```bash
# 仮想環境の作成（推奨）
python -m venv venv
# Windows
venv\Scripts\activate
# macOS/Linux
source venv/bin/activate

# 依存関係のインストール
uv sync --group dev
```

### 3. ローカルビルド

#### 自動ビルドスクリプトを使用する場合

```bash
uv run karukuresize-build-exe
```

#### 手動でビルドする場合

```bash
# 上記コマンドが内部でPyInstallerを実行します
uv run karukuresize-build-exe
```

### 4. ビルド結果

ビルドが成功すると、`dist/`ディレクトリに onefile 実行ファイルが生成されます。

- **Windows**: `dist/KarukuResize.exe`
- **macOS**: `dist/KarukuResize`
- **Linux**: `dist/KarukuResize`

### アイコンの変更

- Windows版EXEアイコンは `assets/app.ico` を使用します。
- 別アイコンにしたい場合は `assets/app.ico` を差し替えてから、再度 `uv run karukuresize-build-exe` を実行してください。

## GitHub Actionsでの自動ビルド

プロジェクトには自動ビルド用のGitHub Actionsワークフローが含まれています。

### タグをプッシュしてリリース

```bash
# バージョンタグを作成
git tag v0.2.1
git push origin v0.2.1
```

これにより、自動的に以下が実行されます：
1. Windows、macOS、Linux用の実行ファイルのビルド
2. 各プラットフォーム用の配布パッケージの作成
3. GitHubリリースへの自動アップロード

### 手動ビルドの実行

GitHubのActionsタブから手動でワークフローを実行することもできます。

## トラブルシューティング

### CustomTkinterが見つからない

```bash
# CustomTkinterを明示的にインストール
pip install customtkinter
```

### tkinterdnd2のエラー

`src/karuku_resizer/tools/hook-tkinterdnd2.py` が存在し、`karukuresize-build-exe` 実行時に
`--additional-hooks-dir` で同ディレクトリが渡されることを確認してください。

### 日本語フォントの問題

- **Windows**: システムに日本語フォントがインストールされていることを確認
- **macOS**: 通常は問題なし
- **Linux**: `sudo apt-get install fonts-noto-cjk`を実行

### Windows長パスの問題

Windows 10/11で長いパスのサポートを有効にする：
1. グループポリシーエディタを開く（gpedit.msc）
2. コンピューターの構成 > 管理用テンプレート > システム > ファイルシステム
3. 「Win32の長いパスを有効にする」を有効にする

### ビルドサイズの最適化

ビルドサイズを削減するには：
1. 不要な依存関係をアンインストールしてビルド対象を最小化
2. `src/karuku_resizer/build_exe.py` の引数を見直し、不要な hidden import を減らす
3. UPX圧縮（PyInstaller側）を有効活用する

## ビルド後スモークチェック（推奨）

生成された実行ファイルで、最低限以下を確認してください。

1. 起動直後にクラッシュしない
2. 画像を個別選択してプレビューできる
3. `プロ` モードでフォルダ再帰読込（`jpg/jpeg/png`）が動作する
4. 再帰読込中に進捗表示され、`読み込み中止` が効く
5. 読込失敗時に「失敗のみ再試行」が表示される
6. `📁 一括適用保存` が完了し、失敗時に詳細が表示される

## 開発者向け情報

### ビルド設定のカスタマイズ

`src/karuku_resizer/build_exe.py` の `PYINSTALLER_ARGS` を編集して、ビルド設定をカスタマイズできます：

- アイコンの追加
- 追加のデータファイル
- 隠しインポートの追加
- プラットフォーム固有の設定

### デバッグビルド

デバッグ情報を含むビルドを作成：

```bash
PYINSTALLER_LOG_LEVEL=DEBUG uv run karukuresize-build-exe
```

### 署名と公証

- **Windows**: コード署名証明書を使用（オプション）
- **macOS**: Developer IDで署名し、公証を行う（オプション）

詳細は各プラットフォームのドキュメントを参照してください。

## ライセンス

ビルドされた実行ファイルは、元のソースコードと同じライセンスに従います。
