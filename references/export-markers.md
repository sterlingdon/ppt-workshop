# Export Marker Reference

## Core Markers

- `data-ppt-slide`: one per slide. Establishes the 1920x1080 coordinate system.
- `data-ppt-bg`: non-item-aware high-fidelity raster region.
- `data-ppt-text`: editable text candidate.
- `data-ppt-group`: item-aware repeatable structure.
- `data-ppt-item`: copyable/deletable unit inside a group.
- `data-ppt-item-bg`: item visual layer when text is overlaid natively.
- `data-ppt-bullet`: item bullet, icon, badge, image, or node.
- `data-ppt-track`: shared rail for timeline/process visuals.
- `data-ppt-segment`: independently captured connector segment.

## Export Behavior

The exporter renders in this order:

1. Slide background.
2. Legacy `data-ppt-bg` components.
3. Group tracks and connector segments.
4. Item rasters.
5. Native item text.
6. Legacy slide-level native text.

## Fallback Hints

- `data-ppt-raster-mode="force"`: force raster capture for the element.
- `data-ppt-native-text="skip"`: keep text inside raster instead of native overlay.
- `data-ppt-fallback="group-raster"`: prefer group-level fallback if item slicing is unsafe.
