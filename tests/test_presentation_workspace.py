from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

from tools.presentation_workspace import (
    PresentationWorkspace,
    create_project_workspace,
    slugify_project_name,
)


def test_slugify_project_name_keeps_readable_ascii():
    assert slugify_project_name("AI Strategy: Q1/Q2 2026!") == "ai-strategy-q1-q2-2026"


def test_create_project_workspace_builds_isolated_paths(tmp_path):
    workspace = create_project_workspace(
        "AI Strategy",
        root_dir=tmp_path,
        project_id="20260421-120000-ai-strategy",
    )

    assert isinstance(workspace, PresentationWorkspace)
    assert workspace.project_dir == tmp_path / "20260421-120000-ai-strategy"
    assert workspace.assets_dir == workspace.project_dir / "assets"
    assert workspace.fonts_dir == workspace.project_dir / "fonts"
    assert workspace.slides_dir == workspace.project_dir / "slides"
    assert workspace.manifest_path == workspace.project_dir / "layout_manifest.json"
    assert workspace.pptx_path == workspace.project_dir / "presentation.pptx"
    assert workspace.html_dir == workspace.project_dir / "presentation-html"
    assert workspace.metadata_path == workspace.project_dir / "project.json"

    assert workspace.assets_dir.is_dir()
    assert workspace.fonts_dir.is_dir()
    assert workspace.slides_dir.is_dir()
    assert workspace.metadata_path.is_file()


def test_create_project_workspace_includes_visual_asset_contract_paths(tmp_path):
    workspace = create_project_workspace(
        "Visual Asset Deck",
        root_dir=tmp_path,
        project_id="20260423-090000-visual-asset-deck",
    )

    assert workspace.project_dir == tmp_path / "20260423-090000-visual-asset-deck"
    assert workspace.slide_blueprint_path == workspace.project_dir / "slide_blueprint.json"
    assert workspace.visual_asset_research_path == workspace.project_dir / "visual_asset_research.json"
    assert workspace.visual_asset_plan_path == workspace.project_dir / "visual_asset_plan.json"
    assert workspace.visual_asset_manifest_path == workspace.project_dir / "visual_asset_manifest.json"
    assert workspace.font_manifest_path == workspace.project_dir / "font_assets_manifest.json"
    assert workspace.font_css_path == workspace.project_dir / "font-face.css"
    assert workspace.human_feedback_log_path == workspace.project_dir / "human_feedback_log.json"


def test_workspace_rejects_path_traversal_ids(tmp_path):
    try:
        create_project_workspace("Bad", root_dir=tmp_path, project_id="../bad")
    except ValueError as exc:
        assert "project_id" in str(exc)
    else:
        raise AssertionError("expected path traversal project_id to fail")
