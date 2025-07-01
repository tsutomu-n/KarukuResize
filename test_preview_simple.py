import customtkinter as ctk
from pathlib import Path
import sys
import io
import time
from PIL import Image, ImageTk

# 必要なモジュールをインポート
try:
    from resize_core import resize_and_compress_image
except ImportError as e:
    print(f"モジュールのインポートに失敗しました: {e}")
    sys.exit(1)

class SimplePreviewTest(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        self.title("シンプルプレビューテスト")
        self.geometry("800x600")
        
        # メインフレーム
        self.main_frame = ctk.CTkFrame(self)
        self.main_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # 画像選択ボタン
        self.select_btn = ctk.CTkButton(
            self.main_frame, 
            text="画像を選択", 
            command=self.select_image
        )
        self.select_btn.pack(pady=10)
        
        # 選択された画像のパス表示
        self.path_label = ctk.CTkLabel(self.main_frame, text="画像が選択されていません")
        self.path_label.pack(pady=5)
        
        # キャンバスフレーム
        self.canvas_frame = ctk.CTkFrame(self.main_frame)
        self.canvas_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # キャンバス
        self.canvas = ctk.CTkCanvas(self.canvas_frame, bg="#f0f0f0")
        self.canvas.pack(fill="both", expand=True)
        
        # 画像参照を保持するリスト
        self._photo_refs = []
        
        # 画像オブジェクト
        self.before_image = None
        self.after_image = None
        
        # ログ表示エリア
        self.log_text = ctk.CTkTextbox(self.main_frame, height=150)
        self.log_text.pack(fill="x", padx=10, pady=10)
        
    def select_image(self):
        # ファイル選択ダイアログ
        file_path = ctk.filedialog.askopenfilename(
            title="画像を選択",
            filetypes=[("画像ファイル", "*.jpg *.jpeg *.png *.webp *.bmp *.gif")]
        )
        
        if not file_path:
            return
            
        # パスを表示
        self.path_label.configure(text=f"選択された画像: {Path(file_path).name}")
        self.add_log(f"画像を読み込みました: {file_path}")
        
        # プレビュー表示
        self.update_preview(file_path)
        
    def update_preview(self, image_path):
        try:
            self.add_log("=== プレビュー生成開始 ===")
            
            # 1. 元画像読み込み
            source_image = Image.open(image_path)
            self.add_log(f"1. 元画像読み込み: {source_image.size}")
            
            # 元画像をキャンバスの左側に表示
            self.before_image = source_image.copy()
            self.update_canvas()
            
            # 2. 圧縮処理
            self.add_log("2. 圧縮処理実行中...")
            output_buffer = io.BytesIO()
            
            start_time = time.time()
            success, error_msg = resize_and_compress_image(
                source_image=source_image,
                output_buffer=output_buffer,
                resize_mode="width",
                resize_value=800,
                quality=85,
                output_format="jpeg",
                exif_handling="keep",
                lanczos_filter=True,
                progressive=False,
                optimize=True,
                webp_lossless=False
            )
            elapsed_time = time.time() - start_time
            
            # 3. 結果確認
            self.add_log(f"3. 圧縮結果: success={success}, error={error_msg}")
            
            if success:
                # 4. バッファサイズ確認
                buffer_size = output_buffer.tell()
                self.add_log(f"4. バッファサイズ: {buffer_size} bytes")
                
                # 5. After画像作成
                output_buffer.seek(0)
                after_image = Image.open(output_buffer)
                self.add_log(f"5. After画像作成: {after_image}")
                
                # 6. After画像コピー
                self.after_image = after_image.copy()
                self.add_log(f"6. After画像コピー完了: {self.after_image.size}")
                
                # UIアップデート
                self.add_log("\n=== UIアップデート ===")
                self.add_log(f"after_image受信: {self.after_image}, size={self.after_image.size}")
                
                # キャンバス更新
                self.update_canvas()
            else:
                self.add_log(f"エラー: {error_msg}")
                
        except Exception as e:
            self.add_log(f"エラー: {str(e)}")
            import traceback
            self.add_log(traceback.format_exc())
    
    def update_canvas(self):
        try:
            self.add_log("\n=== Canvas更新 ===")
            self.add_log(f"before_image: {self.before_image}")
            self.add_log(f"after_image: {self.after_image}")
            
            # キャンバスをクリア
            self.canvas.delete("all")
            self._photo_refs.clear()
            
            # キャンバスのサイズ
            canvas_width = self.canvas.winfo_width()
            canvas_height = self.canvas.winfo_height()
            
            # サイズが0の場合は更新を待つ
            if canvas_width <= 1 or canvas_height <= 1:
                self.add_log(f"キャンバスサイズが不正: {canvas_width}x{canvas_height}、更新を待機")
                self.after(100, self.update_canvas)
                return
            
            # 表示領域の計算
            if self.before_image and self.after_image:
                # 両方の画像がある場合は左右に分割
                before_x = 0
                before_width = canvas_width // 2
                after_x = before_width
                after_width = canvas_width - before_width
                
                # Before画像の表示
                display_before = self.resize_to_fit(self.before_image, before_width, canvas_height)
                before_photo = ImageTk.PhotoImage(display_before)
                self._photo_refs.append(before_photo)
                
                self.canvas.create_image(
                    before_width // 2,
                    canvas_height // 2,
                    image=before_photo,
                    anchor="center"
                )
                
                # After画像の表示
                display_after = self.resize_to_fit(self.after_image, after_width, canvas_height)
                after_photo = ImageTk.PhotoImage(display_after)
                self._photo_refs.append(after_photo)
                
                self.canvas.create_image(
                    before_width + after_width // 2,
                    canvas_height // 2,
                    image=after_photo,
                    anchor="center"
                )
                
                self.add_log(f"After画像表示: {display_after.width}x{display_after.height}")
                
            elif self.before_image:
                # Before画像のみ
                display_before = self.resize_to_fit(self.before_image, canvas_width, canvas_height)
                before_photo = ImageTk.PhotoImage(display_before)
                self._photo_refs.append(before_photo)
                
                self.canvas.create_image(
                    canvas_width // 2,
                    canvas_height // 2,
                    image=before_photo,
                    anchor="center"
                )
            
            # 強制的に再描画
            self.canvas.update_idletasks()
            self.update()
            
        except Exception as e:
            self.add_log(f"キャンバス更新エラー: {str(e)}")
            import traceback
            self.add_log(traceback.format_exc())
    
    def resize_to_fit(self, image, max_width, max_height):
        """画像をキャンバスに収まるようにリサイズ"""
        width, height = image.size
        
        # アスペクト比を維持しながらリサイズ
        if width > max_width or height > max_height:
            ratio = min(max_width / width, max_height / height)
            new_size = (int(width * ratio), int(height * ratio))
            return image.resize(new_size, Image.LANCZOS)
        
        return image
    
    def add_log(self, message):
        self.log_text.insert("end", f"{message}\n")
        self.log_text.see("end")
        print(message)

def main():
    # テーマ設定
    ctk.set_appearance_mode("light")
    ctk.set_default_color_theme("blue")
    
    app = SimplePreviewTest()
    app.mainloop()

if __name__ == "__main__":
    main()
