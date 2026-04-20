import pytest
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))
from tools.html_renderer import HTMLRenderer

THEMES_DIR = Path(__file__).parent.parent / "themes"
TEMPLATES_DIR = Path(__file__).parent.parent / "templates"

@pytest.fixture
def renderer():
    return HTMLRenderer(
        themes_dir=str(THEMES_DIR),
        templates_dir=str(TEMPLATES_DIR),
    )

MINIMAL_SLIDES_DATA = {
    "theme": "aurora-borealis",
    "style_constraints": {
        "heading_emphasis": "gradient",
        "card_style": "glass",
        "stat_style": "gradient-text",
        "bullet_style": "dot",
        "image_style_fingerprint": ["cinematic"]
    },
    "slides": [
        {
            "index": 0,
            "type": "title",
            "heading": "AI的未来",
            "subheading": "探索人工智能的边界",
            "content": {}
        }
    ]
}

def test_renderer_produces_html(renderer):
    html = renderer.render(MINIMAL_SLIDES_DATA)
    assert "<!DOCTYPE html>" in html
    assert "AI的未来" in html

def test_renderer_injects_theme_css(renderer):
    html = renderer.render(MINIMAL_SLIDES_DATA)
    assert "aurora-borealis" in html

def test_renderer_title_slide(renderer):
    html = renderer.render(MINIMAL_SLIDES_DATA)
    assert "AI的未来" in html
    assert "探索人工智能的边界" in html

def test_renderer_unknown_slide_type_raises(renderer):
    data = {**MINIMAL_SLIDES_DATA, "slides": [{
        "index": 0, "type": "unknown-type", "heading": "x", "content": {}
    }]}
    with pytest.raises(ValueError, match="未知幻灯片类型"):
        renderer.render(data)

def test_renderer_slide_count(renderer):
    data = {**MINIMAL_SLIDES_DATA, "slides": [
        {"index": i, "type": "section-divider", "heading": f"Section {i}", "content": {}}
        for i in range(3)
    ]}
    html = renderer.render(data)
    assert html.count('class="slide') == 3
