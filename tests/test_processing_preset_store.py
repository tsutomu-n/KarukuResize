from __future__ import annotations

import json
from pathlib import Path

from karuku_resizer.processing_preset_store import (
    ProcessingPreset,
    ProcessingPresetStore,
    builtin_processing_presets,
    default_processing_values,
)


def test_builtin_processing_presets_count_and_shape() -> None:
    presets = builtin_processing_presets()
    assert len(presets) == 5
    ids = {preset.preset_id for preset in presets}
    assert len(ids) == 5
    assert all(preset.is_builtin for preset in presets)
    assert all(preset.values.get("quality") for preset in presets)


def test_save_and_load_user_presets_roundtrip(tmp_path: Path) -> None:
    preset_path = tmp_path / "processing_presets.json"
    store = ProcessingPresetStore(preset_path=preset_path, legacy_paths=[])

    user = ProcessingPresetStore.new_user_preset(
        name="現場A",
        description="テスト用",
        values={
            **default_processing_values(),
            "mode": "width",
            "width_value": "1400",
            "quality": "88",
            "output_format": "webp",
        },
        existing_ids=[],
    )
    store.save_users([user])

    loaded = store.load()
    loaded_user = [p for p in loaded if not p.is_builtin]
    assert len(loaded_user) == 1
    assert loaded_user[0].name == "現場A"
    assert loaded_user[0].values["width_value"] == "1400"
    assert loaded_user[0].values["output_format"] == "webp"


def test_migrate_legacy_presets(tmp_path: Path) -> None:
    preset_path = tmp_path / "new" / "processing_presets.json"
    legacy_path = tmp_path / "presets.json"
    legacy_payload = {
        "旧プリセットA": {
            "description": "旧形式",
            "resize_mode": "percentage",
            "resize_value": 75,
            "output_format": "webp",
            "quality": 72,
            "webp_lossless": True,
            "preserve_metadata": False,
        }
    }
    legacy_path.write_text(json.dumps(legacy_payload, ensure_ascii=False), encoding="utf-8")

    store = ProcessingPresetStore(preset_path=preset_path, legacy_paths=[legacy_path])
    loaded = store.load()
    loaded_user = [p for p in loaded if not p.is_builtin]

    assert len(loaded_user) == 1
    user = loaded_user[0]
    assert user.name == "旧プリセットA"
    assert user.values["mode"] == "ratio"
    assert user.values["ratio_value"] == "75"
    assert user.values["output_format"] == "webp"
    assert user.values["quality"] == "72"
    assert user.values["webp_lossless"] is True
    assert user.values["exif_mode"] == "remove"
    assert preset_path.exists()
    assert legacy_path.with_suffix(".json.migrated.bak").exists()


def test_user_presets_sorted_by_last_used_then_created(tmp_path: Path) -> None:
    preset_path = tmp_path / "processing_presets.json"
    store = ProcessingPresetStore(preset_path=preset_path, legacy_paths=[])

    base_values = default_processing_values()
    user_presets = [
        ProcessingPreset(
            preset_id="user-unused-new",
            name="未使用(新)",
            description="",
            values=base_values.copy(),
            is_builtin=False,
            created_at="2026-01-02T10:00:00",
            updated_at="2026-01-02T10:00:00",
            last_used_at="",
        ),
        ProcessingPreset(
            preset_id="user-used-old",
            name="使用済(旧)",
            description="",
            values=base_values.copy(),
            is_builtin=False,
            created_at="2026-01-01T10:00:00",
            updated_at="2026-01-01T10:00:00",
            last_used_at="2026-02-01T08:00:00",
        ),
        ProcessingPreset(
            preset_id="user-unused-old",
            name="未使用(旧)",
            description="",
            values=base_values.copy(),
            is_builtin=False,
            created_at="2026-01-01T09:00:00",
            updated_at="2026-01-01T09:00:00",
            last_used_at="",
        ),
        ProcessingPreset(
            preset_id="user-used-new",
            name="使用済(新)",
            description="",
            values=base_values.copy(),
            is_builtin=False,
            created_at="2026-01-03T10:00:00",
            updated_at="2026-01-03T10:00:00",
            last_used_at="2026-02-03T08:00:00",
        ),
    ]
    store.save_users(user_presets)

    loaded = store.load()
    loaded_user_ids = [preset.preset_id for preset in loaded if not preset.is_builtin]

    assert loaded_user_ids == [
        "user-used-new",
        "user-used-old",
        "user-unused-old",
        "user-unused-new",
    ]
