# Engraving Demo

Throwaway project. Proof of concept for an AI-assisted logo-to-engrave-mask pipeline. Built with Claude Code to validate the workflow before investing further.

## Research

- `RESEARCH.md` — the laser engraving workflow, AI vector tool landscape, fal.ai offerings, and why a focused masking pipeline is the right approach for this demo.
- `LASER-SPECS.md` — concrete SVG quality criteria for laser engraving. Key numbers: < 200 nodes/path target, > 500 nodes/path is a fail, prefer splines over polygons. Based on GRBL controller buffer limits and LightBurn community consensus.

## What This Is

A conversational pipeline driven through Claude Code. The operator gives me a logo and I walk them through each stage — removing the background, choosing a segmentation strategy, tuning vectorization — presenting options at each decision point and waiting for their call before moving on.

The "UI" is this conversation. The tools are Python scripts I invoke on the operator's behalf. The output is a single-color SVG ready for laser software.

## The Pipeline

Each step produces intermediate files in `output/{logo_name}/`. At decision points, I generate a contact sheet showing labeled options and open it in Preview for the operator to review.

1. **Input** — operator provides a raster logo (PNG/JPG)
2. **Background removal** — fal.ai BiRefNet (`fal-ai/birefnet/v2`). Show result, confirm it's clean. Note: interior white regions within the logo are expected and handled by thresholding.
3. **Segmentation** — present a grid of strategies (rows) x threshold levels (columns). Strategies: Luminance, Saturation, Adaptive, Edge (Canny). Operator picks the cell that best captures engrave vs don't-engrave. May need to zoom into a narrower range after first pass.
4. **Vectorization** — vtracer in spline mode with input downscaling to control node count. Present options at different scale percentages with node counts shown. Operator picks the scale that balances detail vs node budget (< 500 nodes/path).
5. **Output** — single-color SVG ready for LightBurn / laser software.

### What "laser-ready" means

See `LASER-SPECS.md` for full details. Key criteria:
- < 500 nodes per path (target < 200)
- Spline/Bezier curves, not polylines
- No double lines, closed paths, single color, no gradients

## Key Findings

### Input downscaling > post-processing simplification

We tried two approaches to reduce node counts:
1. **Post-processing** (`lib/simplify.py`) — sample paths, Douglas-Peucker, refit Beziers. **Failed.** The least-squares Bezier refit produces control points that overshoot, causing curves to cross and create visual artifacts. Do not use without fixing the refit algorithm.
2. **Input downscaling** — resize the binary mask before passing to vtracer. **Works well.** vtracer naturally produces fewer nodes from a smaller input. The operator picks a scale percentage that hits the node budget while preserving acceptable detail.

### Different logos need different segmentation strategies

- **Starbucks** (two-color, high-saturation green on white) — Saturation thresholding and Luminance both worked. Luminance 140 was selected.
- **Firefox** (gradient-heavy, all high-saturation colors) — untested. Saturation thresholding likely won't work since all regions are colorful. May need edge detection, AI-assisted segmentation (fal.ai Image2SVG), or a different approach entirely.

### Starbucks results

Pipeline: BiRefNet background removal → Luminance 140 threshold → vtracer spline mode at 45% scale → 499 nodes on main path. Final SVG: `output/starbucks/04-final.svg`.

## Stack

- **Python** with uv for dependency management
- **Pillow** — image processing, thresholding, contact sheet generation
- **OpenCV** — contour detection, morphological cleanup, segmentation strategies
- **vtracer** — bitmap-to-vector conversion (spline mode preferred)
- **cairosvg** — SVG-to-PNG rendering for contact sheet previews
- **fal.ai** — background removal (BiRefNet), potentially Image2SVG for hard cases
- **svgpathtools / rdp** — SVG path parsing and simplification (refit needs work)

## Project Structure

```
lib/
  contact_sheet.py    — single-row or grid contact sheets for HITL previews
  remove_background.py — fal.ai BiRefNet background removal
  threshold.py        — multi-strategy segmentation grid generator
  vectorize.py        — vtracer wrapper with detail presets
  simplify.py         — SVG path simplification (BROKEN — Bezier refit artifacts)
  svg_to_png.py       — render SVGs to PNG for previews (white background)
output/               — intermediate and final outputs (gitignored)
  {logo_name}/        — per-logo working directory
test-logo-*.png       — test input files
LASER-SPECS.md        — SVG quality criteria for laser engraving
RESEARCH.md           — full research context
```

## Presenting Options to the Operator

Use `lib/contact_sheet.py` for all decision points:
- **Single row** (`make_contact_sheet`) — for one dimension of options (e.g., scale levels)
- **Grid** (`make_contact_grid`) — for two dimensions (e.g., strategies x levels)

Label each option clearly with the parameter value and relevant metrics (e.g., node count). Open the contact sheet with `open` so it appears in Preview. Ask the operator which option to proceed with. Be ready to regenerate with a narrower range if they want to dial in.

## Conventions

- This is a demo. No tests, no CI, no deployment.
- Keep it simple. One happy path. Handle the common case, not every edge case.
- Commit working checkpoints so we can roll back if an approach doesn't pan out.
- Pipeline scripts live in `lib/` and are invoked via `uv run`.
- All intermediate outputs go to `output/` (gitignored).
- FAL_KEY is in `.env`, loaded via `python-dotenv` in every script that needs it.
