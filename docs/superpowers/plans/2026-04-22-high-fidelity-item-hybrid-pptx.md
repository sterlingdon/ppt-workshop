# High-Fidelity Item Hybrid PPTX Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a high-fidelity item-level hybrid PPTX export path so repeatable slide components can be copied or deleted item-by-item without sacrificing visual fidelity.

**Architecture:** Keep the existing raster-first export path as the safety baseline. Add explicit slide authoring references, item-aware extraction in `builder.py`, item-aware placement in `pptx_exporter.py`, and validation that falls back instead of degrading visuals.

**Tech Stack:** Python, Playwright, python-pptx, React/TypeScript slide components, pytest, Markdown skill references.

---

## File Structure

- Modify `SKILL.md`: shorten and route detailed Agent 4 guidance to references instead of expanding the monolithic skill.
- Create `references/slide-coding-rules.md`: canonical marker API and React slide coding rules for agents.
- Create `references/component-authoring.md`: practical recipes for list, timeline, process, agenda, fact-list, and card-grid slides.
- Create `references/export-markers.md`: complete marker contract and exporter behavior.
- Create `references/visual-fidelity.md`: fidelity-first fallback policy.
- Create `references/pptx-exporter.md`: builder/exporter behavior and troubleshooting.
- Modify `web/src/styles/STYLE_GUIDE.md`: add short pointers to the new reference architecture.
- Modify `tools/builder.py`: extract `groups`, `items`, `segments`, `bullets`, and item-local text while preserving existing `bg_path`, `components`, and `texts` compatibility.
- Modify `tools/pptx_exporter.py`: render item groups and item text in z-order before legacy slide-level text.
- Modify `tools/quality_gate.py`: validate item marker output and fallback reporting.
- Modify `tests/test_pptx_exporter.py`: cover item raster and item-local text export.
- Create `tests/test_item_manifest.py`: cover item/group manifest extraction helpers without requiring a browser.
- Create `web/src/sample-slides/Slide_3.tsx`: item-aware list sample.
- Create `web/src/sample-slides/Slide_4.tsx`: item-aware timeline sample.
- Modify `web/src/sample-slides/index.ts`: export `Slide_3` and `Slide_4`.

## Task 1: Create Smooth Skill Reference Architecture

**Files:**
- Modify: `SKILL.md`
- Create: `references/slide-coding-rules.md`
- Create: `references/component-authoring.md`
- Create: `references/export-markers.md`
- Create: `references/visual-fidelity.md`
- Create: `references/pptx-exporter.md`
- Modify: `web/src/styles/STYLE_GUIDE.md`

- [ ] **Step 1: Create `references/slide-coding-rules.md`**

Write the reference as an API contract. Include this table and examples:

```markdown
# Slide Coding Rules

This is the canonical API contract for React slide components consumed by the PPTX exporter. Visual fidelity is the product floor. Do not simplify visual design to make PowerPoint objects more native.

## Required Root

| Marker | Purpose | Allowed element | Export behavior |
| --- | --- | --- | --- |
| `data-ppt-slide` | Marks one slide root and defines the coordinate system. | One root `div` per slide. | Builder scans this element and computes all child boxes relative to it. |

## Visual Markers

| Marker | Purpose | Allowed element | Export behavior |
| --- | --- | --- | --- |
| `data-ppt-bg` | High-fidelity raster region that is not item-aware. | Any non-text container. | Captured as a raster component. |
| `data-ppt-text` | Text that should become native PowerPoint text when safe. | Text-bearing elements such as `h1`, `h2`, `p`, `span`, `li`. | Hidden during raster capture, exported as native text. |

## Repeatable Structure Markers

| Marker | Purpose | Allowed element | Export behavior |
| --- | --- | --- | --- |
| `data-ppt-group` | Repeatable structure container. Values: `list`, `timeline`, `stepper`, `agenda`, `fact-list`, `card-grid`. | Container `div`, `ul`, `ol`, `section`. | Builder extracts child `data-ppt-item` units. |
| `data-ppt-item` | One copyable/deletable item. | Item wrapper `div`, `li`, `article`. | Captured independently unless forced to fallback. |
| `data-ppt-item-bg` | Item visual background when text overlays are native. | Child container inside item. | Captured as item raster if present. |
| `data-ppt-bullet` | Bullet, icon, number badge, image, or timeline node. | `span`, `div`, `img`, `svg`. | Included in item raster by default for maximum fidelity. |
| `data-ppt-track` | Shared rail or track. | `div`, `svg`. | Captured independently when present. |
| `data-ppt-segment` | Connector segment. | `div`, `svg`, `line` wrapper. | Captured as segment raster. |

## Optional Overrides

| Attribute | Values | Behavior |
| --- | --- | --- |
| `data-ppt-raster-mode` | `auto`, `force`, `skip` | Controls raster capture for the marked element. |
| `data-ppt-native-text` | `auto`, `force`, `skip` | Controls native text export for a `data-ppt-text` element. |
| `data-ppt-fallback` | `item-raster`, `group-raster`, `slide-raster` | Hints the safe fallback level. |

## Non-Negotiable Rules

- Do not bake item-specific bullets, cards, icons, timeline nodes, labels, or item shadows into the parent background.
- Do not use `::before` or `::after` for item-specific visuals that should become independent PPT objects.
- Keep `data-ppt-text` inside the relevant `data-ppt-item`.
- If a component cannot be itemized without visual risk, use raster fallback instead of reducing visual quality.

## Minimal Valid List

```tsx
<div data-ppt-group="list">
  {items.map((item) => (
    <div data-ppt-item key={item.id}>
      <div data-ppt-item-bg />
      <span data-ppt-bullet />
      <span data-ppt-text>{item.text}</span>
    </div>
  ))}
</div>
```
```

- [ ] **Step 2: Create `references/component-authoring.md`**

Include concrete recipes agents can copy:

```markdown
# Component Authoring Reference

Use this when writing React slide components. Build rich visuals, but keep repeatable units isolatable.

## List Recipe

```tsx
<div data-ppt-group="list" className="space-y-5">
  {items.map((item) => (
    <div data-ppt-item key={item.id} className="relative flex gap-5 rounded-3xl p-6">
      <div data-ppt-item-bg className="absolute inset-0 rounded-3xl bg-white/10 shadow-2xl" />
      <img data-ppt-bullet src={item.icon} className="relative z-10 h-12 w-12" alt="" />
      <div className="relative z-10">
        <h3 data-ppt-text>{item.title}</h3>
        <p data-ppt-text>{item.body}</p>
      </div>
    </div>
  ))}
</div>
```

## Timeline Recipe

```tsx
<div data-ppt-group="timeline" className="relative">
  <div data-ppt-track className="absolute left-0 right-0 top-1/2 h-1 rounded-full bg-white/20" />
  {items.map((item, index) => (
    <div data-ppt-item key={item.id} className="relative">
      {index > 0 && <div data-ppt-segment className="absolute -left-12 top-1/2 h-1 w-12 bg-white/40" />}
      <div data-ppt-bullet data-ppt-node className="h-8 w-8 rounded-full bg-white shadow-xl" />
      <h3 data-ppt-text>{item.title}</h3>
      <p data-ppt-text>{item.body}</p>
    </div>
  ))}
</div>
```

## Authoring Checklist

- Every repeatable structure uses `data-ppt-group`.
- Every repeatable unit uses `data-ppt-item`.
- Item text is nested inside the item.
- Parent background contains only shared atmosphere or tracks.
- Visual richness is not reduced for editability.
```

- [ ] **Step 3: Create the remaining references**

Create `references/export-markers.md`, `references/visual-fidelity.md`, and `references/pptx-exporter.md` with concise rules:

```markdown
# Visual Fidelity Reference

Priority order:

1. Preserve visual fidelity.
2. Preserve item-level copy/delete behavior.
3. Preserve text editability.
4. Preserve icon or shape editability.

Fallbacks are successful safety behavior, not failures.
```

- [ ] **Step 4: Shorten and route `SKILL.md`**

Add an Agent 4 instruction block near the React component generation section:

```markdown
Before writing any React slide component, read:

1. `references/slide-coding-rules.md`
2. `references/component-authoring.md`
3. `references/visual-fidelity.md`

Do not embed repeatable lists, timelines, process steps, agenda rows, fact cards, or card grid cells as one monolithic `data-ppt-bg`. Use `data-ppt-group` and `data-ppt-item`.
```

- [ ] **Step 5: Update `web/src/styles/STYLE_GUIDE.md`**

Add a short section:

```markdown
## Item-Aware PPT Export

Repeatable structures must use `data-ppt-group` and `data-ppt-item`. Read `references/slide-coding-rules.md` before authoring generated slides.
```

- [ ] **Step 6: Commit documentation changes**

Run:

```bash
git add SKILL.md references web/src/styles/STYLE_GUIDE.md
git commit -m "docs: add item-aware slide authoring references"
```

Expected: commit succeeds.

## Task 2: Add Manifest Helpers With Tests

**Files:**
- Create: `tools/item_manifest.py`
- Create: `tests/test_item_manifest.py`

- [ ] **Step 1: Write failing tests**

Create `tests/test_item_manifest.py`:

```python
from tools.item_manifest import make_box, make_group, make_item


def test_make_box_normalizes_coordinates():
    box = make_box({"x": 120.2, "y": 30.8, "width": 400.0, "height": 90.4}, {"x": 20.2, "y": 10.8})
    assert box == {"x": 100.0, "y": 20.0, "width": 400.0, "height": 90.4}


def test_make_item_defaults_to_item_hybrid():
    item = make_item(
        slide_index=0,
        group_index=1,
        item_index=2,
        box={"x": 10, "y": 20, "width": 300, "height": 120},
        raster_path="assets/slide_0_group_1_item_2.png",
        texts=[{"id": "text_0", "box": {"x": 1, "y": 2, "width": 3, "height": 4}, "style": {"text": "Hello"}}],
        bullets=[],
    )
    assert item["id"] == "item_0_1_2"
    assert item["mode"] == "item-hybrid"
    assert item["raster"]["path"] == "assets/slide_0_group_1_item_2.png"
    assert item["texts"][0]["style"]["text"] == "Hello"


def test_make_group_records_kind_and_items():
    item = make_item(0, 0, 0, {"x": 0, "y": 0, "width": 10, "height": 10}, "item.png", [], [])
    group = make_group(0, 0, "list", {"x": 0, "y": 0, "width": 100, "height": 100}, [item], [])
    assert group["id"] == "group_0_0"
    assert group["kind"] == "list"
    assert group["items"] == [item]
```

- [ ] **Step 2: Run tests and verify failure**

Run:

```bash
pytest tests/test_item_manifest.py -v
```

Expected: FAIL with `ModuleNotFoundError: No module named 'tools.item_manifest'`.

- [ ] **Step 3: Implement helper module**

Create `tools/item_manifest.py`:

```python
from __future__ import annotations


def _round_float(value: float) -> float:
    return round(float(value), 2)


def make_box(raw_box: dict, origin: dict | None = None) -> dict:
    origin = origin or {"x": 0, "y": 0}
    return {
        "x": _round_float(raw_box["x"] - origin.get("x", 0)),
        "y": _round_float(raw_box["y"] - origin.get("y", 0)),
        "width": _round_float(raw_box["width"]),
        "height": _round_float(raw_box["height"]),
    }


def make_item(
    slide_index: int,
    group_index: int,
    item_index: int,
    box: dict,
    raster_path: str,
    texts: list[dict],
    bullets: list[dict],
    mode: str = "item-hybrid",
    fallback_reason: str | None = None,
) -> dict:
    item = {
        "id": f"item_{slide_index}_{group_index}_{item_index}",
        "mode": mode,
        "box": box,
        "raster": {"path": raster_path, "mode": "item"},
        "texts": texts,
        "bullets": bullets,
    }
    if fallback_reason:
        item["fallbackReason"] = fallback_reason
    return item


def make_group(
    slide_index: int,
    group_index: int,
    kind: str,
    box: dict,
    items: list[dict],
    segments: list[dict],
    mode: str = "item-hybrid",
    fallback_reason: str | None = None,
) -> dict:
    group = {
        "id": f"group_{slide_index}_{group_index}",
        "kind": kind,
        "mode": mode,
        "box": box,
        "items": items,
        "segments": segments,
    }
    if fallback_reason:
        group["fallbackReason"] = fallback_reason
    return group
```

- [ ] **Step 4: Run tests and verify pass**

Run:

```bash
pytest tests/test_item_manifest.py -v
```

Expected: 3 passed.

- [ ] **Step 5: Commit helper module**

Run:

```bash
git add tools/item_manifest.py tests/test_item_manifest.py
git commit -m "test: add item manifest helpers"
```

Expected: commit succeeds.

## Task 3: Extract Item Groups In Builder

**Files:**
- Modify: `tools/builder.py`
- Test: `tests/test_item_manifest.py`

- [ ] **Step 1: Add helper extraction functions to `tools/builder.py`**

Add imports:

```python
try:
    from .item_manifest import make_box, make_group, make_item
except ImportError:
    from item_manifest import make_box, make_group, make_item
```

Add a JavaScript style extractor constant near the top:

```python
TEXT_STYLE_JS = """el => {
    const s = window.getComputedStyle(el);
    const runs = [];
    function walk(node, inherited) {
        if (node.nodeType === 3) {
            const t = node.textContent;
            if (t) runs.push({ text: t, style: { ...inherited } });
        } else if (node.nodeName === 'BR') {
            runs.push({ text: '\\n', style: { ...inherited } });
        } else if (node.nodeType === 1) {
            const cs = window.getComputedStyle(node);
            const cur = {
                color: cs.color,
                fontWeight: cs.fontWeight,
                fontSize: cs.fontSize,
                fontFamily: cs.fontFamily,
                fontStyle: cs.fontStyle,
                textDecorationLine: cs.textDecorationLine,
            };
            for (const c of node.childNodes) walk(c, cur);
        }
    }
    const rootRun = {
        color: s.color,
        fontWeight: s.fontWeight,
        fontSize: s.fontSize,
        fontFamily: s.fontFamily,
        fontStyle: s.fontStyle,
        textDecorationLine: s.textDecorationLine,
    };
    for (const c of el.childNodes) walk(c, rootRun);
    return {
        fontSize: s.fontSize,
        fontFamily: s.fontFamily,
        color: s.color,
        fontWeight: s.fontWeight,
        textAlign: s.textAlign,
        text: runs.map(r => r.text).join('') || el.innerText,
        backgroundColor: s.backgroundColor,
        borderRadius: s.borderRadius,
        paddingTop: s.paddingTop,
        paddingBottom: s.paddingBottom,
        paddingLeft: s.paddingLeft,
        paddingRight: s.paddingRight,
        runs: runs.length > 0 ? runs : null,
    };
}"""
```

- [ ] **Step 2: Use `TEXT_STYLE_JS` for existing text extraction**

In `tools/builder.py`, find the existing `style = await txt_loc.evaluate("""el => {` assignment inside the `for txt_index, txt_loc in enumerate(text_locators):` loop. Replace that full inline JavaScript evaluator with:

```python
style = await txt_loc.evaluate(TEXT_STYLE_JS)
```

Expected behavior: existing text manifest remains equivalent.

- [ ] **Step 3: Add group extraction after slide background setup**

Inside each slide loop, initialize:

```python
slide_info = {
    "index": slide_index,
    "texts": [],
    "components": [],
    "groups": [],
    "rasterFallbacks": [],
    "bg_path": str(workspace.assets_dir / f"slide_{slide_index}_bg.png")
}
```

Before capturing the slide background, hide group items that will be exported independently:

```python
group_locators = await slide_loc.locator("[data-ppt-group]").all()
for group_loc in group_locators:
    await group_loc.evaluate("""
        el => {
            for (const item of el.querySelectorAll('[data-ppt-item]')) {
                item.dataset.pptOriginalVisibility = item.style.visibility || '';
                item.style.visibility = 'hidden';
            }
        }
    """)
```

- [ ] **Step 4: Capture slide background without item visuals**

Keep the existing:

```python
await slide_loc.screenshot(path=slide_info["bg_path"])
```

Expected: item visuals are absent from background for item-aware groups.

- [ ] **Step 5: Extract groups and item rasters**

After background capture, restore item visibility and capture each item:

```python
for group_index, group_loc in enumerate(group_locators):
    group_box = await group_loc.bounding_box()
    if not group_box:
        slide_info["rasterFallbacks"].append({
            "id": f"group_{slide_index}_{group_index}",
            "reason": "zero-size-box",
            "mode": "slide-raster",
        })
        continue

    kind = await group_loc.get_attribute("data-ppt-group") or "unknown"
    await group_loc.evaluate("""
        el => {
            for (const item of el.querySelectorAll('[data-ppt-item]')) {
                item.style.visibility = item.dataset.pptOriginalVisibility || '';
                delete item.dataset.pptOriginalVisibility;
            }
        }
    """)

    item_locators = await group_loc.locator("[data-ppt-item]").all()
    items = []
    for item_index, item_loc in enumerate(item_locators):
        item_box = await item_loc.bounding_box()
        if not item_box:
            continue

        item_texts = []
        text_locators = await item_loc.locator("[data-ppt-text]").all()
        for text_index, item_text_loc in enumerate(text_locators):
            text_box = await item_text_loc.bounding_box()
            if not text_box:
                continue
            style = await item_text_loc.evaluate(TEXT_STYLE_JS)
            item_texts.append({
                "id": f"text_{slide_index}_{group_index}_{item_index}_{text_index}",
                "box": make_box(text_box, item_box),
                "style": style,
            })
            await item_text_loc.evaluate("el => el.style.visibility = 'hidden'")

        item_path = str(workspace.assets_dir / f"slide_{slide_index}_group_{group_index}_item_{item_index}.png")
        await item_loc.screenshot(path=item_path, omit_background=True)

        for item_text_loc in text_locators:
            await item_text_loc.evaluate("el => el.style.visibility = ''")

        items.append(make_item(
            slide_index=slide_index,
            group_index=group_index,
            item_index=item_index,
            box=make_box(item_box, slide_box),
            raster_path=item_path,
            texts=item_texts,
            bullets=[],
        ))

    slide_info["groups"].append(make_group(
        slide_index=slide_index,
        group_index=group_index,
        kind=kind,
        box=make_box(group_box, slide_box),
        items=items,
        segments=[],
    ))
```

- [ ] **Step 6: Skip legacy component capture for descendants of itemized groups**

When iterating `bg_locators`, skip elements inside a `data-ppt-group`:

```python
is_inside_group = await bg_loc.evaluate("el => Boolean(el.closest('[data-ppt-group]'))")
if is_inside_group:
    continue
```

Expected: item-aware group visuals are not duplicated as both component rasters and item rasters.

- [ ] **Step 7: Run tests**

Run:

```bash
pytest tests/test_item_manifest.py tests/test_pptx_exporter.py -v
```

Expected: all selected tests pass.

- [ ] **Step 8: Commit builder changes**

Run:

```bash
git add tools/builder.py
git commit -m "feat: extract item-aware slide groups"
```

Expected: commit succeeds.

## Task 4: Export Item Groups In PPTX

**Files:**
- Modify: `tools/pptx_exporter.py`
- Modify: `tests/test_pptx_exporter.py`

- [ ] **Step 1: Write failing exporter test**

Add this test to `tests/test_pptx_exporter.py`:

```python
def test_manifest_export_adds_item_raster_and_item_text(tmp_path):
    from PIL import Image

    item_img = tmp_path / "item.png"
    Image.new("RGBA", (400, 120), color=(20, 20, 20, 255)).save(str(item_img))

    manifest = write_manifest(
        tmp_path,
        [
            {
                "index": 0,
                "texts": [],
                "components": [],
                "groups": [
                    {
                        "id": "group_0_0",
                        "kind": "list",
                        "mode": "item-hybrid",
                        "box": {"x": 100, "y": 100, "width": 500, "height": 200},
                        "items": [
                            {
                                "id": "item_0_0_0",
                                "mode": "item-hybrid",
                                "box": {"x": 120, "y": 140, "width": 400, "height": 120},
                                "raster": {"path": str(item_img), "mode": "item"},
                                "texts": [
                                    {
                                        "box": {"x": 80, "y": 30, "width": 250, "height": 40},
                                        "style": {
                                            "text": "独立列表项",
                                            "fontSize": "24px",
                                            "fontFamily": "Inter, sans-serif",
                                            "color": "rgb(255,255,255)",
                                            "fontWeight": "700",
                                            "textAlign": "left",
                                        },
                                    }
                                ],
                                "bullets": [],
                            }
                        ],
                        "segments": [],
                    }
                ],
                "bg_path": None,
            }
        ],
    )

    output = str(tmp_path / "item_group.pptx")
    build_pptx(str(manifest), output)
    prs = Presentation(output)
    slide = prs.slides[0]
    all_text = " ".join(shape.text for shape in slide.shapes if shape.has_text_frame)
    assert "独立列表项" in all_text
    assert len(slide.shapes) >= 2
```

- [ ] **Step 2: Run test and verify failure**

Run:

```bash
pytest tests/test_pptx_exporter.py::test_manifest_export_adds_item_raster_and_item_text -v
```

Expected: FAIL because group item text is not exported yet.

- [ ] **Step 3: Extract text rendering helper in `pptx_exporter.py`**

Move the current text-box logic inside `for txt in slide_data.get("texts", [])` into a nested helper:

```python
def _add_text(slide, txt, offset_x=0, offset_y=0):
    box = txt["box"]
    style = txt["style"]
    text_content = style.get("text", "").strip()
    if not text_content:
        return
    x_emu = int((box["x"] + offset_x) * SCALE)
    y_emu = int((box["y"] + offset_y) * SCALE)
    h_emu = int(box["height"] * SCALE)
    raw_font_px = parse_px(style.get("fontSize", "16px"))
    exact_w_emu = int(box["width"] * SCALE)
    pad_v_px = parse_px(style.get("paddingTop", "0px")) + parse_px(style.get("paddingBottom", "0px"))
    content_h_emu = h_emu - int(pad_v_px * SCALE)
    is_singleline = content_h_emu <= int(raw_font_px * SCALE * 1.8)
    align_css = style.get("textAlign", "left")
    bg_color_str = style.get("backgroundColor", "")
    has_bg = not is_transparent_color(bg_color_str)
    if has_bg:
        bg_r, bg_g, bg_b = parse_rgb(bg_color_str)
        br_str = style.get("borderRadius", "0px")
        has_radius = br_str and br_str not in ("0px", "0%", "")
        shape_type = MSO_AUTO_SHAPE_TYPE.ROUNDED_RECTANGLE if has_radius else MSO_AUTO_SHAPE_TYPE.RECTANGLE
        bg_shape = slide.shapes.add_shape(shape_type, x_emu, y_emu, exact_w_emu, h_emu)
        bg_shape.fill.solid()
        bg_shape.fill.fore_color.rgb = RGBColor(bg_r, bg_g, bg_b)
        bg_shape.line.fill.background()
    if has_bg or not is_singleline:
        w_emu = exact_w_emu
        word_wrap = not is_singleline
    else:
        w_emu = exact_w_emu if align_css == "center" else min(int(exact_w_emu * 1.4), int(prs.slide_width) - x_emu)
        word_wrap = False
    tx_box = slide.shapes.add_textbox(x_emu, y_emu, w_emu, h_emu)
    tf = tx_box.text_frame
    tf.margin_top = int(parse_px(style.get("paddingTop", "0px")) * SCALE)
    tf.margin_bottom = int(parse_px(style.get("paddingBottom", "0px")) * SCALE)
    tf.margin_left = int(parse_px(style.get("paddingLeft", "0px")) * SCALE)
    tf.margin_right = int(parse_px(style.get("paddingRight", "0px")) * SCALE)
    tf.word_wrap = word_wrap
    if has_bg:
        tf.vertical_anchor = MSO_ANCHOR.MIDDLE
    runs_data = style.get("runs")
    if runs_data:
        paragraphs = []
        cur = []
        for run_item in runs_data:
            if run_item["text"] == "\n":
                paragraphs.append(cur)
                cur = []
            elif run_item["text"]:
                cur.append(run_item)
        if cur:
            paragraphs.append(cur)
        for para_idx, para_runs in enumerate(paragraphs):
            p = tf.paragraphs[0] if para_idx == 0 else tf.add_paragraph()
            p.alignment = _pptx_align(align_css)
            for run_item in para_runs:
                run = p.add_run()
                run.text = run_item["text"]
                _apply_run_style(run, run_item.get("style", {}), style)
    else:
        tf.text = text_content
        p = tf.paragraphs[0]
        p.alignment = _pptx_align(align_css)
        run = p.runs[0]
        _apply_run_style(run, style, style)
```

- [ ] **Step 4: Add item group rendering before slide-level text**

Insert after legacy components and before slide-level `texts`:

```python
for group in slide_data.get("groups", []):
    for segment in group.get("segments", []):
        raster = segment.get("raster", {})
        path = raster.get("path")
        box = segment.get("box")
        if path and box:
            slide.shapes.add_picture(path, int(box["x"] * SCALE), int(box["y"] * SCALE), int(box["width"] * SCALE), int(box["height"] * SCALE))

    for item in group.get("items", []):
        box = item["box"]
        raster = item.get("raster", {})
        path = raster.get("path")
        if path:
            slide.shapes.add_picture(path, int(box["x"] * SCALE), int(box["y"] * SCALE), int(box["width"] * SCALE), int(box["height"] * SCALE))
        for txt in item.get("texts", []):
            _add_text(slide, txt, offset_x=box["x"], offset_y=box["y"])
```

Then replace legacy slide text loop body with:

```python
for txt in slide_data.get("texts", []):
    _add_text(slide, txt)
```

- [ ] **Step 5: Run exporter tests**

Run:

```bash
pytest tests/test_pptx_exporter.py -v
```

Expected: all tests pass.

- [ ] **Step 6: Commit exporter changes**

Run:

```bash
git add tools/pptx_exporter.py tests/test_pptx_exporter.py
git commit -m "feat: export item-level pptx groups"
```

Expected: commit succeeds.

## Task 5: Validate Item-Aware Manifests

**Files:**
- Modify: `tools/quality_gate.py`
- Modify: `tests/test_quality_gate.py`

- [ ] **Step 1: Add failing validation test**

Add to `tests/test_quality_gate.py`:

```python
def test_quality_gate_rejects_empty_item_group(tmp_path):
    from tools.presentation_workspace import PresentationWorkspace
    from tools.quality_gate import validate_project

    project_dir = tmp_path / "project"
    slides_dir = project_dir / "slides"
    assets_dir = project_dir / "assets"
    slides_dir.mkdir(parents=True)
    assets_dir.mkdir()
    (slides_dir / "index.ts").write_text("export default []", encoding="utf-8")
    (slides_dir / "Slide_1.tsx").write_text(
        "export default function Slide(){ return <div data-ppt-slide data-ppt-text>Hi</div> }",
        encoding="utf-8",
    )
    manifest = project_dir / "layout_manifest.json"
    manifest.write_text(
        '{"slides":[{"index":0,"groups":[{"id":"group_0_0","kind":"list","items":[]}],"texts":[]}]}',
        encoding="utf-8",
    )
    workspace = PresentationWorkspace(
        project_id="project",
        project_dir=project_dir,
        slides_dir=slides_dir,
        assets_dir=assets_dir,
        manifest_path=manifest,
        pptx_path=project_dir / "presentation.pptx",
    )
    report = validate_project(workspace)
    assert not report.ok
    assert any("has no items" in error for error in report.errors)
```

- [ ] **Step 2: Run test and verify failure**

Run:

```bash
pytest tests/test_quality_gate.py::test_quality_gate_rejects_empty_item_group -v
```

Expected: FAIL because item groups are not validated.

- [ ] **Step 3: Add group validation**

In `_check_manifest_assets`, add:

```python
        for group in slide.get("groups", []):
            group_id = group.get("id", "unknown")
            if not group.get("items"):
                report.errors.append(f"item-aware group has no items: {group_id}")
            for item in group.get("items", []):
                raster_path = item.get("raster", {}).get("path")
                if raster_path and not _resolve_manifest_path(workspace, raster_path).exists():
                    report.errors.append(f"missing item raster referenced by manifest: {raster_path}")
                box = item.get("box", {})
                if box.get("width", 0) <= 0 or box.get("height", 0) <= 0:
                    report.errors.append(f"item has non-positive box: {item.get('id', 'unknown')}")
            for fallback in slide.get("rasterFallbacks", []):
                if fallback.get("mode") and not fallback.get("reason"):
                    report.errors.append(f"fallback missing reason: {fallback.get('id', 'unknown')}")
```

- [ ] **Step 4: Run quality gate tests**

Run:

```bash
pytest tests/test_quality_gate.py -v
```

Expected: all tests pass.

- [ ] **Step 5: Commit validation changes**

Run:

```bash
git add tools/quality_gate.py tests/test_quality_gate.py
git commit -m "test: validate item-aware ppt manifests"
```

Expected: commit succeeds.

## Task 6: Add Item-Aware Sample Slides

**Files:**
- Create: `web/src/sample-slides/Slide_3.tsx`
- Create: `web/src/sample-slides/Slide_4.tsx`
- Modify: `web/src/sample-slides/index.ts`

- [ ] **Step 1: Add a sample item-aware list slide**

Create `web/src/sample-slides/Slide_3.tsx` with:

```tsx
import { getDeckStylePreset, styleVars } from '../styles'

const items = [
  { id: 'a', title: 'Item-level capture', body: 'Each row can be copied or removed.' },
  { id: 'b', title: 'Native text overlay', body: 'Text remains editable when safe.' },
  { id: 'c', title: 'Visual fallback', body: 'Complex visuals remain rasterized.' },
]

export default function Slide_3() {
  const preset = getDeckStylePreset('aurora-borealis')
  return (
    <div
      className="w-[1920px] h-[1080px] bg-[var(--ppt-bg)] p-24"
      style={styleVars(preset)}
      data-ppt-slide="3"
    >
      <h2 data-ppt-text className="mb-12 text-6xl font-black text-[var(--ppt-text)]">
        Item-aware list
      </h2>
      <div data-ppt-group="list" className="space-y-5">
        {items.map((item) => (
          <div data-ppt-item key={item.id} className="relative rounded-3xl p-8">
            <div data-ppt-item-bg className="absolute inset-0 rounded-3xl bg-[var(--ppt-surface)] shadow-2xl" />
            <span data-ppt-bullet className="relative z-10 mr-5 inline-block h-4 w-4 rounded-full bg-[var(--ppt-secondary)]" />
            <h3 data-ppt-text className="relative z-10 text-3xl font-bold text-[var(--ppt-text)]">{item.title}</h3>
            <p data-ppt-text className="relative z-10 text-xl text-[var(--ppt-muted)]">{item.body}</p>
          </div>
        ))}
      </div>
    </div>
  )
}
```

- [ ] **Step 2: Add a sample item-aware timeline**

Create `web/src/sample-slides/Slide_4.tsx` with:

```tsx
import { getDeckStylePreset, styleVars } from '../styles'

const steps = [
  { id: 'one', title: 'Mark', body: 'Use group and item markers.' },
  { id: 'two', title: 'Slice', body: 'Capture each item independently.' },
  { id: 'three', title: 'Export', body: 'Place item rasters and native text.' },
]

export default function Slide_4() {
  const preset = getDeckStylePreset('aurora-borealis')
  return (
    <div
      className="w-[1920px] h-[1080px] bg-[var(--ppt-bg)] p-24"
      style={styleVars(preset)}
      data-ppt-slide="4"
    >
      <h2 data-ppt-text className="mb-24 text-6xl font-black text-[var(--ppt-text)]">
        Item-aware timeline
      </h2>
      <div data-ppt-group="timeline" className="relative grid grid-cols-3 gap-16">
        <div data-ppt-track className="absolute left-24 right-24 top-8 h-1 rounded-full bg-[var(--ppt-border)]" />
        {steps.map((step, index) => (
          <div data-ppt-item key={step.id} className="relative rounded-3xl p-8">
            {index > 0 && <div data-ppt-segment className="absolute -left-16 top-8 h-1 w-16 bg-[var(--ppt-secondary)]" />}
            <div data-ppt-bullet data-ppt-node className="relative z-10 mb-8 h-16 w-16 rounded-full bg-[var(--ppt-secondary)] shadow-2xl" />
            <div data-ppt-item-bg className="absolute inset-0 rounded-3xl bg-[var(--ppt-surface)] shadow-2xl" />
            <h3 data-ppt-text className="relative z-10 text-3xl font-bold text-[var(--ppt-text)]">{step.title}</h3>
            <p data-ppt-text className="relative z-10 text-xl text-[var(--ppt-muted)]">{step.body}</p>
          </div>
        ))}
      </div>
    </div>
  )
}
```

- [ ] **Step 3: Update sample slide exports**

Modify `web/src/sample-slides/index.ts`:

```ts
import Slide_1 from './Slide_1'
import Slide_2 from './Slide_2'
import Slide_3 from './Slide_3'
import Slide_4 from './Slide_4'

export default [Slide_1, Slide_2, Slide_3, Slide_4]
```

- [ ] **Step 4: Run frontend build**

Run from `web/`:

```bash
npm run build
```

Expected: build succeeds.

- [ ] **Step 5: Commit samples**

Run:

```bash
git add web/src/sample-slides
git commit -m "docs: add item-aware slide samples"
```

Expected: commit succeeds.

## Task 7: End-to-End Verification

**Files:**
- No required source changes unless verification finds bugs.

- [ ] **Step 1: Run Python tests**

Run:

```bash
pytest -v
```

Expected: all tests pass.

- [ ] **Step 2: Run frontend build**

Run:

```bash
cd web
npm run build
```

Expected: build succeeds.

- [ ] **Step 3: Generate a test project with item-aware sample slides**

Run:

```bash
python3 tools/ppt_workflow.py init --name "item hybrid verification" --project-id item-hybrid-verification
```

Expected: prints project id and project path.

- [ ] **Step 4: Copy sample slides into project**

Run:

```bash
mkdir -p output/projects/item-hybrid-verification/slides
cp web/src/sample-slides/Slide_*.tsx output/projects/item-hybrid-verification/slides/
cp web/src/sample-slides/index.ts output/projects/item-hybrid-verification/slides/index.ts
```

Expected: slides exist in the project workspace.

- [ ] **Step 5: Build PPTX**

Run:

```bash
python3 tools/ppt_workflow.py build --project item-hybrid-verification
```

Expected: `layout_manifest.json` includes `groups`, and `presentation.pptx` is non-empty.

- [ ] **Step 6: Inspect manifest**

Run:

```bash
python3 -c "import json; d=json.load(open('output/projects/item-hybrid-verification/layout_manifest.json')); print(sum(len(s.get('groups', [])) for s in d['slides']))"
```

Expected: prints a number greater than 0.

- [ ] **Step 7: Commit final fixes**

If verification required fixes, commit them:

```bash
git add .
git commit -m "fix: stabilize item hybrid pptx export"
```

Expected: commit succeeds or no changes remain.

## Self-Review

Spec coverage:

- High visual fidelity baseline: covered by Task 1 references, Task 3 background/item capture strategy, Task 5 validation, and Task 7 verification.
- Item-level list/timeline export: covered by Tasks 3, 4, and 6.
- Skill reference architecture: covered by Task 1.
- Slide coding rules API: covered by Task 1.
- Backward compatibility: covered by preserving legacy `bg_path`, `components`, and `texts`.
- Fallback reporting: covered by Tasks 3 and 5.

Placeholder scan:

- The plan contains no TBD/TODO placeholders.
- Commands and expected outcomes are explicit.

Type consistency:

- Manifest keys are consistently `groups`, `items`, `segments`, `rasterFallbacks`, `fallbackReason`, `mode`, `box`, `raster`, `texts`, and `bullets`.
- Marker names are consistently `data-ppt-group`, `data-ppt-item`, `data-ppt-item-bg`, `data-ppt-bullet`, `data-ppt-track`, and `data-ppt-segment`.
