import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

from tools.presentation_workspace import create_project_workspace
import tools.visual_assets as visual_assets
from tools.visual_assets import (
    build_asset_plan_entry,
    build_visual_asset_manifest,
    build_visual_asset_plan,
)


def write_blueprint(workspace, slides):
    workspace.slide_blueprint_path.write_text(
        json.dumps({"slides": slides}, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )


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


def test_build_visual_asset_plan_writes_routes_from_blueprint(tmp_path):
    workspace = create_project_workspace("Asset Plan Deck", root_dir=tmp_path, project_id="asset-plan-deck")
    write_blueprint(
        workspace,
        [
            {
                "slide": 1,
                "title": "Role Triangle",
                "critical_visual": True,
                "asset_intent": {
                    "visual_role": "core_explainer",
                    "asset_goal": "Explain the three-role model.",
                    "candidate_asset_types": ["diagram/svg", "image_generation"],
                    "must_show": ["Designer", "Partner", "Gatekeeper"],
                    "must_avoid": ["generic card grid"],
                    "wow_goal": "diagram invention",
                },
            },
            {
                "slide": 2,
                "title": "Real Classroom",
                "critical_visual": False,
                "asset_intent": {
                    "visual_role": "supporting_evidence",
                    "asset_goal": "Show a real classroom context.",
                    "candidate_asset_types": ["image_search", "image_generation"],
                    "must_show": ["teacher", "student"],
                    "must_avoid": ["diagram"],
                    "wow_goal": "photo credibility",
                },
            },
        ],
    )

    plan = build_visual_asset_plan(workspace)

    assert workspace.visual_asset_plan_path.is_file()
    assert plan["slides"][0]["asset_slots"][0]["primary_route"] == "diagram/svg"
    assert plan["slides"][0]["asset_slots"][0]["candidate_count"] == 5
    assert plan["slides"][1]["asset_slots"][0]["primary_route"] == "image_search"


def test_build_visual_asset_manifest_generates_diagram_svg_candidates(tmp_path):
    workspace = create_project_workspace("Diagram Deck", root_dir=tmp_path, project_id="diagram-deck")
    write_blueprint(
        workspace,
        [
            {
                "slide": 1,
                "title": "Role Triangle",
                "critical_visual": True,
                "asset_intent": {
                    "visual_role": "core_explainer",
                    "asset_goal": "Explain the three-role model.",
                    "candidate_asset_types": ["diagram/svg"],
                    "must_show": ["Designer", "Partner", "Gatekeeper"],
                    "must_avoid": ["generic card grid"],
                    "wow_goal": "diagram invention",
                },
            }
        ],
    )

    build_visual_asset_plan(workspace)
    manifest = build_visual_asset_manifest(workspace)

    assert workspace.visual_asset_manifest_path.is_file()
    asset = manifest["assets"][0]
    assert asset["review_status"] == "approved"
    assert len(asset["candidate_assets"]) == 5
    assert asset["selected_asset"]["path"].endswith(".svg")
    assert (workspace.project_dir / asset["selected_asset"]["path"]).is_file()


def test_build_visual_asset_manifest_generates_chart_svg_candidates(tmp_path):
    workspace = create_project_workspace("Chart Deck", root_dir=tmp_path, project_id="chart-deck")
    write_blueprint(
        workspace,
        [
            {
                "slide": 1,
                "title": "Growth Chart",
                "critical_visual": False,
                "asset_intent": {
                    "visual_role": "data_evidence",
                    "asset_goal": "Show the growth trend clearly.",
                    "candidate_asset_types": ["chart"],
                    "must_show": ["2023", "2024", "2025"],
                    "must_avoid": ["photo"],
                    "wow_goal": "editorial chart clarity",
                    "data_points": [
                        {"label": "2023", "value": 42},
                        {"label": "2024", "value": 58},
                        {"label": "2025", "value": 81}
                    ]
                },
            }
        ],
    )

    build_visual_asset_plan(workspace)
    manifest = build_visual_asset_manifest(workspace)

    asset = manifest["assets"][0]
    assert asset["review_status"] == "approved"
    assert len(asset["candidate_assets"]) == 3
    assert asset["selected_asset"]["path"].endswith(".svg")


def test_build_visual_asset_manifest_marks_unconfigured_image_search_as_blocked(tmp_path, monkeypatch):
    monkeypatch.delenv("UNSPLASH_ACCESS_KEY", raising=False)
    monkeypatch.delenv("PEXELS_API_KEY", raising=False)
    monkeypatch.delenv("PIXABAY_API_KEY", raising=False)
    workspace = create_project_workspace("Search Deck", root_dir=tmp_path, project_id="search-deck")
    write_blueprint(
        workspace,
        [
            {
                "slide": 1,
                "title": "Real Classroom",
                "critical_visual": False,
                "asset_intent": {
                    "visual_role": "supporting_evidence",
                    "asset_goal": "Show a real classroom context.",
                    "candidate_asset_types": ["image_search"],
                    "must_show": ["teacher", "student"],
                    "must_avoid": ["diagram"],
                    "wow_goal": "photo credibility",
                },
            }
        ],
    )

    build_visual_asset_plan(workspace)
    manifest = build_visual_asset_manifest(workspace)

    asset = manifest["assets"][0]
    assert asset["review_status"] == "blocked"
    assert asset["selected_asset"]["status"] == "unavailable"


def test_build_visual_asset_manifest_fetches_configured_image_search_candidates(tmp_path, monkeypatch):
    workspace = create_project_workspace("Search Deck", root_dir=tmp_path, project_id="search-deck")
    write_blueprint(
        workspace,
        [
            {
                "slide": 1,
                "title": "Real Classroom",
                "critical_visual": False,
                "asset_intent": {
                    "visual_role": "supporting_evidence",
                    "asset_goal": "Show a real classroom context.",
                    "candidate_asset_types": ["image_search"],
                    "must_show": ["teacher", "student"],
                    "must_avoid": ["diagram"],
                    "wow_goal": "photo credibility",
                },
            }
        ],
    )
    build_visual_asset_plan(workspace)

    def fake_search(*, query, candidate_count, workspace_root, asset_prefix):
        path = workspace_root / f"{asset_prefix}.jpg"
        path.write_bytes(b"img")
        return [
            {
                "candidate_id": "search-1",
                "path": path.relative_to(workspace.project_dir).as_posix(),
                "status": "ready",
                "score": 8.9,
                "source_provider": "unsplash",
                "license_metadata": {"provider": "unsplash"},
                "resolution_metadata": {"width": 1600, "height": 900},
            }
        ]

    monkeypatch.setattr(visual_assets, "search_image_candidates", fake_search)

    manifest = build_visual_asset_manifest(workspace)

    asset = manifest["assets"][0]
    assert asset["review_status"] == "approved"
    assert asset["selected_asset"]["source_provider"] == "unsplash"


def test_build_visual_asset_manifest_fetches_configured_generated_images(tmp_path, monkeypatch):
    workspace = create_project_workspace("Hero Deck", root_dir=tmp_path, project_id="hero-deck")
    write_blueprint(
        workspace,
        [
            {
                "slide": 1,
                "title": "AI Teaching Future",
                "critical_visual": True,
                "asset_intent": {
                    "visual_role": "hero_anchor",
                    "asset_goal": "Create a premium hero visual for future teaching.",
                    "candidate_asset_types": ["image_generation"],
                    "must_show": ["teacher", "AI", "classroom"],
                    "must_avoid": ["stock-photo look"],
                    "wow_goal": "hero atmosphere",
                },
            }
        ],
    )
    build_visual_asset_plan(workspace)

    def fake_generate(*, prompt, candidate_count, workspace_root, asset_prefix):
        path = workspace_root / f"{asset_prefix}.png"
        path.write_bytes(b"png")
        return [
            {
                "candidate_id": "gen-1",
                "path": path.relative_to(workspace.project_dir).as_posix(),
                "status": "ready",
                "score": 9.1,
                "source_provider": "gemini",
                "license_metadata": {"provider": "gemini"},
                "resolution_metadata": {"width": 1024, "height": 1024},
            }
        ]

    monkeypatch.setattr(visual_assets, "generate_image_candidates", fake_generate)

    manifest = build_visual_asset_manifest(workspace)

    asset = manifest["assets"][0]
    assert asset["review_status"] == "approved"
    assert asset["selected_asset"]["source_provider"] == "gemini"
