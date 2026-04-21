"""Agent 7: Hybrid PPTX 导出 — 背景截图层 + 原生内容层"""
from __future__ import annotations
import asyncio
import json
import re
from pathlib import Path
from typing import Optional

from pptx import Presentation
from pptx.util import Inches, Pt, Emu
from pptx.enum.text import PP_ALIGN
from pptx.dml.color import RGBColor
from pptx.enum.chart import XL_CHART_TYPE


class ContentImageRenderer:
    """将 resolved_image (SVG/Canvas/URL) 渲染成 PNG 文件，供 PPTX 嵌入使用"""

    def __init__(self, themes_dir: str = "themes"):
        self.themes_dir = Path(themes_dir)

    async def render_all(self, slides: list[dict], theme_name: str, output_dir: str) -> list[dict]:
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        theme_css = self._load_theme_css(theme_name)

        from playwright.async_api import async_playwright
        async with async_playwright() as p:
            browser = await p.chromium.launch()
            page = await browser.new_page()
            for i, slide in enumerate(slides):
                resolved = slide.get("resolved_image", "")
                if not resolved:
                    continue
                out_path = output_dir / f"content_slide_{i}.png"
                img_type = self._detect_image_type(resolved)
                try:
                    ok = False
                    if img_type == "svg":
                        ok = await self._render_svg_to_png(page, resolved, theme_css, out_path)
                    elif img_type == "canvas":
                        ok = await self._render_canvas_to_png(page, resolved, theme_css, out_path)
                    elif img_type == "url":
                        ok = await self._download_url(resolved, out_path)
                    if ok and out_path.exists():
                        slide["resolved_image_path"] = str(out_path)
                        print(f"  ✓ slide {i} ({slide.get('type')}) → {out_path.name}")
                except Exception as e:
                    print(f"  ⚠ slide {i} image failed: {e}")
            await browser.close()
        return slides

    def _detect_image_type(self, data: str) -> str:
        if "<canvas" in data and "<script" in data:
            return "canvas"
        if "<svg" in data:
            return "svg"
        if data.strip().startswith("https://"):
            return "url"
        return "unknown"

    def _load_theme_css(self, theme_name: str) -> str:
        for name in [theme_name, "_base"]:
            p = self.themes_dir / f"{name}.css"
            if p.exists():
                css = p.read_text(encoding="utf-8")
                return re.sub(r"@import\s+url\([^)]+\);?\s*\n?", "", css)
        return (":root{--color-bg:#050818;--color-primary:#6366f1;"
                "--color-secondary:#38bdf8;--color-text:#f1f5f9;--color-text-muted:#94a3b8;}")

    async def _render_svg_to_png(self, page, svg_data: str, theme_css: str, out_path: Path) -> bool:
        svg = re.sub(r'(<svg[^>]*)\s+width="\d+"', r'\1', svg_data)
        svg = re.sub(r'(<svg[^>]*)\s+height="\d+"', r'\1', svg)
        html = f"""<!DOCTYPE html><html><head><style>
{theme_css}
*{{margin:0;padding:0;box-sizing:border-box}}
body{{width:800px;height:480px;overflow:hidden;background:var(--color-bg,#050818);
  display:flex;align-items:center;justify-content:center;padding:2rem}}
svg{{width:100%;height:auto;max-height:100%;display:block}}
</style></head><body>{svg}</body></html>"""
        await page.set_viewport_size({"width": 800, "height": 480})
        await page.set_content(html, wait_until="domcontentloaded")
        await page.screenshot(path=str(out_path))
        return True

    async def _render_canvas_to_png(self, page, canvas_html: str, theme_css: str, out_path: Path) -> bool:
        # Patch Chart.js options: disable responsive + animation so chart fills the viewport
        patched = canvas_html.replace(
            "responsive: true",
            "responsive: false, animation: { duration: 0 }"
        )
        html = f"""<!DOCTYPE html><html><head><style>
{theme_css}
*{{margin:0;padding:0;box-sizing:border-box}}
body{{width:800px;height:450px;overflow:hidden;background:var(--color-bg,#050818);
  display:flex;align-items:center;justify-content:center;padding:1rem}}
canvas{{width:760px!important;height:420px!important}}
</style></head><body>{patched}</body></html>"""
        await page.set_viewport_size({"width": 800, "height": 450})
        await page.set_content(html, wait_until="networkidle")
        await page.wait_for_timeout(800)
        await page.screenshot(path=str(out_path))
        return True

    async def _download_url(self, url: str, out_path: Path) -> bool:
        import httpx
        async with httpx.AsyncClient(timeout=15.0, follow_redirects=True) as client:
            resp = await client.get(url)
            resp.raise_for_status()
        out_path.write_bytes(resp.content)
        return True


class HybridPPTXBuilder:
    W = Inches(16)
    H = Inches(9)

    def __init__(self, theme_config: dict):
        self.theme = theme_config
        self.primary = RGBColor.from_string(theme_config.get("primary_color", "6366f1"))
        self.text_color = RGBColor.from_string(theme_config.get("text_color", "f1f5f9"))
        self.bg_color = RGBColor.from_string(theme_config.get("bg_color", "0f172a"))
        self.muted_color = RGBColor.from_string(theme_config.get("muted_color", "94a3b8"))
        self.display_font = theme_config.get("display_font", "Calibri")
        self.body_font = theme_config.get("body_font", "Calibri")

    def build(self, slides: list[dict], bg_images: list[str], output_path: str) -> str:
        prs = Presentation()
        prs.slide_width = self.W
        prs.slide_height = self.H

        blank_layout = prs.slide_layouts[6]

        for i, slide_data in enumerate(slides):
            slide = prs.slides.add_slide(blank_layout)

            bg_path = bg_images[i] if i < len(bg_images) else None
            if bg_path and Path(bg_path).exists():
                self._set_background(slide, bg_path)
            else:
                self._set_solid_bg(slide)

            self._render_slide_content(slide, slide_data)

        prs.save(output_path)
        return output_path

    def _set_background(self, slide, image_path: str):
        pic = slide.shapes.add_picture(image_path, 0, 0, self.W, self.H)
        slide.shapes._spTree.remove(pic._element)
        slide.shapes._spTree.insert(2, pic._element)

    def _set_solid_bg(self, slide):
        bg = slide.background
        fill = bg.fill
        fill.solid()
        fill.fore_color.rgb = self.bg_color

    def _add_picture_fit(self, slide, img_path: str, left, top, max_w, max_h):
        """Add picture scaled proportionally to fit within max_w × max_h, centered in that box."""
        from PIL import Image as PILImage
        with PILImage.open(img_path) as im:
            iw, ih = im.size
        scale = min(max_w / iw, max_h / ih)
        w = int(iw * scale)
        h = int(ih * scale)
        cx = left + (max_w - w) // 2
        cy = top + (max_h - h) // 2
        slide.shapes.add_picture(img_path, cx, cy, w, h)

    def _render_slide_content(self, slide, data: dict):
        dispatch = {
            "title": self._render_title,
            "conclusion": self._render_title,
            "section-divider": self._render_section_divider,
            "agenda": self._render_agenda,
            "bullet-list": self._render_bullet_list,
            "two-column": self._render_two_column,
            "stats-callout": self._render_stats,
            "timeline": self._render_timeline,
            "card-grid-2": self._render_cards,
            "card-grid-3": self._render_cards,
            "card-grid-6": self._render_cards,
            "chart": self._render_chart,
            "image-hero": self._render_image_hero,
            "quote-callout": self._render_quote,
            "comparison": self._render_comparison,
            "fact-list": self._render_fact_list,
            "exec-summary": self._render_exec_summary,
        }
        fn = dispatch.get(data.get("type", ""))
        if fn:
            fn(slide, data)

    def _render_title(self, slide, data: dict):
        heading = data.get("heading", "")
        subheading = data.get("subheading", "")
        self._add_text_box(slide, heading,
            left=Inches(1.5), top=Inches(2.5), width=Inches(13), height=Inches(2),
            font_size=Pt(54), font_bold=True, color=self.text_color,
            align=PP_ALIGN.CENTER, font_name=self.display_font)
        if subheading:
            self._add_text_box(slide, subheading,
                left=Inches(2), top=Inches(4.8), width=Inches(12), height=Inches(1),
                font_size=Pt(24), color=self.muted_color,
                align=PP_ALIGN.CENTER)

    def _render_section_divider(self, slide, data: dict):
        self._add_text_box(slide, data.get("heading", ""),
            left=Inches(1.5), top=Inches(3), width=Inches(13), height=Inches(2.5),
            font_size=Pt(48), font_bold=True, color=self.text_color,
            font_name=self.display_font)
        line = slide.shapes.add_shape(1, Inches(1.5), Inches(5.8), Inches(3), Pt(3))
        line.fill.solid()
        line.fill.fore_color.rgb = self.primary
        line.line.fill.background()

    def _render_agenda(self, slide, data: dict):
        self._add_text_box(slide, data.get("heading", ""),
            left=Inches(1), top=Inches(0.5), width=Inches(14), height=Inches(1.2),
            font_size=Pt(36), font_bold=True, color=self.text_color,
            font_name=self.display_font)
        items = data.get("content", {}).get("items", [])
        for i, item in enumerate(items[:8]):
            y = Inches(1.9) + i * Inches(0.8)
            self._add_text_box(slide, f"{str(i+1).zfill(2)}  {item}",
                left=Inches(1.5), top=y, width=Inches(12), height=Inches(0.7),
                font_size=Pt(18), color=self.muted_color)

    def _render_bullet_list(self, slide, data: dict):
        img_path = data.get("resolved_image_path")
        has_img = bool(img_path and Path(img_path).exists())
        text_w = Inches(8) if has_img else Inches(14)

        self._add_text_box(slide, data.get("heading", ""),
            left=Inches(0.8), top=Inches(0.5), width=text_w, height=Inches(1.2),
            font_size=Pt(36), font_bold=True, color=self.text_color,
            font_name=self.display_font)
        bullets = data.get("content", {}).get("bullets", [])[:5]
        for i, bullet in enumerate(bullets):
            y = Inches(1.9) + i * Inches(1.1)
            self._add_text_box(slide, f"●  {bullet}",
                left=Inches(1), top=y, width=text_w - Inches(0.2), height=Inches(0.9),
                font_size=Pt(20), color=self.muted_color)
        if has_img:
            self._add_picture_fit(slide, img_path, Inches(9.2), Inches(1.8), Inches(5.8), Inches(5.5))

    def _render_stats(self, slide, data: dict):
        self._add_text_box(slide, data.get("heading", ""),
            left=Inches(0.8), top=Inches(0.4), width=Inches(14), height=Inches(1.2),
            font_size=Pt(36), font_bold=True, color=self.text_color,
            font_name=self.display_font)
        stats = data.get("content", {}).get("stats", [])[:4]
        w = Inches(14) / max(len(stats), 1)
        for i, stat in enumerate(stats):
            x = Inches(1) + i * w
            self._add_shape_card(slide, x, Inches(2), w - Inches(0.2), Inches(2.2))
            self._add_text_box(slide, stat.get("value", ""),
                left=x + Inches(0.1), top=Inches(2.3), width=w - Inches(0.3), height=Inches(1.0),
                font_size=Pt(48), font_bold=True, color=self.primary,
                align=PP_ALIGN.CENTER, font_name=self.display_font)
            self._add_text_box(slide, stat.get("label", ""),
                left=x + Inches(0.1), top=Inches(3.4), width=w - Inches(0.3), height=Inches(0.6),
                font_size=Pt(16), color=self.muted_color, align=PP_ALIGN.CENTER)
        img_path = data.get("resolved_image_path")
        if img_path and Path(img_path).exists():
            self._add_picture_fit(slide, img_path, Inches(4), Inches(4.5), Inches(8), Inches(4))

    def _render_timeline(self, slide, data: dict):
        self._add_text_box(slide, data.get("heading", ""),
            left=Inches(0.8), top=Inches(0.4), width=Inches(14), height=Inches(1.2),
            font_size=Pt(36), font_bold=True, color=self.text_color,
            font_name=self.display_font)
        items = data.get("content", {}).get("items", [])[:5]
        if not items:
            return
        w = Inches(14) / len(items)
        line = slide.shapes.add_shape(1, Inches(1), Inches(3.8), Inches(14), Pt(2))
        line.fill.solid()
        line.fill.fore_color.rgb = self.primary
        line.line.fill.background()
        for i, item in enumerate(items):
            x = Inches(1) + i * w
            self._add_text_box(slide, item.get("date", ""),
                left=x, top=Inches(2.4), width=w - Inches(0.1), height=Inches(0.7),
                font_size=Pt(14), color=self.primary, align=PP_ALIGN.CENTER, font_bold=True)
            self._add_text_box(slide, item.get("event", ""),
                left=x, top=Inches(4.3), width=w - Inches(0.1), height=Inches(1.5),
                font_size=Pt(14), color=self.muted_color, align=PP_ALIGN.CENTER)

    def _render_cards(self, slide, data: dict):
        self._add_text_box(slide, data.get("heading", ""),
            left=Inches(0.8), top=Inches(0.4), width=Inches(14), height=Inches(1.2),
            font_size=Pt(36), font_bold=True, color=self.text_color,
            font_name=self.display_font)
        cards = data.get("content", {}).get("cards", [])
        slide_type = data.get("type", "card-grid-3")
        cols = 3 if slide_type in ("card-grid-3", "card-grid-6") else 2
        cw = Inches(14) / cols
        for i, card in enumerate(cards[:cols*2]):
            col = i % cols
            row = i // cols
            x = Inches(0.8) + col * cw
            y = Inches(1.8) + row * Inches(3.2)
            self._add_shape_card(slide, x, y, cw - Inches(0.15), Inches(2.9))
            self._add_text_box(slide, card.get("title", ""),
                left=x + Inches(0.2), top=y + Inches(0.3), width=cw - Inches(0.5), height=Inches(0.6),
                font_size=Pt(18), font_bold=True, color=self.text_color)
            self._add_text_box(slide, card.get("body", ""),
                left=x + Inches(0.2), top=y + Inches(1.0), width=cw - Inches(0.5), height=Inches(1.6),
                font_size=Pt(14), color=self.muted_color)

    def _render_chart(self, slide, data: dict):
        self._add_text_box(slide, data.get("heading", ""),
            left=Inches(0.8), top=Inches(0.4), width=Inches(14), height=Inches(1.2),
            font_size=Pt(36), font_bold=True, color=self.text_color,
            font_name=self.display_font)
        img_path = data.get("resolved_image_path")
        if img_path and Path(img_path).exists():
            self._add_picture_fit(slide, img_path, Inches(1), Inches(1.8), Inches(14), Inches(6.5))
        else:
            self._add_text_box(slide, "（图表内容见 HTML 版本）",
                left=Inches(1), top=Inches(3), width=Inches(14), height=Inches(1),
                font_size=Pt(18), color=self.muted_color, align=PP_ALIGN.CENTER)

    def _render_image_hero(self, slide, data: dict):
        img_path = data.get("resolved_image_path")
        if img_path and Path(img_path).exists():
            self._add_picture_fit(slide, img_path, 0, 0, self.W, self.H)
        self._add_text_box(slide, data.get("heading", ""),
            left=Inches(1), top=Inches(5.5), width=Inches(14), height=Inches(1.5),
            font_size=Pt(42), font_bold=True, color=self.text_color,
            font_name=self.display_font)
        if data.get("subheading"):
            self._add_text_box(slide, data["subheading"],
                left=Inches(1), top=Inches(7.1), width=Inches(14), height=Inches(0.7),
                font_size=Pt(22), color=self.muted_color)

    def _render_quote(self, slide, data: dict):
        quote = data.get("content", {}).get("quote", {})
        bar = slide.shapes.add_shape(1, Inches(0.8), Inches(1.5), Pt(6), Inches(5))
        bar.fill.solid()
        bar.fill.fore_color.rgb = self.primary
        bar.line.fill.background()
        self._add_text_box(slide, f'"{quote.get("text", "")}"',
            left=Inches(1.3), top=Inches(1.8), width=Inches(13), height=Inches(4),
            font_size=Pt(28), color=self.text_color, font_name=self.display_font)
        author_text = quote.get("author", "")
        if quote.get("role"):
            author_text += f"  ·  {quote['role']}"
        if author_text:
            self._add_text_box(slide, author_text,
                left=Inches(1.3), top=Inches(6.3), width=Inches(13), height=Inches(0.7),
                font_size=Pt(18), color=self.muted_color)

    def _render_comparison(self, slide, data: dict):
        self._add_text_box(slide, data.get("heading", ""),
            left=Inches(0.8), top=Inches(0.4), width=Inches(14), height=Inches(1.2),
            font_size=Pt(36), font_bold=True, color=self.text_color,
            font_name=self.display_font)
        cols = data.get("content", {}).get("columns", [])
        cw = Inches(14) / max(len(cols), 1)
        for i, col in enumerate(cols):
            x = Inches(0.8) + i * cw
            self._add_shape_card(slide, x, Inches(1.8), cw - Inches(0.2), Inches(6.5))
            self._add_text_box(slide, col.get("title", ""),
                left=x + Inches(0.2), top=Inches(2), width=cw - Inches(0.5), height=Inches(0.8),
                font_size=Pt(22), font_bold=True, color=self.primary)
            for j, item in enumerate(col.get("items", [])[:6]):
                self._add_text_box(slide, f"✓  {item}",
                    left=x + Inches(0.2), top=Inches(2.9) + j * Inches(0.75),
                    width=cw - Inches(0.5), height=Inches(0.65),
                    font_size=Pt(14), color=self.muted_color)

    def _render_fact_list(self, slide, data: dict):
        self._add_text_box(slide, data.get("heading", ""),
            left=Inches(0.8), top=Inches(0.4), width=Inches(14), height=Inches(1.2),
            font_size=Pt(36), font_bold=True, color=self.text_color,
            font_name=self.display_font)
        facts = data.get("content", {}).get("facts", [])
        for i, fact in enumerate(facts[:6]):
            col, row = i % 2, i // 2
            x = Inches(0.8) + col * Inches(7)
            y = Inches(1.8) + row * Inches(2.2)
            self._add_text_box(slide,
                f'{fact.get("emoji","💡")} {fact.get("title","")}',
                left=x, top=y, width=Inches(6.5), height=Inches(0.7),
                font_size=Pt(18), font_bold=True, color=self.text_color)
            self._add_text_box(slide, fact.get("body", ""),
                left=x + Inches(0.3), top=y + Inches(0.75), width=Inches(6.2), height=Inches(1.2),
                font_size=Pt(14), color=self.muted_color)

    def _render_exec_summary(self, slide, data: dict):
        bar = slide.shapes.add_shape(1, Inches(0.5), Inches(0.4), Pt(6), Inches(8.2))
        bar.fill.solid()
        bar.fill.fore_color.rgb = self.primary
        bar.line.fill.background()
        self._add_text_box(slide, data.get("heading", ""),
            left=Inches(0.9), top=Inches(0.4), width=Inches(14), height=Inches(1.2),
            font_size=Pt(36), font_bold=True, color=self.text_color,
            font_name=self.display_font)
        points = data.get("content", {}).get("points", [])
        for i, pt in enumerate(points[:6]):
            self._add_text_box(slide, f"●  {pt}",
                left=Inches(0.9), top=Inches(1.8) + i * Inches(1.1),
                width=Inches(13.5), height=Inches(1),
                font_size=Pt(18), color=self.muted_color)

    def _render_two_column(self, slide, data: dict):
        self._add_text_box(slide, data.get("heading", ""),
            left=Inches(0.8), top=Inches(0.4), width=Inches(14), height=Inches(1.2),
            font_size=Pt(36), font_bold=True, color=self.text_color,
            font_name=self.display_font)
        left_col = data.get("content", {}).get("left", {})
        right_col = data.get("content", {}).get("right", {})
        for col_data, x_off in [(left_col, Inches(0.8)), (right_col, Inches(8.3))]:
            if col_data.get("title"):
                self._add_text_box(slide, col_data["title"],
                    left=x_off, top=Inches(1.8), width=Inches(6.8), height=Inches(0.8),
                    font_size=Pt(22), font_bold=True, color=self.text_color)
            items = col_data.get("items", [col_data.get("text", "")])
            for j, item in enumerate(items[:5]):
                self._add_text_box(slide, f"●  {item}" if col_data.get("type") == "bullets" else item,
                    left=x_off, top=Inches(2.7) + j * Inches(1.0),
                    width=Inches(6.8), height=Inches(0.9),
                    font_size=Pt(16), color=self.muted_color)

    def _add_text_box(self, slide, text: str, left, top, width, height,
                      font_size=Pt(18), font_bold=False, color=None,
                      align=PP_ALIGN.LEFT, font_name=None) -> object:
        txBox = slide.shapes.add_textbox(left, top, width, height)
        tf = txBox.text_frame
        tf.word_wrap = True
        p = tf.paragraphs[0]
        p.alignment = align
        run = p.add_run()
        run.text = text
        run.font.size = font_size
        run.font.bold = font_bold
        run.font.color.rgb = color or self.text_color
        if font_name:
            run.font.name = font_name
        return txBox

    def _add_shape_card(self, slide, left, top, width, height):
        shape = slide.shapes.add_shape(1, left, top, width, height)
        shape.fill.solid()
        bg_hex = self.theme.get("bg_color", "0f172a")
        r = int(bg_hex[0:2], 16)
        g = int(bg_hex[2:4], 16)
        b = int(bg_hex[4:6], 16)
        fill_color = RGBColor(min(255, r + 20), min(255, g + 20), min(255, b + 20))
        shape.fill.fore_color.rgb = fill_color
        shape.line.color.rgb = self.primary
        shape.line.width = Pt(0.75)
        return shape


class BackgroundScreenshotter:
    """使用 Playwright 截图每张幻灯片的背景层"""

    async def screenshot_all_backgrounds(self, html_path: str, output_dir: str) -> list[str]:
        from playwright.async_api import async_playwright
        output_dir = Path(output_dir)
        output_dir.mkdir(exist_ok=True)
        bg_paths = []

        async with async_playwright() as p:
            browser = await p.chromium.launch()
            page = await browser.new_page(viewport={"width": 1280, "height": 720})
            await page.goto(f"file://{Path(html_path).resolve()}")
            await page.wait_for_timeout(1000)

            slide_count = await page.locator('.slide').count()
            for i in range(slide_count):
                await page.evaluate(f"""
                    const allSlides = document.querySelectorAll('.slide');
                    allSlides.forEach((s, idx) => {{
                        s.style.opacity = idx === {i} ? '1' : '0';
                    }});
                    const currentSlide = allSlides[{i}];
                    if (currentSlide) {{
                        currentSlide.querySelectorAll(':scope > *:not(.blob-container)').forEach(el => {{
                            el.style.visibility = 'hidden';
                        }});
                    }}
                """)
                await page.wait_for_timeout(500)
                bg_path = str(output_dir / f"bg_slide_{i}.png")
                await page.locator(f'.slide').nth(i).screenshot(path=bg_path)
                bg_paths.append(bg_path)

            await browser.close()
        return bg_paths


if __name__ == "__main__":
    import sys
    slides_path = sys.argv[1]
    html_path = sys.argv[2]
    output_path = sys.argv[3]
    theme_path = sys.argv[4] if len(sys.argv) > 4 else None

    slides = json.loads(Path(slides_path).read_text(encoding="utf-8"))

    # Derive theme name from outline.json in the same directory
    outline_path = Path(slides_path).parent / "outline.json"
    theme_name = "aurora-borealis"
    if outline_path.exists():
        theme_name = json.loads(outline_path.read_text(encoding="utf-8")).get("theme", theme_name)

    theme_config = {"name": theme_name, "primary_color": "6366f1",
                    "text_color": "f1f5f9", "bg_color": "050818"}
    if theme_path:
        theme_config.update(json.loads(Path(theme_path).read_text()))

    themes_dir = str(Path(__file__).parent.parent / "themes")
    content_dir = str(Path(output_path).parent / "content_images")
    bg_dir = str(Path(output_path).parent / "bg_frames")

    async def _run():
        content_renderer = ContentImageRenderer(themes_dir=themes_dir)
        enriched = await content_renderer.render_all(slides, theme_name, content_dir)
        img_count = sum(1 for s in enriched if s.get("resolved_image_path"))
        print(f"✓ 内容图片转换完成 → {img_count} 张")
        bg_images = await BackgroundScreenshotter().screenshot_all_backgrounds(html_path, bg_dir)
        print(f"✓ 截图 {len(bg_images)} 张背景")
        return enriched, bg_images

    enriched_slides, bg_images = asyncio.run(_run())

    builder = HybridPPTXBuilder(theme_config)
    result = builder.build(enriched_slides, bg_images=bg_images, output_path=output_path)
    print(f"✓ PPTX 导出完成 → {result}")
