# PPT Style Preset Guide

Agents should not invent a complete visual language per deck. Choose one preset, then choose slide patterns from that preset.

## Workflow

1. Pick a preset from `presets.ts` based on domain and tone.
2. Use `getDeckStylePreset()` and `styleVars()` in each slide root.
3. Choose a `slidePatterns[].id` for every slide before writing JSX.
4. Use `--ppt-*` CSS variables for color and typography.
5. Mark the root with `data-ppt-slide`, visual screenshot regions with `data-ppt-bg`, and editable text with `data-ppt-text`.

## Current Presets

- `aurora-borealis`: technical, AI, cybersecurity, deep dark visual impact.
- `bold-signal`: business, startup, finance, decision-making decks.
- `editorial-ink`: education, culture, content reports, narrative decks.

## Marker Contract

- `data-ppt-slide`: exactly one root per slide component.
- `data-ppt-bg`: independent visual regions that should be preserved as high-fidelity images.
- `data-ppt-text`: text that should become editable PowerPoint text.

Do not put `data-ppt-bg` and `data-ppt-text` on the same element.

## Item-Aware PPT Export

Repeatable structures must use `data-ppt-group` and `data-ppt-item`. Read `references/slide-coding-rules.md` before authoring generated slides.
