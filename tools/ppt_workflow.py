"""Unified CLI for project-based PPT generation workflow."""
from __future__ import annotations

import argparse
import asyncio
import json
from pathlib import Path

try:
    from .builder import extract_layout_and_assets
    from .deck_sources import activate_project_slides, snapshot_active_slides
    from .human_feedback import apply_feedback
    from .html_exporter import build_html_presentation
    from .pptx_exporter import build_pptx
    from .presentation_workspace import create_project_workspace, get_project_workspace
    from .quality_gate import validate_project
    from .visual_assets import build_visual_asset_manifest, build_visual_asset_plan
    from .visual_validator import capture_review_screenshots, validate_visual_project, write_visual_report, run_visual_validation
except ImportError:
    from builder import extract_layout_and_assets
    from deck_sources import activate_project_slides, snapshot_active_slides
    from human_feedback import apply_feedback
    from html_exporter import build_html_presentation
    from pptx_exporter import build_pptx
    from presentation_workspace import create_project_workspace, get_project_workspace
    from quality_gate import validate_project
    from visual_assets import build_visual_asset_manifest, build_visual_asset_plan
    from visual_validator import capture_review_screenshots, validate_visual_project, write_visual_report, run_visual_validation


def _workspace(args):
    return get_project_workspace(args.project, root_dir=args.project_root)


def _activate_and_validate(args, check_outputs: bool = True, require_agent_reports: bool = False):
    workspace = _workspace(args)
    activate_project_slides(workspace, args.slides_dir)
    report = validate_project(workspace, check_outputs=check_outputs, require_agent_reports=require_agent_reports)
    return workspace, report


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


def cmd_asset_plan(args) -> int:
    workspace = _workspace(args)
    build_visual_asset_plan(workspace)
    print(f"wrote {workspace.visual_asset_plan_path}")
    return 0


def cmd_asset_manifest(args) -> int:
    workspace = _workspace(args)
    build_visual_asset_manifest(workspace)
    print(f"wrote {workspace.visual_asset_manifest_path}")
    return 0


def cmd_log_feedback(args) -> int:
    workspace = _workspace(args)
    apply_feedback(workspace, args.message, default_stage=args.stage)
    print(f"wrote {workspace.human_feedback_log_path}")
    return 0


async def _visual_validate(args) -> int:
    workspace = _workspace(args)
    report = await validate_visual_project(workspace, web_dir=args.web_dir, port=args.port, headless=not args.headed)
    write_visual_report(workspace, report)

    if report.ok:
        print(f"engineering render validation passed: {workspace.project_id}")
        print("AI visual review is still required via visual_review_report.json")
        print(f"preview: {report.preview_url}")
        return 0

    print(f"engineering render validation failed: {workspace.project_id}")
    print("This checks rendered visibility and overflow only; it is not AI visual review.")
    print(f"preview: {report.preview_url}")
    for slide in report.slides:
        if slide["passed"]:
            continue
        print(f"slide {slide['slide']}:")
        for suggestion in slide["suggestions"]:
            print(f"  - {suggestion}")
    return 1


def cmd_visual_validate(args) -> int:
    return asyncio.run(_visual_validate(args))


async def _review_screenshots(args) -> int:
    workspace = _workspace(args)
    result = await capture_review_screenshots(workspace, web_dir=args.web_dir, port=args.port, headless=not args.headed)
    print(f"review screenshots written: {workspace.project_id}")
    print(f"full deck: {result['full_deck_screenshot']}")
    print(f"slides: {len(result['slide_screenshots'])}")
    return 0


def cmd_review_screenshots(args) -> int:
    return asyncio.run(_review_screenshots(args))


async def _extract(args) -> int:
    workspace, report = _activate_and_validate(args)
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


def cmd_export_html(args) -> int:
    workspace, report = _activate_and_validate(args, check_outputs=False)
    if not report.ok:
        print(f"validation failed: {workspace.project_id}")
        for error in report.errors:
            print(f"error: {error}")
        for warning in report.warnings:
            print(f"warning: {warning}")
        return 1
    try:
        build_html_presentation(args.web_dir, workspace.html_dir)
    except RuntimeError as exc:
        print(f"error: {exc}")
        return 1
    print(f"exported {workspace.html_dir / 'index.html'}")
    return 0


async def _build(args) -> int:
    workspace, preflight = _activate_and_validate(args, check_outputs=False, require_agent_reports=True)
    if not preflight.ok:
        print(f"validation failed: {workspace.project_id}")
        for error in preflight.errors:
            print(f"error: {error}")
        for warning in preflight.warnings:
            print(f"warning: {warning}")
        return 1
    visual_code = await _visual_validate(args)
    if visual_code != 0:
        return visual_code
    await extract_layout_and_assets(args.web_dir, workspace=workspace, port=args.port)
    export_code = cmd_export(args)
    if export_code != 0:
        return export_code
    html_code = cmd_export_html(args)
    if html_code != 0:
        return html_code
    final_report = validate_project(workspace, require_agent_reports=True)
    if not final_report.ok:
        print(f"validation failed: {workspace.project_id}")
        for error in final_report.errors:
            print(f"error: {error}")
        for warning in final_report.warnings:
            print(f"warning: {warning}")
        return 1
    return 0


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
        ("asset-plan", "Write the visual asset plan artifact for a project.", cmd_asset_plan),
        ("asset-manifest", "Write the visual asset manifest artifact for a project.", cmd_asset_manifest),
    ]:
        command = sub.add_parser(name, help=help_text)
        command.add_argument("--project", required=True)
        command.add_argument("--project-root", default="output/projects")
        command.set_defaults(func=func)

    log_feedback = sub.add_parser("log-feedback", help="Normalize human feedback into the project feedback log.")
    log_feedback.add_argument("--project", required=True)
    log_feedback.add_argument("--project-root", default="output/projects")
    log_feedback.add_argument("--message", required=True)
    log_feedback.add_argument("--stage", default="visual_review")
    log_feedback.set_defaults(func=cmd_log_feedback)

    for name, help_text, func in [
        ("snapshot-slides", "Persist active web/src/generated/slides into a project.", cmd_snapshot_slides),
        ("activate", "Copy project slides into the active renderer slot.", cmd_activate),
        ("validate", "Run structural quality gates.", cmd_validate),
        ("review-screenshots", "Capture rendered deck screenshots for AI visual review.", cmd_review_screenshots),
        ("visual-validate", "Run browser-based HTML presentation checks.", cmd_visual_validate),
        ("extract", "Activate slides and extract layout manifest/assets.", cmd_extract),
        ("export", "Build PPTX from an existing layout manifest.", cmd_export),
        ("export-html", "Activate project slides and build the complete Vite static-site directory.", cmd_export_html),
        ("build", "Activate, require agent gates, validate engineering render, extract, export PPTX and HTML, and validate outputs.", cmd_build),
    ]:
        command = sub.add_parser(name, help=help_text)
        command.add_argument("--project", required=True)
        command.add_argument("--project-root", default="output/projects")
        command.add_argument("--slides-dir", default="web/src/generated/slides")
        command.add_argument("--web-dir", default="web")
        command.add_argument("--port", type=int, default=5173)
        command.add_argument("--headed", action="store_true", help="Run the browser in headed mode.")
        command.set_defaults(func=func)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
