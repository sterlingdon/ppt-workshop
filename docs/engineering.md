# Article-to-PPT Engineering Reference

**Version:** 1.0  
**Status:** Authoritative — replaces article_to_ppt_agent_architecture.md, multi_style_architecture.md, pptx_delivery_architecture.md, style_consistency_design.md

---

## 1. System Architecture

### 7-Agent Pipeline

```
INPUT (URL / 文本 / PDF)
    ↓
[CLAUDE] Agent 1 · 文章提取       → output/article_text.md
    ↓
[CLAUDE] Agent 2 · 内容分析       → output/analysis.json
    ↓
[CLAUDE] Agent 3 · 幻灯片规划     → output/outline.json
    ↓
[CLAUDE] Agent 4 · 幻灯片数据构建 → output/slides.json
    ↓
[PYTHON] Agent 5 · 图片编排       → output/slides_with_images.json
    ↓
[PYTHON] Agent 6 · HTML渲染       → output/presentation.html
    ↓
[PYTHON] Agent 7 · PPTX导出       → output/presentation_hybrid.pptx
                                    output/assets.zip
```

**Agent 1-4**: Claude executes — reasoning, extraction, structured JSON output.  
**Agent 5-7**: Python scripts — mechanical image fetching, HTML rendering, PPTX assembly.

### Data Flow

Each agent reads from the previous checkpoint file and writes one output file to `output/`. If the output file already exists and is non-empty, the agent is skipped (checkpoint resume). Delete the file to force re-run.

### Responsibility Boundaries

| Agent | Tool | Input | Output | Responsibility |
|-------|------|-------|--------|----------------|
| 1 | Claude | URL/text/PDF | article_text.md | Extract clean article text |
| 2 | Claude | article_text.md | analysis.json | Domain, key points, statistics, quotes |
| 3 | Claude | analysis.json | outline.json | Slide count, types, style_constraints |
| 4 | Claude | outline.json + analysis.json | slides.json | Full content per slide + image_request |
| 5 | Python | slides.json | slides_with_images.json | Resolve images via 5-level fallback |
| 6 | Python | slides_with_images.json | presentation.html | Single-file HTML presentation |
| 7 | Python | slides_with_images.json + HTML | presentation_hybrid.pptx | Hybrid PPTX (bg screenshot + native content) |

---

## 2. Data Schema Reference

### analysis.json (Agent 2 output)

Schema: `schemas/analysis.schema.json`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| domain | string enum | ✓ | technology/finance/healthcare/startup/education/business/cybersecurity/sustainability/gaming/culture/other |
| title | string | ✓ | Distilled article title |
| summary | string | — | 2-3 sentence summary |
| key_points | string[] | ✓ | Max 8 core arguments |
| statistics | {value, label, context}[] | — | Max 5 real data points |
| quotes | {text, author, role}[] | — | Max 3 verbatim quotes |
| entities | string[] | — | Companies, people, technologies |
| complexity | simple/intermediate/expert | — | Technical depth |
| suggested_theme | string enum | ✓ | See theme mapping table |
| language | string | — | zh or en |

### outline.json (Agent 3 output)

Schema: `schemas/outline.schema.json`

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| theme | string | ✓ | Active theme name |
| style_constraints | object | ✓ | Global visual style (fixed for entire presentation) |
| slides | array | ✓ | 8-25 slide descriptors |

`style_constraints` fields:
- `heading_emphasis`: gradient/solid/glow
- `card_style`: glass/solid-surface/outlined/accent-border-left
- `stat_style`: gradient-text/accent-color/white-glow
- `bullet_style`: dot/check/emoji/icon/dash
- `divider_style`: gradient-line/dot-separator/none
- `image_style_fingerprint`: 2-6 style descriptor strings for image generation

Each slide in `slides`:
- `index`: integer (0-based)
- `type`: one of 17 types (see Section 3)
- `title`: slide heading preview
- `needs_image`: boolean
- `notes`: optional string

### slides.json (Agent 4 output)

Schema: `schemas/slides.schema.json`

Array of slide objects. Each slide:

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| index | integer | ✓ | 0-based position |
| type | string | ✓ | One of 17 slide types |
| heading | string | ✓ | Slide heading |
| subheading | string | — | Optional subtitle |
| content | object | ✓ | Type-specific content (see Section 3) |
| image_request | object | — | Required when needs_image=true |

`image_request` fields:
- `description`: string — what the image should show
- `preferred_strategy`: svg/canvas/icon/search/ai
- `fallback_chain`: string[] — ordered list of strategies to try
- `svg_code`: string — inline SVG (when strategy=svg)
- `icon_name`: string — Lucide icon name (when strategy=icon)
- `search_query`: string — Unsplash search query
- `ai_prompt`: string — DALL-E prompt

---

## 3. Slide Type Reference

17 supported types and their `content` schemas:

| Type | content fields | Notes |
|------|---------------|-------|
| title | (none) | heading + optional subheading at top level |
| conclusion | (none) | Same rendering as title |
| section-divider | `section_number?: string` | Full-screen heading with accent line |
| agenda | `items: string[]` | Numbered list |
| bullet-list | `bullets: string[]` | Max 5, icon from style_constraints.bullet_style |
| two-column | `left: {title?, type, items?/text?}`, `right: same` | type: "bullets" or "text" |
| stats-callout | `stats: [{value, label, context?}]` | Max 4 stats |
| timeline | `items: [{date, event}]` | Max 5 items, horizontal flow |
| card-grid-2 | `cards: [{title, body, icon?}]` | 2 columns |
| card-grid-3 | `cards: [{title, body, icon?}]` | 3 columns |
| card-grid-6 | `cards: [{title, body, icon?}]` | 3×2 grid |
| chart | `chart: {type, labels, datasets}` | Chart.js format |
| image-hero | (none) | Full-bleed image with text overlay |
| quote-callout | `quote: {text, author, role?}` | Left accent border |
| comparison | `columns: [{title, items[], positive?}]` | Side-by-side columns |
| fact-list | `facts: [{emoji, title, body}]` | 2-column grid, max 6 |
| exec-summary | `points: string[]` | Accent bar + numbered points |

---

## 4. Image Strategy (5-Level Fallback)

### Level Decision Matrix

| Slide Content | Recommended Strategy | fallback_chain |
|---------------|---------------------|----------------|
| Data / statistics | SVG (Claude-generated) | ["svg", "icon"] |
| Charts | Canvas (Chart.js) | ["canvas"] |
| Decorative / card icons | Icon (Lucide CDN) | ["icon", "svg"] |
| Scene / atmosphere | Search (Unsplash) | ["search", "ai"] |
| Custom brand | AI (DALL-E 3) | ["ai"] |
| Quote illustration | Search | ["search", "icon"] |

### Level Details

**Level 1 — SVG Inline**
- Claude generates SVG during Agent 4, embedded in `image_request.svg_code`
- Python orchestrator injects CSS variables (replaces hardcoded hex colors)
- viewBox="0 0 400 240", use only polyline/rect/circle/path
- Cost: free

**Level 2 — HTML Canvas / Chart.js**
- For chart slides where chart_data is available
- Rendered as inline HTML+JS, Playwright captures it for PPTX layer
- Cost: free

**Level 3 — Icon CDN (Lucide)**
- `icon_name` maps to `https://cdn.jsdelivr.net/npm/lucide-static@latest/icons/{name}.svg`
- Emoji fallback if CDN unreachable
- Cost: free

**Level 4 — Image Search (Unsplash)**
- Requires `UNSPLASH_KEY` in `.env.json`
- `search_query` or `description` as search terms
- Returns `regular` size URL + photographer credit
- Cost: free tier (50 req/hour)

**Level 5 — AI Generation (DALL-E 3)**
- Requires `OPENAI_KEY` in `.env.json`
- `ai_prompt` appended with `image_style_fingerprint` from style_constraints
- Size: 1792×1024 (wide format)
- Cost: ~$0.04/image

### Cache

Images cached by MD5 key (chain + content descriptor) in `image_cache/`. Cache is gitignored. Delete to force fresh fetch.

---

## 5. Theme System

### CSS Variable Architecture

`themes/_base.css` defines the complete variable interface. Theme files only override values — HTML and component CSS never reference theme-specific values directly.

Variable categories:
- Color: `--color-bg`, `--color-surface`, `--color-primary`, `--color-secondary`, `--color-accent`, `--color-text`, `--color-text-muted`, `--color-text-subtle`, `--color-border`
- Gradient: `--gradient-heading`, `--gradient-bg`, `--gradient-card`, `--gradient-accent-line`
- Typography: `--font-display`, `--font-body`, `--font-mono`, `--font-size-*`, `--font-weight-*`
- Card: `--card-bg`, `--card-border`, `--card-radius`, `--card-padding`, `--card-shadow`, `--card-backdrop`
- Layout: `--slide-width` (1280px), `--slide-height` (720px), `--slide-padding`
- Animation: `--transition-fast/base/slow`, `--blob-opacity`, `--blob-blur`
- Feature flags: `--enable-blobs`, `--enable-particles`, `--enable-glass`, `--enable-gradient-text`

### MVP Themes

| Theme | Style | Primary Use | Key Colors |
|-------|-------|-------------|------------|
| aurora-borealis | Dark · aurora gradient | technology/AI | #6366f1, #38bdf8, #a78bfa |
| bold-signal | High contrast · orange | business/startup | #f97316, #fbbf24 |
| editorial-ink | Light · print typography | education/content | #1c1917, #dc2626, Playfair Display |

### Domain → Theme Mapping

| Domain | Theme |
|--------|-------|
| technology, AI, cybersecurity | aurora-borealis |
| finance | midnight-cathedral (MVP: bold-signal) |
| startup, business | bold-signal |
| healthcare, education, culture | editorial-ink |
| other | aurora-borealis |

### Adding a New Theme

1. Create `themes/<theme-name>.css`
2. Override any variables from `_base.css` (override only what changes)
3. Add to `suggested_theme` enum in `schemas/analysis.schema.json`
4. Add domain mapping to SKILL.md Agent 2 section

---

## 6. Hybrid PPTX Architecture

### Two-Layer Approach

**Layer 1 — Background (Playwright screenshot)**  
Playwright opens `presentation.html`, iterates each slide, hides the text content layer, screenshots the background visuals (gradients, blobs, particles). Each screenshot saved as `bg_frames/bg_slide_N.png` (1280×720 PNG).

**Layer 2 — Content (python-pptx native)**  
`HybridPPTXBuilder` adds slides using blank layout (16:9, 1280×720 equiv in EMU). For each slide:
1. Insert background PNG as a picture shape, z-ordered to bottom
2. Add native text boxes, shape cards using python-pptx API

### Content Degradation Table

HTML feature → PPTX equivalent:

| HTML | PPTX Native |
|------|-------------|
| CSS gradient text | Solid color (primary_color) |
| Glass card | Filled rectangle (bg+20 lighter) with primary border |
| Blob animations | Captured in background screenshot |
| Chart.js canvas | Screenshot in background; text fallback in content layer |
| Custom font (Playfair) | Calibri (system fallback) |
| Bullet icons (●, ✓) | Unicode in text run |

### PPTX Theme Config

Passed to `HybridPPTXBuilder(theme_config=...)`:

```json
{
  "name": "aurora-borealis",
  "primary_color": "6366f1",
  "text_color": "f1f5f9",
  "bg_color": "050818",
  "muted_color": "94a3b8",
  "display_font": "Calibri",
  "body_font": "Calibri"
}
```

---

## 7. Adding New Slide Types

1. Add the type string to `schemas/outline.schema.json` → `slides.items.properties.type.enum`
2. Add to `HTMLRenderer` in `tools/html_renderer.py`:
   ```python
   @slide_type("new-type-name")
   def _render_new_type(self, slide: dict, style: dict) -> str:
       # return HTML string
   ```
3. Add to `HybridPPTXBuilder._render_slide_content` dispatch dict in `tools/pptx_exporter.py`
4. Add content schema to SKILL.md Agent 4 section
5. Write test in `tests/test_html_renderer.py` for the new type

---

## 8. Project File Map

```
ppt-workshop/
├── SKILL.md                      # Skill entry point (root, standard architecture)
├── requirements.txt              # Python dependencies
├── pytest.ini                    # asyncio_mode = auto
├── .gitignore                    # Ignores output/, image_cache/, __pycache__
├── tools/
│   ├── ingest.py                 # Agent 1 helper: PDF/URL content extraction
│   ├── image_orchestrator.py     # Agent 5: 5-level image fallback
│   ├── html_renderer.py          # Agent 6: JSON → HTML presentation
│   └── pptx_exporter.py          # Agent 7: HTML + JSON → Hybrid PPTX
├── themes/
│   ├── _base.css                 # CSS variable interface (all themes extend this)
│   ├── aurora-borealis.css       # Dark aurora gradient theme
│   ├── bold-signal.css           # High contrast orange theme
│   └── editorial-ink.css         # Light print typography theme
├── templates/
│   └── slide_base.html           # Jinja2 HTML presentation template
├── schemas/
│   ├── analysis.schema.json      # Agent 2 output validation
│   ├── outline.schema.json       # Agent 3 output validation
│   └── slides.schema.json        # Agent 4 output validation
├── tests/
│   ├── fixtures/test_article.md  # Test fixture article
│   ├── test_schemas.py           # JSON schema validation tests
│   ├── test_ingest.py            # Ingest tool tests
│   ├── test_html_renderer.py     # HTML renderer tests
│   ├── test_image_orchestrator.py # Image orchestrator tests
│   ├── test_pptx_exporter.py     # PPTX exporter tests
│   └── test_e2e.py               # End-to-end integration tests
├── docs/
│   └── engineering.md            # This document — authoritative technical reference
└── output/                       # Runtime checkpoints (gitignored)
```
