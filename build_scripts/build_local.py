#!/usr/bin/env python
"""
ローカルビルド用スクリプト
各プラットフォームでKarukuResizeをビルドします
"""

import sys
import os
import subprocess
import platform
import shutil
from pathlib import Path

def clean_build_dirs():
    """ビルドディレクトリをクリーンアップ"""
    dirs_to_clean = ['build', 'dist', '__pycache__']
    for dir_name in dirs_to_clean:
        if Path(dir_name).exists():
            print(f"Cleaning {dir_name}...")
            shutil.rmtree(dir_name)
    
    # .specファイルのバックアップ
    spec_file = Path('karukuresize.spec')
    if spec_file.exists():
        backup_file = spec_file.with_suffix('.spec.bak')
        shutil.copy2(spec_file, backup_file)
        print(f"Backed up {spec_file} to {backup_file}")

def install_dependencies():
    """必要な依存関係をインストール"""
    print("Installing dependencies...")
    subprocess.run([sys.executable, '-m', 'pip', 'install', '--upgrade', 'pip'], check=True)
    subprocess.run([sys.executable, '-m', 'pip', 'install', '-e', '.'], check=True)
    subprocess.run([sys.executable, '-m', 'pip', 'install', 'pyinstaller'], check=True)

def build_executable():
    """PyInstallerで実行ファイルをビルド"""
    print(f"Building for {platform.system()}...")
    
    # PyInstallerコマンド
    cmd = [
        sys.executable, '-m', 'PyInstaller',
        'karukuresize.spec',
        '--clean',
        '--noconfirm'
    ]
    
    # ビルド実行
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode != 0:
        print("Build failed!")
        print(result.stderr)
        return False
    
    print("Build completed successfully!")
    return True

def create_package():
    """配布用パッケージを作成"""
    system = platform.system()
    dist_dir = Path('dist')
    
    if not dist_dir.exists():
        print("No dist directory found!")
        return
    
    print(f"Creating package for {system}...")
    
    if system == 'Windows':
        # Windowsの場合はZIPファイルを作成
        output_file = 'KarukuResize-Windows.zip'
        shutil.make_archive('KarukuResize-Windows', 'zip', 'dist/KarukuResize')
        print(f"Created {output_file}")
        
    elif system == 'Darwin':  # macOS
        # macOSの場合はZIPファイルを作成
        os.chdir('dist')
        if Path('KarukuResize.app').exists():
            subprocess.run(['zip', '-r', '../KarukuResize-macOS.zip', 'KarukuResize.app'], check=True)
        else:
            subprocess.run(['zip', '-r', '../KarukuResize-macOS.zip', 'KarukuResize'], check=True)
        os.chdir('..')
        print("Created KarukuResize-macOS.zip")
        
    else:  # Linux
        # Linuxの場合はtar.gzファイルを作成
        os.chdir('dist')
        subprocess.run(['tar', '-czf', '../KarukuResize-Linux.tar.gz', 'KarukuResize'], check=True)
        os.chdir('..')
        print("Created KarukuResize-Linux.tar.gz")

def main():
    """メイン処理"""
    print("=== KarukuResize Local Build Script ===")
    print(f"Platform: {platform.system()}")
    print(f"Python: {sys.version}")
    print()
    
    # ビルドディレクトリのクリーンアップ
    if input("Clean build directories? (y/N): ").lower() == 'y':
        clean_build_dirs()
    
    # 依存関係のインストール
    if input("Install/update dependencies? (y/N): ").lower() == 'y':
        install_dependencies()
    
    # ビルド実行
    if build_executable():
        # パッケージ作成
        if input("Create distribution package? (y/N): ").lower() == 'y':
            create_package()
        
        print("\nBuild completed! Check the 'dist' directory for the output.")
    else:
        print("\nBuild failed! Check the error messages above.")
        sys.exit(1)

if __name__ == '__main__':
    main()