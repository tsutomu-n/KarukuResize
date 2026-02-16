"""GUI設定の永続化ストア。"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Iterable, Mapping, Optional

SCHEMA_VERSION = 1
_SETTINGS_FILENAME = "settings.json"
_LEGACY_FILENAME = "karuku_settings.json"
_APP_DIR_NAME = "KarukuResize"


def default_gui_settings() -> dict[str, Any]:
    """GUI設定のデフォルト値を返す。"""
    return {
        "schema_version": SCHEMA_VERSION,
        "mode": "ratio",
        "ui_mode": "simple",
        "appearance_mode": "system",
        "ratio_value": "100",
        "width_value": "",
        "height_value": "",
        "quality": "85",
        "output_format": "auto",
        "webp_method": "6",
        "webp_lossless": False,
        "avif_speed": "6",
        "dry_run": False,
        "verbose_logging": False,
        "show_tooltips": True,
        "ui_scale_mode": "normal",
        "exif_mode": "keep",
        "remove_gps": False,
        "exif_artist": "",
        "exif_copyright": "",
        "exif_user_comment": "",
        "exif_datetime_original": "",
        "details_expanded": False,
        "metadata_panel_expanded": False,
        "window_geometry": "1200x800",
        "zoom_preference": "画面に合わせる",
        "last_input_dir": "",
        "last_output_dir": "",
        "default_output_dir": "",
        "default_preset_id": "",
        "pro_input_mode": "recursive",
        "recent_processing_settings": [],
    }


class GuiSettingsStore:
    """GUI設定のロード/保存を行う。"""

    def __init__(
        self,
        settings_path: Optional[Path] = None,
        legacy_paths: Optional[Iterable[Path]] = None,
    ) -> None:
        self.settings_path = settings_path or self._build_default_settings_path()
        if legacy_paths is None:
            self.legacy_paths = [Path.cwd() / _LEGACY_FILENAME]
        else:
            self.legacy_paths = list(legacy_paths)

    def load(self) -> dict[str, Any]:
        """設定を読み込む。必要なら旧設定ファイルから移行する。"""
        defaults = default_gui_settings()

        loaded_current = self._read_json(self.settings_path)
        if loaded_current is not None:
            defaults.update(loaded_current)
            defaults["schema_version"] = SCHEMA_VERSION
            return defaults

        for legacy_path in self.legacy_paths:
            loaded_legacy = self._read_json(legacy_path)
            if loaded_legacy is None:
                continue
            defaults.update(loaded_legacy)
            defaults["schema_version"] = SCHEMA_VERSION
            self.save(defaults)
            return defaults

        return defaults

    def save(self, settings: Mapping[str, Any]) -> None:
        """設定を保存する。"""
        payload = default_gui_settings()
        payload.update(dict(settings))
        payload["schema_version"] = SCHEMA_VERSION

        self.settings_path.parent.mkdir(parents=True, exist_ok=True)
        tmp_path = self.settings_path.with_suffix(f"{self.settings_path.suffix}.tmp")
        with tmp_path.open("w", encoding="utf-8") as fh:
            json.dump(payload, fh, ensure_ascii=False, indent=2)
        tmp_path.replace(self.settings_path)

    @staticmethod
    def _read_json(path: Path) -> Optional[dict[str, Any]]:
        if not path.exists():
            return None
        try:
            with path.open("r", encoding="utf-8") as fh:
                data = json.load(fh)
        except Exception:
            return None
        if not isinstance(data, dict):
            return None
        return data

    @staticmethod
    def _build_default_settings_path() -> Path:
        if os.name == "nt":
            app_data = os.environ.get("APPDATA")
            if app_data:
                return Path(app_data) / _APP_DIR_NAME / _SETTINGS_FILENAME
            return Path.home() / ".karukuresize" / _SETTINGS_FILENAME

        config_home = os.environ.get("XDG_CONFIG_HOME")
        if config_home:
            return Path(config_home) / "karukuresize" / _SETTINGS_FILENAME
        return Path.home() / ".config" / "karukuresize" / _SETTINGS_FILENAME
