"""
プリセット管理ダイアログ
"""
import customtkinter as ctk
from tkinter import messagebox, filedialog
from .preset_manager import PresetData, PresetManager
from typing import Optional, Callable
from pathlib import Path


class PresetEditDialog(ctk.CTkToplevel):
    """プリセット編集ダイアログ"""
    
    def __init__(self, parent, preset: Optional[PresetData] = None, is_new: bool = True):
        super().__init__(parent)
        
        self.preset = preset or PresetData(name="新しいプリセット")
        self.is_new = is_new
        self.result = None
        
        self.title("プリセット編集" if not is_new else "新規プリセット")
        self.geometry("600x700")
        self.minsize(500, 600)
        
        # モーダルダイアログ設定
        self.transient(parent)
        self.grab_set()
        
        self._setup_ui()
        self._load_preset_data()
        
        # ウィンドウを中央に配置
        self.update_idletasks()
        x = (self.winfo_screenwidth() // 2) - (self.winfo_width() // 2)
        y = (self.winfo_screenheight() // 2) - (self.winfo_height() // 2)
        self.geometry(f"+{x}+{y}")
        
    def _setup_ui(self):
        """UIをセットアップ"""
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)
        
        # スクロール可能フレーム
        scroll_frame = ctk.CTkScrollableFrame(self)
        scroll_frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        scroll_frame.grid_columnconfigure(1, weight=1)
        
        row = 0
        
        # 基本情報セクション
        ctk.CTkLabel(scroll_frame, text="基本情報", font=("", 16, "bold")).grid(
            row=row, column=0, columnspan=2, pady=(0, 10), sticky="w"
        )
        row += 1
        
        # プリセット名
        ctk.CTkLabel(scroll_frame, text="プリセット名:").grid(row=row, column=0, pady=5, sticky="w")
        self.name_entry = ctk.CTkEntry(scroll_frame, width=300)
        self.name_entry.grid(row=row, column=1, pady=5, sticky="ew")
        row += 1
        
        # 説明
        ctk.CTkLabel(scroll_frame, text="説明:").grid(row=row, column=0, pady=5, sticky="w")
        self.description_entry = ctk.CTkEntry(scroll_frame, width=300)
        self.description_entry.grid(row=row, column=1, pady=5, sticky="ew")
        row += 1
        
        # セパレータ
        ctk.CTkFrame(scroll_frame, height=2, fg_color="gray50").grid(
            row=row, column=0, columnspan=2, pady=10, sticky="ew"
        )
        row += 1
        
        # リサイズ設定セクション
        ctk.CTkLabel(scroll_frame, text="リサイズ設定", font=("", 16, "bold")).grid(
            row=row, column=0, columnspan=2, pady=(0, 10), sticky="w"
        )
        row += 1
        
        # リサイズモード
        ctk.CTkLabel(scroll_frame, text="リサイズモード:").grid(row=row, column=0, pady=5, sticky="w")
        self.resize_mode_var = ctk.StringVar()
        self.resize_mode_menu = ctk.CTkOptionMenu(
            scroll_frame,
            variable=self.resize_mode_var,
            values=["none", "width", "height", "longest_side", "percentage"],
            command=self._on_resize_mode_change
        )
        self.resize_mode_menu.grid(row=row, column=1, pady=5, sticky="ew")
        row += 1
        
        # リサイズ値
        ctk.CTkLabel(scroll_frame, text="リサイズ値:").grid(row=row, column=0, pady=5, sticky="w")
        value_frame = ctk.CTkFrame(scroll_frame, fg_color="transparent")
        value_frame.grid(row=row, column=1, pady=5, sticky="ew")
        self.resize_value_entry = ctk.CTkEntry(value_frame, width=100)
        self.resize_value_entry.pack(side="left")
        self.resize_unit_label = ctk.CTkLabel(value_frame, text="px")
        self.resize_unit_label.pack(side="left", padx=5)
        row += 1
        
        # アスペクト比維持
        self.aspect_ratio_var = ctk.BooleanVar()
        self.aspect_ratio_check = ctk.CTkCheckBox(
            scroll_frame,
            text="アスペクト比を維持",
            variable=self.aspect_ratio_var
        )
        self.aspect_ratio_check.grid(row=row, column=1, pady=5, sticky="w")
        row += 1
        
        # セパレータ
        ctk.CTkFrame(scroll_frame, height=2, fg_color="gray50").grid(
            row=row, column=0, columnspan=2, pady=10, sticky="ew"
        )
        row += 1
        
        # 出力設定セクション
        ctk.CTkLabel(scroll_frame, text="出力設定", font=("", 16, "bold")).grid(
            row=row, column=0, columnspan=2, pady=(0, 10), sticky="w"
        )
        row += 1
        
        # 出力フォーマット
        ctk.CTkLabel(scroll_frame, text="出力フォーマット:").grid(row=row, column=0, pady=5, sticky="w")
        self.format_var = ctk.StringVar()
        self.format_menu = ctk.CTkOptionMenu(
            scroll_frame,
            variable=self.format_var,
            values=["original", "jpeg", "png", "webp"],
            command=self._on_format_change
        )
        self.format_menu.grid(row=row, column=1, pady=5, sticky="ew")
        row += 1
        
        # 品質
        ctk.CTkLabel(scroll_frame, text="品質:").grid(row=row, column=0, pady=5, sticky="w")
        quality_frame = ctk.CTkFrame(scroll_frame, fg_color="transparent")
        quality_frame.grid(row=row, column=1, pady=5, sticky="ew")
        self.quality_slider = ctk.CTkSlider(
            quality_frame,
            from_=1,
            to=100,
            number_of_steps=99
        )
        self.quality_slider.pack(side="left", fill="x", expand=True)
        self.quality_label = ctk.CTkLabel(quality_frame, text="85", width=30)
        self.quality_label.pack(side="left", padx=5)
        self.quality_slider.configure(command=self._on_quality_change)
        row += 1
        
        # WebPロスレス
        self.webp_lossless_var = ctk.BooleanVar()
        self.webp_lossless_check = ctk.CTkCheckBox(
            scroll_frame,
            text="WebPロスレス圧縮",
            variable=self.webp_lossless_var
        )
        self.webp_lossless_check.grid(row=row, column=1, pady=5, sticky="w")
        row += 1
        
        # メタデータ保持
        self.preserve_metadata_var = ctk.BooleanVar()
        self.preserve_metadata_check = ctk.CTkCheckBox(
            scroll_frame,
            text="メタデータを保持",
            variable=self.preserve_metadata_var
        )
        self.preserve_metadata_check.grid(row=row, column=1, pady=5, sticky="w")
        row += 1
        
        # セパレータ
        ctk.CTkFrame(scroll_frame, height=2, fg_color="gray50").grid(
            row=row, column=0, columnspan=2, pady=10, sticky="ew"
        )
        row += 1
        
        # 圧縮設定セクション
        ctk.CTkLabel(scroll_frame, text="圧縮設定", font=("", 16, "bold")).grid(
            row=row, column=0, columnspan=2, pady=(0, 10), sticky="w"
        )
        row += 1
        
        # 圧縮有効
        self.compression_var = ctk.BooleanVar()
        self.compression_check = ctk.CTkCheckBox(
            scroll_frame,
            text="圧縮を有効にする",
            variable=self.compression_var,
            command=self._on_compression_change
        )
        self.compression_check.grid(row=row, column=1, pady=5, sticky="w")
        row += 1
        
        # 目標サイズ
        self.target_size_label = ctk.CTkLabel(scroll_frame, text="目標サイズ (KB):")
        self.target_size_label.grid(row=row, column=0, pady=5, sticky="w")
        self.target_size_entry = ctk.CTkEntry(scroll_frame, width=100)
        self.target_size_entry.grid(row=row, column=1, pady=5, sticky="w")
        row += 1
        
        # バランス
        self.balance_label = ctk.CTkLabel(scroll_frame, text="サイズ/品質バランス:")
        self.balance_label.grid(row=row, column=0, pady=5, sticky="w")
        balance_frame = ctk.CTkFrame(scroll_frame, fg_color="transparent")
        balance_frame.grid(row=row, column=1, pady=5, sticky="ew")
        self.balance_slider = ctk.CTkSlider(
            balance_frame,
            from_=1,
            to=10,
            number_of_steps=9
        )
        self.balance_slider.pack(side="left", fill="x", expand=True)
        self.balance_value_label = ctk.CTkLabel(balance_frame, text="5", width=30)
        self.balance_value_label.pack(side="left", padx=5)
        self.balance_slider.configure(command=self._on_balance_change)
        row += 1
        
        # セパレータ
        ctk.CTkFrame(scroll_frame, height=2, fg_color="gray50").grid(
            row=row, column=0, columnspan=2, pady=10, sticky="ew"
        )
        row += 1
        
        # ファイル名設定セクション
        ctk.CTkLabel(scroll_frame, text="ファイル名設定", font=("", 16, "bold")).grid(
            row=row, column=0, columnspan=2, pady=(0, 10), sticky="w"
        )
        row += 1
        
        # プレフィックス
        ctk.CTkLabel(scroll_frame, text="プレフィックス:").grid(row=row, column=0, pady=5, sticky="w")
        self.prefix_entry = ctk.CTkEntry(scroll_frame)
        self.prefix_entry.grid(row=row, column=1, pady=5, sticky="ew")
        row += 1
        
        # サフィックス
        ctk.CTkLabel(scroll_frame, text="サフィックス:").grid(row=row, column=0, pady=5, sticky="w")
        self.suffix_entry = ctk.CTkEntry(scroll_frame)
        self.suffix_entry.grid(row=row, column=1, pady=5, sticky="ew")
        row += 1
        
        # ボタンフレーム
        button_frame = ctk.CTkFrame(self)
        button_frame.grid(row=1, column=0, sticky="ew", padx=10, pady=10)
        
        # キャンセルボタン
        cancel_btn = ctk.CTkButton(
            button_frame,
            text="キャンセル",
            command=self.destroy,
            width=100
        )
        cancel_btn.pack(side="right", padx=5)
        
        # 保存ボタン
        save_btn = ctk.CTkButton(
            button_frame,
            text="保存",
            command=self._save_preset,
            width=100
        )
        save_btn.pack(side="right", padx=5)
        
    def _load_preset_data(self):
        """プリセットデータを読み込む"""
        self.name_entry.insert(0, self.preset.name)
        self.description_entry.insert(0, self.preset.description)
        self.resize_mode_var.set(self.preset.resize_mode)
        self.resize_value_entry.insert(0, str(self.preset.resize_value))
        self.aspect_ratio_var.set(self.preset.maintain_aspect_ratio)
        self.format_var.set(self.preset.output_format)
        self.quality_slider.set(self.preset.quality)
        self.webp_lossless_var.set(self.preset.webp_lossless)
        self.preserve_metadata_var.set(self.preset.preserve_metadata)
        self.compression_var.set(self.preset.enable_compression)
        if self.preset.target_size_kb:
            self.target_size_entry.insert(0, str(self.preset.target_size_kb))
        self.balance_slider.set(self.preset.balance)
        self.prefix_entry.insert(0, self.preset.prefix)
        self.suffix_entry.insert(0, self.preset.suffix)
        
        # 初期状態の更新
        self._on_resize_mode_change(self.preset.resize_mode)
        self._on_format_change(self.preset.output_format)
        self._on_quality_change(self.preset.quality)
        self._on_balance_change(self.preset.balance)
        self._on_compression_change()
        
    def _on_resize_mode_change(self, mode: str):
        """リサイズモード変更時"""
        if mode == "percentage":
            self.resize_unit_label.configure(text="%")
        else:
            self.resize_unit_label.configure(text="px")
            
        if mode == "none":
            self.resize_value_entry.configure(state="disabled")
            self.aspect_ratio_check.configure(state="disabled")
        else:
            self.resize_value_entry.configure(state="normal")
            self.aspect_ratio_check.configure(state="normal")
            
    def _on_format_change(self, format: str):
        """フォーマット変更時"""
        if format in ["jpeg", "webp"]:
            self.quality_slider.configure(state="normal")
            self.quality_label.configure(text_color=("black", "white"))
        else:
            self.quality_slider.configure(state="disabled")
            self.quality_label.configure(text_color="gray")
            
        if format == "webp":
            self.webp_lossless_check.configure(state="normal")
        else:
            self.webp_lossless_check.configure(state="disabled")
            
    def _on_quality_change(self, value: float):
        """品質変更時"""
        self.quality_label.configure(text=str(int(value)))
        
    def _on_balance_change(self, value: float):
        """バランス変更時"""
        self.balance_value_label.configure(text=str(int(value)))
        
    def _on_compression_change(self):
        """圧縮設定変更時"""
        if self.compression_var.get():
            self.target_size_label.configure(state="normal")
            self.target_size_entry.configure(state="normal")
            self.balance_label.configure(state="normal")
            self.balance_slider.configure(state="normal")
        else:
            self.target_size_label.configure(state="disabled")
            self.target_size_entry.configure(state="disabled")
            self.balance_label.configure(state="disabled")
            self.balance_slider.configure(state="disabled")
            
    def _save_preset(self):
        """プリセットを保存"""
        # 入力値の検証
        name = self.name_entry.get().strip()
        if not name:
            messagebox.showerror("エラー", "プリセット名を入力してください")
            return
            
        # プリセットデータを更新
        self.preset.name = name
        self.preset.description = self.description_entry.get().strip()
        self.preset.resize_mode = self.resize_mode_var.get()
        
        try:
            self.preset.resize_value = int(self.resize_value_entry.get())
        except ValueError:
            self.preset.resize_value = 1920
            
        self.preset.maintain_aspect_ratio = self.aspect_ratio_var.get()
        self.preset.output_format = self.format_var.get()
        self.preset.quality = int(self.quality_slider.get())
        self.preset.webp_lossless = self.webp_lossless_var.get()
        self.preset.preserve_metadata = self.preserve_metadata_var.get()
        self.preset.enable_compression = self.compression_var.get()
        
        target_size = self.target_size_entry.get().strip()
        if target_size:
            try:
                self.preset.target_size_kb = int(target_size)
            except ValueError:
                self.preset.target_size_kb = None
        else:
            self.preset.target_size_kb = None
            
        self.preset.balance = int(self.balance_slider.get())
        self.preset.prefix = self.prefix_entry.get()
        self.preset.suffix = self.suffix_entry.get()
        
        self.result = self.preset
        self.destroy()


class PresetManagerDialog(ctk.CTkToplevel):
    """プリセット管理ダイアログ"""
    
    def __init__(self, parent, preset_manager: PresetManager):
        super().__init__(parent)
        
        self.preset_manager = preset_manager
        self.on_preset_selected: Optional[Callable[[PresetData], None]] = None
        
        self.title("プリセット管理")
        self.geometry("700x500")
        self.minsize(600, 400)
        
        # モーダルダイアログ設定
        self.transient(parent)
        
        self._setup_ui()
        self._load_presets()
        
        # ウィンドウを中央に配置
        self.update_idletasks()
        x = (self.winfo_screenwidth() // 2) - (self.winfo_width() // 2)
        y = (self.winfo_screenheight() // 2) - (self.winfo_height() // 2)
        self.geometry(f"+{x}+{y}")
        
    def _setup_ui(self):
        """UIをセットアップ"""
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)
        
        # メインフレーム
        main_frame = ctk.CTkFrame(self)
        main_frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        main_frame.grid_columnconfigure(0, weight=1)
        main_frame.grid_rowconfigure(1, weight=1)
        
        # ヘッダー
        header_frame = ctk.CTkFrame(main_frame)
        header_frame.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        
        ctk.CTkLabel(header_frame, text="プリセット一覧", font=("", 18, "bold")).pack(side="left", padx=10, pady=10)
        
        # ツールバー
        toolbar = ctk.CTkFrame(header_frame)
        toolbar.pack(side="right", padx=10, pady=5)
        
        ctk.CTkButton(toolbar, text="新規作成", command=self._new_preset, width=80).pack(side="left", padx=2)
        ctk.CTkButton(toolbar, text="インポート", command=self._import_preset, width=80).pack(side="left", padx=2)
        
        # リストフレーム
        list_frame = ctk.CTkFrame(main_frame)
        list_frame.grid(row=1, column=0, sticky="nsew")
        list_frame.grid_columnconfigure(0, weight=1)
        list_frame.grid_rowconfigure(0, weight=1)
        
        # プリセットリスト（スクロール可能）
        self.preset_list = ctk.CTkScrollableFrame(list_frame)
        self.preset_list.grid(row=0, column=0, sticky="nsew")
        self.preset_list.grid_columnconfigure(0, weight=1)
        
        # ボタンフレーム
        button_frame = ctk.CTkFrame(self)
        button_frame.grid(row=1, column=0, sticky="ew", padx=10, pady=10)
        
        ctk.CTkButton(button_frame, text="閉じる", command=self.destroy, width=100).pack(side="right", padx=5)
        
    def _load_presets(self):
        """プリセットを読み込む"""
        # 既存のアイテムをクリア
        for widget in self.preset_list.winfo_children():
            widget.destroy()
            
        # プリセットを表示
        presets = self.preset_manager.get_all_presets()
        
        # 組み込みプリセット
        builtin_label = ctk.CTkLabel(self.preset_list, text="組み込みプリセット", font=("", 14, "bold"))
        builtin_label.grid(row=0, column=0, pady=(0, 5), sticky="w")
        
        row = 1
        for preset in [p for p in presets if p.is_builtin]:
            item = self._create_preset_item(preset, row)
            row += 1
            
        # ユーザープリセット
        if any(not p.is_builtin for p in presets):
            user_label = ctk.CTkLabel(self.preset_list, text="ユーザープリセット", font=("", 14, "bold"))
            user_label.grid(row=row, column=0, pady=(10, 5), sticky="w")
            row += 1
            
            for preset in [p for p in presets if not p.is_builtin]:
                item = self._create_preset_item(preset, row)
                row += 1
                
    def _create_preset_item(self, preset: PresetData, row: int) -> ctk.CTkFrame:
        """プリセットアイテムを作成"""
        item_frame = ctk.CTkFrame(self.preset_list, corner_radius=5)
        item_frame.grid(row=row, column=0, pady=2, sticky="ew", padx=(20, 0))
        item_frame.grid_columnconfigure(1, weight=1)
        
        # アイコン
        icon_label = "標準" if preset.is_builtin else "ユーザー"
        ctk.CTkLabel(item_frame, text=icon_label, width=40).grid(row=0, column=0, padx=5, pady=5)
        
        # 名前と説明
        info_frame = ctk.CTkFrame(item_frame, fg_color="transparent")
        info_frame.grid(row=0, column=1, padx=5, pady=5, sticky="ew")
        
        ctk.CTkLabel(info_frame, text=preset.name, font=("", 12, "bold"), anchor="w").pack(anchor="w")
        if preset.description:
            ctk.CTkLabel(info_frame, text=preset.description, font=("", 10), text_color="gray", anchor="w").pack(anchor="w")
            
        # ボタン
        button_frame = ctk.CTkFrame(item_frame, fg_color="transparent")
        button_frame.grid(row=0, column=2, padx=5, pady=5)
        
        ctk.CTkButton(
            button_frame,
            text="適用",
            command=lambda p=preset: self._apply_preset(p),
            width=60,
            height=28
        ).pack(side="left", padx=2)
        
        if not preset.is_builtin:
            ctk.CTkButton(
                button_frame,
                text="編集",
                command=lambda p=preset: self._edit_preset(p),
                width=60,
                height=28
            ).pack(side="left", padx=2)
            
            ctk.CTkButton(
                button_frame,
                text="削除",
                command=lambda p=preset: self._delete_preset(p),
                width=60,
                height=28,
                fg_color="red",
                hover_color="darkred"
            ).pack(side="left", padx=2)
            
        ctk.CTkButton(
            button_frame,
            text="エクスポート",
            command=lambda p=preset: self._export_preset(p),
            width=80,
            height=28
        ).pack(side="left", padx=2)
        
        return item_frame
        
    def _apply_preset(self, preset: PresetData):
        """プリセットを適用"""
        if self.on_preset_selected:
            self.on_preset_selected(preset)
        self.destroy()
        
    def _new_preset(self):
        """新規プリセット作成"""
        dialog = PresetEditDialog(self, is_new=True)
        self.wait_window(dialog)
        
        if dialog.result:
            self.preset_manager.add_preset(dialog.result)
            self._load_presets()
            
    def _edit_preset(self, preset: PresetData):
        """プリセット編集"""
        dialog = PresetEditDialog(self, preset=preset, is_new=False)
        self.wait_window(dialog)
        
        if dialog.result:
            self.preset_manager.update_preset(preset.name, dialog.result)
            self._load_presets()
            
    def _delete_preset(self, preset: PresetData):
        """プリセット削除"""
        if messagebox.askyesno("確認", f"プリセット '{preset.name}' を削除しますか？"):
            self.preset_manager.delete_preset(preset.name)
            self._load_presets()
            
    def _export_preset(self, preset: PresetData):
        """プリセットエクスポート"""
        filepath = filedialog.asksaveasfilename(
            title="プリセットのエクスポート",
            defaultextension=".json",
            filetypes=[("JSONファイル", "*.json")]
        )
        
        if filepath:
            if self.preset_manager.export_preset(preset.name, Path(filepath)):
                messagebox.showinfo("成功", "プリセットをエクスポートしました")
            else:
                messagebox.showerror("エラー", "プリセットのエクスポートに失敗しました")
                
    def _import_preset(self):
        """プリセットインポート"""
        filepath = filedialog.askopenfilename(
            title="プリセットのインポート",
            filetypes=[("JSONファイル", "*.json")]
        )
        
        if filepath:
            imported = self.preset_manager.import_preset(Path(filepath))
            if imported:
                messagebox.showinfo("成功", f"プリセット '{imported.name}' をインポートしました")
                self._load_presets()
            else:
                messagebox.showerror("エラー", "プリセットのインポートに失敗しました")
