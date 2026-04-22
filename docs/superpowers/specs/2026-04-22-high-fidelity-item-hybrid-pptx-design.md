# High-Fidelity Item Hybrid PPTX Export Design

## Goal

Upgrade the current React-to-PPTX exporter so common repeatable structures can be deleted, copied, and extended at item level while preserving the current visual quality as the product baseline.

The design is intentionally not a full HTML-to-native-PPT conversion. Visual fidelity remains the first priority. Editable structure is added only where it can be done without degrading the rendered output.

## Non-Negotiable Requirement

High visual fidelity is the product floor.

If item-level export cannot reproduce the React-rendered visual result reliably, the exporter must fall back to the existing raster-first path for that region or slide. A less editable but visually correct PPTX is preferable to a more editable but visually degraded PPTX.

## Current Problem

The current exporter uses three coarse object types:

- Full-slide background screenshot.
- Component screenshots from `data-ppt-bg`.
- Native PowerPoint text boxes from `data-ppt-text`.

This preserves visual quality, but it causes repeatable components to be baked into background images. For lists, timelines, process flows, agenda pages, and fact grids, deleting or adding one item can leave mismatched bullets, tracks, nodes, shadows, or card backgrounds.

The current full-slide screenshot plus component screenshot approach also duplicates pixels, increasing PPTX size.

## Design Principle

Use a high-fidelity hybrid model:

- Screenshots preserve complex visual effects.
- Item-level slicing preserves repeatable structure.
- Native text overlays preserve text editability.
- Raster-first fallback preserves visual quality when item slicing is unsafe.

The target output is not perfectly semantic PPT. The target output is a visually faithful PPT where common repeated units can be individually copied or removed.

## Scope

Initial supported structures:

- Lists.
- Timelines.
- Steppers and process flows.
- Agenda lists.
- Fact lists.
- Simple card grids.

Out of scope for the first implementation:

- Automatic PowerPoint reflow after deleting an item.
- Full CSS flex/grid behavior inside PowerPoint.
- Full SVG-to-PPT-shape conversion.
- Fully native chart reconstruction.
- PowerPoint add-ins or macros.

Users should be able to duplicate an existing item and manually align it. They should not expect PowerPoint to automatically recompute the whole layout.

## Marker Contract

Existing markers remain valid:

- `data-ppt-slide`: slide root.
- `data-ppt-bg`: high-fidelity raster region.
- `data-ppt-text`: editable text.

New markers introduce item-level structure:

- `data-ppt-group`: repeatable structure container. Values include `list`, `timeline`, `stepper`, `agenda`, `fact-list`, and `card-grid`.
- `data-ppt-item`: one independently removable/copyable item.
- `data-ppt-item-bg`: visual background for one item when the item text will be overlaid natively.
- `data-ppt-bullet`: bullet, icon, image, or node associated with one item.
- `data-ppt-track`: shared timeline or process track.
- `data-ppt-segment`: independently sliced connector segment between items.

## Agent Authoring Requirements

The skill must teach slide-building agents how to create export-friendly React components. Without these authoring rules, agents will keep producing old-style slides where repeatable structures are baked into a large `data-ppt-bg` screenshot.

These rules should be added to `SKILL.md` and the frontend style guide during implementation.

### Required Rule: Repeatable UI Must Be Marked As Groups And Items

Any repeatable visual structure must use `data-ppt-group` and `data-ppt-item`.

This includes:

- Bullet lists.
- Numbered lists.
- Timeline nodes.
- Process or stepper items.
- Agenda rows.
- Fact cards.
- Card grid cells.

Agents must not create a list, timeline, or process flow as one monolithic `data-ppt-bg` block if users may need to add, delete, or copy individual items later.

### Required Rule: Do Not Bake Item Visuals Into Parent Backgrounds

For item-aware components, parent containers may contain only:

- Overall atmosphere.
- Shared background texture.
- Shared track or rail.
- Decorative elements that are not tied to item count.

Parent containers must not contain item-specific bullets, icons, numbers, nodes, labels, cards, or per-item shadows. Those must live inside `data-ppt-item` or item children.

Bad pattern:

```tsx
<div data-ppt-bg="true">
  <DecorativeBulletListBackground count={items.length} />
  {items.map((item) => (
    <span data-ppt-text>{item.text}</span>
  ))}
</div>
```

Good pattern:

```tsx
<div data-ppt-group="list">
  {items.map((item) => (
    <div data-ppt-item key={item.id}>
      <div data-ppt-item-bg />
      <img data-ppt-bullet src={item.icon} />
      <span data-ppt-text>{item.text}</span>
    </div>
  ))}
</div>
```

### Required Rule: Use Real DOM Elements For Exportable Parts

Exportable bullets, icons, nodes, connector segments, and item backgrounds must be real DOM elements. Agents should not use CSS pseudo-elements like `::before` or `::after` for any item-specific visual that should survive as an independent PPT object.

Allowed:

```tsx
<span data-ppt-bullet className="h-3 w-3 rounded-full bg-white" />
```

Avoid for exportable item visuals:

```css
li::before {
  content: "";
  width: 12px;
  height: 12px;
  border-radius: 9999px;
}
```

Pseudo-elements are acceptable only for purely decorative effects that can safely remain in a raster fallback.

### Required Rule: Item Text Should Stay Inside The Item

Text belonging to an item should be nested inside that item and marked with `data-ppt-text`.

```tsx
<div data-ppt-item>
  <div data-ppt-item-bg />
  <h3 data-ppt-text>{item.title}</h3>
  <p data-ppt-text>{item.body}</p>
</div>
```

This lets the exporter attach native text overlays to the same item coordinate system.

### Required Rule: Timeline Connectors Must Be Segmentable

Timeline and process components should not draw all connectors as one inseparable SVG unless that connector can remain after deleting any item.

Preferred structure:

```tsx
<div data-ppt-group="timeline">
  {items.map((item, index) => (
    <div data-ppt-item key={item.id}>
      {index > 0 && <div data-ppt-segment />}
      <div data-ppt-bullet data-ppt-node />
      <h3 data-ppt-text>{item.title}</h3>
    </div>
  ))}
</div>
```

If the timeline visual uses a complex SVG track, the track can remain as `data-ppt-track`, but item-specific nodes and labels must still be separate item children.

### Required Rule: Prefer Item-Level Raster Fidelity Over Native Reconstruction

Agents should continue using visually rich CSS, SVG, images, blur, and shadows, but the repeated unit must be isolatable.

The correct authoring mindset is:

- Build beautiful React visuals as before.
- Wrap repeatable units in export markers.
- Keep item-specific visuals inside each item.
- Let the exporter screenshot each item when native reconstruction would be risky.

Agents should not simplify visuals just to make components native PPT shapes. Visual fidelity remains the product floor.

### Component Recipes For Agents

List recipe:

```tsx
<div data-ppt-group="list" className="space-y-5">
  {items.map((item) => (
    <div data-ppt-item key={item.id} className="relative flex gap-5 rounded-3xl">
      <div data-ppt-item-bg className="absolute inset-0 rounded-3xl bg-white/10 shadow-2xl" />
      <img data-ppt-bullet src={item.icon} className="relative z-10 h-12 w-12" />
      <div className="relative z-10">
        <h3 data-ppt-text>{item.title}</h3>
        <p data-ppt-text>{item.body}</p>
      </div>
    </div>
  ))}
</div>
```

Timeline recipe:

```tsx
<div data-ppt-group="timeline" className="relative">
  <div data-ppt-track className="absolute left-0 right-0 top-1/2 h-1 rounded-full bg-white/20" />
  {items.map((item, index) => (
    <div data-ppt-item key={item.id} className="relative">
      {index > 0 && <div data-ppt-segment className="absolute -left-12 top-1/2 h-1 w-12 bg-white/40" />}
      <div data-ppt-bullet data-ppt-node className="h-8 w-8 rounded-full bg-white shadow-xl" />
      <h3 data-ppt-text>{item.title}</h3>
      <p data-ppt-text>{item.body}</p>
    </div>
  ))}
</div>
```

Card grid recipe:

```tsx
<div data-ppt-group="card-grid" className="grid grid-cols-3 gap-6">
  {cards.map((card) => (
    <article data-ppt-item key={card.id} className="relative rounded-3xl">
      <div data-ppt-item-bg className="absolute inset-0 rounded-3xl bg-white/10 shadow-2xl" />
      <img data-ppt-bullet src={card.iconSrc} alt="" />
      <h3 data-ppt-text>{card.title}</h3>
      <p data-ppt-text>{card.body}</p>
    </article>
  ))}
</div>
```

### Agent Self-Check Before Build

Before running `ppt_workflow.py build`, the agent should check:

- Every repeatable structure has `data-ppt-group`.
- Every repeatable item has `data-ppt-item`.
- Item-specific bullets, icons, nodes, and cards are not drawn in the parent background.
- Item text is nested inside the item and marked with `data-ppt-text`.
- Timeline nodes and labels are separate from the shared track.
- Visual richness has not been reduced for editability.

Example list:

```tsx
<div data-ppt-group="list">
  {items.map((item) => (
    <div data-ppt-item key={item.id}>
      <div data-ppt-item-bg />
      <img data-ppt-bullet src={item.icon} />
      <span data-ppt-text>{item.text}</span>
    </div>
  ))}
</div>
```

Example timeline:

```tsx
<div data-ppt-group="timeline">
  <div data-ppt-track />
  {items.map((item, index) => (
    <div data-ppt-item key={item.id}>
      <div data-ppt-segment data-ppt-segment-index={index} />
      <div data-ppt-bullet data-ppt-node />
      <span data-ppt-text>{item.title}</span>
      <span data-ppt-text>{item.body}</span>
    </div>
  ))}
</div>
```

## Extraction Model

The builder should produce a richer manifest with layers:

```json
{
  "slides": [
    {
      "index": 0,
      "background": {
        "mode": "raster",
        "path": "assets/slide_0_background.png"
      },
      "groups": [
        {
          "id": "group_0_0",
          "kind": "list",
          "box": {},
          "items": [
            {
              "id": "item_0_0_0",
              "box": {},
              "raster": {
                "path": "assets/slide_0_item_0.png",
                "mode": "item"
              },
              "texts": [],
              "bullets": []
            }
          ],
          "segments": []
        }
      ],
      "texts": [],
      "rasterFallbacks": []
    }
  ]
}
```

The existing `texts`, `components`, and `bg_path` fields may remain for backward compatibility during migration.

## Screenshot Strategy

The exporter should stop treating the full slide screenshot as the only visual base for itemized regions.

For item-aware slides:

1. Hide `data-ppt-text` as today.
2. Hide item contents before capturing the slide background if the item is exported separately.
3. Capture the background and global atmosphere only.
4. Capture each `data-ppt-item` or `data-ppt-item-bg` separately.
5. Capture timeline `data-ppt-segment` regions separately when the segment is not part of the item screenshot.
6. Restore visibility after each capture to avoid cross-item contamination.

This prevents item visuals from being baked into the slide background. Deleting an item in PowerPoint will not reveal a stale bullet, card, node, or timeline marker underneath.

## Export Model

The PPTX exporter should add objects in this order:

1. Slide background.
2. Shared decorative rasters.
3. Track or connector segments.
4. Item rasters.
5. Item bullet/icon/image objects when separately extracted.
6. Native text overlays.

This preserves the visual stacking order while keeping item units individually selectable.

## List Behavior

Each list item should be exported as an independent visual unit.

Minimum behavior:

- Each item has its own raster image.
- Each item's text is overlaid as native PowerPoint text when marked with `data-ppt-text`.
- Bullet icons or images can be included inside the item raster for maximum fidelity.

Enhanced behavior:

- Bullet images are extracted as independent objects when marked with `data-ppt-bullet`.
- This allows users to edit or replace icons independently, but it is optional because visual fidelity is more important than icon editability.

## Timeline Behavior

Timeline export should avoid one monolithic timeline screenshot.

Minimum behavior:

- Timeline background or track can remain as one shared raster.
- Each node/item is a separate raster.
- Text inside each node/item is native PowerPoint text when marked.

Enhanced behavior:

- Connector lines are sliced into `data-ppt-segment` objects.
- Deleting one item should not leave that item's node or label in the background.
- Deleting middle items may still require manual adjustment of remaining connector segments.

## Fidelity Fallbacks

Every group should have a measured export confidence:

- `item-hybrid`: item slicing succeeded.
- `item-raster`: item slicing succeeded, text is not native.
- `group-raster`: group slicing failed, group exported as one raster.
- `slide-raster`: slide fallback, current behavior.

Fallback reasons should be written to the manifest:

- `missing-item-markers`
- `overlapping-items`
- `unsafe-css-effect`
- `zero-size-box`
- `capture-failed`
- `text-overlay-risk`

Fallbacks are not failures. They are required to protect visual quality.

## Quality Gate

Validation should check:

- Every `data-ppt-group` contains at least one `data-ppt-item`.
- Every item has a non-zero bounding box.
- Itemized groups are not still visible in the background capture.
- Manifest assets exist.
- Fallback reasons are recorded for any non-itemized group.

Later, visual regression testing can compare:

- React screenshot.
- Exported PPTX rendered to image.

If visual difference exceeds a configured threshold, the slide should fall back to raster-first export.

## File Size Strategy

The first file-size improvement comes from removing item pixels from full-slide backgrounds.

Additional improvements can be added after the item model is stable:

- Asset hash deduplication.
- Resize screenshots to displayed size.
- JPEG compression for opaque photo-like rasters.
- PNG only for transparent UI slices.
- Optional image compression pass after PPTX generation.

These optimizations must not introduce visible artifacts.

## Migration Strategy

The implementation should be incremental:

1. Keep the current raster-first path untouched.
2. Add item-level markers to the skill instructions and style guide.
3. Extend `builder.py` to emit group/item manifest data.
4. Extend `pptx_exporter.py` to place item rasters and item text.
5. Add quality gates and fallback reporting.
6. Update examples for list and timeline.
7. Only after stable item export, consider icon extraction and compression.

## Success Criteria

The first implementation is successful if:

- Existing decks still export with the current visual quality.
- A marked list can export each item as an independent selectable/copyable PPT object.
- A marked timeline can export each item or node as an independent selectable/copyable PPT object.
- Deleting a list or timeline item does not reveal stale item visuals in the background.
- Text remains native where `data-ppt-text` is used and visual risk is low.
- Unsafe or unsupported cases fall back to visually correct raster output.

## Explicit Trade-Off

This design prefers visual correctness over editability.

When there is a conflict:

1. Preserve visual fidelity.
2. Preserve item-level copy/delete behavior.
3. Preserve text editability.
4. Preserve icon or shape editability.

That priority order should guide all implementation decisions.
