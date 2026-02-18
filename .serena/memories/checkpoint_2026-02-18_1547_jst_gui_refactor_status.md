# KarukuResize checkpoint (JST 2026-02-18 15:47)

## Goal
GUI DRY refactor acceptance close-out. Implementation reached app startup success; remaining bookkeeping is updating acceptance matrix record file.

## KeyDecisions
- Keep `gui_app.py` as orchestrator and move UI responsibilities to `ui_*` modules.
- Prioritize startup recovery with minimal patches when runtime crashes occur.
- Convert watcher registration to callback injection to avoid implicit private-name dependency.
- Treat drag-and-drop as optional: disable safely when runtime widget lacks `drop_target_register`.

## CurrentTask
Session checkpoint creation and memory persistence for fast resume.

## PendingIssues
- `plan0218/09_受け入れ試験マトリクス.md` still has "未取得" lines despite 10 screenshot files existing in `acceptance_shots/`.

## Important constraints
- Primary UI acceptance baseline: 1366x768.
- Required screenshot set: 8 matrix conditions + 2 expanded-window shots (10 files total).
- Keep compatibility on Windows11 runtime.

## Restart paths
- Checkpoint: `./.ai_memory/現状：02月18日15時47分/02月18日15時-まとめ＆作業手順.md`
- Session log: `./.ai_memory/現状：02月18日15時47分/02月18日15時47分-セッションログ.txt`
- Chunk index: `./.ai_memory/現状：02月18日15時47分/chunks/00_index.md`