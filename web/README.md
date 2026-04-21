# PPT React Renderer

This Vite app is the active visual renderer for the PPT skill.

## Responsibilities

- Render generated slide components from `web/src/slides/`.
- Provide reusable style presets from `web/src/styles/presets.ts`.
- Expose two modes:
  - normal preview mode for local browsing
  - `?extract=1` mode for Playwright layout extraction

## Style Presets

Agents should choose a preset first, then build slide components from its tokens and recipes instead of inventing a new visual system per slide.

```tsx
import { getDeckStylePreset, styleVars } from './styles'

const preset = getDeckStylePreset('aurora-borealis')

<div style={styleVars(preset)} className="bg-[var(--ppt-bg)] text-[var(--ppt-text)]">
  ...
</div>
```

Available presets:

- `aurora-borealis`: dark technical, cyan-purple light, glass panels
- `bold-signal`: business/startup, black surfaces, orange signal accents
- `editorial-ink`: light editorial, print hierarchy, restrained red accent

## Output Boundaries

Generated project artifacts should go under `output/projects/<project-id>/`, not directly into `output/`.

`tools/builder.py --project <project-id>` writes:

- `layout_manifest.json`
- `assets/slide_*_bg.png`
- `assets/slide_*_comp_*.png`
