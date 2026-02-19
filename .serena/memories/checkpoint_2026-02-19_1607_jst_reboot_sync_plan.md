Goal: Windows環境で `uv sync --group dev` を再起動後に安定完了し、起動まで復帰する。

KeyDecisions:
- 本セッションは環境再現性重視。追加コード変更は実施しない。
- 再起動後は `uv sync --group dev --verbose` を必須化し、停止時ログで原因確定する。
- ロック時は `Get-Process` でプロセスを確認し、必要なら停止してから再試行する。

CurrentTask:
- Windows再起動後にクリーン再クローンし、`uv sync --group dev --verbose > sync-log.txt` を実行して停止位置を確定。

PendingIssues:
- Windows側での `Preparing packages...` 長時間化の最終原因
- `Remove-Item` を塞ぐロックプロセスの確定