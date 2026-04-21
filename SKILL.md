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
python -c "from tools.presentation_workspace import create_project_workspace; print(create_project_workspace('演示文稿标题').project_id)"
```

默认目录结构：

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

每步开始前检查 `output/projects/<project-id>/` 是否已有对应文件。如果存在且非空，跳过该步骤：

```
article_text.md        → 跳过 Agent 1
analysis.json          → 跳过 Agent 2
outline.json           → 跳过 Agent 3
slides.json            → 跳过 Agent 4 内容结构
slides_with_images.json → 跳过 Agent 5 图片编排
layout_manifest.json   → 跳过 Agent 6 React 抽取
presentation.pptx      → 跳过 Agent 7
```

强制重跑某步：删除对应文件后重新运行。

## Agent 1 · 文章提取

**目标**：获取文章纯文本，保存到 `output/projects/<project-id>/article_text.md`

**判断输入类型**：

- 以 `http://` 或 `https://` 开头 → URL
- 以 `.pdf` 结尾或文件存在且为 PDF → PDF
- 否则 → 直接使用文本

**URL 输入**：使用 WebFetch 工具获取页面内容，提取正文（忽略导航、广告、页脚）

**PDF 输入**：调用 Python 工具：

```bash
python tools/ingest.py pdf "<path>" | python -c "import sys,json; print(json.load(sys.stdin)['text'])" > output/projects/<project-id>/article_text.md
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
data = json.load(open('output/projects/<project-id>/analysis.json'))
schema = json.load(open('schemas/analysis.schema.json'))
jsonschema.validate(data, schema)
print('✓ analysis.json 验证通过')
"
```

---

## Agent 3 · 幻灯片规划

**目标**：制定幻灯片大纲，输出 `output/projects/<project-id>/outline.json`（必须符合 `schemas/outline.schema.json`）

读取 `output/projects/<project-id>/analysis.json`，按以下规则规划幻灯片：

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
data = json.load(open('output/projects/<project-id>/outline.json'))
schema = json.load(open('schemas/outline.schema.json'))
jsonschema.validate(data, schema)
print(f'✓ outline.json 验证通过，共 {len(data[\"slides\"])} 张幻灯片')
"
```

---

## Agent 4 · React 组件级构建 (Code-Driven)

**目标**：大模型充当前端工程师，直接编写能够呈现惊艳视觉的 React 组件代码，存入 `web/src/slides/`。运行产物与中间数据必须写入当前项目工作区 `output/projects/<project-id>/`。

读取项目工作区里的 `outline.json` 和 `analysis.json`，为每一张幻灯片编写一个对应的组件文件，例如 `Slide_1.tsx`。你可以编写一个 `index.tsx` 来统一导出这些幻灯片从而供 React 渲染器遍历。

**风格预设（必须优先引用）**：

React 端维护了可复用风格库：`web/src/styles/presets.ts`。目前包含：

- `aurora-borealis`：深色科技、紫青极光、玻璃卡片、适合 AI/技术/网络安全
- `bold-signal`：黑底高对比、橙色信号条、适合商业/创业/决策汇报
- `editorial-ink`：浅色编辑部风、衬线标题、适合教育/文化/内容型报告

写幻灯片组件时先选择 preset，并在根节点注入变量：

```tsx
import { getDeckStylePreset, styleVars } from '../styles'

const preset = getDeckStylePreset('aurora-borealis')

<div
  className="w-[1920px] h-[1080px] bg-[var(--ppt-bg)]"
  style={styleVars(preset)}
  data-ppt-slide="1"
>
```

优先使用 `var(--ppt-bg)`, `var(--ppt-surface)`, `var(--ppt-primary)`, `var(--ppt-secondary)`, `var(--ppt-accent)`, `var(--ppt-text)`, `var(--ppt-muted)`, `var(--ppt-border)`, `var(--ppt-font-display)`, `var(--ppt-font-body)`，不要在每张幻灯片里重新发明一套色彩体系。

**编程规范**：
1. **彻底放飞排版**：不要拘泥于死板的布局！使用 Tailwind CSS 尽情施展排版、渐变、光影、悬浮毛玻璃、卡片交错等高级现代视觉效果。你可以混用各种布局（比如 Bento 便当盒、左大侧图边框、悬浮重叠等）。
2. **必需的组件属性（极其重要）**：
   - 必须在代表单张幻灯片的**根容器**上打上 `data-ppt-slide={index}`。同时确保该容器有一致的标准屏幕比例宽高（例如 `w-[1920px] h-[1080px]` 或纵横比约束）。
   - 遇到任何**独立视觉装饰模块**（特别是带高级光影特效、毛玻璃背景、多层阴影、特殊边框的卡片或形状区块），必须在其 HTML 标签上附带 `data-ppt-bg` 属性。系统提取器会精准对该区块进行“高保真局部截屏”，以保留毛玻璃反射效果，再当做贴片拼接到 PPT 中。
   - 遇到任何需要保留在最终 PPT 里可被用户正常高亮、修改调整的原生**文本元素**（标题、正文文本、数字摘要等），必须在它的标签上附带 `data-ppt-text` 属性，并且通过 `font-['Inter']` 等类库明确标注其字体，只有在这个标签里的文字才会原汁原味生成原生文本框。对于文本元素，千万不要使用 `data-ppt-bg`。
3. 如果你在组件里手绘内联 SVG 图表（你具备此能力！），你应该在此 SVG 外包一个带有 `data-ppt-bg` 的容器，以便 PPT 引擎将其直接截取为高清图块放置。

**示例代码（`web/src/slides/Slide_1.tsx`）**：
```tsx
export default function Slide_1() {
  return (
    // 幻灯片满屏根节点
    <div className="w-[1920px] h-[1080px] bg-slate-900..." data-ppt-slide="1">
      
      {/* PPT 引擎会精确截取这个毛玻璃卡片成为局部高保真图片 */}
      <div className="backdrop-blur-2xl ring-1 ring-white/20..." data-ppt-bg="true">
      
         {/* PPT 引擎会把这里原封不动还原为原生字体文本框，不会变糊 */}
         <h1 className="text-6xl font-black font-sans text-transparent bg-clip-text bg-gradient-to-r from-purple-400 to-pink-600" data-ppt-text="true">
           山寨季的黎明
         </h1>
      </div>
    </div>
  )
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
data = json.load(open('output/projects/<project-id>/slides.json'))
schema = json.load(open('schemas/slides.schema.json'))
jsonschema.validate(data, schema)
print(f'✓ slides.json 验证通过，共 {len(data)} 张幻灯片')
"
```

---

## Agent 5 · 图片编排（Python工具）

```bash
python tools/image_orchestrator.py \
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

一键启动 Vite 服务，并由 Python 的 Playwright 发起并执行“原生元素双轨脱水”动作（背景元素高保真快照，文本元素节点坐标记录）。

```bash
python tools/builder.py --project <project-id>
```
该工具将：
1. 自动调用子进程在后台运行 `npm run dev` 唤醒 Web 端。
2. Playwright 并发请求所有打上 `data-ppt-slide` 的页面树。
3. 对带 `data-ppt-bg` 属性的毛玻璃卡片和绘图进行切块原样保存。
4. 获取带 `data-ppt-text` 的文本内容和样式、物理极值坐标。

输出结果存至 `output/projects/<project-id>/layout_manifest.json` 与 `output/projects/<project-id>/assets/`。

---

## Agent 7 · 终极 PPTX 原生缝合 (Python工具)

依据上一步提取出来的碎图与文字骨架表，反向生成真正的高颜值且拥有完美字体的可编辑 PPT。

```bash
python tools/pptx_exporter.py \
  output/projects/<project-id>/layout_manifest.json \
  output/projects/<project-id>/presentation.pptx
```

**输出文件**：

- `output/projects/<project-id>/presentation.pptx` — 高颜值且完全分离好独立对象组件的终极 Hybrid PPTX
- 运行在本地 `localhost:5173` 的完美前端组件展示站

向用户汇报成功，并告知它最终导出的文件去向！
