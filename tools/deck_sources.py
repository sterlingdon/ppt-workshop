"""Copy generated React slide sources between project workspaces and the renderer."""
from __future__ import annotations

import shutil
from pathlib import Path

try:
    from .presentation_workspace import PresentationWorkspace
except ImportError:
    from presentation_workspace import PresentationWorkspace


SLIDE_SOURCE_PATTERNS = ("*.ts", "*.tsx", "*.css", "*.json")


def _require_slide_index(slides_dir: Path) -> None:
    if not (slides_dir / "index.ts").is_file():
        raise FileNotFoundError(f"slide source directory must contain index.ts: {slides_dir}")


def _copy_slide_sources(source_dir: Path, dest_dir: Path) -> list[Path]:
    _require_slide_index(source_dir)
    if dest_dir.exists():
        shutil.rmtree(dest_dir)
    dest_dir.mkdir(parents=True, exist_ok=True)

    copied: list[Path] = []
    for pattern in SLIDE_SOURCE_PATTERNS:
        for source in sorted(source_dir.glob(pattern)):
            if source.is_file():
                dest = dest_dir / source.name
                shutil.copy2(source, dest)
                copied.append(dest)
    return copied


def snapshot_active_slides(
    workspace: PresentationWorkspace,
    active_slides_dir: str | Path = "web/src/generated/slides",
) -> list[Path]:
    """Persist the active renderer slide slot into a deck project workspace."""
    return _copy_slide_sources(Path(active_slides_dir), workspace.slides_dir)


def activate_project_slides(
    workspace: PresentationWorkspace,
    active_slides_dir: str | Path = "web/src/generated/slides",
) -> list[Path]:
    """Copy a deck project's durable slide sources into the active renderer slot."""
    return _copy_slide_sources(workspace.slides_dir, Path(active_slides_dir))
