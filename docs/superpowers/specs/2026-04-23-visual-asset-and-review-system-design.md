# Visual Asset And Review System Design

## Goal

Upgrade the current Article-to-PPT workflow so it can reliably produce visually striking decks instead of only validating structurally correct slides.

The new system must do three things well:

- decide whether a slide should use a visual asset at all
- generate or source the right kind of visual asset for the slide's job
- enforce a harsh visual-quality gate that blocks weak pages, weak assets, and weak repairs

The product promise is visual impact. The workflow should optimize for memorable, presentation-grade pages, not merely complete pages.

## Non-Negotiable Requirements

Visual quality is the product floor.

The workflow must not approve a deck that is technically valid but visually weak, generic, flat, or strategically unclear.

The workflow must not let an agent generate slides, review the same slides with thin context, and approve them with a vague score.

If a page is not good enough, the system must repair or rebuild it. If only one page is weak, the system must protect already-approved pages and rework only the affected scope unless a shared contract changed.

## Current Problems

The current workflow already has:

- content audit
- design DNA generation
- React slide authoring
- screenshot capture
- AI visual review artifact requirements
- engineering browser validation

But it still has four major gaps:

1. Visual review context is too weak and too inconsistent.
2. The workflow lacks a first-class visual asset generation layer.
3. The repair loop does not explicitly separate asset problems from composition problems or upstream intent problems.
4. Human feedback is possible in conversation, but not represented as a formal rollback and invalidation mechanism.

As a result, the workflow can produce decks that are structurally correct and still not visually impressive.

## Design Principle

Treat visual quality as a production system, not as a final cosmetic check.

The workflow should move from:

```text
content -> slides -> review -> export
```

to:

```text
content understanding
  -> narrative decisions
  -> asset intent
  -> visual asset construction
  -> page composition
  -> contextual visual review
  -> targeted repair or rollback
  -> export
```

This system should create visual assets intentionally, compose them intentionally, and review them against explicit design and audience context.

## Scope

In scope for the first redesign:

- explicit slide-level asset intent
- a unified visual asset system
- routing between `diagram/svg`, `chart`, `image_search`, `image_generation`, and `none`
- multi-candidate asset generation and selection
- contextual AI visual review with harsh scoring
- wow requirements for critical visual slides
- explicit hard blockers
- repair classification and targeted rollback
- human asynchronous feedback normalization
- scoped invalidation: `slide_local`, `pattern_shared`, `deck_global`

Out of scope for the first redesign:

- implementing every image-generation provider at once
- fully automatic style unification across arbitrary external images
- fully automatic multi-slide art direction without blueprint guidance
- replacing human taste with a single numerical score
- forcing every slide to contain an image

## High-Level Architecture

The workflow should be split into five layers plus one control layer.

### 1. Content And Narrative Layer

This layer keeps the existing responsibility for:

- audience
- deck goal
- thesis
- outline
- slide blueprint

It must now also decide what role, if any, a visual asset should play on each page.

### 2. Visual Asset Construction Layer

This is a new first-class workflow layer.

It is responsible for:

- deciding which asset path should be used
- generating multiple candidates
- selecting a final asset through review
- recording source and rollback metadata

Supported asset outcomes:

- `diagram/svg`
- `chart`
- `image_search`
- `image_generation`
- `none`

### 3. Page Composition Layer

This layer turns approved copy plus approved assets into actual slides.

It owns:

- focal point choice
- page hierarchy
- whether the asset is dominant or supportive
- how typography and the asset interact
- whether the page's wow moment comes from layout tension, graphic invention, or both

### 4. Visual Gate Layer

This layer performs a contextual, screenshot-based visual review.

It must reject:

- pages that are technically valid but visually weak
- pages with weak or incorrect assets
- pages that fail the design DNA
- pages that are clear but not premium
- pages that are pretty but strategically empty

### 5. Engineering Gate Layer

This remains the existing browser validation layer.

It checks:

- hidden text
- clipped text
- covered text
- overflow
- expected text presence

It is still necessary, but it never counts as visual approval.

### 6. Human Async Control Layer

Human feedback should become a high-priority asynchronous control input.

The workflow should continue by default, but human feedback must be able to:

- target a single slide
- target a shared visual pattern
- target a deck-wide contract
- trigger scoped rollback without destroying already-approved work

## Blueprint Contract Changes

`slide_blueprint.json` must become the upstream visual contract for each page.

Each slide should add these fields:

- `critical_visual`: boolean
- `visual_goal`: what the audience should remember at first glance
- `wow_goal`: what kind of memorable effect the page should create
- `rollback_scope_default`: usually `slide_local`
- `shared_visual_dependencies`: shared patterns or systems the page depends on
- `asset_intent`: a structured description of the visual asset strategy

### `asset_intent`

Default structure:

- `visual_role`
- `asset_goal`
- `candidate_asset_types`
- `must_show`
- `must_avoid`
- `wow_goal`

Critical visual slides may extend this with:

- `composition_hint`
- `dominant_zone`
- `asset_priority`
- `fallback_visual_strategy`

The blueprint should decide the expressive need, not the implementation provider.

## New Planning And Manifest Artifacts

### `visual_asset_plan.json`

This file translates blueprint intent into executable asset choices.

For each slide or asset slot, it should record:

- whether a visual asset is required
- primary asset route
- fallback routes
- why the route was chosen
- candidate count requirement
- whether independent asset review is required
- whether the slot belongs to a critical visual page

This file exists so the workflow can distinguish "the page needed the wrong asset strategy" from "the chosen asset was poorly executed."

### `visual_asset_manifest.json`

This file records what the asset system actually produced and selected.

For each asset slot, it should record:

- `asset_id`
- `slide`
- `slot`
- `asset_type`
- `source_type`
- `source_provider`
- `prompt_or_query`
- `candidate_assets`
- `selected_asset`
- `selection_rationale`
- `review_status`
- `license_metadata`
- `resolution_metadata`
- `rollback_scope`
- `invalidated_at`

This file provides traceability for repairs and rollbacks.

### `human_feedback_log.json`

Conversation feedback remains the default user input path, but it must be normalized into a persistent project artifact.

Each feedback item should record:

- original feedback text
- timestamp
- targeted slide or artifact
- normalized feedback fields
- computed rollback level
- invalidated artifacts
- agent acknowledgement
- handling status

## Asset Routing Model

The workflow must make an expressive decision before making a technical decision.

Default routing logic:

1. If a slide is stronger without an asset, use `none`.
2. For structure, relationships, systems, flows, timelines, and role models, prefer `diagram/svg`.
3. For trends, comparisons, rankings, distributions, and analytical reporting, prefer `chart`.
4. For real people, places, environments, and real-world evidence, prefer `image_search`.
5. For abstract concepts, branded atmosphere, and custom illustrative anchors, prefer `image_generation`.

If the preferred path cannot deliver the required impact, the workflow may:

- retry the same path
- reroute to a fallback path
- combine two paths
- escalate upstream if the original `asset_intent` is wrong

## Asset Candidate Requirements

No asset may go directly from generation to slide composition without comparison.

Minimum candidate counts:

- normal asset slot: at least 3 candidates
- critical visual slide asset slot: at least 5 candidates

If the first round does not produce a sufficiently strong result, the system must continue generating or sourcing candidates. It must not settle for the least bad option.

Each candidate should keep:

- source or provider
- query or prompt
- rationale for consideration
- rationale for rejection or selection

## Asset Review Gate

Assets should be reviewed before they are placed into the slide.

Review criteria:

- alignment with `asset_intent`
- alignment with current slide thesis and page role
- alignment with `design_dna.json`
- visual strength and premium finish
- crop and composition usability
- resolution quality
- licensing and provenance
- whether the asset truly strengthens the slide

Critical visual slides must separate:

- candidate generation or sourcing
- final candidate selection

The same agent should not both generate and final-approve the decisive asset on a critical visual slide.

## Composition SOP

Slide authoring must treat composition as a separate design step, not as JSX assembly.

For each page, the composition pass should decide:

- what the focal point is
- whether the asset is dominant or supportive
- what the reading order is
- whether wow comes from page tension, a memorable diagram, or both
- whether the chosen asset still deserves to stay prominent once combined with the copy

If the asset weakens the page once placed into layout, the workflow must be able to:

- shrink it to a support role
- replace it
- route back to the asset layer
- replace the asset strategy entirely

## Visual Review SOP

Visual review must be contextual and screenshot-based.

It must not review a page from:

- filename alone
- DOM assumptions alone
- a thin one-line prompt

Required context for each review:

- `analysis.json`
- `design_dna.json`
- `outline.json`
- `slide_blueprint.json`
- current slide `asset_intent`
- current slide selected assets and source rationale
- `review/full_deck.png`
- `review/slides/slide_XX.png`

### Dual Core Scores

Each slide should receive:

- `visual_craft_score`
- `strategic_clarity_score`

Both scores must be high. The system must reject:

- pages that look premium but communicate poorly
- pages that communicate clearly but look ordinary

### Supporting Evidence

Each review should also record evidence for:

- focal point
- hierarchy
- type scale
- composition
- information density
- asset fit
- brand consistency
- intent match
- wow execution

These dimensions explain the decision. They should not be used to average away a core failure.

## Quality Thresholds

### Baseline Gate

Every slide must meet:

- `visual_craft_score >= 8.5`
- `strategic_clarity_score >= 8.5`

The workflow should not accept a "decent" page.

### Critical Visual Pages

Critical visual pages should target 9.0-level work, but the actual gate should be:

- both core scores meet the 8.5 floor
- wow requirements pass
- no hard blocker exists

This preserves a hard minimum while still requiring memorable page quality.

### Rebuild Threshold

- if either core score is below 7.5, rebuild the page instead of patching it
- if either score is between 7.5 and 8.49, allow one targeted repair pass; if it still fails, rebuild the page
- if a critical visual page fails wow requirements, prefer rebuild over incremental polish

## Hard Blockers

Any one of the following should block approval regardless of score:

- changed locked copy, facts, numbers, or conclusions
- broken or removed `visual_anchor`
- broken `signature_visual_moves`
- degraded a graphic page into a generic card or text page
- hid, squeezed, or weakened essential content to satisfy validation
- introduced colors, fonts, or component language outside `design_dna.json`
- approved visual review without real screenshot inspection
- failed to regenerate screenshots and rerun review after repairs
- repaired a slide without the required context packet
- selected an asset that clearly contradicts `asset_intent`
- let a critical visual page pass without a real wow mechanism

## Wow Requirements

Critical visual pages must satisfy at least two meaningful wow conditions:

1. a clear single dominant anchor visible within two seconds
2. strong page tension through hierarchy, scale, whitespace, and balance
3. a memorable visual move or diagram execution tied to the page's intent
4. emotional or judgmental force that helps the audience believe, choose, or remember

Expected emphasis by page type:

- cover and chapter pages: composition tension first
- core diagram pages: diagram invention and correctness first
- ending pages: both composition and memorability

## Repair Classification

Before repairing a failed page, the workflow must classify the failure:

- asset problem
- composition problem
- upstream intent problem
- shared visual contract problem

Repair paths:

- replace or regenerate the asset
- recompose the page
- reroute through `visual_asset_plan.json`
- update `slide_blueprint.json`
- update `design_dna.json`

The system must not assume every failure is a TSX layout issue.

## Human Feedback Model

Human feedback should be accepted in natural language and normalized by the agent into a structured feedback card.

Required normalized fields:

- `feedback_scope`
- `targets`
- `reason`
- `expected_change`
- `rollback_level`
- `invalidated_artifacts`
- `agent_acknowledgement`
- `status`

Before acting, the agent must first restate:

- what feedback it understood
- what slides or artifacts are affected
- whether the rollback is `slide_local`, `pattern_shared`, or `deck_global`
- what artifacts become stale
- what stage it will restart from

This acknowledgement is mandatory, but it should not block the workflow waiting for extra confirmation.

## Rollback And Invalidation Rules

The system should protect approved work by default.

### Rollback Levels

- `slide_local`: only the current slide and its local assets are invalidated
- `pattern_shared`: invalidate every slide that depends on the same shared visual pattern, component, or asset language
- `deck_global`: invalidate deck-wide contracts and all dependent artifacts

### Default Rule

If only one slide is weak or insufficiently impressive, invalidate only that slide.

Do not throw away already-approved slides unless a shared or deck-wide contract changed.

### Automatic Escalation Triggers

Escalate rollback scope when feedback changes:

- `analysis.json`
- `content_quality_report.json`
- `design_recommendation.json`
- `design_dna.json`
- `outline.json`
- `slide_blueprint.json` locked copy, page role, visual anchor, or shared visual pattern fields

### Shared Pattern Cases

A slide problem may escalate from local to shared if it changes:

- a shared diagram language
- a shared chart language
- a shared slide component family
- a shared asset style contract

## Workflow Integration

The redesigned execution sequence should be:

1. content audit
2. design recommendation and design DNA
3. outline and blueprint with `asset_intent`
4. visual asset planning
5. asset generation and sourcing
6. asset review and selection
7. slide composition
8. screenshot generation
9. contextual visual review
10. targeted repair or scoped rollback
11. engineering browser validation
12. extract, export, and final output validation

At any point after step 7, human feedback may interrupt the flow and trigger scoped rollback.

## Documentation And Skill Changes

Implementation should update the skill and references so agents know where to read each rule.

Recommended documentation split:

- `SKILL.md`: orchestration summary and stage links
- `references/workflow.md`: updated end-to-end stages and invalidation rules
- `references/visual-validation.md`: contextual review SOP, scoring rules, wow checks, hard blockers
- `references/ppt-visual-design.md`: deck-level visual craft guidance
- `references/artifact-templates.md`: upgraded report and manifest templates
- new reference for visual asset routing and asset review rules

## Implementation Priorities

Priority 1:

- blueprint contract changes
- visual asset plan and manifest design
- contextual visual review schema and artifact changes
- hard blocker and rollback policy

Priority 2:

- diagram/svg asset path
- chart asset path
- network image search path
- unified routing layer

Priority 3:

- pluggable image-generation provider interface
- provider fallback contracts
- advanced cross-provider style harmonization

## Success Criteria

The redesign succeeds when:

- the workflow can decide when not to use an image
- the workflow can intentionally build diagrams, charts, and sourced imagery as first-class slide assets
- weak slides fail for the right reason, not just "needs polish"
- single weak slides can be rebuilt without invalidating approved pages
- critical visual slides are blocked unless they are both high-scoring and memorable
- human feedback can redirect the workflow without collapsing the entire deck by default
- the final system produces decks that look designed, not merely generated
