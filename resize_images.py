#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
画像リサイズ・圧縮スクリプト 改良版

指定されたディレクトリから画像ファイル(.jpg, .png)を検索し、
指定された幅にリサイズして、圧縮率を指定してJPEG形式で保存します。
処理の進捗表示、サイズ情報、中断・再開機能を備えています。
"""

import os
import sys
import argparse
import time
import signal
import traceback
from pathlib import Path
from datetime import datetime
from tqdm import tqdm
from resize_core import (
    resize_and_compress_image as core_resize_and_compress_image,
    find_image_files as core_find_image_files,
    create_directory_with_permissions,
    get_directory_size as core_get_directory_size,
    calculate_reduction_rate as core_calculate_reduction_rate,
    format_file_size as core_format_file_size,
    normalize_long_path,
)
from loguru import logger

# コア機能をインポート

# デバッグモード設定
DEBUG_MODE = False  # コマンドライン引数で上書き可能

# シグナルハンドラー変数
interrupt_requested = False


# Ctrl+Cハンドラー
def signal_handler(sig, frame):
    """シグナルハンドラー関数"""
    global interrupt_requested
    logger.warning("\n中断シグナルを受信しました。安全に処理を停止します...")
    interrupt_requested = True


# シグナルハンドラーを登録
signal.signal(signal.SIGINT, signal_handler)


def parse_args():
    """コマンドライン引数を解析する関数"""
    parser = argparse.ArgumentParser(
        description="画像ファイルを指定された幅にリサイズし、JPEG形式で圧縮して保存します。"
    )
    parser.add_argument("-s", "--source", required=True, help="入力元のディレクトリパス")
    parser.add_argument("-d", "--dest", required=True, help="出力先のディレクトリパス")
    parser.add_argument(
        "-w",
        "--width",
        type=int,
        default=1280,
        help="リサイズ後の最大幅 (デフォルト: 1280)",
    )
    parser.add_argument(
        "-q",
        "--quality",
        type=int,
        default=85,
        help="JPEGの品質 (0-100、デフォルト: 85)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="ドライランモード（実際にファイルを保存せずシミュレートする）",
    )
    parser.add_argument("--resume", action="store_true", help="既存の出力ファイルがあればスキップする")
    parser.add_argument(
        "--log-level",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        help="ログレベルを設定する (デフォルト: INFO)",
    )
    parser.add_argument("--check-disk", action="store_true", help="処理前にディスク容量を確認する")
    parser.add_argument(
        "--debug",
        action="store_true",
        help="デバッグモードを有効にする（エラー時に詳細な情報を表示）",
    )

    return parser.parse_args()


def setup_logger(verbose=False):
    """
    ロガーの設定を行う関数
    """
    # デフォルトのロガー設定を削除
    logger.remove()

    # ログレベルの設定
    log_level = "DEBUG" if verbose or DEBUG_MODE else "INFO"

    # 画面出力用のロガー設定
    logger.add(
        sys.stderr,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <level>{message}</level>",
        level=log_level,
    )

    # ファイル出力用のロガー設定
    # ログファイルの出力先ディレクトリを指定
    log_dir = Path("/home/tn/projects/tools/karukuresize/log")
    # ディレクトリが存在しない場合は作成
    log_dir.mkdir(parents=True, exist_ok=True)

    # ログファイル名を生成
    log_file_name_only = f"process_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S_%f')}.log"
    # 完全なログファイルパスを構築
    full_log_path = log_dir / log_file_name_only

    logger.add(
        full_log_path,  # 完全なパスを使用
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {module}:{function}:{line} - {message}",
        level="DEBUG",  # ファイルログは常にDEBUGレベルで出力
        rotation="10 MB",  # 10MBでローテーション
        retention="7 days",  # 7日間保持
        encoding="utf-8",
    )
    return str(full_log_path)  # 文字列として返す


def get_destination_path(source_path, source_dir, dest_dir):
    """元のパスから新しい出力先パスを生成する（Windows対応強化版）"""
    # 長いパス対応のため、入力パスを正規化
    source_path = Path(normalize_long_path(source_path))
    source_dir = Path(normalize_long_path(source_dir))
    dest_dir = Path(normalize_long_path(dest_dir))

    # 相対パスを取得
    try:
        rel_path = source_path.relative_to(source_dir)
    except ValueError:
        # 相対パスを取得できない場合はファイル名のみを使用
        rel_path = Path(source_path.name)

    # 新しい出力先パスを生成
    dest_path = dest_dir / rel_path

    # ファイル名部分を安全化（Windows互換に）
    parent_dir = dest_path.parent
    safe_name = sanitize_filename(dest_path.name)

    # 拡張子を.jpgに変更（すでにjpgの場合も含めて統一）
    name_without_ext = Path(safe_name).stem
    dest_path = parent_dir / f"{name_without_ext}.jpg"

    # 長いパス対応のうえでパスを返す
    return Path(normalize_long_path(dest_path))


def sanitize_filename(filename):
    """ファイル名をWindows互換に変換"""
    # Windows禁止文字を置換
    for char in '<>:"/\\|?*':
        filename = filename.replace(char, "_")

    # 空のファイル名の場合
    if not filename:
        return "untitled"

    return filename


def get_system_encoding():
    """システムに適したエンコーディングを返す"""
    if os.name == "nt":  # Windows
        return "cp932"
    return "utf-8"


def main():
    """メイン関数"""
    try:
        args = parse_args()

        # デバッグモードの設定
        global DEBUG_MODE
        DEBUG_MODE = args.debug

        # ロガー設定
        log_filename = setup_logger(verbose=args.debug)
        logger.info(f"CLIモードで起動しました。ログファイル: {log_filename}")
        logger.info(f"Pythonバージョン: {sys.version}")
        logger.info(f"OS情報: {os.name} - {sys.platform}")

        # シグナルハンドラの設定
        signal.signal(signal.SIGINT, signal_handler)

        # コマンドライン引数のログ出力
        logger.debug(f"引数: {args}")

        # 入力値のバリデーション
        source_dir = Path(args.source)
        dest_dir = Path(args.dest)

        if not source_dir.exists():
            logger.error(f"入力ディレクトリが存在しません: {source_dir}")
            return 1

        if not dest_dir.exists():
            logger.info(f"出力ディレクトリを作成します: {dest_dir}")
            try:
                os.makedirs(dest_dir, exist_ok=True)
            except Exception as e:
                error_trace = traceback.format_exc()
                logger.error(f"ディレクトリ作成失敗: {e}")
                if DEBUG_MODE:
                    logger.error(f"トレースバック情報:\n{error_trace}")
                return 1

        # 画像ファイルを検索
        try:
            image_files = core_find_image_files(source_dir)

            if not image_files:
                logger.warning(f"ディレクトリ '{args.source}' には画像ファイルが見つかりませんでした。")
                return 0
        except Exception as e:
            logger.error(f"画像ファイル検索中にエラーが発生しました: {e}")
            return 1

    except Exception as e:
        logger.error(f"予期せぬエラーが発生しました: {e}")
        if DEBUG_MODE:
            error_trace = traceback.format_exc()
            logger.error(f"トレースバック情報:\n{error_trace}")
        return 1

    logger.info(f"{'【ドライラン】' if args.dry_run else ''}処理を開始します。")
    logger.info(f"処理対象画像ファイル数: {len(image_files)}")
    logger.info(f"ソースディレクトリ: {args.source}")
    logger.info(f"出力先ディレクトリ: {args.dest}")
    logger.info(f"リサイズ幅: {args.width}px")
    logger.info(f"JPEG品質: {args.quality}%")

    # 処理開始前にソースディレクトリの総サイズを取得（ドライラン時のみ）
    if args.dry_run:
        total_size_before_display = core_get_directory_size(args.source)
        logger.info(f"処理前の総合サイズ: {core_format_file_size(total_size_before_display)}")

    # 出力ディレクトリを作成 (存在しない場合)
    # create_output_directory(args.dest, args.dry_run)
    success, created_path = create_directory_with_permissions(args.dest)
    if not success:
        logger.error(f"出力ディレクトリの作成に失敗しました: {created_path}")
        return 1
    elif created_path:
        logger.info(f"出力ディレクトリを作成しました: {created_path}")

    image_files = core_find_image_files(args.source)
    if not image_files:
        logger.warning("処理対象の画像ファイルが見つかりませんでした。")
        return 1

    # 処理時間の計測開始
    start_time = time.time()

    # 初期化
    processed_count = 0
    skipped_count = 0
    error_count = 0
    total_size_before = 0
    total_size_after = 0
    results = []

    # tqdmで進捗バーを表示
    with tqdm(total=len(image_files), desc="画像処理中", unit="files") as progress:
        for idx, source_path in enumerate(image_files, 1):
            # 中断リクエストがあれば処理を停止
            if interrupt_requested:
                logger.info("ユーザーによる中断リクエストにより処理を停止します")
                # 処理途中の場合は進捗を保存
                if not args.dry_run:
                    remaining = image_files[idx:]
                    logger.info(f"残り{len(remaining)}個のファイルがあります。")
                break

            # 元のファイルサイズを取得
            try:
                file_size_before = source_path.stat().st_size
                total_size_before += file_size_before
            except Exception:
                file_size_before = 0

            # 出力先パスを取得
            dest_path = get_destination_path(source_path, args.source, args.dest)

            # 処理状況を表示
            person_name = source_path.parent.name
            qualification_name = source_path.stem

            # 詳細情報表示（進捗バーの下に表示）
            tqdm.write(f"[{idx}/{len(image_files)}] 処理中: {source_path}")
            tqdm.write(f"  - 人物名: {person_name}")
            tqdm.write(f"  - 資格名: {qualification_name}")
            tqdm.write(f"  - 元サイズ: {core_format_file_size(file_size_before)}")
            tqdm.write(f"  → 出力先: {dest_path}")

            # 画像をリサイズして圧縮
            # resize_coreの新しいシグネチャに合わせて呼び出し
            success, skipped, new_size_kb = core_resize_and_compress_image(
                source_path=source_path,
                dest_path=dest_path,
                target_width=args.width,
                quality=args.quality,
                format="original",  # オリジナル形式を維持
                dry_run=args.dry_run
            )
            
            # ドライランモードの場合、別の形式で返される可能性があるため
            # 互換性のために元の動作をエミュレート
            if success:
                # 画像のサイズ情報を取得
                from PIL import Image
                try:
                    with Image.open(source_path) as img:
                        original_size = img.size
                    if not args.dry_run and dest_path.exists():
                        with Image.open(dest_path) as img:
                            new_size = img.size
                    else:
                        # ドライランの場合は計算
                        aspect_ratio = original_size[1] / original_size[0]
                        new_size = (args.width, int(args.width * aspect_ratio))
                except Exception:
                    original_size = None
                    new_size = None
            else:
                original_size = None
                new_size = None

            result_item = {
                "path": str(source_path),
                "name": f"{person_name}/{qualification_name}",
                "original_size": core_format_file_size(file_size_before),
            }

            if original_size and new_size:
                tqdm.write(f"  ✓ サイズ変更: {original_size[0]}x{original_size[1]} → {new_size[0]}x{new_size[1]}")
                processed_count += 1
                result_item["status"] = "success"

                # ファイルサイズ情報の表示
                if args.dry_run:
                    # ドライランの場合は推定サイズを使用
                    if new_size_kb:
                        estimated_size = new_size_kb * 1024  # KBをバイトに変換
                        estimated_size_str = core_format_file_size(estimated_size)
                        size_diff = file_size_before - estimated_size
                        reduction_percent = (size_diff / file_size_before * 100) if file_size_before > 0 else 0
                        tqdm.write(
                            f"  ✓ 予測ファイルサイズ: {core_format_file_size(file_size_before)} → {estimated_size_str} ({reduction_percent:.1f}% 削減予定)"
                        )
                        total_size_after += estimated_size
                        result_item["new_size"] = estimated_size_str
                        result_item["reduction"] = f"{reduction_percent:.1f}"
                # 実際の処理結果のファイルサイズを取得（ドライランでない場合）
                elif not args.dry_run and dest_path.exists():
                    try:
                        file_size_after = dest_path.stat().st_size
                        total_size_after += file_size_after
                        size_diff = file_size_before - file_size_after
                        reduction_percent = (size_diff / file_size_before * 100) if file_size_before > 0 else 0
                        tqdm.write(
                            f"  ✓ ファイルサイズ: {core_format_file_size(file_size_before)} → {core_format_file_size(file_size_after)} ({reduction_percent:.1f}% 削減)"
                        )

                        result_item["new_size"] = core_format_file_size(file_size_after)
                        result_item["reduction"] = f"{reduction_percent:.1f}"
                    except Exception as e:
                        logger.debug(f"ファイルサイズ取得エラー: {e}")
                        result_item["new_size"] = "不明"
                        result_item["reduction"] = "0"
            elif original_size is None:
                tqdm.write("  ✗ エラー: 画像処理に失敗しました")
                error_count += 1
                result_item["status"] = "error"
            else:
                tqdm.write("  ✗ スキップしました")
                skipped_count += 1
                result_item["status"] = "skipped"

            results.append(result_item)
            tqdm.write("")  # 空行

            # 進捗バーを更新
            progress.update(1)

    elapsed_time = time.time() - start_time

    print("-" * 80)
    print(f"{'【ドライラン結果】' if args.dry_run else '【処理結果】'}")
    print(f"成功: {processed_count}ファイル")
    print(f"エラー: {error_count}ファイル")
    print(f"スキップ: {skipped_count}ファイル")

    if total_size_before > 0 and total_size_after > 0:
        size_diff = total_size_before - total_size_after
        reduction_percent = size_diff / total_size_before * 100
        print(
            f"合計サイズ削減: {core_format_file_size(total_size_before)} → {core_format_file_size(total_size_after)} ({reduction_percent:.1f}% 削減)"
        )

    if not args.dry_run:
        # ディレクトリサイズ情報
        dest_size = core_get_directory_size(args.dest)
        print(f"処理後の総合サイズ: {core_format_file_size(dest_size)}")
        overall_reduction = core_calculate_reduction_rate(args.source, args.dest)
        print(f"全体の削減率: {overall_reduction:.1f}%")

    print(f"処理時間: {elapsed_time:.2f}秒")

    # HTMLレポート生成 (機能が存在しないためコメントアウト)
    # report_file = generate_html_report(results, args.source, args.dest)
    # if report_file:
    #     logger.info(f"HTMLレポートを生成しました: {report_file}")

    if args.dry_run:
        print("\n実際に処理を実行するには、--dry-runオプションを外して再実行してください。")

    return 0


if __name__ == "__main__":
    sys.exit(main())
