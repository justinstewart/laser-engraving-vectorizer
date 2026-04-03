"""AI-powered edge detection using fal.ai preprocessors.

HED (Holistically-Nested Edge Detection) produces cleaner, more connected
edge maps than traditional Canny/adaptive thresholding — better for
finding structural boundaries in gradient-heavy logos.
"""

import sys
from pathlib import Path

import fal_client
import httpx
from dotenv import load_dotenv

load_dotenv()


def detect_edges(
    input_path: str | Path,
    output_path: str | Path,
    method: str = "hed",
) -> Path:
    """Run fal.ai edge detection on an image.

    Args:
        input_path: Source image.
        output_path: Where to save the edge map.
        method: Preprocessor to use — "hed", "pidi", "canny", "teed".
    """
    input_path = Path(input_path)
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    url = fal_client.upload_file(input_path)

    result = fal_client.subscribe(
        f"fal-ai/image-preprocessors/{method}",
        arguments={"image_url": url},
    )

    image_url = result["image"]["url"]
    response = httpx.get(image_url)
    output_path.write_bytes(response.content)

    return output_path


def generate_edge_options(
    input_path: str | Path,
    output_dir: str | Path,
    methods: list[str] | None = None,
) -> list[tuple[str, Path]]:
    """Generate edge maps using multiple methods for comparison."""
    input_path = Path(input_path)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    if methods is None:
        methods = ["hed", "pidi", "canny", "teed"]

    results = []
    for method in methods:
        out_path = output_dir / f"02-edges-{method}.png"
        detect_edges(input_path, out_path, method)
        results.append((method.upper(), out_path))

    return results


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python edge_detect.py input.png output_dir/")
        sys.exit(1)

    results = generate_edge_options(sys.argv[1], sys.argv[2])
    for label, path in results:
        print(f"{label}: {path}")
