# WSL2 ガイド

WSL2 で KarukuResize を使う場合の推奨運用をまとめます。

## 結論

- WSL2 では **CLI運用を推奨**
- GUIを安定利用したい場合は **Windows側で起動** を推奨

## 1. WSL2 で CLI を使う

```bash
git clone https://github.com/tsutomu-n/KarukuResize.git
cd KarukuResize
uv sync --group dev
```

実行例:

```bash
uv run karukuresize-cli -s input -d output -w 1280 -q 85
uv run karukuresize-cli -s input -d output --dry-run
uv run karukuresize-cli -s input -d output --json --failures-file failures.json
```

## 2. GUI が必要な場合

### 推奨: Windows側で実行

同じリポジトリを Windows 側に clone して、`uv run karuku-resizer` で起動する方法が最も安定します。
詳細は `docs/WINDOWS_GUIDE.md` を参照してください。

### 代替: WSLg

Windows 11 + WSLg 環境であれば動作する場合がありますが、環境差が大きいため運用は自己検証前提です。

## 3. よくある問題

### `cannot open display`

WSL2 側GUI表示設定が不足しています。CLI運用に切り替えるか、Windows側実行へ切り替えてください。

### GUIが不安定・重い

X転送や描画環境差の影響です。Windows側GUI起動に切り替えると安定します。

### コマンドが見つからない

`uv sync --group dev` 済みか、プロジェクトルートで実行しているか確認してください。

## 4. 実務向け運用ヒント

- WSL2ではCLIでバッチ処理
- GUI調整はWindows側で実施
- 生成物の確認は同じ出力フォルダを共有して行う
