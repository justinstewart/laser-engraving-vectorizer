# Engraving Pipeline

An AI-assisted workflow for converting customer raster logos into laser-ready SVGs. This is a proof of concept and is not currently expected to be valuable in a real engraving workflow

## What This Does

You give it a raster logo (PNG/JPG). It walks you through:

1. Removing the background
2. Choosing how to convert the logo to a binary mask (or line art for gradient logos)
3. Picking a vectorization that hits the laser-ready node budget

The output is a single-color SVG ready to import into LightBurn.

## How You Use It

This is a Claude Code project. You don't run a CLI tool — you have a conversation with Claude Code, and it runs the scripts on your behalf. At each decision point, it generates a labeled contact sheet image, opens it in Preview, and asks you to pick.

A typical session:

```
You: "Here's my logo: customer-logo.png"

Claude: "Running background removal..."
        [opens the result in Preview]
        "Does this look clean?"

You: "Yes"

Claude: [generates a 4x4 grid of segmentation strategies]
        "I've opened a comparison sheet. Each row is a different
         strategy, each column a threshold level. Which cell
         captures the right engrave/don't-engrave split?"

You: "Row 2 (Saturation), column 3"

Claude: [generates 5 vectorization options at different scales,
         with node counts shown]
        "Here are vectorization options. The 50% scale lands at
         515 nodes on the main path — slightly over the 500-node
         laser ceiling. 45% hits 499 nodes. Which do you want?"

You: "45%"

Claude: "Final SVG saved to output/customer/04-final.svg"
```

You stay in the loop for the judgment calls. The pipeline does the grunt work.

## Setup

Requires Python 3.12 and [uv](https://docs.astral.sh/uv/) for dependency management. macOS instructions:

```bash
# Install system dependencies
brew install cmake cairo

# Install Python dependencies
uv sync

# Add your fal.ai API key
echo "FAL_KEY=your-key-here" > .env
```

The pipeline uses [fal.ai](https://fal.ai) for AI-powered steps (background removal, edge detection). A fal.ai account is required.

## What's In The Box

```
examples/
  starbucks-final.svg       example output — finished Starbucks engraving
  firefox-final.svg         example output — finished Firefox engraving (line art)
  SUMMARY.md                node counts, file sizes, decisions for the examples
LASER-SPECS.md              what makes an SVG laser-ready (numbers + sources)
RESEARCH.md                 background research on AI vectorization tools
CLAUDE.md                   instructions to Claude Code on how to drive this
lib/                        the pipeline scripts
```

## What "Laser-Ready" Means

We target SVGs that import into LightBurn without manual cleanup:

| Criterion | Target | Fail |
|-----------|--------|------|
| Nodes per path | < 200 | > 500 |
| Path type | Spline/Bezier | Polylines |
| Color | Single | Multiple/gradients |
| Paths | Closed | Open |

The 500-node ceiling comes from GRBL controller buffer limits — past that, the laser stalls mid-path and burns the material. Full details in `LASER-SPECS.md`.

## What Works Well

- **Two-color or high-contrast logos** (like Starbucks): produces a clean filled-mask engraving. Tested at 499 nodes on the main path, well within laser-ready spec.
- **Gradient or multi-color logos** (like Firefox): produces a line-art engraving by detecting structural edges, then vectorizing them. Tested at 249 nodes max.
- **Iterating on judgment calls**: regenerate a tighter range of options whenever an initial pass doesn't have the right answer.

## What Doesn't (Yet)

- **Multi-layer depth engraving** for gradient logos. The pipeline can produce line art, but not regions assigned to different engrave powers. Color-based segmentation didn't separate shapes cleanly enough.
- **Photo / dithered engraving**. This is a vector pipeline. Photo engravings should go through LightBurn's image mode with Jarvis dithering instead.
- **Automated quality checks**. Node counts are reported per option, but there's no hard pass/fail gate — the operator decides.

## The Bigger Lesson

The most useful finding from this experiment wasn't about the vector pipeline — it was that **vector probably isn't the right output format at all**. If you can produce a clean binary mask from the input logo (which is what this pipeline does in step 3, before vectorization), you're better off engraving the raster mask directly than vectorizing it.

A clean black-and-white mask sent to LightBurn as a 1-bit raster has none of the problems we spent the rest of the pipeline solving:

- No node-count ceiling, no GRBL buffer stalls — the controller streams scanlines, not path segments.
- No vectorizer artifacts (overshooting Beziers, jagged polylines, fragmented contours).
- Pixel-accurate to the mask. What you see is what burns.
- Fast. No vtracer pass, no scale tuning, no node budgeting.

The vector workflow only earns its keep when you genuinely need vector output (resizable cut paths, scoring lines, layered power assignments). For pure engraving from a clean mask, raster wins.

The corollary: **the high-leverage problem is producing the clean mask, not vectorizing it.** That's where the AI tools (BiRefNet, PIDI edge detection) actually moved the needle. Step 4 of this pipeline is mostly compensating for choosing the wrong output format.

If you're starting a similar project, consider stopping at step 3 and engraving the mask as a raster.

## How It Was Built

This entire project was built conversationally with Claude Code (Opus 4.6) over two sessions. Most of the lib/ scripts started as one-line ideas in the conversation and got iterated into shape based on whether the output looked right at each step. The codebase is small (~500 lines of Python) and intentionally simple — one happy path, no abstractions until they earn their keep.

If you want to extend it, read `CLAUDE.md` first — it documents the conventions and the findings from building it (including approaches that didn't work and why).
