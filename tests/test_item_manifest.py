from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

from tools.item_manifest import make_box, make_group, make_item


def test_make_box_normalizes_coordinates():
    box = make_box({"x": 120.2, "y": 30.8, "width": 400.0, "height": 90.4}, {"x": 20.2, "y": 10.8})
    assert box == {"x": 100.0, "y": 20.0, "width": 400.0, "height": 90.4}


def test_make_item_defaults_to_item_hybrid():
    item = make_item(
        slide_index=0,
        group_index=1,
        item_index=2,
        box={"x": 10, "y": 20, "width": 300, "height": 120},
        raster_path="assets/slide_0_group_1_item_2.png",
        texts=[{"id": "text_0", "box": {"x": 1, "y": 2, "width": 3, "height": 4}, "style": {"text": "Hello"}}],
        bullets=[],
    )
    assert item["id"] == "item_0_1_2"
    assert item["mode"] == "item-hybrid"
    assert item["raster"]["path"] == "assets/slide_0_group_1_item_2.png"
    assert item["texts"][0]["style"]["text"] == "Hello"


def test_make_group_records_kind_and_items():
    item = make_item(0, 0, 0, {"x": 0, "y": 0, "width": 10, "height": 10}, "item.png", [], [])
    group = make_group(0, 0, "list", {"x": 0, "y": 0, "width": 100, "height": 100}, [item], [])
    assert group["id"] == "group_0_0"
    assert group["kind"] == "list"
    assert group["items"] == [item]
