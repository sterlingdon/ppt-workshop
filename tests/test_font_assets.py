from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

from tools.font_assets import build_font_asset_manifest, resolve_font_strategy
from tools.presentation_workspace import create_project_workspace


def test_build_font_asset_manifest_downloads_google_font(monkeypatch, tmp_path):
    workspace = create_project_workspace("Font Deck", root_dir=tmp_path, project_id="font-deck")
    (workspace.project_dir / "design_dna.json").write_text(
        """
{
  "font_strategy": {
    "display": {
      "family": "Space Grotesk",
      "source": "download",
      "fallback_chain": ["Arial", "sans-serif"]
    }
  }
}
""".strip(),
        encoding="utf-8",
    )

    def fake_request_text(url, *, headers=None, params=None):
        assert "fonts.googleapis.com" in url
        return "@font-face { src: url(https://fonts.example/space-grotesk.woff2) format('woff2'); }"

    def fake_download_binary(url, destination, *, headers=None):
        destination.write_bytes(b"woff2")
        return destination

    monkeypatch.setattr("tools.font_assets._request_text", fake_request_text)
    monkeypatch.setattr("tools.font_assets._download_binary", fake_download_binary)

    manifest = build_font_asset_manifest(workspace)

    assert manifest["fonts"][0]["status"] == "ready"
    assert workspace.font_manifest_path.is_file()
    assert workspace.font_css_path.read_text(encoding="utf-8").count("@font-face") == 1
    assert list(workspace.fonts_dir.iterdir())


def test_build_font_asset_manifest_handles_local_font_without_download(tmp_path):
    workspace = create_project_workspace("Local Font Deck", root_dir=tmp_path, project_id="local-font-deck")
    (workspace.project_dir / "design_dna.json").write_text(
        """
{
  "font_strategy": {
    "body": {
      "family": "Noto Sans SC",
      "source": "local",
      "fallback_chain": ["PingFang SC", "sans-serif"]
    }
  }
}
""".strip(),
        encoding="utf-8",
    )

    manifest = build_font_asset_manifest(workspace)

    assert manifest["fonts"][0]["status"] == "local_only"
    assert workspace.font_css_path.read_text(encoding="utf-8").count("@font-face") == 0


def test_resolve_font_strategy_uses_inferred_preset():
    preset, strategy = resolve_font_strategy(
        {
            "visual_direction": "editorial education story deck",
            "font_strategy": {
                "display": {
                    "family": "Noto Serif SC",
                }
            },
        }
    )

    assert preset == "editorial_publishing"
    assert strategy["display"]["family"] == "Noto Serif SC"
    assert strategy["body"]["family"] == "Noto Sans SC"
