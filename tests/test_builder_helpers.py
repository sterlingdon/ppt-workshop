from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

from tools.builder import (
    cleanup_extracted_assets,
    should_hide_text_for_native_export,
    should_skip_component_capture,
)


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
