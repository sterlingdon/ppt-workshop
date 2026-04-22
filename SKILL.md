---
name: article-to-ppt
description: Use when the user wants to convert an article, URL, PDF, research note, or document into a polished PowerPoint presentation. Triggers on "做成PPT", "转成幻灯片", "制作演示文稿", "make a presentation from", "convert to slides", and similar deck-generation requests.
---

# Article → PPT Skill

This skill turns source material into a presentation by building a project workspace, writing high-fidelity React slides, using AI visual judgment to improve the rendered deck, running engineering checks, and exporting a PPTX.

## Operating Rule

Do not treat the CLI as an article-to-PPT generator or visual designer. The CLI manages project workspaces, validates existing React slides, checks engineering visibility/overflow issues, extracts layout, and exports PPTX. The agent is responsible for content analysis, deck planning, design direction, React slide authoring, AI visual review, and repair loops.

## Read Only What You Need

- Start every deck: read [`references/workflow.md`](references/workflow.md).
- Before running any core agent role: read [`references/agent-prompts.md`](references/agent-prompts.md).
- Before writing any artifact: use [`references/artifact-templates.md`](references/artifact-templates.md).
- Before analysis/planning: read [`references/deck-brief.md`](references/deck-brief.md) and [`references/semantic-validation.md`](references/semantic-validation.md).
- Before creating `design_dna.json`: invoke `ui-ux-pro-max` for design-system recommendations.
- Before writing slides: first read and follow [`examples/react-slides/minimal-deck/README.md`](examples/react-slides/minimal-deck/README.md), then read [`references/slide-coding-rules.md`](references/slide-coding-rules.md), [`references/component-authoring.md`](references/component-authoring.md), and `web/src/styles/STYLE_GUIDE.md`.
- Before visual repair/export: read [`references/visual-validation.md`](references/visual-validation.md), [`references/visual-fidelity.md`](references/visual-fidelity.md), and [`references/pptx-exporter.md`](references/pptx-exporter.md).
- For implementation details only when blocked: read [`references/engineering.md`](references/engineering.md).

## Core Artifacts

Each deck lives under `output/projects/<project-id>/`.

Required working contract:

- `article_text.md`: cleaned source text.
- `deck_state.json`: shared state read and updated by all three core agents.
- `analysis.json`: audience-relevant facts, thesis, statistics, entities, language, and suggested theme.
- `content_quality_report.json`: content auditor gate result. It proves the deck angle, audience, key points, and data emphasis are correct before slide generation.
- `design_recommendation.json`: distilled `ui-ux-pro-max` recommendation used to create the deck's design system.
- `design_dna.json`: visual system for this deck, including preset, tokens, style recipes, slide-pattern assignments, and consistency rules.
- `outline.json`: slide-by-slide plan with type, title, image need, and purpose notes.
- `slide_blueprint.json`: page-by-page build plan for React slide authoring.
- `slides/Slide_N.tsx` plus `slides/index.ts`: final React slide sources.
- `review/full_deck.png` plus `review/slides/*.png`: rendered review screenshots used by the AI visual gate.
- `visual_review_report.json`: AI visual review and repair audit. This is required for quality even though the CLI does not create it.
- `visual_validation_report.json`: engineering visibility/overflow gate result.
- `layout_manifest.json`: extracted slide layout and assets.
- `presentation.pptx`: final deliverable.

## Smooth Execution Path

1. Create or select the project workspace.
2. Extract clean article text into `article_text.md` and initialize `deck_state.json`.
3. Run the **Content Quality Auditor**: read `deck_state.json`, create `analysis.json`, identify the audience, deck goal, thesis, must-emphasize facts, must-cut noise, data points, and slide-worthy arguments.
4. Write `content_quality_report.json` using the report examples in `examples/reports/`; do not proceed unless it has `status: "pass"`, no blocking content findings, no required revisions, and all `resolution_log` items resolved. If the report requires revisions, update the content artifacts, record the fixes, and re-run the audit before handoff.
5. Run the **PPT Generation Agent**: invoke `ui-ux-pro-max`, write `design_recommendation.json`, create `design_dna.json`, create `outline.json`, create `slide_blueprint.json`, then write React slides in `output/projects/<project-id>/slides/`.
6. Run structural validation.
7. Run `python3 tools/ppt_workflow.py review-screenshots --project <project-id>` to create rendered review screenshots in `review/full_deck.png` and `review/slides/*.png`, then run the **Visual Review/Validation Agent**: inspect those screenshots with an AI visual lens, write `visual_review_report.json`, repair weak slides, record each repair in `repair_log`, regenerate screenshots, and repeat until there are no blocking design findings.
8. Run browser engineering validation and repair until `visual_validation_report.json.summary.failed` is `0`.
9. Build/export the deck.
10. Verify `presentation.pptx` exists, is non-empty, and was rebuilt from the approved slides.

## Commands

```bash
python3 tools/ppt_workflow.py init --name "Deck Name"
python3 tools/ppt_workflow.py validate --project <project-id>
python3 tools/ppt_workflow.py review-screenshots --project <project-id>
python3 tools/ppt_workflow.py visual-validate --project <project-id>
python3 tools/ppt_workflow.py build --project <project-id>
```

Use these when needed:

```bash
python3 tools/ppt_workflow.py activate --project <project-id>
python3 tools/ppt_workflow.py snapshot-slides --project <project-id>
python3 tools/ppt_workflow.py extract --project <project-id>
python3 tools/ppt_workflow.py export --project <project-id>
```

## Quality Gates

- Content gate: `content_quality_report.json` must pass before PPT generation. It must verify audience fit, thesis, key points, data emphasis, omissions, slide-worthy narrative, and a resolved revision loop when revisions were requested.
- Generation gate: `analysis.json`, `content_quality_report.json`, `design_recommendation.json`, `design_dna.json`, `outline.json`, and `slide_blueprint.json` must agree on audience, thesis, narrative arc, tone, slide roles, locked copy, flattened required texts, and visual anchors before slide coding.
- Copy lock gate: React slide code must render the approved `slide_blueprint.json` copy. The React authoring step may choose layout, grouping, emphasis, and line breaks, but must not rewrite facts, titles, numbers, entities, or conclusions directly in TSX.
- Source gate: `validate` must pass before export. It checks slide sources and marker basics; it does not judge deck quality.
- AI visual gate: the agent must inspect rendered slides and reject pages that are technically valid but visually weak, generic, sparse, cluttered, off-theme, or not useful to the audience. Record the review and resolved repair loop in `visual_review_report.json`.
- Engineering browser gate: `visual-validate` must pass with `summary.failed == 0`. This is not a visual-quality pass and does not replace `visual_review_report.json`.
- Export gate: run `build` after content and AI visual gates pass; final PPTX must be generated from the approved React slides.

## Non-Negotiables

- Write for the audience, not for the article structure.
- Never start slide generation before the Content Quality Auditor has approved the deck angle and key points.
- One deck, one visual system. Do not mix presets or invent unrelated styles per slide.
- Use `design_dna.json` as the style contract.
- `design_dna.json` must be grounded in `ui-ux-pro-max` recommendations, then mapped to the closest local renderer preset.
- Use the React slide examples as the source of truth for import paths, `index.ts`, and marker structure before relying on validators.
- Do not let React slide authoring become a second writing pass. If approved copy is wrong, revise `slide_blueprint.json` and invalidate downstream artifacts.
- The rendered browser preview is the truth for both AI visual review and engineering validation.
- Never equate `visual-validate` success with visual excellence.
- Do not hide essential content for PPTX-only export.
- Do not downgrade visual quality just to make objects editable; use raster fallback where needed.
