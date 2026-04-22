---
name: article-to-ppt
description: Use when the user wants to convert an article, URL, or document into a presentation. Triggers on phrases like "做成PPT", "转成幻灯片", "制作演示文稿", "make a presentation from", "convert to slides". Supports URL, plain text, and PDF file paths as input.
---

# Article → PPT Skill

将文章（URL / 文本 / PDF）转换为专业演示文稿（React 预览 + Hybrid PPTX）。

## 入参

```
/ppt <input> [--theme <theme>] [--slides <n>] [--lang <zh|en>]
```

- `<input>`：URL、文本内容、或本地文件路径（PDF / .txt / .md）
- `--theme`：可选，指定主题（aurora-borealis | bold-signal | editorial-ink）
- `--slides`：可选，目标幻灯片数量（8-25，默认自动决定）
- `--lang`：可选，输出语言（默认 zh）

## 项目工作区与断点续跑

每次生成 PPT 前，先建立独立项目目录，避免多个 PPT 互相覆盖：

```bash
python3 tools/ppt_workflow.py init --name "演示文稿标题"
```

默认目录结构：

```
output/projects/<project-id>/
├── project.json
├── article_text.md
├── analysis.json
├── design_dna.json          ← 视觉 DNA（Agent 2.5 生成）
├── outline.json
├── slides.json
├── slides_with_images.json
├── layout_manifest.json
├── presentation.pptx
├── assets/
└── slides/
```

`output/projects/<project-id>/slides/` 是该 deck 的 React 源码产物目录，位于 `output/` 下，默认被 Git 忽略。`web/src/generated/slides/` 是当前 Vite 渲染槽，同样被 Git 忽略。仓库只提交工具代码、风格库和 `web/src/sample-slides/` 示例。

每步开始前检查 `output/projects/<project-id>/` 是否已有对应文件。如果存在且非空，跳过该步骤：

```
article_text.md         → 跳过 Agent 1
analysis.json           → 跳过 Agent 2
design_dna.json         → 跳过 Agent 2.5
outline.json            → 跳过 Agent 3
slides.json             → 跳过 Agent 4 内容结构
slides_with_images.json → 跳过 Agent 5 图片编排
layout_manifest.json    → 跳过 Agent 6 React 抽取
presentation.pptx       → 跳过 Agent 7
```

强制重跑某步：删除对应文件后重新运行。

常用命令：

```bash
# 如果临时在渲染槽里改过源码，将 web/src/generated/slides/ 保存回项目工作区
python3 tools/ppt_workflow.py snapshot-slides --project <project-id>

# 激活某个项目的 slides 到 web/src/generated/slides/
python3 tools/ppt_workflow.py activate --project <project-id>

# 校验项目结构、data-ppt-* 标记、manifest 资产和 PPTX
python3 tools/ppt_workflow.py validate --project <project-id>

# 激活 slides → Playwright 抽取 → PPTX 导出 → 输出校验
python3 tools/ppt_workflow.py build --project <project-id>
```

---

## Agent 1 · 文章提取

**目标**：获取文章纯文本，保存到 `output/projects/<project-id>/article_text.md`

**判断输入类型**：

- 以 `http://` 或 `https://` 开头 → URL
- 以 `.pdf` 结尾或文件存在且为 PDF → PDF
- 否则 → 直接使用文本

**URL 输入**：使用 WebFetch 工具获取页面内容，提取正文（忽略导航、广告、页脚）

**PDF 输入**：调用 Python 工具：

```bash
python3 tools/ingest.py pdf "<path>" | python3 -c "import sys,json; print(json.load(sys.stdin)['text'])" > output/projects/<project-id>/article_text.md
```

**文本输入**：直接写入 `output/projects/<project-id>/article_text.md`

**验证**：`output/projects/<project-id>/article_text.md` 字符数 > 200，否则报错提示用户检查输入。

---

## Agent 2 · 内容分析

**目标**：深度分析文章，输出 `output/projects/<project-id>/analysis.json`（必须符合 `schemas/analysis.schema.json`）

阅读 `output/projects/<project-id>/article_text.md`，执行以下分析并输出 JSON：

```json
{
  "domain": "从[technology|finance|healthcare|startup|education|business|cybersecurity|sustainability|gaming|culture|other]中选择最匹配的领域",
  "title": "提炼最能概括文章的标题（非原文标题的直接复制）",
  "summary": "2-3句话总结文章核心观点",
  "key_points": ["提取 6-10 个核心论点，每条15字以内"],
  "statistics": [
    {
      "value": "具体数字/百分比",
      "label": "指标名称",
      "context": "可选补充说明"
    }
  ],
  "quotes": [{ "text": "原文引用", "author": "作者姓名", "role": "职位/背景" }],
  "entities": ["涉及的重要公司/人物/技术名词"],
  "complexity": "simple|intermediate|expert（根据技术深度判断）",
  "suggested_theme": "根据domain自动映射（见下方映射表）",
  "language": "文章主要语言，zh或en",
  "tone": "从[authoritative|inspiring|analytical|narrative|urgent|educational]中选最匹配的基调"
}
```

**Domain → Theme 映射**：

- technology / AI → aurora-borealis
- finance → bold-signal
- healthcare → editorial-ink
- startup → bold-signal
- education → editorial-ink
- business → bold-signal
- cybersecurity → aurora-borealis
- gaming / entertainment → aurora-borealis
- sustainability / culture → editorial-ink
- 其他 → aurora-borealis

**规则**：

- statistics 最多提取5条，必须是文章中的真实数据，不得编造
- quotes 最多提取3条，必须是原文引用，不得改写
- 如果用户通过 `--theme` 参数指定了主题，覆盖 `suggested_theme`

**⚠️ JSON 安全写入规则（必读，违反导致解析炸裂）**：

JSON 字符串内部**严禁**出现以下字符，它们会被 JSON 解析器误判为字符串定界符：
- 中文弯引号：`"` `"` `'` `'`（看起来像引号但不是 ASCII `"`）
- 全角引号：`＂` `＇`

如需在 JSON 字符串中表达引用语气，直接删去引号，或改用书名号 `《》`、方括号 `【】`。

写完 JSON 后运行此检查，发现错误立即修正再继续：

```bash
python3 -c "
import json, sys
try:
    json.load(open('output/projects/<project-id>/analysis.json'))
    print('✓ JSON 格式正确')
except json.JSONDecodeError as e:
    print(f'✗ JSON 解析错误 pos={e.pos}: {e.msg}')
    sys.exit(1)
"
```

**验证 schema**：

```bash
python3 -c "
import json, jsonschema
data = json.load(open('output/projects/<project-id>/analysis.json'))
schema = json.load(open('schemas/analysis.schema.json'))
jsonschema.validate(data, schema)
print('✓ analysis.json 验证通过')
"
```

---

## Agent 2.5 · 动态设计系统生成（Design DNA）

**目标**：根据文章领域、基调和受众，生成整套 PPT 视觉 DNA，输出 `output/projects/<project-id>/design_dna.json`。
这是后续所有幻灯片视觉决策的**唯一宪法**，Agent 3、4 均须严格遵守。

读取 `output/projects/<project-id>/analysis.json`，执行以下步骤：

### Step 1：优先调用 ui-ux-pro-max Skill（主路径，无限制主题）

**⚠️ 这是主路径。只有 Skill 工具完全不可用时，才降级到 Step 2。**

使用 Skill 工具调用 `ui-ux-pro-max`，查询词为：

```
<domain> <tone> <complexity> presentation slide deck visual design system
```

例如：`"technology authoritative expert presentation slide deck visual design system"`

**Skill 输出即是视觉决策的唯一来源**。不要把输出再映射回 3 套内置主题——直接从 Skill 的推荐中自由构建 `design_dna.json`，包括但不限于：

| 提取目标 | 从 Skill 输出中读取 | 写入字段 |
|---------|-----------------|---------|
| 整体视觉语言（深色/浅色/哑光/极简/奢华/暗黑赛博…） | 风格描述关键词 | `visual_language.*` |
| 背景色系 | 色板推荐 | `token_extensions["--ppt-bg-*"]` |
| 主色 / 强调色 | 色板推荐 | `token_extensions["--ppt-chart-1..5"]` |
| 标题字体 / 正文字体 | 排版推荐 | `font_display` / `font_body` |
| 卡片风格（毛玻璃/硬边框/纸质/霓虹…） | 组件风格描述 | `visual_language.card_recipe` |
| 装饰元素 | 视觉语言描述 | `visual_language.bg_decoration` |
| 图片情绪关键词 | 情绪/氛围词 | `visual_language.image_mood` |

**preset 字段**仅用于选择底层 CSS 脚手架（决定基础变量可用性）。按以下最简规则选一个最接近的：
- Skill 推荐深色背景 → `aurora-borealis`
- Skill 推荐深色背景 + 无光效/纯商务 → `bold-signal`
- Skill 推荐浅色/暖白背景 → `editorial-ink`

`preset` 只是 CSS 脚手架，所有实际颜色、字体、视觉语言**必须完全由 Skill 输出决定**，不得受 preset 默认值约束。

若用户通过 `--theme` 指定了主题，仍调用 `ui-ux-pro-max` 获取该主题的完整视觉系统推荐，再填充 `design_dna.json`。

---

### Step 2：降级兜底（仅 Skill 完全不可用时使用）

根据 `analysis.json` 的 `domain`、`tone`，选一个内置 preset 并直接套用对应的默认模板：

| Domain | Tone | 使用模板 |
|--------|------|---------|
| technology / AI / cybersecurity / gaming | any | Aurora Borealis 默认模板 |
| finance / startup / business | any | Bold Signal 默认模板 |
| healthcare / education / culture / sustainability | any | Editorial Ink 默认模板 |
| other | any | Aurora Borealis 默认模板 |

**Aurora Borealis 默认模板**：
```json
{
  "preset": "aurora-borealis",
  "font_display": "Space Grotesk, Inter, ui-sans-serif, system-ui",
  "font_body": "Inter, ui-sans-serif, system-ui, sans-serif",
  "token_extensions": {
    "--ppt-glow-a": "rgba(139,92,246,0.40)",
    "--ppt-glow-b": "rgba(34,211,238,0.28)",
    "--ppt-highlight": "#F472B6",
    "--ppt-chart-1": "#8B5CF6",
    "--ppt-chart-2": "#22D3EE",
    "--ppt-chart-3": "#F472B6",
    "--ppt-chart-4": "#34D399",
    "--ppt-chart-5": "#FB923C",
    "--ppt-gradient-heading": "linear-gradient(135deg, #C4B5FD 0%, #67E8F9 100%)"
  },
  "visual_language": {
    "card_recipe": "bg-white/5 backdrop-blur-2xl border border-white/10 rounded-3xl shadow-[0_0_80px_-24px_var(--ppt-primary)]",
    "heading_recipe": "text-transparent bg-clip-text bg-gradient-to-br from-purple-300 to-cyan-300 font-black",
    "accent_bar_recipe": "w-1 bg-gradient-to-b from-[var(--ppt-primary)] to-[var(--ppt-secondary)] rounded-full",
    "bg_decoration": "two radial-gradient orbs: purple top-left 600px + cyan bottom-right 500px, blur-[140px] opacity-30",
    "image_mood": ["cinematic lighting", "deep purple", "cyan accent", "dark atmosphere", "photorealistic"]
  },
  "slide_pattern_assignments": {
    "title": "aurora-title-glass",
    "agenda": "aurora-metric-bento",
    "section-divider": "aurora-title-glass",
    "bullet-list": "aurora-system-map",
    "two-column": "aurora-metric-bento",
    "stats-callout": "aurora-metric-bento",
    "quote-callout": "aurora-title-glass",
    "timeline": "aurora-system-map",
    "conclusion": "aurora-title-glass"
  },
  "consistency_rules": [
    "严禁在组件内硬编码任何颜色十六进制值，全部使用 var(--ppt-*) 变量",
    "所有卡片必须使用 card_recipe，不得自创背景方案",
    "标题全部使用 heading_recipe 渐变风格，不得使用纯色标题",
    "背景始终为 var(--ppt-bg)，可叠加 bg_decoration 描述的装饰光晕",
    "字体显示元素绑定 font_display，正文绑定 font_body"
  ],
  "visual_mandates": {
    "min_ppt_bg_blocks_per_slide": 1,
    "stats_slides_require": "inline SVG chart or Chart.js canvas visualization",
    "concept_slides_require": "diagram nodes OR decorative SVG pattern OR icon grid",
    "quote_slides_require": "atmospheric background image or large decorative quotation mark",
    "image_coverage_min": 0.4
  }
}
```

**Bold Signal 默认模板**：
```json
{
  "preset": "bold-signal",
  "font_display": "Plus Jakarta Sans, DM Sans, Inter, ui-sans-serif",
  "font_body": "Inter, ui-sans-serif, system-ui, sans-serif",
  "token_extensions": {
    "--ppt-rail": "#F97316",
    "--ppt-number": "#FBBF24",
    "--ppt-chart-1": "#F97316",
    "--ppt-chart-2": "#FBBF24",
    "--ppt-chart-3": "#FFFFFF",
    "--ppt-chart-4": "#6B7280",
    "--ppt-chart-5": "#EF4444",
    "--ppt-gradient-heading": "linear-gradient(90deg, #FFFFFF 0%, #F97316 100%)"
  },
  "visual_language": {
    "card_recipe": "bg-[#1D1D1D] border border-[#404040] rounded-2xl",
    "heading_recipe": "text-white font-black tracking-tight",
    "accent_bar_recipe": "w-1.5 bg-[var(--ppt-rail)] rounded-sm",
    "bg_decoration": "solid dark #111111 base, optional subtle grid overlay opacity-5",
    "image_mood": ["business", "corporate", "dramatic lighting", "dark background", "editorial"]
  },
  "slide_pattern_assignments": {
    "title": "signal-exec-brief",
    "agenda": "signal-market-snapshot",
    "section-divider": "signal-exec-brief",
    "bullet-list": "signal-exec-brief",
    "two-column": "signal-decision-matrix",
    "stats-callout": "signal-market-snapshot",
    "quote-callout": "signal-exec-brief",
    "timeline": "signal-decision-matrix",
    "conclusion": "signal-exec-brief"
  },
  "consistency_rules": [
    "严禁任何 glassmorphism、毛玻璃或 backdrop-blur 效果",
    "所有卡片硬边框，不使用 blur 或透明背景",
    "左侧 accent bar 是版式标志，所有内容幻灯片必须使用",
    "数字颜色全部使用 var(--ppt-rail) 或 var(--ppt-number)",
    "字体全部使用 font_display，不使用衬线字体"
  ],
  "visual_mandates": {
    "min_ppt_bg_blocks_per_slide": 1,
    "stats_slides_require": "horizontal bar chart SVG or metric tiles grid",
    "concept_slides_require": "numbered list panels or comparison matrix",
    "quote_slides_require": "large number callout or bold statement panel",
    "image_coverage_min": 0.3
  }
}
```

**Editorial Ink 默认模板**：
```json
{
  "preset": "editorial-ink",
  "font_display": "Playfair Display, Georgia, ui-serif, serif",
  "font_body": "Inter, ui-sans-serif, system-ui, sans-serif",
  "token_extensions": {
    "--ppt-rule": "#B91C1C",
    "--ppt-warm": "#D97706",
    "--ppt-chart-1": "#B91C1C",
    "--ppt-chart-2": "#1F2937",
    "--ppt-chart-3": "#D97706",
    "--ppt-chart-4": "#059669",
    "--ppt-chart-5": "#7C3AED",
    "--ppt-gradient-heading": "none"
  },
  "visual_language": {
    "card_recipe": "bg-white border border-[#D6D3D1] rounded-xl shadow-sm",
    "heading_recipe": "text-[#1C1917] font-black",
    "accent_bar_recipe": "w-0.5 bg-[var(--ppt-rule)]",
    "bg_decoration": "warm off-white #F8F5F0 base, optional thin rule lines",
    "image_mood": ["editorial photography", "natural light", "documentary", "warm tones", "high contrast BW"]
  },
  "slide_pattern_assignments": {
    "title": "ink-feature-story",
    "agenda": "ink-two-column-brief",
    "section-divider": "ink-feature-story",
    "bullet-list": "ink-two-column-brief",
    "two-column": "ink-two-column-brief",
    "stats-callout": "ink-two-column-brief",
    "quote-callout": "ink-pull-quote",
    "timeline": "ink-two-column-brief",
    "conclusion": "ink-feature-story"
  },
  "consistency_rules": [
    "严禁使用 neon、glow、glassmorphism 任何深色特效",
    "背景保持暖白，不使用深色背景",
    "标题使用衬线字体（font_display），正文无衬线（font_body）",
    "装饰元素只用细线条（border / rule），不用阴影块",
    "颜色克制，全局最多使用3种颜色（primary + secondary + accent）"
  ],
  "visual_mandates": {
    "min_ppt_bg_blocks_per_slide": 1,
    "stats_slides_require": "clean table or minimal bar chart",
    "concept_slides_require": "typographic layout or rule-divided columns",
    "quote_slides_require": "vertical rule + oversized serif quotation",
    "image_coverage_min": 0.35
  }
}
```

---

### Step 3：生成 design_dna.json

**验证**：确认 `design_dna.json` 包含所有必填字段 `preset`, `token_extensions`, `slide_pattern_assignments`, `consistency_rules`, `visual_mandates`。

---

## Agent 3 · 幻灯片规划

**目标**：制定幻灯片大纲，输出 `output/projects/<project-id>/outline.json`（必须符合 `schemas/outline.schema.json`）

读取 `output/projects/<project-id>/analysis.json` 和 `output/projects/<project-id>/design_dna.json`，按以下规则规划幻灯片：

**数量规则**：

- 默认：min(max(key_points数量 × 2, 10), 20) 张
- 如果用户指定 `--slides N`：使用该数量（8-25范围内）

**必须包含的幻灯片类型**（按顺序）：

1. `title`（第1张，必须）
2. `agenda`（第2张，若总数≥12）
3. 内容幻灯片（类型按内容决定，见下方规则）
4. `conclusion`（最后1张，必须）

**内容幻灯片选择规则**：

- 有≥3条统计数据 → 安排1张 `stats-callout`
- 有时间线叙述 → 安排1张 `timeline`
- 有引用 → 安排1张 `quote-callout`
- 每个核心论点通常对应1张 `bullet-list` 或 `two-column`
- 每3-4张内容幻灯片插入1张 `section-divider`
- 不连续使用同一类型（多样化布局）
- 40%的幻灯片应有图片（`needs_image: true`）

**为每张幻灯片指定 pattern_id**：从 `design_dna.json` 的 `slide_pattern_assignments` 中，根据幻灯片类型查出 `pattern_id`，写入 outline 的每个 slide 对象。

**输出格式与全局设计**：
严格按照 `schemas/outline.schema.json` 输出。整体必须透传选定的 `theme` 并固定 `style_constraints`，同时每个 `slide` 对象包含 `index`, `type`, `title`, `needs_image`, `pattern_id` 等核心字段。

```json
{
  "theme": "直接透传 design_dna.json 的 preset 字段",
  "style_constraints": {
    "heading_emphasis": "gradient（深色主题）或 solid（浅色主题/editorial-ink）",
    "card_style": "glass（深色主题）或 outlined（浅色主题）",
    "stat_style": "gradient-text（深色）或 accent-color（浅色）",
    "bullet_style": "dot",
    "divider_style": "gradient-line",
    "image_style_fingerprint": "直接透传 design_dna.json 的 visual_language.image_mood 数组"
  },
  "slides": [
    {
      "index": 1,
      "type": "title",
      "title": "...",
      "needs_image": false,
      "pattern_id": "aurora-title-glass"
    }
  ]
}
```

**schema 枚举约束**（违反会导致 jsonschema 报错）：

| 字段 | 合法值（仅限这几个） |
|------|-------------------|
| `divider_style` | `gradient-line` · `dot-separator` · `none` |
| `bullet_style` | `dot` · `dash` · `none` |
| `card_style` | `glass` · `outlined` · `filled` |
| `stat_style` | `gradient-text` · `accent-color` · `plain` |
| `heading_emphasis` | `gradient` · `solid` · `outline` |

**验证**：

```bash
python3 -c "
import json, jsonschema
data = json.load(open('output/projects/<project-id>/outline.json'))
schema = json.load(open('schemas/outline.schema.json'))
jsonschema.validate(data, schema)
print(f'✓ outline.json 验证通过，共 {len(data[\"slides\"])} 张幻灯片')
"
```

---

## Agent 4 · React 组件级构建（Code-Driven）

**目标**：大模型充当高级前端工程师，严格遵循 Design DNA，为每张幻灯片编写视觉惊艳、风格统一的 React 组件，存入 `output/projects/<project-id>/slides/`。

---

### ⚠️ 核心原则：这是给观众看的演示，不是个人阅读文档

**PPT 的本质是视觉冲击 + 信息传递**。观众在3秒内决定是否关注这张幻灯片。平庸的"标题+列表"结构是失败品，会被观众无视。

---

### 强制性视觉质量门槛（违反即返工）

#### 门槛一：每张幻灯片必须有**至少一个视觉锚点**

视觉锚点是能抓住观众注意力的元素，**必须存在且足够醒目**：

| 视觉锚点类型 | 尺寸要求 | 适用幻灯片 |
|-------------|---------|-----------|
| **超大数字** | 字号 ≥ 120px，占屏幕 1/4 以上 | stats-callout, 有数据的幻灯片 |
| **SVG 图表** | 占屏幕 1/3 以上，有渐变/阴影/动画感 | stats-callout, 对比类 |
| **大图标网格** | 3-6个图标，每个 ≥ 80px | bullet-list, 概念类 |
| **强对比色块** | 占屏幕 1/4，与背景形成明显对比 | section-divider, emphasis |
| **装饰性 SVG 图案** | 覆盖屏幕 20%以上，有动态感 | 所有类型 |
| **真实图片** | 占屏幕 40%以上，高质量摄影 | two-column, quote-callout |

**检查方法**：写完每张幻灯片后，问自己："观众3秒内能被什么抓住？"如果答案是"文字"，则不合格。

#### 门槛二：禁止平庸布局

以下布局**严格禁止**，因为它们无法产生视觉冲击：

| 禁止布局 | 问题 | 替代方案 |
|---------|------|---------|
| 标题 + 简单 bullet list | 无视觉锚点，观众秒走 | Bento 网格 + 大图标 + 装饰 SVG |
| 标题 + 左右两栏纯文字 | 平淡无奇 | 斜切分割 + 大数字 + 图表 |
| 标题 + 单个卡片 | 信息密度过低 | 多卡片叠加 + 悬浮重叠 |
| 纯文字引用 | 无视觉锚点 | 大号装饰引号 SVG + 背景氛围图 |
| 标题 + 图片占位框 | 视觉空洞 | 真实图片 + 装饰层叠加 |

#### 门槛三：现代排版技法强制使用

每张幻灯片**至少使用 2 种**以下技法：

1. **Bento 便当格布局**：不规则网格，大小不一的卡片组合，产生视觉节奏
2. **大数字 Callout**：关键数字放大到 120-200px，形成视觉焦点
3. **悬浮重叠**：卡片或元素部分重叠，产生深度感
4. **斜切分割**：用斜线/三角形分割画面，打破方正感
5. **渐变文字/渐变填充**：标题或关键元素使用渐变，增加视觉丰富度
6. **装饰性 SVG 图案**：背景或边角加入动态感的 SVG 装饰
7. **图标网格**：用统一风格的图标（Lucide/Heroicons）替代 bullet points
8. **强对比色块**：在平淡区域插入强对比色块，打破单调

---

### 启动前必读

**第一步**：读取 `output/projects/<project-id>/design_dna.json`，将以下内容提取到工作记忆：

- `preset`：基础预设名
- `font_display` / `font_body`：全局字体
- `token_extensions`：扩展 CSS 变量（写入每个组件的 style prop 中）
- `visual_language.card_recipe`：卡片 Tailwind 类（全局锁定）
- `visual_language.heading_recipe`：标题样式（全局锁定）
- `visual_language.accent_bar_recipe`：强调条样式
- `visual_language.bg_decoration`：背景装饰描述
- `consistency_rules`：5条禁令，违反即返工
- `visual_mandates`：每张幻灯片的视觉最低要求

**第二步**：读取 `outline.json`，为每张幻灯片预先确认 `pattern_id`。按 index 顺序编写，不得跳过。

**第三步（新增）**：为每张幻灯片在编写前回答：
- 这张幻灯片的**视觉锚点**是什么？（大数字/图表/图标网格/强对比色块）
- 使用了**至少 2 种现代排版技法**吗？
- 是否遵守了**禁止平庸布局**规则？

---

### ⚠️ 技术规范（违反会导致渲染失败）

#### 规范一：Import 路径（必须正确）

```tsx
// ✅ 正确：使用相对路径 '../../styles'
import { getDeckStylePreset, styleVars } from '../../styles'

// ❌ 错误：不要使用绝对路径或错误的相对路径
import { getDeckStylePreset, styleVars } from '../../web/src/styles'  // 错误！
import { getDeckStylePreset, styleVars } from '../../../web/src/styles'  // 错误！
```

**原因**：组件在 `web/src/generated/slides/` 目录下渲染，styles 位于 `web/src/styles/`，相对路径是 `../../styles`。

#### 规范二：SVG 多元素必须用 Fragment 包裹

当在 SVG 内使用条件渲染返回多个元素时，必须用 `<></>` 或 `<g>` 包裹：

```tsx
// ✅ 正确：多元素用 Fragment 包裹
{icon === 'brain' && (
  <>
    <circle cx="28" cy="28" r="16" stroke="#18181B" strokeWidth="3" />
    <path d="M28 8C18 8 10 16..." stroke="#18181B" strokeWidth="2" />
  </>
)}

// ✅ 正确：SVG 内也可用 <g> 包裹
{icon === 'connect' && (
  <g>
    <circle cx="16" cy="28" r="8" stroke="#059669" strokeWidth="3" />
    <circle cx="40" cy="28" r="8" stroke="#059669" strokeWidth="3" />
    <line x1="24" y1="28" x2="32" y2="28" stroke="#059669" />
  </g>
)}

// ❌ 错误：多元素直接返回会导致 JSX 解析错误
{icon === 'brain' && (
  <circle cx="28" cy="28" r="16" />  // 错误！缺少包裹
  <path d="M28 8..." />              // 错误！不能返回多个元素
)}
```

#### 规范三：CSS 变量使用统一命名

```tsx
// ✅ 正确：使用 --ppt-* 命名
const extendedTokens = {
  '--ppt-rule': '#18181B',
  '--ppt-warm': '#EC4899',
  '--ppt-bg-warm': '#F8F5F0',
}

// ❌ 错误：不要使用 --color-* 命名（与系统变量冲突）
const extendedTokens = {
  '--color-primary': '#18181B',  // 错误！
}
```

---

### 组件模板结构

每个组件必须按此结构开始：

```tsx
import { getDeckStylePreset, styleVars } from '../../styles'
import type { CSSProperties } from 'react'

const extendedTokens: CSSProperties = {
  '--ppt-rule': '#18181B',
  '--ppt-warm': '#EC4899',
  '--ppt-bg-warm': '#F8F5F0',
  '--ppt-text-dark': '#09090B',
  '--ppt-chart-1': '#18181B',
  '--ppt-chart-2': '#EC4899',
  '--ppt-chart-3': '#7C3AED',
  '--ppt-chart-4': '#059669',
  '--ppt-chart-5': '#D97706',
}

export default function Slide_N() {
  const preset = getDeckStylePreset('PRESET_ID')
  const baseVars = styleVars(preset)

  return (
    <div
      className="w-[1920px] h-[1080px] bg-[var(--ppt-bg-warm)] relative overflow-hidden"
      style={{ ...baseVars, ...extendedTokens } as CSSProperties}
      data-ppt-slide={N}
    >
      {/* 视觉锚点层 */}
      {/* 内容层 */}
    </div>
  )
}
```

### 编程规范

1. **风格一致性（最高优先级）**：每次写新组件前，朗读 `consistency_rules` 的 5 条禁令。如发现违反，立即修正。
2. **视觉强制要求**：`visual_mandates` 不是建议，是最低标准。每张幻灯片写完后对照检查：
   - `stats_slides_require`：stats-callout 和含数字的 bullet-list，必须有**醒目的 SVG 图表**（带渐变/阴影）
   - `concept_slides_require`：concept/process 类，必须有**图标网格**或**装饰 SVG 图案**
   - `quote_slides_require`：quote-callout 类，必须有**大号装饰引号 SVG**或**背景氛围图**
3. **观众视角设计**：考虑演讲时观众的注意力引导——关键信息必须有视觉强调（大字号、强对比色、渐变效果）
4. **严禁硬编码颜色**：所有颜色使用 `var(--ppt-*)` 或 `var(--ppt-chart-*)` 变量，这些变量通过 `extendedTokens` 注入。

### 执行流程优化（丝滑执行）

**⚠️ 不要使用 background tasks 编写组件！**

原因：
- React 组件编写需要严格遵循设计DNA，background subagent容易产生不一致的import路径
- 组件之间需要保持风格统一，串行生成更容易保证一致性
- Background tasks 超时会导致反复等待

**正确做法**：在同一 session 中按顺序编写所有组件：

```
1. 读取 design_dna.json → 确认所有token和规则
2. 读取 outline.json → 确认14张幻灯片的类型和内容
3. 创建 slides/ 目录
4. 按顺序编写 Slide_1.tsx → Slide_14.tsx（每个组件5-10分钟）
5. 创建 index.ts
6. 验证：activate → build → 检查manifest不为空
```

**预估时间**：14张组件约60-90分钟（比并行background tasks更快更稳定）

---

### 快速生成模板参考

为加速组件编写，以下是最常用的视觉锚点代码模板：

#### 模板A：超大数字 Callout

```tsx
<div className="flex items-center justify-center w-[600px] h-[400px] relative" data-ppt-bg="true">
  <div className="absolute w-[400px] h-[200px] rounded-full opacity-30"
    style={{ background: 'radial-gradient(ellipse at center, var(--ppt-chart-2)20 0%, transparent 70%)' }} />
  <span className="text-[180px] font-black leading-none relative z-10"
    style={{ 
      color: 'var(--ppt-chart-2)',
      fontFamily: 'var(--ppt-font-display)',
    }}
    data-ppt-text="true">
    60%
  </span>
</div>
```

#### 模板B：Bento 网格卡片

```tsx
<div className="grid grid-cols-2 gap-8 p-12" data-ppt-bg="true">
  {items.map((item, idx) => (
    <div key={idx} className="rounded-3xl p-8 bg-white border border-gray-200 shadow-lg">
      <span className="text-[96px] font-light opacity-40" style={{ fontFamily: 'var(--ppt-font-display)' }} data-ppt-text="true">
        {String(idx + 1).padStart(2, '0')}
      </span>
      <h3 className="text-2xl font-bold mt-4" style={{ fontFamily: 'var(--ppt-font-display)' }} data-ppt-text="true">
        {item.title}
      </h3>
      <p className="text-lg opacity-70" style={{ fontFamily: 'var(--ppt-font-body)' }} data-ppt-text="true">
        {item.desc}
      </p>
    </div>
  ))}
</div>
```

#### 模板C：大号装饰引号

```tsx
<div className="flex items-center gap-8" data-ppt-bg="true">
  <span className="text-[150px] leading-none opacity-15" style={{ fontFamily: 'var(--ppt-font-display)', color: 'var(--ppt-rule)' }}>
    「
  </span>
  <div className="flex-1">
    <h2 className="text-[48px] leading-tight font-bold" style={{ fontFamily: 'var(--ppt-font-display)' }} data-ppt-text="true">
      引用文字内容
    </h2>
  </div>
  <span className="text-[150px] leading-none opacity-15" style={{ fontFamily: 'var(--ppt-font-display)', color: 'var(--ppt-rule)' }}>
    」
  </span>
</div>
```

#### 模板D：SVG 图标网格

```tsx
<div className="grid grid-cols-3 gap-6" data-ppt-bg="true">
  {icons.map((icon, idx) => (
    <div key={idx} className="w-[120px] h-[120px] flex items-center justify-center rounded-2xl bg-white/5">
      <svg width="80" height="80" viewBox="0 0 80 80">
        {/* 使用 <g> 包裹多个 SVG 元素 */}
        <g stroke={icon.color} strokeWidth="3" fill="none">
          <circle cx="40" cy="40" r="30" />
          <path d="M40 10 L70 40 L40 70 L10 40 Z" />
        </g>
      </svg>
    </div>
  ))}
</div>
```

### Marker 合同（极其重要）

| Marker | 加在哪里 | 用途 |
|--------|---------|------|
| `data-ppt-slide={N}` | 根容器，每个组件唯一一个 | 幻灯片识别 |
| `data-ppt-bg="true"` | 独立视觉区块（卡片、图表容器、SVG外包层、装饰图形区） | 高保真截图 |
| `data-ppt-text="true"` | 标题、正文、数字等需要在 PPT 中保持可编辑的文本 | 原生文本框 |

**禁止**：同一元素同时有 `data-ppt-bg` 和 `data-ppt-text`。

---

### 视觉能力 · 图表与配图系统

**核心原则：每张幻灯片必须有视觉锚点。纯文字幻灯片是失败品，会被观众无视。**

按以下决策树选择视觉策略：

```
幻灯片有定量数据（百分比/数字对比/趋势）？
  ├─ 是 → SVG 图表（必须带渐变/阴影/动画感，占屏幕1/3以上）
  └─ 否
      ├─ 有流程/关系/架构 → Diagram 节点图（带箭头和颜色区分）
      ├─ 有时间线 → SVG timeline（带渐变填充和节点动画感）
      ├─ 纯概念/论点 → 图标网格（3-6个统一风格图标）+ 装饰SVG图案
      └─ 人物/场景/情感 → 真实高质量图片（占屏幕40%以上）
```

---

#### 能力一：内联 SVG 图表（数据可视化首选）

直接在 React 组件里编写 SVG，无需外部库。适用于柱状图、折线图、饼图、进度条等。

**⚠️ 强制视觉效果要求**：

SVG 图表不能是简单的线条和方块，必须具备以下视觉特征：
1. **渐变填充**：柱状图、面积图必须使用 `linearGradient` 渐变
2. **阴影效果**：关键元素（柱体、节点）必须有 `filter` 阴影
3. **动画感装饰**：背景必须有装饰性元素（网格线、光晕、点点）
4. **颜色丰富**：至少使用 3 种 `var(--ppt-chart-*)` 变量
5. **尺寸醒目**：图表容器必须占屏幕 1/3 以上

**柱状图示例（带渐变+阴影+装饰）**：
```tsx
<div className="w-[600px] h-[400px] rounded-2xl p-8 bg-white/5 backdrop-blur-xl" data-ppt-bg="true">
  <svg viewBox="0 0 560 320" className="w-full h-full">
    <defs>
      {/* 柱状图渐变 */}
      <linearGradient id="barGrad1" x1="0" y1="1" x2="0" y2="0">
        <stop offset="0%" stopColor="var(--ppt-chart-1)" stopOpacity="0.6" />
        <stop offset="100%" stopColor="var(--ppt-chart-1)" stopOpacity="1" />
      </linearGradient>
      <linearGradient id="barGrad2" x1="0" y1="1" x2="0" y2="0">
        <stop offset="0%" stopColor="var(--ppt-chart-2)" stopOpacity="0.6" />
        <stop offset="100%" stopColor="var(--ppt-chart-2)" stopOpacity="1" />
      </linearGradient>
      {/* 阴影滤镜 */}
      <filter id="barShadow" x="-20%" y="-20%" width="140%" height="140%">
        <feDropShadow dx="2" dy="4" stdDeviation="4" floodColor="var(--ppt-chart-1)" floodOpacity="0.3"/>
      </filter>
      {/* 背景光晕 */}
      <radialGradient id="bgGlow" cx="50%" cy="50%" r="70%">
        <stop offset="0%" stopColor="var(--ppt-chart-1)" stopOpacity="0.05" />
        <stop offset="100%" stopColor="var(--ppt-bg)" stopOpacity="0" />
      </radialGradient>
    </defs>
    
    {/* 背景光晕装饰 */}
    <ellipse cx="280" cy="160" rx="400" ry="200" fill="url(#bgGlow)" />
    
    {/* 网格线装饰 */}
    {[0, 0.25, 0.5, 0.75, 1].map((t, i) => (
      <line key={i} x1="60" y1={280 - t*240} x2="540" y2={280 - t*240}
        stroke="var(--ppt-border)" strokeWidth="1" strokeDasharray="4 4" opacity="0.3" />
    ))}
    
    {/* 数据柱（带渐变+阴影） */}
    {[
      { label: 'Q1', value: 0.6, grad: 'barGrad1' },
      { label: 'Q2', value: 0.8, grad: 'barGrad2' },
      { label: 'Q3', value: 0.55, grad: 'barGrad1' },
      { label: 'Q4', value: 0.95, grad: 'barGrad2' },
    ].map((d, i) => (
      <g key={i}>
        <rect x={80 + i*110} y={280 - d.value*240} width="70" height={d.value*240}
          fill={`url(#${d.grad})`} rx="8" filter="url(#barShadow)" />
        {/* 顶部高光 */}
        <rect x={80 + i*110 + 5} y={280 - d.value*240 + 2} width="60" height="3"
          fill="white" opacity="0.4" rx="1.5" />
        {/* 数值标签 */}
        <text x={115 + i*110} y={280 - d.value*240 - 15}
          textAnchor="middle" fill="var(--ppt-text)" fontSize="18" fontWeight="700">
          {Math.round(d.value*100)}%
        </text>
        {/* 底部标签 */}
        <text x={115 + i*110} y="305"
          textAnchor="middle" fill="var(--ppt-muted)" fontSize="14" fontWeight="500">
          {d.label}
        </text>
      </g>
    ))}
  </svg>
</div>
```

**环形进度图示例（带渐变+动画感）**：
```tsx
<div className="w-[300px] h-[300px]" data-ppt-bg="true">
  <svg viewBox="0 0 200 200" className="w-full h-full">
    <defs>
      <linearGradient id="ringGrad" x1="0" y1="0" x2="1" y2="1">
        <stop offset="0%" stopColor="var(--ppt-chart-1)" />
        <stop offset="50%" stopColor="var(--ppt-chart-2)" />
        <stop offset="100%" stopColor="var(--ppt-chart-3)" />
      </linearGradient>
      <filter id="glowFilter">
        <feGaussianBlur stdDeviation="3" result="blur" />
        <feMerge>
          <feMergeNode in="blur" />
          <feMergeNode in="SourceGraphic" />
        </feMerge>
      </filter>
    </defs>
    
    {/* 背景环 */}
    <circle cx="100" cy="100" r="80" fill="none" stroke="var(--ppt-muted)" strokeWidth="12" opacity="0.2" />
    
    {/* 进度环（带渐变+发光） */}
    <circle cx="100" cy="100" r="80" fill="none" stroke="url(#ringGrad)" strokeWidth="12"
      strokeLinecap="round" strokeDasharray="402" strokeDashoffset="160" 
      transform="rotate(-90 100 100)" filter="url(#glowFilter)" />
    
    {/* 中心数字 */}
    <text x="100" y="100" textAnchor="middle" dominantBaseline="middle"
      fill="var(--ppt-text)" fontSize="48" fontWeight="800">
      60%
    </text>
    
    {/* 底部标签 */}
    <text x="100" y="145" textAnchor="middle"
      fill="var(--ppt-muted)" fontSize="12">
      完成进度
    </text>
  </svg>
</div>
```

---

#### 能力二：图标网格（概念类幻灯片首选）

用统一风格的图标替代 bullet points，产生视觉节奏。

**⚠️ 强制视觉效果要求**：
- 图标数量：3-6 个
- 图标尺寸：每个 ≥ 80px
- 排列方式：网格或环形排列，**不能是简单的竖向列表**
- 装饰：图标下方必须有渐变色块或光晕装饰
- 风格统一：使用 Lucide 或 Heroicons，不使用 emoji

**图标网格示例**：
```tsx
<div className="grid grid-cols-3 gap-8 p-12" data-ppt-bg="true">
  {[
    { icon: 'Brain', label: '快速理解', color: 'var(--ppt-chart-1)' },
    { icon: 'Eye', label: '辨别真实', color: 'var(--ppt-chart-2)' },
    { icon: 'Link', label: '知识连接', color: 'var(--ppt-chart-3)' },
    { icon: 'Lightbulb', label: '多角度思考', color: 'var(--ppt-chart-4)' },
    { icon: 'Users', label: '团队协作', color: 'var(--ppt-chart-5)' },
    { icon: 'Rocket', label: '持续学习', color: 'var(--ppt-chart-1)' },
  ].map((item, i) => (
    <div key={i} className="flex flex-col items-center p-6 rounded-2xl bg-white/5 backdrop-blur-xl">
      {/* 图标容器（带光晕） */}
      <div className="w-24 h-24 rounded-xl flex items-center justify-center mb-4"
        style={{ background: `radial-gradient(circle at center, ${item.color}20 0%, transparent 70%)` }}>
        {/* Lucide 图标 */}
        <svg className="w-12 h-12" style={{ color: item.color }}>
          {/* 根据 icon 名称绘制 Lucide 图标路径 */}
        </svg>
      </div>
      {/* 标签 */}
      <span className="text-lg font-semibold text-[var(--ppt-text)]" data-ppt-text="true">{item.label}</span>
    </div>
  ))}
</div>
```

---

#### 能力三：大数字 Callout（统计数据幻灯片首选）

将关键数字放大到极致，形成无可忽视的视觉焦点。

**⚠️ 强制视觉效果要求**：
- 数字字号：≥ 120px，占屏幕 1/4 以上
- 颜色：使用主题强调色或渐变
- 装饰：数字必须有背景光晕、渐变填充或描边效果
- 对比：数字与周围文字形成明显的尺寸对比

**大数字 Callout 示例**：
```tsx
<div className="flex items-center justify-center w-full h-[600px]" data-ppt-bg="true">
  {/* 背景光晕 */}
  <div className="absolute w-[800px] h-[400px] rounded-full"
    style={{ background: 'radial-gradient(ellipse at center, var(--ppt-chart-1)15 0%, transparent 60%)' }} />
  
  {/* 大数字 */}
  <div className="text-center relative">
    <span className="text-[180px] font-black leading-none"
      style={{ 
        color: 'var(--ppt-chart-1)',
        textShadow: '0 0 80px var(--ppt-chart-1), 0 0 40px var(--ppt-chart-1)',
      }}
      data-ppt-text="true">
      60%
    </span>
    <div className="text-3xl text-[var(--ppt-text)] mt-8 font-semibold" data-ppt-text="true">
      未来的工作，今天还不存在
    </div>
  </div>
</div>
```

---

#### 能力四：装饰性 SVG 图案（所有幻灯片通用）

在背景或边角加入动态感的 SVG 装饰，打破方正感。

**常用装饰图案**：
- 动态波浪线/折线
- 点状网格（带渐变透明度）
- 几何形状组合（三角形、圆形、六边形）
- 光晕效果（radial-gradient 模拟）

**装饰图案示例**：
```tsx
{/* 背景动态波浪线 */}
<svg className="absolute top-0 left-0 w-full h-full opacity-10" viewBox="0 0 1920 1080">
  <defs>
    <linearGradient id="waveGrad" x1="0" y1="0" x2="1" y2="0">
      <stop offset="0%" stopColor="var(--ppt-chart-1)" />
      <stop offset="50%" stopColor="var(--ppt-chart-2)" />
      <stop offset="100%" stopColor="var(--ppt-chart-1)" />
    </linearGradient>
  </defs>
  <path d="M0,200 Q480,100 960,200 T1920,200" stroke="url(#waveGrad)" strokeWidth="4" fill="none" />
  <path d="M0,400 Q480,300 960,400 T1920,400" stroke="url(#waveGrad)" strokeWidth="3" fill="none" opacity="0.5" />
</svg>

{/* 点状网格装饰 */}
<svg className="absolute bottom-0 right-0 w-[400px] h-[400px] opacity-5">
  {Array.from({ length: 20 }).map((_, i) =>
    Array.from({ length: 20 }).map((_, j) => (
      <circle key={`${i}-${j}`} cx={i * 20} cy={j * 20} r="2" fill="var(--ppt-chart-1)" />
    ))
  )}
</svg>
```

---

#### 能力五：真实高质量图片（情感类幻灯片首选）

从 Unsplash/Pexels 获取高质量图片，用于营造氛围。

**⚠️ 强制视觉效果要求**：
- 图片占比：≥ 40% 屏幕
- 图片质量：高分辨率（≥ 1920x1080）
- 图片情绪：必须匹配 `image_mood` 关键词
- 装饰叠加：图片上必须叠加装饰层（渐变遮罩、文字叠加区）

**图片叠加示例**：
```tsx
<div className="relative w-[800px] h-[600px]" data-ppt-bg="true">
  {/* 真实图片 */}
  <img src="https://images.unsplash.com/photo-..." 
    className="w-full h-full object-cover rounded-2xl" alt="..." />
  
  {/* 渐变遮罩层 */}
  <div className="absolute inset-0 rounded-2xl"
    style={{ background: 'linear-gradient(to top, var(--ppt-bg) 0%, transparent 50%)' }} />
  
  {/* 文字叠加区 */}
  <div className="absolute bottom-12 left-12 right-12 text-white">
    <h3 className="text-2xl font-bold" data-ppt-text="true">标题文字</h3>
    <p className="text-lg opacity-80" data-ppt-text="true">描述文字</p>
  </div>
</div>
```

---

### index.ts 导出文件（必须最后创建）

所有幻灯片写完后，在 `output/projects/<project-id>/slides/` 下创建 `index.ts`（注意：**必须是 `.ts`，不是 `.tsx`**）。

格式固定为 `export default [array]`，App 通过动态 import 加载，**不接受命名导出**：

```ts
import Slide_1 from './Slide_1'
import Slide_2 from './Slide_2'
// ... 按实际张数补全
import Slide_N from './Slide_N'

export default [Slide_1, Slide_2, /* ... */ Slide_N]
```

### 完成后自动化验证

写完所有幻灯片后，**必须按顺序执行以下验证**：

#### Step 1：检查文件完整性

```bash
# 检查所有文件是否存在
ls output/projects/<project-id>/slides/
# 应看到：Slide_1.tsx 到 Slide_14.tsx + index.ts（共15个文件）
```

#### Step 2：激活并验证基础结构

```bash
python3 tools/ppt_workflow.py activate --project <project-id>
python3 tools/ppt_workflow.py validate --project <project-id>
```

#### Step 3：检查 Vite 渲染是否正常

**⚠️ 关键检查：activate 后必须确认 Vite 能正常渲染**

```bash
# 启动 Vite（如果未启动）
cd web && npm run dev &
sleep 3

# 检查是否有编译错误
curl -s http://localhost:5173/ | head -5
# 如果返回 HTML，说明渲染正常

# 如果有错误，检查错误日志并修复
```

常见错误及修复：

| 错误类型 | 错误信息 | 修复方法 |
|---------|---------|---------|
| Import路径错误 | `Failed to resolve import "../../web/src/styles"` | 替换为 `../../styles` |
| JSX语法错误 | `Expected ',' or ')' but found 'Identifier'` | SVG内多元素用 `<></>` 或 `<g>` 包裹 |
| CSS变量错误 | `var(--color-*)` 未定义 | 替换为 `var(--ppt-*)` |

#### Step 4：构建并检查 manifest 不为空

```bash
python3 tools/ppt_workflow.py build --project <project-id>

# ⚠️ 检查 manifest 不为空（空manifest说明提取失败）
cat output/projects/<project-id>/layout_manifest.json
# 应看到包含 slides 数组的 JSON，不为 `{ "slides": [] }`

# 检查 assets 目录有文件
ls output/projects/<project-id>/assets/ | wc -l
# 应返回 > 0（有多个PNG切片文件）
```

**如果 manifest 为空**：说明渲染失败，返回 Step 3 检查 Vite 错误。

---

**视觉质量门槛检查（核心）**：

- [ ] **视觉锚点存在**：每张幻灯片有至少一个能抓住观众注意力的元素（大数字/图表/图标网格/强对比色块）
- [ ] **视觉锚点醒目**：视觉锚点的尺寸足够大（数字 ≥ 120px，图表 ≥ 屏幕1/3，图标 ≥ 80px）
- [ ] **禁止平庸布局**：没有"标题+简单列表"的死板结构
- [ ] **现代排版技法**：每张幻灯片使用了至少 2 种现代排版技法（Bento网格/大数字/悬浮重叠/斜切分割/渐变/装饰SVG/图标网格/强对比色块）
- [ ] **图表视觉效果**：SVG 图表有渐变填充、阴影效果、背景装饰（不是简单的线条方块）
- [ ] **观众视角验证**：能回答"观众3秒内被什么抓住？"，答案是视觉元素而非文字

---

## Agent 5 · 图片编排（Python工具）

```bash
python3 tools/image_orchestrator.py \
  output/projects/<project-id>/slides.json \
  output/projects/<project-id>/slides_with_images.json \
  .env.json
```

其中 `.env.json` 格式：

```json
{
  "unsplash": "YOUR_UNSPLASH_ACCESS_KEY",
  "pexels": "YOUR_PEXELS_API_KEY",
  "pixabay": "YOUR_PIXABAY_API_KEY",
  "anthropic": "YOUR_ANTHROPIC_API_KEY（可选，claude 策略用）",
  "openai": "YOUR_OPENAI_API_KEY（可选，ai 策略用）"
}
```

如果没有对应 API key，跳过该级别。推荐至少配置 pexels（额度最充裕、免署名）。

---

## Agent 6 · React 引擎无头截获（自动运行并获取组件局部切片坐标）

一键启动 Vite 服务，并由 Python 的 Playwright 发起并执行"原生元素双轨脱水"动作（背景元素高保真快照，文本元素节点坐标记录）。

```bash
python3 tools/ppt_workflow.py extract --project <project-id>
```

该工具将：
1. 自动调用子进程在后台运行 `npm run dev`（从 `web/` 子目录）唤醒 Web 端。
2. Playwright 并发请求所有打上 `data-ppt-slide` 的页面树。
3. 对带 `data-ppt-bg` 属性的毛玻璃卡片和绘图进行切块原样保存。
4. 获取带 `data-ppt-text` 的文本内容和样式、物理极值坐标。

**⚠️ 注意**：`npm run dev` / `npm install` 等命令必须在 `web/` 子目录下执行，项目根目录没有 `package.json`。若工具启动 Vite 失败，手动先跑：
```bash
cd web && npm run dev &
```
确认 `http://localhost:5173` 返回 200 后再重跑 extract。

输出结果存至 `output/projects/<project-id>/layout_manifest.json` 与 `output/projects/<project-id>/assets/`。

---

## Agent 7 · 终极 PPTX 原生缝合（Python工具）

依据上一步提取出来的碎图与文字骨架表，反向生成真正的高颜值且拥有完美字体的可编辑 PPT。

```bash
python3 tools/ppt_workflow.py export --project <project-id>
```

**输出文件**：

- `output/projects/<project-id>/presentation.pptx` — 高颜值且完全分离好独立对象组件的终极 Hybrid PPTX
- 运行在本地 `localhost:5173` 的完美前端组件展示站

向用户汇报成功，并告知它最终导出的文件去向！
