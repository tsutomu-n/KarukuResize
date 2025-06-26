from PIL import Image
import sys

if len(sys.argv) > 1:
    file_path = sys.argv[1]
    try:
        with Image.open(file_path) as img:
            print(f"ファイル: {file_path}")
            print(f"Pillowが認識した形式: {img.format}")
            print(f"モード: {img.mode}")
            print(f"サイズ: {img.size}")
            # 他に知りたい情報があれば img.info なども表示
            # print(f"情報: {img.info}")
    except Exception as e:
        print(f"エラー: {e}")
else:
    print("確認したい画像ファイルのパスを引数に指定してください。")
