# Windows 11 ガイド

Windows 11 で KarukuResize を実行・ビルドするための手順です。

## 1. 前提

- Windows 11
- Python 3.12 以上
- Git
- PowerShell

## 2. セットアップ

```powershell
cd $HOME\Documents
git clone https://github.com/tsutomu-n/KarukuResize.git
cd KarukuResize

python -m venv .venv
.\.venv\Scripts\Activate.ps1

pip install uv
uv sync --group dev
```

## 3. GUI起動

```powershell
uv run karukuresize-gui
# または
uv run python -m karuku_resizer.gui_app
```

## 4. プロモード再帰読込（Windows運用）

1. アプリ上で `プロ` に切替
2. `📂 画像/フォルダを選択`
3. `はい: フォルダーを再帰読み込み`
4. 対象は `jpg/jpeg/png`
5. ドラッグ&ドロップでも同様（単体ファイルは `png/jpg/jpeg/webp/avif`）

動作仕様:
- 読込中は操作を抑制し、進捗バーとステータスを表示
- `読み込み中止` でキャンセル可能
- 完了時に成功/失敗件数を表示
- 失敗ファイルがある場合は「失敗のみ再試行」が可能
- 失敗一覧は結果ダイアログからコピー可能
- 選択方式（再帰/個別）は前回設定を記憶
- 最近使った設定（最大6件）をヘッダから再適用可能

## 5. WindowsでのEXEビルド

```powershell
uv run karukuresize-build-exe
```

生成物:
- `dist\KarukuResize.exe`

アイコン設定:
- EXEアイコンは `assets\app.ico` が自動で使われます。
- アイコンを変更したい場合は `assets\app.ico` を差し替えてから再ビルドしてください。

## 6. ビルド後の最小確認

1. `KarukuResize.exe` が起動する
2. プロモードで再帰読込時、ウィンドウが固まらず進捗表示される
3. `読み込み中止` が効く
4. `📁 一括適用保存` が完了し、失敗時は詳細表示される

## 6.1 DPI / OS 検証ターゲット（運用基準）

今回のUI改修では、次を標準の確認範囲とします。

| 区分 | 対象 |
|---|---|
| 必須DPI | 100% / 125% / 150% |
| 任意DPI | 200% |
| 優先OS | Windows 11 |
| 目視確認 | macOS (Retina) |

確認ポイント:
1. ウィンドウ最小幅 `1200px` で、上部2段の操作エリアが切れない
2. ボタン・ラジオ・プリセット操作がクリック可能
3. 設定サマリー行の文字が極端に欠けない
4. `📂 画像を選択` / `🔄 プレビュー` / `💾 保存` / `📁 一括適用保存` が動作する

## 7. トラブルシュート

- 依存関係エラー:
  - `uv sync --group dev` を再実行
- 起動時エラー:
  - 仮想環境を有効化して `uv run python -m karuku_resizer.gui_app` で詳細確認
- EXEが起動しない:
  - セキュリティソフト除外設定、またはビルドを再実行
