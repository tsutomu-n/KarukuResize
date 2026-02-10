"""GUI向けの画像保存パイプライン。

品質・出力形式・EXIFポリシー・ドライランを集約して扱う。
"""

from __future__ import annotations

from dataclasses import dataclass
import logging
from pathlib import Path
from typing import Dict, Iterable, Literal, Optional, Tuple

from PIL import ExifTags, Image, features

try:
    import pillow_avif  # noqa: F401
except ImportError:
    pass

SaveFormat = Literal["jpeg", "png", "webp", "avif"]
ExifMode = Literal["keep", "remove", "edit"]

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class SaveOptions:
    output_format: SaveFormat
    quality: int = 85
    dry_run: bool = False
    exif_mode: ExifMode = "keep"
    remove_gps: bool = False
    exif_edit: Optional["ExifEditValues"] = None
    verbose: bool = False


@dataclass(frozen=True)
class ExifEditValues:
    artist: Optional[str] = None
    copyright_text: Optional[str] = None
    user_comment: Optional[str] = None
    datetime_original: Optional[str] = None


@dataclass(frozen=True)
class SaveResult:
    success: bool
    output_path: Path
    exif_mode: ExifMode
    dry_run: bool = False
    had_source_exif: bool = False
    exif_requested: bool = False
    exif_attached: bool = False
    exif_fallback_without_metadata: bool = False
    exif_skipped_reason: Optional[str] = None
    gps_removed: bool = False
    edited_fields: Tuple[str, ...] = ()
    skipped_reason: Optional[str] = None
    error: Optional[str] = None


@dataclass(frozen=True)
class ExifPreview:
    exif_mode: ExifMode
    had_source_exif: bool
    source_tag_count: int
    source_has_gps: bool
    exif_will_be_attached: bool
    exif_requested: bool
    gps_removed: bool = False
    edited_fields: Tuple[str, ...] = ()
    skipped_reason: Optional[str] = None


_FORMAT_EXTENSIONS: Dict[SaveFormat, str] = {
    "jpeg": ".jpg",
    "png": ".png",
    "webp": ".webp",
    "avif": ".avif",
}

_EXIF_TAG_GPS_INFO = 0x8825
_EXIF_TAG_ARTIST = 0x013B
_EXIF_TAG_COPYRIGHT = 0x8298
_EXIF_TAG_DATETIME_ORIGINAL = 0x9003
_EXIF_TAG_USER_COMMENT = 0x9286


def supported_output_formats() -> list[SaveFormat]:
    """実行環境で利用可能な出力形式を返す。"""
    formats: list[SaveFormat] = ["jpeg", "png"]
    if _feature_enabled("webp") or _registered_format("WEBP"):
        formats.append("webp")
    if _feature_enabled("avif") or _registered_format("AVIF"):
        formats.append("avif")
    return formats


def normalize_quality(value: int) -> int:
    """品質値を5-100（5刻み）に丸める。"""
    clamped = max(5, min(100, int(value)))
    rounded = int(round(clamped / 5) * 5)
    return max(5, min(100, rounded))


def resolve_output_format(
    selected: str,
    source_image: Image.Image,
    available_formats: Optional[Iterable[SaveFormat]] = None,
) -> SaveFormat:
    """ユーザー選択と入力画像から最終出力形式を決定する。"""
    available = set(available_formats or supported_output_formats())
    selected_lc = selected.lower()

    if selected_lc == "auto":
        if "A" in source_image.getbands() or source_image.mode in ("P", "1"):
            return "png"
        return "jpeg"

    requested = selected_lc
    if requested == "jpg":
        requested = "jpeg"

    if requested not in {"jpeg", "png", "webp", "avif"}:
        return "jpeg"

    if requested not in available:
        return "jpeg"

    return requested  # type: ignore[return-value]


def destination_with_extension(base_path: Path, output_format: SaveFormat) -> Path:
    """出力形式に合わせて拡張子を更新する。"""
    return base_path.with_suffix(_FORMAT_EXTENSIONS[output_format])


def preview_exif_plan(
    source_image: Image.Image,
    exif_mode: ExifMode,
    remove_gps: bool,
    edit_values: Optional[ExifEditValues] = None,
) -> ExifPreview:
    """保存前にEXIFの反映予定を計算する。"""
    source_tag_count = 0
    source_has_gps = False
    had_source_exif = False

    try:
        source_exif = source_image.getexif()
        source_tag_count = len(source_exif)
        source_has_gps = _EXIF_TAG_GPS_INFO in source_exif
        had_source_exif = bool(source_exif)
    except Exception:
        source_tag_count = 0
        source_has_gps = False
        had_source_exif = False

    exif_bytes, exif_meta = _build_exif_bytes(
        source_image=source_image,
        exif_mode=exif_mode,
        remove_gps=remove_gps,
        edit_values=edit_values,
    )
    return ExifPreview(
        exif_mode=exif_mode,
        had_source_exif=had_source_exif,
        source_tag_count=source_tag_count,
        source_has_gps=source_has_gps,
        exif_will_be_attached=exif_bytes is not None,
        exif_requested=exif_meta.exif_requested,
        gps_removed=exif_meta.gps_removed,
        edited_fields=exif_meta.edited_fields,
        skipped_reason=exif_meta.exif_skipped_reason,
    )


def save_image(
    source_image: Image.Image,
    resized_image: Image.Image,
    output_path: Path,
    options: SaveOptions,
) -> SaveResult:
    """画像を保存する（必要ならEXIFを付与）。"""
    final_path = destination_with_extension(output_path, options.output_format)

    exif_bytes, exif_meta = _build_exif_bytes(
        source_image=source_image,
        exif_mode=options.exif_mode,
        remove_gps=options.remove_gps,
        edit_values=options.exif_edit,
    )
    if options.verbose:
        logger.debug(
            "save_image: format=%s quality=%s dry_run=%s exif_mode=%s has_exif=%s gps_removed=%s edits=%s",
            options.output_format,
            options.quality,
            options.dry_run,
            options.exif_mode,
            exif_meta.had_source_exif,
            exif_meta.gps_removed,
            exif_meta.edited_fields,
        )

    if options.dry_run:
        return SaveResult(
            success=True,
            output_path=final_path,
            exif_mode=options.exif_mode,
            dry_run=True,
            had_source_exif=exif_meta.had_source_exif,
            exif_requested=exif_meta.exif_requested,
            exif_attached=exif_bytes is not None,
            exif_skipped_reason=exif_meta.exif_skipped_reason,
            gps_removed=exif_meta.gps_removed,
            edited_fields=exif_meta.edited_fields,
            skipped_reason="dry-run",
        )

    save_img = resized_image
    save_kwargs = _build_save_kwargs(options.output_format, options.quality)

    if options.output_format in {"jpeg", "avif"} and save_img.mode in {"RGBA", "LA", "P"}:
        # 透過を持つ画像は白背景へ合成して保存する
        rgba = save_img.convert("RGBA")
        background = Image.new("RGBA", rgba.size, (255, 255, 255, 255))
        background.alpha_composite(rgba)
        save_img = background.convert("RGB")
    elif options.output_format == "jpeg" and save_img.mode not in {"RGB", "L"}:
        save_img = save_img.convert("RGB")

    exif_requested = bool(exif_bytes is not None)
    if exif_bytes is not None and options.output_format in {"jpeg", "png", "webp", "avif"}:
        save_kwargs["exif"] = exif_bytes

    # EXIF付与に失敗した場合は、メタデータなし保存へフォールバックする。
    try:
        save_img.save(final_path, **save_kwargs)
        exif_attached = "exif" in save_kwargs
        return SaveResult(
            success=True,
            output_path=final_path,
            exif_mode=options.exif_mode,
            dry_run=False,
            had_source_exif=exif_meta.had_source_exif,
            exif_requested=exif_requested,
            exif_attached=exif_attached,
            exif_skipped_reason=exif_meta.exif_skipped_reason,
            gps_removed=exif_meta.gps_removed,
            edited_fields=exif_meta.edited_fields,
        )
    except Exception as e:  # pragma: no cover - GUI経由で表示
        exif_error = str(e)
        if "exif" in save_kwargs:
            save_kwargs_without_exif = dict(save_kwargs)
            save_kwargs_without_exif.pop("exif", None)
            try:
                save_img.save(final_path, **save_kwargs_without_exif)
                return SaveResult(
                    success=True,
                    output_path=final_path,
                    exif_mode=options.exif_mode,
                    dry_run=False,
                    had_source_exif=exif_meta.had_source_exif,
                    exif_requested=exif_requested,
                    exif_attached=False,
                    exif_fallback_without_metadata=True,
                    exif_skipped_reason=f"exif-write-failed: {exif_error}",
                    gps_removed=exif_meta.gps_removed,
                    edited_fields=exif_meta.edited_fields,
                )
            except Exception:
                pass
        return SaveResult(
            success=False,
            output_path=final_path,
            exif_mode=options.exif_mode,
            error=str(e),
            dry_run=False,
            had_source_exif=exif_meta.had_source_exif,
            exif_requested=exif_requested,
            exif_attached=False,
            exif_skipped_reason=exif_meta.exif_skipped_reason,
            gps_removed=exif_meta.gps_removed,
            edited_fields=exif_meta.edited_fields,
        )


def _build_save_kwargs(output_format: SaveFormat, quality: int) -> Dict[str, object]:
    normalized_quality = normalize_quality(quality)

    if output_format == "jpeg":
        return {
            "format": "JPEG",
            "quality": min(normalized_quality, 95),
            "optimize": True,
            "progressive": True,
        }
    if output_format == "png":
        # PNGはロスレス。quality指定を圧縮レベルへ変換する。
        compress_level = int(round((100 - normalized_quality) / 100 * 9))
        return {
            "format": "PNG",
            "optimize": True,
            "compress_level": max(0, min(9, compress_level)),
        }
    if output_format == "webp":
        return {
            "format": "WEBP",
            "quality": normalized_quality,
            "method": 6,
        }
    # avif
    return {
        "format": "AVIF",
        "quality": normalized_quality,
    }


@dataclass(frozen=True)
class ExifBuildMeta:
    had_source_exif: bool
    exif_requested: bool
    gps_removed: bool = False
    edited_fields: Tuple[str, ...] = ()
    exif_skipped_reason: Optional[str] = None


def _build_exif_bytes(
    source_image: Image.Image,
    exif_mode: ExifMode,
    remove_gps: bool,
    edit_values: Optional[ExifEditValues] = None,
) -> tuple[Optional[bytes], ExifBuildMeta]:
    if exif_mode == "remove":
        return None, ExifBuildMeta(had_source_exif=False, exif_requested=False)

    try:
        exif = source_image.getexif()
    except Exception:
        return None, ExifBuildMeta(
            had_source_exif=False,
            exif_requested=False,
            exif_skipped_reason="getexif-failed",
        )

    had_source_exif = bool(exif)
    if not had_source_exif and exif_mode != "edit":
        return None, ExifBuildMeta(had_source_exif=False, exif_requested=False)

    gps_removed = False
    if remove_gps and _EXIF_TAG_GPS_INFO in exif:
        del exif[_EXIF_TAG_GPS_INFO]
        gps_removed = True

    edited_fields: Tuple[str, ...] = ()
    if exif_mode == "edit" and edit_values is not None:
        exif, edited_fields = _apply_exif_edits(exif, edit_values)

    if not had_source_exif and not edited_fields and not gps_removed:
        return None, ExifBuildMeta(had_source_exif=False, exif_requested=False)

    try:
        return (
            exif.tobytes(),
            ExifBuildMeta(
                had_source_exif=had_source_exif,
                exif_requested=True,
                gps_removed=gps_removed,
                edited_fields=edited_fields,
            ),
        )
    except Exception:
        return (
            None,
            ExifBuildMeta(
                had_source_exif=had_source_exif,
                exif_requested=True,
                gps_removed=gps_removed,
                edited_fields=edited_fields,
                exif_skipped_reason="exif-serialize-failed",
            ),
        )


def _apply_exif_edits(exif: Image.Exif, edit_values: ExifEditValues) -> tuple[Image.Exif, Tuple[str, ...]]:
    edited: list[str] = []

    def clean_text(value: Optional[str]) -> Optional[str]:
        if value is None:
            return None
        stripped = value.strip()
        return stripped if stripped else None

    artist = clean_text(edit_values.artist)
    if artist is not None:
        exif[_tag_value("Artist", _EXIF_TAG_ARTIST)] = artist
        edited.append("Artist")

    copyright_text = clean_text(edit_values.copyright_text)
    if copyright_text is not None:
        exif[_tag_value("Copyright", _EXIF_TAG_COPYRIGHT)] = copyright_text
        edited.append("Copyright")

    datetime_original = clean_text(edit_values.datetime_original)
    if datetime_original is not None:
        exif[_tag_value("DateTimeOriginal", _EXIF_TAG_DATETIME_ORIGINAL)] = datetime_original
        edited.append("DateTimeOriginal")

    user_comment = clean_text(edit_values.user_comment)
    if user_comment is not None:
        # EXIF UserCommentは8byteのエンコーディング識別子を前置する。
        exif[_tag_value("UserComment", _EXIF_TAG_USER_COMMENT)] = b"ASCII\x00\x00\x00" + user_comment.encode(
            "ascii", errors="replace"
        )
        edited.append("UserComment")

    return exif, tuple(edited)


def _feature_enabled(feature_name: str) -> bool:
    try:
        return bool(features.check(feature_name))
    except Exception:
        return False


def _registered_format(name: str) -> bool:
    try:
        return any(v.upper() == name for v in Image.registered_extensions().values())
    except Exception:
        return False


def _tag_value(name: str, fallback: int) -> int:
    base = getattr(ExifTags, "Base", None)
    if base is None:
        return fallback
    tag = getattr(base, name, None)
    if tag is None:
        return fallback
    return int(getattr(tag, "value", fallback))
