"""Render SVG files to PNG for preview/contact sheets."""

from pathlib import Path

import cairosvg
from PIL import Image
from io import BytesIO


def svg_to_png(svg_path: str | Path, png_path: str | Path, width: int = 800) -> Path:
    svg_path = Path(svg_path)
    png_path = Path(png_path)
    png_path.parent.mkdir(parents=True, exist_ok=True)

    # Render SVG to PNG bytes (transparent background)
    png_bytes = cairosvg.svg2png(url=str(svg_path), output_width=width)

    # Composite onto white background
    img = Image.open(BytesIO(png_bytes)).convert("RGBA")
    bg = Image.new("RGBA", img.size, (255, 255, 255, 255))
    bg.paste(img, mask=img)
    bg.convert("RGB").save(png_path)

    return png_path
