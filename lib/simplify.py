"""Simplify SVG paths to reduce node counts for laser engraving.

Approach: sample entire path into a dense polyline, apply Douglas-Peucker
to reduce points, then refit as a sequence of cubic Beziers.

BROKEN: the least-squares Bezier refit produces control points that overshoot
the original curve, causing visual artifacts (crossed lines, phantom shapes).
Kept here as a record of the failed approach. Don't use without fixing the
refit. The working alternative is input-mask downscaling before vectorization
(see CLAUDE.md).
"""

import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

import numpy as np
from rdp import rdp
from svgpathtools import CubicBezier, Line, Path as SvgPath, parse_path


def _sample_path(path, points_per_unit=0.5):
    """Sample an entire svgpathtools Path into a dense polyline.

    Returns list of complex-number points along the full path.
    """
    total_length = path.length()
    if total_length == 0:
        return [path.point(0)]

    n_points = max(int(total_length * points_per_unit), 100)
    return [path.point(t / n_points) for t in range(n_points + 1)]


def _fit_cubic(pts):
    """Fit a single cubic Bezier to a list of complex-number points."""
    coords = np.array([(p.real, p.imag) for p in pts])
    p0, p3 = coords[0], coords[-1]

    diffs = np.linalg.norm(np.diff(coords, axis=0), axis=1)
    total = diffs.sum()
    if total == 0 or len(coords) < 3:
        return Line(complex(*p0), complex(*p3))

    t = np.concatenate([[0], np.cumsum(diffs) / total])

    A = np.array([
        [3 * ti * (1 - ti) ** 2, 3 * ti ** 2 * (1 - ti)]
        for ti in t
    ])
    rhs = np.array([
        coords[i] - (1 - t[i]) ** 3 * p0 - t[i] ** 3 * p3
        for i in range(len(coords))
    ])
    result, _, _, _ = np.linalg.lstsq(A, rhs, rcond=None)
    p1, p2 = result

    return CubicBezier(complex(*p0), complex(*p1), complex(*p2), complex(*p3))


def simplify_path_d(d_string, epsilon=1.0):
    """Simplify an SVG path d-string, returning a new d-string.

    Samples the entire path into a polyline, simplifies with Douglas-Peucker,
    then refits cubic Beziers between surviving points.
    """
    path = parse_path(d_string)
    if len(path) == 0:
        return d_string

    # Check if path is closed
    is_closed = d_string.rstrip().upper().endswith("Z")

    # Sample the entire path as one polyline
    pts = _sample_path(path)
    coords = np.array([(p.real, p.imag) for p in pts])

    # Douglas-Peucker simplification
    reduced = rdp(coords, epsilon=epsilon)

    if len(reduced) < 2:
        return d_string

    # Refit cubic Beziers between consecutive reduced points
    reduced_pts = [complex(x, y) for x, y in reduced]
    segments = []

    for i in range(len(reduced_pts) - 1):
        p_start = reduced[i]
        p_end = reduced[i + 1]

        # Find the original sampled points in this span
        start_idx = np.argmin(np.linalg.norm(coords - p_start, axis=1))
        end_idx = np.argmin(np.linalg.norm(coords - p_end, axis=1))

        if end_idx <= start_idx:
            end_idx = start_idx + 1

        span = [complex(x, y) for x, y in coords[start_idx:end_idx + 1]]

        if len(span) < 2:
            continue
        elif len(span) == 2:
            segments.append(Line(span[0], span[-1]))
        else:
            segments.append(_fit_cubic(span))

    if not segments:
        return d_string

    result = SvgPath(*segments).d()
    if is_closed:
        result += " Z"

    return result


def count_nodes(d_string):
    """Count path commands (nodes) in an SVG d-string."""
    return len(re.findall(r'[MLCQSAZmlcqsaz]', d_string))


def simplify_svg(
    input_path: str | Path,
    output_path: str | Path,
    epsilon: float = 1.0,
    node_threshold: int = 500,
) -> tuple[Path, dict]:
    """Simplify paths in an SVG file that exceed the node threshold."""
    input_path = Path(input_path)
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    tree = ET.parse(input_path)
    root = tree.getroot()

    ns = ""
    if root.tag.startswith("{"):
        ns = root.tag.split("}")[0] + "}"

    stats = {"paths": []}

    for elem in root.iter(f"{ns}path"):
        d = elem.get("d", "")
        before = count_nodes(d)

        if before > node_threshold:
            new_d = simplify_path_d(d, epsilon=epsilon)
            after = count_nodes(new_d)
            elem.set("d", new_d)
            stats["paths"].append({"before": before, "after": after, "simplified": True})
        else:
            stats["paths"].append({"before": before, "after": before, "simplified": False})

    tree.write(output_path, xml_declaration=True, encoding="unicode")
    return output_path, stats


def generate_simplify_options(
    input_path: str | Path,
    output_dir: str | Path,
    epsilons: list[float] | None = None,
    node_threshold: int = 500,
) -> list[tuple[str, Path, dict]]:
    """Generate simplified SVGs at different tolerance levels."""
    input_path = Path(input_path)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    if epsilons is None:
        epsilons = [1.0, 2.0, 4.0, 8.0, 16.0]

    results = []
    for eps in epsilons:
        out_path = output_dir / f"04-simplified-eps{eps}.svg"
        _, stats = simplify_svg(input_path, out_path, epsilon=eps, node_threshold=node_threshold)

        max_after = max((p["after"] for p in stats["paths"]), default=0)
        label = f"ε={eps} (max {max_after})"

        results.append((label, out_path, stats))

    return results


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python simplify.py input.svg output_dir/")
        sys.exit(1)

    results = generate_simplify_options(sys.argv[1], sys.argv[2])
    for label, path, stats in results:
        print(f"{label}: {path}")
        for i, p in enumerate(stats["paths"]):
            status = "simplified" if p["simplified"] else "kept"
            print(f"  path {i}: {p['before']} -> {p['after']} ({status})")
