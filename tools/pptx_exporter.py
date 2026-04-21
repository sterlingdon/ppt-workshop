import json
import math
import sys
from pptx import Presentation
from pptx.util import Inches, Pt, Emu
from pptx.enum.text import PP_ALIGN
from pptx.dml.color import RGBColor

def parse_px(px_str):
    if not px_str: return 0
    return float(px_str.replace("px", "").strip())

def _linear_to_srgb(c):
    c = max(0.0, min(1.0, c))
    if c <= 0.0031308:
        return c * 12.92
    return 1.055 * (c ** (1.0 / 2.4)) - 0.055

def oklab_to_rgb(L, a, b):
    """oklab(L a b) → (r, g, b) each 0-255."""
    l_ = L + 0.3963377774 * a + 0.2158037573 * b
    m_ = L - 0.1055613458 * a - 0.0638541728 * b
    s_ = L - 0.0894841775 * a - 1.2914855480 * b

    l = l_ ** 3
    m = m_ ** 3
    s = s_ ** 3

    r_lin =  4.0767416621 * l - 3.3077115913 * m + 0.2309699292 * s
    g_lin = -1.2684380046 * l + 2.6097574011 * m - 0.3413193965 * s
    b_lin = -0.0041960863 * l - 0.7034186147 * m + 1.7076147010 * s

    return (
        int(round(_linear_to_srgb(r_lin) * 255)),
        int(round(_linear_to_srgb(g_lin) * 255)),
        int(round(_linear_to_srgb(b_lin) * 255)),
    )

def oklch_to_rgb(L, C, H):
    """oklch(L C H) → (r, g, b) each 0-255."""
    h_rad = math.radians(H)
    return oklab_to_rgb(L, C * math.cos(h_rad), C * math.sin(h_rad))

def parse_rgb(color_str):
    """Parse any CSS color string → (r, g, b).  Defaults to white on failure."""
    if not color_str:
        return 255, 255, 255
    color_str = color_str.strip()

    # oklch(L C H [/ alpha])
    if color_str.startswith("oklch("):
        try:
            inner = color_str[6:].rstrip(")")
            if "/" in inner:
                inner, alpha_s = inner.split("/", 1)
                if float(alpha_s.strip()) < 0.05:
                    return 255, 255, 255  # near-transparent gradient text → white
            parts = inner.strip().split()
            return oklch_to_rgb(float(parts[0]), float(parts[1]), float(parts[2]))
        except Exception:
            return 255, 255, 255

    # oklab(L a b [/ alpha])
    if color_str.startswith("oklab("):
        try:
            inner = color_str[6:].rstrip(")")
            if "/" in inner:
                inner, alpha_s = inner.split("/", 1)
                if float(alpha_s.strip()) < 0.05:
                    return 240, 240, 240
            parts = inner.strip().split()
            return oklab_to_rgb(float(parts[0]), float(parts[1]), float(parts[2]))
        except Exception:
            return 255, 255, 255

    # rgb(...) / rgba(...)
    try:
        s = color_str.replace("rgb(", "").replace("rgba(", "").replace(")", "")
        parts = [float(p.strip()) for p in s.split(",")]
        if len(parts) == 4 and parts[3] < 0.05:
            return 255, 255, 255  # near-transparent = bg-clip-text gradient → pure white
        return int(parts[0]), int(parts[1]), int(parts[2])
    except Exception:
        return 255, 255, 255  # unknown format → white (safe on dark backgrounds)

# Maps CSS system-font aliases (unrecognised by PPT) to usable fallbacks
_SYSTEM_FONT_MAP = {
    "ui-sans-serif":     "Arial",
    "system-ui":         "Arial",
    "-apple-system":     "Arial",
    "BlinkMacSystemFont":"Arial",
    "ui-serif":          "Georgia",
    "ui-monospace":      "Consolas",
    "ui-rounded":        "Arial",
}

def clean_font_name(font_string):
    """'Inter', sans-serif  →  'Inter'.  System aliases  →  known PPT font."""
    try:
        first = font_string.split(",")[0].strip().strip("'").strip('"')
        return _SYSTEM_FONT_MAP.get(first, first) or "Arial"
    except Exception:
        return "Arial"

def build_pptx(manifest_path, output_path):
    print(f"[*] 读取构件化坐标清单: {manifest_path}")
    with open(manifest_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    prs = Presentation()
    prs.slide_width  = Emu(12192000)   # 13.333 in  (16:9)
    prs.slide_height = Emu(6858000)    # 7.5   in
    blank_layout = prs.slide_layouts[6]

    # CSS-pixel → EMU scale (viewport 1920 px maps to full slide width)
    SCALE = prs.slide_width / 1920     # ≈ 6350 EMU/px

    for slide_data in data.get("slides", []):
        idx = slide_data["index"] + 1
        print(f"[*] 正在编排幻灯片第 {idx} 页...")
        slide = prs.slides.add_slide(blank_layout)

        # ── 1. 全页底图 ──────────────────────────────────────────────
        bg_path = slide_data.get("bg_path")
        if bg_path:
            slide.shapes.add_picture(bg_path, 0, 0, prs.slide_width, prs.slide_height)

        # ── 2. 局部组件截图（GlassCard 等） ──────────────────────────
        for comp in slide_data.get("components", []):
            box = comp["box"]
            slide.shapes.add_picture(
                comp["path"],
                int(box["x"]      * SCALE),
                int(box["y"]      * SCALE),
                int(box["width"]  * SCALE),
                int(box["height"] * SCALE),
            )

        # ── 3. 原生可编辑文字层 ──────────────────────────────────────
        for txt in slide_data.get("texts", []):
            box   = txt["box"]
            style = txt["style"]
            text_content = style.get("text", "").strip()
            if not text_content:
                continue

            x_emu = int(box["x"]     * SCALE)
            y_emu = int(box["y"]     * SCALE)
            h_emu = int(box["height"]* SCALE)

            # Single-line detection: box height ≤ 1.8 × font-size
            # (1.8 covers normal line-height of 1.5 with a little headroom)
            raw_font_px   = parse_px(style.get("fontSize", "16px"))
            is_singleline = h_emu <= int(raw_font_px * SCALE * 1.8)
            align_css     = style.get("textAlign", "left")

            if is_singleline:
                # Center/right-aligned: keep original width so the alignment
                # anchor stays at the correct visual position.
                # Left/start-aligned: expand rightward 40 % to absorb font-
                # metric differences, but never past the slide's right edge.
                if align_css == "center":
                    w_emu = int(box["width"] * SCALE)
                else:
                    max_w = int(prs.slide_width) - x_emu
                    w_emu = min(int(box["width"] * SCALE * 1.4), max_w)
                word_wrap = False
            else:
                # Multi-line: the browser already determined the correct wrap
                # width; keep it so line breaks stay the same.
                w_emu     = int(box["width"] * SCALE)
                word_wrap = True

            tx_box = slide.shapes.add_textbox(x_emu, y_emu, w_emu, h_emu)
            tf = tx_box.text_frame
            tf.margin_top    = 0
            tf.margin_bottom = 0
            tf.margin_left   = 0
            tf.margin_right  = 0
            tf.word_wrap = word_wrap

            tf.text = text_content
            p   = tf.paragraphs[0]

            # Alignment
            if align_css == "center":
                p.alignment = PP_ALIGN.CENTER
            elif align_css == "right":
                p.alignment = PP_ALIGN.RIGHT
            else:
                p.alignment = PP_ALIGN.LEFT

            run = p.runs[0]

            # Font family (map CSS system aliases → known PPT fonts)
            run.font.name = clean_font_name(style.get("fontFamily", "Arial"))

            # Font size: CSS px → proportional pt for this slide canvas
            # SCALE (EMU/px) / 12700 (EMU/pt) = pt per px on this canvas
            pt_size = raw_font_px * SCALE / 12700
            run.font.size = Pt(int(round(pt_size)))

            # Color (handles rgb/rgba/oklch/oklab)
            r, g, b = parse_rgb(style.get("color", "rgb(255,255,255)"))
            run.font.color.rgb = RGBColor(r, g, b)

            # Bold
            fw = str(style.get("fontWeight", "400"))
            if fw >= "700" or fw == "bold":
                run.font.bold = True

    prs.save(output_path)
    print(f"[*] 转化完成！保存至: {output_path}")

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python pptx_exporter.py <manifest.json> <output.pptx>")
        sys.exit(1)
    build_pptx(sys.argv[1], sys.argv[2])
