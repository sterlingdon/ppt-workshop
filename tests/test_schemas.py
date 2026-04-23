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
