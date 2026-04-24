"""Copy generated React slide sources between project workspaces and the renderer."""
from __future__ import annotations

import shutil
from pathlib import Path

try:
    from .font_assets import build_font_asset_manifest
    from .presentation_workspace import PresentationWorkspace
except ImportError:
    from font_assets import build_font_asset_manifest
    from presentation_workspace import PresentationWorkspace


SLIDE_SOURCE_PATTERNS = ("*.ts", "*.tsx", "*.css", "*.json")
GENERATED_FONT_CSS_NAME = "font-face.css"


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


def _sync_generated_font_assets(workspace: PresentationWorkspace, generated_root: Path) -> None:
    generated_root.mkdir(parents=True, exist_ok=True)
    generated_fonts_dir = generated_root / "fonts"
    if generated_fonts_dir.exists():
        shutil.rmtree(generated_fonts_dir)
    generated_fonts_dir.mkdir(parents=True, exist_ok=True)

    if (workspace.project_dir / "design_dna.json").exists():
        build_font_asset_manifest(workspace)
    else:
        workspace.font_css_path.write_text("/* no project font assets */\n", encoding="utf-8")

    if workspace.fonts_dir.exists():
        for source in sorted(workspace.fonts_dir.iterdir()):
            if source.is_file():
                shutil.copy2(source, generated_fonts_dir / source.name)

    destination_css = generated_root / GENERATED_FONT_CSS_NAME
    if workspace.font_css_path.is_file():
        shutil.copy2(workspace.font_css_path, destination_css)
    else:
        destination_css.write_text("/* no project font assets */\n", encoding="utf-8")


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
    destination = Path(active_slides_dir)
    copied = _copy_slide_sources(workspace.slides_dir, destination)
    _sync_generated_font_assets(workspace, destination.parent)
    return copied
