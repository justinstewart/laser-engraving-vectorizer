"""Generate labeled contact sheets for side-by-side image comparison."""

import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


def _get_font(size=20):
    try:
        return ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", size)
    except OSError:
        return ImageFont.load_default()


def make_contact_sheet(
    images: list[tuple[str, str | Path]],
    output_path: str | Path,
    max_width: int = 400,
    padding: int = 20,
    label_height: int = 40,
    bg_color: str = "#222222",
    label_color: str = "#ffffff",
):
    """Create a single-row labeled contact sheet from (label, image_path) tuples."""
    grid = make_contact_grid(
        rows=[("", images)],
        output_path=output_path,
        max_width=max_width,
        padding=padding,
        label_height=label_height,
        bg_color=bg_color,
        label_color=label_color,
    )
    return grid


def make_contact_grid(
    rows: list[tuple[str, list[tuple[str, str | Path]]]],
    output_path: str | Path,
    max_width: int = 300,
    padding: int = 15,
    label_height: int = 30,
    row_label_width: int = 180,
    bg_color: str = "#222222",
    label_color: str = "#ffffff",
):
    """Create a grid contact sheet. Rows are strategies, columns are levels.

    Args:
        rows: List of (row_label, [(col_label, image_path), ...]) tuples.
              Row label is the strategy name (e.g., "Saturation").
              Col labels are the level names (e.g., "20", "60", "100").
        output_path: Where to save the contact sheet.
        max_width: Max width per thumbnail.
        padding: Space between images and edges.
        label_height: Height reserved for column label text above each image.
        row_label_width: Width reserved for the row label on the left.
        bg_color: Background color.
        label_color: Label text color.
    """
    output_path = Path(output_path)
    font = _get_font(18)
    row_font = _get_font(16)

    # Load and resize all images
    loaded_rows = []
    max_cols = 0
    max_thumb_height = 0
    for row_label, cells in rows:
        thumbs = []
        for col_label, img_path in cells:
            img = Image.open(img_path).convert("RGB")
            ratio = max_width / img.width
            new_size = (max_width, int(img.height * ratio))
            img = img.resize(new_size, Image.LANCZOS)
            thumbs.append((col_label, img))
            max_thumb_height = max(max_thumb_height, img.height)
        loaded_rows.append((row_label, thumbs))
        max_cols = max(max_cols, len(thumbs))

    # Check if any row has a label — if not, skip the row label column
    has_row_labels = any(label for label, _ in loaded_rows)
    effective_row_label_width = row_label_width if has_row_labels else 0

    cell_height = label_height + max_thumb_height
    col_header_height = label_height if max_cols > 0 else 0

    sheet_width = padding + effective_row_label_width + max_cols * (max_width + padding)
    sheet_height = padding + col_header_height + len(loaded_rows) * (cell_height + padding)

    sheet = Image.new("RGB", (sheet_width, sheet_height), bg_color)
    draw = ImageDraw.Draw(sheet)

    # Draw column headers from the first row's labels
    if loaded_rows:
        _, first_row_thumbs = loaded_rows[0]
        for col_idx, (col_label, _) in enumerate(first_row_thumbs):
            if col_label:
                bbox = draw.textbbox((0, 0), col_label, font=font)
                text_w = bbox[2] - bbox[0]
                cx = padding + effective_row_label_width + col_idx * (max_width + padding)
                text_x = cx + (max_width - text_w) // 2
                text_y = padding + (label_height - (bbox[3] - bbox[1])) // 2
                draw.text((text_x, text_y), col_label, fill=label_color, font=font)

    # Draw each row
    for row_idx, (row_label, thumbs) in enumerate(loaded_rows):
        row_y = padding + col_header_height + row_idx * (cell_height + padding)

        # Draw row label centered vertically
        if row_label and has_row_labels:
            bbox = draw.textbbox((0, 0), row_label, font=row_font)
            text_h = bbox[3] - bbox[1]
            text_x = padding
            text_y = row_y + (cell_height - text_h) // 2
            draw.text((text_x, text_y), row_label, fill=label_color, font=row_font)

        # Draw thumbnails
        for col_idx, (_, thumb) in enumerate(thumbs):
            cx = padding + effective_row_label_width + col_idx * (max_width + padding)
            # Center thumbnail vertically within cell
            img_y = row_y + (cell_height - thumb.height) // 2
            img_x = cx + (max_width - thumb.width) // 2
            sheet.paste(thumb, (img_x, img_y))

    sheet.save(output_path)
    return output_path


if __name__ == "__main__":
    # CLI usage for single row:
    #   python contact_sheet.py output.png "Label1:path1.png" "Label2:path2.png"
    # CLI usage for grid:
    #   python contact_sheet.py output.png --grid "RowLabel|ColA:pathA.png|ColB:pathB.png" "Row2|ColA:pathA.png|ColB:pathB.png"
    if len(sys.argv) < 3:
        print("Usage: python contact_sheet.py output.png 'A:img1.png' 'B:img2.png' ...")
        print("  Grid: python contact_sheet.py output.png --grid 'Row|A:img1.png|B:img2.png' ...")
        sys.exit(1)

    output = sys.argv[1]

    if sys.argv[2] == "--grid":
        rows = []
        for arg in sys.argv[3:]:
            parts = arg.split("|")
            row_label = parts[0]
            cells = []
            for cell in parts[1:]:
                col_label, path = cell.split(":", 1)
                cells.append((col_label, path))
            rows.append((row_label, cells))
        make_contact_grid(rows, output)
    else:
        pairs = []
        for arg in sys.argv[2:]:
            label, path = arg.split(":", 1)
            pairs.append((label, path))
        make_contact_sheet(pairs, output)

    print(f"Saved: {output}")
