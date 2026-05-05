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
- **Firefox** (gradient-heavy, all high-saturation colors) — standard thresholding failed (saturation sees everything as colorful, luminance can't separate fox from globe). K-means color quantization also struggled. **Winning approach**: fal.ai PIDI edge detection → binary threshold at 120 → vtracer. Produces a line-art engraving that captures the structural shapes.

### Key insight: gradient logos are a different product

Gradient logos can't be meaningfully reduced to a single binary mask. The options are:
1. **Line art engraving** — edge detection to get outlines, vectorize as filled regions (what we built)
2. **Multi-layer depth engraving** — segment into regions, assign each to a different engrave power (not yet built — K-means didn't segment well enough, needs better region detection)
3. **Dithered raster engraving** — grayscale + Jarvis dithering in LightBurn, not a vector workflow at all

### Starbucks results

Pipeline: BiRefNet background removal → Luminance 140 threshold → vtracer spline mode at 45% scale → 499 nodes on main path. Final SVG: `examples/starbucks-final.svg`.

### Firefox results (line art)

Pipeline: BiRefNet background removal → fal.ai PIDI edge detection → binary threshold at 120 → vtracer spline mode at 100% scale → 3 paths, max 249 nodes. Final SVG: `examples/firefox-final.svg`.

### The biggest finding: raster probably beats vector here

The vector pipeline works, but the highest-leverage finding was that **vector is likely the wrong output format for engraving from a clean mask**. Once you have the binary mask from step 3, sending it to LightBurn as a 1-bit raster sidesteps everything steps 4–5 try to solve: no node-count ceiling, no GRBL buffer stalls, no vectorizer overshoot artifacts, no scale tuning. Scanline streaming is exactly what laser controllers want.

The vector path only matters when the output genuinely needs to be vector (resizable cut paths, scoring lines, per-region power layers). For pure engraving, the high-leverage problem is producing a clean mask — which is where the AI tools (BiRefNet, PIDI) actually moved the needle. Steps 4–5 are mostly compensating for the wrong format choice.

If extending this project, the first thing to try is stopping at step 3 and routing the mask straight to a raster engrave.

### Edge detection: PIDI > Adaptive > Canny

fal.ai's PIDI preprocessor (`fal-ai/image-preprocessors/pidi`) produces significantly cleaner, more connected edges than local OpenCV adaptive thresholding or Canny. Important: PIDI output is soft/grayscale — must threshold to binary before vectorizing. Threshold level matters: too high (180) loses fine interior lines, 120 preserves them.

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
  edge_detect.py      — fal.ai edge detection (HED, PIDI, Canny, TEED)
  segment.py          — K-means color quantization region segmentation (needs work)
output/               — intermediate and final outputs (gitignored)
  {logo_name}/        — per-logo working directory
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
