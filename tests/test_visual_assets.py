from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

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


def test_build_asset_plan_entry_uses_default_candidate_count_for_normal_slide():
    entry = build_asset_plan_entry(
        slide=2,
        critical_visual=False,
        asset_intent={
            "visual_role": "supporting_evidence",
            "asset_goal": "Support the title with a real-world image.",
            "candidate_asset_types": ["image_search", "image_generation"],
            "must_show": ["teacher and student"],
            "must_avoid": ["diagram"],
            "wow_goal": "photo credibility",
        },
    )

    slot = entry["asset_slots"][0]

    assert slot["primary_route"] == "image_search"
    assert slot["candidate_count"] == 3
    assert slot["independent_asset_review"] is False
