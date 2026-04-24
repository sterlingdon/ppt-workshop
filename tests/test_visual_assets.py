import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

from tools.presentation_workspace import create_project_workspace
import tools.visual_assets as visual_assets
from tools.visual_asset_providers import ProviderUnavailableError
from tools.visual_assets import (
    build_asset_plan_entry,
    build_visual_asset_manifest,
    build_visual_asset_plan,
    build_visual_asset_research,
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


def test_build_asset_plan_entry_prefers_image_generation_for_critical_editorial_slides():
    entry = build_asset_plan_entry(
        slide=3,
        critical_visual=True,
        asset_intent={
            "visual_role": "hero",
            "asset_goal": "Show a real-world AI classroom scene with editorial impact.",
            "candidate_asset_types": ["diagram/svg", "image_generation"],
            "must_show": ["teacher", "student", "screen glow"],
            "must_avoid": ["flat diagram"],
            "wow_goal": "full-bleed editorial photography",
        },
    )

    slot = entry["asset_slots"][0]

    assert slot["primary_route"] == "image_generation"
    assert slot["candidate_count"] == 5
    assert slot["independent_asset_review"] is True


def test_build_asset_plan_entry_uses_default_candidate_count_for_normal_slide():
    entry = build_asset_plan_entry(
        slide=2,
        critical_visual=False,
        asset_intent={
            "visual_role": "supporting_evidence",
            "asset_goal": "Support the title with a real-world image.",
            "candidate_asset_types": ["image_generation"],
            "must_show": ["teacher and student"],
            "must_avoid": ["diagram"],
            "wow_goal": "photo credibility",
        },
    )

    slot = entry["asset_slots"][0]

    assert slot["primary_route"] == "image_generation"
    assert slot["candidate_count"] == 3
    assert slot["independent_asset_review"] is False


def test_build_asset_plan_entry_keeps_supported_fallback_routes_only():
    entry = build_asset_plan_entry(
        slide=4,
        critical_visual=True,
        asset_intent={
            "visual_role": "hero",
            "asset_goal": "Show a child opening a window to the world.",
            "candidate_asset_types": ["image_generation", "diagram/svg"],
            "must_show": ["window", "child silhouette"],
            "must_avoid": ["generic stock photo"],
            "wow_goal": "editorial opener",
        },
    )

    slot = entry["asset_slots"][0]

    assert slot["primary_route"] == "image_generation"
    assert slot["fallback_routes"] == ["diagram/svg"]


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
                    "candidate_asset_types": ["image_generation"],
                    "must_show": ["teacher", "student"],
                    "must_avoid": ["diagram"],
                    "wow_goal": "photo credibility",
                },
            },
        ],
    )

    plan = build_visual_asset_plan(workspace)

    assert workspace.visual_asset_plan_path.is_file()
    assert workspace.visual_asset_research_path.is_file()
    assert plan["slides"][0]["asset_slots"][0]["primary_route"] == "diagram/svg"
    assert plan["slides"][0]["asset_slots"][0]["candidate_count"] == 5
    assert plan["slides"][1]["asset_slots"][0]["primary_route"] == "image_generation"
    assert plan["slides"][1]["asset_slots"][0]["selection_criteria"]
    assert plan["slides"][1]["asset_slots"][0]["placement_contract"]["mode"] == "supportive"


def test_build_visual_asset_plan_prefers_image_route_for_critical_scene_slide(tmp_path):
    workspace = create_project_workspace("Scene Deck", root_dir=tmp_path, project_id="scene-deck")
    write_blueprint(
        workspace,
        [
            {
                "slide": 1,
                "title": "AI Classroom Future",
                "critical_visual": True,
                "asset_intent": {
                    "visual_role": "hero",
                    "asset_goal": "Show a cinematic classroom scene.",
                    "candidate_asset_types": ["diagram/svg", "image_generation"],
                    "must_show": ["teacher", "student"],
                    "must_avoid": ["generic corporate diagram"],
                    "wow_goal": "editorial cover image",
                },
            }
        ],
    )

    plan = build_visual_asset_plan(workspace)

    assert plan["slides"][0]["asset_slots"][0]["primary_route"] == "image_generation"
    assert plan["slides"][0]["asset_slots"][0]["premium_fallback_required"] is True


def test_build_visual_asset_research_writes_reject_and_search_guidance(tmp_path):
    workspace = create_project_workspace("Research Deck", root_dir=tmp_path, project_id="research-deck")
    write_blueprint(
        workspace,
        [
            {
                "slide": 1,
                "title": "World Window",
                "critical_visual": True,
                "asset_intent": {
                    "visual_role": "hero",
                    "asset_goal": "Show children looking out to the world through news and context.",
                    "candidate_asset_types": ["image_generation", "diagram/svg"],
                    "must_show": ["window", "newspaper", "child silhouette"],
                    "must_avoid": ["generic classroom stock photo"],
                    "wow_goal": "editorial cover atmosphere",
                    "visual_cues": ["editorial photography", "warm paper tones"],
                },
            }
        ],
    )

    research = build_visual_asset_research(workspace)

    assert workspace.visual_asset_research_path.is_file()
    assert research["slides"][0]["research_query"]
    assert "generic classroom stock photo" in research["slides"][0]["reject_if"]
    assert "editorial photography" in research["slides"][0]["research_tags"]


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


def test_build_visual_asset_manifest_marks_unconfigured_image_generation_as_blocked(tmp_path, monkeypatch):
    workspace = create_project_workspace("Generation Deck", root_dir=tmp_path, project_id="generation-deck")
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
                    "candidate_asset_types": ["image_generation"],
                    "must_show": ["teacher", "student"],
                    "must_avoid": ["diagram"],
                    "wow_goal": "photo credibility",
                },
            }
        ],
    )

    build_visual_asset_plan(workspace)

    def fake_generate(*, prompt, candidate_count, workspace_root, asset_prefix):
        raise ProviderUnavailableError("no generation providers configured")

    monkeypatch.setattr(visual_assets, "generate_image_candidates", fake_generate)
    manifest = build_visual_asset_manifest(workspace)

    asset = manifest["assets"][0]
    assert asset["review_status"] == "blocked"
    assert asset["selected_asset"]["status"] == "unavailable"


def test_build_visual_asset_manifest_falls_back_to_diagram_when_generation_is_blocked(tmp_path, monkeypatch):
    workspace = create_project_workspace("Fallback Deck", root_dir=tmp_path, project_id="fallback-deck")
    write_blueprint(
        workspace,
        [
            {
                "slide": 1,
                "title": "World Window",
                "critical_visual": True,
                "asset_intent": {
                    "visual_role": "hero",
                    "asset_goal": "Show an editorial world-window moment.",
                    "candidate_asset_types": ["image_generation", "diagram/svg"],
                    "must_show": ["window", "world"],
                    "must_avoid": ["weak placeholder"],
                    "wow_goal": "editorial cover atmosphere",
                },
            }
        ],
    )

    build_visual_asset_plan(workspace)

    def fake_generate(*, prompt, candidate_count, workspace_root, asset_prefix):
        raise ProviderUnavailableError("no generation providers configured")

    monkeypatch.setattr(visual_assets, "generate_image_candidates", fake_generate)
    manifest = build_visual_asset_manifest(workspace)

    asset = manifest["assets"][0]
    assert asset["asset_type"] == "diagram/svg"
    assert asset["fallback_applied"]["used"] is True
    assert asset["fallback_applied"]["from_route"] == "image_generation"
    assert asset["fallback_applied"]["to_route"] == "diagram/svg"
    assert asset["review_status"] == "approved"
    assert asset["candidate_ranking"][0]["candidate_id"] == asset["selected_asset"]["candidate_id"]


def test_build_visual_asset_manifest_uses_generation_candidates(tmp_path, monkeypatch):
    workspace = create_project_workspace("Generation Deck", root_dir=tmp_path, project_id="generation-deck")
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
                    "candidate_asset_types": ["image_generation"],
                    "must_show": ["teacher", "student"],
                    "must_avoid": ["diagram"],
                    "wow_goal": "photo credibility",
                },
            }
        ],
    )
    build_visual_asset_plan(workspace)

    def fake_generate(*, prompt, candidate_count, workspace_root, asset_prefix):
        path = workspace_root / f"{asset_prefix}.jpg"
        path.write_bytes(b"img")
        return [
            {
                "candidate_id": "gen-1",
                "path": path.relative_to(workspace.project_dir).as_posix(),
                "status": "ready",
                "score": 8.9,
                "source_provider": "gemini",
                "license_metadata": {"provider": "gemini"},
                "resolution_metadata": {"width": 1600, "height": 900},
            }
        ]

    monkeypatch.setattr(visual_assets, "generate_image_candidates", fake_generate)

    manifest = build_visual_asset_manifest(workspace)

    asset = manifest["assets"][0]
    assert asset["review_status"] == "approved"
    assert asset["selected_asset"]["source_provider"] == "gemini"


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
