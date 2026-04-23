# PPT Visual Design Rules

Use this reference before `design_recommendation.json`, `design_dna.json`, `outline.json`, `slide_blueprint.json`, and React slide authoring. It converts product/UI design intelligence into presentation-grade slide craft.

## `ui-ux-pro-max` Adaptation

Invoke the available `ui-ux-pro-max` design-intelligence entry point as a design director, not as a website generator. Prefer a slides/design-oriented entry point when the environment exposes variants such as `ui-ux-pro-max:ckm:slides`; otherwise use the closest available `ui-ux-pro-max` source and record its exact name in `design_recommendation.json.source_skill`.

Ask for transferable principles:

- visual hierarchy and focal point strategy
- color system and contrast pairs
- display/body/number typography choices
- spacing scale, grid, and density
- dashboard/chart language for data slides
- component styling rules for cards, panels, callouts, and diagrams
- avoid-list for the deck's audience and topic

Do not ask it to design navigation, forms, responsive app screens, CTAs, hover states, mobile breakpoints, or app interaction flows unless the slide content specifically depicts a product UI. Translate any web/app advice into fixed 16:9 slide decisions.

`design_recommendation.json.query` must explicitly say:

```text
Use ui-ux-pro-max for transferable web/product design principles, then adapt them to a 16:9 PowerPoint deck. Do not produce a website/app layout.
```

## Slide Craft Baseline

Each slide must have one dominant idea. If two ideas compete, split or reframe the slide.

Use these fixed-slide guidelines unless the content clearly requires an exception:

- Canvas: 1920x1080, with a stable outer margin of roughly 96-140 px.
- Title size: usually 56-88 px; title-slide display type may reach 96-132 px.
- Section/kicker labels: 18-26 px, not all-caps unless the text is short.
- Body copy: usually 28-38 px. Dense footnotes may go to 20-24 px only when non-essential.
- Metric numbers: 88-180 px with short labels nearby.
- Line height: 1.05-1.15 for display, 1.2-1.35 for body.
- Text blocks: prefer 2-4 lines. Avoid long paragraphs and article-like narration.
- Contrast: all important text must be readable in the rendered screenshot without zooming.
- Density: a normal slide should contain 3-7 meaningful visual elements, not a wall of cards.

Typography must be intentional. Use a display/body/number role system, consistent weights, and tabular or mono figures for metrics. Do not scale everything uniformly; establish clear rank between headline, evidence, labels, and supporting notes.

## Layout Principles

Choose a layout from the slide's job, not from habit:

- decision or thesis: strong title plus one visual anchor
- statistics: one dominant number or chart, with minimal explanatory copy
- comparison: two or three columns with symmetric reading paths
- process/timeline: visible progression, numbered stages, connectors, and endpoint emphasis
- framework: diagram or matrix before bullets
- implication/action: grouped choices with clear priority

Avoid generic web-page composition in PPT:

- no navbar/sidebar/footer chrome unless the slide is about a UI
- no stacked landing-page hero sections
- no repeated identical cards when the content needs hierarchy
- no mobile-responsive instructions in slide plans
- no hover or interaction state requirements

## Visual System Requirements

`design_dna.json` should turn the recommendation into enforceable rules:

- `theme_tokens`: complete `--ppt-*` CSS variables for the deck.
- `visual_language`: concrete recipes for panels, headings, accents, diagrams, images, and charts.
- `signature_visual_moves`: 2-5 distinctive visual devices that make this deck feel designed for the source material.
- `slide_pattern_assignments`: optional custom pattern names across the deck.
- `consistency_rules`: rules the slide author must obey in JSX.
- `visual_mandates`: measurable expectations for focal points, data treatment, and minimum visual anchors.

## Review Criteria

Reject or repair a slide when any of these are true:

- no clear focal point within two seconds
- headline and body have similar visual weight
- important text is too small, clipped, low-contrast, or crowded
- slide feels like a raw article summary
- cards or panels repeat without priority or rhythm
- colors feel generic or disconnected from the source material
- chart/data treatment is decorative but not explanatory
- visuals are attractive but do not help the audience understand the message

Engineering validation can pass while these issues remain. AI visual review must still block export until the rendered screenshots look presentation-grade.
