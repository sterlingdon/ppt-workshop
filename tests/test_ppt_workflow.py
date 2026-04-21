from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

from tools.ppt_workflow import main


VALID_SLIDE = """
import { getDeckStylePreset, styleVars } from '../styles'

export default function Slide_1() {
  const preset = getDeckStylePreset('aurora-borealis')
  return (
    <div style={styleVars(preset)} data-ppt-slide="1">
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
