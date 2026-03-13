# Checkpoint 2026-03-13 13:42 JST
- Goal: Windows 11 上で uv sync / GUI 起動を再現可能にしつつ、主要ダイアログが本体 UI 中央に出る状態を確定する。
- KeyDecisions:
  - 中央配置は src/karuku_resizer/ui/dialog_positioning.py に集約した。
  - 仮想スクリーン座標 (winfo_vrootx/y/width/height) を使って負座標モニタを考慮する。
  - 配置計算失敗時も geometry フォールバックでサイズを維持する。
- CurrentTask: Windows 11 実機で uv sync --group dev --verbose とダイアログ中央配置を確認する前提で、再開資料を保存済み。
- PendingIssues:
  - Windows 実機で中央配置が自然に見えるか未確認。
  - Windows 側 sync-log.txt の実測が未取得。
  - 必要なら位置を少し上寄せするなどの微調整余地がある。
- ImportantConstraints:
  - この環境から会話全文ログは直接取得できないため、.ai_memory/現状：03月13日13時42分/03月13日13時42分-セッションログ.txt は代替ログ。
  - 既存チェックポイント 2026-02-19 16:07 JST は Windows 再起動後の uv sync 再検証を最優先としている。
- RestartSteps:
  1. Windows 11 で clone 後、uv sync --group dev --verbose > sync-log.txt 2>&1
  2. uv run karuku-resizer
  3. 設定 / プリセット管理 / 使い方 / 読込結果 / 一括処理結果 の位置を確認
  4. 必要なら uv run karukuresize-build-exe
- Artifacts:
  - .ai_memory/現状：03月13日13時42分/03月13日13時-まとめ＆作業手順.md
  - .ai_memory/現状：03月13日13時42分/03月13日13時42分-セッションログ.txt
  - .ai_memory/現状：03月13日13時42分/chunks/
