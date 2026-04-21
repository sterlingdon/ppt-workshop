# Article-to-PPT Engineering Reference

**Version:** 1.1
**Status:** Authoritative for the current React rendering pipeline

---

## 1. System Architecture

### Current Pipeline

```
INPUT (URL / 文本 / PDF)
    ↓
[PYTHON/AI] Agent 0 · 建立项目工作区 → output/projects/<project-id>/
    ↓
[CLAUDE] Agent 1 · 文章提取       → article_text.md
    ↓
[CLAUDE] Agent 2 · 内容分析       → analysis.json
    ↓
[CLAUDE] Agent 3 · 幻灯片规划     → outline.json
    ↓
[CLAUDE] Agent 4 · React组件构建  → web/src/slides/Slide_N.tsx
    ↓
[PYTHON] Agent 5 · 图片编排       → slides_with_images.json (optional/when needed)
    ↓
[PYTHON] Agent 6 · React布局抽取   → layout_manifest.json + assets/
    ↓
[PYTHON] Agent 7 · PPTX导出       → presentation.pptx
```

**Agent 1-4**: Claude executes reasoning, structure, and React component generation.
**Agent 5-7**: Python scripts handle asset fetching, Playwright extraction, and PPTX assembly.

### Data Flow

Each deck gets an isolated workspace under `output/projects/<project-id>/`. Each agent reads from the previous checkpoint file in that workspace and writes the next checkpoint. If an output file already exists and is non-empty, that step can be skipped. Delete a checkpoint to force re-run.

### Project Workspace

Created by `tools/presentation_workspace.py`.

```
output/projects/<project-id>/
├── project.json
├── article_text.md
├── analysis.json
├── outline.json
├── slides.json
├── slides_with_images.json
├── layout_manifest.json
├── presentation.pptx
├── assets/
└── slides/
```

`output/projects/<project-id>/slides/` is the durable source of truth for generated deck React code. `web/src/slides/` is the active Vite renderer slot. Use `tools/ppt_workflow.py snapshot-slides` to persist generated source and `tools/ppt_workflow.py activate` to load a project into the renderer slot.

### Responsibility Boundaries

| Agent | Tool | Input | Output | Responsibility |
|-------|------|-------|--------|----------------|
| 0 | Python | deck title | project.json + dirs | Create isolated workspace |
| 1 | Claude/Python | URL/text/PDF | article_text.md | Extract clean article text |
| 2 | Claude | article_text.md | analysis.json | Domain, key points, statistics, quotes |
| 3 | Claude | analysis.json | outline.json | Slide count, style preset, slide plan |
| 4 | Claude/React | outline.json + analysis.json | web/src/slides/* | Visual slide implementation |
| 5 | Python | slides.json | slides_with_images.json | Resolve images via 5-level fallback |
| 6 | Python/Playwright | React app | layout_manifest.json + assets/ | Extract backgrounds/components/text boxes |
| 7 | Python | layout_manifest.json | presentation.pptx | Stitch PPTX from images + native text |

### Unified CLI

`tools/ppt_workflow.py` is the main operator entry point:

```bash
python tools/ppt_workflow.py init --name "Deck Name"
python tools/ppt_workflow.py snapshot-slides --project <project-id>
python tools/ppt_workflow.py activate --project <project-id>
python tools/ppt_workflow.py validate --project <project-id>
python tools/ppt_workflow.py extract --project <project-id>
python tools/ppt_workflow.py export --project <project-id>
python tools/ppt_workflow.py build --project <project-id>
```

`build` activates project slides, validates source markers, extracts layout/assets, exports PPTX, then validates final outputs.

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

## 4. Image Strategy (8-Level Fallback)

### Priority Principle

**Agent generates first, external APIs second.** The agent itself is an SVG generator — it produces `diagram_nodes`/`diagram_edges` or inline `svg_code`, and Python tools render professional SVG. External APIs (Pexels, Pixabay, Unsplash) are fallbacks for photo-type content only.

### Level Decision Matrix

| Slide Content | Recommended Strategy | fallback_chain | Why |
|---------------|---------------------|----------------|-----|
| Flow / process / architecture | **diagram** (Agent-generated nodes) | ["diagram", "svg", "icon"] | Agent designs layout, Python renders SVG |
| Comparison / relationships | **diagram** | ["diagram", "svg"] | Node graph > text for relationships |
| Data / statistics trend | **svg** (Agent-generated inline) | ["svg", "icon"] | Simple trend lines, bars |
| Charts | canvas (Chart.js) | ["canvas", "diagram"] | Interactive Chart.js charts |
| Decorative / card icons | icon (Lucide CDN) | ["icon", "svg"] | Simple icon decoration |
| Scene / atmosphere photos | **pexels** → pixabay → unsplash | ["pexels", "pixabay", "unsplash"] | Pexels: 200/hr, no attribution; Pixabay: 100/min; Unsplash: 50/hr, needs attribution |
| Quote illustration | pexels → pixabay → unsplash | ["pexels", "pixabay", "unsplash", "icon"] | Mood photo for quote slides |
| Custom brand (last resort) | AI (DALL-E 3) | ["ai"] | ~$0.04/image, only when all else fails |

### Level Details

**Level 0 — Claude AI SVG Generation**
- Agent calls Anthropic API (if key available) to generate creative aurora-borealis SVG diagrams
- System prompt includes full design system (colors, typography, z-order rules)
- Fallback for when diagram_nodes aren't provided but creative SVG is needed
- Cost: ~$0.01/request

**Level 1 — Diagram (Agent-generated, no API)**
- Agent provides `diagram_nodes` + `diagram_edges` in image_request
- Python `_generate_diagram_svg()` renders: grid bg → edges → opaque mask → node rect → text
- 6 semantic node types: primary, accent, cyan, success, warning, muted
- Cost: free

**Level 2 — SVG Inline**
- Agent generates SVG during Agent 4, embedded in `image_request.svg_code`
- Python orchestrator injects CSS variables (replaces hardcoded hex colors)
- viewBox="0 0 400 240", use only polyline/rect/circle/path
- Cost: free

**Level 3 — HTML Canvas / Chart.js**
- For chart slides where chart_data is available
- Rendered as inline HTML+JS, Playwright captures it for PPTX layer
- Cost: free

**Level 4 — Icon CDN (Lucide)**
- `icon_name` maps to `https://cdn.jsdelivr.net/npm/lucide-static@latest/icons/{name}.svg`
- Emoji fallback if CDN unreachable
- Cost: free

**Level 5a — Pexels Image Search**
- Requires `pexels` key in `.env.json`
- `search_query` or `description` as search terms
- Returns `src.landscape` (1200×627, perfect for slide backgrounds)
- No attribution required
- Rate limit: 200 req/hour, 20,000 req/month
- Cost: free

**Level 5b — Pixabay Image Search**
- Requires `pixabay` key in `.env.json`
- Searches with `orientation=horizontal`, `min_width=1280`
- **Must download to cache** (hotlinking not allowed by Pixabay ToS)
- No attribution required
- Rate limit: 100 req/60sec, must cache 24 hours
- Cost: free

**Level 5c — Unsplash Image Search**
- Requires `unsplash` key in `.env.json`
- `search_query` or `description` as search terms
- Returns `urls.regular` image URL
- **Attribution required**: "Photo by [Name] on Unsplash"
- Rate limit: 50 req/hour (demo), 5,000 req/hour (production approval)
- Cost: free tier

**Level 6 — AI Generation (DALL-E 3)**
- Requires `openai` key in `.env.json`
- `ai_prompt` appended with `image_style_fingerprint` from style_constraints
- Size: 1792×1024 (wide format)
- Cost: ~$0.04/image

### Cache

Images cached by MD5 key (chain + content descriptor) in `image_cache/`. Cache is gitignored. Delete to force fresh fetch.

---

## 5. Style System

### React Style Preset Registry

The active React renderer uses `web/src/styles/presets.ts` as the source of reusable deck styles. This registry is meant for both code and AI instructions: it includes design tokens, layout rules, component recipes, and things to avoid.
The companion guide is `web/src/styles/STYLE_GUIDE.md`.

Current presets:

| Preset | Style | Primary Use |
|--------|-------|-------------|
| aurora-borealis | Dark technical, cyan-purple light, glass panels | technology/AI/cybersecurity |
| bold-signal | High contrast black/orange business deck | startup/business/finance |
| editorial-ink | Light editorial, print hierarchy, restrained red accent | education/culture/content |

React slide components should call:

```tsx
import { getDeckStylePreset, styleVars } from '../styles'

const preset = getDeckStylePreset('aurora-borealis')

<div style={styleVars(preset)} className="bg-[var(--ppt-bg)] text-[var(--ppt-text)]">
```

Primary CSS variables exposed by `styleVars()`:

- `--ppt-bg`
- `--ppt-surface`
- `--ppt-surface-strong`
- `--ppt-primary`
- `--ppt-secondary`
- `--ppt-accent`
- `--ppt-text`
- `--ppt-muted`
- `--ppt-border`
- `--ppt-font-display`
- `--ppt-font-body`

Each preset also exposes `slidePatterns`, which are named layout archetypes. Agents should pick a slide pattern before writing JSX so repeated deck types converge on proven structures instead of improvising every page.

### Legacy CSS Themes

`themes/_base.css` and `themes/*.css` are retained for the older HTML renderer and for reference. They are no longer the primary visual mechanism for the React pipeline.

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

### Adding a New Style Preset

1. Add a new entry to `web/src/styles/presets.ts`.
2. Include tokens, layout rules, component recipes, and avoid-list.
3. Add the id to `DeckStyleId`.
4. Add the style to SKILL.md Agent 4 style preset guidance.
5. Run `npm run build`.

---

## 6. Hybrid PPTX Architecture

### Quality Gates

`tools/quality_gate.py` validates:

- project workspace and slide source directory exist
- `index.ts` exists in the project slide source directory
- every `Slide_*.tsx` has `data-ppt-slide`
- the deck has at least one `data-ppt-text`
- slide code uses style presets or `--ppt-*` variables
- manifest-referenced assets exist
- `presentation.pptx` is not empty when present

### Manifest-Based Approach

`tools/builder.py` opens the React renderer at `?extract=1`, then extracts three kinds of objects:

- full-slide background PNG after hiding `data-ppt-text`
- component PNGs for each `data-ppt-bg`
- native text boxes for each `data-ppt-text`

It writes `layout_manifest.json`. `tools/pptx_exporter.py` consumes that manifest and creates PPTX slides by adding:

1. full-slide background image
2. component image overlays
3. editable native text boxes

Run:

```bash
python tools/ppt_workflow.py build --project <project-id>
```

---

## 7. Adding New Slide Types

1. Add the type string to `schemas/outline.schema.json` → `slides.items.properties.type.enum`
2. Add content guidance to SKILL.md Agent 4 so the AI knows when to choose the type.
3. Add or update React component examples in `web/src/slides/` using `web/src/styles/presets.ts`.
4. If the type needs a reusable visual primitive, add it near the React renderer rather than embedding the same structure in every generated slide.
5. Run `npm run build` and a manifest export smoke test.

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
│   ├── html_renderer.py          # Legacy JSON → HTML presentation renderer
│   ├── presentation_workspace.py # Project directory management
│   ├── deck_sources.py           # Copy project slides to/from active renderer slot
│   ├── quality_gate.py           # Structural validation before/after export
│   ├── ppt_workflow.py           # Unified workflow CLI
│   ├── builder.py                # React → layout manifest extraction
│   └── pptx_exporter.py          # Manifest → Hybrid PPTX
├── web/
│   ├── src/slides/               # Active generated React slide components
│   └── src/styles/               # Reusable style preset registry and guide
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
└── output/projects/              # Runtime deck workspaces (gitignored)
```
