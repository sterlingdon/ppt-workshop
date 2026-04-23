import base64
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

import tools.visual_asset_providers as providers


def test_unsplash_search_normalizes_results(monkeypatch, tmp_path):
    monkeypatch.setenv("UNSPLASH_ACCESS_KEY", "test-key")
    responses = [
        {
            "results": [
                {
                    "id": "photo-1",
                    "alt_description": "Teacher with students",
                    "urls": {"regular": "https://images.example/teacher.jpg"},
                    "width": 1600,
                    "height": 900,
                    "color": "#ccddee",
                    "links": {
                        "html": "https://unsplash.com/photos/photo-1",
                        "download_location": "https://api.unsplash.com/photos/photo-1/download",
                    },
                    "user": {
                        "name": "Jane Doe",
                        "links": {"html": "https://unsplash.com/@jane"},
                    },
                }
            ]
        },
        {"url": "https://images.example/teacher.jpg?tracked=1"},
    ]
    calls = []

    def fake_request_json(url, *, headers=None, params=None, method="GET", payload=None):
        calls.append((url, headers, params, method, payload))
        return responses.pop(0)

    def fake_download_binary(url, destination, *, headers=None):
        destination.write_bytes(b"img")
        return destination

    monkeypatch.setattr(providers, "_request_json", fake_request_json)
    monkeypatch.setattr(providers, "_download_binary", fake_download_binary)

    items = providers.search_image_candidates(
        query="teacher student classroom",
        candidate_count=1,
        workspace_root=tmp_path,
        asset_prefix="slide_01_primary",
    )

    assert items[0]["path"].endswith(".jpg")
    assert items[0]["source_provider"] == "unsplash"
    assert items[0]["license_metadata"]["author"] == "Jane Doe"
    assert any("download" in call[0] for call in calls)


def test_gemini_generation_writes_png_candidate(monkeypatch, tmp_path):
    monkeypatch.setenv("GEMINI_API_KEY", "gem-key")
    monkeypatch.setenv("GEMINI_IMAGE_MODEL", "gemini-2.5-flash-image-preview")
    image_bytes = base64.b64encode(b"png-bytes").decode("ascii")

    def fake_request_json(url, *, headers=None, params=None, method="GET", payload=None):
        return {
            "candidates": [
                {
                    "content": {
                        "parts": [
                            {"inlineData": {"mimeType": "image/png", "data": image_bytes}}
                        ]
                    }
                }
            ]
        }

    monkeypatch.setattr(providers, "_request_json", fake_request_json)

    items = providers.generate_image_candidates(
        prompt="Create a premium classroom hero image",
        candidate_count=1,
        workspace_root=tmp_path,
        asset_prefix="slide_02_primary",
    )

    assert items[0]["path"].endswith(".png")
    assert (tmp_path / items[0]["path"]).is_file()
    assert items[0]["source_provider"] == "gemini"
