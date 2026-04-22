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
    from .item_manifest import make_box, make_group, make_item
except ImportError:
    from presentation_workspace import create_project_workspace, get_project_workspace
    from item_manifest import make_box, make_group, make_item


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
                    "groups": [],
                    "rasterFallbacks": [],
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
                    style = await txt_loc.evaluate(TEXT_STYLE_JS)
                    is_inside_item = await txt_loc.evaluate("el => Boolean(el.closest('[data-ppt-item]'))")
                    if not is_inside_item:
                        slide_info["texts"].append({
                            "id": f"text_{slide_index}_{txt_index}",
                            "box": make_box(box, slide_box),
                            "style": style
                        })

                    # 关键动作：隐掉文本，防止印到底图标上。使用 visibility 保证它绝对不会留有颜色残影，且不破坏周围流式布局！
                    await txt_loc.evaluate("el => el.style.visibility = 'hidden'")

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

                # ------ STEP 2: 先截全页底图（含卡片 box-shadow）------
                # 必须在隐藏任何卡片之前截取，这样背景图里才能保留
                # shadow-2xl / ring 等渲染在元素包围盒外侧的阴影效果。
                # PPT 里：底图保留阴影 → 卡片覆层精确遮住卡片区域 → 阴影从两侧透出
                await slide_loc.screenshot(path=slide_info["bg_path"])

                # ------ STEP 2b: 提取 item-aware 组件组 -----------------
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
                        item_text_locators = await item_loc.locator("[data-ppt-text]").all()
                        for text_index, item_text_loc in enumerate(item_text_locators):
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

                        for item_text_loc in item_text_locators:
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

                # ------ STEP 3: 提取局部组件截图并隐身 ------
                bg_locators = await slide_loc.locator("[data-ppt-bg]").all()
                for bg_index, bg_loc in enumerate(bg_locators):
                    is_inside_group = await bg_loc.evaluate("el => Boolean(el.closest('[data-ppt-group]'))")
                    if is_inside_group:
                        continue

                    box = await bg_loc.bounding_box()
                    if not box:
                        continue

                    comp_path = str(workspace.assets_dir / f"slide_{slide_index}_comp_{bg_index}.png")
                    await bg_loc.screenshot(path=comp_path, omit_background=True)

                    slide_info["components"].append({
                        "id": f"comp_{slide_index}_{bg_index}",
                        "box": make_box(box, slide_box),
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
