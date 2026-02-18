# 08: Tkinter実装規約

## 目的
- Tkinter固有の破綻ポイントを事前に潰し、第三者実装の事故率を下げる。

## レイアウト規約
1. 同一親コンテナで `pack` と `grid` を混在させない。  
2. `grid` 利用時は `rowconfigure/columnconfigure(weight=...)` を必ず設定する。  
3. 可変拡大時の見切れ回避のため、密度判定はスケール補正後幅で行う。  
4. 非表示化はコンテナ単位で行い、断片Widgetだけを隠して段崩れを起こさない。

## スタイル規約
1. 色/余白/フォントは `ui_theme_tokens.py` のみを参照する。  
2. `ttk.Style` の定義は一箇所で行い、画面モジュールで重複定義しない。  
3. Light/Dark切替時、コントラスト低下を起こす配色は禁止。  
4. 文字サイズ切替は `通常` と `大きめ` を明示し、内部倍率値をUI表示しない。

## スレッド規約
1. TkinterのUI操作はメインスレッドのみ。  
2. バックグラウンド結果の反映は `after()` 経由に統一する。  
3. 処理中状態（loading/processing/error）は状態モデルで管理し、直接Widget乱更新をしない。

## モード規約
1. Pro OFFで `プリセット` と `一括保存` を非表示。  
2. 通常時ガイドは非表示。状態時のみ表示。  
3. EXIF/GPS表現は仕様で合意した単一フォーマットを維持する。

## 完了条件
1. 規約違反がレビュー観点として明文化されている。  
2. 1366x768主基準で上部余白と密度が安定する。  
3. 可変拡大でも見切れ・重なり・操作不能が発生しない。

## 参照（一次情報）
1. TkDocs Grid: https://tkdocs.com/tutorial/grid.html  
2. TkDocs Complex Interfaces: https://tkdocs.com/tutorial/complex.html  
3. Tcl/Tk grid manual: https://www.tcl-lang.org/man/tcl8.6/TkCmd/grid.htm  
4. Tcl/Tk pack manual: https://www.tcl-lang.org/man/tcl8.6/TkCmd/pack.htm  
5. Python tkinter docs: https://docs.python.org/3/library/tkinter.html  
6. Python tkinter.ttk docs: https://docs.python.org/3/library/tkinter.ttk.html

