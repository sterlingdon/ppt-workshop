"""Workspace helpers for one generated presentation project."""
from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime
import json
import re
from pathlib import Path


DEFAULT_PROJECT_ROOT = Path("output/projects")


@dataclass(frozen=True)
class PresentationWorkspace:
    project_id: str
    project_dir: Path
    assets_dir: Path
    slides_dir: Path
    manifest_path: Path
    pptx_path: Path
    html_dir: Path
    metadata_path: Path
    slide_blueprint_path: Path
    visual_asset_plan_path: Path
    visual_asset_manifest_path: Path
    human_feedback_log_path: Path

    def to_json_dict(self) -> dict[str, str]:
        return {key: str(value) for key, value in asdict(self).items()}


def slugify_project_name(name: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", name.lower()).strip("-")
    slug = re.sub(r"-{2,}", "-", slug)
    return slug or "presentation"


def validate_project_id(project_id: str) -> str:
    if not project_id or project_id in {".", ".."}:
        raise ValueError("project_id must be a non-empty directory name")
    if "/" in project_id or "\\" in project_id or ".." in project_id:
        raise ValueError("project_id must not contain path traversal")
    if not re.fullmatch(r"[a-zA-Z0-9][a-zA-Z0-9._-]*", project_id):
        raise ValueError("project_id contains unsupported characters")
    return project_id


def create_project_id(name: str, now: datetime | None = None) -> str:
    timestamp = (now or datetime.now()).strftime("%Y%m%d-%H%M%S")
    return f"{timestamp}-{slugify_project_name(name)}"


def get_project_workspace(project_id: str, root_dir: str | Path = DEFAULT_PROJECT_ROOT) -> PresentationWorkspace:
    safe_id = validate_project_id(project_id)
    root = Path(root_dir)
    project_dir = root / safe_id
    return PresentationWorkspace(
        project_id=safe_id,
        project_dir=project_dir,
        assets_dir=project_dir / "assets",
        slides_dir=project_dir / "slides",
        manifest_path=project_dir / "layout_manifest.json",
        pptx_path=project_dir / "presentation.pptx",
        html_dir=project_dir / "presentation-html",
        metadata_path=project_dir / "project.json",
        slide_blueprint_path=project_dir / "slide_blueprint.json",
        visual_asset_plan_path=project_dir / "visual_asset_plan.json",
        visual_asset_manifest_path=project_dir / "visual_asset_manifest.json",
        human_feedback_log_path=project_dir / "human_feedback_log.json",
    )


def create_project_workspace(
    name: str,
    root_dir: str | Path = DEFAULT_PROJECT_ROOT,
    project_id: str | None = None,
) -> PresentationWorkspace:
    workspace = get_project_workspace(project_id or create_project_id(name), root_dir=root_dir)
    workspace.assets_dir.mkdir(parents=True, exist_ok=True)
    workspace.slides_dir.mkdir(parents=True, exist_ok=True)

    metadata = {
        "project_id": workspace.project_id,
        "name": name,
        "paths": workspace.to_json_dict(),
    }
    workspace.metadata_path.write_text(
        json.dumps(metadata, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return workspace
