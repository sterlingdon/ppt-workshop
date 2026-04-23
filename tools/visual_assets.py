from __future__ import annotations

import json
import math
import os
import re
from html import escape
from pathlib import Path


CRITICAL_REVIEW_CANDIDATE_COUNT = 5
DEFAULT_CANDIDATE_COUNT = 3
ROUTE_PRIORITY = [
    "diagram/svg",
    "chart",
    "image_search",
    "image_generation",
    "none",
]

SEARCH_PROVIDER_ENV = {
    "unsplash": "UNSPLASH_ACCESS_KEY",
    "pexels": "PEXELS_API_KEY",
    "pixabay": "PIXABAY_API_KEY",
}
IMAGE_GENERATION_PROVIDER_ENV = {
    "qwen": "QWEN_IMAGE_API_KEY",
    "wanx": "WANX_API_KEY",
    "gemini": "GEMINI_API_KEY",
}


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


def _safe_slug(value: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", value.lower()).strip("-")
    return slug or "asset"


def _must_show_list(asset_intent: dict) -> list[str]:
    return [str(item) for item in asset_intent.get("must_show", []) if str(item).strip()]


def choose_primary_route(asset_intent: dict) -> str:
    candidates = asset_intent.get("candidate_asset_types", [])
    for route in ROUTE_PRIORITY:
        if route in candidates:
            return route
    return "none"


def build_asset_plan_entry(slide: int, critical_visual: bool, asset_intent: dict) -> dict:
    primary_route = choose_primary_route(asset_intent)
    fallback_routes = [route for route in asset_intent.get("candidate_asset_types", []) if route != primary_route]
    return {
        "slide": slide,
        "asset_slots": [
            {
                "slot": "primary",
                "primary_route": primary_route,
                "fallback_routes": fallback_routes,
                "candidate_count": CRITICAL_REVIEW_CANDIDATE_COUNT if critical_visual else DEFAULT_CANDIDATE_COUNT,
                "independent_asset_review": critical_visual,
                "critical_visual": critical_visual,
            }
        ],
    }


def load_slide_blueprint(workspace) -> dict:
    if not workspace.slide_blueprint_path.exists():
        raise FileNotFoundError(f"missing slide blueprint: {workspace.slide_blueprint_path}")
    return _load_json(workspace.slide_blueprint_path)


def build_visual_asset_plan(workspace) -> dict:
    blueprint = load_slide_blueprint(workspace)
    slides = []
    for slide in blueprint.get("slides", []):
        entry = build_asset_plan_entry(
            slide=slide["slide"],
            critical_visual=bool(slide.get("critical_visual", False)),
            asset_intent=slide.get("asset_intent", {}),
        )
        entry["title"] = slide.get("title", f"Slide {slide['slide']}")
        entry["visual_goal"] = slide.get("visual_goal", "")
        entry["wow_goal"] = slide.get("wow_goal") or slide.get("asset_intent", {}).get("wow_goal", "")
        entry["rollback_scope_default"] = slide.get("rollback_scope_default", "slide_local")
        entry["shared_visual_dependencies"] = slide.get("shared_visual_dependencies", [])
        slides.append(entry)

    payload = {
        "project_id": workspace.project_id,
        "slides": slides,
    }
    _write_json(workspace.visual_asset_plan_path, payload)
    return payload


def _route_to_source(route: str) -> tuple[str, str]:
    if route == "diagram/svg":
        return ("diagram/svg", "local_svg_renderer")
    if route == "chart":
        return ("chart", "local_chart_renderer")
    if route == "image_search":
        return ("image_search", _first_configured_provider(SEARCH_PROVIDER_ENV) or "unconfigured")
    if route == "image_generation":
        return ("image_generation", _first_configured_provider(IMAGE_GENERATION_PROVIDER_ENV) or "unconfigured")
    return ("none", "none")


def _first_configured_provider(provider_map: dict[str, str]) -> str | None:
    for provider, env_name in provider_map.items():
        if os.getenv(env_name):
            return provider
    return None


def _asset_query(slide_meta: dict, asset_intent: dict) -> str:
    bits = [slide_meta.get("title", ""), asset_intent.get("asset_goal", "")]
    must_show = _must_show_list(asset_intent)
    if must_show:
        bits.append("must show: " + ", ".join(must_show))
    return " | ".join(bit for bit in bits if bit)


def _relative_asset_path(workspace, path: Path) -> str:
    return path.relative_to(workspace.project_dir).as_posix()


def _write_asset_svg(workspace, filename: str, body: str) -> str:
    asset_path = workspace.assets_dir / filename
    asset_path.write_text(body, encoding="utf-8")
    return _relative_asset_path(workspace, asset_path)


def _diagram_candidate_svg(title: str, labels: list[str], variant: int) -> str:
    positions = [
        [(400, 150), (220, 420), (580, 420)],
        [(400, 135), (235, 430), (565, 430)],
        [(400, 165), (205, 410), (595, 410)],
        [(400, 145), (245, 405), (555, 405)],
        [(400, 160), (225, 435), (575, 435)],
    ]
    palette = [
        ("#2563EB", "#DBEAFE"),
        ("#059669", "#D1FAE5"),
        ("#D97706", "#FEF3C7"),
        ("#1D4ED8", "#E0F2FE"),
        ("#047857", "#ECFDF5"),
    ]
    coords = positions[(variant - 1) % len(positions)]
    primary, surface = palette[(variant - 1) % len(palette)]
    circles = []
    for index, label in enumerate(labels[:3] or ["Focus", "Structure", "Decision"]):
        x, y = coords[index]
        circles.append(
            f'<circle cx="{x}" cy="{y}" r="88" fill="{surface}" stroke="{primary}" stroke-width="4" />'
            f'<text x="{x}" y="{y + 6}" text-anchor="middle" font-family="Inter, Arial" font-size="28" '
            f'font-weight="700" fill="#0F172A">{escape(label)}</text>'
        )
    lines = [
        f'<line x1="{coords[0][0]}" y1="{coords[0][1] + 88}" x2="{coords[1][0] + 66}" y2="{coords[1][1] - 44}" '
        f'stroke="{primary}" stroke-width="4" opacity="0.85" />',
        f'<line x1="{coords[0][0]}" y1="{coords[0][1] + 88}" x2="{coords[2][0] - 66}" y2="{coords[2][1] - 44}" '
        f'stroke="{primary}" stroke-width="4" opacity="0.85" />',
        f'<line x1="{coords[1][0] + 88}" y1="{coords[1][1]}" x2="{coords[2][0] - 88}" y2="{coords[2][1]}" '
        f'stroke="{primary}" stroke-width="4" opacity="0.85" />',
    ]
    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 800 600" role="img">
  <rect width="800" height="600" rx="36" fill="#F8FAFC" />
  <text x="64" y="72" font-family="Inter, Arial" font-size="34" font-weight="700" fill="#0F172A">{escape(title)}</text>
  <text x="64" y="112" font-family="Inter, Arial" font-size="18" fill="#475569">Diagram candidate {variant}</text>
  {''.join(lines)}
  {''.join(circles)}
</svg>
"""


def _chart_candidate_svg(title: str, data_points: list[dict], variant: int) -> str:
    width = 800
    height = 520
    chart_left = 92
    chart_bottom = 420
    chart_height = 250
    step = 190 if len(data_points) <= 1 else 540 / max(len(data_points) - 1, 1)
    max_value = max((float(point.get("value", 0)) for point in data_points), default=100.0) or 100.0
    colors = ["#2563EB", "#059669", "#D97706"]
    points = []
    labels = []
    for index, point in enumerate(data_points):
        x = chart_left + index * step
        value = float(point.get("value", 0))
        y = chart_bottom - (value / max_value) * chart_height
        points.append((x, y, value, str(point.get("label", f"P{index + 1}"))))
        labels.append(
            f'<text x="{x}" y="{chart_bottom + 36}" text-anchor="middle" font-family="Inter, Arial" '
            f'font-size="20" fill="#334155">{escape(str(point.get("label", "")))}</text>'
        )
    polyline = " ".join(f"{x},{y}" for x, y, _, _ in points)
    point_nodes = []
    for index, (x, y, value, label) in enumerate(points):
        color = colors[index % len(colors)]
        point_nodes.append(
            f'<circle cx="{x}" cy="{y}" r="{8 + (variant % 2)}" fill="{color}" />'
            f'<text x="{x}" y="{y - 18}" text-anchor="middle" font-family="Inter, Arial" font-size="18" '
            f'font-weight="700" fill="#0F172A">{int(value)}</text>'
        )
    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" role="img">
  <rect width="{width}" height="{height}" rx="32" fill="#FFFFFF" />
  <text x="64" y="68" font-family="Inter, Arial" font-size="34" font-weight="700" fill="#0F172A">{escape(title)}</text>
  <text x="64" y="104" font-family="Inter, Arial" font-size="18" fill="#475569">Chart candidate {variant}</text>
  <line x1="{chart_left}" y1="{chart_bottom}" x2="700" y2="{chart_bottom}" stroke="#CBD5E1" stroke-width="3" />
  <line x1="{chart_left}" y1="150" x2="{chart_left}" y2="{chart_bottom}" stroke="#CBD5E1" stroke-width="3" />
  <polyline fill="none" stroke="#2563EB" stroke-width="{4 + (variant % 2)}" points="{polyline}" />
  {''.join(point_nodes)}
  {''.join(labels)}
</svg>
"""


def _build_diagram_candidates(workspace, slide_meta: dict, slot: dict, asset_intent: dict) -> list[dict]:
    labels = _must_show_list(asset_intent)
    title = slide_meta.get("title", f"Slide {slide_meta['slide']}")
    candidates = []
    for variant in range(1, slot["candidate_count"] + 1):
        filename = f"slide_{slide_meta['slide']:02d}_{slot['slot']}_diagram_{variant:02d}.svg"
        path = _write_asset_svg(workspace, filename, _diagram_candidate_svg(title, labels, variant))
        candidates.append(
            {
                "candidate_id": f"{slide_meta['slide']}-{slot['slot']}-diagram-{variant}",
                "path": path,
                "status": "ready",
                "score": round(9.4 - (variant - 1) * 0.2, 2),
                "variant": variant,
            }
        )
    return candidates


def _build_chart_candidates(workspace, slide_meta: dict, slot: dict, asset_intent: dict) -> list[dict]:
    title = slide_meta.get("title", f"Slide {slide_meta['slide']}")
    raw_points = asset_intent.get("data_points") or [
        {"label": label, "value": 30 + index * 15} for index, label in enumerate(_must_show_list(asset_intent)[:4])
    ]
    candidates = []
    for variant in range(1, slot["candidate_count"] + 1):
        filename = f"slide_{slide_meta['slide']:02d}_{slot['slot']}_chart_{variant:02d}.svg"
        path = _write_asset_svg(workspace, filename, _chart_candidate_svg(title, raw_points, variant))
        candidates.append(
            {
                "candidate_id": f"{slide_meta['slide']}-{slot['slot']}-chart-{variant}",
                "path": path,
                "status": "ready",
                "score": round(9.1 - (variant - 1) * 0.15, 2),
                "variant": variant,
            }
        )
    return candidates


def _build_remote_placeholder(slide_meta: dict, slot: dict, route: str, provider_map: dict[str, str], asset_intent: dict) -> tuple[list[dict], dict, str]:
    provider = _first_configured_provider(provider_map)
    query = _asset_query(slide_meta, asset_intent)
    if provider:
        candidate = {
            "candidate_id": f"{slide_meta['slide']}-{slot['slot']}-{route}-provider",
            "status": "provider_ready",
            "provider": provider,
            "query": query,
        }
        return [candidate], candidate, "pending"

    unavailable = {
        "candidate_id": f"{slide_meta['slide']}-{slot['slot']}-{route}-unavailable",
        "status": "unavailable",
        "reason": f"configure one of: {', '.join(provider_map.values())}",
        "query": query,
    }
    return [], unavailable, "blocked"


def _select_best_candidate(candidates: list[dict]) -> dict:
    return max(candidates, key=lambda item: item.get("score", 0.0))


def build_visual_asset_manifest(workspace) -> dict:
    plan = _load_json(workspace.visual_asset_plan_path) if workspace.visual_asset_plan_path.exists() else build_visual_asset_plan(workspace)
    blueprint = load_slide_blueprint(workspace)
    blueprint_by_slide = {entry["slide"]: entry for entry in blueprint.get("slides", [])}
    assets = []

    for slide_entry in plan.get("slides", []):
        slide_meta = blueprint_by_slide.get(slide_entry["slide"], {"slide": slide_entry["slide"], "title": slide_entry.get("title", "")})
        asset_intent = slide_meta.get("asset_intent", {})
        for slot in slide_entry.get("asset_slots", []):
            route = slot["primary_route"]
            source_type, source_provider = _route_to_source(route)
            asset_id = f"slide-{slide_entry['slide']}-{slot['slot']}"
            review_status = "approved"
            selection_rationale = f"Selected the highest-scoring {route} candidate for slide {slide_entry['slide']}."

            if route == "diagram/svg":
                candidate_assets = _build_diagram_candidates(workspace, slide_meta, slot, asset_intent)
                selected_asset = _select_best_candidate(candidate_assets)
            elif route == "chart":
                candidate_assets = _build_chart_candidates(workspace, slide_meta, slot, asset_intent)
                selected_asset = _select_best_candidate(candidate_assets)
            elif route == "image_search":
                candidate_assets, selected_asset, review_status = _build_remote_placeholder(
                    slide_meta,
                    slot,
                    route,
                    SEARCH_PROVIDER_ENV,
                    asset_intent,
                )
                selection_rationale = "Blocked until an image-search provider key is configured." if review_status == "blocked" else "Provider route prepared."
            elif route == "image_generation":
                candidate_assets, selected_asset, review_status = _build_remote_placeholder(
                    slide_meta,
                    slot,
                    route,
                    IMAGE_GENERATION_PROVIDER_ENV,
                    asset_intent,
                )
                selection_rationale = "Blocked until an image-generation provider key is configured." if review_status == "blocked" else "Provider route prepared."
            else:
                candidate_assets = []
                selected_asset = {"status": "not_required"}
                review_status = "approved"
                selection_rationale = "No visual asset is required for this slide."

            asset = {
                "asset_id": asset_id,
                "slide": slide_entry["slide"],
                "slot": slot["slot"],
                "asset_type": route,
                "source_type": source_type,
                "source_provider": source_provider,
                "prompt_or_query": _asset_query(slide_meta, asset_intent),
                "candidate_assets": candidate_assets,
                "selected_asset": selected_asset,
                "selection_rationale": selection_rationale,
                "review_status": review_status,
                "license_metadata": {},
                "resolution_metadata": {"candidate_count": len(candidate_assets)},
                "rollback_scope": slide_meta.get("rollback_scope_default", "slide_local"),
            }
            assets.append(asset)

    payload = {"project_id": workspace.project_id, "assets": assets}
    _write_json(workspace.visual_asset_manifest_path, payload)
    return payload
