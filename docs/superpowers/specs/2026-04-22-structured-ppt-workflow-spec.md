# Structured PPT Workflow Spec

## Goal

Turn the current React PPT demo into a reusable skill workflow that can generate many decks without file collisions, while giving less capable agents concrete style and layout references.

## Scope

This spec completes the remaining architecture work after the initial React rendering pipeline:

1. Isolate generated deck source files per project.
2. Productize the style preset system into a reusable catalog.
3. Add a unified CLI runner for project initialization, slide activation, validation, extraction, and PPTX export.
4. Add quality gates that fail before export when required PPT extraction markers are missing.

## Non-Goals

- Do not build a web-based project manager UI.
- Do not replace Vite or React.
- Do not make the AI analysis/content-generation steps fully automatic; those remain agent-authored checkpoints.
- Do not remove the legacy HTML renderer yet. It remains covered by existing tests.

## Architecture

### Project Workspace

Every generated deck lives under:

```text
output/projects/<project-id>/
├── project.json
├── article_text.md
├── analysis.json
├── outline.json
├── slides.json
├── slides_with_images.json
├── layout_manifest.json
├── presentation.pptx
├── assets/
└── slides/
    ├── Slide_1.tsx
    ├── Slide_2.tsx
    └── index.ts
```

`output/projects/<project-id>/slides/` is the durable source of truth for generated deck React code.

`web/src/slides/` is the active Vite renderer slot. Tools copy a project's slides into this slot before preview/extraction and can snapshot the active slot back into the project.

This gives the workflow one simple invariant:

> Runtime tools render exactly one active deck, but the repository can store many generated deck workspaces safely.

### Style Presets

The preset registry remains in `web/src/styles/presets.ts`, but each preset must expose enough information for agents to reuse it:

- design tokens
- layout rules
- component recipes
- slide patterns
- avoid-list

Agents should first choose a style preset, then choose slide patterns inside that preset, then write React components using `styleVars(preset)` and `data-ppt-*` markers.

### CLI Runner

Add `tools/ppt_workflow.py` with these subcommands:

- `init --name <name>`: create a project workspace.
- `snapshot-slides --project <id>`: copy active `web/src/slides/` into the project workspace.
- `activate --project <id>`: copy project slides into `web/src/slides/`.
- `validate --project <id>`: run structural quality gates on active/project slides and optional manifest/PPTX outputs.
- `extract --project <id>`: activate slides, run Playwright extraction, write manifest/assets.
- `export --project <id>`: build PPTX from manifest.
- `build --project <id>`: validate slides, extract layout, export PPTX, then validate outputs.

### Quality Gates

Validation must check:

- project workspace exists
- project slide source directory contains `index.ts`
- each `Slide_*.tsx` contains `data-ppt-slide`
- each slide component uses the style preset helper or CSS preset variables
- active/project slides expose at least one `data-ppt-text` marker across the deck
- if `layout_manifest.json` exists, every referenced background/component image exists
- if `presentation.pptx` exists, it is non-empty

Validation returns structured errors and exits non-zero from the CLI when any gate fails.

## Data Flow

1. `ppt_workflow.py init --name "Deck Name"` creates the workspace.
2. Agent writes or updates React slide files in `web/src/slides/`.
3. `ppt_workflow.py snapshot-slides --project <id>` persists generated source into the deck workspace.
4. `ppt_workflow.py build --project <id>` activates project slides, validates, extracts, exports, and validates outputs.

## Testing

Add Python tests for:

- slide source snapshot and activation
- validation failures for missing markers
- validation success for a minimal valid deck
- CLI-level workspace behavior where practical without invoking a browser

Keep existing full test suite green.

## Implementation Status

Implemented in this branch:

- `tools/deck_sources.py` snapshots active slides into a project and activates project slides into the renderer slot.
- `tools/quality_gate.py` validates source markers, style preset usage, manifest assets, and non-empty PPTX outputs.
- `tools/ppt_workflow.py` provides `init`, `snapshot-slides`, `activate`, `validate`, `extract`, `export`, and `build`.
- `web/src/styles/presets.ts` now includes `slidePatterns` for each preset.
- `web/src/styles/STYLE_GUIDE.md` documents the AI-facing marker and preset contract.
- Tests cover deck source copy behavior, quality gates, and CLI workspace behavior.
