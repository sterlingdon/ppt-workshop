# PPT React Renderer

This Vite app is the active visual renderer for the PPT skill.

## Responsibilities

- Render generated slide components from ignored `web/src/generated/slides/`, with tracked fallback examples from `web/src/sample-slides/`.
- Provide reusable style presets from `web/src/styles/presets.ts`.
- Provide AI-facing style guidance from `web/src/styles/STYLE_GUIDE.md`.
- Expose two modes:
  - normal preview mode for local browsing
  - `?extract=1` mode for Playwright layout extraction

## Style Presets

Agents should choose a preset first, choose one of its `slidePatterns`, then build slide components from its tokens and recipes instead of inventing a new visual system per slide.

```tsx
import { getDeckStylePreset, styleVars } from '../../styles'

const preset = getDeckStylePreset('aurora-borealis')

<div style={styleVars(preset)} className="bg-[var(--ppt-bg)] text-[var(--ppt-text)]">
  ...
</div>
```

This import path is for generated project slides because they are activated into `web/src/generated/slides/` before rendering. Tracked sample slides under `web/src/sample-slides/` use a different relative path.

Available presets:

- `aurora-borealis`: dark technical, cyan-purple light, glass panels
- `bold-signal`: business/startup, black surfaces, orange signal accents
- `editorial-ink`: light editorial, print hierarchy, restrained red accent

## Output Boundaries

Generated project artifacts should go under `output/projects/<project-id>/`, not directly into `output/`. `output/` is gitignored, so generated deck source does not go to Git by default.

The durable slide source for a deck is:

- `output/projects/<project-id>/slides/`

The active renderer slot is:

- `web/src/generated/slides/`

Tracked example slides live in:

- `web/src/sample-slides/`

Use:

```bash
python ../tools/ppt_workflow.py snapshot-slides --project <project-id>
python ../tools/ppt_workflow.py activate --project <project-id>
python ../tools/ppt_workflow.py review-screenshots --project <project-id>
python ../tools/ppt_workflow.py build --project <project-id>
```

`ppt_workflow.py build` writes:

- `layout_manifest.json`
- `assets/slide_*_bg.png`
- `assets/slide_*_comp_*.png`
- `presentation.pptx`
