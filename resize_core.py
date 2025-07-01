#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
画像リサイズ・圧縮ツールのコア機能モジュール

コマンドラインインターフェース(CLI)とグラフィカルユーザーインターフェース(GUI)の
両方から利用可能な共通機能を提供します。
"""

import os
import sys
import json
import shutil
import time
from pathlib import Path
from typing import Optional, Union, Tuple
from PIL import Image, UnidentifiedImageError
from loguru import logger

# Windows固有のエラーコードと対応する日本語メッセージ
WINDOWS_ERROR_MESSAGES = {
    2: "指定されたファイルが見つかりません",
    3: "指定されたパスが見つかりません",
    5: "アクセスが拒否されました。管理者権限で実行するか、ファイルの権限を確認してください",
    32: "ファイルが他のプロセスで使用中です。開いているアプリケーションを閉じてください",
    80: "ファイル名が正しくありません。使用できない文字が含まれています",
    123: "ファイル名、ディレクトリ名、またはボリュームラベルの構文が正しくありません",
    145: "ディレクトリが空ではありません",
    183: "この名前のファイルまたはディレクトリが既に存在しています",
    206: "ファイルパスが長すぎます。260文字以内に収まるパスを使用してください",
    1920: "メディアが書き込み保護されています",
}


# ログ設定
def setup_logging(
    console_level="INFO", file_level="DEBUG", log_file="process_{time}.log"
):
    """ロギングの設定を行います"""
    logger.remove()  # デフォルト設定を削除
    logger.add(
        sys.stderr,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{function}</cyan>: <white>{message}</white>",
        colorize=True,
        level=console_level,
    )
    logger.add(
        log_file,
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {function}: {message}",
        rotation="1 day",
        level=file_level,
    )


def get_directory_size(path):
    """ディレクトリの合計サイズを取得します"""
    total_size = 0
    dir_path = Path(path)

    if not dir_path.exists():
        return 0

    for file_path in dir_path.glob("**/*"):
        if file_path.is_file():
            try:
                total_size += file_path.stat().st_size
            except OSError:
                # ファイルアクセスエラーの場合はスキップ
                pass

    return total_size


def calculate_reduction_rate(source_dir, dest_dir):
    """削減率を計算します（%）"""
    source_size = get_directory_size(source_dir)
    dest_size = get_directory_size(dest_dir)

    if source_size == 0:
        return 0

    return (source_size - dest_size) / source_size * 100


def check_disk_space(path, required_space_mb=500):
    """ディスクの空き容量を確認します"""
    try:
        total, used, free = shutil.disk_usage(path)
        free_mb = free / (1024 * 1024)  # MB単位

        if free_mb < required_space_mb:
            logger.warning(f"ディスク空き容量が少なくなっています: {free_mb:.2f}MB")
            return False
        return True
    except Exception as e:
        logger.error(f"ディスク容量確認エラー: {e}")
        return False


def get_windows_error_message(error_code):
    """
    Windowsエラーコードから日本語メッセージを取得します

    Args:
        error_code: Windowsエラーコード

    Returns:
        str: 日本語エラーメッセージ
    """
    return WINDOWS_ERROR_MESSAGES.get(error_code, "不明なエラー")


def get_japanese_error_message(error):
    """
    例外から日本語のエラーメッセージを生成します

    Args:
        error: 例外オブジェクト

    Returns:
        str: 日本語エラーメッセージ
    """
    error_type = type(error).__name__
    error_msg = str(error)
    
    # ファイル関連エラー
    if isinstance(error, FileNotFoundError):
        return f"ファイルが見つかりません: {error_msg}"
    elif isinstance(error, PermissionError):
        return f"アクセス権限がありません: {error_msg}"
    elif isinstance(error, IsADirectoryError):
        return f"ディレクトリが指定されました（ファイルを指定してください）: {error_msg}"
    elif isinstance(error, NotADirectoryError):
        return f"ディレクトリではありません: {error_msg}"
    
    # 画像関連エラー
    elif isinstance(error, UnidentifiedImageError):
        return f"画像ファイルとして認識できません: {error_msg}"
    elif error_type == "DecompressionBombError":
        return f"画像が大きすぎます（圧縮爆弾の可能性）: {error_msg}"
    
    # OS関連エラー
    elif isinstance(error, OSError):
        if hasattr(error, 'winerror') and error.winerror:
            return get_windows_error_message(error.winerror)
        elif error.errno == 28:  # ENOSPC
            return "ディスク容量が不足しています"
        elif error.errno == 36:  # ENAMETOOLONG
            return "ファイル名が長すぎます"
        else:
            return f"システムエラー: {error_msg}"
    
    # メモリ関連エラー
    elif isinstance(error, MemoryError):
        return "メモリ不足エラー: 画像が大きすぎるか、使用可能なメモリが不足しています"
    
    # 値関連エラー
    elif isinstance(error, ValueError):
        return f"無効な値: {error_msg}"
    elif isinstance(error, TypeError):
        return f"型エラー: {error_msg}"
    
    # その他
    else:
        return f"{error_type}: {error_msg}"


def retry_on_file_error(func, *args, max_retries=3, retry_delay=0.5, **kwargs):
    """
    ファイル操作に関連する関数を実行し、エラー時にリトライするラッパー関数

    Args:
        func: 実行する関数
        *args: 関数の引数
        max_retries: 最大リトライ回数
        retry_delay: リトライ間の待機時間（秒）
        **kwargs: 関数のキーワード引数

    Returns:
        関数の結果

    Raises:
        最大リトライ回数後も失敗した場合は最後の例外を再送出
    """
    retries = 0
    last_exception = None

    while retries < max_retries:
        try:
            return func(*args, **kwargs)
        except (PermissionError, OSError) as e:
            last_exception = e
            retries += 1
            logger.debug(f"ファイル操作エラー: {e} - リトライ {retries}/{max_retries}")

            # Windows環境ではファイルロックが一時的な場合があるため、待機して再試行
            time.sleep(retry_delay)

    # 最大リトライ回数到達後も失敗した場合
    if last_exception:
        logger.error(f"最大リトライ回数到達: {last_exception}")
        raise last_exception
    return None


def is_long_path_enabled():
    """
    Windows環境で長いパスサポートが有効か確認します

    Returns:
        bool: 長いパスサポートが有効かどうか
    """
    if os.name != "nt":
        return True  # Windows以外では常にTrueとする

    try:
        # 長いパスが有効かテスト
        test_long_path = "a" * 260
        Path(test_long_path)
        return True
    except OSError:
        # ファイル名の制限に達した場合
        return False
    except Exception:
        # その他のエラー
        return False


def normalize_long_path(path, add_prefix=True, remove_prefix=False, normalize=True):
    """
    Windowsの長いパスを処理するためのパス正規化処理。
    Windowsの260文字制限を回避し、絵文字などのUnicode文字を含むパスも処理します。

    Args:
        path: パスオブジェクトまたはパス文字列
        add_prefix: \\?\\u30d7レフィックスを追加するか（Windowsのみ有効）
        remove_prefix: 既存の\\?\\u30d7レフィックスを削除するか（Windowsのみ有効）
        normalize: パスを正規化するか（二重スラッシュなどの正規化）

    Returns:
        str: 正規化されたパス（Windowsでは必要に応じて\\?\\u5f62式）
    """
    try:
        # パスを文字列に変換
        path_str = str(path)
        original_path = path_str  # ログ記録用に元のパスを保存

        # Windowsでなければそのまま返す
        if os.name != "nt":
            return path_str

        # UNCパス（ネットワークパス）の处理
        is_unc = path_str.startswith("\\\\")

        # 既存のプレフィックスを確認
        has_prefix = path_str.startswith("\\\\?\\")
        has_unc_prefix = path_str.startswith("\\\\?\\UNC\\")

        # プレフィックスを削除する必要がある場合
        if remove_prefix:
            if has_unc_prefix:
                # UNCパスのプレフィックスを削除
                path_str = (
                    "\\\\" + path_str[8:]
                )  # '\\?\UNC\\'(8文字)を削除して'\\\\'(2文字)を追加
                logger.debug(
                    f"UNCパスのプレフィックスを削除: '{original_path}' -> '{path_str}'"
                )
            elif has_prefix:
                # 通常のプレフィックスを削除
                path_str = path_str[4:]  # '\\?\\'(4文字)を削除
                logger.debug(f"プレフィックスを削除: '{original_path}' -> '{path_str}'")

        # パスを正規化する必要がある場合
        if normalize:
            # プレフィックスの有無に応じて正規化
            if has_prefix and not remove_prefix:
                # 一時的にプレフィックスを削除して正規化
                temp_path = path_str[4:] if has_prefix else path_str
                normalized_path = os.path.abspath(temp_path)
                # プレフィックスを復元
                path_str = "\\\\?\\" + normalized_path
                logger.debug(
                    f"プレフィックス付きパスを正規化: '{original_path}' -> '{path_str}'"
                )
            else:
                # 正規化のみ実行
                path_str = os.path.abspath(path_str)
                logger.debug(f"パスを正規化: '{original_path}' -> '{path_str}'")

        # プレフィックスを追加する必要がある場合
        if add_prefix and not has_prefix and not path_str.startswith("\\\\?\\"):
            # パスが無効な場合は正規化
            norm_path = path_str if normalize else os.path.abspath(path_str)

            if is_unc:
                # UNCパスの場合は特別な処理が必要
                # \\で始まるパスは\\を削除してUNCプレフィックスを追加
                path_str = "\\\\?\\UNC\\" + norm_path[2:]
                logger.debug(
                    f"UNCパスにプレフィックスを追加: '{original_path}' -> '{path_str}'"
                )
            else:
                # 通常のパスにプレフィックスを追加
                path_str = "\\\\?\\" + norm_path
                logger.debug(
                    f"パスにプレフィックスを追加: '{original_path}' -> '{path_str}'"
                )

        # パス长のチェック
        if len(path_str) > 260 and not (has_prefix or path_str.startswith("\\\\?\\")):
            logger.warning(
                f"パスが260文字を超えていますが、\\?\\プレフィックスが付いていません: {path_str}"
            )
            # プレフィックスが付いていない場合は自動的に追加
            if is_unc:
                path_str = "\\\\?\\UNC\\" + path_str[2:]
            else:
                path_str = "\\\\?\\" + path_str

        return path_str

    except Exception as e:
        # パスの正規化中に問題が発生した場合はログに記録し、元のパスを返す
        import traceback

        error_trace = traceback.format_exc()
        logger.error(f"パスの正規化中にエラーが発生しました: {e}")
        logger.debug(f"トレースバック情報: \n{error_trace}")
        logger.warning(f"元のパスを返します: {str(path)}")
        return str(path)  # 元のパスを返す


def get_japanese_error_message(error):
    """
    エラーから日本語のエラーメッセージを取得します

    Args:
        error: Exception オブジェクト

    Returns:
        str: 日本語のエラーメッセージ
    """
    if isinstance(error, OSError):
        return analyze_os_error(error)
    elif isinstance(error, ValueError):
        return f"値エラー: {str(error)}"
    elif isinstance(error, FileNotFoundError):
        return f"ファイルが見つかりません: {str(error)}"
    elif isinstance(error, PermissionError):
        return f"権限エラー: {str(error)}"
    elif isinstance(error, UnidentifiedImageError):
        return "未対応または破損した画像形式です"
    else:
        return f"エラー: {str(error)}"


def analyze_os_error(e):
    """
    OSエラーを詳細に分析し、具体的な情報を返します

    Args:
        e: OSError例外オブジェクト

    Returns:
        str: 詳細なエラー情報
    """
    error_msg = str(e)

    # WindowsのOSエラーで、winerrnoがある場合
    if os.name == "nt" and hasattr(e, "winerror"):
        win_code = e.winerror
        win_msg = get_windows_error_message(win_code)

        if win_code == 206:  # Path too long
            return f"{error_msg}。パスが長すぎます。長いパス有効化の設定を確認するか、短いパスを使用してください。"
        elif win_code == 80:  # Invalid filename
            return f"{error_msg}。ファイル名に使用できない文字が含まれています。"
        elif win_code == 5:  # Access denied
            return f"{error_msg}。アクセスが拒否されました。管理者権限で実行するか、ファイルの権限を確認してください。"
        else:
            return f"{error_msg}。{win_msg}"

    # 一般的なファイル/ディレクトリエラー
    if "No such file or directory" in error_msg:
        return f"{error_msg}。指定されたパスが存在しません。"
    elif "Permission denied" in error_msg:
        return f"{error_msg}。ファイルへのアクセス権限がありません。"
    elif "File exists" in error_msg:
        return f"{error_msg}。ファイルが既に存在します。"
    else:
        return error_msg


def create_directory_with_permissions(directory_path):
    """
    ディレクトリを安全に作成し、権限エラーの場合は回避策を試みます

    Args:
        directory_path: 作成するディレクトリパス（Path オブジェクトまたは文字列）

    Returns:
        tuple: (成功したかどうか, 作成されたディレクトリパス)
    """
    try:
        # Pathオブジェクトに変換
        directory = Path(directory_path)

        # 既に存在する場合は成功とみなす
        if directory.exists():
            return True, directory

        # Windows環境で長いパス対応
        if os.name == "nt":
            # normalize_long_pathは文字列を返すので、文字列として明示的に扱う
            directory_str = normalize_long_path(directory)
            os.makedirs(directory_str, exist_ok=True)
            # 成功した場合、directory変数を更新して返却値に反映させる
            directory = Path(directory_str)
        else:
            # 通常の処理
            directory.mkdir(parents=True, exist_ok=True)

        logger.debug(f"ディレクトリを作成しました: {directory}")
        return True, directory

    except PermissionError:
        # 権限エラーの場合、ユーザーホームディレクトリに作成を試みる
        logger.warning(f"権限エラー: {directory_path} を作成できません")
        try:
            home_dir = Path.home() / "resize_images_output"
            home_dir.mkdir(parents=True, exist_ok=True)
            logger.info(f"代替ディレクトリを作成しました: {home_dir}")
            return True, home_dir
        except Exception as e:
            logger.error(f"代替ディレクトリの作成にも失敗しました: {e}")
            return False, None

    except OSError as e:
        # その他のOSエラー
        error_msg = analyze_os_error(e)
        logger.error(f"ディレクトリ作成エラー: {error_msg}")
        return False, None

    except Exception as e:
        # その他の予期せぬエラー
        logger.error(f"ディレクトリ作成中の予期せぬエラー: {e}")
        return False, None


def sanitize_filename(filename):
    """
    ファイル名をWindows互換に変換します。絵文字などの特殊文字も処理します。

    Args:
        filename: 元のファイル名

    Returns:
        str: 安全なファイル名
    """
    try:
        # emojiパッケージのインポート（必要な場合のみ実行）
        try:
            import emoji

            has_emoji_lib = True
        except ImportError:
            has_emoji_lib = False
            logger.warning(
                "emojiパッケージがインストールされていません。通常の絵文字処理を使用します。"
            )

        # 文字列に変換
        safe_name = str(filename)
        original_name = safe_name

        # 絵文字を処理する
        if has_emoji_lib:
            # emojiパッケージを使用して絵文字をテキスト表現に変換
            try:
                # 絵文字が含まれているかチェック
                if emoji.emoji_count(safe_name) > 0:
                    # 絵文字をテキスト表現に変換 (:smile: などに変換)
                    demojized = emoji.demojize(safe_name)

                    # コロンをアンダースコアに変換し、ファイル名に適した形式にする
                    import re

                    safe_name = re.sub(r":(\w+):", r"_\1_", demojized)
                    logger.debug(f"絵文字を変換: '{original_name}' -> '{safe_name}'")
            except Exception as emoji_err:
                logger.warning(f"絵文字処理中にエラーが発生しました: {emoji_err}")

        # Windows禁止文字をアンダースコアに置換
        unsafe_chars = '<>:"/\\|?*\0'
        for char in unsafe_chars:
            safe_name = safe_name.replace(char, "_")

        # コントロール文字をアンダースコアに置換
        safe_name = "".join(c if ord(c) >= 32 else "_" for c in safe_name)

        # 絵文字パッケージが使えない場合のバックアップ処理
        if not has_emoji_lib and emoji.emoji_count(original_name) > 0:
            # unicodedataを使用した代替絵文字処理
            import unicodedata
            import re

            # ASCII文字と一部の一般的な非ASCII文字を許可
            # 日本語は正規表現でマッチしないようにし、そのまま残す
            ascii_and_safe = re.compile(
                r"[a-zA-Z0-9\-_. \[\]()\u3040-\u30ff\u3400-\u4dbf\u4e00-\u9fff\uf900-\ufaff]+"
            )

            def replace_unsafe_char(c):
                # 日本語など一般的な文字はそのまま使用
                if ascii_and_safe.fullmatch(c):
                    return c
                # 絵文字やアクセント記号などは名前に変換
                try:
                    emoji_name = unicodedata.name(c).lower()
                    # 絵文字などは短い説明的な名前に変換
                    if "emoji" in emoji_name:
                        return f"_{emoji_name.split()[-1][:8]}_"
                    # その他の特殊文字は単純なアンダースコアに
                    return "_"
                except Exception:
                    return "_"

            # 安全でないUnicode文字を処理
            safe_name = "".join(replace_unsafe_char(c) for c in safe_name)

        # Windowsの予約語をチェック
        reserved_names = [
            "CON",
            "PRN",
            "AUX",
            "NUL",
            "COM1",
            "COM2",
            "COM3",
            "COM4",
            "COM5",
            "COM6",
            "COM7",
            "COM8",
            "COM9",
            "LPT1",
            "LPT2",
            "LPT3",
            "LPT4",
            "LPT5",
            "LPT6",
            "LPT7",
            "LPT8",
            "LPT9",
        ]

        # ファイル名と拡張子を分ける
        name_parts = os.path.splitext(safe_name)
        base_name = name_parts[0]
        extension = name_parts[1] if len(name_parts) > 1 else ""

        # 予約語対策
        if base_name.upper() in reserved_names:
            base_name = base_name + "_file"

        # 先頭や末尾のスペースとピリオドを削除
        base_name = base_name.strip(" .")

        # 空の場合はデフォルト名
        if not base_name:
            base_name = "unnamed_file"

        # ダブルアンダースコアをシングルに置換して可読性を高める
        import re

        base_name = re.sub(r"_+", "_", base_name)

        # ファイル名が長すぎる場合は切り詰め
        if len(base_name) > 200:  # Windowsの制限より少なく
            base_name = base_name[:197] + "..."

        # 拡張子も簡素化
        if len(extension) > 10:  # 正常な拡張子はそれより短い
            extension = extension[:10]

        # ファイル名を元に戻す
        safe_name = base_name + extension

        logger.debug(f"ファイル名を正規化: '{filename}' -> '{safe_name}'")
        return safe_name

    except Exception as e:
        # 例外発生時はログに記録し、デフォルト名を使用
        logger.error(f"ファイル名の正規化中にエラーが発生しました: {e}")
        import uuid

        return f"unnamed_file_{uuid.uuid4().hex[:8]}"


def get_system_encoding():
    """システムに適したエンコーディングを返します"""
    return "cp932" if os.name == "nt" else "utf-8"


def get_destination_path(source_path, source_dir, dest_dir):
    """
    元のパスから新しい出力先パスを生成します（Windows対応強化版）

    Args:
        source_path: 元のファイルパス (Path)
        source_dir: 入力ディレクトリ (Path)
        dest_dir: 出力ディレクトリ (Path)

    Returns:
        Path: 出力先のパス
    """
    # 出力先のパスを保持する変数を初期化
    # どのケースでもデフォルト値を持つようにする
    result_path = None

    # dest_dirを安全に取得
    dest_dir_str = ""
    if dest_dir is not None:
        try:
            dest_dir_str = str(dest_dir)
            # 万が一で空文字列ならデフォルト値を使用
            if not dest_dir_str:
                dest_dir_str = "./output"
        except Exception:
            dest_dir_str = "./output"
    else:
        dest_dir_str = "./output"

    # source_pathを安全に取得
    source_path_str = ""
    filename = "output_file.jpg"  # デフォルトファイル名
    if source_path is not None:
        try:
            source_path_str = str(source_path)
            filename = os.path.basename(source_path_str)
        except Exception:
            pass

    # source_dirを安全に取得
    source_dir_str = ""
    if source_dir is not None:
        try:
            source_dir_str = str(source_dir)
        except Exception:
            pass

    # メイン処理ブロック
    try:
        # Windowsの長いパス処理
        is_long_path = False
        if os.name == "nt" and source_path_str.startswith("\\\\?\\"):
            is_long_path = True
            source_path_str = source_path_str[4:]
            source_dir_str = (
                source_dir_str[4:]
                if source_dir_str.startswith("\\\\?\\")
                else source_dir_str
            )

        # 相対パスの計算
        rel_path_str = ""
        if source_path_str and source_dir_str:
            if not source_path_str.startswith(source_dir_str):
                # 絶対パスで試行
                try:
                    abs_source = os.path.abspath(source_path_str)
                    abs_source_dir = os.path.abspath(source_dir_str)

                    if abs_source.startswith(abs_source_dir):
                        rel_path_str = abs_source[len(abs_source_dir) :].lstrip(os.sep)
                except Exception:
                    # 失敗した場合は相対パスなし
                    rel_path_str = ""
            else:
                # 直接相対パス計算
                rel_path_str = source_path_str[len(source_dir_str) :].lstrip(os.sep)

        # 相対パスが存在する場合
        if rel_path_str:
            # パス部分の分割
            path_parts = rel_path_str.split(os.sep)

            # 出力先パスの構築
            result_path = Path(dest_dir_str)

            # ディレクトリ部分の処理
            if len(path_parts) > 1:
                for part in path_parts[:-1]:
                    try:
                        part_safe = sanitize_filename(part)
                        result_path = result_path / part_safe
                    except Exception:
                        # 失敗した場合はスキップして次のディレクトリ部分へ
                        continue

                # ディレクトリ作成
                try:
                    create_directory_with_permissions(result_path)
                except Exception as dir_err:
                    logger.debug(f"ディレクトリ作成エラーは無視します: {dir_err}")

            # ファイル名部分の処理
            if path_parts:
                try:
                    filename = sanitize_filename(path_parts[-1])
                    result_path = result_path / filename
                except Exception:
                    # ファイル名部分の処理に失敗した場合は元のファイル名を使用
                    result_path = result_path / filename
        else:
            # 相対パスが存在しない場合、ファイル名のみ使用
            try:
                safe_name = sanitize_filename(filename)
                result_path = Path(dest_dir_str) / safe_name
            except Exception:
                # 安全なファイル名の生成に失敗した場合はデフォルト名を使用
                result_path = Path(dest_dir_str) / "output_file.jpg"

        # Windowsの長いパス処理
        if os.name == "nt" and is_long_path and result_path:
            try:
                dest_path_str = normalize_long_path(str(result_path))
                result_path = Path(dest_path_str)
            except Exception:
                # 長いパスの正規化に失敗した場合は元のパスを使用
                pass

    except Exception as e:
        # メイン処理でエラーが発生した場合
        logger.error(f"出力先パス生成エラー: {e}")

    # 最終的なチェックと結果返却
    if result_path is None:
        # メイン処理に失敗した場合の最終手段
        try:
            # 安全なファイル名を生成
            safe_name = sanitize_filename(filename)
            result_path = Path(dest_dir_str) / safe_name
        except Exception:
            # 本当に最後の手段として、デフォルトから生成
            result_path = Path("./output/output_file.jpg")

    # 結果返却
    return result_path


def find_image_files(source_dir) -> list[Path]:
    """
    指定されたディレクトリから全ての.jpgと.pngファイルを検索します

    Args:
        source_dir: 検索対象のディレクトリパス（str または Path オブジェクト）

    Returns:
        list[Path]: 画像ファイルパスのリスト（Path）

    Raises:
        ValueError: source_dir が None、空文字列、または無効な形式の場合
        FileNotFoundError: 指定されたディレクトリが存在しない場合
        NotADirectoryError: 指定されたパスがディレクトリでない場合
        PermissionError: 権限不足でアクセスできない場合
    """
    # 入力バリデーション
    if source_dir is None:
        error_msg = "ディレクトリパスがNoneです"
        logger.error(error_msg)
        raise ValueError(error_msg)

    if isinstance(source_dir, str) and not source_dir.strip():
        error_msg = "ディレクトリパスが空です"
        logger.error(error_msg)
        raise ValueError(error_msg)

    # Pathオブジェクトに変換
    try:
        source_path = Path(source_dir)
    except TypeError as e:
        error_msg = f"無効なディレクトリパス形式です: {e}"
        logger.error(error_msg)
        raise ValueError(error_msg) from e

    # 存在確認
    if not source_path.exists():
        error_msg = f"指定されたディレクトリが存在しません: {source_dir}"
        logger.error(error_msg)
        raise FileNotFoundError(error_msg)

    # ディレクトリであることを確認
    if not source_path.is_dir():
        error_msg = f"指定されたパスはディレクトリではありません: {source_dir}"
        logger.error(error_msg)
        raise NotADirectoryError(error_msg)

    # 読み取り権限があることを確認
    try:
        os.access(source_path, os.R_OK)
    except Exception as e:
        error_msg = f"ディレクトリの読み取り権限を確認できません: {e}"
        logger.error(error_msg)
        # 権限チェックでエラーがあれば後続の処理で捕捉する
        pass

    image_files = []
    extensions = [".jpg", ".jpeg", ".png"]

    try:
        # Windows環境の場合は長いパス対応
        if os.name == "nt":
            try:
                # normalize_long_path は文字列を返すので、再度 Path オブジェクトに変換する
                norm_path_str = normalize_long_path(source_path)
                norm_path = Path(norm_path_str)
            except Exception as e:
                logger.warning(
                    f"パス正規化中にエラーが発生しました（通常パスを使用します）: {e}"
                )
                norm_path = source_path
        else:
            norm_path = source_path

        # 一度に複数の拡張子をチェック
        for ext in extensions:
            try:
                # rglob を使用して再帰的に検索 (glob の代わりにより堅牢なパターン)
                pattern = f"*{ext}"
                found_files = list(norm_path.rglob(pattern))
                logger.debug(
                    f"{ext} 拡張子のファイルを {len(found_files)} 個見つけました"
                )
                image_files.extend(found_files)
            except PermissionError as e:
                # 権限エラーの場合（一部のサブディレクトリにはアクセスできない可能性がある）
                logger.warning(
                    f"一部のディレクトリにアクセスできませんでした（権限エラー）: {e}"
                )
                continue
            except OSError as e:
                # ファイルシステム関連のエラー
                logger.warning(f"ファイルシステムエラー（パターン '{pattern}'）: {e}")
                continue
            except Exception as e:
                # その他の予期せぬエラー
                logger.warning(
                    f"画像検索中にエラーが発生しました（パターン '{pattern}'）: {e}"
                )
                continue

        # 重複の削除（念のため）と並べ替え
        unique_files = list(set(image_files))
        sorted_files = sorted(unique_files)

        total_found = len(sorted_files)
        if total_found > 0:
            logger.info(f"{total_found}個の画像ファイルが見つかりました")
        else:
            logger.warning(f"画像ファイルが見つかりませんでした: {source_dir}")

        return sorted_files
    except PermissionError as e:
        error_msg = f"ディレクトリにアクセスする権限がありません: {e}"
        logger.error(error_msg)
        raise PermissionError(error_msg) from e
    except Exception as e:
        error_msg = f"画像ファイル検索中に予期せぬエラーが発生しました: {e}"
        logger.error(error_msg)
        # 重大なエラーはログを出して、呼び出し元に例外を伝播させる
        raise RuntimeError(error_msg) from e


def resize_and_compress_image(
    source_path: Optional[Union[str, Path]] = None,
    dest_path: Optional[Union[str, Path]] = None,
    target_width: Optional[int] = None,
    quality: Optional[int] = None,
    format: str = "original",
    exif_handling: str = "keep",
    balance: int = 5,
    webp_lossless: bool = False,
    dry_run: bool = False,
    # メモリベース処理用の新しいパラメータ
    source_image=None,
    output_buffer=None,
    resize_mode: str = "width",
    resize_value: Optional[int] = None,
    lanczos_filter: bool = True,
    progressive: bool = False,
    optimize: bool = False,
    output_format: Optional[str] = None,
) -> Union[Tuple[bool, bool, Optional[int]], Tuple[bool, Optional[str]]]:
    """
    画像をリサイズして圧縮します（ファイルベースとメモリベースの両方をサポート）

    Args:
        source_path: 元の画像ファイルパス (str または Path)
        dest_path: 出力先ファイルパス (str または Path)
        target_width: 目標の幅 (ピクセル、1以上の整数)
        quality: 圧縮品質 (1-100の整数)
        format: 出力形式 ('original', 'jpeg', 'png', 'webp')
        exif_handling: EXIFメタデータの取り扱い ('keep': 維持, 'remove': 削除)
        balance: 圧縮と品質のバランス (1-10, 1=最高圧縮率, 10=最高品質)
        webp_lossless: WebPをロスレスで保存するかどうか
        dry_run: 実際の処理を行わずサイズ見積もりのみ実施
        
        # メモリベース処理用の新しいパラメータ
        source_image: PIL.Imageオブジェクト（メモリベース処理用）
        output_buffer: io.BytesIOオブジェクト（メモリベース処理用）
        resize_mode: リサイズモード ('width', 'height', 'longest_side', 'percentage', 'none')
        resize_value: リサイズ値（resize_modeに応じたピクセル数またはパーセンテージ）
        lanczos_filter: Lanczosフィルタを使用するか
        progressive: プログレッシブJPEGを使用するか
        optimize: PNG/JPEG最適化を使用するか
        output_format: 出力フォーマット（formatパラメータより優先）

    Returns:
        tuple[bool, bool, int | None]: (成功したか, 元のサイズを維持したか, 見積もりサイズ)
        メモリベース処理の場合は、(成功したか, エラーメッセージ or None) を返す

    Raises:
        ValueError: パラメータが無効な場合
        FileNotFoundError: ソースファイルが存在しない場合
        PermissionError: ファイルアクセス権限がない場合
        OSError: ファイルシステム関連のエラー
        PIL.UnidentifiedImageError: サポートされていない画像形式または破損している場合
    """
    
    # メモリベース処理の場合
    if source_image is not None and output_buffer is not None:
        # resize_valueが設定されていない場合はtarget_widthを使用
        if resize_value is None and target_width is not None:
            resize_value = target_width
        
        # output_formatが設定されていない場合はformatを使用
        if output_format is None:
            output_format = format if format != "original" else "jpeg"
        
        # メモリベース処理を実行
        success, error_msg = resize_and_compress_image_memory(
            source_image=source_image,
            output_buffer=output_buffer,
            resize_mode=resize_mode,
            resize_value=resize_value,
            quality=quality or 85,
            output_format=output_format,
            exif_handling=exif_handling,
            lanczos_filter=lanczos_filter,
            progressive=progressive,
            optimize=optimize,
            webp_lossless=webp_lossless,
        )
        
        # メモリベース処理の戻り値を調整
        return (success, error_msg)
    
    # ファイルベース処理の場合
    # resize_modeとresize_valueからtarget_widthを設定
    if resize_mode == "none":
        # リサイズなしの場合、target_widthは不要（ダミー値を設定してバリデーションを通す）
        target_width = 1  # ダミー値（実際には使用されない）
    elif resize_value is not None:
        target_width = resize_value
    elif target_width is None:
        # 古い呼び出し方式との互換性のため、デフォルト値を設定
        target_width = 800
    
    # パラメータバリデーション（resize_mode="none"の場合はスキップ）
    if resize_mode != "none" and (target_width is None or target_width <= 0):
        error_msg = f"無効な目標幅です: {target_width}. 1以上の正の整数が必要です"
        logger.error(error_msg)
        raise ValueError(error_msg)

    if quality is None or not (1 <= quality <= 100):
        error_msg = f"無効な品質値です: {quality}. 1から100の間の整数が必要です"
        logger.error(error_msg)
        raise ValueError(error_msg)

    if balance is None or not (1 <= balance <= 10):
        error_msg = f"無効なバランス値です: {balance}. 1から10の間の整数が必要です"
        logger.error(error_msg)
        raise ValueError(error_msg)

    if format not in ["original", "jpeg", "jpg", "png", "webp"]:
        logger.warning(
            f"推奨されない出力形式: {format}. 'original', 'jpeg', 'jpg', 'png', 'webp' のいずれかを使用することをお勧めします"
        )

    if exif_handling not in ["keep", "remove"]:
        logger.warning(
            f"推奨されないEXIF取り扱い: {exif_handling}. 'keep' または 'remove' のいずれかを使用することをお勧めします"
        )

    # 変数の初期化 - スコープ問題防止のため先に定義
    source_path_str = ""
    dest_path_str = ""
    keep_original_size = False
    estimated_size = None
    resized_img = None
    img = None
    save_img = None

    try:
        # Path オブジェクトに変換
        try:
            source_path = (
                Path(source_path) if not isinstance(source_path, Path) else source_path
            )
            dest_path = (
                Path(dest_path) if not isinstance(dest_path, Path) else dest_path
            )
        except TypeError as e:
            error_msg = f"パスの変換に失敗しました: {e}"
            logger.error(error_msg)
            raise ValueError(error_msg) from e

        # パスの正規化にリトライ機構を使用
        def normalize_path_with_retry(path):
            return normalize_long_path(path, remove_prefix=True)

        source_path_str = retry_on_file_error(
            normalize_path_with_retry, source_path, max_retries=3, retry_delay=0.2
        )
        source_path = Path(source_path_str)

        # 実際に存在するか確認し、存在しない場合は再試行
        def check_file_exists(path):
            if not Path(path).exists():
                raise FileNotFoundError(f"ファイルが存在しません: {path}")
            return True

        retry_on_file_error(
            check_file_exists, source_path_str, max_retries=3, retry_delay=0.3
        )

        # 出力先ディレクトリの安全な取得 (dest_path引数を使用)
        dest_dir = Path(dest_path).parent
        success, created_dir = create_directory_with_permissions(dest_dir)
        if not success:
            error_msg = f"出力先ディレクトリを作成できませんでした: {dest_dir}"
            logger.error(error_msg)
            raise PermissionError(error_msg)

        # 出力先パスを文字列に変換
        dest_path_str = str(dest_path)

        # 画像ファイルの有効性を確認
        try:
            # ファイルの存在とアクセス権限を確認
            if not os.path.isfile(source_path_str):
                logger.error(f"ファイルが存在しません: {source_path_str}")
                return False, False, None

            if not os.access(source_path_str, os.R_OK):
                logger.error(f"ファイルに読み取り権限がありません: {source_path_str}")
                return False, False, None

            # 画像ファイルを開いてフォーマットを確認
            with Image.open(source_path_str) as img:
                # 画像フォーマットの確認
                img_format = img.format
                SUPPORTED_FORMATS = {"JPEG", "PNG", "WEBP"}
                if img_format not in SUPPORTED_FORMATS and img_format != "MPO":
                    logger.warning(
                        f"サポートされていない入力画像フォーマット: {img_format}。処理を試みますが、予期せぬ結果になる可能性があります。 - {source_path.name}"
                    )
                    # 続行するが警告を記録
                # 元の画像サイズ
                original_width, original_height = img.size

                # --- 実際の出力形式を決定 ---
                actual_output_format = ""
                is_mpo_input = img_format == "MPO"  # MPO形式かどうかのフラグを追加
                if format == "original":
                    # 元の形式を維持する場合
                    if is_mpo_input:
                        # MPOは維持できないのでJPEGとして扱い、警告を出す
                        logger.warning(
                            f"入力形式がMPOのため、元の形式を維持できません。JPEGとして処理します。 - {source_path.name}"
                        )
                        actual_output_format = "JPEG"
                    elif img_format and img_format.upper() in SUPPORTED_FORMATS:
                        actual_output_format = img_format.upper()
                    else:
                        # サポート外または不明な形式はJPEGにフォールバック
                        if img_format:
                            logger.warning(
                                f"入力形式 '{img_format}' は維持できません。JPEGに変換します。 - {source_path.name}"
                            )
                        else:
                            logger.warning(
                                f"入力形式が不明です。JPEGとして処理します。 - {source_path.name}"
                            )
                        actual_output_format = "JPEG"
                elif format.upper() in SUPPORTED_FORMATS:
                    # 特定の形式が指定された場合 (WEBP含む)
                    actual_output_format = format.upper()
                elif format.upper() == "JPG":
                    # JPGはJPEGとして扱う
                    actual_output_format = "JPEG"
                else:
                    # 指定された形式がサポート外の場合、JPEGにフォールバック
                    logger.warning(
                        f"指定された出力形式 '{format}' はサポートされていません。JPEGとして処理します。"
                    )
                    actual_output_format = "JPEG"

                logger.info(f"決定された出力形式: {actual_output_format}")
                # --- 出力形式決定ここまで ---

                # リサイズ判定とリサイズ処理
                if resize_mode == "none":
                    # リサイズしない場合
                    keep_original_size = True
                    resized_img = img
                else:
                    # リサイズする場合（従来通り）
                    keep_original_size = original_width <= target_width
                    
                    # 縦横比を維持したリサイズ計算
                    if not keep_original_size:
                        ratio = original_height / original_width
                        new_height = int(target_width * ratio)
                        new_size = (target_width, new_height)
                        resized_img = img.resize(new_size, Image.LANCZOS)
                    else:
                        resized_img = img

                # 見積もりサイズ計算（テンポラリファイルに保存して測定）
                estimated_size = None

                # ドライランまたはサイズ計算が必要な場合
                if dry_run or not keep_original_size:
                    # テンポラリパスを用意
                    import tempfile
                    import uuid

                    # Windows環境での権限問題に対応するため、一意なファイル名を使用
                    temp_dir = tempfile.gettempdir()
                    temp_filename = f"resize_temp_{uuid.uuid4().hex}.jpg"
                    temp_path = os.path.join(temp_dir, temp_filename)

                    # リトライ機構を使って一時ファイル操作
                    def save_temp_image():
                        # RGBモードに変換してから保存
                        img_to_save = resized_img.convert("RGB")
                        img_to_save.save(temp_path, format="JPEG", quality=quality)
                        return os.path.getsize(temp_path)

                    try:
                        # リトライ機構で一時ファイルを保存してサイズを計測
                        estimated_size = retry_on_file_error(
                            save_temp_image, max_retries=3, retry_delay=0.5
                        )
                    except Exception as e:
                        logger.error(f"サイズ見積もりエラー: {e}")
                    finally:
                        # 一時ファイルの削除を試みる
                        try:
                            if os.path.exists(temp_path):
                                os.remove(temp_path)
                        except Exception as e:
                            logger.debug(f"一時ファイルの削除に失敗: {e}")

                # 保存する画像を選択（ドライランでも必要）
                if not keep_original_size:
                    save_img = resized_img
                else:
                    # リサイズ不要でも、形式変換が必要な場合があるので img を使う
                    save_img = img

                # ドライランの場合は実際の保存は行わない
                if dry_run:
                    # ドライランの場合はサイズ見積もりを返すのみ
                    return True, keep_original_size, estimated_size

                # 以下は実際の保存処理
                # ディレクトリが存在するか確認
                if not os.path.exists(os.path.dirname(dest_path_str)):
                    os.makedirs(os.path.dirname(dest_path_str), exist_ok=True)

                # バランス値に基づいて最適化パラメータを調整 (JPEG/WebPの品質に使用)
                optimized_quality = adjust_quality_by_balance(
                    quality, balance, actual_output_format.lower()
                )

                # 出力形式に応じた保存処理
                save_options = {}
                output_ext = ""
                final_dest_path_str = str(dest_path)  # 元のdest_pathをベースにする
                final_dest_path = dest_path  # Path オブジェクトも初期化

                if actual_output_format == "JPEG":
                    output_ext = ".jpg"
                    final_dest_path_str = update_extension(
                        final_dest_path_str, output_ext
                    )
                    save_options = {
                        "format": "JPEG",
                        "quality": optimized_quality,
                        "optimize": True,
                        "progressive": True,
                    }
                    # EXIF情報を保持する場合
                    if (
                        exif_handling == "keep"
                        and hasattr(img, "info")
                        and "exif" in img.info
                    ):
                        save_options["exif"] = img.info["exif"]

                    # JPEGはRGBモードである必要がある
                    if save_img.mode != "RGB":
                        logger.debug(f"画像をRGBモードに変換中 (元: {save_img.mode})")
                        save_img = save_img.convert("RGB")

                elif actual_output_format == "PNG":
                    output_ext = ".png"
                    final_dest_path_str = update_extension(
                        final_dest_path_str, output_ext
                    )
                    # PNGの圧縮レベル (0-9, 9が最高圧縮)。品質とは直接関係ない。
                    # 一旦固定値 (6) を使うか、バランスから簡易的に計算？ -> 固定値6 (Pillowのデフォルトより少し高め) にする
                    compress_level = 6
                    save_options = {
                        "format": "PNG",
                        "optimize": True,
                        "compress_level": compress_level,
                    }
                    # EXIFはPNG標準では保存されないことが多いが、念のため試みる (Pillow次第)
                    if (
                        exif_handling == "keep"
                        and hasattr(img, "info")
                        and "exif" in img.info
                    ):
                        if "exif" not in save_options:
                            save_options["exif"] = img.info["exif"]  # 試すだけ

                elif actual_output_format == "WEBP":
                    output_ext = ".webp"
                    final_dest_path_str = update_extension(
                        final_dest_path_str, output_ext
                    )
                    save_options = {
                        "format": "WEBP",
                        "quality": optimized_quality,
                        "lossless": webp_lossless,
                        "method": 6,  # 高品質な圧縮方法
                    }
                    # EXIF情報を保持する場合
                    if (
                        exif_handling == "keep"
                        and hasattr(img, "info")
                        and "exif" in img.info
                    ):
                        save_options["exif"] = img.info["exif"]

                    # ロスレスで透明度がある場合は RGBA のまま保存
                    if webp_lossless and "A" in save_img.mode:
                        logger.debug("WebPロスレスでRGBAモードのまま保存")
                    # ロッシーで透明度がある場合も Pillow はよしなに対応してくれるはず
                    elif not webp_lossless and "A" in save_img.mode:
                        logger.debug(
                            "WebPロッシーでRGBAモードのまま保存 (透明度サポート)"
                        )
                    # 透明度がない場合はRGBで良い
                    elif "A" not in save_img.mode and save_img.mode != "RGB":
                        logger.debug(
                            f"WebP用に画像をRGBモードに変換中 (元: {save_img.mode})"
                        )
                        save_img = save_img.convert("RGB")

                else:
                    logger.error(f"未対応の出力形式です: {actual_output_format}")
                    return False, False, estimated_size  # エラーとして返す

                # アトミック書き込みの実装（一時ファイル → リネーム）
                import tempfile
                import uuid
                import shutil

                # 一時ファイルパスを生成（出力先と同一ボリューム上に作成）
                temp_dir = dest_dir if dest_dir.exists() else tempfile.gettempdir()
                temp_filename = f"resize_temp_{uuid.uuid4().hex}{output_ext}"
                temp_path = temp_dir / temp_filename
                temp_path_str = str(temp_path)

                # 画像を一時ファイルに保存
                def save_image_to_temp():
                    logger.debug(
                        f"一時ファイルに保存: {temp_path_str}, オプション: {save_options}"
                    )
                    save_img.save(temp_path_str, **save_options)
                    return True

                # 一時ファイルを最終出力先にリネーム
                def rename_to_final():
                    logger.debug(
                        f"一時ファイルを最終出力先に移動: {temp_path_str} → {final_dest_path_str}"
                    )
                    shutil.move(temp_path_str, final_dest_path_str)
                    return True

                try:
                    # 一時ファイルに保存
                    logger.info(f"画像を保存中: フォーマット={actual_output_format}, パス={final_dest_path_str}")
                    success = retry_on_file_error(
                        save_image_to_temp, max_retries=3, retry_delay=0.5
                    )
                    if not success:
                        raise OSError(
                            f"一時ファイルへの保存に失敗しました: {temp_path_str}"
                        )

                    # 最終出力先にリネーム
                    success = retry_on_file_error(
                        rename_to_final, max_retries=3, retry_delay=0.5
                    )
                    if not success:
                        raise OSError(
                            f"最終出力先へのリネームに失敗しました: {final_dest_path_str}"
                        )

                    logger.info(f"保存完了（アトミック操作）: {final_dest_path_str}")
                except Exception as e:
                    logger.error(f"画像保存エラー ({final_dest_path_str}): {e}")
                    # 一時ファイルの削除を試みる
                    try:
                        if temp_path.exists():
                            temp_path.unlink()
                    except Exception as cleanup_error:
                        logger.debug(
                            f"一時ファイルのクリーンアップに失敗: {cleanup_error}"
                        )
                    return False, False, estimated_size

                if is_mpo_input:
                    logger.info(
                        f"MPO形式のファイルをJPEGとして保存処理を実行します: {final_dest_path.name}"
                    )

                if save_img.mode != "RGB":
                    logger.debug(
                        f"JPEG保存のためRGBモードに変換中 (元: {save_img.mode})"
                    )
                    save_img = save_img.convert("RGB")

                return True, keep_original_size, estimated_size

        except UnidentifiedImageError:
            logger.error(f"未対応または破損した画像形式: {source_path}")
            return False, False, None

        except Exception as e:
            logger.error(f"画像処理エラー: {e}")
            return False, False, None

    except OSError as e:
        # ファイルアクセスエラー
        error_msg = analyze_os_error(e)
        logger.error(f"ファイルアクセスエラー: {error_msg}")
        return False, False, None

    except Exception as e:
        # その他の予期せぬエラー
        logger.error(f"予期せぬエラー: {e}")
        return False, False, None


def update_extension(file_path, new_ext):
    """
    ファイルパスの拡張子を更新します

    Args:
        file_path: 元のファイルパス
        new_ext: 新しい拡張子 (ドット付き、例: '.jpg')

    Returns:
        str: 拡張子を更新したパス
    """
    path_obj = Path(file_path)
    stem = path_obj.stem
    parent = path_obj.parent

    # 新しいパスを作成
    new_path = parent / f"{stem}{new_ext}"

    return str(new_path)


def adjust_quality_by_balance(quality, balance, format):
    """
    圧縮と品質のバランスに基づいて品質パラメータを調整します

    Args:
        quality: 元の品質値 (1-100)
        balance: 圧縮と品質のバランス (1-10, 1=最高圧縮率, 10=最高品質) - 現在は主に品質調整に使用
        format: 出力形式 ('jpeg', 'png', 'webp')

    Returns:
        int: 調整後の品質値
    """
    # バランス値を正規化 (1-10 → 0.0-1.0)
    balance_factor = (balance - 1) / 9.0

    # 形式ごとの品質調整
    if format.lower() == "jpeg":
        # JPEGの場合: バランス値が高いほど高品質
        # balance = 1 (最高圧縮) → quality * 0.7
        # balance = 10 (最高品質) → quality * 1.2 (上限100)
        adjustment = 0.7 + (balance_factor * 0.5)
        new_quality = int(quality * adjustment)

    elif format.lower() == "png":
        # PNGの場合: 圧縮レベルは別関数で処理するのでそのまま返す
        new_quality = quality

    elif format.lower() == "webp":
        # WebPの場合: バランスに基づく調整
        # balance = 1 (最高圧縮) → quality * 0.6
        # balance = 10 (最高品質) → quality * 1.1 (上限100)
        adjustment = 0.6 + (balance_factor * 0.5)
        new_quality = int(quality * adjustment)

    else:
        # 未対応の形式はそのまま返す
        new_quality = quality

    # 範囲の正規化 (1-100)
    return max(1, min(100, new_quality))


def format_file_size(size_in_bytes):
    """
    ファイルサイズを読みやすい形式に変換します

    Args:
        size_in_bytes: バイト単位のサイズ

    Returns:
        str: 人間が読みやすい形式（例: 1.2 MB）
    """
    for unit in ["B", "KB", "MB", "GB"]:
        if size_in_bytes < 1024.0 or unit == "GB":
            break
        size_in_bytes /= 1024.0
    return f"{size_in_bytes:.1f} {unit}"


def resize_and_compress_image_memory(
    source_image=None,
    output_buffer=None,
    resize_mode: str = "width",
    resize_value: int = None,
    quality: int = 85,
    output_format: str = "jpeg",
    exif_handling: str = "keep",
    lanczos_filter: bool = True,
    progressive: bool = False,
    optimize: bool = False,
    webp_lossless: bool = False,
) -> tuple[bool, str | None]:
    """
    メモリベースの画像リサイズと圧縮を行う
    
    Args:
        source_image: PIL.Imageオブジェクト
        output_buffer: io.BytesIOオブジェクト
        resize_mode: リサイズモード ('width', 'height', 'longest_side', 'percentage', 'none')
        resize_value: リサイズ値
        quality: 圧縮品質 (1-100)
        output_format: 出力フォーマット ('jpeg', 'png', 'webp')
        exif_handling: EXIFの扱い ('keep', 'remove')
        lanczos_filter: Lanczosフィルタを使用するか
        progressive: プログレッシブJPEGを使用するか
        optimize: 最適化を使用するか
        webp_lossless: WebPロスレスを使用するか
        
    Returns:
        tuple[bool, str | None]: (成功したか, エラーメッセージ)
    """
    try:
        # 入力検証
        if source_image is None or output_buffer is None:
            return False, "source_imageとoutput_bufferは必須です"
        
        if not hasattr(source_image, 'size') or not hasattr(source_image, 'mode'):
            return False, "無効な画像オブジェクトです"
            
        if not hasattr(output_buffer, 'write') or not hasattr(output_buffer, 'seek'):
            return False, "無効な出力バッファです"
        
        # リサイズ値の検証（resize_mode="none"の場合はスキップ）
        if resize_mode != "none":
            if resize_value is None or resize_value <= 0:
                return False, f"無効なリサイズ値: {resize_value} (resize_mode={resize_mode})"
        
        # 画像のコピーを作成（元の画像を変更しないため）
        img = source_image.copy()
        original_width, original_height = img.size
        
        # リサイズ処理
        if resize_mode != "none":
            new_size = None
            
            if resize_mode == "width":
                ratio = original_height / original_width
                new_height = int(resize_value * ratio)
                new_size = (resize_value, new_height)
            elif resize_mode == "height":
                ratio = original_width / original_height
                new_width = int(resize_value * ratio)
                new_size = (new_width, resize_value)
            elif resize_mode == "longest_side":
                if original_width > original_height:
                    ratio = original_height / original_width
                    new_size = (resize_value, int(resize_value * ratio))
                else:
                    ratio = original_width / original_height
                    new_size = (int(resize_value * ratio), resize_value)
            elif resize_mode == "percentage":
                scale = resize_value / 100.0
                new_size = (int(original_width * scale), int(original_height * scale))
            
            if new_size:
                filter_type = Image.LANCZOS if lanczos_filter else Image.BICUBIC
                img = img.resize(new_size, filter_type)
        
        # 出力フォーマットの正規化
        output_format = output_format.lower()
        if output_format == "jpg":
            output_format = "jpeg"
        
        # 保存オプションの設定
        save_options = {}
        
        if output_format == "jpeg":
            save_options["format"] = "JPEG"
            save_options["quality"] = quality
            save_options["optimize"] = optimize
            save_options["progressive"] = progressive
            
            # EXIF処理
            if exif_handling == "keep" and hasattr(source_image, "info") and "exif" in source_image.info:
                save_options["exif"] = source_image.info["exif"]
            
            # JPEGはRGBモードが必要
            if img.mode not in ("RGB", "L"):
                if img.mode == "RGBA":
                    # 透明度がある場合は白背景で合成
                    background = Image.new("RGB", img.size, (255, 255, 255))
                    background.paste(img, mask=img.split()[3])
                    img = background
                else:
                    img = img.convert("RGB")
                    
        elif output_format == "png":
            save_options["format"] = "PNG"
            save_options["optimize"] = optimize
            save_options["compress_level"] = 6
            
            # PNGはEXIFをサポートしない場合が多い
            if exif_handling == "keep" and hasattr(source_image, "info"):
                # PNGメタデータとして保存を試みる
                for key in ["exif", "dpi", "icc_profile"]:
                    if key in source_image.info:
                        save_options[key] = source_image.info[key]
                        
        elif output_format == "webp":
            save_options["format"] = "WEBP"
            save_options["quality"] = quality
            save_options["lossless"] = webp_lossless
            save_options["method"] = 6
            
            # EXIF処理
            if exif_handling == "keep" and hasattr(source_image, "info") and "exif" in source_image.info:
                save_options["exif"] = source_image.info["exif"]
            
            # WebPはRGBAをサポート
            if not webp_lossless and img.mode not in ("RGB", "RGBA", "L"):
                img = img.convert("RGB")
        else:
            return False, f"サポートされていない出力フォーマット: {output_format}"
        
        # バッファに保存
        output_buffer.seek(0)
        img.save(output_buffer, **save_options)
        output_buffer.seek(0)
        
        return True, None
        
    except Exception as e:
        error_msg = f"画像処理エラー: {str(e)}"
        logger.error(error_msg)
        return False, error_msg


def save_progress(processed_files, remaining_files, output_file="progress.json"):
    """
    処理の進捗状況を保存します

    Args:
        processed_files: 処理済みファイルのリスト
        remaining_files: 残りのファイルのリスト
        output_file: 出力ファイル名
    """
    data = {
        "processed": [str(p) for p in processed_files],
        "remaining": [str(r) for r in remaining_files],
        "timestamp": time.time(),
    }

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def load_progress(input_file="progress.json"):
    """
    保存された進捗を読み込みます

    Args:
        input_file: 入力ファイル名

    Returns:
        tuple: (処理済みファイルリスト, 残りファイルリスト)
    """
    try:
        if not os.path.exists(input_file):
            return [], []

        with open(input_file, "r", encoding="utf-8") as f:
            data = json.load(f)

        processed = [Path(p) for p in data.get("processed", [])]
        remaining = [Path(r) for r in data.get("remaining", [])]

        return processed, remaining
    except Exception as e:
        logger.error(f"進捗データ読み込みエラー: {e}")
        return [], []


# 初期ロギング設定
# setup_logging()
