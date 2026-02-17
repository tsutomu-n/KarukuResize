# GUI デザインガイド（開発者向け）

KarukuResize の GUI 実装に関わる開発者向けリファレンス。
コードの実態（`src/karuku_resizer/gui_app.py`）に基づいて記述している。

---

## 1. フレームワーク構成

| 役割 | ライブラリ |
|---|---|
| メイン GUI フレームワーク | `customtkinter >= 5.2.2` |
| ドラッグ&ドロップ | `tkinterdnd2 >= 0.3.0` |
| 画像処理・表示 | `Pillow` (`ImageTk.PhotoImage`, `CTkImage`) |
| アイコン画像 | `customtkinter.CTkImage`（ライト/ダーク PNG ペア） |

`ResizeApp` クラスは `customtkinter.CTk` を継承する。

```python
class ResizeApp(customtkinter.CTk):
    ...
```

---

## 2. カラーシステム（`METALLIC_COLORS`）

全ウィジェットの色は `METALLIC_COLORS` 辞書で一元管理する。
値は `(light_hex, dark_hex)` のタプル形式で、CustomTkinter がテーマに応じて自動選択する。

```python
METALLIC_COLORS = {
    # アクセント
    "primary":       ("#125FAF", "#2F7FC8"),   # プライマリボタン背景
    "hover":         ("#0F4E93", "#286CB0"),   # ホバー時
    "accent_soft":   ("#E8F3FF", "#1E2D40"),   # セカンダリホバー
    "pressed":       ("#0F67C4", "#1F7DCF"),

    # テキスト
    "text_primary":  ("#1F2A37", "#E8EEF5"),
    "text_secondary":("#5B6878", "#A7B4C4"),
    "text_tertiary": ("#7A8696", "#7E8A9A"),

    # 背景
    "bg_primary":    ("#F4F7FB", "#12161D"),   # ウィンドウ背景
    "bg_secondary":  ("#FFFFFF", "#171C24"),   # カード背景
    "bg_tertiary":   ("#EFF4FA", "#202835"),   # セカンダリボタン背景
    "input_bg":      ("#FFFFFF", "#111723"),   # 入力フィールド

    # ボーダー
    "border_light":  ("#D9E2EC", "#2A3340"),
    "border_medium": ("#CBD5E1", "#334155"),

    # ステータス
    "success":       ("#2E8B57", "#3CA66A"),
    "warning":       ("#C97A00", "#EF9A1A"),
    "error":         ("#CC3344", "#E25A68"),

    # キャンバス
    "canvas_bg":     ("#EEF3FA", "#111722"),
}
```

新しいウィジェットを追加する際は、必ず `METALLIC_COLORS` から色を参照すること。
ハードコードした色値は使用しない。

---

## 3. ボタンスタイル

ボタンは用途に応じて 2 種類のスタイルメソッドで統一する。

### Primary（主要アクション）

```python
def _style_primary_button(self, button: customtkinter.CTkButton) -> None:
    button.configure(
        fg_color=METALLIC_COLORS["primary"],
        hover_color=METALLIC_COLORS["hover"],
        text_color=METALLIC_COLORS["text_primary"],
        corner_radius=10,
        border_width=0,
    )
```

**使用箇所**: 画像を選択、プレビュー、保存、一括適用保存

### Secondary（補助アクション）

```python
def _style_secondary_button(self, button: customtkinter.CTkButton) -> None:
    button.configure(
        fg_color=METALLIC_COLORS["bg_tertiary"],
        hover_color=METALLIC_COLORS["accent_soft"],
        text_color=METALLIC_COLORS["text_primary"],
        border_width=1,
        border_color=METALLIC_COLORS["border_light"],
        corner_radius=10,
    )
```

**使用箇所**: 設定、キャンセル、各種ダイアログのアクションボタン

### カードフレーム

パネルやコンテナには `_style_card_frame` を使用する。

```python
def _style_card_frame(self, frame: customtkinter.CTkFrame, corner_radius: int = 12) -> None:
    frame.configure(
        fg_color=METALLIC_COLORS["bg_secondary"],
        border_width=1,
        border_color=METALLIC_COLORS["border_light"],
        corner_radius=corner_radius,
    )
```

---

## 4. フォントシステム

### フォントオブジェクト

| 変数 | 用途 | 通常サイズ | 大きめサイズ |
|---|---|---|---|
| `self.font_default` | 標準テキスト | 16px | 18px |
| `self.font_small` | 補助テキスト・小ラベル | 14px | 16px |
| `self.font_bold` | 強調テキスト | 16px bold | 18px bold |

### フォントファミリー優先順（Windows）

1. BIZ UDPGothic（`assets/fonts/` に同梱、なければシステムから検索）
2. Yu Gothic / Yu Gothic UI
3. Meiryo / MS PGothic
4. Segoe UI（最終フォールバック）

### フォントファミリー優先順（macOS / Linux）

1. SF Pro Display
2. Hiragino Kaku Gothic ProN / Pro
3. Yu Gothic / Meiryo

フォント解決は `_resolve_system_font_family()` が担当する。
`customtkinter.set_widget_scaling(scale)` でウィジェット全体のスケールも同時に適用される。

---

## 5. スケーリングシステム

### UI スケールモード

| モード ID | ラベル | スケール係数 |
|---|---|---|
| `normal` | 通常 | 1.0 |
| `large` | 大きめ | 1.125 |

スケール係数は `UI_SCALE_FACTORS` 辞書で管理する。

### スケール適用メソッド

```python
def _scale_px(self, value: int) -> int:
    """px 値をスケール係数で変換する"""
    return max(1, round(value * self._ui_scale_factor))

def _scale_pad(self, value: Any) -> Any:
    """padding タプル/スカラーをスケール変換する"""
```

**ルール**: レイアウト内のすべての `padx`/`pady`/`width` は `_scale_px()` または `_scale_pad()` を通すこと。ハードコードした px 値は使用しない。

---

## 6. アイコンシステム

### ファイル構成

```
assets/icons/
  light/<name>_<size>.png   # ライトテーマ用
  dark/<name>_<size>.png    # ダークテーマ用
```

### 読み込み

`icon_loader.py` の `load_icon()` を使用する。結果は `lru_cache` でキャッシュされる。

```python
from karuku_resizer.icon_loader import load_icon

icon = load_icon("folder", 16)   # → CTkImage | None
```

- 見つからない場合は `None` を返す（ボタンはテキストのみで表示される）
- PyInstaller ビルド時は `sys._MEIPASS` を優先して探索する

### 現在使用中のアイコン

| 変数名 | アイコン名 | 使用箇所 |
|---|---|---|
| `_icon_folder` | `folder` | 画像を選択ボタン |
| `_icon_circle_help` | `circle-help` | 使い方ボタン |
| `_icon_settings` | `settings` | 設定ボタン |
| `_icon_folder_open` | `folder-open` | 一括適用保存ボタン |
| `_icon_refresh` | `refresh-cw` | プレビューボタン |
| `_icon_save` | `save` | 保存ボタン |

新しいアイコンを追加する場合は `assets/icons/light/` と `assets/icons/dark/` の両方に PNG を配置し、`_setup_ui_icons()` に追記する。

---

## 7. レイアウト構造

```
ResizeApp (CTk)
├── top_container (CTkFrame / card)        ← トップバー全体
│   ├── top_guide_frame                    ← ガイドラベル（状態依存で表示/非表示）
│   ├── top_row_primary                    ← 第1行: 選択・サイズ指定・プリセット・設定
│   └── top_row_secondary (action_controls)← 第2行: プレビュー・保存・一括保存・ズーム
├── settings_header_frame (CTkFrame / card)← 設定サマリー + 詳細設定トグル + モード切替
├── progress_bar                           ← 処理中のみ表示
├── main_content (CTkFrame)                ← 左右分割エリア
│   ├── left_panel                         ← ファイルリスト
│   └── right_panel (preview_pane)         ← プレビュー（オリジナル + リサイズ後）
├── session_summary_label                  ← セッション統計（下部）
├── action_hint_label                      ← 操作ガイド（下部）
└── status_bar                             ← ステータス（最下部）
```

### トップバー密度（Responsive）

ウィンドウ幅が `TOPBAR_DENSITY_COMPACT_MAX_WIDTH = 1310px` 以下になると `compact` モードに切り替わり、ボタン幅が縮小される。

```python
TOPBAR_WIDTHS = {
    "normal":  {"select": 128, "preview": 118, "save": 118, "batch": 118, ...},
    "compact": {"select": 118, "preview": 108, "save":  96, "batch": 106, ...},
}
```

`_apply_topbar_density()` が `<Configure>` イベントで呼ばれ、幅を動的に更新する。

---

## 8. テーマ・外観モード

CustomTkinter の外観モードを `customtkinter.set_appearance_mode()` で制御する。

| モード ID | ラベル | 動作 |
|---|---|---|
| `system` | OSに従う | OS のダーク/ライト設定に追従 |
| `light` | ライト | 強制ライト |
| `dark` | ダーク | 強制ダーク |

初期値は `system`。設定ダイアログで変更可能。

キャンバス背景色はテーマ変更時に `_canvas_background_color()` で再取得して手動更新が必要（`CTkCanvas` は自動追従しないため）。

---

## 9. ツールチップ

`TooltipManager`（`tooltip_manager.py`）でホバー説明を管理する。

```python
# 登録
self._register_tooltip(widget, "説明テキスト")

# セグメントボタンの各値に個別登録
self._register_segmented_value_tooltips(segmented_button, {
    "値A": "説明A",
    "値B": "説明B",
})
```

- 表示遅延: `TOOLTIP_DELAY_MS = 400ms`
- 設定の「ホバー説明」で全体オン/オフ可能
- モーダルダイアログが開いている間は無効化される

---

## 10. キーボードショートカット

| ショートカット | 動作 |
|---|---|
| `Ctrl+P` | プレビュー |
| `Ctrl+S` | 保存 |
| `Ctrl+Shift+S` | 一括適用保存 |

モーダルダイアログ（設定・プリセット管理・結果）が開いている間は無効化される（`_is_modal_dialog_open()` で判定）。

---

## 11. ガイドラベルの状態管理

トップバーのガイドラベル（`top_action_guide_label`）は状態に応じて表示/非表示を切り替える。

| 状態 | 表示内容 |
|---|---|
| 画像未読込 | `{モード}モード — 画像を選択またはドラッグ&ドロップして開始` |
| ファイル読込中 | `画像読み込み中…` |
| 処理実行中 | `処理中 — キャンセル以外の操作はできません` |
| 画像読込済み | 非表示（`pack_forget()`） |

`_refresh_top_action_guide()` を呼び出すと状態に応じて自動更新される。

---

## 12. 設定サマリー

`settings_header_frame` 内の `settings_summary_label` に現在の設定を1行で表示する。

**表示形式**: `現在設定: {モード} / 形式:{形式} / Q{品質} / EXIF:{モード}[ (GPS:OFF)][ / ドライラン:ON]`

- カラーテーマ・文字サイズは表示しない（設定ダイアログで管理）
- GPS削除がONの場合のみ `(GPS:OFF)` を付加
- ドライランがONの場合のみ `ドライラン:ON` を付加
- WEBP/AVIF のコーデック詳細はプロモード時のみ付加

`_update_settings_summary()` を呼び出すと更新される。

---

## 13. プリセットメニューのコールバック制御

プリセットドロップダウン（`CTkOptionMenu`）は選択時に自動適用するが、
初期化時の `preset_var.set()` でコールバックが誤発火しないよう抑制フラグを使用する。

```python
self._suppress_preset_menu_callback = True   # 初期化開始
# ... preset_var.set() などの初期化処理 ...
self._suppress_preset_menu_callback = False  # 初期化完了

def _on_preset_menu_changed(self, _value: str) -> None:
    if self._suppress_preset_menu_callback:
        return
    # 自動適用処理
```

`preset_var.set()` を直接呼ばず、必ず `_set_selected_preset_label()` を経由すること。
このメソッドが内部でフラグを一時的に立てて誤発火を防ぐ。

---

## 14. 新しいウィジェットを追加する際のチェックリスト

1. **色**: `METALLIC_COLORS` から参照する
2. **フォント**: `self.font_default` / `self.font_small` / `self.font_bold` を使用する
3. **サイズ**: `self._scale_px()` / `self._scale_pad()` を通す
4. **ボタン**: `_style_primary_button()` または `_style_secondary_button()` を適用する
5. **フレーム**: カード型なら `_style_card_frame()` を適用する
6. **ツールチップ**: `self._register_tooltip(widget, "説明")` を追加する
7. **インタラクティブ制御**: 処理中に無効化が必要なら `_set_interactive_controls_enabled()` のリストに追加する
8. **密度対応**: トップバーに追加する場合は `TOPBAR_WIDTHS` と `_apply_topbar_density()` を更新する
