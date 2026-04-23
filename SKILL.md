---
name: article-to-ppt
description: Use when the user wants to convert an article, URL, PDF, research note, or document into a polished PowerPoint presentation. Triggers on "做成PPT", "转成幻灯片", "制作演示文稿", "make a presentation from", "convert to slides", and similar deck-generation requests.
---

# Article → PPT Skill

This skill turns source material into a presentation by building a project workspace, writing high-fidelity React slides, using AI visual judgment to improve the rendered deck, running engineering checks, and exporting both a PPTX and a Vite-built static HTML presentation directory.

## Operating Rule

Do not treat the CLI as an article-to-PPT generator or visual designer. The CLI manages project workspaces, validates existing React slides, checks engineering visibility/overflow issues, extracts layout, and exports PPTX plus the static HTML asset directory. The agent is responsible for content analysis, deck planning, design direction, React slide authoring, AI visual review, and repair loops.

## Read Only What You Need

- Start every deck: read [`references/quickstart.md`](references/quickstart.md) and [`references/workflow.md`](references/workflow.md).
- Before running any core agent role, including role switches performed by the same main agent: read [`references/agent-prompts.md`](references/agent-prompts.md), load the Shared Preamble, and load the exact active role prompt. Do not assume the agent has already read this skill, workflow, or system prompt.
- Default to no sub-agent delegation. If delegation is necessary, follow the Sub-Agent Delegation Policy in [`references/workflow.md`](references/workflow.md) and [`references/agent-prompts.md`](references/agent-prompts.md); never delegate orchestration, role activation, gate approval, Design DNA ownership, slide blueprint ownership, AI visual approval, or invalidation decisions.
- Before writing any artifact: use [`references/artifact-templates.md`](references/artifact-templates.md).
- Before analysis/planning: read [`references/deck-brief.md`](references/deck-brief.md) and [`references/semantic-validation.md`](references/semantic-validation.md).
- Before creating `design_recommendation.json` or `design_dna.json`: read [`references/ppt-visual-design.md`](references/ppt-visual-design.md), then invoke `ui-ux-pro-max` as a product/web design intelligence source for transferable visual principles, not as a request to build a website.
- Before writing slides: first read and follow [`examples/react-slides/minimal-deck/README.md`](examples/react-slides/minimal-deck/README.md), then read [`references/slide-coding-rules.md`](references/slide-coding-rules.md), [`references/component-authoring.md`](references/component-authoring.md), and `web/src/styles/STYLE_GUIDE.md`.
- Before visual repair/export: read [`references/visual-validation.md`](references/visual-validation.md), [`references/visual-fidelity.md`](references/visual-fidelity.md), and [`references/pptx-exporter.md`](references/pptx-exporter.md).
- For implementation details only when blocked: read [`references/engineering.md`](references/engineering.md).

## Core Artifacts

Each deck lives under `output/projects/<project-id>/`.

Required working contract:

- `article_text.md`: cleaned source text.
- `deck_state.json`: shared state read and updated by all three core agents, including `active_role` for the prompt currently governing the workflow.
- `analysis.json`: audience-relevant facts, thesis, statistics, entities, language, and suggested theme.
- `content_quality_report.json`: content auditor gate result. It proves the deck angle, audience, key points, and data emphasis are correct before slide generation.
- `design_recommendation.json`: distilled `ui-ux-pro-max` recommendation used to create the deck's design system.
- `design_dna.json`: visual system for this deck, including full theme tokens, style recipes, signature visual moves, slide-pattern assignments, and consistency rules.
- `outline.json`: slide-by-slide plan with type, title, image need, and purpose notes.
- `slide_blueprint.json`: page-by-page build plan for React slide authoring.
- `slides/Slide_N.tsx` plus `slides/index.ts`: final React slide sources.
- `review/full_deck.png` plus `review/slides/*.png`: rendered review screenshots used by the AI visual gate.
- `visual_review_report.json`: AI visual review and repair audit. This is required for quality even though the CLI does not create it.
- `visual_validation_report.json`: engineering visibility/overflow gate result.
- `layout_manifest.json`: extracted slide layout and assets.
- `presentation.pptx`: final PowerPoint deliverable.
- `presentation-html/`: final Vite static site output, including `index.html` and referenced assets, for browser review and PPTX-vs-HTML visual comparison.

## Smooth Execution Path

1. Create or select the project workspace.
2. Extract clean article text into `article_text.md` and initialize `deck_state.json`.
3. Activate the **Content Quality Auditor** role prompt, set `deck_state.json.active_role` to `content_quality_auditor`: read `deck_state.json`, create `analysis.json`, identify the audience, deck goal, thesis, must-emphasize facts, must-cut noise, data points, and slide-worthy arguments.
4. Write `content_quality_report.json` using the report examples in `examples/reports/`; do not proceed unless it has `status: "pass"`, no blocking content findings, no required revisions, and all `resolution_log` items resolved. If the report requires revisions, update the content artifacts, record the fixes, and re-run the audit before handoff.
5. Activate the **PPT Generation Agent** role prompt, set `deck_state.json.active_role` to `ppt_generation_agent`: provide the exact prompt from `references/agent-prompts.md`, read `references/ppt-visual-design.md`, invoke `ui-ux-pro-max`, write `design_recommendation.json`, create `design_dna.json`, create `outline.json`, create `slide_blueprint.json`, then write React slides in `output/projects/<project-id>/slides/`.
6. Run structural validation.
7. Run `python3 tools/ppt_workflow.py review-screenshots --project <project-id>` to create rendered review screenshots in `review/full_deck.png` and `review/slides/*.png`, then activate the **Visual Review/Validation Agent** role prompt and set `deck_state.json.active_role` to `visual_review_validation_agent`: inspect those screenshots with an AI visual lens, write `visual_review_report.json`, repair weak slides, record each repair in `repair_log`, regenerate screenshots, and repeat until there are no blocking design findings.
8. Run browser engineering validation and repair until `visual_validation_report.json.summary.failed` is `0`.
9. Build/export the deck.
10. Verify `presentation.pptx` and the complete `presentation-html/` static site exist, are non-empty, and were rebuilt from the approved slides.

## Commands

```bash
python3 tools/ppt_workflow.py init --name "Deck Name"
python3 tools/ppt_workflow.py validate --project <project-id>
python3 tools/ppt_workflow.py review-screenshots --project <project-id>
python3 tools/ppt_workflow.py visual-validate --project <project-id>
python3 tools/ppt_workflow.py build --project <project-id>
```

`review-screenshots`, `visual-validate`, `extract`, and `build` manage the preview server internally. Do not start a separate Vite server unless you are manually inspecting the browser preview.

Use these when needed:

```bash
python3 tools/ppt_workflow.py activate --project <project-id>
python3 tools/ppt_workflow.py snapshot-slides --project <project-id>
python3 tools/ppt_workflow.py extract --project <project-id>
python3 tools/ppt_workflow.py export --project <project-id>
python3 tools/ppt_workflow.py export-html --project <project-id>
```

## Quality Gates

- Content gate: `content_quality_report.json` must pass before PPT generation. It must verify audience fit, thesis, key points, data emphasis, omissions, slide-worthy narrative, and a resolved revision loop when revisions were requested.
- Generation gate: `analysis.json`, `content_quality_report.json`, `design_recommendation.json`, `design_dna.json`, `outline.json`, and `slide_blueprint.json` must agree on audience, thesis, narrative arc, tone, slide roles, locked copy, flattened required texts, and visual anchors before slide coding.
- Copy lock gate: React slide code must render the approved `slide_blueprint.json` copy. The React authoring step may choose layout, grouping, emphasis, and line breaks, but must not rewrite facts, titles, numbers, entities, or conclusions directly in TSX.
- Source gate: `validate` must pass before export. It checks slide sources and marker basics; it does not judge deck quality.
- AI visual gate: the agent must inspect rendered slides and reject pages that are technically valid but visually weak, generic, sparse, cluttered, off-theme, or not useful to the audience. Record the review and resolved repair loop in `visual_review_report.json`.
- Engineering browser gate: `visual-validate` must pass with `summary.failed == 0`. This is not a visual-quality pass and does not replace `visual_review_report.json`.
- Export gate: run `build` after content and AI visual gates pass; final PPTX and complete static HTML asset directory must be generated from the approved React slides.

## Non-Negotiables

- Write for the audience, not for the article structure.
- Role prompts are mandatory execution context. Before switching roles, re-read `references/agent-prompts.md`, load the Shared Preamble plus the active role prompt, and let that role's pass/failure conditions govern the next artifact.
- Sub-agent delegation is optional and discouraged by default. Use it only for narrow tasks with complete role context, explicit artifact paths, clear write scope, and main-agent review.
- Never start slide generation before the Content Quality Auditor has approved the deck angle and key points.
- One deck, one visual system. Do not mix unrelated styles per slide.
- Use `design_dna.json` as the style contract.
- `design_dna.json` must be grounded in `ui-ux-pro-max` recommendations and must define the deck's full visual system. `ui-ux-pro-max` is used for cross-domain design judgment: hierarchy, layout, typography, color, spacing, chart language, and interface-level polish that transfer to PPT. It is not a signal to make a website or app.
- Use the React slide examples as the source of truth for import paths, `index.ts`, and marker structure before relying on validators.
- PPT visual craft is a gate, not decoration. Weak hierarchy, oversized/undersized type, monotonous templates, poor whitespace, or generic web-card layouts must be repaired before export even when validators pass.
- Do not let React slide authoring become a second writing pass. If approved copy is wrong, revise `slide_blueprint.json` and invalidate downstream artifacts.
- The rendered browser preview is the truth for both AI visual review and engineering validation.
- Never equate `visual-validate` success with visual excellence.
- Do not hide essential content for PPTX-only export.
- Do not downgrade visual quality just to make objects editable; use raster fallback where needed.
