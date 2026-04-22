# Slide Coding Rules

This is the canonical API contract for React slide components consumed by the PPTX exporter.

Visual fidelity is the product floor. Do not simplify visual design to make PowerPoint objects more native.

## Required Root

| Marker | Purpose | Allowed element | Export behavior |
| --- | --- | --- | --- |
| `data-ppt-slide` | Marks one slide root and defines the coordinate system. | One root `div` per slide. | Builder scans this element and computes all child boxes relative to it. |

## Visual Markers

| Marker | Purpose | Allowed element | Export behavior |
| --- | --- | --- | --- |
| `data-ppt-bg` | High-fidelity raster region that is not item-aware. | Any non-text container. | Captured as a raster component. |
| `data-ppt-text` | Text that should become native PowerPoint text when safe. | Text-bearing elements such as `h1`, `h2`, `p`, `span`, `li`. | Hidden during raster capture, exported as native text. |

## Repeatable Structure Markers

| Marker | Purpose | Allowed element | Export behavior |
| --- | --- | --- | --- |
| `data-ppt-group` | Repeatable structure container. Values: `list`, `timeline`, `stepper`, `agenda`, `fact-list`, `card-grid`. | Container `div`, `ul`, `ol`, `section`. | Builder extracts child `data-ppt-item` units. |
| `data-ppt-item` | One copyable/deletable item. | Item wrapper `div`, `li`, `article`. | Captured independently unless forced to fallback. |
| `data-ppt-item-bg` | Item visual background when text overlays are native. | Child container inside item. | Captured as item raster if present. |
| `data-ppt-bullet` | Bullet, icon, number badge, image, or timeline node. | `span`, `div`, `img`, `svg`. | Included in item raster by default for maximum fidelity. |
| `data-ppt-track` | Shared rail or track. | `div`, `svg`. | Captured independently when present. |
| `data-ppt-segment` | Connector segment. | `div`, `svg`, line wrapper. | Captured as segment raster. |

## Optional Overrides

| Attribute | Values | Behavior |
| --- | --- | --- |
| `data-ppt-raster-mode` | `auto`, `force`, `skip` | Controls raster capture for the marked element. |
| `data-ppt-native-text` | `auto`, `force`, `skip` | Controls native text export for a `data-ppt-text` element. |
| `data-ppt-fallback` | `item-raster`, `group-raster`, `slide-raster` | Hints the safe fallback level. |

## Non-Negotiable Rules

- Do not bake item-specific bullets, cards, icons, timeline nodes, labels, or item shadows into the parent background.
- Do not use `::before` or `::after` for item-specific visuals that should become independent PPT objects.
- Keep `data-ppt-text` inside the relevant `data-ppt-item`.
- If a component cannot be itemized without visual risk, use raster fallback instead of reducing visual quality.

## Minimal Valid List

```tsx
<div data-ppt-group="list">
  {items.map((item) => (
    <div data-ppt-item key={item.id}>
      <div data-ppt-item-bg />
      <span data-ppt-bullet />
      <span data-ppt-text>{item.text}</span>
    </div>
  ))}
</div>
```

## Common Mistakes

- Wrong: one `data-ppt-bg` wrapper contains all list bullets and item cards.
- Wrong: bullet dots are CSS pseudo-elements on `li::before`.
- Wrong: timeline nodes are drawn into a single background SVG while labels are separate text.
- Correct: every repeatable row, card, node, or step has its own `data-ppt-item`.
