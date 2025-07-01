# WSL2でKarukuResizeを使う完全ガイド

## 🎯 推奨方法：CLI版を使う（最も確実）

WSL2では**CLI版の使用を強く推奨**します。GUIと同等の機能があり、安定して動作します。

### CLI版の基本的な使い方

```bash
# 基本的なリサイズ（幅1280px、品質85%）
karukuresize-cli -s input -d output -w 1280 -q 85

# 高品質でリサイズ
karukuresize-cli -s input -d output -w 1920 -q 95

# サムネイル作成
karukuresize-cli -s input -d output -w 300 -q 80

# ドライラン（実際に保存せず確認）
karukuresize-cli -s input -d output -w 1280 --dry-run
```

### CLI版の利点
- ✅ 環境依存なし - WSL2で確実に動作
- ✅ スクリプト化可能 - 自動化に便利
- ✅ 高速処理 - GUIオーバーヘッドなし
- ✅ SSH経由でも使用可能

## 🖼️ GUI版を使いたい場合

### 方法1: WSLg（Windows 11のみ）

Windows 11をお使いの場合、WSLgが標準搭載されています。

```bash
# WSL2を最新版に更新
wsl --update

# 必要なパッケージをインストール
sudo apt update
sudo apt install -y libgtk-3-0 libnotify4 libsdl2-2.0-0

# GUIを起動
karukuresize-gui
```

### 方法2: VcXsrvを使う（Windows 10/11）

#### 1. Windows側でVcXsrvをインストール

1. [VcXsrv](https://sourceforge.net/projects/vcxsrv/)をダウンロード・インストール
2. XLaunchを起動し、以下の設定で開始：
   - Display number: 0
   - Start no client
   - ✅ Disable access control

#### 2. WSL2側で環境変数を設定

```bash
# ~/.bashrcに追加（永続化）
echo 'export DISPLAY=$(cat /etc/resolv.conf | grep nameserver | awk '\''{print $2}'\''):0' >> ~/.bashrc
echo 'export LIBGL_ALWAYS_INDIRECT=1' >> ~/.bashrc

# 現在のセッションに適用
source ~/.bashrc

# GUIを起動
karukuresize-gui
```

### 方法3: Windows側で直接実行

WSL2のファイルにWindows側からアクセス：

```powershell
# Windows PowerShellで実行
# WSL2のプロジェクトパスを確認
\\wsl$\Ubuntu\home\tn\projects\KarukuResize

# Windows側にPythonがインストールされている場合
cd \\wsl$\Ubuntu\home\tn\projects\KarukuResize
python resize_images_gui.py
```

## 🚀 WSL2用クイック起動スクリプト

以下のスクリプトを作成すると便利です：

### `wsl-gui.sh`
```bash
#!/bin/bash
# WSL2でGUIを起動するスクリプト

# Display設定
export DISPLAY=$(cat /etc/resolv.conf | grep nameserver | awk '{print $2}'):0
export LIBGL_ALWAYS_INDIRECT=1

# エラーハンドリング
if ! command -v karukuresize-gui &> /dev/null; then
    echo "karukuresize-guiが見つかりません。インストールしてください："
    echo "uv pip install -e ."
    exit 1
fi

# VcXsrvが起動しているか確認
if ! nc -z $(cat /etc/resolv.conf | grep nameserver | awk '{print $2}') 6000 2>/dev/null; then
    echo "警告: X11サーバーが検出されません。"
    echo "Windows側でVcXsrvを起動してください。"
    echo ""
    echo "代わりにCLI版を使いますか？ [Y/n]"
    read -r response
    if [[ "$response" =~ ^([yY][eE][sS]|[yY])$ ]] || [[ -z "$response" ]]; then
        echo "CLI版の使い方："
        echo "karukuresize-cli -s input -d output -w 1280 -q 85"
        exit 0
    fi
fi

# GUIを起動
echo "GUIを起動中..."
karukuresize-gui
```

## 📊 WSL2でのパフォーマンス比較

| 方法 | 速度 | 安定性 | 設定の簡単さ |
|------|------|--------|--------------|
| CLI版 | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| WSLg | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| VcXsrv | ⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐ |
| Windows側実行 | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ |

## 🔧 トラブルシューティング

### よくある問題と解決策

1. **「cannot open display」エラー**
   ```bash
   export DISPLAY=$(cat /etc/resolv.conf | grep nameserver | awk '{print $2}'):0
   ```

2. **「xcb_xlib_unknown_seq_number」エラー**
   ```bash
   # 代わりにCLI版を使用
   karukuresize-cli -s input -d output -w 1280 -q 85
   ```

3. **VcXsrvに接続できない**
   - Windowsファイアウォールで許可
   - VcXsrvを「Disable access control」で起動

4. **パフォーマンスが遅い**
   - CLI版の使用を検討
   - ファイルをWindows側にコピーして処理

## 💡 WSL2での実用的な使い方

### バッチ処理スクリプトの例

```bash
#!/bin/bash
# batch_resize.sh - 複数フォルダを一括処理

folders=("photos2023" "photos2024" "screenshots")
for folder in "${folders[@]}"; do
    echo "処理中: $folder"
    karukuresize-cli -s "$folder" -d "${folder}_resized" -w 1280 -q 85
done
```

### エイリアスの設定

```bash
# ~/.bashrcに追加
alias resize='karukuresize-cli'
alias resize-thumb='karukuresize-cli -w 300 -q 80'
alias resize-web='karukuresize-cli -w 1280 -q 85'
alias resize-hq='karukuresize-cli -w 1920 -q 95'

# 使用例
resize -s input -d output  # 基本的なリサイズ
resize-thumb -s photos -d thumbs  # サムネイル作成
```

## 🎯 結論

WSL2では**CLI版の使用が最も実用的**です。GUIが必要な場合は、Windows 11のWSLgまたはVcXsrvを使用してください。

### 💡 最も簡単な解決策

**Windows側にGit Cloneして使う**のが最も簡単です。詳細は[Windowsガイド](./WINDOWS_GUIDE.md)を参照してください。

```powershell
# Windows PowerShellで
git clone [このリポジトリ]
cd KarukuResize
pip install -e .
karukuresize-gui
```