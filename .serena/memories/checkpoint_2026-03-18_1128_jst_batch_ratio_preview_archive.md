# KarukuResize checkpoint 2026-03-18 11:28 JST

- Goal:
  - Keep KarukuResize GUI mainline in a clean state with correct per-image batch resize behavior, preview size feedback (`推定 -> 高精度`), and archived legacy paths.

- KeyDecisions:
  - Batch save uses `ResizePlan` per image instead of fixed `reference_target` for every file.
  - `auto` output format is resolved per image during batch save.
  - Preview size display is two-stage: fast estimate first, then high-precision estimate using `estimate_output_size_kb()`.
  - Preview high-precision estimate shares save payload preparation with `save_image()`.
  - Unreferenced legacy modules were moved to `archive/legacy_karukuresize/`.

- CurrentTask:
  - Code and tests are complete; next step is Windows real-GUI verification.

- PendingIssues:
  - Verify mixed portrait/landscape batch save in Windows GUI.
  - Verify `推定 -> 高精度` preview transition feels natural.
  - Optionally verify EXE build/startup after archive cleanup.

- Constraints:
  - Full raw chat log was not accessible from the CLI environment; a summarized substitute log was stored under `.ai_memory`.
  - Windows GUI is not directly controllable from this environment.

- Restart:
  1. Open `./.ai_memory/現状：03月18日11時28分/03月18日11時-まとめ＆作業手順.md`
  2. Run `uv run karuku-resizer`
  3. Test preview/save/batch-save on mixed inputs

- Artifacts:
  - `./.ai_memory/現状：03月18日11時28分/03月18日11時-まとめ＆作業手順.md`
  - `./.ai_memory/現状：03月18日11時28分/03月18日11時28分-セッションログ.txt`
  - `./archive/legacy_karukuresize/README.md`
