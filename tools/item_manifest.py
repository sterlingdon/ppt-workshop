from __future__ import annotations


def _round_float(value: float) -> float:
    return round(float(value), 2)


def make_box(raw_box: dict, origin: dict | None = None) -> dict:
    origin = origin or {"x": 0, "y": 0}
    return {
        "x": _round_float(raw_box["x"] - origin.get("x", 0)),
        "y": _round_float(raw_box["y"] - origin.get("y", 0)),
        "width": _round_float(raw_box["width"]),
        "height": _round_float(raw_box["height"]),
    }


def make_item(
    slide_index: int,
    group_index: int,
    item_index: int,
    box: dict,
    raster_path: str,
    texts: list[dict],
    bullets: list[dict],
    mode: str = "item-hybrid",
    fallback_reason: str | None = None,
) -> dict:
    item = {
        "id": f"item_{slide_index}_{group_index}_{item_index}",
        "mode": mode,
        "box": box,
        "raster": {"path": raster_path, "mode": "item"},
        "texts": texts,
        "bullets": bullets,
    }
    if fallback_reason:
        item["fallbackReason"] = fallback_reason
    return item


def make_group(
    slide_index: int,
    group_index: int,
    kind: str,
    box: dict,
    items: list[dict],
    segments: list[dict],
    mode: str = "item-hybrid",
    fallback_reason: str | None = None,
) -> dict:
    group = {
        "id": f"group_{slide_index}_{group_index}",
        "kind": kind,
        "mode": mode,
        "box": box,
        "items": items,
        "segments": segments,
    }
    if fallback_reason:
        group["fallbackReason"] = fallback_reason
    return group
