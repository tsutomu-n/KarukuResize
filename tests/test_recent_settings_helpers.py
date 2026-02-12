from __future__ import annotations

from karuku_resizer.gui_app import RECENT_SETTINGS_MAX, ResizeApp


def test_recent_setting_label_from_values_ratio() -> None:
    label = ResizeApp._recent_setting_label_from_values(
        {
            "mode": "ratio",
            "ratio_value": "80",
            "output_format": "webp",
            "quality": "90",
        }
    )
    assert label == "比率80%/WEBP/Q90"


def test_normalize_recent_settings_entries_dedupes_and_limits() -> None:
    sample_values = {
        "mode": "width",
        "width_value": "1200",
        "output_format": "jpeg",
        "quality": "85",
    }
    duplicate_values = {
        "mode": "height",
        "height_value": "900",
        "output_format": "png",
        "quality": "80",
    }
    duplicate_fingerprint = ResizeApp._recent_settings_fingerprint(duplicate_values)

    raw = [{"values": sample_values}]
    raw.append({"values": duplicate_values, "fingerprint": duplicate_fingerprint})
    raw.append({"values": duplicate_values, "fingerprint": duplicate_fingerprint, "label": "duplicate"})
    for idx in range(10):
        raw.append(
            {
                "values": {
                    "mode": "ratio",
                    "ratio_value": str(50 + idx),
                    "output_format": "auto",
                    "quality": "85",
                }
            }
        )

    normalized = ResizeApp._normalize_recent_settings_entries(raw)
    assert len(normalized) == RECENT_SETTINGS_MAX
    fingerprints = [entry["fingerprint"] for entry in normalized]
    assert len(fingerprints) == len(set(fingerprints))


def test_normalize_recent_settings_entries_ignores_invalid_rows() -> None:
    raw = [
        {"values": "not-a-dict"},
        {"fingerprint": "x"},
        "string-row",
        123,
    ]
    assert ResizeApp._normalize_recent_settings_entries(raw) == []
