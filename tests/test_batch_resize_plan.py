from types import SimpleNamespace

from PIL import Image

from karuku_resizer.gui_app import ResizeApp, ResizePlan
from karuku_resizer.image_save_pipeline import SaveOptions, supported_output_formats


class DummyVar:
    def __init__(self, value):
        self.value = value

    def get(self):
        return self.value

    def set(self, value):
        self.value = value


def test_resolve_target_from_resize_plan_preserves_landscape_ratio():
    plan = ResizePlan(mode="width", width=1000)

    target = ResizeApp._resolve_target_from_resize_plan((4000, 3000), plan)

    assert target == (1000, 750)


def test_resolve_target_from_resize_plan_preserves_portrait_ratio():
    plan = ResizePlan(mode="width", width=1000)

    target = ResizeApp._resolve_target_from_resize_plan((3000, 4000), plan)

    assert target == (1000, 1333)


def test_resolve_target_from_resize_plan_uses_fixed_size_when_requested():
    plan = ResizePlan(mode="fixed", width=1000, height=750)

    target = ResizeApp._resolve_target_from_resize_plan((3000, 4000), plan)

    assert target == (1000, 750)


def test_resolve_target_from_resize_plan_clamps_extreme_ratio_to_one_pixel():
    plan = ResizePlan(mode="width", width=1)

    target = ResizeApp._resolve_target_from_resize_plan((1000, 1), plan)

    assert target == (1, 1)


def test_resolve_output_format_for_image_with_selection_auto_depends_on_image_mode():
    app = object.__new__(ResizeApp)
    app.available_formats = supported_output_formats()

    rgba_image = Image.new("RGBA", (32, 32), (255, 0, 0, 128))
    rgb_image = Image.new("RGB", (32, 32), (255, 0, 0))

    assert app._resolve_output_format_for_image_with_selection(rgba_image, "auto") == "png"
    assert app._resolve_output_format_for_image_with_selection(rgb_image, "auto") == "jpeg"


def test_snapshot_preview_save_options_requires_valid_exif_datetime_for_edit_mode():
    app = object.__new__(ResizeApp)
    app.quality_var = DummyVar("85")
    app.webp_method_var = DummyVar("6")
    app.avif_speed_var = DummyVar("6")
    app.webp_lossless_var = DummyVar(False)
    app.exif_mode_var = DummyVar("編集")
    app.remove_gps_var = DummyVar(False)
    app.exif_datetime_original_var = DummyVar("invalid")
    app.exif_artist_var = DummyVar("artist")
    app.exif_copyright_var = DummyVar("")
    app.exif_user_comment_var = DummyVar("")

    options = app._snapshot_preview_save_options("jpeg")

    assert options is None


def test_start_preview_size_estimation_keeps_inflight_version_for_same_request():
    app = object.__new__(ResizeApp)
    app._snapshot_encoder_settings = lambda: (85, 6, 6, False)
    precise_options = SaveOptions(output_format="jpeg", quality=85, exif_mode="keep")
    app._snapshot_preview_save_options = lambda output_format: precise_options
    app._format_preview_size_with_reduction = lambda source_bytes, estimated_kb: "-"
    app.info_resized_var = DummyVar("")
    app._size_estimation_version = 7
    app._size_estimation_timeout_id = None

    job = SimpleNamespace(preview_size_cache={}, source_size_bytes=1024)
    source = Image.new("RGB", (64, 64), (255, 0, 0))
    fast_cache_key = ("fast", 64, 64, "RGB", "jpeg", 75, 6, 6, False)
    precise_cache_key = ("precise", 64, 64, "RGB", "jpeg", 85, 6, 6, False, "keep", False, "", "", "", "")
    app._size_estimation_inflight_key = (id(job), fast_cache_key, precise_cache_key)

    app._start_preview_size_estimation(
        job=job,
        source=source,
        output_format="jpeg",
        pct=100.0,
        fmt_label="JPEG",
    )

    assert app._size_estimation_version == 7
    assert app._size_estimation_inflight_key == (id(job), fast_cache_key, precise_cache_key)
