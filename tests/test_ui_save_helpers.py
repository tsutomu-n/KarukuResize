from karuku_resizer.image_save_pipeline import destination_with_extension
from karuku_resizer.ui_save_helpers import build_unique_batch_base_path


def test_build_unique_batch_base_path_uses_safe_stem_for_collisions(temp_dir):
    first = build_unique_batch_base_path(
        output_dir=temp_dir,
        stem="a:b*image",
        output_format="jpeg",
        destination_with_extension_func=destination_with_extension,
        dry_run=False,
    )
    first.with_suffix('.jpg').touch()

    second = build_unique_batch_base_path(
        output_dir=temp_dir,
        stem="a:b*image",
        output_format="jpeg",
        destination_with_extension_func=destination_with_extension,
        dry_run=False,
    )

    assert second.name == "a_b_image_resized_1"


def test_build_unique_batch_base_path_keeps_sanitized_stem_for_collision_without_dots(temp_dir):
    first = build_unique_batch_base_path(
        output_dir=temp_dir,
        stem="folder/name",
        output_format="png",
        destination_with_extension_func=destination_with_extension,
        dry_run=False,
    )
    first.with_suffix('.png').touch()

    second = build_unique_batch_base_path(
        output_dir=temp_dir,
        stem="folder/name",
        output_format="png",
        destination_with_extension_func=destination_with_extension,
        dry_run=False,
    )

    assert "/" not in second.name
    assert second.name == "folder_name_resized_1"
