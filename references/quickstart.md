# Quickstart

Use this as the execution entry point before reading deeper references.

## Read Order

1. Start: read `references/workflow.md` and this file.
2. Before each role: read `references/agent-prompts.md`, then load the Shared Preamble plus the exact active role prompt.
3. Before content artifacts: read `references/deck-brief.md`, `references/semantic-validation.md`, and `references/artifact-templates.md`.
4. Before design artifacts: read `references/ppt-visual-design.md`, invoke the available `ui-ux-pro-max` design-intelligence entry point, then write `design_recommendation.json` and `design_dna.json`.
5. Before React slides: read `examples/react-slides/minimal-deck/README.md`, `references/slide-coding-rules.md`, `references/component-authoring.md`, and `web/src/styles/STYLE_GUIDE.md`.
6. Before repair/export: read `references/visual-validation.md`, `references/visual-fidelity.md`, and `references/pptx-exporter.md`.

Read `references/engineering.md` only when blocked by implementation details.

## Happy Path

```bash
python3 tools/ppt_workflow.py init --name "Deck Name"
python3 tools/ppt_workflow.py validate --project <project-id>
python3 tools/ppt_workflow.py review-screenshots --project <project-id>
python3 tools/ppt_workflow.py visual-validate --project <project-id>
python3 tools/ppt_workflow.py build --project <project-id>
```

`review-screenshots`, `visual-validate`, `extract`, and `build` manage the preview server internally. If the sandbox blocks local HTTP probing, rerun the same command with the required execution approval instead of starting a separate long-lived server.

## Marker Rules That Prevent Build Timeouts

- Use one `data-ppt-group` boundary for one repeatable structure.
- Put `data-ppt-item` only on the immediate repeatable card, row, step, or timeline node.
- Never put `data-ppt-group` or another `data-ppt-item` inside a `data-ppt-item`.
- Never nest `data-ppt-group` inside another `data-ppt-group`.
- If an item contains an internal bullet list, leave the inner `ul/li` unmarked, or make the whole card a raster fallback.

Run `python3 tools/ppt_workflow.py validate --project <project-id>` immediately after slide authoring. It catches marker nesting before Playwright tries to screenshot invisible elements during export.

## Repair Loop

1. If `validate` fails, repair slide source or required artifacts first.
2. If AI visual review fails, repair the React slide, record the fix in `visual_review_report.json.repair_log`, regenerate screenshots, and review again.
3. If `visual-validate` fails, repair the reported slide source, rerun `visual-validate`, regenerate screenshots, and repeat AI visual review because source changed.
4. Build only after content, AI visual, and engineering gates all pass.

## Delegation

Default to no delegation. Delegate only narrow, scoped subtasks with the current role prompt, exact artifact paths, and explicit read/write boundaries. The main agent keeps orchestration, role activation, gate approval, Design DNA ownership, slide blueprint ownership, AI visual approval, and invalidation decisions.

