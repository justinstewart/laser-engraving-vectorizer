# Engraving Demo

Throwaway project. Proof of concept for an AI-assisted logo-to-engrave-mask pipeline. Built with Claude Code to validate the workflow before investing further.

## Research

See `RESEARCH.md` for the full research context — the laser engraving workflow, AI vector tool landscape, fal.ai offerings, and why a focused masking pipeline is the right approach for this demo.

## What This Is

A demo that takes a customer's logo (raster, messy, too many colors) and produces a clean, single-color vector mask suitable for laser engraving. Not a product. Not production code. Just enough to prove the pipeline works.

## The Pipeline

1. **Input** — raster logo (PNG/JPG), any quality
2. **Background removal** — segment the logo from its background
3. **Simplification** — collapse to binary (engrave / don't engrave)
4. **Contour detection** — extract clean edges from the mask
5. **Vectorization** — convert contours to minimal-node SVG paths
6. **Output** — single-color SVG ready for laser software (LightBurn, etc.)

## Stack

Python. Use whatever libraries get the job done fastest:
- Pillow / OpenCV for image processing
- rembg or similar for background removal
- potrace / vtracer or similar for bitmap-to-vector conversion
- fal.ai SDK if we need AI-powered steps (Image2SVG, Recraft, etc.)

## Test Files

`test-logo-starbucks.png` — Starbucks siren logo. Green and white, circular, with fine interior detail (hair, crown, stars). Good test case because it requires collapsing to a single-color mask while preserving delicate line work. Essentially already two-color — thresholding is straightforward.

`test-logo-firefox.png` — Firefox logo. Gradient-heavy: orange-to-yellow fox wrapping a purple-to-blue globe, pink-to-orange base. No hard edges between regions — all continuous color transitions. The hard test case: the pipeline must decide where boundaries fall when colors blend into each other rather than separate cleanly.

## Conventions

- This is a demo. No tests, no CI, no deployment.
- Scripts over frameworks. CLI scripts that take an input image and produce an output SVG.
- Keep it simple. One happy path. Handle the common case, not every edge case.
- Commit working checkpoints so we can roll back if an approach doesn't pan out.
