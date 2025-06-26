# KarukuResize インストールガイド

## 🔧 インストール方法

### 方法1: uv を使用（推奨）

このプロジェクトはpyproject.tomlで管理されているため、uvを使用することを推奨します：

```bash
# uvをインストール（まだの場合）
curl -LsSf https://astral.sh/uv/install.sh | sh  # Linux/macOS
# または
pip install uv  # すべてのOS

# プロジェクトをインストール
uv pip install -e .
```

インストール後、以下のコマンドが使用可能になります：
- `karukuresize-cli` - コマンドラインツール
- `karukuresize-gui` - GUIツール

### 方法2: pip を使用

uvが使えない場合は、通常のpipでもインストール可能です：

```bash
# pyproject.toml を使用してインストール
pip install -e .
```

### 方法3: 依存関係の個別インストール（非推奨）

pyproject.tomlを使わずに必要な依存関係だけをインストール：

```bash
# 必要な依存関係をインストール
pip install pillow customtkinter loguru tqdm emoji
```

注意: この方法では`karukuresize-cli`や`karukuresize-gui`コマンドは使用できません。

## 🐍 Python バージョンの確認

KarukuResizeはPython 3.12以上が必要です：

```bash
# Pythonバージョンを確認
python --version

# python3 コマンドの場合
python3 --version
```

## 🖥️ OS別の注意事項

### Windows
```bash
# Windowsの場合はpyコマンドも使用可能
py -m pip install pillow customtkinter loguru tqdm emoji
```

### macOS
```bash
# Homebrewでpython3をインストールしている場合
python3 -m pip install pillow customtkinter loguru tqdm emoji
```

### Linux
```bash
# システムのpython3を使用
python3 -m pip install pillow customtkinter loguru tqdm emoji
```

## ✅ インストール確認

インストールが成功したか確認：

```python
# Pythonインタープリタで確認
python -c "import PIL; print('Pillow OK')"
python -c "import customtkinter; print('CustomTkinter OK')"
python -c "import loguru; print('Loguru OK')"
python -c "import tqdm; print('tqdm OK')"
python -c "import emoji; print('emoji OK')"
```

すべて「OK」と表示されれば成功です！

## 🚨 よくあるエラーと対処法

### 1. pip が見つからない
```bash
# pipをインストール
python -m ensurepip --upgrade

# またはget-pip.pyを使用
curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py
python get-pip.py
```

### 2. Permission denied エラー
```bash
# ユーザーディレクトリにインストール
pip install --user pillow customtkinter loguru tqdm emoji
```

### 3. customtkinter のインストールエラー
```bash
# tkinterが必要な場合（Linux）
sudo apt-get install python3-tk  # Ubuntu/Debian
sudo yum install python3-tkinter  # CentOS/RHEL
```

## 🎯 次のステップ

インストールが完了したら、[QUICK_START.md](./QUICK_START.md)を参照して使い始めてください！