# Article-to-PPT Skill 设计文档

**日期**: 2026-04-20  
**状态**: 已批准，待实现

---

## Context

将任意文章（URL / 文本 / PDF）自动转换为专业演示文稿（HTML + PPTX）。现有4份架构文档已完成系统设计，本文档确定实现范围与方式，作为实现计划的输入。

目标：构建一个 Claude Code Skill，Claude 作为执行智能体，自主完成文章分析→幻灯片规划→数据构建，并调用Python工具完成图片编排、HTML渲染、PPTX导出。

---

## 架构总览

**核心决策**：方案B — 分阶段检查点（Checkpoint-based）

每个Agent步骤输出一个中间文件到 `output/` 目录，支持断点续跑、逐步调试。

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

**Agent 1-4**：由Claude执行，充分利用其推理和结构化输出能力。  
**Agent 5-7**：Python脚本处理机械性工作，Claude通过Bash工具调用。

---

## 项目结构

遵循标准Skill架构，`SKILL.md` 放根目录；原4份散乱架构文档合并为一份精密工程文档 `docs/engineering.md`。

```
ppt-workshop/
├── SKILL.md                      # Skill入口（根目录，标准架构）
├── tools/
│   ├── ingest.py                 # Agent 1辅助: PDF提取(pymupdf4llm)，URL由Claude WebFetch处理
│   ├── image_orchestrator.py     # Agent 5: 图片5级fallback编排
│   ├── html_renderer.py          # Agent 6: JSON → HTML渲染
│   └── pptx_exporter.py          # Agent 7: HTML → Hybrid PPTX
├── themes/
│   ├── _base.css                 # 公共CSS变量接口定义
│   ├── aurora-borealis.css       # MVP主题1
│   ├── bold-signal.css           # MVP主题2
│   └── editorial-ink.css         # MVP主题3
├── templates/
│   └── slide_base.html           # HTML渲染基础模板
├── schemas/
│   ├── analysis.schema.json      # Agent 2输出约束
│   ├── outline.schema.json       # Agent 3输出约束
│   └── slides.schema.json        # Agent 4输出约束
├── docs/
│   └── engineering.md            # 统一工程文档（替代原4份散乱文档）
└── output/                       # 每次运行的检查点文件（gitignore）
```

**原文档处理**：`article_to_ppt_agent_architecture.md`、`multi_style_architecture.md`、`pptx_delivery_architecture.md`、`style_consistency_design.md` 四份文档在实现完成后删除，内容精炼整合到 `docs/engineering.md`。

---

## Skill 文件设计（SKILL.md）

Skill文件职责：
1. **触发条件与入参**：接收 URL / 文本 / 文件路径；可选参数：主题名、语言、幻灯片数量
2. **Agent 1-4 执行指令**：指导Claude如何分析、规划、构建数据，每步验证schema后写入 `output/`
3. **Python工具调用时机**：明确指定何时调用哪个脚本、如何传参、如何处理结果
4. **断点续跑逻辑**：检测 `output/` 中已有的检查点，跳过已完成步骤
5. **Schema验证**：Claude输出必须通过schema验证才进入下一步

---

## 核心数据Schema

### analysis.json（Agent 2输出）
```json
{
  "domain": "technology",
  "title": "文章标题",
  "key_points": ["核心论点1", "核心论点2"],
  "statistics": [{"value": "85%", "label": "增长率"}],
  "quotes": [{"text": "...", "author": "..."}],
  "entities": ["公司名", "人名"],
  "complexity": "intermediate",
  "suggested_theme": "aurora-borealis"
}
```

### outline.json（Agent 3输出）
```json
{
  "theme": "aurora-borealis",
  "style_constraints": {
    "heading_emphasis": "gradient",
    "card_style": "glass",
    "stat_style": "gradient-text",
    "bullet_style": "dot",
    "image_style_fingerprint": ["cinematic lighting", "deep purple and cyan"]
  },
  "slides": [
    {"index": 0, "type": "title", "title": "...", "needs_image": true},
    {"index": 1, "type": "bullet-list", "title": "...", "needs_image": false}
  ]
}
```

`style_constraints` 在规划阶段一次性确定，传递给所有后续步骤，保证全局视觉一致性。

### slides.json（Agent 4输出）
每张幻灯片完整数据，含 `image_request`：
```json
[{
  "index": 0,
  "type": "stats-callout",
  "heading": "关键数据",
  "content": {
    "stats": [{"value": "85%", "label": "增长率", "icon": "trending-up"}]
  },
  "image_request": {
    "description": "增长趋势抽象图",
    "preferred_strategy": "svg",
    "fallback_chain": ["svg", "icon", "ai"]
  }
}]
```

**支持的16种幻灯片类型**：title, agenda, bullet-list, stats-callout, timeline, card-grid, chart, image-hero, quote-callout, comparison, section-divider, conclusion 等。

---

## 图片5级Fallback策略

Claude在构建 `slides.json` 时为每张幻灯片指定 `fallback_chain`，`image_orchestrator.py` 按链依次尝试：

| Level | 方案 | 成本 | 适用场景 |
|-------|------|------|---------|
| 1 | SVG内联生成（Claude在Agent 4中生成SVG代码写入slides.json，Python注入主题色变量） | 免费 | stats / timeline / 抽象图形 |
| 2 | HTML Canvas / Chart.js | 免费 | chart slides，PPTX中转原生图表 |
| 3 | 图标库（Lucide / Phosphor / Simple Icons CDN） | 免费 | 装饰图标，bullet/card装饰 |
| 4 | 图片搜索（Unsplash / Pexels免费API） | 免费tier | image-hero / 封面背景 |
| 5 | AI生图（DALL·E 3 / FLUX Pro / Ideogram） | 付费 | 定制图像，前4级不达标时 |

**决策逻辑（Claude在slides.json中指定）**：
- 数据/统计类 → Level 1 (SVG) → Level 3 (icon)
- 图表类 → Level 2 (Canvas)
- 装饰类 → Level 3 (icon) → Level 1 (SVG)
- 场景/氛围图 → Level 4 (search) → Level 5 (AI)
- 定制品牌图 → Level 5 (AI) directly

---

## 主题系统

**MVP实现3个主题**，主题系统设计为CSS变量驱动，添加新主题只需一个新CSS文件：

| 主题 | 风格 | 触发领域 |
|------|------|---------|
| aurora-borealis | 深色·极光渐变 | technology / AI |
| bold-signal | 强对比·橙色accent | business / 通用 |
| editorial-ink | 亮色·印刷排版 | education / 内容 |

`_base.css` 定义所有CSS变量接口（`--color-primary`, `--font-display`, `--card-bg` 等），各主题CSS只覆盖变量值，HTML模板和组件样式与主题完全解耦。

**扩展新主题**：只需新增一个CSS文件覆盖 `_base.css` 中的变量，其余10个预设主题（tokyo-neon, venture-pitch, midnight-cathedral 等）可逐步补充。

---

## HTML渲染（Agent 6）

`html_renderer.py` 接收 `slides_with_images.json`，输出单文件 `presentation.html`：
- 注入选定主题CSS
- 支持16种幻灯片类型的组件渲染
- 键盘导航（方向键）
- 进度条 + 幻灯片编号
- 背景动画（Blob渐变 / Particle）

---

## PPTX导出（Agent 7）

采用架构文档推荐的 **Hybrid方案**：
- **Layer 1（背景）**：Playwright截图每张幻灯片的背景视觉效果（渐变、动画粒子等）
- **Layer 2（内容）**：python-pptx原生TextFrame / Table / Chart / Shape（完全可编辑）

输出：`presentation_hybrid.pptx`（~80%视觉还原，内容层可编辑）+ `assets.zip`

---

## 验证方案

1. **单步验证**：对每个Agent步骤，准备一篇测试文章，检查输出JSON是否符合schema
2. **端到端验证**：运行完整pipeline，检查 `presentation.html` 在浏览器中的视觉效果
3. **PPTX验证**：用PowerPoint/Keynote打开 `presentation_hybrid.pptx`，验证文字可编辑、图表可调整
4. **主题验证**：对同一文章分别用3个主题生成，验证视觉差异和风格一致性
5. **断点续跑验证**：在某步骤中断后重新运行Skill，验证已完成步骤被跳过

---

## docs/engineering.md 内容范围

统一工程文档，替代原4份散乱的架构文档，涵盖：

1. **系统架构**：7 Agent流水线、数据流、职责边界
2. **数据Schema完整定义**：所有JSON结构的字段说明与约束
3. **幻灯片类型规范**：16种类型的内容规则与渲染要求
4. **图片策略详解**：5级fallback的实现细节、prompt工程
5. **主题系统规范**：CSS变量接口清单、各主题设计token
6. **PPTX Hybrid方案**：背景截图 + 原生内容层的实现逻辑
7. **一致性保障机制**：StyleConstraints传播、ConsistencyValidator规则
8. **扩展指南**：如何添加新主题、新幻灯片类型、新图片策略

该文档在实现过程中随代码同步更新，是项目的权威技术参考。

---

## MVP范围外（不在本次实现中）

- StyleDNA多风格系统（pixel-art, anime, high-tech等）
- Google Slides导出
- 多语言支持
- 品牌Kit
- Web服务/API层
