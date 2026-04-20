"""端到端集成测试：从文章到HTML演示"""
import pytest
import json
import asyncio
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from tools.ingest import extract_from_text
from tools.html_renderer import HTMLRenderer
from tools.image_orchestrator import ImageOrchestrator

FIXTURE_ARTICLE = Path(__file__).parent / "fixtures" / "test_article.md"
THEMES_DIR = Path(__file__).parent.parent / "themes"
TEMPLATES_DIR = Path(__file__).parent.parent / "templates"

MOCK_SLIDES_DATA = {
    "theme": "aurora-borealis",
    "title": "2024年大型语言模型发展综述",
    "language": "zh",
    "style_constraints": {
        "heading_emphasis": "gradient",
        "card_style": "glass",
        "stat_style": "gradient-text",
        "bullet_style": "dot",
        "image_style_fingerprint": ["cinematic lighting", "deep purple"]
    },
    "slides": [
        {"index": 0, "type": "title", "heading": "2024年大模型发展综述", "subheading": "AI时代的里程碑", "content": {}},
        {"index": 1, "type": "stats-callout", "heading": "关键数据",
         "content": {"stats": [
             {"value": "1000亿", "label": "全球AI投资"},
             {"value": "85%", "label": "同比增长"},
             {"value": "3倍", "label": "推理速度提升"},
             {"value": "70%", "label": "API成本下降"}
         ]},
         "image_request": {"description": "增长趋势图", "fallback_chain": ["svg"],
                           "svg_code": '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 400 240"><polyline points="20,200 100,160 200,100 300,60 380,20" stroke="var(--color-primary)" fill="none" stroke-width="3"/></svg>'}},
        {"index": 2, "type": "bullet-list", "heading": "主要进展",
         "content": {"bullets": ["GPT-4、Claude 3代表技术前沿", "模型参数增至万亿规模", "企业采用率提升至52%"]}},
        {"index": 3, "type": "quote-callout", "heading": "行业声音",
         "content": {"quote": {"text": "这是自互联网以来最重要的技术变革", "author": "Sam Altman", "role": "OpenAI CEO"}}},
        {"index": 4, "type": "conclusion", "heading": "2025年展望", "subheading": "AI应用落地的关键年", "content": {}}
    ]
}

def test_ingest_reads_fixture():
    text = FIXTURE_ARTICLE.read_text(encoding="utf-8")
    result = extract_from_text(text)
    assert result.word_count > 0
    assert "大型语言模型" in result.text

def test_html_renderer_full_pipeline():
    renderer = HTMLRenderer(
        themes_dir=str(THEMES_DIR),
        templates_dir=str(TEMPLATES_DIR),
    )
    html = renderer.render(MOCK_SLIDES_DATA)
    assert "<!DOCTYPE html>" in html
    assert "2024年大模型发展综述" in html
    assert "aurora-borealis" in html
    assert html.count('class="slide') == 5

@pytest.mark.asyncio
async def test_image_orchestrator_resolves_svg():
    orch = ImageOrchestrator(api_keys={})
    result = await orch.resolve_all_images(MOCK_SLIDES_DATA["slides"])
    stats_slide = result[1]
    assert stats_slide.get("resolved_image") is not None
    assert "<svg" in stats_slide["resolved_image"]

def test_html_output_to_file(tmp_path):
    renderer = HTMLRenderer(
        themes_dir=str(THEMES_DIR),
        templates_dir=str(TEMPLATES_DIR),
    )
    html = renderer.render(MOCK_SLIDES_DATA)
    out = tmp_path / "presentation.html"
    out.write_text(html, encoding="utf-8")
    assert out.stat().st_size > 5000
    print(f"\n✓ HTML 输出: {out}")
