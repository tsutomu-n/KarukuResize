Goal: GUI表示フォーマットを `JPEG|Wpx x Hpx|KB|-NN%` へ統一し、Windows運用での uv sync 長時間化とロック障害を次回再実行で切り分けする。

KeyDecisions:
- 表示文字列を4区画で統一（例: `JPEG|4096px x 2731px|1200KB|-23%`）
- `font_resized_info` を `small_size - 2` に固定
- `uv sync` 切り分けは `--verbose` を主軸、`--no-build` 系は暫定回避のみ

CurrentTask:
- Windows実行環境で `uv sync --group dev` を再実行し、停止フェーズを確定。

PendingIssues:
- フリーズ時に Tkinter キュー更新が止まる根因
- `Remove-Item` を塞ぐロックプロセスの特定