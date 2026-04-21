"""Agent 5: 5级图片Fallback编排器"""
from __future__ import annotations
import asyncio
import hashlib
import html
import json
import math
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional


@dataclass
class ResolvedImage:
    strategy: str          # "claude" | "diagram" | "svg" | "canvas" | "icon" | "search" | "ai"
    data: str              # SVG代码 / Canvas HTML / 图片URL
    url: str = ""
    credit: str = ""


class ImageOrchestrator:
    ICON_CDN = "https://cdn.jsdelivr.net/npm/lucide-static@latest/icons/{name}.svg"
    ICON_FALLBACKS = {
        "trending-up": "↗", "trending-down": "↘", "star": "★",
        "check": "✓", "info": "ℹ", "warning": "⚠",
    }

    # Aurora-borealis 语义节点样式 — 颜色取自主题的 primary/secondary/accent 体系
    # 借鉴 architecture-diagram 的类型化色彩思路，但完全使用自己的调色板
    NODE_STYLES = {
        "primary": {"fill": "rgba(99,102,241,0.20)",  "stroke": "#6366f1", "text": "#e0e7ff"},
        "accent":  {"fill": "rgba(167,139,250,0.20)", "stroke": "#a78bfa", "text": "#ede9fe"},
        "cyan":    {"fill": "rgba(56,189,248,0.20)",  "stroke": "#38bdf8", "text": "#e0f2fe"},
        "success": {"fill": "rgba(52,211,153,0.20)",  "stroke": "#34d399", "text": "#d1fae5"},
        "warning": {"fill": "rgba(251,146,60,0.20)",  "stroke": "#fb923c", "text": "#ffedd5"},
        "muted":   {"fill": "rgba(71,85,105,0.35)",   "stroke": "#64748b", "text": "#94a3b8"},
    }
    EDGE_COLOR  = "#334155"
    EDGE_ACCENT = "#6366f1"
    GRID_COLOR  = "#0c1a35"
    BG_COLOR    = "#050818"
    BG_MASK     = "#050818"   # opaque mask behind each node (hides arrows)

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
                # Enrich slot with slide context so _try_claude can generate better prompts
                slot = dict(slide["image_request"])
                slot["_slide_heading"] = slide.get("heading", "")
                slot["_slide_type"] = slide.get("type", "")
                slot["_slide_bullets"] = slide.get("content", {}).get("bullets", [])
                slot["_slide_content"] = slide.get("content", {})
                tasks.append(self.resolve_image_slot(slot))
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
            "claude": self._try_claude,
            "diagram": self._try_diagram,
            "svg": self._try_svg,
            "canvas": self._try_canvas,
            "icon": self._try_icon,
            "pexels": self._try_pexels,
            "pixabay": self._try_pixabay,
            "search": self._try_search,
            "ai": self._try_ai,
        }
        fn = dispatch.get(strategy)
        if not fn:
            return None
        return await fn(slot)

    # ─── Level 0: Claude AI — 智能体SVG生成 ──────────────────────

    async def _try_claude(self, slot: dict) -> Optional[ResolvedImage]:
        """调用 Claude API 智能生成高质量 aurora-borealis 风格 SVG 图表。
        与硬编码的 diagram 策略不同，Claude 能理解语义、自由布局、创造性设计。
        """
        import os
        api_key = self.api_keys.get("anthropic") or os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            return None
        try:
            import anthropic
        except ImportError:
            return None

        description = slot.get("description", "")
        heading     = slot.get("_slide_heading", "")
        slide_type  = slot.get("_slide_type", "")
        bullets     = slot.get("_slide_bullets", [])
        content     = slot.get("_slide_content", {})

        content_ctx = f"Slide type: {slide_type}\nHeading: {heading}\n"
        if bullets:
            content_ctx += "Bullets:\n" + "\n".join(f"- {b}" for b in bullets[:5]) + "\n"
        elif content:
            content_ctx += f"Content: {json.dumps(content, ensure_ascii=False)[:400]}\n"

        system = """You are an expert SVG diagram designer for dark-theme presentations (aurora-borealis).

Design system (use these exact values):
- Background: #050818  Grid color: #0c1a35 (40px pattern)
- Primary: #6366f1  Secondary: #38bdf8  Accent: #a78bfa
- Text: #f1f5f9  Muted: #94a3b8  Border: #1e293b
- Node fills are semi-transparent; node text is light

Node semantic palette:
  primary → fill:rgba(99,102,241,0.20)  stroke:#6366f1  text:#e0e7ff
  accent  → fill:rgba(167,139,250,0.20) stroke:#a78bfa  text:#ede9fe
  cyan    → fill:rgba(56,189,248,0.20)  stroke:#38bdf8  text:#e0f2fe
  success → fill:rgba(52,211,153,0.20)  stroke:#34d399  text:#d1fae5
  warning → fill:rgba(251,146,60,0.20)  stroke:#fb923c  text:#ffedd5
  muted   → fill:rgba(71,85,105,0.35)   stroke:#64748b  text:#94a3b8

CRITICAL engineering rules:
1. Z-ORDER: defs → bg rect → grid rect → edges/arrows → opaque mask rect → node rect → text
2. OPAQUE MASK: draw solid fill="#050818" rect BEFORE each semi-transparent node rect (hides arrow lines underneath)
3. ARROWHEADS: define <marker> in <defs>, attach with marker-end="url(#ah)"
4. GRID: define <pattern id="grid"> in <defs>, cover bg with <rect fill="url(#grid)">
5. EDGE ENDPOINTS: attach arrows at node borders, not centers — use boundary intersection math

Typography: font-family="'JetBrains Mono', monospace"  font-size: 12px labels, 9px sublabels
viewBox must be "0 0 900 450". Output ONLY the <svg> element, nothing else."""

        user = f"""{content_ctx}
Image description: {description}

Generate a professional diagram SVG for this slide. Requirements:
- Include grid background pattern
- Use 3–7 colored nodes with semantic types (primary/accent/cyan/success/warning/muted)
- Draw directional arrows between nodes (z-order: edges before nodes, opaque mask before node rect)
- Add edge labels where meaningful
- Make it visually rich and clearly communicate the slide's concept
- Chinese text is fine for labels

Output ONLY the <svg> element."""

        loop = asyncio.get_event_loop()
        client = anthropic.Anthropic(api_key=api_key)

        def _call():
            msg = client.messages.create(
                model="claude-sonnet-4-6",
                max_tokens=4096,
                system=system,
                messages=[{"role": "user", "content": user}],
            )
            return msg.content[0].text

        try:
            text = await loop.run_in_executor(None, _call)
        except Exception as e:
            print(f"  ⚠ Claude strategy failed: {e}")
            return None

        match = re.search(r'(<svg[\s\S]*?</svg>)', text, re.IGNORECASE)
        if not match:
            return None
        return ResolvedImage(strategy="claude", data=match.group(1), url="")

    # ─── Level 1: Diagram — 节点关系图生成器（无API回退） ────────

    async def _try_diagram(self, slot: dict) -> Optional[ResolvedImage]:
        """从 diagram_nodes + diagram_edges 生成节点图（无需API）。
        作为 claude 策略的离线回退：有 API key 时优先用 claude 策略。
        """
        nodes = slot.get("diagram_nodes", [])
        if not nodes:
            return None
        edges = slot.get("diagram_edges", [])
        svg = self._generate_diagram_svg(
            nodes, edges,
            width=slot.get("diagram_width", 900),
            height=slot.get("diagram_height", 400),
        )
        return ResolvedImage(strategy="diagram", data=svg, url="")

    def _generate_diagram_svg(self, nodes: list, edges: list, width: int, height: int) -> str:
        parts: list[str] = []
        uid = abs(hash(json.dumps(nodes))) % 9999   # unique id suffix for defs

        # ── SVG 开头 + defs（grid pattern、arrowhead marker）
        parts.append(
            f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}">'
        )
        parts.append(f"""<defs>
  <pattern id="pg{uid}" width="40" height="40" patternUnits="userSpaceOnUse">
    <path d="M 40 0 L 0 0 0 40" fill="none" stroke="{self.GRID_COLOR}" stroke-width="0.5"/>
  </pattern>
  <marker id="ah{uid}" markerWidth="8" markerHeight="6" refX="7" refY="3" orient="auto">
    <polygon points="0 0,8 3,0 6" fill="{self.EDGE_COLOR}"/>
  </marker>
  <marker id="ahe{uid}" markerWidth="8" markerHeight="6" refX="7" refY="3" orient="auto">
    <polygon points="0 0,8 3,0 6" fill="{self.EDGE_ACCENT}"/>
  </marker>
</defs>""")

        # ── 背景：纯色 + grid 叠加（z-order: 最底层）
        parts.append(f'<rect width="{width}" height="{height}" fill="{self.BG_COLOR}"/>')
        parts.append(f'<rect width="{width}" height="{height}" fill="url(#pg{uid})"/>')

        # ── 构建节点查找表（用于计算边的端点）
        node_map = {n["id"]: n for n in nodes}

        # ── 边（先于节点绘制 → 藏在节点下方，体现 z-order 纪律）
        for edge in edges:
            src = node_map.get(edge.get("from", ""))
            dst = node_map.get(edge.get("to", ""))
            if not src or not dst:
                continue

            sx, sy = self._node_center(src)
            dx_c, dy_c = self._node_center(dst)

            # 计算边在节点边界上的精确进出点
            ex1, ey1 = self._boundary_point(src,  dx_c, dy_c)
            ex2, ey2 = self._boundary_point(dst,  sx,   sy)

            is_accent = edge.get("accent", False)
            is_dashed = edge.get("dashed", False)
            color  = self.EDGE_ACCENT if is_accent else self.EDGE_COLOR
            marker = f"ahe{uid}" if is_accent else f"ah{uid}"
            dash   = ' stroke-dasharray="6,3"' if is_dashed else ""
            parts.append(
                f'<line x1="{ex1:.1f}" y1="{ey1:.1f}" x2="{ex2:.1f}" y2="{ey2:.1f}" '
                f'stroke="{color}" stroke-width="1.5"{dash} marker-end="url(#{marker})"/>'
            )

            # 边标签（居中偏上）
            label = edge.get("label", "")
            if label:
                mx, my = (ex1 + ex2) / 2, (ey1 + ey2) / 2 - 7
                parts.append(
                    f'<text x="{mx:.1f}" y="{my:.1f}" fill="#475569" '
                    f'font-size="10" text-anchor="middle" font-family="monospace">'
                    f'{html.escape(label)}</text>'
                )

        # ── 节点（后于边绘制 → 覆盖在边上方）
        for node in nodes:
            x, y   = node["x"], node["y"]
            w, h   = node.get("w", 140), node.get("h", 52)
            ntype  = node.get("type", "primary")
            style  = self.NODE_STYLES.get(ntype, self.NODE_STYLES["primary"])
            cx, cy = x + w / 2, y + h / 2

            # Opaque mask（完全遮住穿过节点的边线，architecture-diagram 核心技法）
            parts.append(
                f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="6" fill="{self.BG_MASK}"/>'
            )
            # 语义色节点框
            parts.append(
                f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="6" '
                f'fill="{style["fill"]}" stroke="{style["stroke"]}" stroke-width="1.5"/>'
            )

            # 主标签
            label    = html.escape(node.get("label", ""))
            sublabel = html.escape(node.get("sublabel", ""))
            if sublabel:
                parts.append(
                    f'<text x="{cx:.1f}" y="{cy - 7:.1f}" fill="{style["text"]}" '
                    f'font-size="11" font-weight="600" text-anchor="middle" font-family="monospace">'
                    f'{label}</text>'
                )
                parts.append(
                    f'<text x="{cx:.1f}" y="{cy + 9:.1f}" fill="#64748b" '
                    f'font-size="9" text-anchor="middle" font-family="monospace">'
                    f'{sublabel}</text>'
                )
            else:
                parts.append(
                    f'<text x="{cx:.1f}" y="{cy + 4:.1f}" fill="{style["text"]}" '
                    f'font-size="11" font-weight="600" text-anchor="middle" font-family="monospace">'
                    f'{label}</text>'
                )

        parts.append("</svg>")
        return "\n".join(parts)

    def _node_center(self, node: dict) -> tuple[float, float]:
        return node["x"] + node.get("w", 140) / 2, node["y"] + node.get("h", 52) / 2

    def _boundary_point(self, node: dict, tx: float, ty: float) -> tuple[float, float]:
        """计算从节点中心指向 (tx,ty) 方向的边界交叉点（箭头端点）。"""
        nx, ny = node["x"], node["y"]
        nw, nh = node.get("w", 140), node.get("h", 52)
        cx, cy = nx + nw / 2, ny + nh / 2
        dx, dy = tx - cx, ty - cy
        if abs(dx) < 0.001 and abs(dy) < 0.001:
            return cx, cy

        candidates: list[float] = []
        if abs(dx) > 0.001:
            for bx in [nx + 2, nx + nw - 2]:
                t = (bx - cx) / dx
                if t > 0.001:
                    iy = cy + t * dy
                    if ny + 2 <= iy <= ny + nh - 2:
                        candidates.append(t)
        if abs(dy) > 0.001:
            for by in [ny + 2, ny + nh - 2]:
                t = (by - cy) / dy
                if t > 0.001:
                    ix = cx + t * dx
                    if nx + 2 <= ix <= nx + nw - 2:
                        candidates.append(t)

        if not candidates:
            return cx, cy
        t = min(candidates)
        return cx + t * dx, cy + t * dy

    # ─── Level 2: SVG 内联 ───────────────────────────────────────

    async def _try_svg(self, slot: dict) -> Optional[ResolvedImage]:
        """简单图表 SVG（趋势线、柱状等）。
        默认注入主题 CSS 变量；当 preserve_colors=true 时跳过注入（供多色图使用）。
        """
        svg_code = slot.get("svg_code", "")
        if not svg_code or "<svg" not in svg_code:
            return None
        if not slot.get("preserve_colors"):
            svg_code = re.sub(r'stroke="#[0-9a-fA-F]{3,6}"', 'stroke="var(--color-primary)"', svg_code)
            svg_code = re.sub(r'fill="#[0-9a-fA-F]{3,6}"(?! none)', 'fill="var(--color-secondary)"', svg_code)
        return ResolvedImage(strategy="svg", data=svg_code, url="")

    # ─── Level 2: Chart.js Canvas ────────────────────────────────

    async def _try_canvas(self, slot: dict) -> Optional[ResolvedImage]:
        """Chart.js Canvas HTML"""
        chart_data = slot.get("chart_data")
        if not chart_data:
            return None
        chart_type = chart_data.get("type", "bar")
        labels   = json.dumps(chart_data.get("labels",   []), ensure_ascii=False)
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

    # ─── Level 3: Lucide 图标 ────────────────────────────────────

    async def _try_icon(self, slot: dict) -> Optional[ResolvedImage]:
        """Lucide 图标CDN"""
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
        svg = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="48" height="48">'
               f'<text y="20" font-size="20">{fallback}</text></svg>')
        return ResolvedImage(strategy="icon", data=svg, url="")

    # ─── Level 4a: Pexels 搜索（免署名，200次/小时） ──────────────

    async def _try_pexels(self, slot: dict) -> Optional[ResolvedImage]:
        """Pexels API 搜索 — 免署名，有 landscape 预裁切(1200×627)"""
        import httpx
        api_key = self.api_keys.get("pexels")
        if not api_key:
            return None
        query = slot.get("search_query") or slot.get("description", "")
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(
                "https://api.pexels.com/v1/search",
                params={"query": query, "per_page": 1, "orientation": "landscape"},
                headers={"Authorization": api_key},
            )
            if resp.status_code == 200:
                photos = resp.json().get("photos", [])
                if photos:
                    img = photos[0]
                    return ResolvedImage(
                        strategy="pexels",
                        data=img["src"]["landscape"],  # 1200×627, 完美适配幻灯片
                        url=img["src"]["landscape"],
                        credit=f'Photo by {img["photographer"]} on Pexels',
                    )
        return None

    # ─── Level 4b: Pixabay 搜索（免署名，100次/60秒） ────────────

    async def _try_pixabay(self, slot: dict) -> Optional[ResolvedImage]:
        """Pixabay API 搜索 — 免署名，需下载缓存（禁止热链接）"""
        import httpx
        api_key = self.api_keys.get("pixabay")
        if not api_key:
            return None
        query = slot.get("search_query") or slot.get("description", "")
        async with httpx.AsyncClient(timeout=10.0) as client:
            # 1. 搜索
            resp = await client.get(
                "https://pixabay.com/api/",
                params={
                    "key": api_key,
                    "q": query,
                    "per_page": 3,
                    "orientation": "horizontal",
                    "min_width": 1280,
                    "image_type": "photo",
                    "safesearch": "true",
                },
            )
            if resp.status_code != 200:
                return None
            hits = resp.json().get("hits", [])
            if not hits:
                return None

            # 2. 下载到缓存（Pixabay 禁止热链接，必须自行托管）
            img_url = hits[0].get("largeImageURL") or hits[0].get("webformatURL")
            if not img_url:
                return None
            img_resp = await client.get(img_url, timeout=15.0)
            if img_resp.status_code != 200:
                return None
            cache_path = Path(self.cache_dir) / f"pixabay_{hits[0]['id']}.jpg"
            cache_path.write_bytes(img_resp.content)
            return ResolvedImage(
                strategy="pixabay",
                data=str(cache_path),
                url=img_url,
                credit=f'Photo by {hits[0].get("user", "")} on Pixabay',
            )

    # ─── Level 4c: Unsplash 搜索（需署名，50次/小时 Demo） ───────

    async def _try_search(self, slot: dict) -> Optional[ResolvedImage]:
        """Unsplash 免费图片搜索"""
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

    # ─── Level 5: DALL-E AI 生图 ─────────────────────────────────

    async def _try_ai(self, slot: dict) -> Optional[ResolvedImage]:
        """DALL-E 3 AI生图"""
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
            model="dall-e-3", prompt=prompt,
            size="1792x1024", quality="standard", n=1,
        )
        url = response.data[0].url
        return ResolvedImage(strategy="ai", data=url, url=url)

    # ─── 缓存工具 ──────────────────────────────────────────────────

    def _make_cache_key(self, slot: dict) -> str:
        chain_str = ":".join(slot.get("fallback_chain", []))
        # diagram 用 nodes 内容作为缓存键
        content = (slot.get("ai_prompt")
                   or slot.get("search_query")
                   or json.dumps(slot.get("diagram_nodes", ""), ensure_ascii=False)
                   or slot.get("description", ""))
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
    slides_path    = sys.argv[1]
    output_path    = sys.argv[2]
    api_keys_path  = sys.argv[3] if len(sys.argv) > 3 else None

    api_keys = {}
    if api_keys_path:
        api_keys = json.loads(Path(api_keys_path).read_text())

    slides = json.loads(Path(slides_path).read_text(encoding="utf-8"))
    orch   = ImageOrchestrator(api_keys=api_keys)
    result = asyncio.run(orch.resolve_all_images(slides))
    Path(output_path).write_text(json.dumps(result, ensure_ascii=False, indent=2))
    print(f"✓ 图片编排完成 → {output_path}")
