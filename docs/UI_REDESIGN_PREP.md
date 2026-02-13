# UI Redesign Prep

大幅なUI変更に入る前の準備メモです。  
目的は、`src/karuku_resizer/gui_app.py` の責務を段階的に分離し、レイアウト変更を安全に行える状態を作ることです。

## 1. 既に実施済みの準備

- ホバー解説文言を `src/karuku_resizer/ui_tooltip_content.py` に集約
- `ResizeApp._setup_tooltips()` は文言データを参照するだけの薄い層へ変更
- セグメント系（簡易/プロ、システム/ライト/ダーク、全件/失敗/未処理）は値単位で解説を付与
- `TooltipManager` は `bind` 非対応ウィジェットでもクラッシュしないよう防御済み

## 2. 次に分離する対象（推奨順）

1. **UI構成情報（ラベル、初期値、選択肢）**
   - まず `gui_app.py` の定数群をUI定数モジュールへ移す
2. **レイアウト構築**
   - `_setup_ui`, `_setup_main_layout`, `_setup_left_panel`, `_setup_right_panel` を `ui/layout_*` へ分割
3. **表示更新ロジック**
   - `_populate_listbox`, `_on_select_change`, `_draw_previews` などをプレゼンテーション層へ寄せる
4. **状態管理**
   - `jobs/current_index/filter/state` を `UIState` 相当へ集約

## 3. 改修時のガイド

- 1回で全部変えず、**表示層だけ**→**状態層**の順で段階的に行う
- 既存機能（一括保存、再帰読込、ドライラン、失敗再試行）の回帰を常に確認
- UI文言は `ui_tooltip_content.py` 側を単一ソースにする

## 4. 最低限の検証コマンド

```bash
uv run ruff check src tests
uv run pytest -q
```

Windowsビルド確認:

```powershell
uv sync --group dev
uv run karukuresize-build-exe
.\dist\KarukuResize.exe
```
