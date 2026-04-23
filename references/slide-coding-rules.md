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

## Marker Nesting Contract

The extractor hides and reveals `data-ppt-item` nodes while capturing each item. Nested item-aware markers can make the target element invisible during Playwright screenshot capture.

- Use exactly one `data-ppt-group` boundary for a repeatable structure.
- Put `data-ppt-item` on the immediate repeatable unit: the card, row, step, or timeline node.
- Do not put `data-ppt-group` inside `data-ppt-item`.
- Do not put `data-ppt-item` inside another `data-ppt-item`.
- Do not nest `data-ppt-group` inside another `data-ppt-group`.
- For a list inside a card, leave the inner `ul/li` unmarked, or export the whole card with a raster fallback.

## Optional Overrides

| Attribute | Values | Behavior |
| --- | --- | --- |
| `data-ppt-raster-mode` | `auto`, `force`, `skip` | Controls raster capture for the marked element. |
| `data-ppt-native-text` | `auto`, `force`, `skip` | Controls native text export for a `data-ppt-text` element. |
| `data-ppt-fallback` | `item-raster`, `group-raster`, `slide-raster` | Hints the safe fallback level. |

## Raster And Native Text Contract

- Full-slide `data-ppt-bg` is the base layer only; it is not captured again as a component.
- Smaller standalone `data-ppt-bg` components are hidden before the base screenshot, then captured independently.
- `data-ppt-text` defaults to native export and is hidden during raster capture.
- `data-ppt-text data-ppt-native-text="skip"` stays visible in its local raster and is not exported as a native PPT text box.
- Use `skip` for tiny labels, kicker pills, badges, chart tags, and text with critical CSS effects such as letter spacing, glow, gradient clipping, or blend modes.
- **Shadow Wrapper Contract**: Because Playwright's component capture clips to the element's strict bounding box, any `data-ppt-item` or `data-ppt-bg` element with a `box-shadow` or `drop-shadow` MUST be wrapped in an invisible padding layer (e.g., `className="p-10 -m-10"`) that acts as the marker host. This ensures the extracted raster has enough space to hold the shadow ink without cropping.

## Non-Negotiable Rules

- Do not bake item-specific bullets, cards, icons, timeline nodes, labels, or item shadows into the parent background.
- Do not nest item-aware markers. `validate` rejects nested `data-ppt-group`/`data-ppt-item` structures because they can make export screenshots time out.
- Do not use `::before` or `::after` for item-specific visuals that should become independent PPT objects.
- Keep `data-ppt-text` inside the relevant `data-ppt-item`.
- Do not put `data-ppt-text` on a complex label unless you also mark it with `data-ppt-native-text="skip"`.
- If a component cannot be itemized without visual risk, use raster fallback instead of reducing visual quality.
- If a slide title, subtitle, or body copy must be visible to humans, it must be visible in HTML preview too. PPTX-only visibility is a bug.
- Do not hide essential content with `display:none`, `visibility:hidden`, `opacity:0`, or off-canvas positioning unless it is explicitly a temporary extractor-only state.
- When a piece of content is intentionally exported as native PowerPoint text but should stay visually faithful in HTML, prefer `data-ppt-native-text="skip"` on a safe visible duplicate or restyle the text so both HTML and PPTX share the same visible layer.

## Visual Validation Contract

- Browser validation must inspect the rendered HTML tree, not just the manifest.
- Repaired slides must be rerun through validation until the validator returns no issues.
- The preview server should be reused when possible and closed when the validator owns it.
- Use `?extract=1` for stable full-deck inspection when checking export consistency.
- HTML and PPTX must agree on essential visible content.

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
- Wrong: a `data-ppt-item` card contains an inner `data-ppt-group="list"` or inner `li data-ppt-item`.
- Wrong: bullet dots are CSS pseudo-elements on `li::before`.
- Wrong: timeline nodes are drawn into a single background SVG while labels are separate text.
- Correct: every repeatable row, card, node, or step has its own `data-ppt-item`.
