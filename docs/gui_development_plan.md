# 画像処理ツール GUI化計画書

## 1. 目的

既存のコマンドライン画像処理ツール (`resize_images.py`) の機能をGUIで利用できるようにする。
ユーザーがより直感的に操作できるようにし、ツールの利便性を向上させる。
既存の `resize_images_gui.py` は無視し、ゼロベースで開発する。

## 2. 設計原則

*   **クラスベース設計**: アプリケーションのメインウィンドウは `customtkinter.CTk` を継承し、UIの主要なセクション（各タブのコンテナなど）は `customtkinter.CTkFrame` を継承したクラスとして実装する。これにより、コードの構造化、可読性、再利用性を向上させる。
    *   参考: [CustomTkinter Wiki - App structure and layout](https://github.com/TomSchimansky/CustomTkinter/wiki/App-structure-and-layout)
*   **レイアウト管理**: ウィジェットの配置には主に `.grid()` を使用する。複雑なレイアウトや動的な変更に対応しやすいため。`.pack()` は非常にシンプルな場合に限定し、`.place()` は原則として使用しない。
    *   参考: 同上
*   **スタイリング**: CustomTkinterのテーマ機能 (`customtkinter.set_appearance_mode()`, `customtkinter.set_default_color_theme()`) を活用する。必要に応じてカスタムテーマJSONファイルを作成し、`ui_simulation_v2.html` のデザインに近づける。
    *   参考: [CustomTkinter Wiki - Themes](https://github.com/TomSchimansky/CustomTkinter/wiki/Themes)
    *   テーマパック例: [a13xe/CTkThemesPack](https://github.com/a13xe/CTkThemesPack)
*   **イベント処理**: コールバック関数は簡潔に保ち、複雑なロジックは専用のメソッドやクラスに分離する。
*   **コードの可読性**: 適切なコメント、一貫した命名規則、マジックナンバーの排除を心がける。

## 3. 基本レイアウトと機能 (ui_simulation_v2.html ベースに改訂)

### 3.1. メインウィンドウ構成

*   **ウィンドウタイトル**: 「画像処理ツール v2 (仮)」
*   **タブビュー (`customtkinter.CTkTabview`)**: 以下の3つのタブで構成。
    *   「Basic Settings」タブ (デフォルトでアクティブ)
    *   「Advanced Settings」タブ
    *   「Log」タブ

### 3.2. 「Basic Settings」タブ

#### 3.2.1. ディレクトリ設定エリア

*   **セクションタイトル**: 「Directory Settings」 (`customtkinter.CTkLabel`)
*   **グリッドレイアウト (`.form-grid`)**: ソースと出力の選択ボタンを横並びに配置。
*   **ソースディレクトリ選択**:
    *   ボタン (`customtkinter.CTkButton`): アイコン (`folder-open`) とテキスト「Source Directory」。クリックで `filedialog.askdirectory` を呼び出し、結果を内部変数に保持。
        *   **注意**: アイコン表示は `CTkImage` と画像ファイル (例: `.png`) を使用するか、`CTkFont` とアイコンフォント文字で対応。`CTkButton` の `image` プロパティに `CTkImage` オブジェクトを指定。
    *   選択パス表示: ボタンの下や別の場所に `customtkinter.CTkLabel` で表示 (動的更新)。
*   **出力ディレクトリ選択**:
    *   ボタン (`customtkinter.CTkButton`): アイコン (`folder-plus`) とテキスト「Output Directory」。クリックで `filedialog.askdirectory` を呼び出し、結果を内部変数に保持。
        *   **アイコン**: 同上。
    *   選択パス表示: 同上。
*   **出力ディレクトリ自動作成スイッチ (`customtkinter.CTkSwitch`)**:
    *   ラベル「Create if not exists」を右側に配置。
    *   デフォルトON。

#### 3.2.2. 画像設定エリア

*   **セクションタイトル**: 「Image Settings」 (`customtkinter.CTkLabel`)
*   **グリッドレイアウト (`.form-grid`)**: 幅と高さを横並びに配置。
*   **リサイズ後の幅 (`customtkinter.CTkEntry`)**:
    *   ラベル「Width (px)」。
    *   数値入力、デフォルト値 800。
    *   入力変更時にアスペクト比維持ロジックと連携。
*   **リサイズ後の高さ (`customtkinter.CTkEntry`)**:
    *   ラベル「Height (px)」。
    *   数値入力、デフォルト値 800。
    *   入力変更時にアスペクト比維持ロジックと連携。
*   **アスペクト比維持チェックボックス (`customtkinter.CTkCheckBox`)**:
    *   ラベル「<i class="fas fa-lock"></i> Maintain aspect ratio」 (アイコンは画像かフォントで)。
        *   **アイコン**: `CTkImage` を使用。鍵の画像ファイルを準備する。
    *   デフォルトON。
    *   チェック状態変更で幅/高さ入力の挙動を制御。

#### 3.2.3. 処理開始ボタン

*   **処理開始ボタン (`customtkinter.CTkButton`)**: テキスト「Start Processing」。
    *   ウィンドウ幅いっぱいに広がるスタイル。
    *   クリックで設定値を取得し、バリデーション後、処理スレッドを開始。
    *   処理中は無効化。

### 3.3. 「Advanced Settings」タブ

#### 3.3.1. ファイル名変更ルール (アコーディオン形式)

*   **アコーディオンヘッダー (`customtkinter.CTkFrame` + `customtkinter.CTkButton` or `CTkLabel`)**:
    *   アイコン (`chevron-right` / `chevron-down` の画像) とタイトル「File Renaming Rules」。
    *   クリックでコンテンツの表示/非表示を切り替え。`CTkButton` の `command` に切り替え用メソッドを紐付ける。
*   **アコーディオンコンテンツ (`customtkinter.CTkFrame`)**: デフォルトで表示。表示/非表示は `.grid()` / `.grid_remove()` または `.pack()` / `.pack_forget()` で制御。
    *   **接頭辞 (`customtkinter.CTkEntry`)**: ラベル「Prefix」。
    *   **ナンバリング**: ラベル「Numbering」。
        *   開始番号 (`customtkinter.CTkEntry`): 数値入力、デフォルト値 1。
        *   桁数 (`customtkinter.CTkEntry`): 数値入力、デフォルト値 3。
    *   **既存ファイルがある場合 (`customtkinter.CTkComboBox`)**: ラベル「If file exists」。
        *   オプション: 「上書き」「スキップ」「新しい名前で保存 (連番など)」
        *   選択に応じてプレビュー表示を更新。
    *   **プレビュー表示 (`customtkinter.CTkLabel`)**: ラベル「Preview:」、動的に生成されたファイル名例を表示。

### 3.4. 「Log」タブ

#### 3.4.1. ログコントロール

*   **フィルターボタン (`customtkinter.CTkSegmentedButton` または複数の `CTkButton`)**: 「All」「Success」「Error」。
    *   クリックで表示するログエントリをフィルタリング。

#### 3.4.2. ログ表示エリア

*   **スクロール可能なフレーム (`customtkinter.CTkScrollableFrame`)**: ログエントリをここに動的に追加。
    *   参考: [CustomTkinter Wiki - CTkScrollableFrame](https://github.com/TomSchimansky/CustomTkinter/wiki/CTkScrollableFrame)
    *   参考: [scrollable_frame_example.py](https://github.com/TomSchimansky/CustomTkinter/blob/master/examples/scrollable_frame_example.py)
*   **ログエントリの形式 (各行)**: `CTkFrame` をコンテナとし、その中に以下のウィジェットを配置。
    *   ファイル名 (`customtkinter.CTkLabel`)
    *   進捗バー (`customtkinter.CTkProgressBar`): 処理中のファイルに表示。
    *   ステータス (`customtkinter.CTkLabel`): 「Success」「Error」など、色分け表示。

### 3.5. 削除または変更される既存計画項目

*   旧「3.2. 基本オプション要素 (必須)」のドライラン、処理再開は新UI案にないため、一旦削除または「Advanced Settings」に移動検討。
*   旧「3.4. 表示要素 (必須)」の処理結果サマリーは、「Log」タブの最終行や別途ダイアログで表示検討。
*   旧「4. 画面構成案」は全面的に新しい構成に置き換え。

## 4. 実装フェーズとタスク (ui_simulation_v2.html ベース)

### フェーズ 1: 基本ウィンドウとタブ構造、Basic Settings タブの静的配置

1.  **メインウィンドウとタブのセットアップ:**
    *   [ ] `resize_images_gui.py` を新規作成または初期化。
    *   [ ] `App` クラスを作成し、`customtkinter.CTk` を継承またはインスタンス化。クラスベースの設計を意識する。
    *   [ ] ウィンドウタイトル、初期サイズ (例: 800x700) を設定。
    *   [ ] `customtkinter.set_appearance_mode("System")` や `customtkinter.set_default_color_theme("blue")` などで基本的なテーマを設定。
    *   [ ] `CTkTabview` を作成し、3つのタブ（`basic_settings_tab`, `advanced_settings_tab`, `log_tab`）を追加。
        *   参考: [CustomTkinter Wiki - CTkTabview](https://github.com/TomSchimansky/CustomTkinter/wiki/CTkTabview)
2.  **Basic Settings - ディレクトリ設定UIの配置:**
    *   [ ] `basic_settings_tab` 内に「Directory Settings」セクション用の `CTkFrame` を配置。
    *   [ ] ソース/出力ディレクトリ選択ボタン (`CTkButton`) を配置。スタイルは `ui_simulation_v2.html` を参考に。アイコンは `CTkImage` を使用して設定。
    *   [ ] 現時点ではクリック時の動作は `print("Button clicked")` などでOK。
3.  **Basic Settings - 画像設定UIの配置:**
    *   [ ] `basic_settings_tab` 内に「Image Settings」セクション用の `CTkFrame` を配置。
    *   [ ] 幅/高さ入力用の `CTkEntry` とラベルを配置。
    *   [ ] 「Maintain aspect ratio」チェックボックス (`CTkCheckBox`) とラベルを配置。
4.  **Basic Settings - 処理開始ボタンの配置:**
    *   [ ] `basic_settings_tab` の下部に「Start Processing」ボタン (`CTkButton`) を配置。

### フェーズ 2: Advanced Settings タブと Log タブの静的配置、アコーディオン実装

5.  **Advanced Settings - ファイル名変更ルールUIの配置:**
    *   [ ] `advanced_settings_tab` 内にアコーディオンヘッダー用の `CTkFrame` と `CTkButton` (または `CTkLabel`) を配置。
    *   [ ] ヘッダークリックで表示/非表示が切り替わるコンテンツ用 `CTkFrame` を配置 (アコーディオンロジック実装)。`.grid()` / `.grid_remove()` を使用して表示状態を制御。
    *   [ ] コンテンツ内に接頭辞、ナンバリング、既存ファイル処理の各 `CTkEntry`, `CTkLabel`, `CTkComboBox` を配置。
    *   [ ] プレビュー用 `CTkLabel` を配置。
6.  **Log タブ - UIの配置:**
    *   [ ] `log_tab` 内にフィルターボタン (`CTkSegmentedButton` または複数の `CTkButton`) を配置。
    *   [ ] `CTkScrollableFrame` をログ表示エリアとして配置。
    *   [ ] 初期メッセージ用 `CTkLabel` を `CTkScrollableFrame` 内に配置。

### フェーズ 3: UI要素の基本的な対話機能と設定値の取得

7.  **ディレクトリ選択ダイアログの実装:**
    *   [ ] ソース/出力ディレクトリボタンクリックで `filedialog.askdirectory` を呼び出し、選択されたパスをコンソールに出力する。
    *   [ ] (オプション) 選択パスを保持するインスタンス変数を準備。
8.  **タブ切り替え機能の確認:**
    *   [ ] `CTkTabview` が正しく機能し、タブをクリックすると対応するコンテンツが表示されることを確認。
9.  **アコーディオン機能の実装:**
    *   [ ] 「File Renaming Rules」ヘッダークリックで、コンテンツフレームの表示/非表示が切り替わるようにする。
    *   [ ] アイコンの向きも変更する (例: `▶` から `▼`)。
10. **設定値取得関数の準備:**
    *   [ ] 「Start Processing」ボタンクリック時に、Basic Settings および Advanced Settings の各UI要素から現在の設定値を取得し、辞書などにまとめてコンソールに出力するダミー関数を作成。
    *   [ ] 数値入力のバリデーション (空でないか、数値かなど) を簡単に追加。

### フェーズ 4: コアロジック (`resize_core.py`) との連携、ログ表示の基本

11. **画像処理スレッドの準備:**
    *   [ ] `threading.Thread` を使用して、画像処理をバックグラウンドで実行する準備。
    *   [ ] GUIがフリーズしないように、処理ロジックはワーカースレッドで実行する。
12. **`resize_core.py` の関数呼び出し:**
    *   [ ] 取得した設定値を元に、ワーカースレッド内から `resize_core.py` の主要な処理関数を呼び出す。
    *   [ ] `resize_core.py` が進捗やログ情報をコールバック関数やキュー経由でGUIに渡せるように改修検討。
13. **基本的なログ出力の実装:**
    *   [ ] 処理スレッドからのメッセージ (例: 「処理開始」「ファイルXを処理中」「完了」) を `CTkScrollableFrame` に `CTkLabel` として追加していく。新しいログエントリ用の `CTkFrame` を作成し、その中に `CTkLabel` などを配置して `CTkScrollableFrame` に `.grid()` または `.pack()` で追加。
    *   [ ] スクロールフレームが自動で最下部にスクロールするようにする (`CTkScrollableFrame._parent_canvas.yview_moveto(1.0)` など)。
14. **処理開始/終了時のUI制御:**
    *   [ ] 処理開始時に「Start Processing」ボタンを無効化。
    *   [ ] 処理終了時にボタンを再度有効化。
    *   [ ] Logタブに自動で切り替える (ユーザビリティ向上のため)。

### フェーズ 5: 動的UI更新 (進捗バー、プレビュー等) と詳細機能

15. **ファイルごとの進捗表示 (Logタブ):**
    *   [ ] 処理中のファイルに対して `CTkProgressBar` をログエントリ内に追加し、進捗を更新。不要になったら `.destroy()` するか、値を1.0にして非表示にする。
    *   [ ] 処理完了後、プログレスバーを削除し、ステータスラベル (Success/Error) に置き換える。
16. **ログフィルター機能の実装:**
    *   [ ] フィルターボタンクリックで、ログエントリの表示/非表示を切り替える。
17. **アスペクト比維持ロジックの実装:**
    *   [ ] 幅または高さの `CTkEntry` の値が変更された際、「Maintain aspect ratio」がチェックされていれば、もう一方の値を自動計算して更新。
18. **ファイル名プレビューの動的更新:**
    *   [ ] ファイル名変更ルールの設定値が変更された際に、プレビュー用 `CTkLabel` の内容を更新。
19. **エラーハンドリングと表示:**
    *   [ ] `resize_core.py` からのエラー情報を取得し、Logタブに分かりやすく表示。
    *   [ ] 必要に応じてエラーダイアログ (`customtkinter.CTkInputDialog` や自作ダイアログ) を表示。

### フェーズ 6: スタイリング、最終調整、テスト

20. **スタイルの調整:**
    *   [ ] `ui_simulation_v2.html` の見た目に近づけるように、各ウィジェットの `configure` メソッドを使って色、フォントサイズ、パディング、マージンなどを調整。
    *   [ ] アイコンの組み込み (Font Awesome CDN は使えないので、ローカル画像ファイルや `CTkFont` での代替を検討)。
21. **ウィンドウのリサイズ対応:**
    *   [ ] ウィンドウサイズが変更されたときに、UI要素が適切に追従するように `pack`, `grid`, `place` の設定を見直す。
22. **総合テスト:**
    *   [ ] 様々な設定、ファイル、エッジケースでテスト。
    *   [ ] 長時間処理のテスト。
23. **コードのリファクタリングとドキュメント化:**
    *   [ ] コード全体を整理し、可読性を向上させる。
    *   [ ] 主要なクラスや関数にコメントを追加。

## 5. 処理の流れ

1.  ユーザーがGUI上で各種設定を入力・選択。
2.  「処理開始」ボタンをクリック。
3.  入力値のバリデーションチェック。
4.  画像処理のコアロジック (`resize_core.py` の関数群) を別スレッドで実行。
    *   GUIのフリーズを防ぐため、`threading` モジュールを使用。
    *   処理スレッドからGUIスレッドへは `queue` モジュールを使って進捗やログ情報を安全に渡す。
5.  ログ表示エリアに進捗やメッセージをリアルタイムで更新。
6.  プログレスバーを更新。
7.  処理完了後、結果サマリーを表示。
8.  中断ボタンが押された場合、ワーカースレッドに通知し、安全に処理を停止する。

## 6. ファイル構成

*   `resize_images_gui.py`: GUIのメインスクリプト。
*   `resize_core.py`: 既存の画像処理コアモジュール (変更なしで再利用、または必要に応じてGUI向けに調整)。
*   (オプション) `gui_config.json`: GUI設定保存用ファイル。

## 7. 参考情報源

*   **CustomTkinter Official Documentation (Wiki)**: [https://github.com/TomSchimansky/CustomTkinter/wiki](https://github.com/TomSchimansky/CustomTkinter/wiki)
*   **CustomTkinter GitHub Repository (Examples & Discussions)**: [https://github.com/TomSchimansky/CustomTkinter](https://github.com/TomSchimansky/CustomTkinter)
*   **Sample CustomTkinter Projects/Snippets**:
    *   [dei8bit/tkinter-and-CustomTKinter](https://github.com/dei8bit/tkinter-and-CustomTKinter)
    *   (その他、有用なリポジトリがあれば追記)
