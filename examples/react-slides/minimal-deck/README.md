# Minimal React Slide Deck Example

Use this example before authoring slides in `output/projects/<project-id>/slides/`.

The workflow copies project slide sources into `web/src/generated/slides/` before rendering. Write imports as if the file already lives in that active renderer slot.

The visual system comes from `design_dna.json.theme_tokens`, mapped into a slide-level `CSSProperties` object:

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
  '--ppt-font-display': 'Inter, ui-sans-serif, system-ui, sans-serif',
  '--ppt-font-body': 'Inter, ui-sans-serif, system-ui, sans-serif',
} as CSSProperties
```

Generated project slides should keep theme values in the project artifact and slide source.

## Files

- `Slide_1.tsx`: title slide with locked copy and a high-fidelity background region.
- `Slide_2.tsx`: card list with `data-ppt-group`, `data-ppt-item`, `data-ppt-item-bg`, and native text markers.
- `Slide_3.tsx`: `design_dna.theme_tokens` applied directly.
- `design_dna.json`: example output from the ui-ux-pro-max → design DNA step, including `theme_tokens`, signature visual moves, visual recipes, type scale, and composition rules.
- `index.ts`: imports and exports every slide in order.

## Authoring Rules

- Keep slide components in `output/projects/<project-id>/slides/`.
- Use the same structure as this example instead of guessing import paths or marker names.
- Use CSS variables such as `var(--ppt-bg)`, `var(--ppt-text)`, and `var(--ppt-accent)` for deck styling.
- Treat `design_dna.json` as the visual source. `theme_tokens` should be complete enough for the slide root to render directly.
- Treat ui-ux-pro-max as transferable design intelligence for a PPT deck. Apply its hierarchy, palette, typography, spacing, and chart guidance to fixed 16:9 slides; do not turn slides into website/app screens.
- Put every human-facing text string in `slide_blueprint.json.locked_copy` first.
- Before JSX, decide each slide's focal point, type scale, whitespace strategy, and density in `slide_blueprint.json`.
- React slide code may arrange, split, emphasize, and wrap locked copy, but it must not rewrite facts, numbers, titles, entities, or conclusions.
- Use `data-ppt-text` for text that should become editable PowerPoint text.
- Use `data-ppt-bg` for visual regions that should be preserved as raster.
- Use `data-ppt-group` and `data-ppt-item` for repeatable structures such as lists, timelines, cards, and steps.
- Keep marker structure flat: a `data-ppt-item` must not contain another `data-ppt-item` or `data-ppt-group`, and a `data-ppt-group` must not contain another `data-ppt-group`. Inner lists inside a card should use plain `ul/li` without `data-ppt-*` item markers, or the whole card should use raster fallback.

## Applying `design_dna.json`

There is no separate override artifact in the real workflow. The PPT Generation Agent creates one `output/projects/<project-id>/design_dna.json` after reading the ui-ux-pro-max recommendation. Copy `theme_tokens` into a slide-level theme object and apply it directly to the slide root:

```tsx
import type { CSSProperties } from 'react'

const designDnaTheme = {
  '--ppt-bg': '#F7F3EA',
  '--ppt-primary': '#2D5A4A',
  '--ppt-accent': '#C99A2E',
  '--ppt-text': '#18211D',
} as CSSProperties

<div style={designDnaTheme} className="bg-[var(--ppt-bg)] text-[var(--ppt-text)]">
```

Keep JSX classes tied to `var(--ppt-*)` or derived CSS expressions such as `color-mix(...var(--ppt-primary)...)` so the external design recommendation controls the final visual system. Hex colors belong in `design_dna.json.theme_tokens` and the slide-level token mapping object, not scattered through JSX.
