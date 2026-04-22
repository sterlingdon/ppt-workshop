# Minimal React Slide Deck Example

Use this example before authoring slides in `output/projects/<project-id>/slides/`.

The workflow copies project slide sources into `web/src/generated/slides/` before rendering. Write imports as if the file already lives in that active renderer slot.

Correct style import for every generated `Slide_N.tsx`:

```tsx
import { getDeckStylePreset, styleVars } from '../../styles'
```

Do not import from `../../../web/src/styles/presets`, `web/src/styles`, or `../styles` in generated project slides.

## Files

- `Slide_1.tsx`: title slide with locked copy and a high-fidelity background region.
- `Slide_2.tsx`: card list with `data-ppt-group`, `data-ppt-item`, `data-ppt-item-bg`, and native text markers.
- `Slide_3.tsx`: local preset plus `design_dna.token_extensions` override from ui-ux-pro-max recommendations.
- `design_dna.json`: example output from the ui-ux-pro-max → design DNA step, including `token_extensions`.
- `index.ts`: imports and exports every slide in order.

## Authoring Rules

- Keep slide components in `output/projects/<project-id>/slides/`.
- Use the same structure as this example instead of guessing import paths or marker names.
- Use `getDeckStylePreset()` and `styleVars(preset)` on each slide root.
- Use CSS variables such as `var(--ppt-bg)`, `var(--ppt-text)`, and `var(--ppt-accent)` for deck styling.
- Treat the local preset as a renderer scaffold. If ui-ux-pro-max recommends custom colors or typography, write them into `design_dna.json.token_extensions` and spread those variables after `styleVars(preset)`.
- Put every human-facing text string in `slide_blueprint.json.locked_copy` first.
- React slide code may arrange, split, emphasize, and wrap locked copy, but it must not rewrite facts, numbers, titles, entities, or conclusions.
- Use `data-ppt-text` for text that should become editable PowerPoint text.
- Use `data-ppt-bg` for visual regions that should be preserved as raster.
- Use `data-ppt-group` and `data-ppt-item` for repeatable structures such as lists, timelines, cards, and steps.

## Applying `design_dna.json`

There is no separate override artifact in the real workflow. The PPT Generation Agent creates one `output/projects/<project-id>/design_dna.json` after reading the ui-ux-pro-max recommendation. If that file contains `token_extensions`, copy those variables into a slide-level theme object and spread them after `styleVars(preset)`:

```tsx
import type { CSSProperties } from 'react'
import { getDeckStylePreset, styleVars } from '../../styles'

const designDnaTokenExtensions = {
  '--ppt-bg': '#F7F3EA',
  '--ppt-primary': '#2D5A4A',
  '--ppt-accent': '#C99A2E',
  '--ppt-text': '#18211D',
} as CSSProperties

const preset = getDeckStylePreset('editorial-ink')
const themeVars = {
  ...styleVars(preset),
  ...designDnaTokenExtensions,
} as CSSProperties

<div style={themeVars} className="bg-[var(--ppt-bg)] text-[var(--ppt-text)]">
```

Do not use the preset default colors after `design_dna.json` overrides them. Keep JSX classes tied to `var(--ppt-*)` or derived CSS expressions such as `color-mix(...var(--ppt-primary)...)` so the external design recommendation controls the final visual system. Hex colors belong in `design_dna.json.token_extensions` and the slide-level token mapping object, not scattered through JSX.
