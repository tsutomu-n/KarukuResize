import customtkinter as ctk
from pathlib import Path
import sys
import io
from PIL import Image

# 必要なモジュールをインポート
try:
    from image_preview import ImagePreviewWidget, ComparisonPreviewWidget
    from resize_core import resize_and_compress_image
except ImportError as e:
    print(f"モジュールのインポートに失敗しました: {e}")
    sys.exit(1)

class TestPreviewApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        self.title("プレビューテスト")
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
        
        # プレビューウィジェット
        self.preview = ComparisonPreviewWidget(self.main_frame)
        self.preview.pack(fill="both", expand=True, padx=10, pady=10)
        
        # ログ表示エリア
        self.log_text = ctk.CTkTextbox(self.main_frame, height=100)
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
            # 元画像をプレビュー
            self.preview.load_before_image(Path(image_path))
            self.add_log("元画像のプレビューを表示しました")
            
            # 変換後画像を生成してプレビュー
            self.generate_preview(image_path)
            
        except Exception as e:
            self.add_log(f"エラー: {str(e)}")
            
    def generate_preview(self, image_path):
        try:
            # 元画像を読み込み
            source_image = Image.open(image_path)
            
            # 出力バッファを作成
            output_buffer = io.BytesIO()
            
            # リサイズ処理を実行
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
            
            if success:
                # 一時ファイルに保存
                import tempfile
                import uuid
                
                temp_dir = Path(tempfile.gettempdir())
                temp_filename = f"preview_{uuid.uuid4().hex}.png"
                temp_path = temp_dir / temp_filename
                
                # バッファから画像を読み込み
                output_buffer.seek(0)
                preview_image = Image.open(output_buffer)
                
                # PNGとして保存
                preview_image.save(temp_path, format='PNG')
                
                # プレビュー表示
                self.preview.load_after_image(temp_path)
                self.add_log(f"変換後画像のプレビューを表示しました: {temp_path}")
                
            else:
                self.add_log(f"プレビュー生成エラー: {error_msg}")
                
        except Exception as e:
            self.add_log(f"プレビュー生成中にエラーが発生: {str(e)}")
            import traceback
            self.add_log(traceback.format_exc())
    
    def add_log(self, message):
        self.log_text.insert("end", f"{message}\n")
        self.log_text.see("end")

def main():
    # テーマ設定
    ctk.set_appearance_mode("light")
    ctk.set_default_color_theme("blue")
    
    app = TestPreviewApp()
    app.mainloop()

if __name__ == "__main__":
    main()
