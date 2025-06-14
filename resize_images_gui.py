import customtkinter as ctk
from tkinter import filedialog
from pathlib import Path
from PIL import Image
import traceback
import threading

# 日本語フォント設定モジュールをインポート
try:
    from japanese_font_utils import get_normal_font, get_button_font, get_heading_font
except ImportError:
    # フォールバック用の簡易フォント設定
    def get_normal_font():
        return {"family": "", "size": 11}

    def get_button_font():
        return {"family": "", "size": 11, "weight": "bold"}

    def get_heading_font():
        return {"family": "", "size": 13, "weight": "bold"}


try:
    from resize_core import (
        resize_and_compress_image,
        get_destination_path,
        sanitize_filename,
        format_file_size,
    )
except ImportError:

    def resize_and_compress_image(*args, **kwargs):
        print("ダミー: resize_and_compress_image")
        return (
            True,
            {"original_size": 100000, "new_size": 50000, "compression_ratio": 50.0},
            "ダミー処理成功",
        )

    def get_destination_path(source_path, source_dir, dest_dir):
        print("ダミー: get_destination_path")
        return Path(dest_dir) / Path(source_path).name

    def sanitize_filename(filename):
        print("ダミー: sanitize_filename")
        return filename

    def format_file_size(size_in_bytes):
        for unit in ["B", "KB", "MB", "GB"]:
            if size_in_bytes < 1024.0 or unit == "GB":
                break
            size_in_bytes /= 1024.0
        return f"{size_in_bytes:.1f} {unit}"


class App(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("画像処理ツール")

        # ウィンドウサイズを設定
        self.geometry("1000x900")  # 高さを900に増やしました
        self.minsize(900, 800)  # 最小の高さも800に調整しました

        # ウィンドウの背景色を設定（ライトモード用）
        self.configure(fg_color="#F8F9FA")

        # フレームの拡大性を確保するためにgridを設定
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # フォント設定の初期化
        self.normal_font = ctk.CTkFont(size=15)
        self.button_font = ctk.CTkFont(size=15, weight="bold")
        self.heading_font = ctk.CTkFont(size=18, weight="bold")
        self.small_font = ctk.CTkFont(size=13)

        # 先にログとプログレスバーのフレームを作成
        self.main_frame = ctk.CTkFrame(self, corner_radius=0, fg_color="transparent")
        self.main_frame.pack(fill="both", expand=True, padx=20, pady=20)

        self.main_frame.grid_rowconfigure(0, weight=1)
        self.main_frame.grid_rowconfigure(1, weight=0)
        self.main_frame.grid_columnconfigure(0, weight=1)

        # ログとプログレスバーを先に初期化
        self.log_progress_frame = ctk.CTkFrame(
            self.main_frame, corner_radius=10, border_width=1, border_color="#E9ECEF"
        )
        self.log_progress_frame.grid(row=1, column=0, sticky="ew", pady=(10, 0))
        self.log_progress_frame.grid_columnconfigure(0, weight=1)

        # ログタイトル
        log_title = ctk.CTkLabel(self.log_progress_frame, text="📋 処理ログ", font=self.heading_font, anchor="w")
        log_title.grid(row=0, column=0, sticky="w", padx=10, pady=(10, 5))

        self.log_textbox = ctk.CTkTextbox(
            self.log_progress_frame,
            height=140,
            corner_radius=6,
            wrap="word",
            state="disabled",
            font=self.normal_font,
            border_width=1,
            border_color="#E9ECEF",
        )
        self.log_textbox.grid(row=1, column=0, sticky="nsew", padx=10, pady=(0, 5))

        self.progress_bar = ctk.CTkProgressBar(
            self.log_progress_frame, corner_radius=6, height=8, progress_color="#5B5FCF"
        )
        self.progress_bar.grid(row=2, column=0, sticky="ew", padx=10, pady=(0, 10))

        # タブを作成
        self.tab_view = ctk.CTkTabview(self.main_frame)
        self.tab_view.grid(row=0, column=0, sticky="nsew", pady=(0, 10))

        # タブビューのフォント設定と色設定
        try:
            # 内部的なセグメントボタンにアクセスしてフォントとテキストカラーを設定
            if hasattr(self.tab_view, "_segmented_button") and self.tab_view._segmented_button:
                self.tab_view._segmented_button.configure(
                    font=self.heading_font,
                    text_color=("#212529", "#FFFFFF"),  # (非選択タブのテキスト色, 選択タブのテキスト色)
                    fg_color="#E9ECEF",  # 非選択タブの背景色（薄いグレー）
                    selected_color="#6C63FF",  # 選択タブの背景色（紫）
                    selected_hover_color="#5A52D5",  # 選択タブのホバー時の背景色
                    unselected_hover_color="#DEE2E6",  # 非選択タブのホバー時の背景色
                )
            else:
                # Fallback or log if _segmented_button is not available as expected
                print("Debug: _segmented_button not found or is None, cannot set tab font directly.")
        except Exception as e:
            print(f"タブフォント設定エラー(改): {e}")

        # タブを追加
        self.tab_resize = self.tab_view.add("リサイズ")
        self.tab_compress = self.tab_view.add("圧縮")
        self.tab_batch_process = self.tab_view.add("一括処理")  # This tab is for batch processing

        # 必要な変数を初期化
        self.resize_value_unit_label = None
        self.resize_quality_text_label = None
        self.resize_quality_slider = None
        self.resize_quality_value_label = None
        self.resize_start_button = None
        self.resize_cancel_button = None

        # ログ初期化完了後にタブの中身を作成
        self.create_tab_content_frames()

        # 初期化完了後に初期状態を設定
        self.add_log_message("アプリケーションを初期化しました")

        # リサイズタブの初期値を設定
        if hasattr(self, "resize_mode_var"):
            self.on_resize_mode_change(self.resize_mode_var.get())
        if hasattr(self, "resize_output_format_var"):
            self.on_output_format_change(self.resize_output_format_var.get())

        # ウィンドウを中央に配置
        self.center_window()

        self.cancel_requested = False  # 中断リクエストフラグ

    def _select_file(
        self,
        entry_widget,
        title="ファイルを選択",
        filetypes=(
            ("画像ファイル", "*.jpg *.jpeg *.png *.gif *.bmp *.tiff"),
            ("すべてのファイル", "*.*"),
        ),
    ):
        filepath = filedialog.askopenfilename(title=title, filetypes=filetypes)
        if filepath:
            entry_widget.delete(0, "end")
            entry_widget.insert(0, filepath)
            self.add_log_message(f"ファイル選択: {filepath}")

    def _select_directory(self, entry_widget, title="フォルダを選択"):
        """ディレクトリ選択ダイアログを表示し、選択されたパスをエントリーに設定する"""
        dirpath = filedialog.askdirectory(title=title)
        if dirpath:
            entry_widget.delete(0, "end")
            entry_widget.insert(0, dirpath)
            self.add_log_message(f"フォルダ選択: {dirpath}")

    def browse_resize_input_file(self):
        """リサイズ用の入力ファイルを選択"""
        filetypes = [("画像ファイル", "*.jpg;*.jpeg;*.png;*.webp;*.bmp;*.gif"), ("すべてのファイル", "*.*")]
        filename = filedialog.askopenfilename(title="入力ファイルを選択", filetypes=filetypes)
        if filename:
            self.resize_input_file_entry.delete(0, "end")
            self.resize_input_file_entry.insert(0, filename)
            self.add_log_message(f"ファイル選択: {filename}")

    def browse_resize_output_dir(self):
        """リサイズ用の出力先フォルダを選択"""
        self._select_directory(self.resize_output_dir_entry, title="出力先フォルダを選択")

    def on_output_format_change(self, selected_format):
        # ログメッセージは初期化完了後のみ表示
        if hasattr(self, "log_textbox") and self.log_textbox is not None:
            self.add_log_message(f"出力フォーマット変更: {selected_format}")
        show_quality = selected_format in ["JPEG", "WEBP"]

        if self.resize_quality_text_label:
            if show_quality:
                self.resize_quality_text_label.grid()
            else:
                self.resize_quality_text_label.grid_remove()

        if self.resize_quality_slider:
            if show_quality:
                self.resize_quality_slider.grid()
            else:
                self.resize_quality_slider.grid_remove()

        if self.resize_quality_value_label:
            if show_quality:
                self.resize_quality_value_label.grid()
                self.update_quality_label(self.resize_quality_var.get())
            else:
                self.resize_quality_value_label.grid_remove()

    def update_quality_label(self, value):
        if self.resize_quality_value_label:
            self.resize_quality_value_label.configure(text=f"{int(value)}")

    def on_resize_mode_change(self, selected_mode):
        # ログメッセージは初期化完了後のみ表示
        if hasattr(self, "log_textbox") and self.log_textbox is not None:
            self.add_log_message(f"リサイズモード変更: {selected_mode}")
        if hasattr(self, "resize_value_unit_label") and self.resize_value_unit_label:
            if selected_mode == "パーセント":
                self.resize_value_unit_label.configure(text="%")
            else:
                self.resize_value_unit_label.configure(text="px")

        if hasattr(self, "resize_value_entry"):
            self.resize_value_entry.delete(0, "end")

    def create_tab_content_frames(self):
        self.resize_tab_content = ctk.CTkFrame(self.tab_resize, corner_radius=0, fg_color="transparent")
        self.resize_tab_content.pack(fill="both", expand=True)

        self.resize_tab_content.grid_columnconfigure(0, weight=0)
        self.resize_tab_content.grid_columnconfigure(1, weight=1)
        self.resize_tab_content.grid_columnconfigure(2, weight=0)

        current_row = 0

        # ラベルでタイトル（アイコン付き）
        title_label = ctk.CTkLabel(
            self.resize_tab_content, text="🔧 リサイズ設定", font=self.heading_font, text_color="#212529"
        )
        title_label.grid(row=current_row, column=0, columnspan=3, padx=10, pady=(0, 20), sticky="w")
        current_row += 1

        # 入力ファイル・フォルダ選択
        ctk.CTkLabel(self.resize_tab_content, text="入力ファイル:", font=self.normal_font, text_color="#212529").grid(
            row=current_row, column=0, padx=(10, 5), pady=15, sticky="w"
        )
        self.resize_input_file_entry = ctk.CTkEntry(
            self.resize_tab_content,
            font=self.normal_font,
            corner_radius=6,
            border_width=2,
            border_color="#CED4DA",
            placeholder_text="画像ファイルを選択してください...",
        )
        self.resize_input_file_entry.grid(row=current_row, column=1, padx=5, pady=15, sticky="ew")
        self.resize_input_file_button = ctk.CTkButton(
            self.resize_tab_content,
            text="📁 参照",
            command=self.browse_resize_input_file,
            width=100,
            height=36,
            font=self.normal_font,
            corner_radius=6,
            fg_color="#6C63FF",
            hover_color="#5A52D5",
            text_color="#FFFFFF",
        )
        self.resize_input_file_button.grid(row=current_row, column=2, padx=5, pady=15)
        current_row += 1

        ctk.CTkLabel(self.resize_tab_content, text="出力先フォルダ:", font=self.normal_font, text_color="#212529").grid(
            row=current_row, column=0, padx=(10, 5), pady=15, sticky="w"
        )

        self.resize_output_dir_entry = ctk.CTkEntry(
            self.resize_tab_content,
            font=self.normal_font,
            corner_radius=6,
            border_width=2,
            border_color="#CED4DA",
            placeholder_text="出力先フォルダを選択してください...",
        )
        self.resize_output_dir_entry.grid(row=current_row, column=1, padx=5, pady=15, sticky="ew")

        self.resize_output_dir_button = ctk.CTkButton(
            self.resize_tab_content,
            text="📁 参照",
            command=self.browse_resize_output_dir,
            width=100,
            height=36,
            font=self.normal_font,
            corner_radius=6,
            fg_color="#6C63FF",
            hover_color="#5A52D5",
            text_color="#FFFFFF",
        )
        self.resize_output_dir_button.grid(row=current_row, column=2, padx=5, pady=15)
        current_row += 1

        # リサイズ設定フレーム
        resize_settings_frame = ctk.CTkFrame(
            self.resize_tab_content, corner_radius=10, fg_color="#FFFFFF", border_width=1, border_color="#DEE2E6"
        )
        resize_settings_frame.grid(row=current_row, column=0, columnspan=3, padx=10, pady=(20, 10), sticky="ew")
        resize_settings_frame.grid_columnconfigure(1, weight=1)

        # リサイズ設定のタイトル
        resize_settings_title = ctk.CTkLabel(
            resize_settings_frame, text="⚙️ リサイズ設定", font=ctk.CTkFont(size=16, weight="bold"), text_color="#212529"
        )
        resize_settings_title.grid(row=0, column=0, columnspan=3, padx=20, pady=(15, 20), sticky="w")

        rs_current_row = 1

        # モード選択
        ctk.CTkLabel(resize_settings_frame, text="モード:", font=self.normal_font, text_color="#212529").grid(
            row=rs_current_row, column=0, padx=(20, 5), pady=10, sticky="w"
        )
        mode_frame = ctk.CTkFrame(resize_settings_frame, fg_color="transparent")
        mode_frame.grid(row=rs_current_row, column=1, columnspan=2, padx=5, pady=10, sticky="ew")

        self.resize_mode_var = ctk.StringVar(value="幅を指定")
        resize_modes = [
            ("幅を指定", "幅を指定"),
            ("高さを指定", "高さを指定"),
            ("縦横最大", "縦横最大"),
            ("パーセント", "パーセント"),
        ]

        for i, (text, value) in enumerate(resize_modes):
            radio = ctk.CTkRadioButton(
                mode_frame,
                text=text,
                variable=self.resize_mode_var,
                value=value,
                command=lambda mode=value: self.on_resize_mode_change(mode),
                font=self.normal_font,
                fg_color="#6C63FF",
                hover_color="#5A52D5",
                border_color="#CED4DA",
            )
            radio.grid(row=0, column=i, padx=(0, 10), sticky="w")
        rs_current_row += 1

        # リサイズ値入力部分のフレームを作成
        resize_value_frame = ctk.CTkFrame(resize_settings_frame, fg_color="transparent")
        resize_value_frame.grid(row=rs_current_row, column=0, columnspan=3, padx=20, pady=10, sticky="w")

        ctk.CTkLabel(resize_value_frame, text="値:", font=self.normal_font, text_color="#212529").pack(
            side="left", padx=(0, 5)
        )

        self.resize_value_entry = ctk.CTkEntry(
            resize_value_frame,
            font=self.normal_font,
            width=100,
            corner_radius=6,
            border_width=2,
            border_color="#CED4DA",
            placeholder_text="数値を入力",
        )
        self.resize_value_entry.pack(side="left", padx=(0, 5))

        self.resize_value_unit_label = ctk.CTkLabel(
            resize_value_frame, text="px", font=self.normal_font, text_color="#212529"
        )
        self.resize_value_unit_label.pack(side="left")
        rs_current_row += 1

        self.resize_aspect_ratio_var = ctk.BooleanVar(value=True)
        self.resize_aspect_ratio_checkbox = ctk.CTkCheckBox(
            resize_settings_frame,
            text="アスペクト比を維持する",
            variable=self.resize_aspect_ratio_var,
            font=self.normal_font,
            fg_color="#6C63FF",
            hover_color="#5A52D5",
            border_color="#CED4DA",
        )
        self.resize_aspect_ratio_checkbox.grid(row=rs_current_row, column=0, columnspan=3, padx=20, pady=10, sticky="w")
        rs_current_row += 1

        ctk.CTkLabel(resize_settings_frame, text="出力フォーマット:", font=self.normal_font, text_color="#212529").grid(
            row=rs_current_row, column=0, padx=5, pady=10, sticky="w"
        )
        self.resize_output_format_options = [
            "元のフォーマットを維持",
            "PNG",
            "JPEG",
            "WEBP",
        ]
        self.resize_output_format_var = ctk.StringVar(value=self.resize_output_format_options[0])
        self.resize_output_format_menu = ctk.CTkOptionMenu(
            resize_settings_frame,
            values=self.resize_output_format_options,
            variable=self.resize_output_format_var,
            command=self.on_output_format_change,
            font=self.normal_font,
            dropdown_font=self.normal_font,
        )
        self.resize_output_format_menu.grid(row=rs_current_row, column=1, columnspan=2, padx=5, pady=10, sticky="ew")
        rs_current_row += 1

        # EXIF Handling Option
        ctk.CTkLabel(resize_settings_frame, text="EXIF情報:", font=self.normal_font, text_color="#212529").grid(
            row=rs_current_row, column=0, padx=5, pady=10, sticky="w"
        )
        self.exif_handling_options = ["EXIFを保持", "EXIFを削除"]
        self.exif_handling_var = ctk.StringVar(value=self.exif_handling_options[0])
        self.exif_handling_menu = ctk.CTkOptionMenu(
            resize_settings_frame,
            values=self.exif_handling_options,
            variable=self.exif_handling_var,
            font=self.normal_font,
            dropdown_font=self.normal_font,
        )
        self.exif_handling_menu.grid(row=rs_current_row, column=1, columnspan=2, padx=5, pady=10, sticky="ew")
        rs_current_row += 1

        self.resize_quality_text_label = ctk.CTkLabel(
            resize_settings_frame, text="品質 (JPEG/WEBP):", font=self.normal_font, text_color="#212529"
        )
        self.resize_quality_text_label.grid(row=rs_current_row, column=0, padx=5, pady=10, sticky="w")
        self.resize_quality_var = ctk.IntVar(value=85)
        self.resize_quality_slider = ctk.CTkSlider(
            resize_settings_frame,
            from_=1,
            to=100,
            number_of_steps=99,
            variable=self.resize_quality_var,
            command=self.update_quality_label,
            progress_color="#6C63FF",
            button_color="#6C63FF",
            button_hover_color="#5A52D5",
        )
        self.resize_quality_slider.grid(row=rs_current_row, column=1, padx=5, pady=10, sticky="ew")
        self.resize_quality_value_label = ctk.CTkLabel(
            resize_settings_frame,
            text=str(self.resize_quality_var.get()),
            font=self.normal_font,
        )
        self.resize_quality_value_label.grid(row=rs_current_row, column=2, padx=(5, 10), pady=10, sticky="w")
        rs_current_row += 1

        current_row += 1  # resize_settings_frame の分

        action_buttons_frame = ctk.CTkFrame(self.resize_tab_content, fg_color="transparent")
        action_buttons_frame.grid(row=current_row, column=0, columnspan=3, padx=10, pady=(10, 0), sticky="ew")
        action_buttons_frame.grid_columnconfigure(0, weight=1)
        action_buttons_frame.grid_columnconfigure(1, weight=0)  # Start button column
        action_buttons_frame.grid_columnconfigure(2, weight=0)  # Cancel button column
        action_buttons_frame.grid_columnconfigure(3, weight=1)

        self.resize_start_button = ctk.CTkButton(
            action_buttons_frame,
            text="🚀 処理開始",
            command=self.start_resize_process,
            width=150,
            height=42,
            font=self.button_font,
            fg_color="#6C63FF",
            hover_color="#5A52D5",
            text_color="#FFFFFF",
            corner_radius=8,
        )
        self.resize_start_button.grid(row=0, column=1, padx=5, pady=10)

        self.resize_cancel_button = ctk.CTkButton(
            action_buttons_frame,
            text="⏹ 中断",
            command=self.request_cancel_processing,
            state="disabled",
            width=130,
            height=42,
            font=self.button_font,
            fg_color="#DC3545",
            hover_color="#C82333",
            text_color="#FFFFFF",
            text_color_disabled="#FFFFFF",
            corner_radius=8,
        )
        self.resize_cancel_button.grid(row=0, column=2, padx=5, pady=10)
        current_row += 1

        # 全ての初期化が完了した後に初期値を設定する

        self.compress_tab_content = ctk.CTkFrame(self.tab_compress, corner_radius=0, fg_color="transparent")
        self.compress_tab_content.pack(fill="both", expand=True, padx=5, pady=5)
        ctk.CTkLabel(
            self.compress_tab_content,
            text="圧縮設定はここに配置",
            font=self.normal_font,
        ).pack(pady=20)

        self.batch_process_content_frame = ctk.CTkScrollableFrame(
            self.tab_batch_process, corner_radius=0, fg_color="transparent"
        )
        self.batch_process_content_frame.pack(fill="both", expand=True, padx=10, pady=10)
        self.batch_process_content_frame.grid_columnconfigure(1, weight=1)

        # タイトル
        batch_title_label = ctk.CTkLabel(
            self.batch_process_content_frame, text="📁 一括処理設定", font=self.heading_font, text_color="#212529"
        )
        batch_title_label.grid(row=0, column=0, columnspan=3, padx=10, pady=(0, 20), sticky="w")

        # --- 入力フォルダ選択 ---
        self.label_batch_input_folder = ctk.CTkLabel(
            self.batch_process_content_frame, text="入力フォルダ:", font=self.normal_font, text_color="#212529"
        )
        self.label_batch_input_folder.grid(row=1, column=0, padx=(10, 5), pady=15, sticky="w")

        self.batch_input_folder_path_var = ctk.StringVar()
        self.entry_batch_input_folder = ctk.CTkEntry(
            self.batch_process_content_frame,
            textvariable=self.batch_input_folder_path_var,
            font=self.normal_font,
            corner_radius=6,
            border_width=2,
            border_color="#CED4DA",
            placeholder_text="一括処理する入力フォルダを選択...",
        )
        self.entry_batch_input_folder.grid(row=1, column=1, padx=5, pady=15, sticky="ew")

        self.button_batch_input_folder = ctk.CTkButton(
            self.batch_process_content_frame,
            text="📁 参照",
            command=self.browse_batch_input_folder,
            width=100,
            height=36,
            font=self.normal_font,
            corner_radius=6,
            fg_color="#6C63FF",
            hover_color="#5A52D5",
            text_color="#FFFFFF",
        )
        self.button_batch_input_folder.grid(row=1, column=2, padx=5, pady=15)

        # --- 出力フォルダ選択 ---
        self.label_batch_output_folder = ctk.CTkLabel(
            self.batch_process_content_frame, text="出力フォルダ:", font=self.normal_font, text_color="#212529"
        )
        self.label_batch_output_folder.grid(row=2, column=0, padx=(10, 5), pady=15, sticky="w")

        self.batch_output_folder_path_var = ctk.StringVar()
        self.entry_batch_output_folder = ctk.CTkEntry(
            self.batch_process_content_frame,
            textvariable=self.batch_output_folder_path_var,
            font=self.normal_font,
            corner_radius=6,
            border_width=2,
            border_color="#CED4DA",
            placeholder_text="一括処理の出力先フォルダを選択...",
        )
        self.entry_batch_output_folder.grid(row=2, column=1, padx=5, pady=15, sticky="ew")

        self.button_batch_output_folder = ctk.CTkButton(
            self.batch_process_content_frame,
            text="📁 参照",
            command=self.browse_batch_output_folder,
            width=100,
            height=36,
            font=self.normal_font,
            corner_radius=6,
            fg_color="#6C63FF",
            hover_color="#5A52D5",
            text_color="#FFFFFF",
        )
        self.button_batch_output_folder.grid(row=2, column=2, padx=5, pady=15)

        # --- 区切り線 ---
        self.batch_separator1 = ctk.CTkFrame(
            self.batch_process_content_frame, fg_color="#E9ECEF", height=2, corner_radius=1
        )
        self.batch_separator1.grid(row=3, column=0, columnspan=3, sticky="ew", pady=10)

        # --- リサイズ設定フレーム ---
        batch_resize_settings_outer_frame = ctk.CTkFrame(
            self.batch_process_content_frame,
            corner_radius=10,
            fg_color="#FFFFFF",
            border_width=1,
            border_color="#DEE2E6",
        )
        batch_resize_settings_outer_frame.grid(row=3, column=0, columnspan=3, padx=10, pady=(10, 10), sticky="ew")
        batch_resize_settings_outer_frame.grid_columnconfigure(0, weight=1)  # ラベル用に左寄せ
        batch_resize_settings_outer_frame.grid_columnconfigure(1, weight=1)  # ウィジェット用に拡張

        # リサイズ設定タイトル
        batch_resize_title = ctk.CTkLabel(
            batch_resize_settings_outer_frame,
            text="⚙️ リサイズ設定",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color="#212529",
        )
        batch_resize_title.grid(row=0, column=0, columnspan=2, padx=20, pady=(15, 10), sticky="w")

        # モード設定
        mode_label = ctk.CTkLabel(
            batch_resize_settings_outer_frame, text="モード:", font=self.normal_font, text_color="#212529"
        )
        mode_label.grid(row=1, column=0, padx=(20, 5), pady=10, sticky="w")

        mode_frame = ctk.CTkFrame(batch_resize_settings_outer_frame, fg_color="transparent")
        mode_frame.grid(row=1, column=1, padx=5, pady=10, sticky="ew")

        self.batch_resize_mode_var = ctk.StringVar(value="指定なし")
        self.batch_resize_modes = ["指定なし", "幅を指定", "高さを指定", "縦横最大", "パーセント指定"]
        self.batch_radio_buttons_resize_mode = []
        for i, mode_text in enumerate(self.batch_resize_modes):
            radio_button = ctk.CTkRadioButton(
                mode_frame,
                text=mode_text,
                variable=self.batch_resize_mode_var,
                value=mode_text,
                font=self.normal_font,
                command=self.update_batch_resize_value_unit_label,
                radiobutton_width=20,
                radiobutton_height=20,
                border_width_checked=2,
                border_width_unchecked=2,
                fg_color="#6C63FF",
                hover_color="#5A52D5",
            )
            # 2列で表示 (i % 2 で列インデックス、 i // 2 で行インデックス)
            radio_button.grid(row=(i // 3), column=(i % 3), padx=5, pady=5, sticky="w")
            self.batch_radio_buttons_resize_mode.append(radio_button)

        # 値設定
        value_label = ctk.CTkLabel(
            batch_resize_settings_outer_frame, text="値:", font=self.normal_font, text_color="#212529"
        )
        value_label.grid(row=2, column=0, padx=(20, 5), pady=10, sticky="w")

        batch_resize_value_frame = ctk.CTkFrame(batch_resize_settings_outer_frame, fg_color="transparent")
        batch_resize_value_frame.grid(row=2, column=1, padx=5, pady=10, sticky="ew")

        self.batch_resize_value_var = ctk.StringVar(value="1000")
        self.entry_batch_resize_value = ctk.CTkEntry(
            batch_resize_value_frame,
            textvariable=self.batch_resize_value_var,
            font=self.normal_font,
            width=120,  # 少し幅を広げる
            corner_radius=6,
            border_width=2,
            border_color="#CED4DA",
            placeholder_text="数値を入力",
        )
        self.entry_batch_resize_value.pack(side="left", padx=(0, 5))

        self.batch_resize_value_unit_label = ctk.CTkLabel(
            batch_resize_value_frame, text="px", font=self.normal_font, text_color="#212529"
        )
        self.batch_resize_value_unit_label.pack(side="left", padx=(0, 5))

        # アスペクト比を維持
        self.batch_keep_aspect_ratio_var = ctk.BooleanVar(value=True)
        self.checkbox_batch_keep_aspect_ratio = ctk.CTkCheckBox(
            batch_resize_settings_outer_frame,
            text="アスペクト比を維持",
            variable=self.batch_keep_aspect_ratio_var,
            font=self.normal_font,
            checkbox_width=20,
            checkbox_height=20,
            corner_radius=6,
            border_width=2,
            fg_color="#6C63FF",
            hover_color="#5A52D5",
        )
        self.checkbox_batch_keep_aspect_ratio.grid(row=3, column=0, columnspan=2, padx=20, pady=(10, 15), sticky="w")

        self.update_batch_resize_value_unit_label()  # 初期単位表示

        # --- 区切り線 ---
        self.batch_separator2 = ctk.CTkFrame(
            self.batch_process_content_frame, fg_color="#E9ECEF", height=2, corner_radius=1
        )
        self.batch_separator2.grid(row=10, column=0, columnspan=3, sticky="ew", pady=10)

        # --- 圧縮設定 ---
        self.label_batch_compress_settings = ctk.CTkLabel(
            self.batch_process_content_frame, text="圧縮設定", font=self.heading_font
        )
        self.label_batch_compress_settings.grid(row=11, column=0, columnspan=3, pady=(0, 5), sticky="w")

        # 圧縮を有効にするか
        self.batch_enable_compression_var = ctk.BooleanVar(value=True)  # デフォルトは有効
        self.checkbox_batch_enable_compression = ctk.CTkCheckBox(
            self.batch_process_content_frame,
            text="圧縮設定を有効にする",
            variable=self.batch_enable_compression_var,
            font=self.normal_font,
            command=self.update_batch_compression_settings_state,
            fg_color="#5B5FCF",
            border_color="#E9ECEF",
            hover_color="#4B4FBF",
        )
        self.checkbox_batch_enable_compression.grid(row=12, column=0, columnspan=3, padx=5, pady=5, sticky="w")

        # 出力フォーマット
        self.label_batch_output_format = ctk.CTkLabel(
            self.batch_process_content_frame,
            text="出力フォーマット:",
            font=self.normal_font,
        )
        self.label_batch_output_format.grid(row=13, column=0, padx=(0, 5), pady=5, sticky="w")

        self.batch_output_format_var = ctk.StringVar(value="オリジナルを維持")
        self.batch_output_formats = ["オリジナルを維持", "JPEG", "PNG", "WEBP"]
        self.optionmenu_batch_output_format = ctk.CTkOptionMenu(
            self.batch_process_content_frame,
            variable=self.batch_output_format_var,
            values=self.batch_output_formats,
            font=self.normal_font,
            command=self.update_batch_quality_settings_visibility,  # コマンド追加
        )
        self.optionmenu_batch_output_format.grid(row=13, column=1, columnspan=2, padx=5, pady=5, sticky="ew")

        # --- JPEG 品質設定 (最初は非表示) ---
        self.label_batch_jpeg_quality = ctk.CTkLabel(
            self.batch_process_content_frame, text="JPEG品質:", font=self.normal_font
        )
        self.batch_jpeg_quality_var = ctk.IntVar(value=85)
        self.slider_batch_jpeg_quality = ctk.CTkSlider(
            self.batch_process_content_frame,
            from_=1,
            to=100,
            number_of_steps=99,
            variable=self.batch_jpeg_quality_var,
            command=lambda x: self.label_batch_jpeg_quality_value.configure(text=f"{int(x)}"),
            progress_color="#5B5FCF",
            button_color="#5B5FCF",
            button_hover_color="#4B4FBF",
        )
        self.label_batch_jpeg_quality_value = ctk.CTkLabel(
            self.batch_process_content_frame,
            text=f"{self.batch_jpeg_quality_var.get()}",
            font=self.normal_font,
            width=30,
        )

        # --- WEBP 品質設定 (最初は非表示) ---
        self.label_batch_webp_quality = ctk.CTkLabel(
            self.batch_process_content_frame, text="WEBP品質:", font=self.normal_font
        )
        self.batch_webp_quality_var = ctk.IntVar(value=85)
        self.slider_batch_webp_quality = ctk.CTkSlider(
            self.batch_process_content_frame,
            from_=1,
            to=100,
            number_of_steps=99,
            variable=self.batch_webp_quality_var,
            command=lambda x: self.label_batch_webp_quality_value.configure(text=f"{int(x)}"),
            progress_color="#5B5FCF",
            button_color="#5B5FCF",
            button_hover_color="#4B4FBF",
        )
        self.label_batch_webp_quality_value = ctk.CTkLabel(
            self.batch_process_content_frame,
            text=f"{self.batch_webp_quality_var.get()}",
            font=self.normal_font,
            width=30,
        )
        self.batch_webp_lossless_var = ctk.BooleanVar(value=False)
        self.checkbox_batch_webp_lossless = ctk.CTkCheckBox(
            self.batch_process_content_frame,
            text="ロスレス圧縮",
            variable=self.batch_webp_lossless_var,
            font=self.normal_font,
            command=self.update_batch_webp_lossless_state,
            fg_color="#5B5FCF",
            border_color="#E9ECEF",
            hover_color="#4B4FBF",
        )

        self.update_batch_compression_settings_state()  # 初期状態設定 (これにより品質設定も更新される)

        # --- 区切り線 ---
        self.batch_separator3 = ctk.CTkFrame(
            self.batch_process_content_frame, fg_color="#E9ECEF", height=2, corner_radius=1
        )
        self.batch_separator3.grid(row=17, column=0, columnspan=3, sticky="ew", pady=10)

        # --- その他設定 ---
        self.label_batch_other_settings = ctk.CTkLabel(
            self.batch_process_content_frame, text="その他設定", font=self.heading_font
        )
        self.label_batch_other_settings.grid(row=18, column=0, columnspan=3, pady=(0, 5), sticky="w")  # rowは適宜調整

        # EXIF情報
        self.label_batch_exif = ctk.CTkLabel(self.batch_process_content_frame, text="EXIF情報:", font=self.normal_font)
        self.label_batch_exif.grid(row=19, column=0, padx=(0, 5), pady=5, sticky="w")  # rowは適宜調整
        self.batch_exif_handling_var = ctk.StringVar(value="保持する")
        self.batch_exif_options = ["保持する", "削除する", "保持（回転情報のみ削除）"]
        self.optionmenu_batch_exif_handling = ctk.CTkOptionMenu(
            self.batch_process_content_frame,
            variable=self.batch_exif_handling_var,
            values=self.batch_exif_options,
            font=self.normal_font,
        )
        self.optionmenu_batch_exif_handling.grid(
            row=19, column=1, columnspan=2, padx=5, pady=5, sticky="ew"
        )  # rowは適宜調整

        # ファイル命名規則
        self.label_batch_prefix = ctk.CTkLabel(
            self.batch_process_content_frame,
            text="ﾌｧｲﾙ名ﾌﾟﾚﾌｨｯｸｽ:",
            font=self.normal_font,
        )
        self.label_batch_prefix.grid(row=20, column=0, padx=(0, 5), pady=5, sticky="w")  # rowは適宜調整
        self.batch_prefix_var = ctk.StringVar(value="")
        self.entry_batch_prefix = ctk.CTkEntry(
            self.batch_process_content_frame,
            textvariable=self.batch_prefix_var,
            font=self.normal_font,
            corner_radius=6,
            border_width=1,
            border_color="#E9ECEF",
            placeholder_text="プレフィックスを入力（オプション）",
        )
        self.entry_batch_prefix.grid(row=20, column=1, columnspan=2, padx=5, pady=5, sticky="ew")  # rowは適宜調整

        self.label_batch_suffix = ctk.CTkLabel(
            self.batch_process_content_frame,
            text="ﾌｧｲﾙ名ｻﾌｨｯｸｽ:",
            font=self.normal_font,
        )
        self.label_batch_suffix.grid(row=21, column=0, padx=(0, 5), pady=5, sticky="w")  # rowは適宜調整
        self.batch_suffix_var = ctk.StringVar(value="_processed")
        self.entry_batch_suffix = ctk.CTkEntry(
            self.batch_process_content_frame,
            textvariable=self.batch_suffix_var,
            font=self.normal_font,
            corner_radius=6,
            border_width=1,
            border_color="#E9ECEF",
        )
        self.entry_batch_suffix.grid(row=21, column=1, columnspan=2, padx=5, pady=5, sticky="ew")  # rowは適宜調整

        # サブフォルダの処理
        self.batch_process_subfolders_var = ctk.BooleanVar(value=True)
        self.checkbox_batch_process_subfolders = ctk.CTkCheckBox(
            self.batch_process_content_frame,
            text="サブフォルダも処理する",
            variable=self.batch_process_subfolders_var,
            font=self.normal_font,
            fg_color="#5B5FCF",
            border_color="#E9ECEF",
            hover_color="#4B4FBF",
        )
        self.checkbox_batch_process_subfolders.grid(
            row=22, column=0, columnspan=3, padx=5, pady=10, sticky="w"
        )  # rowは適宜調整

        # 一括処理ボタンのフレーム
        batch_action_frame = ctk.CTkFrame(self.batch_process_content_frame, fg_color="transparent")
        batch_action_frame.grid(row=23, column=0, columnspan=3, padx=10, pady=(20, 10), sticky="ew")
        batch_action_frame.grid_columnconfigure(0, weight=1)
        batch_action_frame.grid_columnconfigure(1, weight=0)
        batch_action_frame.grid_columnconfigure(2, weight=0)
        batch_action_frame.grid_columnconfigure(3, weight=1)

        # 一括処理開始ボタン
        self.batch_start_button = ctk.CTkButton(
            batch_action_frame,
            text="🚀 一括処理開始",
            command=self.start_batch_process,
            width=160,
            height=42,
            font=self.button_font,
            fg_color="#6C63FF",
            hover_color="#5A52D5",
            text_color="#FFFFFF",
            corner_radius=8,
        )
        self.batch_start_button.grid(row=0, column=1, padx=5, pady=5)

        # 一括処理中断ボタン
        self.batch_cancel_button = ctk.CTkButton(
            batch_action_frame,
            text="⏹ 中断",
            command=self.cancel_batch_process,
            state="disabled",
            width=120,
            height=36,
            font=self.button_font,
            fg_color="#DC3545",
            hover_color="#C82333",
            text_color="#FFFFFF",
            text_color_disabled="#FFFFFF",
            corner_radius=8,
        )
        self.batch_cancel_button.grid(row=0, column=2, padx=5, pady=5)

    def browse_batch_input_folder(self):
        folder_selected = filedialog.askdirectory(title="一括処理する入力フォルダを選択")
        if folder_selected:
            self.batch_input_folder_path_var.set(folder_selected)
            self.add_log_message(f"一括処理 入力フォルダ: {folder_selected}")

    def browse_batch_output_folder(self):
        folder_selected = filedialog.askdirectory(title="一括処理後の出力先フォルダを選択")
        if folder_selected:
            self.batch_output_folder_path_var.set(folder_selected)
            self.add_log_message(f"一括処理 出力フォルダ: {folder_selected}")

    def update_batch_resize_value_unit_label(self):
        mode = self.batch_resize_mode_var.get()
        if mode == "パーセント指定":
            self.batch_resize_value_unit_label.configure(text="%")
        else:
            self.batch_resize_value_unit_label.configure(text="px")
        # 「指定なし」の場合、値入力と単位を無効化（または非表示）
        if mode == "指定なし":
            self.entry_batch_resize_value.configure(state="disabled")
            self.batch_resize_value_unit_label.configure(text="")  # 単位を消す
            self.checkbox_batch_keep_aspect_ratio.configure(state="disabled")
        else:
            self.entry_batch_resize_value.configure(state="normal")
            self.checkbox_batch_keep_aspect_ratio.configure(state="normal")

    def update_batch_compression_settings_state(self):
        enable_compression = self.batch_enable_compression_var.get()
        if enable_compression:
            self.label_batch_output_format.configure(state="normal")
            self.optionmenu_batch_output_format.configure(state="normal")
        else:
            self.label_batch_output_format.configure(state="disabled")
            self.optionmenu_batch_output_format.configure(state="disabled")
        self.update_batch_quality_settings_visibility()  # 品質設定の表示/非表示も連動

    def update_batch_quality_settings_visibility(self, _event=None):  # _eventはOptionMenuのcommandから渡されるため追加
        # 一旦すべての品質設定UIを非表示にする
        self.label_batch_jpeg_quality.grid_remove()
        self.slider_batch_jpeg_quality.grid_remove()
        self.label_batch_jpeg_quality_value.grid_remove()
        self.label_batch_webp_quality.grid_remove()
        self.slider_batch_webp_quality.grid_remove()
        self.label_batch_webp_quality_value.grid_remove()
        self.checkbox_batch_webp_lossless.grid_remove()

        if not self.batch_enable_compression_var.get():
            return  # 圧縮が無効なら何も表示しない

        selected_format = self.batch_output_format_var.get()
        current_row = 14  # 品質設定UIの開始行

        if selected_format == "JPEG":
            self.label_batch_jpeg_quality.grid(row=current_row, column=0, padx=(0, 5), pady=5, sticky="w")
            self.slider_batch_jpeg_quality.grid(row=current_row, column=1, padx=5, pady=5, sticky="ew")
            self.label_batch_jpeg_quality_value.grid(row=current_row, column=2, padx=(0, 5), pady=5, sticky="w")
            self.slider_batch_jpeg_quality.configure(state="normal")
        elif selected_format == "WEBP":
            self.label_batch_webp_quality.grid(row=current_row, column=0, padx=(0, 5), pady=5, sticky="w")
            self.slider_batch_webp_quality.grid(row=current_row, column=1, padx=5, pady=5, sticky="ew")
            self.label_batch_webp_quality_value.grid(row=current_row, column=2, padx=(0, 5), pady=5, sticky="w")
            current_row += 1
            self.checkbox_batch_webp_lossless.grid(row=current_row, column=1, columnspan=2, padx=5, pady=5, sticky="w")
            self.update_batch_webp_lossless_state()  # WEBPロスレスチェックボックスの状態を更新
        # PNGやオリジナルを維持の場合は、専用の品質UIは表示しない

    def update_batch_webp_lossless_state(self):
        if self.batch_webp_lossless_var.get():
            self.slider_batch_webp_quality.configure(state="disabled")
            self.label_batch_webp_quality_value.configure(state="disabled")
        else:
            self.slider_batch_webp_quality.configure(state="normal")
            self.label_batch_webp_quality_value.configure(state="normal")

    def add_log_message(self, message, is_warning=False, is_error=False):
        # log_textboxがまだ初期化されていない場合は何もしない
        if not hasattr(self, "log_textbox") or self.log_textbox is None:
            print(f"ログメッセージ（表示不可）: {message}")
            return

        try:
            self.log_textbox.configure(state="normal")
            if is_warning:
                self.log_textbox.insert("end", f"[警告] {message}\n", "warning")
            elif is_error:
                self.log_textbox.insert("end", f"[エラー] {message}\n", "error")
            else:
                self.log_textbox.insert("end", f"{message}\n")
            self.log_textbox.configure(state="disabled")
            self.log_textbox.see("end")
        except Exception as e:
            print(f"ログ表示エラー: {e} - メッセージ: {message}")

    def update_progress(self, value, pulse=False):
        """
        進捗バーを更新する

        Args:
            value: 0.0-1.0の間の進捗値
            pulse: Trueの場合、パルスモードを使用（処理中アニメーション）
        """
        if pulse:
            # パルスモードの場合、少し値を変動させて動きを演出
            current = self.progress_bar.get()
            # 0.45-0.55の間で値を変動させる
            if current < 0.45 or current > 0.55:
                self.progress_bar.set(0.5)
            else:
                # 少しずつ値を変更して動きを作る
                delta = 0.01
                new_value = current + delta if current < 0.55 else current - delta
                self.progress_bar.set(new_value)
        else:
            # 通常モード
            self.progress_bar.set(value)

    def center_window(self):
        """Windows環境でも正しく動作するよう修正した中央配置メソッド"""
        self.update_idletasks()

        # サイズが小さすぎる場合は最小値を適用
        width = max(self.winfo_width(), 1000)
        height = max(self.winfo_height(), 900)

        x = (self.winfo_screenwidth() // 2) - (width // 2)
        y = (self.winfo_screenheight() // 2) - (height // 2)

        # 位置とサイズを設定
        self.geometry(f"{width}x{height}+{x}+{y}")

        # 再度サイズを確定させる
        self.update_idletasks()

    def start_resize_process(self):
        self.add_log_message("リサイズ処理を開始します...")
        if self.resize_start_button:
            self.resize_start_button.configure(state="disabled")
        if self.resize_cancel_button:
            self.resize_cancel_button.configure(state="normal")
        self.update_progress(0.1)

        input_file_str = self.resize_input_file_entry.get()
        output_dir_str = self.resize_output_dir_entry.get()
        resize_mode_gui = self.resize_mode_var.get()
        resize_value_str = self.resize_value_entry.get()
        keep_aspect_ratio = self.resize_aspect_ratio_var.get()
        output_format_gui = self.resize_output_format_var.get()
        quality = self.resize_quality_var.get()
        exif_handling_gui = self.exif_handling_var.get()  # Get EXIF handling option

        if not input_file_str:
            self.add_log_message("エラー: 入力ファイルが選択されていません。ファイルを選択してください。")
            self.finish_resize_process(success=False)
            return

        core_output_format = {
            "JPEG": "jpeg",
            "PNG": "png",
            "WebP": "webp",
            "入力と同じ": "same",
        }.get(output_format_gui, "same")

        exif_map = {"EXIFを保持": "keep", "EXIFを削除": "remove"}
        core_exif_handling = exif_map.get(exif_handling_gui, "keep")

        source_file_path = Path(input_file_str)

        if not input_file_str or not output_dir_str:
            self.add_log_message(
                "エラー: 入力ファイルまたは出力ディレクトリが指定されていません。",
                is_error=True,
            )
            self.finish_resize_process(success=False, message="入力または出力先が未指定")
            return

        output_directory = Path(output_dir_str)
        if not output_directory.is_dir():
            try:
                output_directory.mkdir(parents=True, exist_ok=True)
                self.add_log_message(f"出力ディレクトリを作成しました: {output_directory}")
            except OSError as e_os:
                self.add_log_message(
                    f"エラー: 出力ディレクトリの作成に失敗しました: {output_directory} ({e_os})",
                    is_error=True,
                )
                self.finish_resize_process(success=False, message="出力ディレクトリ作成失敗")
                return

        file_stem = source_file_path.stem
        original_suffix = source_file_path.suffix

        if core_output_format == "jpeg":
            new_suffix = ".jpg"
        elif core_output_format == "png":
            new_suffix = ".png"
        elif core_output_format == "webp":
            new_suffix = ".webp"
        elif core_output_format == "same":
            new_suffix = original_suffix
        else:
            new_suffix = original_suffix
            self.add_log_message(
                f"警告: 不明な出力フォーマット '{core_output_format}'。元の拡張子 '{original_suffix}' を使用します。",
                is_warning=True,
            )

        dest_path = output_directory / (file_stem + new_suffix)

        resize_mode_map = {
            "パーセント指定": "percent",
            "幅指定": "width",
            "高さ指定": "height",
            "長辺指定": "long_edge",
            "短辺指定": "short_edge",
        }
        if resize_mode_gui == "パーセント指定":
            core_resize_mode = "percentage"
        else:
            core_resize_mode = resize_mode_map.get(resize_mode_gui, "width")

        try:
            resize_value_parsed = int(resize_value_str) if resize_value_str else 0
        except ValueError:
            self.add_log_message(
                f"エラー: リサイズ値 '{resize_value_str}'は不正な数値です。",
                is_error=True,
            )
            self.finish_resize_process(success=False, message="リサイズ値が不正")
            return

        try:
            quality_parsed = int(quality) if quality else 75
        except ValueError:
            self.add_log_message(f"エラー: 品質値 '{quality}'は不正な数値です。", is_error=True)
            self.finish_resize_process(success=False, message="品質値が不正")
            return

        try:
            self.processing_thread = threading.Thread(
                target=self._execute_resize_in_thread,
                args=(
                    source_file_path,
                    dest_path,
                    core_resize_mode,
                    resize_value_parsed,
                    keep_aspect_ratio,
                    core_output_format,
                    quality_parsed,
                    core_exif_handling,
                ),
            )
            self.processing_thread.start()
        except Exception as e:
            self.add_log_message(f"画像処理の開始中に予期せぬエラーが発生しました: {e}", is_error=True)
            tb_str = traceback.format_exc()
            self.add_log_message(f"トレースバック:\n{tb_str}", is_error=True)
            self.finish_resize_process(success=False, message=str(e))

    def request_cancel_processing(self):
        self.cancel_requested = True
        self.add_log_message("中断リクエストを受け付けました。現在の処理ステップが完了次第、停止します。")
        # 中断ボタンは finish_resize_process で無効化される

    def _execute_resize_in_thread(
        self,
        source_path,
        dest_path,
        core_resize_mode,
        resize_value,
        keep_aspect_ratio,
        core_output_format,
        quality,
        exif_handling,
    ):
        try:
            self.add_log_message("画像処理スレッドを開始しました...")

            if self.cancel_requested:
                self.after(
                    0,
                    lambda: self.add_log_message("処理が中断されました (スレッド開始直後)。", is_warning=True),
                )
                self.after(
                    0,
                    lambda: self.finish_resize_process(success=False, message="処理がユーザーによって中断されました。"),
                )
                return

            try:
                img = Image.open(source_path)
                original_width, original_height = img.size
            except FileNotFoundError:
                self.after(
                    0,
                    lambda: self.add_log_message(
                        f"エラー: 入力ファイルが見つかりません: {source_path}",
                        is_error=True,
                    ),
                )
                self.after(
                    0,
                    lambda: self.finish_resize_process(success=False, message="入力ファイルが見つかりません。"),
                )
                return
            except Exception as e:
                self.after(
                    0,
                    lambda e=e: self.add_log_message(
                        f"エラー: 画像ファイルを開けません: {source_path} ({e})",
                        is_error=True,
                    ),
                )
                self.after(
                    0,
                    lambda e=e: self.finish_resize_process(success=False, message="画像ファイルを開けません。"),
                )
                return

            if self.cancel_requested:
                self.after(
                    0,
                    lambda: self.add_log_message("処理が中断されました (画像読み込み後)。", is_warning=True),
                )
                self.after(
                    0,
                    lambda: self.finish_resize_process(success=False, message="処理がユーザーによって中断されました。"),
                )
                return

            calculated_target_width = 0
            if core_resize_mode == "width":
                calculated_target_width = resize_value
            elif core_resize_mode == "percentage":
                calculated_target_width = int(original_width * (resize_value / 100))
            elif core_resize_mode == "height":
                if keep_aspect_ratio:
                    calculated_target_width = int(original_width * (resize_value / original_height))
                else:
                    # アスペクト比を維持しない場合、resize_coreは幅と高さの両方を必要とするが、
                    # GUIからは一方しか指定できるため、ここでは元の幅を維持し高さを変更する挙動を想定する。
                    # ただし、resize_and_compress_image は target_width のみを取るため、
                    # このケースは resize_core 側で適切に扱われるか、GUIの仕様を見直す必要がある。
                    # 現状では、アスペクト比非維持の高さ指定は期待通りに動作しない可能性がある。
                    calculated_target_width = original_width  # 元の幅を維持
                    # target_height = resize_value # この値は resize_and_compress_image に直接渡せない
                    self.after(
                        0,
                        lambda: self.add_log_message(
                            "警告: 高さ指定でアスペクト比を維持しない場合、resize_coreの現在の仕様では期待通りに動作しない可能性があります。"
                            "コア関数は目標幅のみを受け取ります。",
                            is_warning=True,
                        ),
                    )

            if calculated_target_width <= 0:
                self.after(
                    0,
                    lambda: self.add_log_message(
                        f"エラー: 計算された目標幅が無効です ({calculated_target_width}px)。入力値を確認してください。",
                        is_error=True,
                    ),
                )
                self.after(
                    0,
                    lambda: self.finish_resize_process(success=False, message="目標幅の計算結果が無効です。"),
                )
                return

            self.after(0, lambda: self.update_progress(0.5))

            if self.cancel_requested:  # Check before core processing
                self.after(
                    0,
                    lambda: self.add_log_message("処理が中断されました (コア処理開始前)。", is_warning=True),
                )
                self.after(
                    0,
                    lambda: self.finish_resize_process(success=False, message="処理がユーザーによって中断されました。"),
                )
                return

            # resize_and_compress_image を呼び出す
            success, skipped, new_size_kb = resize_and_compress_image(
                source_path=source_path,
                dest_path=dest_path,
                target_width=calculated_target_width,
                quality=quality,
                format=core_output_format,
                exif_handling=exif_handling,  # Pass EXIF handling to core function
                balance=5,  # balance の値はGUIからは設定できないため固定値
                webp_lossless=False,  # webp_lossless の値はGUIからは設定できないため固定値
                # dry_run=False # dry_run はGUIの主要機能ではないためFalse固定
            )

            if self.cancel_requested:
                self.after(
                    0,
                    lambda: self.add_log_message("処理が中断されました (コア処理後)。", is_warning=True),
                )
                self.after(
                    0,
                    lambda: self.finish_resize_process(success=False, message="処理がユーザーによって中断されました。"),
                )
                return

            self.after(0, lambda: self.update_progress(0.9))

            if success:
                if skipped:
                    self.after(
                        0,
                        lambda: self.add_log_message(
                            f"画像は既に最適化されているか、設定より小さいためスキップされました: {dest_path.name}",
                            is_warning=True,
                        ),
                    )
                else:
                    self.after(
                        0,
                        lambda: self.add_log_message(f"画像処理成功: {dest_path.name} (サイズ: {new_size_kb} KB)"),
                    )
                self.after(
                    0,
                    lambda: self.finish_resize_process(success=True, message="画像処理が正常に完了しました。"),
                )
            else:
                self.after(
                    0,
                    lambda: self.add_log_message(f"画像処理失敗: {dest_path.name}", is_error=True),
                )
                self.after(
                    0,
                    lambda: self.finish_resize_process(success=False, message="画像処理中にエラーが発生しました。"),
                )

        except Exception as e:
            detailed_error_message = f"画像処理スレッドで予期せぬエラーが発生しました: {type(e).__name__}: {e}"
            tb_str = traceback.format_exc()
            self.after(
                0,
                lambda e=e: self.add_log_message(detailed_error_message, is_error=True),
            )
            self.after(
                0,
                lambda e=e: self.add_log_message(f"トレースバック:\n{tb_str}", is_error=True),
            )
            self.after(
                0,
                lambda e=e: self.finish_resize_process(success=False, message=f"予期せぬエラー: {e}"),
            )

            # 進捗状況の更新を開始
            self.after(100, self._check_thread_status)
        except Exception as e:
            self.add_log_message(f"画像処理の開始中に予期せぬエラーが発生しました: {e}")
            self.finish_resize_process(success=False, message=str(e))

    def cancel_resize_process(self):
        self.add_log_message("リサイズ処理を中断しています...")
        self.cancel_requested = True

        # スレッドは自然に終了するのを待つ
        # 本格的な実装では、もっと洗練された中断機構が必要

    def finish_resize_process(self, success=True, message="処理完了"):
        if success:
            self.add_log_message(f"完了: {message}")
            self.update_progress(1)
        else:
            self.add_log_message(f"エラー/中断: {message}")
            self.update_progress(0)

        if self.resize_start_button:
            self.resize_start_button.configure(state="normal")
        if self.resize_cancel_button:
            self.resize_cancel_button.configure(state="disabled")
        self.cancel_requested = False  # 念のため再度リセット

    def start_batch_process(self):
        """一括処理を開始"""
        self.add_log_message("一括処理機能は現在開発中です...")
        # TODO: 実際の一括処理実装

    def cancel_batch_process(self):
        """一括処理を中断"""
        self.add_log_message("一括処理を中断します...")
        # TODO: 実際の中断処理実装


def main():
    # ライトモードに固定設定
    ctk.set_appearance_mode("light")

    # カスタムテーマを適用
    theme_path = Path(__file__).parent / "karuku_light_theme.json"
    if theme_path.exists():
        ctk.set_default_color_theme(str(theme_path))
    else:
        ctk.set_default_color_theme("blue")

    app = App()
    app.mainloop()


if __name__ == "__main__":
    main()
