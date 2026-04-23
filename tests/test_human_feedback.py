import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

from tools.human_feedback import apply_feedback, normalize_feedback
from tools.presentation_workspace import create_project_workspace


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


def test_apply_feedback_appends_items_to_workspace_log(tmp_path):
    workspace = create_project_workspace("Feedback Deck", root_dir=tmp_path, project_id="feedback-deck")

    first = apply_feedback(workspace, "Slide 7 的三角图完全不对，回到 visual review 重做", default_stage="visual_review")
    second = apply_feedback(workspace, "整体颜色太保守，回到 design DNA", default_stage="visual_review")

    data = json.loads(workspace.human_feedback_log_path.read_text(encoding="utf-8"))

    assert first["rollback_level"] == "slide_local"
    assert second["rollback_level"] == "deck_global"
    assert len(data["items"]) == 2
    assert data["items"][0]["targets"] == ["Slide_7"]
    assert data["items"][1]["restart_stage"] == "design_dna"
