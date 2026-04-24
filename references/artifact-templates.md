# Artifact Templates

Use these templates as the contract for generated project artifacts. Keep JSON valid and compact. If a field is unknown, write an explicit empty value and add a blocking finding instead of guessing.

## `deck_state.json`

Created during ingest and updated by every core agent.

```json
{
  "project_id": "<project-id>",
  "source_title": "",
  "source_type": "unknown",
  "audience": "",
  "goal": "",
  "core_thesis": "",
  "language": "zh",
  "tone": "",
  "must_emphasize": [],
  "must_cut": [],
  "key_data_points": [],
  "design_direction": "",
  "active_role": "none",
  "current_stage": "ingest",
  "approved_artifacts": [],
  "blocking_findings": [],
  "handoff_notes": []
}
```

Allowed `current_stage` values:

- `ingest`
- `content_quality_audit`
- `design_intelligence`
- `design_dna`
- `outline`
- `slide_blueprint`
- `ppt_generation`
- `structural_validation`
- `render_review_assets`
- `ai_visual_review`
- `engineering_validation`
- `export`
- `complete`

Allowed `active_role` values:

- `none`
- `content_quality_auditor`
- `ppt_generation_agent`
- `visual_review_validation_agent`

Update `active_role` at every role activation. Set it to the role currently governing the artifact being written; reset to `none` only when the deck is complete or paused outside a role.

`deck_state.blocking_findings` is a list of unresolved handoff issues. Report files such as `content_quality_report.json` and `visual_review_report.json` use numeric `blocking_findings` counts.

## `analysis.json`

```json
{
  "domain": "business",
  "title": "<deck-title>",
  "summary": "",
  "audience": "",
  "goal": "",
  "core_thesis": "",
  "key_points": ["<key-point>"],
  "statistics": [
    {
      "value": "",
      "label": "",
      "context": "",
      "source_evidence": ""
    }
  ],
  "quotes": [
    {
      "text": "",
      "author": "",
      "role": "",
      "source_evidence": ""
    }
  ],
  "entities": [],
  "complexity": "intermediate",
  "visual_direction": "",
  "language": "zh",
  "tone": ""
}
```

## `content_quality_report.json`

```json
{
  "project_id": "<project-id>",
  "review_type": "content_quality_audit",
  "status": "pass",
  "audience": "",
  "goal": "",
  "core_thesis": "",
  "deck_angle": "",
  "must_emphasize": [],
  "must_cut": [],
  "key_data_points": [],
  "slide_worthy_arguments": [
    {
      "argument": "",
      "why_it_matters_to_audience": "",
      "supporting_evidence": ""
    }
  ],
  "blocking_findings": 0,
  "required_revisions": [],
  "resolution_log": [],
  "resolution_notes": "",
  "findings": []
}
```

Blocking findings include unknown audience, unclear goal, weak thesis, invented data, omitted key point, or an article-summary angle.

Use `examples/reports/content-quality-report.pass.json` and `examples/reports/content-quality-report.needs-revision.json` as the expected shape. A report with `status` other than `"pass"`, `blocking_findings` greater than `0`, non-empty `required_revisions`, or unresolved `resolution_log` items must be resolved before design or slide coding.

When the auditor requests changes, keep the loop explicit:

1. Auditor writes `status: "needs_revision"`, blocking findings, and `required_revisions`.
2. Execution agent updates the affected artifacts.
3. Execution agent records each fix in `resolution_log` with `status: "resolved"`, `changed_artifacts`, and evidence.
4. Auditor rechecks the updated artifacts, clears `required_revisions`, sets `status: "pass"`, and keeps the resolved log as proof.

## `design_recommendation.json`

Raw design-intelligence output distilled from the available `ui-ux-pro-max` entry point. This file preserves the external recommendation before it is converted into `design_dna.json`.

The `query` must make the adaptation explicit: use `ui-ux-pro-max` for transferable web/product design principles, then adapt them to a fixed 16:9 PowerPoint deck. Do not ask for a website or app layout.

Set `source_skill` to the exact design-intelligence entry point used, such as `ui-ux-pro-max`, `ui-ux-pro-max:ckm:slides`, or the closest available `ui-ux-pro-max:*` variant.

```json
{
  "project_id": "<project-id>",
  "source_skill": "ui-ux-pro-max",
  "query": "Use ui-ux-pro-max for transferable web/product design principles, then adapt them to a 16:9 PowerPoint deck. Do not produce a website/app layout. Deck context: ...",
  "recommended_style": "",
  "rationale": "",
  "palette": {
    "background": "",
    "surface": "",
    "primary": "",
    "secondary": "",
    "accent": "",
    "text": "",
    "muted": ""
  },
  "typography": {
    "display": "",
    "body": "",
    "number": "",
    "font_family_guidance": {
      "display_role": "",
      "body_role": "",
      "number_role": "",
      "tone": "",
      "language_coverage_notes": ""
    }
  },
  "asset_direction": {
    "image_mood": [],
    "visual_cues": [],
    "generation_cues": [],
    "icon_style": "",
    "diagram_style": ""
  },
  "ppt_adaptation": {
    "focal_point_strategy": "",
    "type_scale_guidance": "",
    "density_guidance": "",
    "fixed_16_9_translation_notes": "",
    "deck_rhythm_guidance": ""
  },
  "layout_guidance": [],
  "chart_guidance": [],
  "motion_guidance": [],
  "avoid": []
}
```

## `concept_directions.json`

```json
{
  "project_id": "<project-id>",
  "selected_direction": "editorial-contrast",
  "directions": [
    {
      "name": "editorial-contrast",
      "rationale": "",
      "composition_archetypes": {
        "opener": "",
        "section": "",
        "evidence": "",
        "closing": ""
      },
      "typography_posture": "",
      "image_posture": "",
      "signature_moves": []
    }
  ],
  "rejected_directions": [
    {
      "name": "safe-enterprise-grid",
      "rejection_reason": ""
    }
  ]
}
```

## `design_dna.json`

```json
{
  "source_skill": "ui-ux-pro-max",
  "recommendation_summary": "",
  "visual_direction": "",
  "font_preset": "editorial_publishing|business_strategy|education_family|tech_future",
  "renderer_contract": "Use --ppt-* CSS variables directly from this design DNA.",
  "font_display": "",
  "font_body": "",
  "font_strategy": {
    "display": {
      "family": "",
      "source": "local|download|bundled",
      "fallback_chain": [],
      "ppt_fidelity_mode": "native|raster_ok",
      "coverage_notes": ""
    },
    "body": {
      "family": "",
      "source": "local|download|bundled",
      "fallback_chain": [],
      "ppt_fidelity_mode": "native|raster_ok",
      "coverage_notes": ""
    },
    "number": {
      "family": "",
      "source": "local|download|bundled",
      "fallback_chain": [],
      "ppt_fidelity_mode": "native|raster_ok",
      "coverage_notes": ""
    }
  },
  "theme_tokens": {
    "--ppt-bg": "",
    "--ppt-surface": "",
    "--ppt-surface-strong": "",
    "--ppt-primary": "",
    "--ppt-secondary": "",
    "--ppt-accent": "",
    "--ppt-text": "",
    "--ppt-muted": "",
    "--ppt-border": "",
    "--ppt-font-display": "",
    "--ppt-font-body": "",
    "--ppt-chart-1": "",
    "--ppt-chart-2": "",
    "--ppt-chart-3": ""
  },
  "visual_language": {
    "card_recipe": "",
    "heading_recipe": "",
    "accent_bar_recipe": "",
    "bg_decoration": "",
    "diagram_recipe": "",
    "chart_recipe": "",
    "icon_recipe": "",
    "image_mood": []
  },
  "signature_visual_moves": [],
  "slide_pattern_assignments": {},
  "consistency_rules": [],
  "type_scale": {
    "title_px": "56-88",
    "section_label_px": "18-26",
    "body_px": "28-38",
    "metric_px": "88-180"
  },
  "composition_rules": {
    "outer_margin_px": "96-140",
    "focal_point_rule": "",
    "density_rule": "",
    "whitespace_rule": ""
  },
  "visual_mandates": {
    "min_ppt_bg_blocks_per_slide": 1,
    "stats_slides_require": "",
    "concept_slides_require": "",
    "quote_slides_require": "",
    "image_coverage_min": 0.3
  }
}
```

Every non-empty `theme_tokens` value must be reflected in React slide theme variables. The slide root should apply `theme_tokens` directly.

`type_scale` and `composition_rules` are required design decisions even if the exact numeric values vary by deck. They prevent agents from leaving font size, hierarchy, and spacing to improvised JSX.

## `outline.json`

```json
{
  "theme": "",
  "style_constraints": {
    "heading_emphasis": "solid",
    "card_style": "solid-surface",
    "stat_style": "accent-color",
    "bullet_style": "dot",
    "divider_style": "none",
    "image_style_fingerprint": ["editorial", "high-contrast"]
  },
  "slides": [
    {
      "index": 1,
      "type": "title",
      "title": "<title-slide>",
      "needs_image": false,
      "notes": ""
    },
    {
      "index": 2,
      "type": "exec-summary",
      "title": "<executive-summary>",
      "needs_image": false,
      "notes": ""
    },
    {
      "index": 3,
      "type": "stats-callout",
      "title": "<key-data>",
      "needs_image": false,
      "notes": ""
    },
    {
      "index": 4,
      "type": "two-column",
      "title": "<argument-one>",
      "needs_image": false,
      "notes": ""
    },
    {
      "index": 5,
      "type": "comparison",
      "title": "<argument-two>",
      "needs_image": false,
      "notes": ""
    },
    {
      "index": 6,
      "type": "timeline",
      "title": "<development-path>",
      "needs_image": false,
      "notes": ""
    },
    {
      "index": 7,
      "type": "card-grid-3",
      "title": "<implications>",
      "needs_image": false,
      "notes": ""
    },
    {
      "index": 8,
      "type": "conclusion",
      "title": "<final-takeaway>",
      "needs_image": false,
      "notes": ""
    }
  ]
}
```

The real `outline.json` must satisfy `schemas/outline.schema.json`, including 8-25 slide descriptors.

## `slide_blueprint.json`

Required before React slide authoring. This is the page-by-page build plan.

```json
{
  "project_id": "<project-id>",
  "slides": [
    {
      "index": 1,
      "type": "title",
      "slide_role": "",
      "key_message": "",
      "supporting_evidence": [],
      "locked_copy": {
        "title": "",
        "subtitle": "",
        "body": [],
        "callouts": [],
        "labels": []
      },
      "required_texts": [],
      "must_not_include": [],
      "critical_visual": false,
      "visual_goal": "",
      "wow_goal": "",
      "visual_anchor": {
        "kind": "big-number",
        "description": ""
      },
      "layout_pattern": "",
      "visual_hierarchy": {
        "primary_focus": "",
        "secondary_focus": "",
        "reading_order": []
      },
      "type_scale": {
        "title_px": "",
        "body_px": "",
        "metric_px": "",
        "label_px": ""
      },
      "composition": {
        "outer_margin_px": "",
        "whitespace_strategy": "",
        "density_target": "",
        "rhythm_notes": ""
      },
      "asset_intent": {
        "visual_role": "",
        "asset_goal": "",
        "candidate_asset_types": [],
        "must_show": [],
        "must_avoid": [],
        "wow_goal": "",
        "composition_hint": "",
        "dominant_zone": "",
        "visual_cues": [],
        "generation_cues": [],
        "icon_style": ""
      },
      "data_ppt_requirements": {
        "needs_group": false,
        "needs_item_markers": false,
        "native_text_priority": "high",
        "raster_fallback_allowed": true
      }
    }
  ]
}
```

`locked_copy` is the source of truth for human-facing React slide text. `required_texts` may duplicate or flatten this copy for validation, but React slide code must not invent or rewrite core copy outside the blueprint. If the copy needs editorial repair, update `slide_blueprint.json` before changing `Slide_N.tsx`.

`visual_hierarchy`, `type_scale`, and `composition` are required authoring inputs. A blueprint that only names a layout pattern is incomplete; it must tell the slide author what should dominate, how large the main text classes should be, and how dense the slide should feel.

## `visual_asset_research.json`

Write this before `visual_asset_plan.json` whenever the deck expects image generation, charting, or any non-trivial diagram route.

```json
{
  "project_id": "<project-id>",
  "deck_visual_strategy": "",
  "slides": [
    {
      "slide": 1,
      "title": "",
      "primary_route": "image_generation",
      "research_query": "",
      "research_tags": [],
      "visual_motif": "",
      "desired_composition": "",
      "desired_mood": "",
      "reject_if": [],
      "sourcing_guidance": []
    }
  ]
}
```

This artifact exists to decide what "the right picture" or "the right diagram posture" looks like before generators or local renderers are called.

## `visual_asset_plan.json`

```json
{
  "project_id": "<project-id>",
  "research_artifact": "visual_asset_research.json",
  "slides": [
    {
      "slide": 1,
      "title": "",
      "visual_goal": "",
      "wow_goal": "",
      "rollback_scope_default": "slide_local",
      "shared_visual_dependencies": [],
      "asset_slots": [
        {
          "slot": "primary",
          "primary_route": "image_generation",
          "fallback_routes": ["diagram/svg"],
          "candidate_count": 5,
          "independent_asset_review": true,
          "critical_visual": true,
          "research_query": "",
          "research_tags": [],
          "selection_criteria": [],
          "placement_contract": {
            "mode": "dominant",
            "dominant_zone": "full-bleed",
            "crop_preference": "cover",
            "content_priority": "preserve_text_clear_space",
            "composition_hint": ""
          },
          "fallback_strategy": "",
          "premium_fallback_required": true
        }
      ]
    }
  ]
}
```

## `visual_asset_manifest.json`

```json
{
  "project_id": "<project-id>",
  "assets": [
    {
      "asset_id": "slide-1-primary",
      "slide": 1,
      "slot": "primary",
      "asset_type": "image_generation",
      "source_type": "image_generation",
      "source_provider": "gemini",
      "prompt_or_query": "",
      "candidate_assets": [],
      "selected_asset": {},
      "candidate_ranking": [
        {
          "candidate_id": "",
          "rank": 1,
          "total_score": 9.2,
          "criteria_scores": {
            "goal_match": 9.3,
            "composition_fit": 9.1,
            "distinctiveness": 9.0,
            "implementation_confidence": 9.4
          },
          "notes": ""
        }
      ],
      "selection_rationale": "",
      "review_status": "approved",
      "research_summary": {
        "research_query": "",
        "research_tags": [],
        "desired_composition": "",
        "reject_if": []
      },
      "placement_decision": {
        "mode": "dominant",
        "dominant_zone": "full-bleed",
        "crop_preference": "cover",
        "content_priority": "preserve_text_clear_space",
        "resolved_route": "image_generation",
        "critical_visual": true
      },
      "fallback_applied": {
        "used": false,
        "from_route": "image_generation",
        "to_route": "image_generation",
        "reason": ""
      },
      "license_metadata": {},
      "resolution_metadata": {},
      "rollback_scope": "slide_local"
    }
  ]
}
```

## `visual_review_report.json`

AI Lens Review output.

```json
{
  "project_id": "<project-id>",
  "review_type": "ai_lens_visual_review",
  "gate_type": "ai_visual_quality_review",
  "status": "pass",
  "review_assets": {
    "full_deck_screenshot": "review/full_deck.png",
    "slide_screenshots_dir": "review/slides"
  },
  "review_context": {
    "context_sources": [
      "analysis.json",
      "design_dna.json",
      "outline.json",
      "slide_blueprint.json"
    ],
    "rubric_version": "visual_review_rubric_v1",
    "critical_slide_policy_version": "critical_visual_policy_v1"
  },
  "review_capability": {
    "method": "vision_model",
    "image_input": true,
    "model": "vision-capable-model-name",
    "inspected_assets": [
      "review/full_deck.png",
      "review/slides/slide_01.png"
    ],
    "notes": ""
  },
  "blocking_findings": 0,
  "repair_log": [],
  "slides": [
    {
      "slide": 1,
      "passed": true,
      "visual_score": 9,
      "visual_craft_score": 9.1,
      "strategic_clarity_score": 9.0,
      "hard_blockers": [],
      "criteria_scores": {
        "focal_point": 9,
        "hierarchy": 9,
        "composition": 9
      },
      "critical_visual": true,
      "wow_passed": true,
      "review_scope": "slide_local",
      "rollback_recommendation": "none",
      "findings": [],
      "repairs": []
    }
  ]
}
```

Use `examples/reports/visual-review-report.pass.json` and `examples/reports/visual-review-report.blocked.json` as examples. This report is a separate AI visual judgment gate; `visual_validation_report.json` from the engineering script does not replace it.

A passing visual report must record real screenshot inspection in `review_capability`. If the active agent/model cannot inspect images, set `status` to `"blocked"`, set `blocking_findings` above `0`, and explain the missing capability in `findings`; do not fabricate scores or strengths. `build` rejects passing reports that omit `review_capability.inspected_assets` or reference screenshots that do not exist.

Passing reports must also record:

- `review_context.context_sources`
- `review_context.rubric_version`
- per-slide `visual_craft_score`
- per-slide `strategic_clarity_score`
- per-slide `hard_blockers`
- per-slide `wow_passed` when `critical_visual` is true
- per-slide `rollback_recommendation`

When AI visual review requests changes, keep the repair loop explicit:

1. Reviewer writes `status: "blocked"`, failed slide entries, and required repairs.
2. Execution agent repairs React slide sources and regenerates review screenshots.
3. Execution agent records each repair in `repair_log` with `status: "resolved"`, `changed_artifacts`, and evidence.
4. Reviewer rechecks the new screenshots, marks every slide `passed: true`, sets `status: "pass"`, and keeps the resolved repair log as proof.

## Review Assets

AI visual review must use real render artifacts:

```text
output/projects/<project-id>/review/
├── full_deck.png
└── slides/
    ├── slide_01.png
    └── ...
```
