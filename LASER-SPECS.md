# Laser Engraving SVG Specifications

What makes an SVG "laser-ready" — concrete numbers from LightBurn docs, GRBL internals, and community consensus.

## The Core Constraint: Controller Buffer

Standard GRBL controllers have a **2KB serial input buffer**. Each line segment in a path becomes a G-code move. When moves arrive faster than the buffer drains, the laser stalls mid-path and dwells on the material — leaving a burn mark.

Observed stutter thresholds on typical diode lasers with USB: ~110 mm/s fine, ~163 mm/s stutters. xTool caps USB-connected engraving at 105 mm/s for this reason. High node counts make it worse because they generate more G-code lines per second of travel.

## Pass/Fail Criteria

| Criterion | Target | Fail Threshold | Source |
|-----------|--------|----------------|--------|
| Nodes per path | < 200 | > 500 | VectoSolve; LightBurn forums |
| Path representation | Bezier curves (splines) | Polyline approximations | LightBurn curve tolerance docs |
| Minimum feature size | >= 1mm | < 0.5mm | CutLaserCut; community |
| Fill type | Filled paths | Stroked hairlines used as fills | Standard practice |
| Double lines | None | Any overlapping duplicate paths | Standard practice |
| Open paths | None (all closed) | Gaps or incomplete curves | Standard practice |

**No published hard limits exist for total path count or file size.** File size is a proxy for complexity; the real constraint is nodes-per-path and resulting G-code volume.

## Why Splines Over Polygons

LightBurn's curve tolerance setting (default: 0.05mm, roughly half a typical laser beam width) controls how it subdivides Bezier curves into line segments before sending to the controller. This means:

- **Spline/Bezier paths**: LightBurn receives the curve and resamples it at 0.05mm tolerance — efficiently.
- **Polygon/polyline paths**: LightBurn receives thousands of discrete line segments and must process each as a separate move.

A spline with 200 nodes describes the same shape as a polyline with 1,500+ nodes, but the controller handles it far better. **Always prefer spline mode over polygon mode.**

## LightBurn's Curve Tolerance ($12)

GRBL's arc segmentation setting (`$12`) defaults to 0.002mm, meaning it further subdivides any arc the controller receives. This is a second amplification point: a path with many short segments, when passed through arc fitting, can explode in move count.

At the 0.05mm default tolerance, output is already finer than most laser beam diameters (0.1–0.2mm for diode lasers). Lowering it buys nothing visible and adds controller load.

## Geometry Constraints (Cuts, Not Engraving)

These matter more for cutting than fill-engraving, but worth knowing:

- **Minimum gap between cut lines**: 0.5mm (closer and material burns away)
- **Minimum feature width**: ~1mm (thinner is fragile, may warp)
- **Kerf**: 0.1–0.4mm depending on material and laser

For engraving masks (laser on/off, not cutting), fine detail below ~0.5mm won't survive the laser pass regardless of SVG quality.

## What Doesn't Exist

To be explicit about gaps in available guidance:

- No official LightBurn node-count limit or file-size cap
- No published "nodes per inch" formula
- No LightBurn UI warning triggered by excessive complexity
- The 500-nodes-per-path ceiling is community-sourced (VectoSolve), not vendor-published

The physics behind the problem (buffer overflow → dwell → burn mark) is well-understood, but the community hasn't produced a rigorous per-inch-density benchmark.

## Sources

- [VectoSolve — Vector Files for Laser Cutting Guide](https://vectosolve.com/blog/vector-files-laser-cutting-guide)
- [LightBurn Docs — Settings/Preferences (Curve Tolerance)](https://docs.lightburnsoftware.com/latest/Reference/SettingsPreferences/)
- [LightBurn Docs — Optimize Selected Shapes](https://docs.lightburnsoftware.com/latest/Reference/OptimizeSelectedShapes/)
- [LightBurn Forum — Simplifying Nodes](https://forum.lightburnsoftware.com/t/simplifying-nodes/35112)
- [LightBurn Forum — GRBL Buffer Size and Stuttering](https://forum.lightburnsoftware.com/t/laser-stuttering-at-high-speed-ability-to-increase-grbl-buffer-size/87007)
- [LightBurn Feature Request — Reduce Nodes](https://lightburn.fider.io/posts/985/reduce-nodes)
- [CutLaserCut — Inkscape Drawing Guidelines](https://cutlasercut.com/drawing-resources/inkscape-drawing-guidelines/)
- [GRBL Settings — Arc Tolerance ($12)](https://github.com/gnea/grbl/blob/master/doc/markdown/settings.md)
- [ThinkLaser — Optimise Artwork for Lasers](https://thinklaser.com/news/optimise-artwork-for-lasers/)
