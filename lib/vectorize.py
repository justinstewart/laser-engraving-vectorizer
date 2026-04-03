"""Convert a binary mask to SVG using vtracer with varying detail levels."""

import subprocess
import sys
from pathlib import Path

import vtracer


# Presets from loose (fewer nodes) to tight (more detail)
PRESETS = {
    "Minimal": {
        "color_precision": 1,
        "filter_speckle": 8,
        "corner_threshold": 120,
        "length_threshold": 10.0,
        "splice_threshold": 90,
        "mode": "polygon",
    },
    "Low": {
        "color_precision": 1,
        "filter_speckle": 5,
        "corner_threshold": 90,
        "length_threshold": 6.0,
        "splice_threshold": 60,
        "mode": "polygon",
    },
    "Medium": {
        "color_precision": 1,
        "filter_speckle": 3,
        "corner_threshold": 60,
        "length_threshold": 4.0,
        "splice_threshold": 45,
        "mode": "spline",
    },
    "High": {
        "color_precision": 1,
        "filter_speckle": 2,
        "corner_threshold": 45,
        "length_threshold": 2.5,
        "splice_threshold": 30,
        "mode": "spline",
    },
    "Maximum": {
        "color_precision": 1,
        "filter_speckle": 1,
        "corner_threshold": 30,
        "length_threshold": 1.0,
        "splice_threshold": 20,
        "mode": "spline",
    },
}


def vectorize(
    input_path: str | Path,
    output_path: str | Path,
    preset_name: str = "Medium",
) -> Path:
    input_path = Path(input_path)
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    preset = PRESETS[preset_name]

    vtracer.convert_image_to_svg_py(
        image_path=str(input_path),
        out_path=str(output_path),
        colormode="binary",
        color_precision=preset["color_precision"],
        filter_speckle=preset["filter_speckle"],
        corner_threshold=preset["corner_threshold"],
        length_threshold=preset["length_threshold"],
        splice_threshold=preset["splice_threshold"],
        mode=preset["mode"],
    )

    return output_path


def generate_vectorize_options(
    input_path: str | Path,
    output_dir: str | Path,
    presets: list[str] | None = None,
) -> list[tuple[str, Path]]:
    input_path = Path(input_path)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    if presets is None:
        presets = list(PRESETS.keys())

    results = []
    for name in presets:
        out_path = output_dir / f"03-vector-{name.lower()}.svg"
        vectorize(input_path, out_path, name)
        results.append((name, out_path))

    return results


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python vectorize.py input.png output_dir/")
        sys.exit(1)

    results = generate_vectorize_options(sys.argv[1], sys.argv[2])
    for name, path in results:
        print(f"{name}: {path}")
