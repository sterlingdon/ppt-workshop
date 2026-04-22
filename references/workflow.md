# Workflow

This is the operator runbook for the current React-to-PPTX pipeline.

## Current Model

The agent creates the content and slide code. The CLI handles workspace setup, slide activation, validation, browser extraction, and PPTX export.

```text
source material
  -> article_text.md
  -> deck_state.json
  -> analysis.json
  -> content_quality_report.json
  -> design_recommendation.json
  -> design_dna.json
  -> outline.json
  -> slide_blueprint.json
  -> slides/Slide_N.tsx + slides/index.ts
  -> review/full_deck.png + review/slides/*.png
  -> visual_review_report.json
  -> visual_validation_report.json
  -> layout_manifest.json + assets/
  -> presentation.pptx
```

## Workspace

Create one isolated project per deck:

```bash
python3 tools/ppt_workflow.py init --name "Deck Name"
```

Canonical workspace:

```text
output/projects/<project-id>/
├── project.json
├── article_text.md
├── deck_state.json
├── analysis.json
├── content_quality_report.json
├── design_recommendation.json
├── design_dna.json
├── outline.json
├── slide_blueprint.json
├── slides/
│   ├── Slide_1.tsx
│   ├── ...
│   └── index.ts
├── review/
│   ├── full_deck.png
│   └── slides/
├── visual_review_report.json
├── visual_validation_report.json
├── layout_manifest.json
├── presentation.pptx
└── assets/
```

## Shared State And Prompts

All three core agents must read `deck_state.json` before work and update it before handoff. Use the system prompts in `references/agent-prompts.md` and artifact formats in `references/artifact-templates.md`; do not improvise a new role prompt or artifact shape.

When assigning work to another agent, include the Shared Preamble plus that role's exact prompt from `references/agent-prompts.md`. Do not assume a delegated agent has read this skill, this workflow, or the operator's system prompt.

Before writing slide code, read `examples/react-slides/minimal-deck/README.md` and copy its import, `index.ts`, and marker patterns. The examples are the positive path; validators are only the fallback.

`deck_state.json` is the compact shared memory:

```json
{
  "project_id": "<project-id>",
  "source_title": "...",
  "source_type": "url|pdf|text|markdown|unknown",
  "audience": "...",
  "goal": "...",
  "core_thesis": "...",
  "language": "zh",
  "tone": "...",
  "must_emphasize": [],
  "must_cut": [],
  "key_data_points": [],
  "design_direction": "...",
  "current_stage": "ingest",
  "approved_artifacts": [],
  "blocking_findings": [],
  "handoff_notes": []
}
```

Handoff rule: a downstream agent must not reinterpret audience, goal, thesis, or content priorities unless it updates `deck_state.json` and regenerates affected downstream artifacts.

## Three Critical Agents

### 1. Content Quality Auditor

Purpose: make sure the future deck is worth making for a specific audience before any slide generation starts.

Inputs:

- `deck_state.json`
- `article_text.md`
- user request and audience hints

Outputs:

- updated `deck_state.json`
- `analysis.json`
- `content_quality_report.json`

Must verify:

- who the deck is for
- what the audience should believe, decide, or remember
- the one-sentence thesis
- the strongest arguments and data points
- what must be emphasized
- what should be cut as noise
- whether the planned deck angle serves the audience instead of blindly following the article

Blocking rule: if `content_quality_report.json` has blocking findings, fix the content analysis before Design DNA, outline, or slide coding.

### 2. PPT Generation Agent

Purpose: turn the approved content into a coherent, styled React deck.

This is the A-lens visual generation pass. It owns design direction, typography sizing, composition, and visual craft before any validator or export step runs.

Inputs:

- `deck_state.json`
- `analysis.json`
- `content_quality_report.json`
- `ui-ux-pro-max` skill access
- `references/ppt-visual-design.md`

Outputs:

- updated `deck_state.json`
- `design_recommendation.json`
- `design_dna.json`
- `outline.json`
- `slide_blueprint.json`
- `slides/Slide_N.tsx`
- `slides/index.ts`

Must do:

- read `references/ppt-visual-design.md` before design work
- invoke `ui-ux-pro-max` before writing `design_recommendation.json` or `design_dna.json`
- use `ui-ux-pro-max` for transferable web/product design principles that improve a fixed 16:9 PPT deck: visual hierarchy, type scale, palette, spacing, chart language, component polish, and avoid-rules
- explicitly tell `ui-ux-pro-max` not to produce website/app navigation, forms, responsive screens, hover states, or interaction flows unless the slide content itself is about a product UI
- save the distilled recommendation as `design_recommendation.json`
- map the external design recommendation to the closest local renderer preset
- map ui-ux-pro-max color and typography recommendations into `design_dna.json.token_extensions`, then apply those token overrides after `styleVars(preset)` in every slide root
- create an outline where every slide has a clear job
- create `slide_blueprint.json` before writing React code, including locked copy for every human-facing text string plus visual hierarchy, type-scale, focal-point, whitespace, and density decisions
- follow `examples/react-slides/minimal-deck/` for import paths, marker structure, and `index.ts`
- write slides that follow `design_dna.json` and preserve the approved content priorities
- keep React authoring as visual implementation; do not rewrite facts, titles, numbers, entities, or conclusions directly in TSX
- avoid generic web-card grids. Every slide needs presentation composition: a dominant idea, deliberate type scale, readable contrast, useful visual anchor, and controlled density

### 3. Visual Review/Validation Agent

Purpose: use AI visual judgment plus engineering checks to make the rendered deck presentation-grade.

Inputs:

- `deck_state.json`
- rendered browser preview
- `review/full_deck.png`
- `review/slides/*.png`
- `analysis.json`
- `content_quality_report.json`
- `design_dna.json`
- `outline.json`
- `slide_blueprint.json`

Outputs:

- updated `deck_state.json`
- `visual_review_report.json`
- `visual_validation_report.json`
- repaired React slides

Must do:

- read `references/ppt-visual-design.md` before reviewing
- inspect slides with an AI visual lens, not just a DOM validator
- use `review/full_deck.png` and `review/slides/*.png` as the review inputs
- reject weak, generic, cluttered, off-theme, preset-looking, article-like, or low-value slides, including slides with poor font sizing, weak hierarchy, cramped spacing, or no clear focal point
- repair React slides directly
- run engineering validation only after AI visual review has no blocking findings

## Stage Checklist

1. **Ingest**: extract clean source into `article_text.md` and initialize `deck_state.json`. Remove navigation, ads, boilerplate, and irrelevant appendix material.
2. **Content Quality Audit**: create `analysis.json` and `content_quality_report.json`. If the auditor sets `status: "needs_revision"`, repair the affected content artifacts, record resolved items in `resolution_log`, and re-run the audit until `status: "pass"`, `blocking_findings == 0`, `required_revisions == []`, and every `resolution_log` item is `resolved`.
3. **Design Intelligence**: read `references/ppt-visual-design.md`, then invoke `ui-ux-pro-max` with the approved deck domain, audience, tone, complexity, source thesis, and desired presentation goal. The query must state that `ui-ux-pro-max` is being used for transferable web/product design principles adapted to a fixed 16:9 PowerPoint deck, not for website or app UI generation. Save the distilled style, palette, typography, layout, chart, and UX-quality recommendations to `design_recommendation.json`.
4. **Design DNA**: create `design_dna.json` from the `ui-ux-pro-max` recommendations. Map the recommended visual direction to the closest local renderer preset, then add token extensions, visual recipes, slide-pattern assignments, and consistency rules. If token extensions override preset colors or fonts, React slides must spread those overrides after `styleVars(preset)`.
5. **Outline**: create `outline.json`. Every slide needs a type, title, and one sentence explaining its job. The outline must reflect `content_quality_report.json`.
6. **Slide Blueprint**: create `slide_blueprint.json` with each slide's role, key message, supporting evidence, `locked_copy`, flattened `required_texts`, visual anchor, layout pattern, type-scale guidance, hierarchy plan, whitespace strategy, density target, and marker requirements. `locked_copy` is what React renders; `required_texts` is only a validation-friendly flattening of the same copy.
7. **PPT Generation**: write slide components in `output/projects/<project-id>/slides/`. Each slide root is 1920x1080 and has `data-ppt-slide`.
8. **Structural Gate**: run `python3 tools/ppt_workflow.py validate --project <project-id>`.
9. **Render Review Assets**: run `python3 tools/ppt_workflow.py review-screenshots --project <project-id>`. This activates the project slides, opens the full-deck browser preview with `?extract=1`, writes `review/full_deck.png`, and writes one screenshot per slide to `review/slides/slide_XX.png`.
10. **AI Lens Review**: inspect the rendered browser deck as a visual director. Judge hierarchy, focal point, visual rhythm, brand consistency, information density, audience usefulness, and slide-to-slide pacing.
11. **AI Repair Loop**: write `visual_review_report.json`, repair React slides, record each fix in `repair_log`, regenerate `review/full_deck.png` and `review/slides/*.png`, then repeat AI review until `status: "pass"`, every slide has `passed: true`, `blocking_findings == 0`, and every `repair_log` item is `resolved`.
12. **Engineering Browser Gate**: run `python3 tools/ppt_workflow.py visual-validate --project <project-id>`. This is a rendered DOM visibility and overflow check, not an AI visual-quality review. Repair reported text, clipping, coverage, or overflow issues until `summary.failed == 0`. If the repair changes any slide source, return to Stage 9 and regenerate review screenshots before repeating AI Lens Review.
13. **Build**: run `python3 tools/ppt_workflow.py build --project <project-id>`.
14. **Final Check**: confirm `presentation.pptx`, `layout_manifest.json`, and `assets/` were regenerated after the final slide repairs.

## Command Semantics

- `init`: creates `project.json`, `assets/`, and `slides/`.
- `validate`: checks slide sources and marker basics. It does not judge narrative or design quality.
- `review-screenshots`: activates project slides and writes rendered screenshots for AI Lens Review.
- `visual-validate`: activates project slides, opens the browser preview, checks visible text, clipping, coverage, and overflow, then writes `visual_validation_report.json`. It is an engineering render gate, not a design critic, and does not satisfy the AI Lens Review.
- `build`: activates slides, requires passed content and AI visual gate reports, runs engineering validation, extracts layout/assets, exports PPTX, and validates final outputs.
- `activate`: copies project slides into `web/src/generated/slides/`.
- `snapshot-slides`: copies active generated slides back into the project.
- `extract`: activates slides and writes `layout_manifest.json` plus assets.
- `export`: builds PPTX from an existing manifest.

## Invalidation Rules

- Changing `analysis.json` or `content_quality_report.json` invalidates `design_recommendation.json`, `design_dna.json`, `outline.json`, `slide_blueprint.json`, downstream slide code, and visual validation.
- Changing `design_recommendation.json`, `design_dna.json`, `outline.json`, or `slide_blueprint.json` invalidates downstream slide code and visual validation.
- Changing any slide source invalidates review screenshots, `visual_review_report.json`, `visual_validation_report.json`, `layout_manifest.json`, `assets/`, and `presentation.pptx`.
- Regenerate invalidated downstream artifacts before export. Do not trust stale downstream artifacts.

## Completion Criteria

A deck is complete only when:

- The source material has been transformed into a clear audience-specific argument.
- `content_quality_report.json` has no blocking content findings.
- `content_quality_report.json.required_revisions` is empty and every `resolution_log` item is `resolved`.
- `design_recommendation.json` records the `ui-ux-pro-max` recommendation used for the deck.
- `design_dna.json` gives a consistent visual direction.
- Every slide has a clear job and uses the same visual system without looking like an unadapted website/app screen.
- `slide_blueprint.json` exists and every slide has a build plan for copy, visual hierarchy, type scale, focal point, whitespace, density, and export markers.
- `review/full_deck.png` and one `review/slides/slide_XX.png` per slide were generated after the final slide source change.
- `visual_review_report.json.status` is `"pass"` and has no blocking AI visual findings.
- Every `visual_review_report.json` slide has `passed: true` and every `repair_log` item is `resolved`.
- `visual_validation_report.json.summary.failed` is `0`.
- `presentation.pptx` has been rebuilt from the approved slide sources.
