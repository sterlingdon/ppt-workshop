"""Structural quality gates for generated PPT projects."""
from __future__ import annotations

from dataclasses import dataclass, field
import json
from pathlib import Path

try:
    from .presentation_workspace import PresentationWorkspace
except ImportError:
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

    has_text_marker = False
    for slide_file in slide_files:
        content = slide_file.read_text(encoding="utf-8")
        if "data-ppt-slide" not in content:
            report.errors.append(f"{slide_file.name} missing data-ppt-slide marker")
        if "data-ppt-text" in content:
            has_text_marker = True
        if "getDeckStylePreset" not in content and "var(--ppt-" not in content:
            report.errors.append(f"{slide_file.name} must use a style preset or --ppt-* variables")

    if not has_text_marker:
        report.errors.append("deck must contain at least one data-ppt-text marker")


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

    for slide in data.get("slides", []):
        bg_path = slide.get("bg_path")
        if bg_path and not _resolve_manifest_path(workspace, bg_path).exists():
            report.errors.append(f"missing asset referenced by manifest: {bg_path}")
        for component in slide.get("components", []):
            comp_path = component.get("path")
            if comp_path and not _resolve_manifest_path(workspace, comp_path).exists():
                report.errors.append(f"missing asset referenced by manifest: {comp_path}")


def _check_pptx(workspace: PresentationWorkspace, report: QualityReport) -> None:
    if workspace.pptx_path.exists() and workspace.pptx_path.stat().st_size == 0:
        report.errors.append(f"presentation.pptx exists but is empty: {workspace.pptx_path}")


def validate_project(workspace: PresentationWorkspace, check_outputs: bool = True) -> QualityReport:
    report = QualityReport()
    _check_slide_sources(workspace, report)
    if check_outputs:
        _check_manifest_assets(workspace, report)
        _check_pptx(workspace, report)
    return report
