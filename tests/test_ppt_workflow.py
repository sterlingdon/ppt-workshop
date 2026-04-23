from pathlib import Path
import sys
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).parent.parent))

import tools.ppt_workflow as ppt_workflow
from tools.ppt_workflow import main


VALID_SLIDE = """
import type { CSSProperties } from 'react'

const designDnaTheme = {
  '--ppt-bg': '#F7F3EA',
  '--ppt-text': '#18211D',
} as CSSProperties

export default function Slide_1() {
  return (
    <div style={designDnaTheme} className="bg-[var(--ppt-bg)] text-[var(--ppt-text)]" data-ppt-slide="1">
      <h1 data-ppt-text="true">CLI Deck</h1>
    </div>
  )
}
""".strip()


def write_active_slides(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)
    (path / "Slide_1.tsx").write_text(VALID_SLIDE, encoding="utf-8")
    (path / "index.ts").write_text("import Slide_1 from './Slide_1'\n\nexport default [Slide_1]\n", encoding="utf-8")


def test_cli_init_creates_project_workspace(tmp_path, capsys):
    code = main(["init", "--name", "CLI Deck", "--project-root", str(tmp_path), "--project-id", "cli-deck"])

    captured = capsys.readouterr()
    assert code == 0
    assert "cli-deck" in captured.out
    assert (tmp_path / "cli-deck" / "project.json").is_file()


def test_cli_snapshot_then_validate(tmp_path, capsys):
    active = tmp_path / "active-slides"
    write_active_slides(active)

    assert main(["init", "--name", "CLI Deck", "--project-root", str(tmp_path), "--project-id", "cli-deck"]) == 0
    assert main([
        "snapshot-slides",
        "--project",
        "cli-deck",
        "--project-root",
        str(tmp_path),
        "--slides-dir",
        str(active),
    ]) == 0
    code = main(["validate", "--project", "cli-deck", "--project-root", str(tmp_path)])

    captured = capsys.readouterr()
    assert code == 0
    assert "validation passed" in captured.out


def test_cli_validate_returns_nonzero_for_invalid_deck(tmp_path, capsys):
    assert main(["init", "--name", "Bad Deck", "--project-root", str(tmp_path), "--project-id", "bad-deck"]) == 0

    code = main(["validate", "--project", "bad-deck", "--project-root", str(tmp_path)])

    captured = capsys.readouterr()
    assert code == 1
    assert "validation failed" in captured.out


def test_cli_build_runs_visual_validation(tmp_path, monkeypatch, capsys):
    project_root = tmp_path
    active = tmp_path / "active-slides"
    write_active_slides(active)

    assert main(["init", "--name", "CLI Deck", "--project-root", str(project_root), "--project-id", "cli-deck"]) == 0
    assert main([
        "snapshot-slides",
        "--project",
        "cli-deck",
        "--project-root",
        str(project_root),
        "--slides-dir",
        str(active),
    ]) == 0

    calls = []

    def fake_activate(*args, **kwargs):
        calls.append("activate")
        return None

    async def fake_extract(*args, **kwargs):
        calls.append("extract")
        return None

    def fake_export(args):
        calls.append("export")
        return 0

    def fake_export_html(args):
        calls.append("export-html")
        return 0

    def fake_validate(workspace, check_outputs=True, require_agent_reports=False):
        calls.append(f"validate:{check_outputs}:{require_agent_reports}")
        return SimpleNamespace(ok=True, errors=[], warnings=[])

    async def fake_visual_validate(args):
        calls.append("visual")
        return 0

    monkeypatch.setattr(ppt_workflow, "activate_project_slides", fake_activate)
    monkeypatch.setattr(ppt_workflow, "extract_layout_and_assets", fake_extract)
    monkeypatch.setattr(ppt_workflow, "cmd_export", fake_export)
    monkeypatch.setattr(ppt_workflow, "cmd_export_html", fake_export_html)
    monkeypatch.setattr(ppt_workflow, "validate_project", fake_validate)
    monkeypatch.setattr(ppt_workflow, "_visual_validate", fake_visual_validate)

    code = main(["build", "--project", "cli-deck", "--project-root", str(project_root)])

    captured = capsys.readouterr()
    assert code == 0
    assert calls == ["activate", "validate:False:True", "visual", "extract", "export", "export-html", "validate:True:True"]


def test_cli_export_html_writes_static_presentation(tmp_path, monkeypatch, capsys):
    assert main(["init", "--name", "CLI Deck", "--project-root", str(tmp_path), "--project-id", "cli-deck"]) == 0
    write_active_slides(tmp_path / "cli-deck" / "slides")
    calls = []

    def fake_build_html(web_dir, output_dir):
        calls.append((web_dir, output_dir))
        (output_dir / "assets").mkdir(parents=True, exist_ok=True)
        (output_dir / "index.html").write_text("<!doctype html>", encoding="utf-8")
        (output_dir / "assets" / "index.js").write_text("console.log('deck')", encoding="utf-8")
        return output_dir

    monkeypatch.setattr(ppt_workflow, "build_html_presentation", fake_build_html)

    code = main([
        "export-html",
        "--project",
        "cli-deck",
        "--project-root",
        str(tmp_path),
        "--slides-dir",
        str(tmp_path / "active-slides"),
        "--web-dir",
        "web",
    ])

    captured = capsys.readouterr()
    assert code == 0
    assert calls == [("web", tmp_path / "cli-deck" / "presentation-html")]
    assert "presentation-html/index.html" in captured.out


def test_cli_review_screenshots_command_writes_review_assets(tmp_path, monkeypatch, capsys):
    project_root = tmp_path
    active = tmp_path / "active-slides"
    write_active_slides(active)

    assert main(["init", "--name", "CLI Deck", "--project-root", str(project_root), "--project-id", "cli-deck"]) == 0
    assert main([
        "snapshot-slides",
        "--project",
        "cli-deck",
        "--project-root",
        str(project_root),
        "--slides-dir",
        str(active),
    ]) == 0

    calls = []

    async def fake_capture(workspace, web_dir="web", port=5173, headless=True):
        calls.append((workspace.project_id, web_dir, port, headless))
        return {
            "full_deck_screenshot": str(workspace.project_dir / "review" / "full_deck.png"),
            "slide_screenshots": [str(workspace.project_dir / "review" / "slides" / "slide_01.png")],
        }

    monkeypatch.setattr(ppt_workflow, "capture_review_screenshots", fake_capture)

    code = main(["review-screenshots", "--project", "cli-deck", "--project-root", str(project_root)])

    captured = capsys.readouterr()
    assert code == 0
    assert calls == [("cli-deck", "web", 5173, True)]
    assert "review screenshots written" in captured.out
