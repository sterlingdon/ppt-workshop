# PPT Web Renderer

This Vite app renders generated React slide components for browser review, engineering validation, layout extraction, and PPTX export.

## Flow

- Generated project slides are activated into `web/src/generated/slides/`.
- If no generated deck is active, tracked sample slides render as a local smoke-test deck.
- Slide visuals come from `design_dna.json.theme_tokens` mapped into `--ppt-*` CSS variables on each slide root.
- The renderer mounts slides, supports review navigation, and provides the `?extract=1` full-deck mode used by Playwright.

## Slide Source Pattern

Generated slides should define theme variables directly from the project design DNA:

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

Keep colors and fonts in `design_dna.json.theme_tokens`, then use `var(--ppt-*)` in JSX classes.

## Commands

From the repository root:

```bash
python ../tools/ppt_workflow.py snapshot-slides --project <project-id>
python ../tools/ppt_workflow.py activate --project <project-id>
python ../tools/ppt_workflow.py review-screenshots --project <project-id>
python ../tools/ppt_workflow.py build --project <project-id>
```

`ppt_workflow.py build` writes:

- `output/projects/<project-id>/layout_manifest.json`
- `output/projects/<project-id>/assets/`
- `output/projects/<project-id>/presentation.pptx`
