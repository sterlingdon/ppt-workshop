"""Agent 6: slides_with_images.json → 单文件 HTML 演示"""
from __future__ import annotations
import json
from pathlib import Path
from jinja2 import Environment, FileSystemLoader


SLIDE_RENDERERS = {}  # type 字符串 → 渲染方法名


def slide_type(*types):
    """装饰器：注册幻灯片类型渲染器"""
    def decorator(fn):
        for t in types:
            SLIDE_RENDERERS[t] = fn.__name__
        return fn
    return decorator


class HTMLRenderer:
    def __init__(self, themes_dir: str, templates_dir: str):
        self.themes_dir = Path(themes_dir)
        self.templates_dir = Path(templates_dir)
        self.env = Environment(
            loader=FileSystemLoader(str(templates_dir)),
            autoescape=False,
        )

    def render(self, data: dict) -> str:
        """主入口：data 为 slides_with_images.json 内容（dict）"""
        theme = data.get("theme", "aurora-borealis")
        style = data.get("style_constraints", {})

        rendered_slides = []
        for slide in data["slides"]:
            slide_type_name = slide.get("type", "")
            method_name = SLIDE_RENDERERS.get(slide_type_name)
            if not method_name:
                raise ValueError(f"未知幻灯片类型: {slide_type_name}")
            method = getattr(self, method_name)
            html_content = method(slide, style)
            rendered_slides.append({
                **slide,
                "html_content": html_content,
                "blobs": self._gen_blobs(slide_type_name),
            })

        template = self.env.get_template("slide_base.html")
        return template.render(
            title=data.get("title", "演示文稿"),
            lang=data.get("language", "zh"),
            theme_css_path=f"../themes/{theme}.css",
            slides=rendered_slides,
        )

    def _gen_blobs(self, slide_type: str) -> list[dict]:
        """按幻灯片类型生成 Blob 配置（视觉节奏）"""
        high_energy = {"title", "conclusion", "image-hero"}
        low_energy = {"bullet-list", "two-column", "fact-list", "exec-summary"}
        if slide_type in high_energy:
            return [
                {"size": 500, "x": 10, "y": 20, "color": "var(--color-primary)"},
                {"size": 400, "x": 60, "y": 60, "color": "var(--color-secondary)"},
                {"size": 300, "x": 80, "y": 10, "color": "var(--color-accent)"},
            ]
        elif slide_type in low_energy:
            return [
                {"size": 350, "x": -10, "y": 30, "color": "var(--color-primary)"},
                {"size": 280, "x": 85, "y": 65, "color": "var(--color-secondary)"},
            ]
        else:
            return [
                {"size": 400, "x": 5, "y": 50, "color": "var(--color-primary)"},
                {"size": 350, "x": 70, "y": 20, "color": "var(--color-secondary)"},
            ]

    # ─── 幻灯片类型渲染器 ──────────────────────────────────────

    @slide_type("title")
    def _render_title(self, slide: dict, style: dict) -> str:
        heading_class = "heading-gradient" if style.get("heading_emphasis") == "gradient" else ""
        image_html = f'<img src="{slide["resolved_image"]}" class="title-bg-img" alt="">' if slide.get("resolved_image") else ""
        return f"""
<div class="title-slide" style="text-align:center; padding: 4rem;">
  {image_html}
  <h1 class="title-heading {heading_class}" style="
    font-family: var(--font-display);
    font-size: var(--font-size-display);
    font-weight: var(--font-weight-display);
    margin-bottom: 1.5rem;
    line-height: 1.1;
  ">{slide['heading']}</h1>
  {"<p class='subtitle' style='font-size: var(--font-size-h2); color: var(--color-text-muted); max-width: 700px; margin: 0 auto;'>" + slide.get('subheading','') + "</p>" if slide.get('subheading') else ""}
</div>"""

    @slide_type("section-divider")
    def _render_section_divider(self, slide: dict, style: dict) -> str:
        heading_class = "heading-gradient" if style.get("heading_emphasis") == "gradient" else ""
        section_num = slide.get("content", {}).get("section_number", "")
        return f"""
<div style="display:flex; flex-direction:column; justify-content:center; height:100%; padding: 4rem 6rem;">
  {f'<span style="font-size:0.9rem; color:var(--color-text-subtle); font-family:var(--font-mono); letter-spacing:0.1em; margin-bottom:1rem;">SECTION {section_num}</span>' if section_num else ""}
  <h2 class="{heading_class}" style="
    font-family: var(--font-display);
    font-size: var(--font-size-display);
    font-weight: var(--font-weight-display);
    line-height: 1.1;
  ">{slide['heading']}</h2>
  <hr class="accent-divider" style="max-width:200px; margin-top:1.5rem;">
</div>"""

    @slide_type("agenda")
    def _render_agenda(self, slide: dict, style: dict) -> str:
        items = slide.get("content", {}).get("items", [])
        items_html = "".join([
            f'<li style="padding: 0.75rem 0; border-bottom: 1px solid var(--color-border); color: var(--color-text-muted); font-size: var(--font-size-body);">'
            f'<span style="color:var(--color-primary); font-weight:600; margin-right:1rem;">{str(i+1).zfill(2)}</span>{item}'
            f'</li>'
            for i, item in enumerate(items)
        ])
        return f"""
<div style="padding: 2rem 0;">
  <h2 style="font-family:var(--font-display); font-size:var(--font-size-h1); font-weight:var(--font-weight-heading); margin-bottom:2rem;">{slide['heading']}</h2>
  <ol style="list-style:none; padding:0; max-width:600px;">{items_html}</ol>
</div>"""

    @slide_type("bullet-list")
    def _render_bullet_list(self, slide: dict, style: dict) -> str:
        bullets = slide.get("content", {}).get("bullets", [])[:5]  # max 5
        bullet_style = style.get("bullet_style", "dot")
        icons = {"dot": "●", "check": "✓", "dash": "—"}
        icon = icons.get(bullet_style, "●")
        bullets_html = "".join([
            f'<li style="display:flex; gap:1rem; padding:0.6rem 0; font-size:var(--font-size-body); line-height:1.6;">'
            f'<span style="color:var(--color-primary); flex-shrink:0; margin-top:0.15rem;">{icon}</span>'
            f'<span>{b}</span></li>'
            for b in bullets
        ])
        image_html = f'<div style="width:280px; flex-shrink:0;"><img src="{slide["resolved_image"]}" style="width:100%; border-radius:var(--card-radius);" alt=""></div>' if slide.get("resolved_image") else ""
        return f"""
<div style="display:flex; gap:3rem; align-items:center; height:100%;">
  <div style="flex:1;">
    <h2 style="font-family:var(--font-display); font-size:var(--font-size-h1); font-weight:var(--font-weight-heading); margin-bottom:1.5rem;">{slide['heading']}</h2>
    <ul style="list-style:none; padding:0;">{bullets_html}</ul>
  </div>
  {image_html}
</div>"""

    @slide_type("stats-callout")
    def _render_stats_callout(self, slide: dict, style: dict) -> str:
        stats = slide.get("content", {}).get("stats", [])[:4]
        stat_class = "gradient-text" if style.get("stat_style") == "gradient-text" else ""
        card_style_val = style.get("card_style", "glass")
        card_class = "glass-card" if card_style_val in ("glass",) else ""
        stats_html = "".join([
            f'<div class="{card_class}" style="text-align:center; padding:1.5rem 1rem; flex:1;">'
            f'<div class="stat-value {stat_class}">{s["value"]}</div>'
            f'<div style="font-size:var(--font-size-small); color:var(--color-text-muted); margin-top:0.5rem;">{s["label"]}</div>'
            f'{"<div style=\"font-size:0.75rem; color:var(--color-text-subtle); margin-top:0.25rem;\">" + s.get("context","") + "</div>" if s.get("context") else ""}'
            f'</div>'
            for s in stats
        ])
        return f"""
<div>
  <h2 style="font-family:var(--font-display); font-size:var(--font-size-h1); font-weight:var(--font-weight-heading); margin-bottom:2rem;">{slide['heading']}</h2>
  <div style="display:flex; gap:1.5rem;">{stats_html}</div>
</div>"""

    @slide_type("quote-callout")
    def _render_quote_callout(self, slide: dict, style: dict) -> str:
        quote = slide.get("content", {}).get("quote", {})
        return f"""
<div style="display:flex; flex-direction:column; justify-content:center; height:100%; padding:2rem;">
  <div style="border-left:4px solid var(--color-primary); padding-left:2rem; max-width:800px;">
    <p style="font-size:clamp(1.3rem,2.5vw,2rem); font-family:var(--font-display); line-height:1.5; color:var(--color-text); margin-bottom:1.5rem;">
      "{quote.get('text','')}"
    </p>
    <div style="color:var(--color-text-muted);">
      <span style="font-weight:600;">{quote.get('author','')}</span>
      {"<span style='margin-left:0.5rem; color:var(--color-text-subtle);'>· " + quote.get('role','') + "</span>" if quote.get('role') else ""}
    </div>
  </div>
</div>"""

    @slide_type("timeline")
    def _render_timeline(self, slide: dict, style: dict) -> str:
        items = slide.get("content", {}).get("items", [])[:5]
        items_html = "".join([
            f'<div style="flex:1; text-align:center;">'
            f'<div style="width:12px; height:12px; border-radius:50%; background:var(--color-primary); margin:0 auto 0.75rem;"></div>'
            f'<div style="font-weight:600; font-size:var(--font-size-small); color:var(--color-primary); margin-bottom:0.25rem;">{item.get("date","")}</div>'
            f'<div style="font-size:var(--font-size-small); line-height:1.5; color:var(--color-text-muted);">{item.get("event","")}</div>'
            f'</div>'
            for item in items
        ])
        return f"""
<div>
  <h2 style="font-family:var(--font-display); font-size:var(--font-size-h1); font-weight:var(--font-weight-heading); margin-bottom:2.5rem;">{slide['heading']}</h2>
  <div style="position:relative;">
    <div style="position:absolute; top:6px; left:5%; right:5%; height:2px; background:var(--gradient-accent-line);"></div>
    <div style="display:flex; gap:1rem; position:relative;">{items_html}</div>
  </div>
</div>"""

    @slide_type("card-grid-2", "card-grid-3", "card-grid-6")
    def _render_card_grid(self, slide: dict, style: dict) -> str:
        cards = slide.get("content", {}).get("cards", [])
        cols = 3 if slide["type"] == "card-grid-3" else (2 if slide["type"] == "card-grid-2" else 3)
        card_class = "glass-card" if style.get("card_style") == "glass" else ""
        cards_html = "".join([
            f'<div class="{card_class}" style="padding:1.25rem;">'
            f'{"<div style=\"font-size:1.5rem; margin-bottom:0.5rem;\">" + c.get("icon","") + "</div>" if c.get("icon") else ""}'
            f'<h3 style="font-size:var(--font-size-body); font-weight:600; margin-bottom:0.5rem;">{c.get("title","")}</h3>'
            f'<p style="font-size:var(--font-size-small); color:var(--color-text-muted); line-height:1.5;">{c.get("body","")}</p>'
            f'</div>'
            for c in cards
        ])
        return f"""
<div>
  <h2 style="font-family:var(--font-display); font-size:var(--font-size-h1); font-weight:var(--font-weight-heading); margin-bottom:1.5rem;">{slide['heading']}</h2>
  <div style="display:grid; grid-template-columns:repeat({cols}, 1fr); gap:1.25rem;">{cards_html}</div>
</div>"""

    @slide_type("chart")
    def _render_chart(self, slide: dict, style: dict) -> str:
        chart_html = slide.get("resolved_image", "")
        if not chart_html:
            chart_html = "<div style='padding:2rem; color:var(--color-text-muted);'>图表数据加载中...</div>"
        return f"""
<div>
  <h2 style="font-family:var(--font-display); font-size:var(--font-size-h1); font-weight:var(--font-weight-heading); margin-bottom:1.5rem;">{slide['heading']}</h2>
  {chart_html}
</div>"""

    @slide_type("image-hero")
    def _render_image_hero(self, slide: dict, style: dict) -> str:
        img_src = slide.get("resolved_image", "")
        return f"""
<div style="position:relative; width:100%; height:100%; overflow:hidden; padding:0;">
  {"<img src='" + img_src + "' style='position:absolute; inset:0; width:100%; height:100%; object-fit:cover; opacity:0.5;' alt=''>" if img_src else ""}
  <div style="position:relative; z-index:1; padding:4rem; display:flex; flex-direction:column; justify-content:flex-end; height:100%; background:linear-gradient(to top, rgba(0,0,0,0.8) 0%, transparent 60%);">
    <h2 style="font-family:var(--font-display); font-size:var(--font-size-display); font-weight:var(--font-weight-display); margin-bottom:1rem;">{slide['heading']}</h2>
    {"<p style='font-size:var(--font-size-h2); color:var(--color-text-muted);'>" + slide.get('subheading','') + "</p>" if slide.get('subheading') else ""}
  </div>
</div>"""

    @slide_type("comparison")
    def _render_comparison(self, slide: dict, style: dict) -> str:
        cols = slide.get("content", {}).get("columns", [])
        cols_html = "".join([
            f'<div class="glass-card">'
            f'<h3 style="font-size:var(--font-size-h2); font-weight:600; margin-bottom:1rem; color:var(--color-primary);">{col.get("title","")}</h3>'
            f'<ul style="list-style:none; padding:0;">'
            + "".join([f'<li style="padding:0.4rem 0; font-size:var(--font-size-small); color:var(--color-text-muted);">{"✓" if col.get("positive") else "–"} {item}</li>' for item in col.get("items",[])])
            + f'</ul></div>'
            for col in cols
        ])
        return f"""
<div>
  <h2 style="font-family:var(--font-display); font-size:var(--font-size-h1); font-weight:var(--font-weight-heading); margin-bottom:1.5rem;">{slide['heading']}</h2>
  <div style="display:grid; grid-template-columns:repeat({len(cols)}, 1fr); gap:1.5rem;">{cols_html}</div>
</div>"""

    @slide_type("two-column")
    def _render_two_column(self, slide: dict, style: dict) -> str:
        left = slide.get("content", {}).get("left", {})
        right = slide.get("content", {}).get("right", {})
        def col_html(col):
            if col.get("type") == "bullets":
                items = "".join([f'<li style="padding:0.4rem 0; color:var(--color-text-muted);">● {b}</li>' for b in col.get("items",[])])
                return f'<ul style="list-style:none; padding:0;">{items}</ul>'
            return f'<p style="color:var(--color-text-muted); line-height:1.7;">{col.get("text","")}</p>'
        return f"""
<div>
  <h2 style="font-family:var(--font-display); font-size:var(--font-size-h1); font-weight:var(--font-weight-heading); margin-bottom:2rem;">{slide['heading']}</h2>
  <div style="display:grid; grid-template-columns:1fr 1fr; gap:3rem;">
    <div>{"<h3 style='font-weight:600; margin-bottom:1rem;'>" + left.get('title','') + "</h3>" if left.get('title') else ""}{col_html(left)}</div>
    <div>{"<h3 style='font-weight:600; margin-bottom:1rem;'>" + right.get('title','') + "</h3>" if right.get('title') else ""}{col_html(right)}</div>
  </div>
</div>"""

    @slide_type("fact-list")
    def _render_fact_list(self, slide: dict, style: dict) -> str:
        facts = slide.get("content", {}).get("facts", [])
        facts_html = "".join([
            f'<div style="display:flex; gap:1rem; padding:0.75rem; border-radius:8px;">'
            f'<span style="font-size:1.5rem; flex-shrink:0;">{f.get("emoji","💡")}</span>'
            f'<div><strong style="display:block; margin-bottom:0.25rem;">{f.get("title","")}</strong>'
            f'<span style="color:var(--color-text-muted); font-size:var(--font-size-small);">{f.get("body","")}</span></div>'
            f'</div>'
            for f in facts
        ])
        return f"""
<div>
  <h2 style="font-family:var(--font-display); font-size:var(--font-size-h1); font-weight:var(--font-weight-heading); margin-bottom:1.5rem;">{slide['heading']}</h2>
  <div style="display:grid; grid-template-columns:1fr 1fr; gap:0.5rem;">{facts_html}</div>
</div>"""

    @slide_type("exec-summary")
    def _render_exec_summary(self, slide: dict, style: dict) -> str:
        points = slide.get("content", {}).get("points", [])
        points_html = "".join([
            f'<li style="padding:0.6rem 0; border-bottom:1px solid var(--color-border); color:var(--color-text-muted); font-size:var(--font-size-body); line-height:1.6;">{p}</li>'
            for p in points
        ])
        return f"""
<div style="display:flex; gap:2rem; height:100%; align-items:stretch;">
  <div style="width:6px; background:var(--gradient-accent-line); border-radius:3px; flex-shrink:0;"></div>
  <div style="flex:1;">
    <h2 style="font-family:var(--font-display); font-size:var(--font-size-h1); font-weight:var(--font-weight-heading); margin-bottom:1.5rem;">{slide['heading']}</h2>
    <ul style="list-style:none; padding:0;">{points_html}</ul>
  </div>
</div>"""

    @slide_type("conclusion")
    def _render_conclusion(self, slide: dict, style: dict) -> str:
        return self._render_title(slide, style)
