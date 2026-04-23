# Engineering Reference

This file is for implementation details. For day-to-day deck execution, start with `references/workflow.md`.

## Current Architecture

The current pipeline is React-first and project-workspace based.

```text
INPUT (URL / text / PDF / notes)
  -> output/projects/<project-id>/
  -> article_text.md
  -> deck_state.json
  -> analysis.json
  -> content_quality_report.json
  -> design_recommendation.json
  -> design_dna.json
  -> outline.json
  -> slide_blueprint.json
  -> slides/Slide_N.tsx + slides/index.ts
  -> review/full_deck.png + review/slides/*.png
  -> visual_review_report.json
  -> visual_validation_report.json
  -> layout_manifest.json + assets/
  -> presentation.pptx
```

The CLI does not create the analysis, design DNA, outline, or React slide code. The agent creates those files.

## Workspace

Created by `tools/presentation_workspace.py`:

```text
output/projects/<project-id>/
├── project.json
├── article_text.md
├── deck_state.json
├── analysis.json
├── content_quality_report.json
├── design_recommendation.json
├── design_dna.json
├── outline.json
├── slide_blueprint.json
├── slides/
├── review/
├── visual_review_report.json
├── visual_validation_report.json
├── layout_manifest.json
├── presentation.pptx
└── assets/
```

## Responsibility Boundaries

| Stage | Owner | Input | Output | Responsibility |
| --- | --- | --- | --- | --- |
| Workspace | Python CLI | deck name | `project.json`, dirs | Create isolated project |
| Ingest | Agent/Python | URL/text/PDF | `article_text.md` | Clean source text |
| Content Quality Auditor | Agent | `deck_state.json`, `article_text.md` | `deck_state.json`, `analysis.json`, `content_quality_report.json` | Audience, thesis, evidence, stats, emphasis, cut list, deck angle |
| Design intelligence | Agent + `ui-ux-pro-max` | approved content audit | `design_recommendation.json` | External style, color, typography, layout, and chart guidance |
| PPT Generation Agent | Agent | `deck_state.json`, content audit + design recommendation | `deck_state.json`, `design_dna.json`, `outline.json`, `slide_blueprint.json`, `slides/*.tsx` | Map design guidance, plan slides, author React deck |
| Structural gate | Python CLI | slide sources | terminal result | Marker/source sanity checks |
| Render review assets | Agent/browser tool | React preview | `review/full_deck.png`, `review/slides/*.png` | Capture the rendered deck for AI visual review |
| AI Lens Review | Agent | `deck_state.json`, rendered deck + contract + review screenshots | `deck_state.json`, `visual_review_report.json` | Visual quality, strategic fit, and repair decisions |
| Engineering browser gate | Python/Playwright | React preview | `visual_validation_report.json` | Visibility, clipping, coverage, overflow |
| Extraction | Python/Playwright | React preview | `layout_manifest.json`, `assets/` | Capture backgrounds/components/text boxes |
| Export | Python | manifest | `presentation.pptx` | Build hybrid PPTX |

## CLI

```bash
python3 tools/ppt_workflow.py init --name "Deck Name"
python3 tools/ppt_workflow.py validate --project <project-id>
python3 tools/ppt_workflow.py visual-validate --project <project-id>
python3 tools/ppt_workflow.py build --project <project-id>
```

Other commands:

- `activate`: copy project slides into `web/src/generated/slides/`.
- `snapshot-slides`: copy active generated slides back into the project.
- `extract`: activate slides and write manifest/assets.
- `export`: build PPTX from an existing manifest.

`build` executes: activate -> source validation plus required agent gate report checks -> engineering browser validation -> extract -> export -> final output validation.

`build` does not perform the human/agent work of Content Quality Audit or AI Lens Review. It does require their passed report files before export; missing or blocked `content_quality_report.json` or `visual_review_report.json` fails the build preflight.

## Style System

Generated project slides use `design_dna.json.theme_tokens` as the visual source of truth.

Slide components should map the design DNA into CSS variables:

```tsx
import type { CSSProperties } from 'react'

const designDnaTheme = {
  '--ppt-bg': '#F7F3EA',
  '--ppt-surface': '#FFFFFF',
  '--ppt-primary': '#2D5A4A',
  '--ppt-accent': '#C99A2E',
  '--ppt-text': '#18211D',
  '--ppt-muted': '#5D665F',
  '--ppt-border': '#D8CCB8',
} as CSSProperties

<div style={designDnaTheme} className="bg-[var(--ppt-bg)] text-[var(--ppt-text)]">
```

Read `references/ppt-visual-design.md`, then use `ui-ux-pro-max` before writing `design_recommendation.json` or `design_dna.json`. The `ui-ux-pro-max` query must ask for transferable web/product design principles adapted to a fixed 16:9 PowerPoint deck, not a website/app layout. Save its distilled output as `design_recommendation.json`, then use `design_dna.json` to define theme variables and lock deck-specific visual rules.

`design_dna.json` is the design source. Preserve the recommendation through `theme_tokens`, `visual_language`, `signature_visual_moves`, `type_scale`, `composition_rules`, and `consistency_rules`.

See `examples/react-slides/minimal-deck/Slide_3.tsx` for the full pattern.

## Marker Contract

The exporter depends on markers documented in `references/slide-coding-rules.md`.

Minimum requirements:

- one `data-ppt-slide` root per slide
- visible human-facing text marked with `data-ppt-text`
- visual raster regions marked with `data-ppt-bg`
- repeatable structures marked with `data-ppt-group` and `data-ppt-item`

Do not put `data-ppt-bg` and `data-ppt-text` on the same element unless the slide has been tested and the export behavior is intentional.

## Quality Gate Details

`tools/quality_gate.py` validates:

- project workspace exists
- `slides/` exists
- `slides/index.ts` exists
- `Slide_*.tsx` files exist
- each slide has `data-ppt-slide`
- the deck has at least one `data-ppt-text`
- slide code uses `--ppt-*` variables from `design_dna.json.theme_tokens`
- manifest-referenced assets exist when outputs are checked
- `presentation.pptx` is not empty when present

It does not validate narrative quality, visual taste, audience fit, or design consistency.

`tools/visual_validator.py` validates the rendered browser preview for text visibility, clipping, coverage, and overflow. It is an engineering render validator. It does not judge strategic quality or visual excellence, and a passing result must not be treated as AI visual review approval.

`visual_review_report.json` is the agent-owned AI visual audit. It should record blocking design findings, visual scores, and repairs. It is not generated by Python.

## Export Architecture

`tools/builder.py` opens the React renderer at `?extract=1` and writes `layout_manifest.json`.

It extracts:

- full-slide background screenshots
- component rasters from `data-ppt-bg`
- item-aware groups from `data-ppt-group`
- item rasters from `data-ppt-item` / `data-ppt-item-bg`
- native text boxes from `data-ppt-text`

`tools/pptx_exporter.py` consumes `layout_manifest.json` and writes `presentation.pptx`.

Layer order:

1. Background image.
2. Component rasters.
3. Group tracks and connector segments.
4. Item rasters.
5. Item-local native text.
6. Slide-level native text.

## Images And Diagrams

For diagrams, icons, charts, and atmospheric visuals, prefer React/SVG/CSS implementations inside slide components and let the extractor rasterize them where appropriate.

## Troubleshooting

- `validate` fails: fix missing `index.ts`, missing `Slide_*.tsx`, missing `data-ppt-slide`, missing `data-ppt-text`, or missing `--ppt-*` theme variables.
- `visual-validate` fails: fix clipped, hidden, covered, missing, or overflowing content in the browser preview.
- PPTX has missing item graphics: check `data-ppt-group`, `data-ppt-item`, and item bounding boxes.
- Text appears twice: check whether text stayed visible in a raster while also exporting as native text.
- Visual quality regressed: prefer raster fallback over lower-fidelity native reconstruction.
