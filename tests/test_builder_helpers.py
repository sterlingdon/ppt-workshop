from pathlib import Path
import sys
import subprocess
from contextlib import contextmanager
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).parent.parent))

from tools import builder
from tools.builder import (
    cleanup_extracted_assets,
    extract_layout_and_assets,
    should_hide_text_for_native_export,
    should_skip_component_capture,
)
from tools.presentation_workspace import create_project_workspace


def test_skip_full_slide_component_capture():
    slide_box = {"x": 0, "y": 0, "width": 1920, "height": 1080}
    component_box = {"x": 0, "y": 0, "width": 1920, "height": 1080}

    assert should_skip_component_capture(component_box, slide_box)


def test_capture_non_full_slide_component():
    slide_box = {"x": 0, "y": 0, "width": 1920, "height": 1080}
    component_box = {"x": 96, "y": 80, "width": 260, "height": 38}

    assert not should_skip_component_capture(component_box, slide_box)


def test_native_text_skip_stays_visible_in_raster():
    assert not should_hide_text_for_native_export("skip")
    assert should_hide_text_for_native_export(None)
    assert should_hide_text_for_native_export("auto")


def test_cleanup_extracted_assets_only_removes_builder_outputs(tmp_path):
    generated = [
        tmp_path / "slide_0_bg.png",
        tmp_path / "slide_0_comp_1.png",
        tmp_path / "slide_0_group_1_item_2.png",
    ]
    for path in generated:
        path.write_text("generated")
    keep = tmp_path / "user_supplied_asset.png"
    keep.write_text("keep")

    cleanup_extracted_assets(tmp_path)

    assert keep.exists()
    assert not any(path.exists() for path in generated)


async def test_extract_layout_uses_managed_preview_server(tmp_path, monkeypatch):
    workspace = create_project_workspace("Managed Preview", root_dir=tmp_path, project_id="managed-preview")
    used_servers = []
    visited_urls = []

    @contextmanager
    def fake_managed_preview_server(web_dir, port=5173):
        used_servers.append((web_dir, port))
        yield SimpleNamespace(url=f"http://127.0.0.1:{port}", owns_process=True)

    def fail_popen(*args, **kwargs):
        raise AssertionError("extract_layout_and_assets must use managed_preview_server")

    class FakeSlidesLocator:
        async def all(self):
            return []

    class FakePage:
        async def set_viewport_size(self, size):
            return None

        async def goto(self, url):
            visited_urls.append(url)

        async def wait_for_timeout(self, timeout):
            return None

        def locator(self, selector):
            assert selector == "[data-ppt-slide]"
            return FakeSlidesLocator()

    class FakeContext:
        async def new_page(self):
            return FakePage()

    class FakeBrowser:
        async def new_context(self, device_scale_factor=1.0):
            return FakeContext()

        async def close(self):
            return None

    class FakeChromium:
        async def launch(self, headless=True):
            return FakeBrowser()

    class FakePlaywright:
        async def __aenter__(self):
            return SimpleNamespace(chromium=FakeChromium())

        async def __aexit__(self, exc_type, exc, tb):
            return None

    monkeypatch.setattr(builder, "managed_preview_server", fake_managed_preview_server, raising=False)
    monkeypatch.setattr(subprocess, "Popen", fail_popen)
    monkeypatch.setattr(builder, "async_playwright", lambda: FakePlaywright())

    await extract_layout_and_assets(web_dir=tmp_path, workspace=workspace, port=5181)

    assert used_servers == [(tmp_path, 5181)]
    assert visited_urls == ["http://127.0.0.1:5181/?extract=1"]
