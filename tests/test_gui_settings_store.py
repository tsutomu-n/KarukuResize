from __future__ import annotations

import json
from pathlib import Path

from karuku_resizer.gui_settings_store import GuiSettingsStore, SCHEMA_VERSION, default_gui_settings


def test_load_returns_defaults_when_no_settings_file(tmp_path: Path) -> None:
    settings_path = tmp_path / "settings.json"
    store = GuiSettingsStore(settings_path=settings_path, legacy_paths=[])

    loaded = store.load()

    assert loaded == default_gui_settings()
    assert not settings_path.exists()


def test_save_and_load_roundtrip(tmp_path: Path) -> None:
    settings_path = tmp_path / "settings.json"
    store = GuiSettingsStore(settings_path=settings_path, legacy_paths=[])

    payload = default_gui_settings()
    payload["quality"] = "75"
    payload["output_format"] = "webp"
    payload["default_output_dir"] = "/tmp/out"
    payload["default_preset_id"] = "user-test-preset"
    store.save(payload)

    loaded = store.load()

    assert loaded["quality"] == "75"
    assert loaded["output_format"] == "webp"
    assert loaded["default_output_dir"] == "/tmp/out"
    assert loaded["default_preset_id"] == "user-test-preset"
    assert loaded["schema_version"] == SCHEMA_VERSION


def test_load_migrates_legacy_settings_file(tmp_path: Path) -> None:
    settings_path = tmp_path / "new" / "settings.json"
    legacy_path = tmp_path / "karuku_settings.json"
    legacy_data = {
        "quality": "65",
        "ui_mode": "pro",
        "default_output_dir": "/tmp/legacy",
    }
    legacy_path.write_text(json.dumps(legacy_data, ensure_ascii=False), encoding="utf-8")

    store = GuiSettingsStore(settings_path=settings_path, legacy_paths=[legacy_path])
    loaded = store.load()

    assert loaded["quality"] == "65"
    assert loaded["ui_mode"] == "pro"
    assert loaded["default_output_dir"] == "/tmp/legacy"
    assert loaded["schema_version"] == SCHEMA_VERSION
    assert settings_path.exists()

    migrated = json.loads(settings_path.read_text(encoding="utf-8"))
    assert migrated["quality"] == "65"
    assert migrated["ui_mode"] == "pro"
    assert migrated["default_output_dir"] == "/tmp/legacy"
    assert migrated["schema_version"] == SCHEMA_VERSION
