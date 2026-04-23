# PPT Design DNA Guide

The visual system comes from `design_dna.json`, which is created from the `ui-ux-pro-max` recommendation for the specific source material.

## Workflow

Start from `examples/react-slides/minimal-deck/README.md` when authoring generated project slides. It shows the marker structure and how to map design DNA into React.

1. Read `design_dna.json` before writing JSX.
2. Copy `design_dna.json.theme_tokens` into a slide-level `CSSProperties` object.
3. Use `--ppt-*` CSS variables for color, typography, surfaces, borders, and chart colors.
4. Implement at least one `signature_visual_moves` idea on every slide.
5. Follow `type_scale` and `composition_rules`; do not improvise font sizes after copy is locked.
6. Mark the root with `data-ppt-slide`, visual screenshot regions with `data-ppt-bg`, and editable text with `data-ppt-text`.

Generated project slides should keep theme values in the project artifact and slide source.

## Marker Contract

- `data-ppt-slide`: exactly one root per slide component.
- `data-ppt-bg`: independent visual regions that should be preserved as high-fidelity images.
- `data-ppt-text`: text that should become editable PowerPoint text.

Do not put `data-ppt-bg` and `data-ppt-text` on the same element.

## HTML Preview Rule

Slides are not valid if they only work in PPTX export. The HTML preview is the human-facing deck, so slide titles, subtitles, and other essential copy must remain visible in browser rendering unless the element is explicitly marked for a safe export-only treatment.

## Item-Aware PPT Export

Repeatable structures must use `data-ppt-group` and `data-ppt-item`. Read `references/slide-coding-rules.md` before authoring generated slides.
