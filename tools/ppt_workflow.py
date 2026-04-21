"""Unified CLI for project-based PPT generation workflow."""
from __future__ import annotations

import argparse
import asyncio
from pathlib import Path

try:
    from .builder import extract_layout_and_assets
    from .deck_sources import activate_project_slides, snapshot_active_slides
    from .pptx_exporter import build_pptx
    from .presentation_workspace import create_project_workspace, get_project_workspace
    from .quality_gate import validate_project
except ImportError:
    from builder import extract_layout_and_assets
    from deck_sources import activate_project_slides, snapshot_active_slides
    from pptx_exporter import build_pptx
    from presentation_workspace import create_project_workspace, get_project_workspace
    from quality_gate import validate_project


def _workspace(args):
    return get_project_workspace(args.project, root_dir=args.project_root)


def cmd_init(args) -> int:
    workspace = create_project_workspace(args.name, root_dir=args.project_root, project_id=args.project_id)
    print(workspace.project_id)
    print(workspace.project_dir)
    return 0


def cmd_snapshot_slides(args) -> int:
    workspace = _workspace(args)
    copied = snapshot_active_slides(workspace, args.slides_dir)
    print(f"snapshot copied {len(copied)} slide source files to {workspace.slides_dir}")
    return 0


def cmd_activate(args) -> int:
    workspace = _workspace(args)
    copied = activate_project_slides(workspace, args.slides_dir)
    print(f"activated {len(copied)} slide source files from {workspace.slides_dir}")
    return 0


def cmd_validate(args) -> int:
    workspace = _workspace(args)
    report = validate_project(workspace, check_outputs=False)
    if report.ok:
        print(f"validation passed: {workspace.project_id}")
        for warning in report.warnings:
            print(f"warning: {warning}")
        return 0

    print(f"validation failed: {workspace.project_id}")
    for error in report.errors:
        print(f"error: {error}")
    for warning in report.warnings:
        print(f"warning: {warning}")
    return 1


async def _extract(args) -> int:
    workspace = _workspace(args)
    activate_project_slides(workspace, args.slides_dir)
    report = validate_project(workspace)
    if not report.ok:
        for error in report.errors:
            print(f"error: {error}")
        return 1
    await extract_layout_and_assets(args.web_dir, workspace=workspace, port=args.port)
    return 0


def cmd_extract(args) -> int:
    return asyncio.run(_extract(args))


def cmd_export(args) -> int:
    workspace = _workspace(args)
    if not workspace.manifest_path.exists():
        print(f"error: missing layout manifest: {workspace.manifest_path}")
        return 1
    workspace.pptx_path.parent.mkdir(parents=True, exist_ok=True)
    build_pptx(str(workspace.manifest_path), str(workspace.pptx_path))
    print(f"exported {workspace.pptx_path}")
    return 0


async def _build(args) -> int:
    extract_code = await _extract(args)
    if extract_code != 0:
        return extract_code
    export_code = cmd_export(args)
    if export_code != 0:
        return export_code
    return cmd_validate(args)


def cmd_build(args) -> int:
    return asyncio.run(_build(args))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Manage project-based PPT workflow.")
    sub = parser.add_subparsers(dest="command", required=True)

    init = sub.add_parser("init", help="Create a deck project workspace.")
    init.add_argument("--name", required=True)
    init.add_argument("--project-root", default="output/projects")
    init.add_argument("--project-id")
    init.set_defaults(func=cmd_init)

    for name, help_text, func in [
        ("snapshot-slides", "Persist active web/src/slides into a project.", cmd_snapshot_slides),
        ("activate", "Copy project slides into the active renderer slot.", cmd_activate),
        ("validate", "Run structural quality gates.", cmd_validate),
        ("extract", "Activate slides and extract layout manifest/assets.", cmd_extract),
        ("export", "Build PPTX from an existing layout manifest.", cmd_export),
        ("build", "Validate, extract, export, and validate outputs.", cmd_build),
    ]:
        command = sub.add_parser(name, help=help_text)
        command.add_argument("--project", required=True)
        command.add_argument("--project-root", default="output/projects")
        command.add_argument("--slides-dir", default="web/src/slides")
        command.add_argument("--web-dir", default="web")
        command.add_argument("--port", type=int, default=5173)
        command.set_defaults(func=func)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
