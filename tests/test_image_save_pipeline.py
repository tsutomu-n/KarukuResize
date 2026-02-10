from pathlib import Path

from PIL import ExifTags, Image

from karuku_resizer.image_save_pipeline import (
    ExifEditValues,
    SaveOptions,
    build_encoder_save_kwargs,
    destination_with_extension,
    normalize_avif_speed,
    normalize_quality,
    normalize_webp_method,
    preview_exif_plan,
    resolve_output_format,
    save_image,
)


def _tag_value(name: str, fallback: int) -> int:
    base = getattr(ExifTags, "Base", None)
    if base is None:
        return fallback
    tag = getattr(base, name, None)
    if tag is None:
        return fallback
    return int(getattr(tag, "value", fallback))


def _make_source_with_artist(path: Path, artist: str = "Alice") -> Image.Image:
    source = Image.new("RGB", (64, 48), (120, 30, 10))
    exif = Image.Exif()
    exif[_tag_value("Artist", 0x013B)] = artist
    source.save(path, format="JPEG", exif=exif.tobytes())
    loaded = Image.open(path)
    loaded.load()
    return loaded


def test_normalize_quality_rounds_and_clamps():
    assert normalize_quality(0) == 5
    assert normalize_quality(1) == 5
    assert normalize_quality(6) == 5
    assert normalize_quality(7) == 5
    assert normalize_quality(8) == 10
    assert normalize_quality(99) == 100
    assert normalize_quality(150) == 100


def test_normalize_webp_method_clamps():
    assert normalize_webp_method(-1) == 0
    assert normalize_webp_method(0) == 0
    assert normalize_webp_method(3) == 3
    assert normalize_webp_method(10) == 6


def test_normalize_avif_speed_clamps():
    assert normalize_avif_speed(-5) == 0
    assert normalize_avif_speed(2) == 2
    assert normalize_avif_speed(99) == 10


def test_build_encoder_save_kwargs_webp_and_avif_options():
    webp_kwargs = build_encoder_save_kwargs(
        output_format="webp",
        quality=83,
        webp_method=2,
        webp_lossless=True,
        avif_speed=6,
    )
    assert webp_kwargs["format"] == "WEBP"
    assert webp_kwargs["quality"] == 85
    assert webp_kwargs["method"] == 2
    assert webp_kwargs["lossless"] is True

    avif_kwargs = build_encoder_save_kwargs(
        output_format="avif",
        quality=95,
        webp_method=6,
        webp_lossless=False,
        avif_speed=2,
    )
    assert avif_kwargs["format"] == "AVIF"
    assert avif_kwargs["quality"] == 95
    assert avif_kwargs["speed"] == 2


def test_resolve_output_format_auto_and_fallback():
    rgba = Image.new("RGBA", (10, 10), (255, 0, 0, 128))
    rgb = Image.new("RGB", (10, 10), (255, 0, 0))

    assert resolve_output_format("auto", rgba, {"jpeg", "png", "webp"}) == "png"
    assert resolve_output_format("auto", rgb, {"jpeg", "png", "webp"}) == "jpeg"
    assert resolve_output_format("webp", rgb, {"jpeg", "png"}) == "jpeg"
    assert resolve_output_format("jpg", rgb, {"jpeg", "png"}) == "jpeg"


def test_destination_with_extension():
    assert destination_with_extension(Path("out/file"), "jpeg") == Path("out/file.jpg")
    assert destination_with_extension(Path("out/file.tmp"), "png") == Path("out/file.png")


def test_save_image_keep_exif(temp_dir):
    source_path = temp_dir / "source_keep.jpg"
    source = _make_source_with_artist(source_path, "Keep Artist")
    resized = source.resize((32, 24))

    result = save_image(
        source_image=source,
        resized_image=resized,
        output_path=temp_dir / "output_keep",
        options=SaveOptions(output_format="jpeg", quality=85, exif_mode="keep"),
    )

    assert result.success
    assert result.exif_attached
    assert result.had_source_exif
    assert result.output_path.exists()

    output = Image.open(result.output_path)
    output_exif = output.getexif()
    assert output_exif.get(_tag_value("Artist", 0x013B)) == "Keep Artist"


def test_save_image_edit_exif_without_source_exif(temp_dir):
    source = Image.new("RGB", (80, 60), (0, 120, 180))
    resized = source.resize((40, 30))

    result = save_image(
        source_image=source,
        resized_image=resized,
        output_path=temp_dir / "output_edit",
        options=SaveOptions(
            output_format="jpeg",
            quality=80,
            exif_mode="edit",
            exif_edit=ExifEditValues(
                artist="Edited Artist",
                copyright_text="(c) Example",
                user_comment="note",
                datetime_original="2026:02:10 11:30:00",
            ),
        ),
    )

    assert result.success
    assert result.exif_attached
    assert not result.had_source_exif
    assert "Artist" in result.edited_fields
    assert "DateTimeOriginal" in result.edited_fields
    assert result.output_path.exists()

    output = Image.open(result.output_path)
    output_exif = output.getexif()
    assert output_exif.get(_tag_value("Artist", 0x013B)) == "Edited Artist"
    assert output_exif.get(_tag_value("Copyright", 0x8298)) == "(c) Example"
    assert output_exif.get(_tag_value("DateTimeOriginal", 0x9003)) == "2026:02:10 11:30:00"
    comment = output_exif.get(_tag_value("UserComment", 0x9286))
    assert isinstance(comment, (bytes, bytearray))
    assert bytes(comment).startswith(b"ASCII\x00\x00\x00")


def test_save_image_remove_exif(temp_dir):
    source_path = temp_dir / "source_remove.jpg"
    source = _make_source_with_artist(source_path, "Drop Artist")
    resized = source.resize((32, 24))

    result = save_image(
        source_image=source,
        resized_image=resized,
        output_path=temp_dir / "output_remove",
        options=SaveOptions(output_format="jpeg", quality=85, exif_mode="remove"),
    )

    assert result.success
    assert not result.exif_attached
    assert result.exif_mode == "remove"

    output = Image.open(result.output_path)
    output_exif = output.getexif()
    assert output_exif.get(_tag_value("Artist", 0x013B)) is None


def test_preview_exif_plan_reports_remove_mode(temp_dir):
    source_path = temp_dir / "source_preview_remove.jpg"
    source = _make_source_with_artist(source_path, "Preview Artist")

    preview = preview_exif_plan(
        source_image=source,
        exif_mode="remove",
        remove_gps=True,
    )

    assert preview.exif_mode == "remove"
    assert preview.had_source_exif
    assert preview.source_tag_count >= 1
    assert not preview.exif_will_be_attached
    assert not preview.exif_requested


def test_preview_exif_plan_reports_edit_fields_without_source_exif():
    source = Image.new("RGB", (80, 60), (50, 100, 150))
    preview = preview_exif_plan(
        source_image=source,
        exif_mode="edit",
        remove_gps=False,
        edit_values=ExifEditValues(
            artist="Edited Artist",
            user_comment="memo",
        ),
    )

    assert preview.exif_mode == "edit"
    assert not preview.had_source_exif
    assert preview.source_tag_count == 0
    assert preview.exif_will_be_attached
    assert preview.exif_requested
    assert "Artist" in preview.edited_fields
    assert "UserComment" in preview.edited_fields


def test_save_image_dry_run_does_not_write_file(temp_dir):
    source = Image.new("RGB", (64, 64), (10, 20, 30))
    resized = source.resize((32, 32))

    result = save_image(
        source_image=source,
        resized_image=resized,
        output_path=temp_dir / "dry_output",
        options=SaveOptions(output_format="jpeg", quality=85, exif_mode="keep", dry_run=True),
    )

    assert result.success
    assert result.dry_run
    assert result.skipped_reason == "dry-run"
    assert not result.output_path.exists()
