# Contributing to KarukuResize

このプロジェクトへの改善提案・PR は歓迎です。  
公開リポジトリとして、変更は次の手順で揃えてください。

## 1. 開発環境

```bash
uv sync --group dev
```

## 2. ブランチ運用

- `main` から作業ブランチを切ってください。
- 1つのPRでは1つの目的に絞ってください（機能追加 / 修正 / ドキュメント更新）。

## 3. 変更時の確認

```bash
uv run ruff check src tests
uv run pytest -q
```

- 失敗がある状態ではPRを作らないでください。
- 仕様変更がある場合は `README.md` または `docs/` も更新してください。

## 4. コミットメッセージ

- 変更内容が分かる短い要約を先頭に置いてください。
- 例:
  - `fix(gui): prevent recursion in appearance mode callback`
  - `feat(cli): add --failures-file and json summary`
  - `docs: update windows build guide`

## 5. PR本文に含める内容

- 何を変えたか
- なぜ必要か
- どう確認したか（実行コマンド / 結果）
- 影響範囲（GUI / CLI / docs / build）
