import json
import pytest
from pathlib import Path
import jsonschema

SCHEMAS_DIR = Path(__file__).parent.parent / "schemas"

def load_schema(name):
    return json.loads((SCHEMAS_DIR / f"{name}.schema.json").read_text())

def test_analysis_schema_valid_minimal():
    schema = load_schema("analysis")
    data = {
        "domain": "technology",
        "title": "AI的崛起",
        "key_points": ["LLM改变了世界"],
        "visual_direction": "luminous AI research briefing"
    }
    jsonschema.validate(data, schema)

def test_analysis_schema_invalid_domain():
    schema = load_schema("analysis")
    data = {"domain": "invalid", "title": "x", "key_points": ["y"], "visual_direction": "compact evidence brief"}
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(data, schema)

def test_outline_schema_slide_count_min():
    schema = load_schema("outline")
    data = {
        "theme": "luminous AI research briefing",
        "style_constraints": {
            "heading_emphasis": "gradient",
            "card_style": "glass",
            "stat_style": "gradient-text",
            "bullet_style": "dot",
            "image_style_fingerprint": ["cinematic", "deep purple"]
        },
        "slides": [{"index": i, "type": "bullet-list", "title": f"Slide {i}"} for i in range(3)]
    }
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(data, schema)

def test_slides_schema_image_request():
    schema = load_schema("slides")
    data = [{
        "index": 0, "type": "stats-callout", "heading": "数据",
        "content": {"stats": [{"value": "85%", "label": "增长"}]},
        "image_request": {
            "description": "增长趋势图",
            "fallback_chain": ["svg", "icon"]
        }
    }]
    jsonschema.validate(data, schema)

def test_visual_review_schema_requires_review_capability():
    schema = load_schema("visual_review")
    data = {
        "project_id": "deck",
        "review_type": "ai_lens_visual_review",
        "gate_type": "ai_visual_quality_review",
        "status": "pass",
        "blocking_findings": 0,
        "slides": [{"slide": 1, "passed": True, "visual_score": 8, "findings": [], "repairs": []}]
    }
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(data, schema)

def test_visual_review_schema_accepts_vision_review_evidence():
    schema = load_schema("visual_review")
    data = {
        "project_id": "deck",
        "review_type": "ai_lens_visual_review",
        "gate_type": "ai_visual_quality_review",
        "status": "pass",
        "review_assets": {
            "full_deck_screenshot": "review/full_deck.png",
            "slide_screenshots_dir": "review/slides"
        },
        "review_capability": {
            "method": "vision_model",
            "image_input": True,
            "model": "vision-capable-model",
            "inspected_assets": ["review/full_deck.png", "review/slides/slide_01.png"]
        },
        "blocking_findings": 0,
        "repair_log": [],
        "slides": [{"slide": 1, "passed": True, "visual_score": 8, "findings": [], "repairs": []}]
    }
    jsonschema.validate(data, schema)


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
                    "wow_goal": "diagram invention",
                },
            }
        ]
    }
    jsonschema.validate(data, schema)


def test_visual_asset_plan_schema_requires_primary_route():
    schema = load_schema("visual_asset_plan")
    data = {"slides": [{"slide": 1, "asset_slots": [{"slot": "hero"}]}]}
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(data, schema)
