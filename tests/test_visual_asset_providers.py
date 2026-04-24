import base64
import json
from pathlib import Path
import types
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

import tools.visual_asset_providers as providers

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


def test_qwen_generation_writes_png_candidate(monkeypatch, tmp_path):
    monkeypatch.setenv("VISUAL_ASSET_IMAGE_PROVIDER", "qwen")
    monkeypatch.setenv("DASHSCOPE_API_KEY", "dash-key")
    monkeypatch.setenv("QWEN_IMAGE_MODEL", "qwen-image-2.0-pro")

    class FakeResponse:
        status_code = 200

        def __str__(self):
            return json.dumps(
                {
                    "output": {
                        "choices": [
                            {
                                "message": {
                                    "content": [
                                        {"image": "https://images.example/qwen.png"}
                                    ]
                                }
                            }
                        ]
                    }
                }
            )

    class FakeMultiModalConversation:
        @staticmethod
        def call(**kwargs):
            return FakeResponse()

    fake_dashscope = types.SimpleNamespace(
        api_key="",
        base_http_api_url="",
        MultiModalConversation=FakeMultiModalConversation,
    )

    monkeypatch.setitem(sys.modules, "dashscope", fake_dashscope)

    def fake_download_binary(url, destination, *, headers=None):
        destination.write_bytes(b"qwen")
        return destination

    monkeypatch.setattr(providers, "_download_binary", fake_download_binary)

    items = providers.generate_image_candidates(
        prompt="Create a premium classroom hero image",
        candidate_count=1,
        workspace_root=tmp_path,
        asset_prefix="slide_03_primary",
    )

    assert items[0]["path"].endswith(".png")
    assert (tmp_path / items[0]["path"]).is_file()
    assert items[0]["source_provider"] == "qwen"


def test_wanx_generation_writes_png_candidate(monkeypatch, tmp_path):
    monkeypatch.setenv("VISUAL_ASSET_IMAGE_PROVIDER", "wanx")
    monkeypatch.setenv("DASHSCOPE_API_KEY", "dash-key")
    monkeypatch.setenv("WANX_IMAGE_MODEL", "wan2.6-t2i")

    class FakeMessage:
        def __init__(self, role, content):
            self.role = role
            self.content = content

    class FakeResponse:
        status_code = 200
        message = "ok"

        def __str__(self):
            return json.dumps(
                {
                    "output": {
                        "choices": [
                            {
                                "message": {
                                    "content": [
                                        {"image": "https://images.example/wanx.png"}
                                    ]
                                }
                            }
                        ]
                    }
                }
            )

    class FakeImageGeneration:
        @staticmethod
        def call(**kwargs):
            return FakeResponse()

    fake_dashscope = types.SimpleNamespace(api_key="", base_url="")
    fake_image_generation = types.SimpleNamespace(ImageGeneration=FakeImageGeneration)
    fake_response_module = types.SimpleNamespace(Message=FakeMessage)

    monkeypatch.setitem(sys.modules, "dashscope", fake_dashscope)
    monkeypatch.setitem(sys.modules, "dashscope.aigc.image_generation", fake_image_generation)
    monkeypatch.setitem(sys.modules, "dashscope.api_entities.dashscope_response", fake_response_module)

    def fake_download_binary(url, destination, *, headers=None):
        destination.write_bytes(b"wanx")
        return destination

    monkeypatch.setattr(providers, "_download_binary", fake_download_binary)

    items = providers.generate_image_candidates(
        prompt="Create a premium classroom hero image",
        candidate_count=1,
        workspace_root=tmp_path,
        asset_prefix="slide_04_primary",
    )

    assert items[0]["path"].endswith(".png")
    assert (tmp_path / items[0]["path"]).is_file()
    assert items[0]["source_provider"] == "wanx"
