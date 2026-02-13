#!/usr/bin/env python3
"""Lucide SVGアイコンからダーク/ライト用PNGを生成するスクリプト。

Usage:
    python scripts/generate_icon_pngs.py

開発依存: cairosvg が必要 (pip install cairosvg)
生成されたPNGは assets/icons/ にコミットし、ランタイムではcairosvg不要。
"""
from __future__ import annotations

import re
from pathlib import Path

import cairosvg

ICONS_DIR = Path(__file__).resolve().parent.parent / "assets" / "icons"
SVG_DIR = ICONS_DIR / "svg"
SIZES = [16, 20, 24, 32]  # 1x and 2x for 16px and 20px buttons

# stroke colors for dark and light themes
THEMES = {
    "dark": "#e8eef5",   # --t1 from ui-v2-mockup
    "light": "#1a1a2e",  # dark text for light theme
}


def generate_pngs() -> None:
    svg_files = sorted(SVG_DIR.glob("*.svg"))
    if not svg_files:
        print(f"No SVG files found in {SVG_DIR}")
        return

    for theme_name, stroke_color in THEMES.items():
        theme_dir = ICONS_DIR / theme_name
        theme_dir.mkdir(parents=True, exist_ok=True)

        for svg_path in svg_files:
            svg_content = svg_path.read_text(encoding="utf-8")
            # Replace stroke="currentColor" with the theme color
            themed_svg = svg_content.replace('stroke="currentColor"', f'stroke="{stroke_color}"')

            for size in SIZES:
                # Scale the SVG to the target size
                sized_svg = re.sub(
                    r'width="24"',
                    f'width="{size}"',
                    themed_svg,
                )
                sized_svg = re.sub(
                    r'height="24"',
                    f'height="{size}"',
                    sized_svg,
                )

                out_name = f"{svg_path.stem}_{size}.png"
                out_path = theme_dir / out_name

                cairosvg.svg2png(
                    bytestring=sized_svg.encode("utf-8"),
                    write_to=str(out_path),
                    output_width=size,
                    output_height=size,
                )

    total = len(svg_files) * len(SIZES) * len(THEMES)
    print(f"Generated {total} PNG icons in {ICONS_DIR}")
    for theme_name in THEMES:
        theme_dir = ICONS_DIR / theme_name
        files = sorted(theme_dir.glob("*.png"))
        print(f"  {theme_name}/: {len(files)} files")
        for f in files:
            print(f"    {f.name} ({f.stat().st_size} bytes)")


if __name__ == "__main__":
    generate_pngs()
