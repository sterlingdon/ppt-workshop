import pytest
import json
from pathlib import Path
from pptx import Presentation
from pptx.util import Inches
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))
from tools.pptx_exporter import HybridPPTXBuilder

SAMPLE_SLIDES = [
    {
        "index": 0, "type": "title",
        "heading": "AI的未来", "subheading": "探索边界",
        "content": {}
    },
    {
        "index": 1, "type": "bullet-list",
        "heading": "核心要点",
        "content": {"bullets": ["要点一", "要点二", "要点三"]}
    },
    {
        "index": 2, "type": "stats-callout",
        "heading": "关键数据",
        "content": {"stats": [{"value": "85%", "label": "增长率"}, {"value": "3倍", "label": "效率提升"}]}
    }
]

SAMPLE_THEME = {
    "name": "aurora-borealis",
    "primary_color": "6366f1",
    "text_color": "f1f5f9",
    "bg_color": "050818",
}

@pytest.fixture
def builder():
    return HybridPPTXBuilder(theme_config=SAMPLE_THEME)

def test_builder_creates_correct_slide_count(builder, tmp_path):
    output = str(tmp_path / "test.pptx")
    builder.build(SAMPLE_SLIDES, bg_images=[], output_path=output)
    prs = Presentation(output)
    assert len(prs.slides) == 3

def test_builder_slides_are_widescreen(builder, tmp_path):
    output = str(tmp_path / "test.pptx")
    builder.build(SAMPLE_SLIDES, bg_images=[], output_path=output)
    prs = Presentation(output)
    assert abs(prs.slide_width - Inches(16)) < Inches(0.01)
    assert abs(prs.slide_height - Inches(9)) < Inches(0.01)

def test_builder_title_slide_has_text(builder, tmp_path):
    output = str(tmp_path / "test.pptx")
    builder.build([SAMPLE_SLIDES[0]], bg_images=[], output_path=output)
    prs = Presentation(output)
    slide = prs.slides[0]
    all_text = " ".join(shape.text for shape in slide.shapes if shape.has_text_frame)
    assert "AI的未来" in all_text

def test_builder_stats_slide_has_values(builder, tmp_path):
    output = str(tmp_path / "test.pptx")
    builder.build([SAMPLE_SLIDES[2]], bg_images=[], output_path=output)
    prs = Presentation(output)
    slide = prs.slides[0]
    all_text = " ".join(shape.text for shape in slide.shapes if shape.has_text_frame)
    assert "85%" in all_text
    assert "增长率" in all_text

def test_builder_accepts_bg_images(builder, tmp_path):
    from PIL import Image
    bg_img = tmp_path / "bg_0.png"
    img = Image.new("RGB", (1920, 1080), color=(10, 8, 24))
    img.save(str(bg_img))
    output = str(tmp_path / "with_bg.pptx")
    builder.build([SAMPLE_SLIDES[0]], bg_images=[str(bg_img)], output_path=output)
    prs = Presentation(output)
    slide = prs.slides[0]
    assert len(slide.shapes) > 0
