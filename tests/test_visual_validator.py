from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

from tools.presentation_workspace import create_project_workspace
from tools.visual_validator import _manifest_slide_texts, VisualSlideFinding


def test_manifest_slide_texts_recurses_into_groups():
    slide = {
        "texts": [{"style": {"text": "Root title"}}],
        "groups": [
            {
                "items": [
                    {"texts": [{"style": {"text": "Nested item"}}]},
                    {"texts": [{"style": {"text": "Another item"}}]},
                ]
            }
        ],
    }

    assert _manifest_slide_texts(slide) == ["Root title", "Nested item", "Another item"]


def test_visual_slide_finding_ok_when_no_issues():
    finding = VisualSlideFinding(slide=1)
    assert finding.ok


def test_create_project_workspace_keeps_expected_paths(tmp_path):
    workspace = create_project_workspace("Visual Deck", root_dir=tmp_path, project_id="visual")
    assert workspace.project_dir == tmp_path / "visual"
