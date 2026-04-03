"""Generate labeled contact sheets for side-by-side image comparison."""

import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


def make_contact_sheet(
    images: list[tuple[str, str | Path]],
    output_path: str | Path,
    max_width: int = 400,
    padding: int = 20,
    label_height: int = 40,
    bg_color: str = "#222222",
    label_color: str = "#ffffff",
):
    """Create a labeled contact sheet from a list of (label, image_path) tuples.

    Args:
        images: List of (label, image_path) tuples. Labels like "A", "B", "C".
        output_path: Where to save the contact sheet.
        max_width: Max width per thumbnail.
        padding: Space between images and edges.
        label_height: Height reserved for the label text above each image.
        bg_color: Background color.
        label_color: Label text color.
    """
    thumbnails = []
    for label, img_path in images:
        img = Image.open(img_path)
        # Scale to fit max_width, preserving aspect ratio
        ratio = max_width / img.width
        new_size = (max_width, int(img.height * ratio))
        img = img.resize(new_size, Image.LANCZOS)
        thumbnails.append((label, img))

    # Calculate sheet dimensions
    max_thumb_height = max(img.height for _, img in thumbnails)
    cell_height = label_height + max_thumb_height
    cols = len(thumbnails)
    sheet_width = padding + cols * (max_width + padding)
    sheet_height = padding + cell_height + padding

    sheet = Image.new("RGB", (sheet_width, sheet_height), bg_color)
    draw = ImageDraw.Draw(sheet)

    # Try to get a reasonable font
    try:
        font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 20)
    except OSError:
        font = ImageFont.load_default()

    x = padding
    for label, thumb in thumbnails:
        # Draw label centered above thumbnail
        bbox = draw.textbbox((0, 0), label, font=font)
        text_width = bbox[2] - bbox[0]
        text_x = x + (max_width - text_width) // 2
        text_y = padding + (label_height - (bbox[3] - bbox[1])) // 2
        draw.text((text_x, text_y), label, fill=label_color, font=font)

        # Paste thumbnail below label, centered if narrower than max_width
        img_x = x + (max_width - thumb.width) // 2
        img_y = padding + label_height
        sheet.paste(thumb, (img_x, img_y))

        x += max_width + padding

    sheet.save(output_path)
    return output_path


if __name__ == "__main__":
    # CLI usage: python contact_sheet.py output.png "Label1:path1.png" "Label2:path2.png" ...
    if len(sys.argv) < 3:
        print("Usage: python contact_sheet.py output.png 'A:image1.png' 'B:image2.png' ...")
        sys.exit(1)

    output = sys.argv[1]
    pairs = []
    for arg in sys.argv[2:]:
        label, path = arg.split(":", 1)
        pairs.append((label, path))

    make_contact_sheet(pairs, output)
    print(f"Saved: {output}")
