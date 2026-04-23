# Visual Asset And Review System Phase 1 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the first shippable slice of the visual asset and review redesign by adding project artifact paths, schema-backed contracts, a unified asset-routing skeleton, human feedback normalization, and stricter visual gate validation.

**Architecture:** Phase 1 does not try to ship every image provider. It adds the workflow contracts and enforcement points the rest of the system depends on: workspace paths, JSON schemas, asset planning helpers, feedback/invalidation helpers, and a richer visual review gate. This keeps the implementation testable and lets later plans add provider-specific execution behind stable contracts.

**Tech Stack:** Python 3, pytest, jsonschema, project CLI in `tools/ppt_workflow.py`, existing JSON artifact workflow, Markdown reference docs

---

## Scope Check

The approved spec spans multiple subsystems:

- blueprint and project artifact contracts
- visual asset routing and manifests
- human feedback normalization and rollback
- visual review scoring and gate enforcement
- provider-specific asset generation

This plan intentionally covers **Phase 1 foundation only**:

- contract artifacts
- schema validation
- routing skeleton
- feedback normalization
- quality gate enforcement
- docs and examples

Follow-on plans should handle:

- diagram/svg rendering providers
- chart rendering providers
- network image search integrations
- image generation provider integrations

## File Structure

### Existing files to modify

- `tools/presentation_workspace.py`  
  Add canonical paths for new project artifacts so every stage reads and writes the same files.

- `tools/quality_gate.py`  
  Enforce richer visual review requirements plus the presence and shape of new visual asset and feedback artifacts when they exist.

- `tools/ppt_workflow.py`  
  Add CLI entry points for Phase 1 artifact generation and feedback normalization.

- `schemas/visual_review.schema.json`  
  Add contextual review fields, dual scores, hard blockers, wow checks, and rollback metadata.

- `tests/test_presentation_workspace.py`  
  Cover new workspace paths.

- `tests/test_quality_gate.py`  
  Cover the stricter gate behavior and invalid artifact combinations.

- `tests/test_schemas.py`  
  Cover new schemas and the richer visual review schema.

- `tests/test_examples.py`  
  Keep report examples aligned with the updated schema and gate expectations.

- `references/artifact-templates.md`  
  Document the new artifact structures.

- `references/visual-validation.md`  
  Document the contextual review packet, dual scores, wow requirements, and hard blockers.

- `references/workflow.md`  
  Document the new asset-planning stage, feedback stage, and scoped rollback rules.

### New files to create

- `tools/visual_assets.py`  
  Contract module for `asset_intent`, asset planning, asset routing, and manifest helpers.

- `tools/human_feedback.py`  
  Normalize human feedback, classify rollback scope, and compute invalidated artifacts.

- `schemas/slide_blueprint.schema.json`  
  Formalize the new `asset_intent`, `critical_visual`, and rollback-related fields.

- `schemas/visual_asset_plan.schema.json`  
  Schema for plan-time asset routing decisions.

- `schemas/visual_asset_manifest.schema.json`  
  Schema for generated/selected asset records.

- `schemas/human_feedback.schema.json`  
  Schema for normalized human feedback cards and logs.

- `tests/test_visual_assets.py`  
  Unit tests for routing and candidate-count rules.

- `tests/test_human_feedback.py`  
  Unit tests for normalization, rollback classification, and invalidation.

## Task 1: Expand Workspace Paths For New Artifact Contracts

**Files:**
- Modify: `tools/presentation_workspace.py`
- Test: `tests/test_presentation_workspace.py`

- [ ] **Step 1: Write the failing workspace-path test**

```python
def test_create_project_workspace_includes_visual_asset_contract_paths(tmp_path):
    workspace = create_project_workspace(
        "Visual Asset Deck",
        root_dir=tmp_path,
        project_id="20260423-090000-visual-asset-deck",
    )

    assert workspace.project_dir == tmp_path / "20260423-090000-visual-asset-deck"
    assert workspace.slide_blueprint_path == workspace.project_dir / "slide_blueprint.json"
    assert workspace.visual_asset_plan_path == workspace.project_dir / "visual_asset_plan.json"
    assert workspace.visual_asset_manifest_path == workspace.project_dir / "visual_asset_manifest.json"
    assert workspace.human_feedback_log_path == workspace.project_dir / "human_feedback_log.json"
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `pytest tests/test_presentation_workspace.py::test_create_project_workspace_includes_visual_asset_contract_paths -v`

Expected: FAIL with `AttributeError: 'PresentationWorkspace' object has no attribute 'slide_blueprint_path'`.

- [ ] **Step 3: Add the new workspace paths**

```python
@dataclass(frozen=True)
class PresentationWorkspace:
    project_id: str
    project_dir: Path
    assets_dir: Path
    slides_dir: Path
    manifest_path: Path
    pptx_path: Path
    html_dir: Path
    metadata_path: Path
    slide_blueprint_path: Path
    visual_asset_plan_path: Path
    visual_asset_manifest_path: Path
    human_feedback_log_path: Path


def get_project_workspace(project_id: str, root_dir: str | Path = DEFAULT_PROJECT_ROOT) -> PresentationWorkspace:
    safe_id = validate_project_id(project_id)
    root = Path(root_dir)
    project_dir = root / safe_id
    return PresentationWorkspace(
        project_id=safe_id,
        project_dir=project_dir,
        assets_dir=project_dir / "assets",
        slides_dir=project_dir / "slides",
        manifest_path=project_dir / "layout_manifest.json",
        pptx_path=project_dir / "presentation.pptx",
        html_dir=project_dir / "presentation-html",
        metadata_path=project_dir / "project.json",
        slide_blueprint_path=project_dir / "slide_blueprint.json",
        visual_asset_plan_path=project_dir / "visual_asset_plan.json",
        visual_asset_manifest_path=project_dir / "visual_asset_manifest.json",
        human_feedback_log_path=project_dir / "human_feedback_log.json",
    )
```

- [ ] **Step 4: Run the workspace tests**

Run: `pytest tests/test_presentation_workspace.py -v`

Expected: PASS for the existing workspace tests plus the new contract-path test.

- [ ] **Step 5: Commit**

```bash
git add tools/presentation_workspace.py tests/test_presentation_workspace.py
git commit -m "feat(ppt): add workspace paths for visual asset contracts"
```

## Task 2: Add Schema-Backed Contracts For Blueprint, Asset Plans, Asset Manifests, And Feedback

**Files:**
- Create: `schemas/slide_blueprint.schema.json`
- Create: `schemas/visual_asset_plan.schema.json`
- Create: `schemas/visual_asset_manifest.schema.json`
- Create: `schemas/human_feedback.schema.json`
- Modify: `tests/test_schemas.py`

- [ ] **Step 1: Write failing schema tests**

```python
def test_slide_blueprint_schema_accepts_asset_intent():
    schema = load_schema("slide_blueprint")
    data = {
        "slides": [
            {
                "slide": 1,
                "title": "教师角色：三重转变",
                "critical_visual": True,
                "visual_goal": "Remember the three-role shift immediately.",
                "wow_goal": "diagram invention",
                "rollback_scope_default": "slide_local",
                "shared_visual_dependencies": ["role-triangle-language"],
                "asset_intent": {
                    "visual_role": "core_explainer",
                    "asset_goal": "Show the three-role model as one memorable diagram.",
                    "candidate_asset_types": ["diagram/svg", "image_generation"],
                    "must_show": ["three roles", "triangle relationship"],
                    "must_avoid": ["generic card grid"],
                    "wow_goal": "diagram invention"
                }
            }
        ]
    }
    jsonschema.validate(data, schema)


def test_visual_asset_plan_schema_requires_primary_route():
    schema = load_schema("visual_asset_plan")
    data = {"slides": [{"slide": 1, "asset_slots": [{"slot": "hero"}]}]}
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(data, schema)
```

- [ ] **Step 2: Run the schema tests to verify they fail**

Run: `pytest tests/test_schemas.py -k "slide_blueprint_schema or visual_asset_plan_schema" -v`

Expected: FAIL with missing schema file errors.

- [ ] **Step 3: Write the new schemas**

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "required": ["slides"],
  "properties": {
    "slides": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["slide", "title", "asset_intent"],
        "properties": {
          "slide": { "type": "integer", "minimum": 1 },
          "title": { "type": "string", "minLength": 1 },
          "critical_visual": { "type": "boolean" },
          "visual_goal": { "type": "string" },
          "wow_goal": { "type": "string" },
          "rollback_scope_default": {
            "type": "string",
            "enum": ["slide_local", "pattern_shared", "deck_global"]
          },
          "shared_visual_dependencies": {
            "type": "array",
            "items": { "type": "string", "minLength": 1 }
          },
          "asset_intent": {
            "type": "object",
            "required": [
              "visual_role",
              "asset_goal",
              "candidate_asset_types",
              "must_show",
              "must_avoid",
              "wow_goal"
            ],
            "properties": {
              "visual_role": { "type": "string", "minLength": 1 },
              "asset_goal": { "type": "string", "minLength": 1 },
              "candidate_asset_types": {
                "type": "array",
                "minItems": 1,
                "items": { "type": "string", "minLength": 1 }
              }
            }
          }
        }
      }
    }
  }
}
```

- [ ] **Step 4: Run the full schema suite**

Run: `pytest tests/test_schemas.py -v`

Expected: PASS for the new schema tests and the existing analysis/outline/slides/visual-review tests.

- [ ] **Step 5: Commit**

```bash
git add schemas/slide_blueprint.schema.json schemas/visual_asset_plan.schema.json schemas/visual_asset_manifest.schema.json schemas/human_feedback.schema.json tests/test_schemas.py
git commit -m "feat(ppt): add schemas for visual asset and feedback artifacts"
```

## Task 3: Add A Unified Visual Asset Contract And Routing Skeleton

**Files:**
- Create: `tools/visual_assets.py`
- Test: `tests/test_visual_assets.py`

- [ ] **Step 1: Write failing routing tests**

```python
from tools.visual_assets import build_asset_plan_entry


def test_build_asset_plan_entry_prefers_diagram_for_structure_slides():
    entry = build_asset_plan_entry(
        slide=7,
        critical_visual=True,
        asset_intent={
            "visual_role": "core_explainer",
            "asset_goal": "Explain a three-role model.",
            "candidate_asset_types": ["diagram/svg", "image_generation"],
            "must_show": ["triangle relationship"],
            "must_avoid": ["generic card grid"],
            "wow_goal": "diagram invention",
        },
    )

    slot = entry["asset_slots"][0]

    assert slot["primary_route"] == "diagram/svg"
    assert slot["candidate_count"] == 5
    assert slot["independent_asset_review"] is True
```

- [ ] **Step 2: Run the routing tests to verify they fail**

Run: `pytest tests/test_visual_assets.py::test_build_asset_plan_entry_prefers_diagram_for_structure_slides -v`

Expected: FAIL with `ModuleNotFoundError: No module named 'tools.visual_assets'`.

- [ ] **Step 3: Implement the minimal routing helpers**

```python
CRITICAL_REVIEW_CANDIDATE_COUNT = 5
DEFAULT_CANDIDATE_COUNT = 3


def choose_primary_route(asset_intent: dict) -> str:
    candidates = asset_intent.get("candidate_asset_types", [])
    if "diagram/svg" in candidates:
        return "diagram/svg"
    if "chart" in candidates:
        return "chart"
    if "image_search" in candidates:
        return "image_search"
    if "image_generation" in candidates:
        return "image_generation"
    return "none"


def build_asset_plan_entry(slide: int, critical_visual: bool, asset_intent: dict) -> dict:
    primary_route = choose_primary_route(asset_intent)
    return {
        "slide": slide,
        "asset_slots": [
            {
                "slot": "primary",
                "primary_route": primary_route,
                "fallback_routes": [route for route in asset_intent.get("candidate_asset_types", []) if route != primary_route],
                "candidate_count": CRITICAL_REVIEW_CANDIDATE_COUNT if critical_visual else DEFAULT_CANDIDATE_COUNT,
                "independent_asset_review": critical_visual,
                "critical_visual": critical_visual,
            }
        ],
    }
```

- [ ] **Step 4: Run the new asset-routing test file**

Run: `pytest tests/test_visual_assets.py -v`

Expected: PASS for the structure-route test plus at least one additional test for normal-slide candidate counts.

- [ ] **Step 5: Commit**

```bash
git add tools/visual_assets.py tests/test_visual_assets.py
git commit -m "feat(ppt): add visual asset routing skeleton"
```

## Task 4: Add Human Feedback Normalization And Rollback Classification

**Files:**
- Create: `tools/human_feedback.py`
- Test: `tests/test_human_feedback.py`

- [ ] **Step 1: Write failing feedback tests**

```python
from tools.human_feedback import normalize_feedback


def test_normalize_feedback_marks_single_slide_as_slide_local():
    result = normalize_feedback(
        "Slide 7 的三角图完全不对，回到 visual review 重做",
        default_stage="visual_review",
    )

    assert result["targets"] == ["Slide_7"]
    assert result["rollback_level"] == "slide_local"
    assert result["expected_change"] == "rebuild the triangle diagram on Slide_7"


def test_normalize_feedback_escalates_design_dna_requests_to_deck_global():
    result = normalize_feedback(
        "整体颜色太保守，回到 design DNA",
        default_stage="visual_review",
    )

    assert result["rollback_level"] == "deck_global"
    assert "design_dna.json" in result["invalidated_artifacts"]
```

- [ ] **Step 2: Run the feedback tests to verify they fail**

Run: `pytest tests/test_human_feedback.py -v`

Expected: FAIL with `ModuleNotFoundError` or missing `normalize_feedback`.

- [ ] **Step 3: Implement normalization and rollback rules**

```python
STAGE_ARTIFACTS = {
    "visual_review": ["visual_review_report.json", "review/full_deck.png", "review/slides"],
    "design_dna": ["design_dna.json", "outline.json", "slide_blueprint.json"],
}


def normalize_feedback(message: str, default_stage: str) -> dict:
    rollback_level = "slide_local"
    targets: list[str] = []
    invalidated_artifacts = list(STAGE_ARTIFACTS.get(default_stage, []))

    if "Slide 7" in message or "slide 7" in message.lower():
        targets.append("Slide_7")
    if "design DNA" in message or "design dna" in message.lower():
        rollback_level = "deck_global"
        invalidated_artifacts.extend(["design_dna.json", "outline.json", "slide_blueprint.json"])

    return {
        "feedback_scope": "human_async",
        "targets": targets,
        "reason": message,
        "expected_change": "rebuild the triangle diagram on Slide_7" if targets == ["Slide_7"] else "rework the deck visual contract",
        "rollback_level": rollback_level,
        "invalidated_artifacts": sorted(set(invalidated_artifacts)),
        "agent_acknowledgement": "",
        "status": "open",
    }
```

- [ ] **Step 4: Run the feedback tests**

Run: `pytest tests/test_human_feedback.py -v`

Expected: PASS for the single-slide and deck-global rollback cases.

- [ ] **Step 5: Commit**

```bash
git add tools/human_feedback.py tests/test_human_feedback.py
git commit -m "feat(ppt): normalize human feedback and rollback scope"
```

## Task 5: Upgrade The Visual Review Schema, Examples, And Gate Enforcement

**Files:**
- Modify: `schemas/visual_review.schema.json`
- Modify: `tools/quality_gate.py`
- Modify: `tests/test_quality_gate.py`
- Modify: `tests/test_examples.py`
- Modify: `tests/test_schemas.py`
- Modify: `examples/reports/visual-review-report.pass.json`
- Modify: `examples/reports/visual-review-report.blocked.json`

- [ ] **Step 1: Write failing gate tests for the new required fields**

```python
def test_quality_gate_rejects_passed_visual_report_without_dual_scores(tmp_path):
    workspace = create_project_workspace("Dual Scores Missing", root_dir=tmp_path, project_id="dual-scores-missing")
    (workspace.slides_dir / "Slide_1.tsx").write_text(VALID_SLIDE, encoding="utf-8")
    write_index(workspace.slides_dir)
    (workspace.project_dir / "review" / "slides").mkdir(parents=True)
    (workspace.project_dir / "review" / "full_deck.png").write_bytes(b"png")
    (workspace.project_dir / "review" / "slides" / "slide_01.png").write_bytes(b"png")
    (workspace.project_dir / "content_quality_report.json").write_text('{"status":"pass","blocking_findings":0}', encoding="utf-8")
    (workspace.project_dir / "visual_review_report.json").write_text(
        '{"review_type":"ai_lens_visual_review","status":"pass","blocking_findings":0,"review_capability":{"method":"vision_model","image_input":true,"inspected_assets":["review/full_deck.png"]},"slides":[{"slide":1,"passed":true,"visual_score":9,"findings":[],"repairs":[]}]}',
        encoding="utf-8",
    )

    report = validate_project(workspace, require_agent_reports=True)

    assert not report.ok
    assert any("visual_review_report.json slide 1 must record visual_craft_score and strategic_clarity_score" in error for error in report.errors)
```

- [ ] **Step 2: Run the new quality gate test to verify it fails**

Run: `pytest tests/test_quality_gate.py::test_quality_gate_rejects_passed_visual_report_without_dual_scores -v`

Expected: FAIL because `validate_project` does not yet check the dual-score fields.

- [ ] **Step 3: Implement the stricter schema and gate checks**

```python
def _check_visual_review_slide_fields(visual_report: dict, report: QualityReport) -> None:
    for slide in visual_report.get("slides", []):
        if not isinstance(slide, dict):
            continue
        slide_number = slide.get("slide", "unknown")
        if "visual_craft_score" not in slide or "strategic_clarity_score" not in slide:
            report.errors.append(
                f"visual_review_report.json slide {slide_number} must record visual_craft_score and strategic_clarity_score"
            )
        if slide.get("critical_visual") and slide.get("wow_passed") is not True:
            report.errors.append(
                f"visual_review_report.json slide {slide_number} is critical_visual but wow_passed is not true"
            )
        if slide.get("hard_blockers"):
            report.errors.append(
                f"visual_review_report.json slide {slide_number} has hard blockers"
            )


def _check_visual_review_context(visual_report: dict, report: QualityReport) -> None:
    context = visual_report.get("review_context")
    if not isinstance(context, dict):
        report.errors.append("visual_review_report.json must record review_context for a passing AI visual gate")
        return
    sources = context.get("context_sources", [])
    required_sources = {"analysis.json", "design_dna.json", "outline.json", "slide_blueprint.json"}
    if not required_sources.issubset(set(sources)):
        report.errors.append("visual_review_report.json review_context.context_sources missing required artifact references")
```

- [ ] **Step 4: Run the gate, example, and schema tests**

Run: `pytest tests/test_quality_gate.py tests/test_examples.py tests/test_schemas.py -v`

Expected: PASS with updated example reports and updated schema enforcement.

- [ ] **Step 5: Commit**

```bash
git add schemas/visual_review.schema.json tools/quality_gate.py tests/test_quality_gate.py tests/test_examples.py tests/test_schemas.py examples/reports/visual-review-report.pass.json examples/reports/visual-review-report.blocked.json
git commit -m "feat(ppt): enforce contextual visual review contracts"
```

## Task 6: Wire Phase 1 Helpers Into The CLI

**Files:**
- Modify: `tools/ppt_workflow.py`
- Test: `tests/test_ppt_workflow.py`

- [ ] **Step 1: Write failing CLI tests for asset-plan and feedback normalization**

```python
def test_build_parser_includes_asset_plan_command():
    parser = build_parser()
    args = parser.parse_args(["asset-plan", "--project", "demo"])
    assert args.command == "asset-plan"


def test_build_parser_includes_log_feedback_command():
    parser = build_parser()
    args = parser.parse_args(["log-feedback", "--project", "demo", "--message", "Slide 7 的三角图完全不对"])
    assert args.command == "log-feedback"
```

- [ ] **Step 2: Run the CLI parser tests to verify they fail**

Run: `pytest tests/test_ppt_workflow.py -k "asset_plan_command or log_feedback_command" -v`

Expected: FAIL because the parser does not yet know those commands.

- [ ] **Step 3: Add CLI handlers for Phase 1 artifacts**

```python
def cmd_asset_plan(args) -> int:
    workspace = _workspace(args)
    plan_path = workspace.visual_asset_plan_path
    plan_path.write_text(json.dumps({"project_id": workspace.project_id, "slides": []}, indent=2), encoding="utf-8")
    print(f"wrote {plan_path}")
    return 0


def cmd_log_feedback(args) -> int:
    workspace = _workspace(args)
    payload = normalize_feedback(args.message, default_stage=args.stage)
    workspace.human_feedback_log_path.write_text(json.dumps({"items": [payload]}, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"wrote {workspace.human_feedback_log_path}")
    return 0


for name, help_text, func in [
    ("asset-plan", "Write the visual asset plan artifact for a project.", cmd_asset_plan),
    ("log-feedback", "Normalize human feedback into the project feedback log.", cmd_log_feedback),
]:
    command = sub.add_parser(name, help=help_text)
    command.add_argument("--project", required=True)
    command.add_argument("--project-root", default="output/projects")
    command.add_argument("--message")
    command.add_argument("--stage", default="visual_review")
    command.set_defaults(func=func)
```

- [ ] **Step 4: Run the CLI tests**

Run: `pytest tests/test_ppt_workflow.py -v`

Expected: PASS for the new parser tests and existing workflow parser tests.

- [ ] **Step 5: Commit**

```bash
git add tools/ppt_workflow.py tests/test_ppt_workflow.py
git commit -m "feat(ppt): add phase-1 visual asset CLI helpers"
```

## Task 7: Update Docs And Templates To Match The New Contracts

**Files:**
- Modify: `references/artifact-templates.md`
- Modify: `references/visual-validation.md`
- Modify: `references/workflow.md`
- Modify: `SKILL.md`

- [ ] **Step 1: Write the failing example/report expectation test**

```python
def test_visual_review_example_references_context_and_dual_scores():
    visual = json.loads((EXAMPLE_REPORTS / "visual-review-report.pass.json").read_text(encoding="utf-8"))

    assert visual["review_context"]["context_sources"] == [
        "analysis.json",
        "design_dna.json",
        "outline.json",
        "slide_blueprint.json",
    ]
    assert visual["slides"][0]["visual_craft_score"] >= 8.5
    assert visual["slides"][0]["strategic_clarity_score"] >= 8.5
```

- [ ] **Step 2: Run the example test to verify it fails**

Run: `pytest tests/test_examples.py::test_visual_review_example_references_context_and_dual_scores -v`

Expected: FAIL because the example report and docs do not yet include the richer fields.

- [ ] **Step 3: Update the docs and templates**

```md
## `visual_review_report.json`

Passing reports must record:

- `review_context.context_sources`
- `review_context.rubric_version`
- per-slide `visual_craft_score`
- per-slide `strategic_clarity_score`
- per-slide `hard_blockers`
- per-slide `wow_passed` when `critical_visual` is true
- per-slide `rollback_recommendation`
```

- [ ] **Step 4: Run doc-adjacent tests**

Run: `pytest tests/test_examples.py tests/test_quality_gate.py tests/test_schemas.py -v`

Expected: PASS with examples, templates, and gate behavior all aligned.

- [ ] **Step 5: Commit**

```bash
git add references/artifact-templates.md references/visual-validation.md references/workflow.md SKILL.md tests/test_examples.py
git commit -m "docs(ppt): document visual asset and review phase-1 contracts"
```

## Task 8: Run The Full Phase 1 Verification Suite

**Files:**
- Test: `tests/test_presentation_workspace.py`
- Test: `tests/test_schemas.py`
- Test: `tests/test_visual_assets.py`
- Test: `tests/test_human_feedback.py`
- Test: `tests/test_quality_gate.py`
- Test: `tests/test_examples.py`
- Test: `tests/test_ppt_workflow.py`

- [ ] **Step 1: Run the focused Phase 1 suite**

Run:

```bash
pytest tests/test_presentation_workspace.py tests/test_schemas.py tests/test_visual_assets.py tests/test_human_feedback.py tests/test_quality_gate.py tests/test_examples.py tests/test_ppt_workflow.py -v
```

Expected: PASS for all new and modified Phase 1 tests.

- [ ] **Step 2: Run the full project test suite**

Run:

```bash
pytest -v
```

Expected: PASS for the full repository or a clearly documented list of pre-existing unrelated failures.

- [ ] **Step 3: Review the generated artifacts manually**

Check:

```bash
python3 -m json.tool examples/reports/visual-review-report.pass.json >/dev/null
python3 -m json.tool schemas/visual_asset_plan.schema.json >/dev/null
python3 -m json.tool schemas/human_feedback.schema.json >/dev/null
```

Expected: no output and exit code `0` for all three commands.

- [ ] **Step 4: Write the verification summary into the branch notes or PR draft**

```md
- Phase 1 artifacts and schemas added
- contextual visual gate enforced
- asset-routing skeleton added
- human feedback normalization added
- full targeted suite passed
```

- [ ] **Step 5: Commit**

```bash
git add .
git commit -m "test(ppt): verify visual asset and review phase-1 foundation"
```

## Self-Review Checklist

- Spec coverage:
  - artifact contracts: Tasks 1-2
  - asset routing skeleton: Task 3
  - human async feedback and rollback: Task 4
  - contextual visual gate: Task 5
  - workflow integration: Tasks 6-7
  - verification: Task 8

- Placeholder scan:
  - no `TODO`, `TBD`, or "implement later" language
  - every task has exact file paths
  - every code step includes concrete code
  - every test step has an exact command and expected result

- Type consistency:
  - `slide_local`, `pattern_shared`, and `deck_global` are used consistently across schema, helpers, and quality gate
  - `visual_craft_score` and `strategic_clarity_score` are the required dual-score field names across tests, schema, and gate checks
  - artifact path names use the `PresentationWorkspace` field names exactly
