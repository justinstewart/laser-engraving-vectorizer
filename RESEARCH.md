# Research: AI-Assisted Vector Graphics for Laser Engraving

## The Problem

Laser engraving shops spend 40-50% of design time on vector file preparation — primarily converting customer-supplied raster logos into clean, machine-ready vectors. The actual engraving is fast. The bottleneck is design cleanup.

## Key Insight

Most laser engraving work is binary. The laser is on or off. A complex multi-color logo needs to be reduced to a single-color mask with clean contours. This is fundamentally a contour detection / masking problem, not a generative art problem.

The pipeline is: **complex raster logo -> binary mask -> clean vector contours**

## Laser Engraving Technical Requirements

### What makes a "good" vector for engraving

- Minimal nodes — excess nodes cause laser stalling and burn marks
- No double lines — common vectorization artifact, laser hits the same path twice
- Closed paths — no gaps or incomplete curves
- Stroke/fill discipline — hairline strokes (0.001") for cuts, fills for engraving areas
- RGB color mapping — colors define operations (cut, engrave, score)
- No gradients or textures — flat, clean geometry only

### Software stack

- **LightBurn** — industry standard laser control software
- **Design tools** — Adobe Illustrator, CorelDRAW, Inkscape
- **File formats** — SVG, DXF, AI, EPS accepted by laser software

### Common design categories

- Monograms and text layouts
- Logo vectorization (the biggest bottleneck)
- Decorative borders and flourishes
- Photo engraving (raster mode with dithering — separate workflow)

## AI Vector Generation Landscape (April 2026)

### fal.ai offerings (our preferred platform)

| Model | Purpose | Cost | Notes |
|---|---|---|---|
| Recraft V4 Vector | Text-to-SVG | $0.08/image | Native vector paths, not traced raster |
| Recraft V4 Pro Vector | Premium text-to-SVG | $0.30/image | Better composition and detail |
| Image2SVG | Raster-to-vector | $0.005/image | Customizable: color/binary, spline/polygon, detail levels |
| StarVector | AI vectorization | $0.10/megapixel | CVPR 2025, academic origin |
| VecGlypher | Font/glyph SVG generation | $0.005/image | Good for typography work |
| Recraft V3 styles | Style presets | — | Has explicit `engraving` and `line_art` style params |

### Other notable tools

- **Vectorizer.AI** — best raster-to-vector (8.8/10 quality), supports DXF export, $9.99-$139.99/month
- **Vector Magic** — high accuracy, $295 one-time desktop license
- **VectorWitch** — specifically targets laser engraving, zero duplicate lines
- **LayerTracer** (2025 research) — 27 seconds vs 95 min for SVGDreamer, ~35 clean paths vs 128-512
- **Chat2SVG** (CVPR 2025) — LLM + diffusion hybrid, natural language SVG editing

### Why current tools underwhelm engravers

1. **Bloated SVG code** — 45% redundant data average, 6+ decimal places, fragmented paths
2. **Raster-first pipelines** — most "vector" tools generate PNG then auto-trace (same as Illustrator Image Trace)
3. **No production awareness** — tools don't know about stroke vs fill, color-mapped operations, node optimization
4. **Post-processing still required** — even best tools need SVGO optimization and manual cleanup

## Human in the Loop

Full automation is unlikely because:

- **Material-specific judgment** — same design engraves differently on wood vs glass vs leather
- **Customer intent is ambiguous** — "make my logo look good on a cutting board" requires taste
- **Quality stakes are high** — bad engrave wastes material (especially customer-supplied items)
- **Color layer assignment** — cut vs engrave vs score is a design decision per product

The sweet spot is reducing a 20-minute cleanup task to a 2-minute review. The operator stays in the loop for judgment calls, not node editing.

## Demo Approach

Rather than using general-purpose AI vector generation, this demo tests a focused pipeline:

1. **Background removal** — segment logo from background
2. **Simplification** — collapse colors to binary mask (engrave / don't engrave)
3. **Contour detection** — extract clean edges
4. **Vectorization** — convert contours to minimal-node SVG paths

This is a more tractable problem than general vector generation and maps to well-understood CV operations. The hypothesis is that a purpose-built pipeline for this specific transformation will outperform generic AI vector tools for the engraving use case.
