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
- `active_role`
- `current_stage`
- `approved_artifacts`
- `blocking_findings`
- `handoff_notes`

Do not let downstream agents silently reinterpret shared state. If audience, goal, thesis, content priorities, or design direction changes, update `deck_state.json` and regenerate affected artifacts.

`active_role` records which role prompt is governing the current artifact. Update it whenever the main agent switches roles or work is delegated to a role-specific agent.

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

Must preserve the external design-intelligence step before the recommendation is converted into the deck's design DNA.

`ui-ux-pro-max` is used here as a transferable design intelligence source, not as a literal website/app builder. The query must ask it to adapt web/product design principles to a fixed 16:9 PowerPoint deck and must not request navigation, forms, responsive app screens, hover states, or app interaction flows unless those are part of the slide subject.

`design_recommendation.json` must define:

- `project_id`
- `source_skill`: `ui-ux-pro-max`
- `query`: the deck-specific design request sent to the skill, including the fixed 16:9 PPT adaptation instruction.
- `recommended_style`
- `rationale`
- `palette`
- `typography`
- `ppt_adaptation`: focal point strategy, type-scale guidance, density guidance, and fixed-slide translation notes.
- `layout_guidance`
- `chart_guidance`
- `motion_guidance`
- `avoid`

Do not skip this file. Without it, reviewers cannot tell whether `design_dna.json` came from real design intelligence or from a local template guess.

## `design_dna.json`

Must be created after `content_quality_report.json` passes and after `design_recommendation.json` has been saved.

Use the external recommendation as the creative source of truth.

`design_dna.json` must define:

- `source_skill`: `ui-ux-pro-max`
- `recommendation_summary`: concise summary of the style, palette, typography, layout, and chart guidance received.
- `visual_direction`: a short named direction specific to the source material.
- `renderer_contract`: state that generated slides use `--ppt-*` variables directly from this design DNA.
- `theme_tokens`: complete deck-specific `--ppt-*` variables.
- `visual_language`: card, heading, accent, background, and image/diagram recipes.
- `signature_visual_moves`: distinctive visual devices that make this deck feel designed, not templated.
- `slide_pattern_assignments`: optional custom pattern names for recurring slide jobs.
- `consistency_rules`: hard rules the slide author must not violate.
- `type_scale`: deck-level title, label, body, and metric size ranges.
- `composition_rules`: deck-level margin, focal point, density, and whitespace rules.
- `visual_mandates`: minimum expectations such as metric anchors, chart treatment, or background blocks.

Use `design_dna.json` before writing any slide JSX. It prevents the deck from becoming a collection of unrelated pages.

Use `theme_tokens`, `visual_language`, `signature_visual_moves`, and `consistency_rules` to carry the recommendation into the React slides.

## `outline.json`

Must define:

- `theme`: the design DNA direction.
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
- `visual_hierarchy`: primary focus, secondary focus, and reading order.
- `type_scale`: intended title/body/metric/label sizing for that slide.
- `composition`: outer margin, whitespace strategy, density target, and rhythm notes.
- `data_ppt_requirements`

The blueprint is the execution handoff to the slide author. It must include `locked_copy` for every human-facing string. `required_texts` may flatten that copy for validation, but the React author should render `locked_copy` rather than rewriting text while coding.

The blueprint must not leave typography and composition to chance. If a slide has no clear focal point, no type-scale plan, or only says "card grid" without priority, it is not ready for React authoring.

## Review Screenshots And `visual_review_report.json`

`review/full_deck.png` and one `review/slides/slide_XX.png` per slide must be generated after the latest slide source change.

`visual_review_report.json` must be written by the Visual Review/Validation Agent after inspecting those rendered screenshots.

Must define:

- `project_id`
- `review_type`: `ai_lens_visual_review`
- `gate_type`: `ai_visual_quality_review`
- `status`: `pass` or `blocked`
- `review_assets`
- `review_capability`: real review method, image-input capability, and inspected screenshot paths
- `blocking_findings`
- per-slide `passed`, `visual_score`, `findings`, and `repairs`

This is not the Python engineering validator. It records AI visual judgment and repair decisions. `visual_validation_report.json` cannot replace it. If the active agent cannot inspect images, write a blocked report instead of pretending the rendered screenshots were reviewed.

## Update Rules

- If the audience, thesis, or key evidence changes, update `analysis.json` and revisit the outline.
- If content emphasis or exclusion changes, update `content_quality_report.json` and regenerate downstream files.
- If external design guidance changes, update `design_recommendation.json`, then regenerate `design_dna.json`, `outline.json`, `slide_blueprint.json`, slides, and visual review.
- If visual tone, theme tokens, signature visual moves, or layout recipes change, update `design_dna.json` and repair all affected slides.
- If slide order, roles, or count changes, update `outline.json`, `slide_blueprint.json`, and affected slides.
- If slide sources change, regenerate review screenshots, `visual_review_report.json`, engineering validation, manifest, assets, and PPTX.
- After any contract change, rerun validation and rebuild both the PPTX and `presentation-html/` static-site output.
