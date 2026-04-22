from __future__ import annotations

import asyncio
from collections import Counter
from dataclasses import dataclass, field
import json
from pathlib import Path

from playwright.async_api import async_playwright

try:
    from .deck_sources import activate_project_slides
    from .preview_server import managed_preview_server
    from .presentation_workspace import PresentationWorkspace, get_project_workspace
except ImportError:
    from deck_sources import activate_project_slides
    from preview_server import managed_preview_server
    from presentation_workspace import PresentationWorkspace, get_project_workspace


@dataclass
class VisualSlideFinding:
    slide: int
    expected_texts: list[str] = field(default_factory=list)
    rendered_texts: list[str] = field(default_factory=list)
    missing_texts: list[str] = field(default_factory=list)
    hidden_texts: list[str] = field(default_factory=list)
    clipped_texts: list[str] = field(default_factory=list)
    covered_texts: list[str] = field(default_factory=list)
    content_overflow_px: int = 0
    suggestions: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not (
            self.missing_texts
            or self.hidden_texts
            or self.clipped_texts
            or self.covered_texts
            or self.content_overflow_px > 0
        )


@dataclass
class VisualValidationReport:
    project_id: str
    validation_time: str
    preview_url: str
    slides: list[dict]
    summary: dict
    gate_type: str = "engineering_render_validation"
    note: str = "Checks rendered text visibility, clipping, coverage, and overflow only. AI visual review is still required."

    @property
    def ok(self) -> bool:
        return self.summary.get("failed", 0) == 0


def _manifest_slide_texts(slide: dict) -> list[str]:
    texts: list[str] = []

    def walk(node: dict) -> None:
        for text in node.get("texts", []) or []:
            value = str(text.get("style", {}).get("text") or "").strip()
            if value:
                texts.append(value)
        for group in node.get("groups", []) or []:
            for item in group.get("items", []) or []:
                walk(item)

    walk(slide)
    return texts


def _normalize_text(value: str) -> str:
    return " ".join(value.split())


def _build_suggestions(finding: VisualSlideFinding) -> list[str]:
    suggestions: list[str] = []

    if finding.missing_texts:
        suggestions.append(
            f"Slide {finding.slide}: HTML preview is missing expected text: {', '.join(finding.missing_texts[:3])}. "
            "Check for clipped headings, hidden overlays, or accidental display/visibility rules."
        )
    if finding.hidden_texts:
        suggestions.append(
            f"Slide {finding.slide}: some exported text nodes exist but are hidden in HTML: {', '.join(finding.hidden_texts[:3])}. "
            "Remove the accidental hidden style or move the element out from under the overlay."
        )
    if finding.clipped_texts:
        suggestions.append(
            f"Slide {finding.slide}: some text is clipped by the slide frame: {', '.join(finding.clipped_texts[:3])}. "
            "Move it inside the 1920x1080 canvas or reduce the surrounding overflow-hidden region."
        )
    if finding.covered_texts:
        suggestions.append(
            f"Slide {finding.slide}: some text is covered by another element: {', '.join(finding.covered_texts[:3])}. "
            "Lower the background layer or raise the text element with a safer stacking order."
        )

    return suggestions


def _load_manifest(workspace: PresentationWorkspace) -> list[dict]:
    if not workspace.manifest_path.exists():
        return []
    with workspace.manifest_path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    return list(data.get("slides", []) or [])


async def _inspect_slide(slide_locator) -> dict:
    return await slide_locator.evaluate(
        """
        (slide) => {
          if (!slide) {
            return { exists: false, texts: [] };
          }

          const slideRect = slide.getBoundingClientRect();
          let maxOverflow = 0;
          let contentBottom = slideRect.bottom;
          for (const el of slide.querySelectorAll('*')) {
            const rect = el.getBoundingClientRect();
            contentBottom = Math.max(contentBottom, rect.bottom);
            const overflow = rect.bottom - slideRect.bottom;
            if (overflow > 0) {
              maxOverflow = Math.max(maxOverflow, overflow);
            }
          }

          const texts = Array.from(slide.querySelectorAll('[data-ppt-text]')).map((el) => {
            const rect = el.getBoundingClientRect();
            const style = window.getComputedStyle(el);
            const centerX = rect.left + rect.width / 2;
            const centerY = rect.top + rect.height / 2;
            const topEl = Number.isFinite(centerX) && Number.isFinite(centerY)
              ? document.elementFromPoint(centerX, centerY)
              : null;
            const clipped = rect.width > 0 && rect.height > 0 && (
              rect.left < slideRect.left - 1 ||
              rect.right > slideRect.right + 1 ||
              rect.top < slideRect.top - 1 ||
              rect.bottom > slideRect.bottom + 1
            );
            const hidden = style.display === 'none' || style.visibility === 'hidden' || Number(style.opacity) === 0 || rect.width === 0 || rect.height === 0;
            const covered = !!topEl && topEl !== el && !el.contains(topEl);

            return {
              text: (el.innerText || el.textContent || '').trim(),
              x: Math.round(rect.left),
              y: Math.round(rect.top),
              width: Math.round(rect.width),
              height: Math.round(rect.height),
              hidden,
              clipped,
              covered,
              topTag: topEl ? topEl.tagName : null,
            };
          });

          return {
            exists: true,
            slide: {
              x: Math.round(slideRect.left),
              y: Math.round(slideRect.top),
              width: Math.round(slideRect.width),
              height: Math.round(slideRect.height),
            },
            contentOverflowPx: Math.round(contentBottom - slideRect.bottom),
            maxOverflowPx: Math.round(maxOverflow),
            texts,
          };
        }
        """
    )


async def validate_visual_project(
    workspace: PresentationWorkspace,
    web_dir: str | Path = "web",
    port: int = 5173,
    headless: bool = True,
) -> VisualValidationReport:
    activate_project_slides(workspace)
    manifest_slides = _load_manifest(workspace)
    slide_files = sorted(workspace.slides_dir.glob("Slide_*.tsx"))

    findings: list[VisualSlideFinding] = []
    preview_url = f"http://127.0.0.1:{port}"

    with managed_preview_server(web_dir, port=port) as server:
        preview_url = server.url
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=headless)
            context = await browser.new_context(device_scale_factor=1.0)
            page = await context.new_page()
            await page.set_viewport_size({"width": 1920, "height": 1080})
            await page.goto(f"{server.url}/?extract=1")
            await page.wait_for_timeout(1000)

            total_slides = max(len(slide_files), len(manifest_slides))
            rendered_slide_count = await page.locator("[data-ppt-slide]").count()
            for index in range(total_slides):
                if index >= rendered_slide_count:
                    findings.append(
                        VisualSlideFinding(
                            slide=index + 1,
                            suggestions=[f"Slide {index + 1}: HTML preview did not render a slide root."],
                        )
                    )
                    continue

                slide_locator = page.locator("[data-ppt-slide]").nth(index)

                snapshot = await _inspect_slide(slide_locator)
                if not snapshot.get("exists"):
                    findings.append(
                        VisualSlideFinding(
                            slide=index + 1,
                            suggestions=[f"Slide {index + 1}: HTML preview did not render a slide root."],
                        )
                    )
                    continue

                expected_texts = _manifest_slide_texts(manifest_slides[index]) if index < len(manifest_slides) else []
                rendered_texts = [str(node.get("text") or "") for node in snapshot["texts"] if str(node.get("text") or "").strip()]

                expected_counts = Counter(_normalize_text(text) for text in expected_texts if _normalize_text(text))
                rendered_counts = Counter(_normalize_text(text) for text in rendered_texts if _normalize_text(text))
                missing_texts: list[str] = []
                for text, count in expected_counts.items():
                    if rendered_counts[text] < count:
                        missing_texts.extend([text] * (count - rendered_counts[text]))

                hidden_texts = [node["text"] for node in snapshot["texts"] if node["hidden"] and node["text"]]
                clipped_texts = [node["text"] for node in snapshot["texts"] if node["clipped"] and node["text"]]
                covered_texts = [node["text"] for node in snapshot["texts"] if node["covered"] and node["text"]]
                overflow_px = int(snapshot.get("contentOverflowPx") or 0)

                finding = VisualSlideFinding(
                    slide=index + 1,
                    expected_texts=expected_texts,
                    rendered_texts=rendered_texts,
                    missing_texts=missing_texts,
                    hidden_texts=hidden_texts,
                    clipped_texts=clipped_texts,
                    covered_texts=covered_texts,
                    content_overflow_px=overflow_px,
                )
                finding.suggestions = _build_suggestions(finding)
                if overflow_px > 0:
                    finding.suggestions.append(
                        f"Slide {index + 1}: content overflows the 1080px slide boundary by {overflow_px}px. "
                        "Reduce padding, gaps, or element height until the full slide fits."
                    )
                findings.append(finding)

            await browser.close()

    slides = [
        {
            "slide": finding.slide,
            "expected_texts": finding.expected_texts,
            "rendered_texts": finding.rendered_texts,
            "missing_texts": finding.missing_texts,
            "hidden_texts": finding.hidden_texts,
            "clipped_texts": finding.clipped_texts,
            "covered_texts": finding.covered_texts,
            "content_overflow_px": finding.content_overflow_px,
            "suggestions": finding.suggestions,
            "passed": finding.ok,
        }
        for finding in findings
    ]

    summary = {
        "total": len(slides),
        "passed": sum(1 for slide in slides if slide["passed"]),
        "failed": sum(1 for slide in slides if not slide["passed"]),
    }

    return VisualValidationReport(
        project_id=workspace.project_id,
        validation_time="2026-04-22",
        preview_url=preview_url,
        slides=slides,
        summary=summary,
    )


async def capture_review_screenshots(
    workspace: PresentationWorkspace,
    web_dir: str | Path = "web",
    port: int = 5173,
    headless: bool = True,
) -> dict:
    """Render the active deck and write screenshots for AI visual review."""
    activate_project_slides(workspace)
    review_dir = workspace.project_dir / "review"
    slide_dir = review_dir / "slides"
    slide_dir.mkdir(parents=True, exist_ok=True)

    full_deck_path = review_dir / "full_deck.png"
    slide_paths: list[str] = []

    with managed_preview_server(web_dir, port=port) as server:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=headless)
            context = await browser.new_context(device_scale_factor=1.0)
            page = await context.new_page()
            await page.set_viewport_size({"width": 1920, "height": 1080})
            await page.goto(f"{server.url}/?extract=1")
            await page.wait_for_timeout(1000)
            await page.screenshot(path=str(full_deck_path), full_page=True)

            slides = page.locator("[data-ppt-slide]")
            slide_count = await slides.count()
            for index in range(slide_count):
                path = slide_dir / f"slide_{index + 1:02d}.png"
                await slides.nth(index).screenshot(path=str(path))
                slide_paths.append(str(path))

            await browser.close()

    return {
        "full_deck_screenshot": str(full_deck_path),
        "slide_screenshots": slide_paths,
    }


def write_visual_report(workspace: PresentationWorkspace, report: VisualValidationReport) -> None:
    payload = {
        "project_id": report.project_id,
        "gate_type": report.gate_type,
        "note": report.note,
        "validation_time": report.validation_time,
        "preview_url": report.preview_url,
        "slides": report.slides,
        "summary": report.summary,
    }
    workspace.metadata_path.parent.mkdir(parents=True, exist_ok=True)
    with workspace.project_dir.joinpath("visual_validation_report.json").open("w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)


def run_visual_validation(
    workspace: PresentationWorkspace,
    web_dir: str | Path = "web",
    port: int = 5173,
    headless: bool = True,
) -> VisualValidationReport:
    return asyncio.run(validate_visual_project(workspace, web_dir=web_dir, port=port, headless=headless))


def resolve_workspace(project_id: str, project_root: str | Path = "output/projects") -> PresentationWorkspace:
    return get_project_workspace(project_id, root_dir=project_root)
