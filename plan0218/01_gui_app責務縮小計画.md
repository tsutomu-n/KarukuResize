# 01: `gui_app.py` 責務縮小計画

## 目的
- `gui_app.py` を「起動・状態管理・イベント配線」に限定する。
- UI構築や文言組み立ての責務を外部モジュールへ移す。

## 対象範囲
- 対象: `src/karuku_resizer/gui_app.py`
- 連携先: `ui_topbar.py` `ui_settings_dialog.py`（既存）+ 新規分割先モジュール

## 実装ステップ
1. `gui_app.py` 内の関数を責務タグで分類する。  
`bootstrap` `state` `event_wiring` `ui_build` `ui_style` `ui_text` `layout`
2. `ui_build` と `layout` を優先抽出する。  
既存イベントハンドラ参照はコールバック注入で維持する。
3. `ui_style` をトークン層へ移し、`gui_app.py` から直接値参照を削除する。
4. `ui_text` を文言層へ移し、`gui_app.py` では表示結果のみ受け取る。
5. `gui_app.py` は以下のみを保持する。  
`main()` `ResizeApp` 初期化 `状態更新` `各分割モジュール呼び出し`

## 完了条件
- `gui_app.py` にUI部品の直接生成が残っていない（最小限の受け口のみ）。
- `gui_app.py` から色値/余白値/固定文言を直接持たない。
- 変更時にUI見た目修正の主編集先が `gui_app.py` 以外になる。

## 目安行数
- 現在約5880行から、最終的に約2000行前後（1800〜2500）を目標。

## 第三者への実行指示
- 1PRで一気にやらず、`ui_build` → `layout` → `style` → `text` の順で段階分割する。
- 各段階で「`gui_app.py` から何が消えたか」を変更ログに明記する。

