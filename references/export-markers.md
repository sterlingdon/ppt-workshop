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
2. `data-ppt-bg` components.
3. Group tracks and connector segments.
4. Item rasters.
5. Native item text.
6. Slide-level native text.

## Fallback Hints

- `data-ppt-raster-mode="force"`: force raster capture for the element.
- `data-ppt-native-text="skip"`: keep text inside raster instead of native overlay.
- `data-ppt-fallback="group-raster"`: prefer group-level fallback if item slicing is unsafe.

## High-Fidelity Label Rule

Use `data-ppt-native-text="skip"` for visually styled micro-labels, kicker pills, badges, chart tags, and small uppercase tracking-heavy labels. The text stays inside the local raster component, so PowerPoint does not place a lower-fidelity native text box on top of an already captured label.

```tsx
<div data-ppt-bg className="rounded-full border bg-white/5 px-5 py-2 tracking-[0.32em]">
  <span className="h-2 w-2 rounded-full bg-cyan-300 shadow-[0_0_18px_#22d3ee]" />
  <span data-ppt-text data-ppt-native-text="skip">Technical Stack</span>
</div>
```

Keep slide-level atmospheric backgrounds as full-slide `data-ppt-bg`; the builder treats full-slide backgrounds as the base layer and does not capture them again as components. Smaller standalone `data-ppt-bg` components are removed from the base screenshot first, then captured independently, preventing duplicate raster layers.
