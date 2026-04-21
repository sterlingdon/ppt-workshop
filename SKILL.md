---
name: article-to-ppt
description: Use when the user wants to convert an article, URL, or document into a presentation. Triggers on phrases like "做成PPT", "转成幻灯片", "制作演示文稿", "make a presentation from", "convert to slides". Supports URL, plain text, and PDF file paths as input.
---

# Article → PPT Skill

将文章（URL / 文本 / PDF）转换为专业演示文稿（HTML + Hybrid PPTX）。

## 入参

```
/ppt <input> [--theme <theme>] [--slides <n>] [--lang <zh|en>]
```

- `<input>`：URL、文本内容、或本地文件路径（PDF / .txt / .md）
- `--theme`：可选，指定主题（aurora-borealis | bold-signal | editorial-ink）
- `--slides`：可选，目标幻灯片数量（8-25，默认自动决定）
- `--lang`：可选，输出语言（默认 zh）

## 断点续跑

每步开始前检查 `output/` 是否已有对应文件。如果存在且非空，跳过该步骤：

```
output/article_text.md      → 跳过 Agent 1
output/analysis.json        → 跳过 Agent 2
output/outline.json         → 跳过 Agent 3
output/slides.json          → 跳过 Agent 4
output/slides_with_images.json → 跳过 Agent 5
output/presentation.html    → 跳过 Agent 6
output/presentation_hybrid.pptx → 跳过 Agent 7
```

强制重跑某步：删除对应文件后重新运行。

## Agent 1 · 文章提取

**目标**：获取文章纯文本，保存到 `output/article_text.md`

**判断输入类型**：

- 以 `http://` 或 `https://` 开头 → URL
- 以 `.pdf` 结尾或文件存在且为 PDF → PDF
- 否则 → 直接使用文本

**URL 输入**：使用 WebFetch 工具获取页面内容，提取正文（忽略导航、广告、页脚）

**PDF 输入**：调用 Python 工具：

```bash
python tools/ingest.py pdf "<path>" | python -c "import sys,json; print(json.load(sys.stdin)['text'])" > output/article_text.md
```

**文本输入**：直接写入 `output/article_text.md`

**验证**：`output/article_text.md` 字符数 > 200，否则报错提示用户检查输入。

---

## Agent 2 · 内容分析

**目标**：深度分析文章，输出 `output/analysis.json`（必须符合 `schemas/analysis.schema.json`）

阅读 `output/article_text.md`，执行以下分析并输出 JSON：

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
  "language": "文章主要语言，zh或en"
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
- 其他 → aurora-borealis

**规则**：

- statistics 最多提取5条，必须是文章中的真实数据，不得编造
- quotes 最多提取3条，必须是原文引用，不得改写
- 如果用户通过 `--theme` 参数指定了主题，覆盖 `suggested_theme`

**验证**：用 `jsonschema` 验证输出：

```bash
python -c "
import json, jsonschema
data = json.load(open('output/analysis.json'))
schema = json.load(open('schemas/analysis.schema.json'))
jsonschema.validate(data, schema)
print('✓ analysis.json 验证通过')
"
```

---

## Agent 3 · 幻灯片规划

**目标**：制定幻灯片大纲，输出 `output/outline.json`（必须符合 `schemas/outline.schema.json`）

读取 `output/analysis.json`，按以下规则规划幻灯片：

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

**输出格式与全局设计**：
严格按照 `schemas/outline.schema.json` 输出。整体必须透传选定的 `theme` 并固定 `style_constraints`，同时每个 `slide` 对象包含 `index`, `type`, `title`, `needs_image` 等核心排版字段。

```json
{
  "theme": "直接透传 Agent 2 输出的 suggested_theme，如 bold-signal",
  "style_constraints": {
    "heading_emphasis": "gradient（深色主题）或 solid（浅色主题/editorial-ink）",
    "card_style": "glass（深色主题）或 outlined（浅色主题）",
    "stat_style": "gradient-text（深色）或 accent-color（浅色）",
    "bullet_style": "dot",
    "divider_style": "gradient-line",
    "image_style_fingerprint": [
      "基于主题和领域选2-4个风格词，如：cinematic lighting, deep purple and cyan"
    ]
  },
  "slides": []
}
```

**验证**：

```bash
python -c "
import json, jsonschema
data = json.load(open('output/outline.json'))
schema = json.load(open('schemas/outline.schema.json'))
jsonschema.validate(data, schema)
print(f'✓ outline.json 验证通过，共 {len(data[\"slides\"])} 张幻灯片')
"
```

---

## Agent 4 · 幻灯片数据构建

**目标**：为每张幻灯片填充完整数据，输出 `output/slides.json`（必须符合 `schemas/slides.schema.json`）

读取 `output/outline.json` 和 `output/analysis.json`，逐张构建幻灯片数据。

**每种幻灯片类型的 `content` 结构**：

`title` / `conclusion`：

```json
{
  "type": "title",
  "heading": "标题",
  "subheading": "副标题（可选）",
  "content": {}
}
```

`bullet-list`：

```json
{
  "content": {
    "bullets": ["最多5条", "每条不超过20字", "主动语态", "包含关键词"]
  }
}
```

`stats-callout`：

```json
{
  "content": {
    "stats": [{ "value": "85%", "label": "增长率", "context": "同比2023年" }]
  }
}
```

`timeline`：

```json
{
  "content": {
    "items": [{ "date": "2020年", "event": "重要节点描述，15字以内" }]
  }
}
```

`card-grid-2` / `card-grid-3`：

```json
{
  "content": {
    "cards": [
      {
        "title": "标题",
        "body": "描述，30字以内",
        "icon": "lucide图标名（可选）"
      }
    ]
  }
}
```

`quote-callout`：

```json
{
  "content": {
    "quote": { "text": "引用原文", "author": "姓名", "role": "职位" }
  }
}
```

`comparison`：

```json
{
  "content": {
    "columns": [
      { "title": "方案A", "items": ["特点1", "特点2"], "positive": true }
    ]
  }
}
```

`two-column`：

```json
{
  "content": {
    "left": { "title": "左侧标题", "type": "bullets", "items": ["..."] },
    "right": { "title": "右侧标题", "type": "text", "text": "..." }
  }
}
```

`fact-list`：

```json
{ "content": { "facts": [{ "emoji": "🚀", "title": "标题", "body": "描述" }] } }
```

`exec-summary`：

```json
{ "content": { "points": ["要点1", "要点2", "要点3"] } }
```

`section-divider` / `agenda`：

```json
{ "content": { "items": ["章节1", "章节2"], "section_number": "01" } }
```

`chart`：

```json
{
  "content": {
    "chart": {
      "type": "bar",
      "labels": ["Q1", "Q2", "Q3"],
      "datasets": [
        {
          "label": "收入",
          "data": [100, 150, 200],
          "backgroundColor": "rgba(99,102,241,0.7)"
        }
      ]
    }
  }
}
```

**出图能力与媒体策略规范**（`image_request`字段，`needs_image: true`的幻灯片必填）：

**【核心原则】：你具备原生绘制逻辑图和生成图表数据的能力！请优先发挥你的“造图”能力，尽量减少对外部图片搜索API的依赖。**

**策略划分框架：**

1. **Agent 自主管控策略**（无需网络请求，直接靠你的智能输出构建）：
   - `diagram`（逻辑节点图）：你提供节点结构和坐标系关系，渲染引擎绘制。
   - `svg`（基础矢量图）：你直接编写带样式的 SVG 代码。
   - `canvas`（图表数据驱动）：外层 chart 组件生效，Chart.js 渲染。
2. **后置拉取渲染策略**（由 Agent 5 的外部脚本负责找图或生图）：
   - `unsplash` / `pexels` / `pixabay`：触发外部真实背景图库搜索拉取。
   - `ai`：触发外部 DALL-E/Midjourney 等纯 AI 绘图模型的图像生成调用。

**大模型决策与输出规则：**

- 在 `image_request` 中，你需要决策一个 `strategy_chain`（策略优先级列表）。后续处理流水线会按你的建议链条顺次尝试渲染。
- **重点：** 如果你的链首选填了自治策略（如 `diagram`、`svg` 等），**你必须当即生成对应的高级数据结构！**

不同幻灯片类型对应的推荐选型参考表：

| 幻灯片类型      | 优先首选策略                 | `strategy_chain` 示例          | 你作为 Agent 必须顺带输出的数据                     |
| --------------- | ---------------------------- | ------------------------------ | --------------------------------------------------- |
| 对比/层级/架构  | **diagram**（重点使用）      | `["diagram", "svg"]`           | 计算好的 `diagram_nodes` 与 `diagram_edges`         |
| 发展趋势/事件流 | **diagram** 连线或纯 **svg** | `["diagram", "svg", "icon"]`   | 节点关系列表或完整的 `svg_code` 图形                |
| 数据占比与统计  | **canvas** 或图标            | `["canvas"]`                   | 在外层 `chart` 对象中填写严谨具体的统计值           |
| 名言引用/纯背景 | 外部搜索图库辅助             | `["pexels", "unsplash", "ai"]` | 只需在 `description` 中写出高质量英文图像搜索提示词 |

---

**能力一：Diagram 自动布局节点图（最强大招，体现智能的核心）**
当策略含 `diagram`，你不是输出一张画完的位图，而是直接向后端的架构师引擎输出**语义化的节点与层级连接**。这套系统后续会自动结合主题调配颜色。
_适用大场景：流程框架拆解、业务流转、事物组件网络、逻辑决策树。_

**节点颜色类型映射（与幻灯片主题自动融色，你只需要指定类型语义而不用管具体色值）：**

- `primary`：主角核心实体
- `accent`：次要核心、支撑件
- `cyan`：系统入口、输入流、外部数据
- `success`：正向结果、业务输出、完结
- `warning`：瓶颈点、系统黑盒、风险点
- `muted`：底层基石、底座或说明性辅助

生成示例代码块要求如下：

```json
"image_request": {
  "description": "内容理解系统处理逻辑流程架构图",
  "strategy_chain": ["diagram", "svg"],
  "diagram_width": 900,
  "diagram_height": 420,
  "diagram_nodes": [
    {"id": "a", "label": "输入参数", "sublabel": "复杂多模态", "type": "cyan", "x": 80, "y": 180},
    {"id": "b", "label": "AI大脑解析", "sublabel": "调度流", "type": "primary", "x": 350, "y": 180},
    {"id": "c", "label": "执行渲染组", "sublabel": "渲染器群集", "type": "accent", "x": 620, "y": 100},
    {"id": "d", "label": "交付成品", "sublabel": "用户可感知界面", "type": "success", "x": 620, "y": 260}
  ],
  "diagram_edges": [
    {"from": "a", "to": "b", "label": "发送协议", "dashed": false},
    {"from": "b", "to": "c", "label": "发版", "accent": true},
    {"from": "b", "to": "d", "dashed": true}
  ]
}
```

**空间绘图心智准则：**

- 作为一个严谨的布局系统引擎输入源：标准节点尺寸为 `w:140, h:52`。你的画布坐标是左上角 `(0, 0)` 到右下角 `(900, 500)`，预先在大脑里推算一下分布的 `(x, y)` 不发生拥挤重叠。
- 线性流程必须固定 Y 轴平推 X 值。层级结构或条件分支必须错落排开 Y 值。避免交叉线条。节点控制在 3到8 个最清爽。

---

**能力二：手工构建基础 SVG 图形（轻量级替代品）**
当架构关系极简、亦或是非节点的线型展现形式（比如纯粹展示利润走势的单根大号折线），选取该方案。
要求：

- 底板为 `viewBox="0 0 400 240"` 大小框架。
- 必须严格挂载工程CSS变量体系，颜色**严禁出现硬编码色值（如 #FFFFFF）**。只使用 `var(--color-primary)`、`var(--color-secondary)` 和 `var(--color-accent)`。
- 将纯粹的原生结构直接写到 `svg_code` 属性内。

生成示例：

```json
"image_request": {
  "description": "利润率持续爬升大面积折线趋势底层底图",
  "strategy_chain": ["svg", "icon"],
  "svg_code": "<svg xmlns=\"http://www.w3.org/2000/svg\" viewBox=\"0 0 400 240\">\n  <!-- Agent 手指绘制走线，运用主题自适应映射变量颜色 -->\n  <polyline points=\"20,200 80,160 140,120 200,90 260,60 320,40 380,20\" stroke=\"var(--color-primary)\" fill=\"none\" stroke-width=\"4\" stroke-linecap=\"round\"/>\n  <!-- 底层氛围 -->\n  <polyline points=\"20,200 80,160 140,120 200,90 260,60 320,40 380,20 380,240 20,240\" fill=\"var(--color-primary)\" opacity=\"0.1\"/>\n</svg>"
}
```

**验证**：

```bash
python -c "
import json, jsonschema
data = json.load(open('output/slides.json'))
schema = json.load(open('schemas/slides.schema.json'))
jsonschema.validate(data, schema)
print(f'✓ slides.json 验证通过，共 {len(data)} 张幻灯片')
"
```

---

## Agent 5 · 图片编排（Python工具）

```bash
python tools/image_orchestrator.py output/slides.json output/slides_with_images.json .env.json
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

## Agent 6 · HTML 渲染（Python工具）

```bash
python -c "
import json
from tools.html_renderer import HTMLRenderer
data = json.load(open('output/slides_with_images.json'))
renderer = HTMLRenderer(themes_dir='themes', templates_dir='templates')
html = renderer.render(data)
open('output/presentation.html', 'w').write(html)
print('✓ HTML 渲染完成 → output/presentation.html')
"
```

打开 `output/presentation.html` 在浏览器中预览，确认视觉效果。

---

## Agent 7 · PPTX 导出（Python工具）

读取主题 token（从 outline.json 的 theme 字段决定）：

```bash
python tools/pptx_exporter.py \
  output/slides_with_images.json \
  output/presentation.html \
  output/presentation_hybrid.pptx
```

**输出文件**：

- `output/presentation.html` — 完整HTML版本（所有效果）
- `output/presentation_hybrid.pptx` — Hybrid PPTX（~80%视觉还原，内容可编辑）

告知用户输出位置，并说明：

- HTML版本在浏览器中用方向键翻页
- PPTX版本可在 PowerPoint / Keynote 中编辑文字和数据
