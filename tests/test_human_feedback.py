from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

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
