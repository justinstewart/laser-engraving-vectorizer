"""Segment a logo into distinct regions using color quantization.

Reduces gradient-heavy images to N discrete color regions, then extracts
each as a separate mask. Regions are sorted by area (largest first) and
rendered as grayscale levels for engrave-depth preview.
"""

import sys
from pathlib import Path

import cv2
import numpy as np
from PIL import Image


def quantize_regions(
    input_path: str | Path,
    n_clusters: int = 6,
    min_area_pct: float = 0.5,
) -> list[np.ndarray]:
    """Segment an image into distinct regions via K-means color quantization.

    Args:
        input_path: Path to input image (should have background removed).
        n_clusters: Number of color clusters.
        min_area_pct: Minimum region area as percentage of image area to keep.

    Returns:
        List of boolean masks (numpy arrays), sorted largest first.
    """
    img = Image.open(input_path).convert("RGBA")
    rgb = np.array(img.convert("RGB"))
    alpha = np.array(img.split()[3])

    # Only cluster foreground pixels
    fg_mask = alpha > 128
    fg_pixels = rgb[fg_mask].astype(np.float32)

    if len(fg_pixels) == 0:
        return []

    # K-means in Lab color space (better perceptual clustering)
    fg_lab = cv2.cvtColor(fg_pixels.reshape(1, -1, 3).astype(np.uint8), cv2.COLOR_RGB2Lab)
    fg_lab = fg_lab.reshape(-1, 3).astype(np.float32)

    criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 20, 1.0)
    _, labels, centers = cv2.kmeans(fg_lab, n_clusters, None, criteria, 10, cv2.KMEANS_PP_CENTERS)
    labels = labels.flatten()

    # Map labels back to full image
    full_labels = np.full(fg_mask.shape, -1, dtype=np.int32)
    full_labels[fg_mask] = labels

    # Extract connected components per color cluster
    image_area = fg_mask.sum()
    min_area = int(image_area * min_area_pct / 100)

    regions = []
    for cluster_id in range(n_clusters):
        cluster_mask = (full_labels == cluster_id).astype(np.uint8) * 255
        n_components, components = cv2.connectedComponents(cluster_mask)

        for comp_id in range(1, n_components):
            region_mask = (components == comp_id).astype(np.uint8) * 255
            area = int(region_mask.sum() / 255)
            if area >= min_area:
                regions.append((area, region_mask))

    # Sort by area, largest first
    regions.sort(key=lambda x: x[0], reverse=True)
    return [mask for _, mask in regions]


def render_layer_preview(
    regions: list[np.ndarray],
    image_size: tuple[int, int],
) -> Image.Image:
    """Render regions as a grayscale layer map.

    Largest region = darkest (deepest engrave), smallest = lightest.
    Each region gets an evenly spaced gray level.
    """
    h, w = image_size
    preview = np.full((h, w), 255, dtype=np.uint8)  # white background

    n = len(regions)
    for i, mask in enumerate(regions):
        # Evenly space gray levels from dark to light
        gray_level = int(40 + (180 * i / max(n - 1, 1)))
        preview[mask > 128] = gray_level

    return Image.fromarray(preview)


def generate_segment_options(
    input_path: str | Path,
    output_dir: str | Path,
    cluster_counts: list[int] | None = None,
) -> list[tuple[str, Path, int]]:
    """Generate segmentation previews at different cluster counts.

    Returns:
        List of (label, preview_path, region_count) tuples.
    """
    input_path = Path(input_path)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    if cluster_counts is None:
        cluster_counts = [3, 4, 5, 6, 8]

    img = Image.open(input_path).convert("RGBA")
    image_size = (img.height, img.width)

    results = []
    for n in cluster_counts:
        regions = quantize_regions(input_path, n_clusters=n)
        preview = render_layer_preview(regions, image_size)

        out_path = output_dir / f"02-segments-{n}colors.png"
        preview.save(out_path)

        label = f"{n} colors\n{len(regions)} regions"
        results.append((label, out_path, len(regions)))

    return results


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python segment.py input.png output_dir/")
        sys.exit(1)

    results = generate_segment_options(sys.argv[1], sys.argv[2])
    for label, path, count in results:
        print(f"{label}: {path}")
