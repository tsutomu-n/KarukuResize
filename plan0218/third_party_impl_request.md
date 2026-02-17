# KarukuResize 第三者実装依頼テンプレート

最終更新: 2026-02-18  
ステータス: 実装着手可（追加調査不要）

## 1. 依頼目的

`src/karuku_resizer/gui_app.py` に集中している UI 構築責務を分離し、上部UIの余白過多を解消する。  
対象は `topbar` と `settings dialog` の先行分割。

## 2. 固定要件（変更不可）

1. 主基準は `1366x768` で評価する。  
2. 補助確認は固定 `1920x1080` ではなく「可変拡大」で行う。  
3. Pro OFF では `プリセット` と `一括保存` を非表示にする。  
4. 通常時はガイド非表示。`loading/processing/error` 等の状態時のみ表示。  
5. 低頻度操作（使い方/プリセット管理/拡大率）は設定ダイアログ側導線で維持する。  

## 3. 参照資料（必読）

1. 計画書  
`/home/tn/projects/KarukuResize/.memo/ui-ux-improvement-plan.md`
2. 基準モック（サイズ確認用）  
`/home/tn/projects/KarukuResize/.memo/current_ui_mock_rulecheck_baseline_sizes.html`
3. 基準モック（コンパクト上部）  
`/home/tn/projects/KarukuResize/.memo/current_ui_mock_rulecheck_compact_topbar.html`

## 4. 実装スコープ

1. 新規作成  
`src/karuku_resizer/ui_topbar.py`
2. 新規作成  
`src/karuku_resizer/ui_settings_dialog.py`
3. 既存改修  
`src/karuku_resizer/gui_app.py`

## 5. 実装方針

1. `gui_app.py` は状態保持とイベント配線中心にする。  
2. Topbar 構築と更新ロジックは `ui_topbar.py` に移譲する。  
3. Settings Dialog 構築は `ui_settings_dialog.py` に移譲する。  
4. 既存設定キー互換（例: `ui_mode`, `zoom_preference`）を維持する。  
5. Topbar は余白制御がしやすい構造にし、通常時は主操作1段 + サマリー1段を目標にする。  

## 6. 実装手順（順序厳守）

1. フェーズA: Topbar分割  
`_setup_ui` の topbar 構築ロジックを `ui_topbar.py` へ抽出。  
既存ハンドラ参照は `gui_app.py` 側が注入する方式にする。

2. フェーズB: Settings Dialog分割  
`_open_settings_dialog` 周辺を `ui_settings_dialog.py` に移す。  
設定保存・即時反映の動作を維持する。

3. フェーズC: 表示密度調整  
上部余白とパディングを基準モックに寄せる。  
Pro OFF/ON の表示差分を固定する。

4. フェーズD: 回帰検証  
静的検証 + テスト + 実機スクショ比較を実施する。

## 7. 完了条件（Definition of Done）

1. `ruff` / `pytest` / `basedpyright` が全通。  
2. `1366x768` で上部余白が過大でない。  
3. 可変拡大で見切れや破綻がない。  
4. Pro OFF/ON 切替時の表示ルールが要件どおり。  
5. 設定保存・復元が既存互換を維持。  

## 8. 実行コマンド（Windows PowerShell）

```powershell
cd C:\Users\tn\d-projects\KarukuResize
uv sync
uv run ruff check src tests
uv run pytest -q
uvx basedpyright src
uv run python -m karuku_resizer.gui_app
```

## 9. 提出物

1. 変更ファイル一覧。  
2. 変更要約（各ファイル1〜3行）。  
3. 検証結果ログ要約（ruff/pytest/basedpyright）。  
4. スクショ2枚以上。  
`1366x768` 主基準。  
可変拡大補助確認。  
5. 残課題があれば箇条書きで明示。  

## 10. 注意点（実装時）

1. 既存未関連の挙動は変更しない。  
2. 文字列ラベルを変更する場合は、設定保存との整合を確認する。  
3. 同一親で `pack` と `grid` を混在させない。  
4. 段階ごとに小さくコミット可能な差分で進める。  

## 11. 実装依頼メッセージ（そのまま利用可）

```text
KarukuResize の UI/UX 改修をお願いします。

参照:
- .memo/ui-ux-improvement-plan.md
- .memo/current_ui_mock_rulecheck_baseline_sizes.html
- .memo/current_ui_mock_rulecheck_compact_topbar.html

要件:
1) topbar と settings dialog を先に分割
2) Pro OFF でプリセット/一括保存を非表示
3) 通常時ガイド非表示、状態時のみ表示
4) 主基準 1366x768、補助は可変拡大
5) 既存設定キー互換を維持

対象:
- src/karuku_resizer/gui_app.py
- src/karuku_resizer/ui_topbar.py (new)
- src/karuku_resizer/ui_settings_dialog.py (new)

完了条件:
- ruff/pytest/basedpyright 全通
- スクショ比較で上部余白が改善
```
