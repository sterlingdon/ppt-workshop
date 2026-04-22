from __future__ import annotations

import argparse

try:
    from .presentation_workspace import get_project_workspace
    from .visual_validator import run_visual_validation, write_visual_report
except ImportError:
    from presentation_workspace import get_project_workspace
    from visual_validator import run_visual_validation, write_visual_report


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run browser-based HTML presentation validation.")
    parser.add_argument("--project", required=True)
    parser.add_argument("--project-root", default="output/projects")
    parser.add_argument("--web-dir", default="web")
    parser.add_argument("--port", type=int, default=5173)
    parser.add_argument("--headed", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    workspace = get_project_workspace(args.project, root_dir=args.project_root)
    report = run_visual_validation(workspace, web_dir=args.web_dir, port=args.port, headless=not args.headed)
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


if __name__ == "__main__":
    raise SystemExit(main())
