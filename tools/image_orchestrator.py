"""Agent 5: 5级图片Fallback编排器"""
from __future__ import annotations
import asyncio
import hashlib
import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional


@dataclass
class ResolvedImage:
    strategy: str          # "svg" | "canvas" | "icon" | "search" | "ai"
    data: str              # SVG代码 / Canvas HTML / 图片URL
    url: str = ""
    credit: str = ""


class ImageOrchestrator:
    ICON_CDN = "https://cdn.jsdelivr.net/npm/lucide-static@latest/icons/{name}.svg"
    ICON_FALLBACKS = {
        "trending-up": "↗", "trending-down": "↘", "star": "★",
        "check": "✓", "info": "ℹ", "warning": "⚠",
    }

    def __init__(self, api_keys: dict, cache_dir: str = "image_cache"):
        self.api_keys = api_keys
        self.cache_dir = cache_dir
        Path(cache_dir).mkdir(exist_ok=True)

    async def resolve_all_images(self, slides: list[dict]) -> list[dict]:
        """解析所有幻灯片的图片需求，并行处理"""
        tasks = []
        indices = []
        for i, slide in enumerate(slides):
            if slide.get("image_request"):
                tasks.append(self.resolve_image_slot(slide["image_request"]))
                indices.append(i)

        if not tasks:
            return slides

        results = await asyncio.gather(*tasks, return_exceptions=True)
        output = [dict(s) for s in slides]
        for idx, result in zip(indices, results):
            if isinstance(result, ResolvedImage):
                output[idx]["resolved_image"] = result.data or result.url
                output[idx]["image_credit"] = result.credit
        return output

    async def resolve_image_slot(self, slot: dict) -> ResolvedImage:
        """按 fallback_chain 逐级尝试，命中缓存直接返回"""
        chain = slot.get("fallback_chain", [])
        cache_key = self._make_cache_key(slot)
        cached = self._read_cache(cache_key)
        if cached:
            return cached

        for strategy in chain:
            try:
                result = await self._try_strategy(strategy, slot)
                if result:
                    self._write_cache(cache_key, result)
                    return result
            except Exception:
                continue

        return ResolvedImage(strategy="none", data="", url="")

    async def _try_strategy(self, strategy: str, slot: dict) -> Optional[ResolvedImage]:
        dispatch = {
            "svg": self._try_svg,
            "canvas": self._try_canvas,
            "icon": self._try_icon,
            "search": self._try_search,
            "ai": self._try_ai,
        }
        fn = dispatch.get(strategy)
        if not fn:
            return None
        return await fn(slot)

    async def _try_svg(self, slot: dict) -> Optional[ResolvedImage]:
        """Level 1: SVG内联（Claude在Agent 4中生成，此处注入主题色）"""
        svg_code = slot.get("svg_code", "")
        if not svg_code or "<svg" not in svg_code:
            return None
        svg_code = re.sub(r'stroke="#[0-9a-fA-F]{3,6}"', 'stroke="var(--color-primary)"', svg_code)
        svg_code = re.sub(r'fill="#[0-9a-fA-F]{3,6}"(?! none)', 'fill="var(--color-secondary)"', svg_code)
        return ResolvedImage(strategy="svg", data=svg_code, url="")

    async def _try_canvas(self, slot: dict) -> Optional[ResolvedImage]:
        """Level 2: Chart.js Canvas HTML"""
        chart_data = slot.get("chart_data")
        if not chart_data:
            return None
        chart_type = chart_data.get("type", "bar")
        labels = json.dumps(chart_data.get("labels", []), ensure_ascii=False)
        datasets = json.dumps(chart_data.get("datasets", []), ensure_ascii=False)
        canvas_html = f"""
<div style="max-height:400px; position:relative;">
  <canvas id="chart-{hash(str(chart_data)) % 10000}" style="max-height:380px;"></canvas>
</div>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4/dist/chart.umd.min.js"></script>
<script>
(function(){{
  const ctx = document.querySelector('canvas[id^="chart-"]');
  new Chart(ctx, {{
    type: '{chart_type}',
    data: {{ labels: {labels}, datasets: {datasets} }},
    options: {{
      responsive: true,
      plugins: {{ legend: {{ labels: {{ color: 'var(--color-text)' }} }} }},
      scales: {{
        x: {{ ticks: {{ color: 'var(--color-text-muted)' }}, grid: {{ color: 'var(--color-border)' }} }},
        y: {{ ticks: {{ color: 'var(--color-text-muted)' }}, grid: {{ color: 'var(--color-border)' }} }}
      }}
    }}
  }});
}})();
</script>"""
        return ResolvedImage(strategy="canvas", data=canvas_html, url="")

    async def _try_icon(self, slot: dict) -> Optional[ResolvedImage]:
        """Level 3: Lucide 图标CDN"""
        import httpx
        icon_name = slot.get("icon_name", "")
        if not icon_name:
            return None
        url = self.ICON_CDN.format(name=icon_name)
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                resp = await client.get(url)
                if resp.status_code == 200:
                    svg = resp.text.replace('stroke="currentColor"', 'stroke="var(--color-primary)"')
                    return ResolvedImage(strategy="icon", data=svg, url=url)
        except Exception:
            pass
        fallback = self.ICON_FALLBACKS.get(icon_name, "◆")
        svg = f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="48" height="48"><text y="20" font-size="20">{fallback}</text></svg>'
        return ResolvedImage(strategy="icon", data=svg, url="")

    async def _try_search(self, slot: dict) -> Optional[ResolvedImage]:
        """Level 4: Unsplash 免费图片搜索"""
        import httpx
        api_key = self.api_keys.get("unsplash")
        if not api_key:
            return None
        query = slot.get("search_query") or slot.get("description", "")
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(
                "https://api.unsplash.com/search/photos",
                params={"query": query, "per_page": 1, "orientation": "landscape"},
                headers={"Authorization": f"Client-ID {api_key}"},
            )
            if resp.status_code == 200:
                hits = resp.json().get("results", [])
                if hits:
                    img = hits[0]
                    return ResolvedImage(
                        strategy="search",
                        data=img["urls"]["regular"],
                        url=img["urls"]["regular"],
                        credit=f'Photo by {img["user"]["name"]} on Unsplash',
                    )
        return None

    async def _try_ai(self, slot: dict) -> Optional[ResolvedImage]:
        """Level 5: DALL-E 3 AI生图"""
        api_key = self.api_keys.get("openai")
        if not api_key:
            return None
        from openai import AsyncOpenAI
        client = AsyncOpenAI(api_key=api_key)
        prompt = slot.get("ai_prompt") or slot.get("description", "")
        fingerprint = slot.get("image_style_fingerprint", [])
        if fingerprint:
            prompt = f"{prompt}. Style: {', '.join(fingerprint)}. Wide aspect ratio, presentation background."
        response = await client.images.generate(
            model="dall-e-3",
            prompt=prompt,
            size="1792x1024",
            quality="standard",
            n=1,
        )
        url = response.data[0].url
        return ResolvedImage(strategy="ai", data=url, url=url)

    # ─── 缓存工具 ──────────────────────────────────────────────

    def _make_cache_key(self, slot: dict) -> str:
        chain_str = ":".join(slot.get("fallback_chain", []))
        content = slot.get("ai_prompt") or slot.get("search_query") or slot.get("description", "")
        return hashlib.md5(f"{chain_str}:{content}".encode()).hexdigest()

    def _read_cache(self, key: str) -> Optional[ResolvedImage]:
        path = Path(self.cache_dir) / f"{key}.json"
        if path.exists():
            data = json.loads(path.read_text())
            return ResolvedImage(**data)
        return None

    def _write_cache(self, key: str, result: ResolvedImage):
        path = Path(self.cache_dir) / f"{key}.json"
        path.write_text(json.dumps({
            "strategy": result.strategy,
            "data": result.data,
            "url": result.url,
            "credit": result.credit,
        }))


if __name__ == "__main__":
    import sys
    slides_path = sys.argv[1]
    output_path = sys.argv[2]
    api_keys_path = sys.argv[3] if len(sys.argv) > 3 else None

    api_keys = {}
    if api_keys_path:
        api_keys = json.loads(Path(api_keys_path).read_text())

    slides = json.loads(Path(slides_path).read_text(encoding="utf-8"))
    orch = ImageOrchestrator(api_keys=api_keys)
    result = asyncio.run(orch.resolve_all_images(slides))
    Path(output_path).write_text(json.dumps(result, ensure_ascii=False, indent=2))
    print(f"✓ 图片编排完成 → {output_path}")
