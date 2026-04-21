from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

from tools.deck_sources import activate_project_slides, snapshot_active_slides
from tools.presentation_workspace import create_project_workspace


def write_active_deck(slides_dir: Path, title: str = "Demo") -> None:
    slides_dir.mkdir(parents=True, exist_ok=True)
    (slides_dir / "Slide_1.tsx").write_text(
        f"""
import {{ getDeckStylePreset, styleVars }} from '../../styles'

export default function Slide_1() {{
  const preset = getDeckStylePreset('aurora-borealis')
  return (
    <div style={{styleVars(preset)}} data-ppt-slide="1">
      <h1 data-ppt-text="true">{title}</h1>
    </div>
  )
}}
""".strip(),
        encoding="utf-8",
    )
    (slides_dir / "index.ts").write_text(
        "import Slide_1 from './Slide_1'\n\nexport default [Slide_1]\n",
        encoding="utf-8",
    )


def test_snapshot_active_slides_copies_renderer_slot_to_project(tmp_path):
    workspace = create_project_workspace("Demo Deck", root_dir=tmp_path, project_id="deck-a")
    active_slides = tmp_path / "web" / "src" / "slides"
    write_active_deck(active_slides, title="Snapshot Title")

    copied = snapshot_active_slides(workspace, active_slides)

    assert sorted(path.name for path in copied) == ["Slide_1.tsx", "index.ts"]
    assert (workspace.slides_dir / "Slide_1.tsx").read_text(encoding="utf-8").count("Snapshot Title") == 1


def test_activate_project_slides_replaces_renderer_slot(tmp_path):
    workspace = create_project_workspace("Demo Deck", root_dir=tmp_path, project_id="deck-a")
    write_active_deck(workspace.slides_dir, title="Project Title")

    active_slides = tmp_path / "web" / "src" / "slides"
    write_active_deck(active_slides, title="Old Active Title")

    copied = activate_project_slides(workspace, active_slides)

    assert sorted(path.name for path in copied) == ["Slide_1.tsx", "index.ts"]
    assert "Project Title" in (active_slides / "Slide_1.tsx").read_text(encoding="utf-8")
    assert "Old Active Title" not in (active_slides / "Slide_1.tsx").read_text(encoding="utf-8")


def test_activate_project_slides_requires_index(tmp_path):
    workspace = create_project_workspace("Bad Deck", root_dir=tmp_path, project_id="deck-b")
    (workspace.slides_dir / "Slide_1.tsx").write_text("export default function Slide_1() { return null }\n", encoding="utf-8")

    try:
        activate_project_slides(workspace, tmp_path / "active")
    except FileNotFoundError as exc:
        assert "index.ts" in str(exc)
    else:
        raise AssertionError("expected missing index.ts to fail")
