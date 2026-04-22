# Deck Contract

The deck contract is the shared planning context for content, design, slide authoring, and visual review.

In the current pipeline the contract is eight files:

- `deck_state.json`: compact shared state for all core agents.
- `analysis.json`: what the deck says.
- `content_quality_report.json`: why this deck is valid for the intended audience and what must be emphasized or cut.
- `design_recommendation.json`: external design-intelligence recommendation from `ui-ux-pro-max`.
- `design_dna.json`: how the deck looks and behaves visually.
- `outline.json`: how the story unfolds slide by slide.
- `slide_blueprint.json`: how each slide will be built before JSX authoring starts.
- `visual_review_report.json`: AI visual review and repair record.

## `deck_state.json`

This is the handoff state. Every core agent reads it first and updates it before passing work downstream.

Must include:

- `project_id`
- `source_title`
- `source_type`
- `audience`
- `goal`
- `core_thesis`
- `language`
- `tone`
- `must_emphasize`
- `must_cut`
- `key_data_points`
- `design_direction`
- `current_stage`
- `approved_artifacts`
- `blocking_findings`
- `handoff_notes`

Do not let downstream agents silently reinterpret shared state. If audience, goal, thesis, content priorities, or design direction changes, update `deck_state.json` and regenerate affected artifacts.

## `analysis.json`

Must answer:

- Who is the audience?
- What should they believe, decide, or remember?
- What is the one-sentence thesis?
- Which facts, statistics, quotes, and entities are strong enough to appear in the deck?
- What language and complexity level should the deck use?

## `design_recommendation.json`

Must be created after `content_quality_report.json` passes and before `design_dna.json`.

The recommendation must come from invoking or applying `ui-ux-pro-max` using the deck's:

- domain
- audience
- tone
- complexity
- thesis
- desired reader decision or takeaway
- content priorities from `content_quality_report.json`

Must preserve the external design-intelligence step before the recommendation is mapped into the local renderer.

`design_recommendation.json` must define:

- `project_id`
- `source_skill`: `ui-ux-pro-max`
- `query`: the deck-specific design request sent to the skill.
- `recommended_style`
- `rationale`
- `palette`
- `typography`
- `layout_guidance`
- `chart_guidance`
- `motion_guidance`
- `avoid`

Do not skip this file. Without it, reviewers cannot tell whether `design_dna.json` came from real design intelligence or from a local preset guess.

## `design_dna.json`

Must be created after `content_quality_report.json` passes and after `design_recommendation.json` has been saved.

Use the external recommendation as the creative source of truth. The local renderer preset is only an implementation scaffold.

`design_dna.json` must define:

- `source_skill`: `ui-ux-pro-max`
- `recommendation_summary`: concise summary of the style, palette, typography, layout, and chart guidance received.
- `preset`: one of the style presets in `web/src/styles/presets.ts`, chosen as the closest scaffold to the external recommendation.
- `token_extensions`: deck-specific `--ppt-*` variables.
- `visual_language`: card, heading, accent, background, and image/diagram recipes.
- `slide_pattern_assignments`: which preset pattern each slide type should use.
- `consistency_rules`: hard rules the slide author must not violate.
- `visual_mandates`: minimum expectations such as metric anchors, chart treatment, or background blocks.

Use `design_dna.json` before writing any slide JSX. It prevents the deck from becoming a collection of unrelated pages.

If `ui-ux-pro-max` recommends a style that does not exactly match a local preset, keep the recommendation and map it to the nearest preset:

- dark technical / AI / cybersecurity / luminous interfaces -> `aurora-borealis`
- business / finance / startup / high-contrast decision decks -> `bold-signal`
- editorial / education / culture / warm report decks -> `editorial-ink`

The preset must not override the external recommendation. Use `token_extensions`, `visual_language`, and `consistency_rules` to carry the recommendation into the React slides.

## `outline.json`

Must define:

- `theme`: the active style preset.
- `style_constraints`: global visual constraints.
- `slides`: ordered slide descriptors.

Each slide descriptor needs:

- `index`
- `type`
- `title`
- `needs_image`
- `notes`: one sentence stating the slide's job.

The outline must reflect `content_quality_report.json`: it should emphasize the approved key points and data, exclude `must_cut` material, and give every slide an audience-facing role.

## `slide_blueprint.json`

Must be created after `outline.json` and before React slide authoring.

Each slide blueprint must define:

- `index`
- `type`
- `slide_role`
- `key_message`
- `supporting_evidence`
- `required_texts`
- `must_not_include`
- `visual_anchor`
- `layout_pattern`
- `data_ppt_requirements`

The blueprint is the execution handoff to the slide author. It must include `locked_copy` for every human-facing string. `required_texts` may flatten that copy for validation, but the React author should render `locked_copy` rather than rewriting text while coding.

## Review Screenshots And `visual_review_report.json`

`review/full_deck.png` and one `review/slides/slide_XX.png` per slide must be generated after the latest slide source change.

`visual_review_report.json` must be written by the Visual Review/Validation Agent after inspecting those rendered screenshots.

Must define:

- `project_id`
- `review_type`: `ai_lens_visual_review`
- `gate_type`: `ai_visual_quality_review`
- `status`: `pass` or `blocked`
- `review_assets`
- `blocking_findings`
- per-slide `passed`, `visual_score`, `findings`, and `repairs`

This is not the Python engineering validator. It records AI visual judgment and repair decisions. `visual_validation_report.json` cannot replace it.

## Update Rules

- If the audience, thesis, or key evidence changes, update `analysis.json` and revisit the outline.
- If content emphasis or exclusion changes, update `content_quality_report.json` and regenerate downstream files.
- If external design guidance changes, update `design_recommendation.json`, then regenerate `design_dna.json`, `outline.json`, `slide_blueprint.json`, slides, and visual review.
- If visual tone, preset, tokens, or layout recipes change, update `design_dna.json` and repair all affected slides.
- If slide order, roles, or count changes, update `outline.json`, `slide_blueprint.json`, and affected slides.
- If slide sources change, regenerate review screenshots, `visual_review_report.json`, engineering validation, manifest, assets, and PPTX.
- After any contract change, rerun validation and rebuild the PPTX.
