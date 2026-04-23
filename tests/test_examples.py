import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

from tools.presentation_workspace import create_project_workspace
from tools.quality_gate import validate_project


ROOT = Path(__file__).parent.parent
EXAMPLE_SLIDES = ROOT / "examples" / "react-slides" / "minimal-deck"
EXAMPLE_REPORTS = ROOT / "examples" / "reports"


def test_minimal_deck_example_validates_as_slide_source(tmp_path):
    workspace = create_project_workspace("Example Deck", root_dir=tmp_path, project_id="example-deck")
    for source in EXAMPLE_SLIDES.glob("Slide_*.tsx"):
        (workspace.slides_dir / source.name).write_text(source.read_text(encoding="utf-8"), encoding="utf-8")
    (workspace.slides_dir / "index.ts").write_text(
        (EXAMPLE_SLIDES / "index.ts").read_text(encoding="utf-8"),
        encoding="utf-8",
    )

    report = validate_project(workspace)

    assert report.ok


def test_example_design_dna_is_the_only_design_dna_artifact():
    assert (EXAMPLE_SLIDES / "design_dna.json").is_file()
    assert not list(EXAMPLE_SLIDES.glob("*override*.json"))

    data = json.loads((EXAMPLE_SLIDES / "design_dna.json").read_text(encoding="utf-8"))

    assert data["source_skill"] == "ui-ux-pro-max"
    assert data["visual_direction"] == "warm editorial command center"
    assert data["theme_tokens"]["--ppt-accent"] == "#C99A2E"
    assert "signature_visual_moves" in data


def test_report_examples_use_required_gate_fields():
    for path in EXAMPLE_REPORTS.glob("*.json"):
        data = json.loads(path.read_text(encoding="utf-8"))

        assert "status" in data
        assert "blocking_findings" in data

    visual = json.loads((EXAMPLE_REPORTS / "visual-review-report.pass.json").read_text(encoding="utf-8"))
    assert visual["gate_type"] == "ai_visual_quality_review"

    content_pass = json.loads((EXAMPLE_REPORTS / "content-quality-report.pass.json").read_text(encoding="utf-8"))
    assert all(item["status"] == "resolved" for item in content_pass["resolution_log"])

    content_blocked = json.loads((EXAMPLE_REPORTS / "content-quality-report.needs-revision.json").read_text(encoding="utf-8"))
    assert any(item["status"] == "open" for item in content_blocked["resolution_log"])

    visual_pass = json.loads((EXAMPLE_REPORTS / "visual-review-report.pass.json").read_text(encoding="utf-8"))
    assert all(item["status"] == "resolved" for item in visual_pass["repair_log"])

    visual_blocked = json.loads((EXAMPLE_REPORTS / "visual-review-report.blocked.json").read_text(encoding="utf-8"))
    assert any(item["status"] == "open" for item in visual_blocked["repair_log"])
