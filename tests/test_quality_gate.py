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
