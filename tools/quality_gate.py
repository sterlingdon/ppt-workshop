"""Structural quality gates for generated PPT projects."""
from __future__ import annotations

from dataclasses import dataclass, field
import json
from pathlib import Path
import re

try:
    from .html_exporter import validate_static_html_output
    from .presentation_workspace import PresentationWorkspace
except ImportError:
    from html_exporter import validate_static_html_output
    from presentation_workspace import PresentationWorkspace


@dataclass
class QualityReport:
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.errors


def _check_slide_sources(workspace: PresentationWorkspace, report: QualityReport) -> None:
    if not workspace.project_dir.is_dir():
        report.errors.append(f"project workspace does not exist: {workspace.project_dir}")
        return
    if not workspace.slides_dir.is_dir():
        report.errors.append(f"slides directory does not exist: {workspace.slides_dir}")
        return
    if not (workspace.slides_dir / "index.ts").is_file():
        report.errors.append(f"slides directory must contain index.ts: {workspace.slides_dir}")

    slide_files = sorted(workspace.slides_dir.glob("Slide_*.tsx"))
    if not slide_files:
        report.errors.append(f"slides directory must contain Slide_*.tsx files: {workspace.slides_dir}")
        return

    index_content = (workspace.slides_dir / "index.ts").read_text(encoding="utf-8") if (workspace.slides_dir / "index.ts").is_file() else ""
    imported_slides = set(re.findall(r"import\s+(Slide_\d+)\s+from\s+['\"]\.\/Slide_\d+['\"]", index_content))
    export_match = re.search(r"export\s+default\s+\[(.*?)\]", index_content, re.DOTALL)
    exported_slides = set(re.findall(r"\bSlide_\d+\b", export_match.group(1))) if export_match else set()

    has_text_marker = False
    slide_stems = {slide_file.stem for slide_file in slide_files}
    for slide_file in slide_files:
        content = slide_file.read_text(encoding="utf-8")
        if "data-ppt-slide" not in content:
            report.errors.append(f"{slide_file.name} missing data-ppt-slide marker")
        if "data-ppt-text" in content:
            has_text_marker = True
        if "var(--ppt-" not in content:
            report.errors.append(f"{slide_file.name} must use --ppt-* variables from design_dna.json.theme_tokens")
        if "../../../web/src/styles" in content or "web/src/styles" in content:
            report.errors.append(f"{slide_file.name} imports renderer styles through web/src; use design_dna.json.theme_tokens directly")
        if "from '../styles'" in content or 'from "../styles"' in content:
            report.errors.append(f"{slide_file.name} imports styles from ../styles; generated project slides should use ../../styles")
        _check_marker_nesting(slide_file, content, report)
        if slide_file.stem not in imported_slides:
            report.errors.append(f"index.ts must import {slide_file.stem}")
        if export_match and slide_file.stem not in exported_slides:
            report.errors.append(f"index.ts must export {slide_file.stem}")

    if not has_text_marker:
        report.errors.append("deck must contain at least one data-ppt-text marker")
    if index_content and not export_match:
        report.errors.append("index.ts must export default an ordered slide array")
    for imported in sorted(imported_slides - slide_stems):
        report.errors.append(f"index.ts imports missing slide file: {imported}.tsx")
    for exported in sorted(exported_slides - slide_stems):
        report.errors.append(f"index.ts exports missing slide file: {exported}.tsx")


TAG_RE = re.compile(r"<(/?)([A-Za-z][\w.]*)\b([^<>]*?)(/?)>", re.DOTALL)


def _has_marker(attrs: str, marker: str) -> bool:
    return re.search(rf"(?<![\w-]){re.escape(marker)}(?![\w-])(?:\s*=\s*{{?['\"][^'\"]*['\"]}}?)?", attrs) is not None


def _check_marker_nesting(slide_file: Path, content: str, report: QualityReport) -> None:
    marker_stack: list[tuple[str, set[str]]] = []

    for match in TAG_RE.finditer(content):
        closing, tag_name, attrs, self_closing = match.groups()
        if closing:
            for index in range(len(marker_stack) - 1, -1, -1):
                if marker_stack[index][0] == tag_name:
                    del marker_stack[index:]
                    break
            continue

        markers = {
            marker
            for marker in ("data-ppt-group", "data-ppt-item")
            if _has_marker(attrs, marker)
        }
        if not markers:
            continue

        ancestor_item = any("data-ppt-item" in ancestor_markers for _, ancestor_markers in marker_stack)
        if ancestor_item:
            if "data-ppt-group" in markers:
                report.errors.append(
                    f"{slide_file.name} has nested data-ppt-group inside data-ppt-item; "
                    "keep each repeatable card/row as a single top-level item or use raster fallback"
                )
            if "data-ppt-item" in markers:
                report.errors.append(
                    f"{slide_file.name} has nested data-ppt-item inside data-ppt-item; "
                    "do not mark list rows inside an already itemized card"
                )

        ancestor_group = any("data-ppt-group" in ancestor_markers for _, ancestor_markers in marker_stack)
        if ancestor_group and "data-ppt-group" in markers:
            report.errors.append(
                f"{slide_file.name} has nested data-ppt-group inside data-ppt-group; "
                "use one group boundary per repeatable structure"
            )

        if not self_closing:
            marker_stack.append((tag_name, markers))


def _load_json(path: Path, report: QualityReport, label: str) -> dict | None:
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        report.errors.append(f"{label} is not valid JSON: {exc}")
        return None


def _blocking_count(data: dict) -> int:
    value = data.get("blocking_findings", 0)
    if isinstance(value, int):
        return value
    if isinstance(value, list):
        return len(value)
    return 0


def _open_log_items(data: dict, field: str) -> list[dict]:
    items = data.get(field, [])
    if not isinstance(items, list):
        return []
    return [item for item in items if isinstance(item, dict) and item.get("status") != "resolved"]


def _resolve_project_path(workspace: PresentationWorkspace, raw_path: str) -> Path:
    path = Path(raw_path)
    if path.is_absolute():
        return path
    return workspace.project_dir / path


def _check_visual_review_capability(
    workspace: PresentationWorkspace,
    visual_report: dict,
    report: QualityReport,
    require_agent_reports: bool,
) -> None:
    if visual_report.get("status") != "pass":
        return

    capability = visual_report.get("review_capability")
    if not isinstance(capability, dict):
        report.errors.append("visual_review_report.json must record review_capability for a passing AI visual gate")
        return

    method = capability.get("method")
    allowed_methods = {"vision_model", "human_visual_review"}
    if method not in allowed_methods:
        report.errors.append(
            "visual_review_report.json review_capability.method must be vision_model or human_visual_review"
        )

    if method == "vision_model" and capability.get("image_input") is not True:
        report.errors.append("visual_review_report.json vision_model review_capability must set image_input true")

    inspected_assets = capability.get("inspected_assets", [])
    if not isinstance(inspected_assets, list) or not inspected_assets:
        report.errors.append("visual_review_report.json review_capability.inspected_assets must list reviewed screenshots")
        return

    for asset in inspected_assets:
        if not isinstance(asset, str) or not asset.strip():
            report.errors.append("visual_review_report.json review_capability.inspected_assets contains an invalid path")
            continue
        if not _resolve_project_path(workspace, asset).is_file():
            report.errors.append(f"visual review inspected asset does not exist: {asset}")


def _check_agent_reports(workspace: PresentationWorkspace, report: QualityReport, require_agent_reports: bool = False) -> None:
    content_report = _load_json(workspace.project_dir / "content_quality_report.json", report, "content_quality_report.json")
    if require_agent_reports and content_report is None:
        report.errors.append("missing required content_quality_report.json; run the Content Quality Auditor before build")
    if content_report:
        status = content_report.get("status")
        blocking = _blocking_count(content_report)
        if not status and require_agent_reports:
            report.errors.append("content_quality_report.json missing required status field")
        if status and status != "pass":
            report.errors.append(f"content_quality_report.json status is {status}; resolve required revisions before continuing")
        if blocking > 0:
            report.errors.append(f"content_quality_report.json has {blocking} blocking findings")
        if content_report.get("required_revisions"):
            report.errors.append("content_quality_report.json has unresolved required revisions")
        if _open_log_items(content_report, "resolution_log"):
            report.errors.append("content_quality_report.json has unresolved resolution log items")

    visual_report = _load_json(workspace.project_dir / "visual_review_report.json", report, "visual_review_report.json")
    if require_agent_reports and visual_report is None:
        report.errors.append("missing required visual_review_report.json; run AI Lens Review before build")
    if visual_report:
        status = visual_report.get("status")
        blocking = _blocking_count(visual_report)
        if not status and require_agent_reports:
            report.errors.append("visual_review_report.json missing required status field")
        if visual_report.get("review_type") and visual_report.get("review_type") != "ai_lens_visual_review":
            report.errors.append("visual_review_report.json review_type must be ai_lens_visual_review")
        if status and status != "pass":
            report.errors.append(f"visual_review_report.json status is {status}; AI visual review is not approved")
        if blocking > 0:
            report.errors.append(f"visual_review_report.json has {blocking} blocking findings")
        failed_slides = [slide for slide in visual_report.get("slides", []) if isinstance(slide, dict) and not slide.get("passed", False)]
        if failed_slides:
            report.errors.append("visual_review_report.json has slides not passed")
        if _open_log_items(visual_report, "repair_log"):
            report.errors.append("visual_review_report.json has unresolved repair log items")
        _check_visual_review_capability(workspace, visual_report, report, require_agent_reports)


def _resolve_manifest_path(workspace: PresentationWorkspace, raw_path: str) -> Path:
    path = Path(raw_path)
    if path.is_absolute():
        return path
    candidate = workspace.manifest_path.parent / path
    if candidate.exists():
        return candidate
    return path


def _check_manifest_assets(workspace: PresentationWorkspace, report: QualityReport) -> None:
    if not workspace.manifest_path.exists():
        return
    try:
        data = json.loads(workspace.manifest_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        report.errors.append(f"layout manifest is not valid JSON: {exc}")
        return

    slides = data.get("slides", [])
    if not slides:
        report.errors.append(f"manifest contains no slides: {workspace.manifest_path}")

    for slide in slides:
        bg_path = slide.get("bg_path")
        if bg_path and not _resolve_manifest_path(workspace, bg_path).exists():
            report.errors.append(f"missing asset referenced by manifest: {bg_path}")
        for component in slide.get("components", []):
            comp_path = component.get("path")
            if comp_path and not _resolve_manifest_path(workspace, comp_path).exists():
                report.errors.append(f"missing asset referenced by manifest: {comp_path}")
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


def _check_pptx(workspace: PresentationWorkspace, report: QualityReport) -> None:
    if workspace.pptx_path.exists() and workspace.pptx_path.stat().st_size == 0:
        report.errors.append(f"presentation.pptx exists but is empty: {workspace.pptx_path}")


def _check_html_presentation(workspace: PresentationWorkspace, report: QualityReport) -> None:
    if not workspace.html_dir.exists():
        return
    try:
        validate_static_html_output(workspace.html_dir)
    except RuntimeError as exc:
        report.errors.append(str(exc))


def validate_project(
    workspace: PresentationWorkspace,
    check_outputs: bool = True,
    require_agent_reports: bool = False,
) -> QualityReport:
    report = QualityReport()
    _check_slide_sources(workspace, report)
    _check_agent_reports(workspace, report, require_agent_reports=require_agent_reports)
    if check_outputs:
        _check_manifest_assets(workspace, report)
        _check_pptx(workspace, report)
        _check_html_presentation(workspace, report)
    return report
