"""処理プリセットの保存・読込・旧形式移行を扱う。"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
import json
import os
from pathlib import Path
import re
from typing import Any, Iterable, Mapping, Optional

SCHEMA_VERSION = 1
_APP_DIR_NAME = "KarukuResize"
_PRESET_FILE_NAME = "processing_presets.json"
_LEGACY_PRESET_FILE_NAME = "presets.json"


def default_processing_values() -> dict[str, Any]:
    """処理系パラメータのデフォルト。"""
    return {
        "mode": "ratio",
        "ratio_value": "100",
        "width_value": "",
        "height_value": "",
        "quality": "85",
        "output_format": "auto",
        "webp_method": "6",
        "webp_lossless": False,
        "avif_speed": "6",
        "dry_run": False,
        "exif_mode": "keep",
        "remove_gps": False,
        "exif_artist": "",
        "exif_copyright": "",
        "exif_user_comment": "",
        "exif_datetime_original": "",
    }


def merge_processing_values(values: Optional[Mapping[str, Any]]) -> dict[str, Any]:
    merged = default_processing_values()
    if values:
        merged.update(dict(values))
    return merged


@dataclass
class ProcessingPreset:
    preset_id: str
    name: str
    description: str = ""
    values: dict[str, Any] = field(default_factory=default_processing_values)
    is_builtin: bool = False
    created_at: str = field(default_factory=lambda: datetime.now().isoformat(timespec="seconds"))
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat(timespec="seconds"))
    last_used_at: str = ""

    def to_dict(self) -> dict[str, Any]:
        payload = {
            "preset_id": self.preset_id,
            "name": self.name,
            "description": self.description,
            "values": merge_processing_values(self.values),
            "is_builtin": bool(self.is_builtin),
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "last_used_at": self.last_used_at,
        }
        return payload

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "ProcessingPreset":
        return cls(
            preset_id=str(data.get("preset_id", "")).strip(),
            name=str(data.get("name", "")).strip(),
            description=str(data.get("description", "")),
            values=merge_processing_values(data.get("values")),
            is_builtin=bool(data.get("is_builtin", False)),
            created_at=str(data.get("created_at", datetime.now().isoformat(timespec="seconds"))),
            updated_at=str(data.get("updated_at", datetime.now().isoformat(timespec="seconds"))),
            last_used_at=str(data.get("last_used_at", "")),
        )


def builtin_processing_presets() -> list[ProcessingPreset]:
    """組み込みプリセット。"""
    defaults = default_processing_values()
    return [
        ProcessingPreset(
            preset_id="builtin-standard-high",
            name="標準（品質重視）",
            description="長辺1920相当の高品質設定",
            values=merge_processing_values(
                {
                    **defaults,
                    "mode": "width",
                    "width_value": "1920",
                    "ratio_value": "100",
                    "quality": "90",
                    "output_format": "jpeg",
                }
            ),
            is_builtin=True,
        ),
        ProcessingPreset(
            preset_id="builtin-standard-light",
            name="標準（軽量）",
            description="長辺1280相当の軽量設定",
            values=merge_processing_values(
                {
                    **defaults,
                    "mode": "width",
                    "width_value": "1280",
                    "ratio_value": "100",
                    "quality": "75",
                    "output_format": "jpeg",
                }
            ),
            is_builtin=True,
        ),
        ProcessingPreset(
            preset_id="builtin-webp-high",
            name="WEBP（高品質）",
            description="WebP高品質・可逆オフ",
            values=merge_processing_values(
                {
                    **defaults,
                    "mode": "width",
                    "width_value": "1600",
                    "quality": "85",
                    "output_format": "webp",
                    "webp_method": "6",
                    "webp_lossless": False,
                }
            ),
            is_builtin=True,
        ),
        ProcessingPreset(
            preset_id="builtin-avif-compact",
            name="AVIF（省容量）",
            description="AVIFで容量優先",
            values=merge_processing_values(
                {
                    **defaults,
                    "mode": "width",
                    "width_value": "1600",
                    "quality": "80",
                    "output_format": "avif",
                    "avif_speed": "6",
                }
            ),
            is_builtin=True,
        ),
        ProcessingPreset(
            preset_id="builtin-remove-metadata",
            name="メタデータ削除",
            description="EXIFを削除して保存",
            values=merge_processing_values(
                {
                    **defaults,
                    "mode": "ratio",
                    "ratio_value": "100",
                    "quality": "85",
                    "output_format": "auto",
                    "exif_mode": "remove",
                    "remove_gps": False,
                }
            ),
            is_builtin=True,
        ),
    ]


class ProcessingPresetStore:
    """処理プリセットストア。"""

    def __init__(
        self,
        preset_path: Optional[Path] = None,
        legacy_paths: Optional[Iterable[Path]] = None,
    ) -> None:
        self.preset_path = preset_path or self._build_default_preset_path()
        if legacy_paths is None:
            self.legacy_paths = [self.preset_path.parent / _LEGACY_PRESET_FILE_NAME]
        else:
            self.legacy_paths = [Path(p) for p in legacy_paths]

    def load(self) -> list[ProcessingPreset]:
        builtins = builtin_processing_presets()
        users = self._load_user_presets_from_file()
        if users is None:
            users = self._migrate_legacy_presets()
            if users:
                self.save_users(users)
        users = _sort_user_presets(users)
        merged = builtins + users
        return merged

    def save_users(self, presets: Iterable[ProcessingPreset]) -> None:
        sorted_users = _sort_user_presets([preset for preset in presets if not preset.is_builtin])
        user_payload = [
            preset.to_dict() for preset in sorted_users if preset.preset_id
        ]
        payload = {
            "schema_version": SCHEMA_VERSION,
            "user_presets": user_payload,
        }
        self.preset_path.parent.mkdir(parents=True, exist_ok=True)
        tmp_path = self.preset_path.with_suffix(f"{self.preset_path.suffix}.tmp")
        with tmp_path.open("w", encoding="utf-8") as fh:
            json.dump(payload, fh, ensure_ascii=False, indent=2)
        tmp_path.replace(self.preset_path)

    @staticmethod
    def new_user_preset(
        name: str,
        description: str,
        values: Mapping[str, Any],
        existing_ids: Optional[Iterable[str]] = None,
    ) -> ProcessingPreset:
        now = datetime.now().isoformat(timespec="seconds")
        preset_id = _build_unique_user_preset_id(name=name, existing_ids=existing_ids or [])
        return ProcessingPreset(
            preset_id=preset_id,
            name=name.strip(),
            description=description.strip(),
            values=merge_processing_values(values),
            is_builtin=False,
            created_at=now,
            updated_at=now,
        )

    def _load_user_presets_from_file(self) -> Optional[list[ProcessingPreset]]:
        if not self.preset_path.exists():
            return None
        try:
            with self.preset_path.open("r", encoding="utf-8") as fh:
                payload = json.load(fh)
        except Exception:
            return []
        if not isinstance(payload, dict):
            return []
        raw_presets = payload.get("user_presets", [])
        if not isinstance(raw_presets, list):
            return []

        users: list[ProcessingPreset] = []
        for raw in raw_presets:
            if not isinstance(raw, dict):
                continue
            preset = ProcessingPreset.from_dict(raw)
            if not preset.preset_id or not preset.name:
                continue
            preset.is_builtin = False
            users.append(preset)
        return users

    def _migrate_legacy_presets(self) -> list[ProcessingPreset]:
        users: list[ProcessingPreset] = []
        for path in self.legacy_paths:
            if not path.exists():
                continue
            try:
                with path.open("r", encoding="utf-8") as fh:
                    payload = json.load(fh)
            except Exception:
                continue
            if not isinstance(payload, dict):
                continue

            for index, (name, raw) in enumerate(payload.items(), start=1):
                if not isinstance(raw, dict):
                    continue
                preset = _convert_legacy_preset(name=name, legacy=raw, index=index)
                users.append(preset)

            if users:
                backup_path = path.with_suffix(f"{path.suffix}.migrated.bak")
                try:
                    path.replace(backup_path)
                except OSError:
                    pass
                break

        return users

    @staticmethod
    def _build_default_preset_path() -> Path:
        if os.name == "nt":
            app_data = os.environ.get("APPDATA")
            if app_data:
                return Path(app_data) / _APP_DIR_NAME / _PRESET_FILE_NAME
            return Path.home() / ".karukuresize" / _PRESET_FILE_NAME

        config_home = os.environ.get("XDG_CONFIG_HOME")
        if config_home:
            return Path(config_home) / "karukuresize" / _PRESET_FILE_NAME
        return Path.home() / ".config" / "karukuresize" / _PRESET_FILE_NAME


def _convert_legacy_preset(name: str, legacy: Mapping[str, Any], index: int) -> ProcessingPreset:
    values = default_processing_values()

    resize_mode = str(legacy.get("resize_mode", "longest_side")).lower()
    resize_value = int(legacy.get("resize_value", 100) or 100)
    if resize_mode == "percentage":
        values["mode"] = "ratio"
        values["ratio_value"] = str(max(1, resize_value))
    elif resize_mode == "width":
        values["mode"] = "width"
        values["width_value"] = str(max(1, resize_value))
    elif resize_mode == "height":
        values["mode"] = "height"
        values["height_value"] = str(max(1, resize_value))
    elif resize_mode == "none":
        values["mode"] = "ratio"
        values["ratio_value"] = "100"
    else:
        values["mode"] = "width"
        values["width_value"] = str(max(1, resize_value))

    output_format = str(legacy.get("output_format", "original")).lower()
    if output_format in {"jpeg", "png", "webp", "avif"}:
        values["output_format"] = output_format
    else:
        values["output_format"] = "auto"

    values["quality"] = str(max(5, min(100, int(legacy.get("quality", 85) or 85))))
    values["webp_lossless"] = bool(legacy.get("webp_lossless", False))
    preserve_metadata = bool(legacy.get("preserve_metadata", True))
    values["exif_mode"] = "keep" if preserve_metadata else "remove"

    now = datetime.now().isoformat(timespec="seconds")
    preset_id = _build_unique_user_preset_id(
        name=name,
        existing_ids=[f"legacy-{index}"],
        prefix="migrated",
    )
    return ProcessingPreset(
        preset_id=preset_id,
        name=str(name).strip() or f"移行プリセット{index}",
        description=str(legacy.get("description", "")).strip(),
        values=values,
        is_builtin=False,
        created_at=now,
        updated_at=now,
    )


def _build_unique_user_preset_id(
    *,
    name: str,
    existing_ids: Iterable[str],
    prefix: str = "user",
) -> str:
    normalized = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")
    if not normalized:
        normalized = "preset"
    base = f"{prefix}-{normalized}"
    used = set(existing_ids)
    candidate = base
    counter = 2
    while candidate in used:
        candidate = f"{base}-{counter}"
        counter += 1
    return candidate


def _parse_iso_datetime(value: str) -> Optional[datetime]:
    text = str(value).strip()
    if not text:
        return None
    try:
        return datetime.fromisoformat(text)
    except ValueError:
        return None


def _sort_user_presets(presets: list[ProcessingPreset]) -> list[ProcessingPreset]:
    used: list[ProcessingPreset] = []
    unused: list[ProcessingPreset] = []
    for preset in presets:
        if str(preset.last_used_at).strip():
            used.append(preset)
        else:
            unused.append(preset)

    used.sort(
        key=lambda preset: _parse_iso_datetime(preset.last_used_at) or datetime.min,
        reverse=True,
    )
    unused.sort(
        key=lambda preset: _parse_iso_datetime(preset.created_at) or datetime.min,
    )
    return used + unused
