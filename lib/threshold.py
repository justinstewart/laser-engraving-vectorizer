"""Generate binary mask options across multiple segmentation strategies and levels.

Strategies:
  - Luminance: threshold on grayscale brightness
  - Saturation: threshold on color intensity (HSV S channel)
  - Adaptive: OpenCV locally-varying threshold (no manual level needed)
  - Edge (Canny): outline detection rather than filled regions
"""

import sys
from pathlib import Path

import cv2
import numpy as np
from PIL import Image


def _pil_to_cv(img: Image.Image) -> np.ndarray:
    return cv2.cvtColor(np.array(img.convert("RGB")), cv2.COLOR_RGB2BGR)


def _mask_with_alpha(mask: np.ndarray, alpha: np.ndarray) -> np.ndarray:
    """Zero out mask pixels where alpha is transparent."""
    mask[alpha < 128] = 255  # white = don't engrave
    return mask


def luminance_threshold(img: Image.Image, alpha: np.ndarray, level: int) -> Image.Image:
    gray = cv2.cvtColor(_pil_to_cv(img), cv2.COLOR_BGR2GRAY)
    _, mask = cv2.threshold(gray, level, 255, cv2.THRESH_BINARY)
    mask = _mask_with_alpha(mask, alpha)
    return Image.fromarray(mask)


def saturation_threshold(img: Image.Image, alpha: np.ndarray, level: int) -> Image.Image:
    hsv = cv2.cvtColor(_pil_to_cv(img), cv2.COLOR_BGR2HSV)
    sat = hsv[:, :, 1]
    # High saturation = engrave (black), low saturation = don't engrave (white)
    mask = np.where(sat >= level, 0, 255).astype(np.uint8)
    mask = _mask_with_alpha(mask, alpha)
    return Image.fromarray(mask)


def adaptive_threshold(img: Image.Image, alpha: np.ndarray, block_size: int) -> Image.Image:
    gray = cv2.cvtColor(_pil_to_cv(img), cv2.COLOR_BGR2GRAY)
    # block_size must be odd
    if block_size % 2 == 0:
        block_size += 1
    mask = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, block_size, 2)
    mask = _mask_with_alpha(mask, alpha)
    return Image.fromarray(mask)


def edge_threshold(img: Image.Image, alpha: np.ndarray, sensitivity: int) -> Image.Image:
    gray = cv2.cvtColor(_pil_to_cv(img), cv2.COLOR_BGR2GRAY)
    # sensitivity controls Canny thresholds — lower = more edges
    low = sensitivity
    high = sensitivity * 2
    edges = cv2.Canny(gray, low, high)
    # Invert: edges become black (engrave), rest white
    mask = 255 - edges
    mask = _mask_with_alpha(mask, alpha)
    return Image.fromarray(mask)


STRATEGIES = {
    "Luminance": {
        "fn": luminance_threshold,
        "default_levels": [60, 100, 140, 180],
        "level_label": lambda l: str(l),
    },
    "Saturation": {
        "fn": saturation_threshold,
        "default_levels": [20, 50, 80, 120],
        "level_label": lambda l: str(l),
    },
    "Adaptive": {
        "fn": adaptive_threshold,
        "default_levels": [11, 31, 51, 71],
        "level_label": lambda l: f"block {l}",
    },
    "Edge (Canny)": {
        "fn": edge_threshold,
        "default_levels": [30, 60, 100, 150],
        "level_label": lambda l: str(l),
    },
}


def generate_threshold_grid(
    input_path: str | Path,
    output_dir: str | Path,
    strategies: list[str] | None = None,
) -> list[tuple[str, list[tuple[str, Path]]]]:
    """Generate masks for all strategies and levels.

    Returns rows for contact_sheet.make_contact_grid:
        [(strategy_name, [(level_label, image_path), ...]), ...]
    """
    input_path = Path(input_path)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    img = Image.open(input_path).convert("RGBA")
    alpha = np.array(img.split()[3])

    if strategies is None:
        strategies = list(STRATEGIES.keys())

    rows = []
    for strategy_name in strategies:
        s = STRATEGIES[strategy_name]
        cells = []
        for level in s["default_levels"]:
            mask = s["fn"](img, alpha, level)
            label = s["level_label"](level)
            safe_name = strategy_name.lower().replace(" ", "_").replace("(", "").replace(")", "")
            out_path = output_dir / f"02-{safe_name}-{level}.png"
            mask.save(out_path)
            cells.append((label, out_path))
        rows.append((strategy_name, cells))

    return rows


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python threshold.py input.png output_dir/")
        sys.exit(1)

    rows = generate_threshold_grid(sys.argv[1], sys.argv[2])
    for strategy, cells in rows:
        for label, path in cells:
            print(f"{strategy} [{label}]: {path}")
