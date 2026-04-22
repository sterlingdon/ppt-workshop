# PPTX Exporter Reference

## Builder Responsibilities

`tools/builder.py` opens the React renderer and writes `layout_manifest.json`.

It extracts:

- Slide background.
- Component rasters from `data-ppt-bg`.
- Native text candidates from `data-ppt-text`.
- Item-aware groups from `data-ppt-group`.
- Item rasters from `data-ppt-item` or `data-ppt-item-bg`.
- Item-local text from `data-ppt-text` nested inside `data-ppt-item`.

## Exporter Responsibilities

`tools/pptx_exporter.py` consumes `layout_manifest.json` and creates `presentation.pptx`.

It must preserve visual stacking:

1. Background.
2. Raster components.
3. Group segments and tracks.
4. Item rasters.
5. Item-local native text.
6. Slide-level native text.

## Troubleshooting

- Missing item in PPTX: check `data-ppt-item` and item bounding boxes.
- Stale bullet remains after deleting item: item visuals were baked into parent background.
- Text appears twice: text was not hidden before item screenshot.
- Visual quality regressed: use raster fallback instead of native reconstruction.
