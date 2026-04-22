# Visual Fidelity Reference

Visual fidelity is the product floor.

Priority order:

1. Preserve visual fidelity.
2. Preserve item-level copy/delete behavior.
3. Preserve text editability.
4. Preserve icon or shape editability.

Fallbacks are successful safety behavior, not failures.

## Rules

- Do not reduce visual complexity just to make PPT objects native.
- Use raster capture for blur, glow, mask, rich shadow, complex SVG, and photo-like effects.
- Use native text only when it does not visibly degrade the slide.
- If item slicing creates visible mismatch, fall back to group-raster or slide-raster.

## Acceptable Tradeoff

A visually correct raster object is better than a visually degraded editable object.
