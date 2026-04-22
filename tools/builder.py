import asyncio
import argparse
import json
import os
import signal
import subprocess
import time
from playwright.async_api import async_playwright

try:
    from .presentation_workspace import create_project_workspace, get_project_workspace
except ImportError:
    from presentation_workspace import create_project_workspace, get_project_workspace

async def extract_layout_and_assets(web_dir="web", workspace=None, port=5173):
    if workspace is None:
        workspace = create_project_workspace("presentation")

    # 确保输出目录存在
    workspace.assets_dir.mkdir(parents=True, exist_ok=True)

    # 隐式拉起 Vite 服务
    print(">>> [Phase 1] 正在启动 Vite 渲染器...")
    vite_process = subprocess.Popen(
        ["npm", "run", "dev", "--", "--port", str(port)],
        cwd=str(web_dir),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        start_new_session=True,  # new process group → killpg cleans up all Vite children
    )

    # 给 Vite 几秒钟启动时间
    time.sleep(3)

    try:
        async with async_playwright() as p:
            print(">>> [Phase 2] 无头浏览器就绪，开始解剖提取！")
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(device_scale_factor=2.0)
            page = await context.new_page()

            # 定制 1920x1080 标准 PPT 规格
            await page.set_viewport_size({"width": 1920, "height": 1080})
            await page.goto(f"http://localhost:{port}/?extract=1")

            # 等待所有框架渲染完成
            await page.wait_for_timeout(2000)

            slides_data = []

            # 获取所有打上 [data-ppt-slide] 的主幻灯片节点
            slide_locators = await page.locator("[data-ppt-slide]").all()
            for slide_index, slide_loc in enumerate(slide_locators):
                print(f"  > 正在解剖第 {slide_index + 1} 张幻灯片...")

                # 滚动到幻灯片位置确保视口可见
                await slide_loc.scroll_into_view_if_needed()
                slide_box = await slide_loc.bounding_box()
                if not slide_box:
                    continue

                slide_info = {
                    "index": slide_index,
                    "texts": [],
                    "components": [],
                    "bg_path": str(workspace.assets_dir / f"slide_{slide_index}_bg.png")
                }

                # ------ STEP 1: 提取所有原生文本并隐身 ------
                text_locators = await slide_loc.locator("[data-ppt-text]").all()
                for txt_index, txt_loc in enumerate(text_locators):
                    # 获取计算样式和坐标
                    box = await txt_loc.bounding_box()
                    if not box:
                        continue

                    # 计算相对于当前 Slide 容器的坐标，彻底无视视口滚动或边距偏差
                    rel_box = {
                        "x": box["x"] - slide_box["x"],
                        "y": box["y"] - slide_box["y"],
                        "width": box["width"],
                        "height": box["height"]
                    }

                    style = await txt_loc.evaluate("""el => {
                        const s = window.getComputedStyle(el);

                        // Walk the DOM tree to collect per-run styles (handles <br> and <span> color/weight overrides)
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
                                    color:              cs.color,
                                    fontWeight:         cs.fontWeight,
                                    fontSize:           cs.fontSize,
                                    fontFamily:         cs.fontFamily,
                                    fontStyle:          cs.fontStyle,
                                    textDecorationLine: cs.textDecorationLine,
                                };
                                for (const c of node.childNodes) walk(c, cur);
                            }
                        }
                        const rootRun = {
                            color:              s.color,
                            fontWeight:         s.fontWeight,
                            fontSize:           s.fontSize,
                            fontFamily:         s.fontFamily,
                            fontStyle:          s.fontStyle,
                            textDecorationLine: s.textDecorationLine,
                        };
                        for (const c of el.childNodes) walk(c, rootRun);

                        return {
                            fontSize:           s.fontSize,
                            fontFamily:         s.fontFamily,
                            color:              s.color,
                            fontWeight:         s.fontWeight,
                            textAlign:          s.textAlign,
                            text:               runs.map(r => r.text).join('') || el.innerText,
                            backgroundColor:    s.backgroundColor,
                            borderRadius:       s.borderRadius,
                            paddingTop:         s.paddingTop,
                            paddingBottom:      s.paddingBottom,
                            paddingLeft:        s.paddingLeft,
                            paddingRight:       s.paddingRight,
                            runs:               runs.length > 0 ? runs : null,
                        };
                    }""")

                    slide_info["texts"].append({
                        "id": f"text_{slide_index}_{txt_index}",
                        "box": rel_box,
                        "style": style
                    })

                    # 关键动作：隐掉文本，防止印到底图标上。使用 visibility 保证它绝对不会留有颜色残影，且不破坏周围流式布局！
                    await txt_loc.evaluate("el => el.style.visibility = 'hidden'")

                # ------ STEP 2: 先截全页底图（含卡片 box-shadow）------
                # 必须在隐藏任何卡片之前截取，这样背景图里才能保留
                # shadow-2xl / ring 等渲染在元素包围盒外侧的阴影效果。
                # PPT 里：底图保留阴影 → 卡片覆层精确遮住卡片区域 → 阴影从两侧透出
                await slide_loc.screenshot(path=slide_info["bg_path"])

                # ------ STEP 3: 提取局部组件截图并隐身 ------
                bg_locators = await slide_loc.locator("[data-ppt-bg]").all()
                for bg_index, bg_loc in enumerate(bg_locators):
                    box = await bg_loc.bounding_box()
                    if not box:
                        continue

                    rel_box = {
                        "x": box["x"] - slide_box["x"],
                        "y": box["y"] - slide_box["y"],
                        "width": box["width"],
                        "height": box["height"]
                    }

                    comp_path = str(workspace.assets_dir / f"slide_{slide_index}_comp_{bg_index}.png")
                    await bg_loc.screenshot(path=comp_path, omit_background=True)

                    slide_info["components"].append({
                        "id": f"comp_{slide_index}_{bg_index}",
                        "box": rel_box,
                        "path": comp_path
                    })

                    await bg_loc.evaluate("el => el.style.opacity = '0'")

                slides_data.append(slide_info)

            await browser.close()

            with open(workspace.manifest_path, "w", encoding="utf-8") as f:
                json.dump({"slides": slides_data}, f, indent=4, ensure_ascii=False)

            print(f">>> [Phase 3] 提取成功，布局清单写入 {workspace.manifest_path}")

    finally:
        # Kill the process group so Vite's forked child processes are cleaned up too
        try:
            os.killpg(os.getpgid(vite_process.pid), signal.SIGTERM)
        except Exception:
            vite_process.terminate()
        try:
            vite_process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            try:
                os.killpg(os.getpgid(vite_process.pid), signal.SIGKILL)
            except Exception:
                vite_process.kill()
            vite_process.wait(timeout=5)


def parse_args():
    parser = argparse.ArgumentParser(description="Extract React slide layout into a PPT manifest.")
    parser.add_argument("--project", help="Existing project id under output/projects")
    parser.add_argument("--name", default="presentation", help="Presentation project name for new workspace")
    parser.add_argument("--project-root", default="output/projects", help="Directory that stores generated projects")
    parser.add_argument("--web-dir", default="web", help="React renderer directory")
    parser.add_argument("--port", type=int, default=5173, help="Vite dev server port")
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    workspace = (
        get_project_workspace(args.project, root_dir=args.project_root)
        if args.project
        else create_project_workspace(args.name, root_dir=args.project_root)
    )
    workspace.assets_dir.mkdir(parents=True, exist_ok=True)
    asyncio.run(extract_layout_and_assets(args.web_dir, workspace=workspace, port=args.port))
