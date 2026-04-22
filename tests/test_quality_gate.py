from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

from tools.presentation_workspace import create_project_workspace
from tools.quality_gate import validate_project


VALID_SLIDE = """
import { getDeckStylePreset, styleVars } from '../../styles'

export default function Slide_1() {
  const preset = getDeckStylePreset('aurora-borealis')
  return (
    <div style={styleVars(preset)} data-ppt-slide="1">
      <h1 data-ppt-text="true">Valid</h1>
    </div>
  )
}
""".strip()


def write_index(slides_dir: Path) -> None:
    (slides_dir / "index.ts").write_text(
        "import Slide_1 from './Slide_1'\n\nexport default [Slide_1]\n",
        encoding="utf-8",
    )


def test_validate_project_passes_for_minimal_valid_deck(tmp_path):
    workspace = create_project_workspace("Valid Deck", root_dir=tmp_path, project_id="valid")
    (workspace.slides_dir / "Slide_1.tsx").write_text(VALID_SLIDE, encoding="utf-8")
    write_index(workspace.slides_dir)

    report = validate_project(workspace)

    assert report.ok
    assert report.errors == []


def test_validate_project_fails_without_slide_marker(tmp_path):
    workspace = create_project_workspace("Invalid Deck", root_dir=tmp_path, project_id="invalid")
    (workspace.slides_dir / "Slide_1.tsx").write_text(
        VALID_SLIDE.replace(' data-ppt-slide="1"', ""),
        encoding="utf-8",
    )
    write_index(workspace.slides_dir)

    report = validate_project(workspace)

    assert not report.ok
    assert any("data-ppt-slide" in error for error in report.errors)


def test_validate_project_fails_without_any_text_marker(tmp_path):
    workspace = create_project_workspace("No Text Deck", root_dir=tmp_path, project_id="no-text")
    (workspace.slides_dir / "Slide_1.tsx").write_text(
        VALID_SLIDE.replace(' data-ppt-text="true"', ""),
        encoding="utf-8",
    )
    write_index(workspace.slides_dir)

    report = validate_project(workspace)

    assert not report.ok
    assert any("data-ppt-text" in error for error in report.errors)


def test_validate_project_checks_manifest_asset_paths(tmp_path):
    workspace = create_project_workspace("Manifest Deck", root_dir=tmp_path, project_id="manifest")
    (workspace.slides_dir / "Slide_1.tsx").write_text(VALID_SLIDE, encoding="utf-8")
    write_index(workspace.slides_dir)
    workspace.manifest_path.write_text(
        '{"slides":[{"index":0,"bg_path":"missing.png","components":[{"path":"also-missing.png"}],"texts":[]}]}',
        encoding="utf-8",
    )

    report = validate_project(workspace)

    assert not report.ok
    assert any("missing asset" in error for error in report.errors)


def test_quality_gate_rejects_empty_item_group(tmp_path):
    workspace = create_project_workspace("Item Deck", root_dir=tmp_path, project_id="item-deck")
    (workspace.slides_dir / "Slide_1.tsx").write_text(VALID_SLIDE, encoding="utf-8")
    write_index(workspace.slides_dir)
    workspace.manifest_path.write_text(
        '{"slides":[{"index":0,"groups":[{"id":"group_0_0","kind":"list","items":[]}],"texts":[]}]}',
        encoding="utf-8",
    )

    report = validate_project(workspace)

    assert not report.ok
    assert any("has no items" in error for error in report.errors)


def test_quality_gate_rejects_empty_manifest_slides(tmp_path):
    workspace = create_project_workspace("Empty Manifest", root_dir=tmp_path, project_id="empty-manifest")
    (workspace.slides_dir / "Slide_1.tsx").write_text(VALID_SLIDE, encoding="utf-8")
    write_index(workspace.slides_dir)
    workspace.manifest_path.write_text('{"slides":[]}', encoding="utf-8")

    report = validate_project(workspace)

    assert not report.ok
    assert any("manifest contains no slides" in error for error in report.errors)


def test_quality_gate_rejects_wrong_renderer_style_import(tmp_path):
    workspace = create_project_workspace("Bad Import Deck", root_dir=tmp_path, project_id="bad-import")
    (workspace.slides_dir / "Slide_1.tsx").write_text(
        VALID_SLIDE.replace("../../styles", "../../../web/src/styles/presets"),
        encoding="utf-8",
    )
    write_index(workspace.slides_dir)

    report = validate_project(workspace)

    assert not report.ok
    assert any("use ../../styles" in error for error in report.errors)


def test_quality_gate_rejects_index_missing_slide_export(tmp_path):
    workspace = create_project_workspace("Index Deck", root_dir=tmp_path, project_id="index-deck")
    (workspace.slides_dir / "Slide_1.tsx").write_text(VALID_SLIDE, encoding="utf-8")
    (workspace.slides_dir / "Slide_2.tsx").write_text(
        VALID_SLIDE.replace("Slide_1", "Slide_2").replace('data-ppt-slide="1"', 'data-ppt-slide="2"'),
        encoding="utf-8",
    )
    write_index(workspace.slides_dir)

    report = validate_project(workspace)

    assert not report.ok
    assert any("index.ts must import Slide_2" in error for error in report.errors)
    assert any("index.ts must export Slide_2" in error for error in report.errors)


def test_quality_gate_rejects_blocked_content_report(tmp_path):
    workspace = create_project_workspace("Blocked Content", root_dir=tmp_path, project_id="blocked-content")
    (workspace.slides_dir / "Slide_1.tsx").write_text(VALID_SLIDE, encoding="utf-8")
    write_index(workspace.slides_dir)
    (workspace.project_dir / "content_quality_report.json").write_text(
        '{"status":"needs_revision","blocking_findings":2}',
        encoding="utf-8",
    )

    report = validate_project(workspace)

    assert not report.ok
    assert any("content_quality_report.json status is needs_revision" in error for error in report.errors)
    assert any("content_quality_report.json has 2 blocking findings" in error for error in report.errors)


def test_quality_gate_rejects_blocked_visual_review_report(tmp_path):
    workspace = create_project_workspace("Blocked Visual", root_dir=tmp_path, project_id="blocked-visual")
    (workspace.slides_dir / "Slide_1.tsx").write_text(VALID_SLIDE, encoding="utf-8")
    write_index(workspace.slides_dir)
    (workspace.project_dir / "visual_review_report.json").write_text(
        '{"status":"blocked","blocking_findings":1}',
        encoding="utf-8",
    )

    report = validate_project(workspace)

    assert not report.ok
    assert any("visual_review_report.json status is blocked" in error for error in report.errors)
    assert any("visual_review_report.json has 1 blocking findings" in error for error in report.errors)


def test_quality_gate_requires_content_report_when_requested(tmp_path):
    workspace = create_project_workspace("Missing Content Gate", root_dir=tmp_path, project_id="missing-content")
    (workspace.slides_dir / "Slide_1.tsx").write_text(VALID_SLIDE, encoding="utf-8")
    write_index(workspace.slides_dir)

    report = validate_project(workspace, require_agent_reports=True)

    assert not report.ok
    assert any("missing required content_quality_report.json" in error for error in report.errors)


def test_quality_gate_requires_ai_visual_report_when_requested(tmp_path):
    workspace = create_project_workspace("Missing Visual Gate", root_dir=tmp_path, project_id="missing-visual")
    (workspace.slides_dir / "Slide_1.tsx").write_text(VALID_SLIDE, encoding="utf-8")
    write_index(workspace.slides_dir)
    (workspace.project_dir / "content_quality_report.json").write_text(
        '{"status":"pass","blocking_findings":0}',
        encoding="utf-8",
    )

    report = validate_project(workspace, require_agent_reports=True)

    assert not report.ok
    assert any("missing required visual_review_report.json" in error for error in report.errors)


def test_quality_gate_accepts_passed_required_agent_reports(tmp_path):
    workspace = create_project_workspace("Passed Gates", root_dir=tmp_path, project_id="passed-gates")
    (workspace.slides_dir / "Slide_1.tsx").write_text(VALID_SLIDE, encoding="utf-8")
    write_index(workspace.slides_dir)
    (workspace.project_dir / "content_quality_report.json").write_text(
        '{"status":"pass","blocking_findings":0}',
        encoding="utf-8",
    )
    (workspace.project_dir / "visual_review_report.json").write_text(
        '{"status":"pass","blocking_findings":0}',
        encoding="utf-8",
    )

    report = validate_project(workspace, require_agent_reports=True)

    assert report.ok


def test_quality_gate_rejects_passed_content_report_with_unresolved_revisions(tmp_path):
    workspace = create_project_workspace("Unresolved Content", root_dir=tmp_path, project_id="unresolved-content")
    (workspace.slides_dir / "Slide_1.tsx").write_text(VALID_SLIDE, encoding="utf-8")
    write_index(workspace.slides_dir)
    (workspace.project_dir / "content_quality_report.json").write_text(
        '{"status":"pass","blocking_findings":0,"required_revisions":["Fix audience"],"resolution_log":[]}',
        encoding="utf-8",
    )
    (workspace.project_dir / "visual_review_report.json").write_text(
        '{"status":"pass","blocking_findings":0}',
        encoding="utf-8",
    )

    report = validate_project(workspace, require_agent_reports=True)

    assert not report.ok
    assert any("content_quality_report.json has unresolved required revisions" in error for error in report.errors)


def test_quality_gate_rejects_passed_content_report_with_open_resolution_log_item(tmp_path):
    workspace = create_project_workspace("Open Content Log", root_dir=tmp_path, project_id="open-content-log")
    (workspace.slides_dir / "Slide_1.tsx").write_text(VALID_SLIDE, encoding="utf-8")
    write_index(workspace.slides_dir)
    (workspace.project_dir / "content_quality_report.json").write_text(
        '{"status":"pass","blocking_findings":0,"required_revisions":[],"resolution_log":[{"id":"C1","status":"open"}]}',
        encoding="utf-8",
    )
    (workspace.project_dir / "visual_review_report.json").write_text(
        '{"status":"pass","blocking_findings":0}',
        encoding="utf-8",
    )

    report = validate_project(workspace, require_agent_reports=True)

    assert not report.ok
    assert any("content_quality_report.json has unresolved resolution log items" in error for error in report.errors)


def test_quality_gate_rejects_passed_visual_report_with_failed_slide(tmp_path):
    workspace = create_project_workspace("Failed Visual Slide", root_dir=tmp_path, project_id="failed-visual-slide")
    (workspace.slides_dir / "Slide_1.tsx").write_text(VALID_SLIDE, encoding="utf-8")
    write_index(workspace.slides_dir)
    (workspace.project_dir / "content_quality_report.json").write_text(
        '{"status":"pass","blocking_findings":0}',
        encoding="utf-8",
    )
    (workspace.project_dir / "visual_review_report.json").write_text(
        '{"status":"pass","blocking_findings":0,"slides":[{"slide":1,"passed":false,"findings":["Weak focal point"],"repairs":[]}]}',
        encoding="utf-8",
    )

    report = validate_project(workspace, require_agent_reports=True)

    assert not report.ok
    assert any("visual_review_report.json has slides not passed" in error for error in report.errors)


def test_quality_gate_rejects_passed_visual_report_with_open_repair_log_item(tmp_path):
    workspace = create_project_workspace("Open Visual Repair", root_dir=tmp_path, project_id="open-visual-repair")
    (workspace.slides_dir / "Slide_1.tsx").write_text(VALID_SLIDE, encoding="utf-8")
    write_index(workspace.slides_dir)
    (workspace.project_dir / "content_quality_report.json").write_text(
        '{"status":"pass","blocking_findings":0}',
        encoding="utf-8",
    )
    (workspace.project_dir / "visual_review_report.json").write_text(
        '{"status":"pass","blocking_findings":0,"repair_log":[{"id":"V1","status":"open"}],"slides":[{"slide":1,"passed":true,"findings":[],"repairs":[]}]}',
        encoding="utf-8",
    )

    report = validate_project(workspace, require_agent_reports=True)

    assert not report.ok
    assert any("visual_review_report.json has unresolved repair log items" in error for error in report.errors)
