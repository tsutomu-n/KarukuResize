# Windows ガイド

Windows 環境で KarukuResize を実行・ビルドする手順です。

## 前提

- Windows 10/11
- Python 3.12 以上
- Git
- PowerShell

## 1. セットアップ

```powershell
cd $HOME\Documents
git clone https://github.com/tsutomu-n/KarukuResize.git
cd KarukuResize
uv sync --group dev
```

## 2. GUI 起動

```powershell
uv run karuku-resizer
```

互換エイリアス:

```powershell
uv run karukuresize-gui
```

## 3. 使い方（実運用）

1. `画像を選択` で画像またはフォルダを読み込む
2. 必要ならプロモードに切り替えて再帰読込を使う
3. サイズ・形式・品質などを調整して `プレビュー`
4. `保存` または `一括適用保存` を実行

プロモード再帰読込:
- 対象拡張子は `jpg/jpeg/png`
- 読込中は進捗表示
- 失敗がある場合は「失敗のみ再試行」が利用可能

## 4. EXE ビルド

```powershell
uv run karukuresize-build-exe
```

生成物:
- `dist\KarukuResize.exe`

アイコン:
- `assets\app.ico` を使用
- 変更する場合は差し替えて再ビルド

## 5. ビルド後チェック

1. `KarukuResize.exe` が起動する
2. 画像読み込み、プレビュー、保存が実行できる
3. 一括適用保存が完了まで進む
4. 失敗時にエラー内容が確認できる

## 6. DPI確認基準

推奨検証:
- 必須: 100% / 125% / 150%
- 任意: 200%

確認ポイント:
1. 最小幅 `1200px` で上部操作エリアが破綻しない
2. ボタン・ラジオ・入力が操作可能
3. 設定サマリー行の表示が欠けすぎない

## 7. トラブルシュート

- 依存関係エラー:
  - `uv sync --group dev` を再実行
- GUI起動エラー:
  - `uv run python -m karuku_resizer.gui_app` で詳細確認
- EXE起動失敗:
  - 再ビルド後に再確認
