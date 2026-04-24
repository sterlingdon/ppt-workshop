# Visual SOP

This is the visual operating procedure for deck generation. The goal is not "clean enough" slides; the goal is a deck with a point of view, sequence rhythm, and assets that earn their space.

## Visual Pipeline

1. Lock the audience and thesis first in `analysis.json` and `deck_state.json`.
2. Invoke `ui-ux-pro-max`, then write `design_recommendation.json` as a transferable design contract, not loose inspiration.
3. Explore 2-3 directions in `concept_directions.json`; reject safe variants explicitly.
4. Lock `design_dna.json`, including `font_preset`, `font_strategy`, anti-patterns, and signature moves.
5. Write `slide_blueprint.json` with `visual_goal`, `wow_goal`, `asset_intent`, and the intended sequence rhythm.
6. Write `visual_asset_research.json` before route execution. Research should define what the image or diagram should feel like, what to reject, and what composition is needed.
7. Convert research into `visual_asset_plan.json`. Each slot must record route, ranking criteria, placement contract, and fallback strategy.
8. Materialize `visual_asset_manifest.json`. Generation routes should produce multiple composition variants, rank them against the slide intent, record why the winner won, and apply fallback routes automatically if the primary route is blocked.
9. Render slides, capture screenshots, and run AI or human visual review from the screenshots, not from code.

## Visual Gates

- `design_recommendation.json` must preserve palette, typography, image mood, icon language, and anti-patterns from `ui-ux-pro-max`.
- `concept_directions.json` must include at least one compositionally different option, not just palette swaps.
- `slide_blueprint.json` must identify the pages that carry the deck's visual memory.
- `visual_asset_research.json` must exist before an image-generation route is treated as ready.
- `visual_asset_manifest.json` must show candidate ranking and whether fallback was applied.
- `visual_review_report.json` must reject decks that are correct but interchangeable with a generic template.

## Asset Decisions

- Use `image_generation` when the slide needs realism, atmosphere, or a scene that should be art-directed to the deck rather than merely found.
- Use `diagram/svg` when the slide's job is to explain a relationship, mechanism, or framework.
- Use `chart` when the visual anchor is evidence.
- Use `none` only when typography can carry the page without looking empty.

If a generation route fails, do not insert weak placeholder art. Switch to a premium fallback such as typography-plus-diagram, typography-plus-shape composition, or evidence-led layout.

## Typography SOP

- Choose a `font_preset` before slide implementation. Fonts are a deck-level system, not a final polish step.
- Use `font_strategy` only to override or refine the preset. Do not leave roles unspecified.
- Check language coverage for Chinese and English before preview.
- If PPT native text fidelity is weak for a hero title, mark that role as `raster_ok` intentionally instead of silently downgrading the design.

## Known Pitfalls

- Do not start from JSX. Once slide code starts first, the deck collapses into local optimizations and repeated web cards.
- Do not run `review-screenshots`, `visual-validate`, and `build` in parallel. They compete for the active renderer slot.
- Do not confuse "the model returned an image" with "the deck now has a strong image". Generation still needs art direction, ranking, and review.
- Do not assume one visual system means one repeated layout. Consistency is not repetition.
