# Engraving Demo

Throwaway project. Proof of concept for an AI-assisted logo-to-engrave-mask pipeline. Built with Claude Code to validate the workflow before investing further.

## Research

See `RESEARCH.md` for the full research context — the laser engraving workflow, AI vector tool landscape, fal.ai offerings, and why a focused masking pipeline is the right approach for this demo.

## What This Is

A conversational pipeline driven through Claude Code. The operator gives me a logo and I walk them through each stage — removing the background, choosing a threshold, cleaning up contours, vectorizing — presenting options at each decision point and waiting for their call before moving on.

The "UI" is this conversation. The tools are Python scripts I invoke on the operator's behalf. The output is a single-color SVG ready for laser software.

## The Pipeline

Each step produces intermediate files in `output/{logo_name}/`. At decision points, I generate a contact sheet showing labeled options (A, B, C, etc.), open it for the operator to review, and ask them to pick.

1. **Input** — operator provides a raster logo (PNG/JPG)
2. **Background removal** — segment the logo from its background. Show result, confirm it's clean.
3. **Simplification** — generate multiple threshold options (binary masks at different levels). Present contact sheet. Operator picks.
4. **Contour detection** — extract clean edges from the chosen mask. Show result.
5. **Vectorization** — convert to SVG with different node density / detail settings. Present contact sheet of options. Operator picks.
6. **Output** — single-color SVG ready for LightBurn / laser software.

### What "laser-ready" means

- Minimal nodes — excess nodes cause laser stalling and burn marks
- No double lines — laser hits the same path twice
- Closed paths — no gaps or incomplete curves
- Single color, no gradients — flat geometry only
- Clean enough to import into LightBurn without manual cleanup

## Stack

- **Python** with uv for dependency management
- **Pillow** — image processing, thresholding, contact sheet generation
- **OpenCV** — contour detection, morphological cleanup
- **vtracer** — bitmap-to-vector conversion
- **fal.ai** — AI-powered steps (background removal, Image2SVG, etc.)

## Project Structure

```
lib/              — reusable pipeline utilities
  contact_sheet.py  — side-by-side image comparison sheets
output/           — intermediate and final outputs (gitignored)
  {logo_name}/    — per-logo working directory
test-logo-*.png   — test input files
```

## Presenting Options to the Operator

When a pipeline step has tunable parameters, generate multiple variants and present them using `lib/contact_sheet.py`. Label each option clearly (e.g., "A — Threshold 100", "B — Threshold 140", "C — Threshold 180"). Open the contact sheet with `open` so it appears in Preview. Ask the operator which option to proceed with.

## Conventions

- This is a demo. No tests, no CI, no deployment.
- Keep it simple. One happy path. Handle the common case, not every edge case.
- Commit working checkpoints so we can roll back if an approach doesn't pan out.
- Pipeline steps are Python scripts in `lib/` that Claude Code invokes via `uv run`.
- All intermediate outputs go to `output/` (gitignored).
