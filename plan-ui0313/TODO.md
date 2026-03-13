# UI TODO

`plan-ui0313/iken.md` の未完了項目から、次に着手すべき実装だけを優先順に抜き出した短縮版。

## 進める順

1. 実機確認後の余白・高さバランス微調整

## Task 1: 設定ダイアログのカテゴリ分割

- [x] `ui_settings_dialog.py` を「基本」「出力」「高度な設定」単位に再構成する
- [x] `ヘルプ/管理` の位置をカテゴリ境界に合わせて整理する
- [x] 既存の設定値読み書きロジックを壊さない

対象ファイル:
- `src/karuku_resizer/ui_settings_dialog.py`
- 必要なら `src/karuku_resizer/gui_app.py`

完了条件:
- ダイアログを開いたとき、設定項目の塊が明確に分かれる
- `ヘルプ/管理` が唐突な位置に見えない
- 既存設定の保存/反映がそのまま動く

## Task 2: TopBar のセパレータ導入とレイアウト整理

- [x] TopBar を `Input / Parameter / Output` の3群に視覚分離する
- [x] 群の間に軽いセパレータまたは十分な余白を入れる
- [x] `最近使った設定` と `詳細設定を隠す` の位置関係を見直す

対象ファイル:
- `src/karuku_resizer/ui_topbar.py`
- `src/karuku_resizer/ui_detail_controls.py`
- 必要なら `src/karuku_resizer/ui_theme_tokens.py`

完了条件:
- TopBar を見た瞬間に「選択」「設定」「実行」の塊が分かる
- ボタンや入力欄がひとかたまりに見えず、群として認識できる
- compact 時も破綻しない

## Task 3: ダイアログ内ボタンの危険度別配色整理

- [x] 設定ダイアログの主要操作を `Primary / Secondary / Tertiary` へ整理する
- [x] プリセット管理ダイアログの `削除` を危険色へ分離する
- [x] `閉じる` は非強調の安全アクションとして揃える

対象ファイル:
- `src/karuku_resizer/ui_settings_dialog.py`
- `src/karuku_resizer/ui/preset_dialog.py`
- 必要なら `src/karuku_resizer/ui_bootstrap.py`

完了条件:
- `保存/適用` と `閉じる` の優先度差が色で一目で分かる
- `削除` が他ボタンと誤認されない
- 既存の配色方針と矛盾しない

## Task 4: 横幅/compact モード再設計

- [x] `MIN_WINDOW_WIDTH` と `window_geometry` の既定値を再検討する
- [x] `TOPBAR_DENSITY_COMPACT_MAX_WIDTH` の閾値を見直す
- [x] 狭い幅でラベル省略、広い幅で完全表示の方針を明文化する

対象ファイル:
- `src/karuku_resizer/gui_app.py`
- `src/karuku_resizer/gui_settings_store.py`
- `src/karuku_resizer/ui_display_policy.py`
- `src/karuku_resizer/ui_theme_tokens.py`

完了条件:
- 125%〜150% スケーリングでも主要ボタンが画面外に消えない
- compact / normal の切替が見た目にも自然
- `一括保存` のような短縮ラベル方針が他要素にも一貫して適用できる

## Next Candidate: プリセット管理ダイアログの `key: value` グリッド化

- [x] 中央の情報ダンプを `key: value` の整列表現へ置き換える
- [x] `種別 / ID / サイズ / 形式 / 品質 / EXIF / GPS / ドライラン / 更新日時` を個別行に分解する
- [x] 情報表示とアクションボタンの距離感を整理する

対象ファイル:
- `src/karuku_resizer/ui/preset_dialog.py`

完了条件:
- 現在のプリセット情報が一読で把握できる
- 長文ダンプを追わなくても主要値を見つけられる
- 既存の更新/削除/適用ロジックはそのまま動く

## メモ

- すでに完了済み:
  - メタデータの左カラム移設
  - WEBP / AVIF 設定の近接化
  - 状態サマリー削除
  - ステータスバーの大枠整理
  - `一括適用保存` の見切れ対策
  - `customtkinter` の配色ルールを `karuku_metallic_theme.json` へ集約
  - 読込結果/一括処理結果ダイアログを `要約 + 件数メトリクス + 補足 + 失敗詳細` 構成へ再設計
- 詳細な実装状況は `plan-ui0313/iken.md` を正本として参照する
