import pytest
import asyncio
from unittest.mock import AsyncMock, patch, MagicMock
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))
from tools.image_orchestrator import ImageOrchestrator, ResolvedImage

@pytest.fixture
def orchestrator():
    return ImageOrchestrator(api_keys={})

@pytest.mark.asyncio
async def test_resolve_svg_strategy(orchestrator):
    slot = {
        "description": "增长趋势图",
        "fallback_chain": ["svg"],
        "svg_code": '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 60"><polyline points="0,60 30,40 60,20 100,10" stroke="var(--color-primary)" fill="none" stroke-width="3"/></svg>'
    }
    result = await orchestrator.resolve_image_slot(slot)
    assert isinstance(result, ResolvedImage)
    assert result.strategy == "svg"
    assert "<svg" in result.data

@pytest.mark.asyncio
async def test_fallback_to_icon_when_svg_fails(orchestrator):
    slot = {
        "description": "统计图标",
        "fallback_chain": ["svg", "icon"],
        "icon_name": "trending-up"
    }
    with patch.object(orchestrator, "_try_svg", side_effect=Exception("SVG failed")):
        with patch.object(orchestrator, "_try_icon", new_callable=AsyncMock) as mock_icon:
            mock_icon.return_value = ResolvedImage(strategy="icon", data="<svg>icon</svg>", url="")
            result = await orchestrator.resolve_image_slot(slot)
            assert result.strategy == "icon"

@pytest.mark.asyncio
async def test_resolve_all_images_skips_slides_without_request(orchestrator):
    slides = [
        {"index": 0, "type": "bullet-list", "heading": "x", "content": {}},
        {"index": 1, "type": "stats-callout", "heading": "y", "content": {},
         "image_request": {"description": "test", "fallback_chain": ["icon"], "icon_name": "star"}}
    ]
    with patch.object(orchestrator, "_try_icon", new_callable=AsyncMock) as mock_icon:
        mock_icon.return_value = ResolvedImage(strategy="icon", data="<svg/>", url="")
        result = await orchestrator.resolve_all_images(slides)
        assert result[0].get("resolved_image") is None
        assert result[1].get("resolved_image") is not None

@pytest.mark.asyncio
async def test_cache_hit_skips_api_call(orchestrator, tmp_path):
    orchestrator.cache_dir = str(tmp_path)
    slot = {"description": "cached item", "fallback_chain": ["ai"], "ai_prompt": "test prompt"}
    cached = ResolvedImage(strategy="ai", data="", url="https://cached.example.com/img.png")
    cache_key = orchestrator._make_cache_key(slot)
    orchestrator._write_cache(cache_key, cached)
    result = await orchestrator.resolve_image_slot(slot)
    assert result.url == "https://cached.example.com/img.png"
