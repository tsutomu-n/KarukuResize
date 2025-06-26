# Windows 11でKarukuResizeを使う方法

WSL2で開発したKarukuResizeをWindows 11で直接使う方法を説明します。

## 🚀 方法1: Git Cloneして使う（推奨）

### 1. 前提条件
- Windows 11
- Python 3.12以上がインストール済み
- Git for Windowsがインストール済み

### 2. セットアップ手順

```powershell
# PowerShellを開く（管理者権限不要）

# 1. 適当な場所にクローン
cd C:\Users\%USERNAME%\Documents
git clone https://github.com/yourusername/KarukuResize.git
cd KarukuResize

# 2. Python仮想環境を作成（推奨）
python -m venv venv
.\venv\Scripts\activate

# 3. 依存関係をインストール
pip install -e .

# 4. GUIを起動
karukuresize-gui

# または直接実行
python resize_images_gui.py
```

### 3. ショートカット作成

デスクトップにショートカットを作成すると便利です：

1. デスクトップで右クリック → 新規作成 → ショートカット
2. 項目の場所：
   ```
   C:\Users\%USERNAME%\Documents\KarukuResize\venv\Scripts\python.exe C:\Users\%USERNAME%\Documents\KarukuResize\resize_images_gui.py
   ```
3. 名前：`KarukuResize GUI`

## 🎯 方法2: WSL2のファイルを直接使う

Git Cloneせずに、WSL2のプロジェクトをWindows側から直接使うこともできます。

### 1. エクスプローラーから開く

1. Windowsキー + R → `\\wsl$` と入力
2. Ubuntu → home → tn → projects → KarukuResize を開く
3. アドレスバーに `cmd` と入力してコマンドプロンプトを開く

### 2. PowerShellから実行

```powershell
# PowerShellで直接WSL2のファイルにアクセス
cd \\wsl$\Ubuntu\home\tn\projects\KarukuResize

# Python環境の確認
python --version

# 依存関係をインストール（初回のみ）
pip install pillow customtkinter loguru tqdm emoji

# GUIを起動
python resize_images_gui.py
```

## 🖼️ Windows版GUI使用時のメリット

1. **ネイティブ動作** - X11サーバー不要
2. **高速** - WSL2のオーバーヘッドなし
3. **安定** - Windows標準のGUIフレームワーク使用
4. **ドラッグ&ドロップ** - エクスプローラーから直接ファイル操作

## 📝 使い方

### GUI起動後の操作

#### 1. 単一ファイル処理（リサイズタブ）
1. 「📁 参照」ボタンで画像を選択
2. リサイズ設定を調整
3. 「🚀 処理開始」をクリック

#### 2. 一括処理（一括処理タブ）
1. 入力フォルダを選択
2. 出力フォルダを選択
3. リサイズ・圧縮設定を調整
4. 「🚀 一括処理開始」をクリック

## 🔧 トラブルシューティング

### Q: 「ModuleNotFoundError」が出る
```powershell
# 依存関係を再インストール
pip install -r requirements.txt

# または個別にインストール
pip install pillow customtkinter loguru tqdm emoji
```

### Q: 「Python が見つかりません」
1. [Python公式サイト](https://www.python.org/)からPython 3.12以上をダウンロード
2. インストール時に「Add Python to PATH」にチェック

### Q: 文字化けする
Windows版は日本語に完全対応しています。フォントの問題の場合：
- Windows設定 → 時刻と言語 → 言語 → 管理用の言語の設定
- 「Unicode UTF-8」を有効にする

## 💡 便利な使い方

### バッチファイルの作成

`karuku_gui.bat`を作成：
```batch
@echo off
cd /d C:\Users\%USERNAME%\Documents\KarukuResize
call venv\Scripts\activate
python resize_images_gui.py
```

### スタートメニューへの登録

1. `karuku_gui.bat`を右クリック
2. 「スタートメニューにピン留め」を選択

## 🎉 まとめ

Windows 11では、WSL2なしでKarukuResizeのGUIを快適に使用できます。Git CloneするかWSL2のファイルを直接参照するだけで、すぐに使い始められます！