from __future__ import annotations

import json
import os
import re
from html import escape
from pathlib import Path

try:
    from .visual_asset_providers import (
        IMAGE_GENERATION_PROVIDER_ENV,
        ProviderRequestError,
        ProviderUnavailableError,
        generate_image_candidates,
    )
except ImportError:
    from visual_asset_providers import (
        IMAGE_GENERATION_PROVIDER_ENV,
        ProviderRequestError,
        ProviderUnavailableError,
        generate_image_candidates,
    )


CRITICAL_REVIEW_CANDIDATE_COUNT = 5
DEFAULT_CANDIDATE_COUNT = 3
ROUTE_PRIORITY = [
    "image_generation",
    "diagram/svg",
    "chart",
    "none",
]
REMOTE_ROUTES = {"image_generation"}
SUPPORTED_ASSET_ROUTES = {"image_generation", "diagram/svg", "chart", "none"}


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _load_optional_json(path: Path) -> dict:
    if not path.exists():
        return {}
    return _load_json(path)


def _write_json(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


def _safe_slug(value: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", value.lower()).strip("-")
    return slug or "asset"


def _must_show_list(asset_intent: dict) -> list[str]:
    return [str(item) for item in asset_intent.get("must_show", []) if str(item).strip()]


def _normalized_text(value: object) -> str:
    return str(value or "").strip().lower()


def _dedupe_texts(items: list[object]) -> list[str]:
    seen: set[str] = set()
    results: list[str] = []
    for item in items:
        text = str(item or "").strip()
        if not text:
            continue
        normalized = text.casefold()
        if normalized in seen:
            continue
        seen.add(normalized)
        results.append(text)
    return results


def _normalized_candidate_routes(asset_intent: dict) -> list[str]:
    normalized: list[str] = []
    for route in asset_intent.get("candidate_asset_types", []):
        resolved = str(route or "").strip()
        if not resolved or resolved not in SUPPORTED_ASSET_ROUTES or resolved in normalized:
            continue
        normalized.append(resolved)
    return normalized


def _prefer_photo_first(asset_intent: dict, critical_visual: bool) -> bool:
    if not asset_intent:
        return False
    visual_role = _normalized_text(asset_intent.get("visual_role"))
    wow_goal = _normalized_text(asset_intent.get("wow_goal"))
    asset_goal = _normalized_text(asset_intent.get("asset_goal"))
    composition_hint = _normalized_text(asset_intent.get("composition_hint"))
    dominant_zone = _normalized_text(asset_intent.get("dominant_zone"))
    keyword_blob = " ".join([visual_role, wow_goal, asset_goal, composition_hint, dominant_zone])
    photo_terms = (
        "photo",
        "photography",
        "real-world",
        "real world",
        "realistic",
        "editorial",
        "atmosphere",
        "mood",
        "hero",
        "full-bleed",
        "full bleed",
        "cover",
        "scene",
        "human",
        "people",
    )
    visual_roles = {
        "hero",
        "supporting_evidence",
        "case_study",
        "context_scene",
        "scene_setter",
        "opener",
    }
    if visual_role in visual_roles:
        return True
    if any(term in keyword_blob for term in photo_terms):
        return True
    return critical_visual and "diagram" not in keyword_blob and "chart" not in keyword_blob


def _prefer_diagram_first(asset_intent: dict) -> bool:
    if not asset_intent:
        return False
    visual_role = _normalized_text(asset_intent.get("visual_role"))
    wow_goal = _normalized_text(asset_intent.get("wow_goal"))
    asset_goal = _normalized_text(asset_intent.get("asset_goal"))
    keyword_blob = " ".join([visual_role, wow_goal, asset_goal])
    diagram_roles = {
        "core_explainer",
        "framework",
        "process",
        "system_map",
        "mechanism",
    }
    if visual_role in diagram_roles:
        return True
    return any(term in keyword_blob for term in ("diagram", "framework", "relationship", "process", "system"))


def _prefer_chart_first(asset_intent: dict) -> bool:
    if not asset_intent:
        return False
    visual_role = _normalized_text(asset_intent.get("visual_role"))
    wow_goal = _normalized_text(asset_intent.get("wow_goal"))
    asset_goal = _normalized_text(asset_intent.get("asset_goal"))
    keyword_blob = " ".join([visual_role, wow_goal, asset_goal])
    if visual_role in {"data_evidence", "trend", "metric", "comparison_data"}:
        return True
    return any(term in keyword_blob for term in ("chart", "trend", "data", "metric", "compare"))


def choose_primary_route(asset_intent: dict, critical_visual: bool = False) -> str:
    candidates = _normalized_candidate_routes(asset_intent)
    if not candidates:
        return "none"
    if _prefer_photo_first(asset_intent, critical_visual):
        for route in ("image_generation",):
            if route in candidates:
                return route
    if _prefer_chart_first(asset_intent) and "chart" in candidates:
        return "chart"
    if _prefer_diagram_first(asset_intent) and "diagram/svg" in candidates:
        return "diagram/svg"
    for route in ROUTE_PRIORITY:
        if route in candidates:
            return route
    return "none"


def _selection_criteria(route: str, critical_visual: bool) -> list[str]:
    criteria = ["goal_match", "composition_fit", "anti_template_risk"]
    if route in REMOTE_ROUTES:
        criteria.append("subject_relevance")
        criteria.append("crop_resilience")
    if route == "diagram/svg":
        criteria.append("explanatory_clarity")
    if route == "chart":
        criteria.append("data_readability")
    if critical_visual:
        criteria.append("distinctiveness")
    return criteria


def _placement_contract(route: str, asset_intent: dict, critical_visual: bool) -> dict:
    dominant_zone = str(asset_intent.get("dominant_zone") or "").strip() or ("full-bleed" if critical_visual else "side-panel")
    composition_hint = str(asset_intent.get("composition_hint") or "").strip()
    if route in REMOTE_ROUTES:
        mode = "dominant" if critical_visual else "supportive"
        crop_preference = "cover" if dominant_zone in {"full-bleed", "cover", "background"} else "framed"
    elif route == "diagram/svg":
        mode = "anchored-explainer"
        crop_preference = "none"
    elif route == "chart":
        mode = "evidence-panel"
        crop_preference = "none"
    else:
        mode = "typography-first"
        crop_preference = "none"
    return {
        "mode": mode,
        "dominant_zone": dominant_zone,
        "crop_preference": crop_preference,
        "content_priority": "preserve_text_clear_space" if route in REMOTE_ROUTES else "preserve_readability",
        "composition_hint": composition_hint,
    }


def _fallback_strategy(primary_route: str, fallback_routes: list[str], asset_intent: dict) -> str:
    explicit = str(asset_intent.get("fallback_visual_strategy") or "").strip()
    if explicit:
        return explicit
    if primary_route in REMOTE_ROUTES:
        if "diagram/svg" in fallback_routes:
            return "If photo/generation fails, switch to a premium typography-plus-diagram composition."
        if "chart" in fallback_routes:
            return "If image routes fail, elevate the evidence chart and let typography carry mood."
        return "If image routes fail, switch to a typography-first layout with no weak placeholder art."
    return "If the planned asset underperforms, simplify the page and strengthen typography instead of adding filler."


def _design_context(workspace) -> tuple[dict, dict]:
    recommendation = _load_optional_json(workspace.project_dir / "design_recommendation.json")
    design_dna = _load_optional_json(workspace.project_dir / "design_dna.json")
    return recommendation, design_dna


def build_visual_asset_research(workspace) -> dict:
    blueprint = load_slide_blueprint(workspace)
    recommendation, design_dna = _design_context(workspace)
    asset_direction = recommendation.get("asset_direction") or {}
    visual_language = design_dna.get("visual_language") or {}
    deck_visual_strategy = str(design_dna.get("visual_direction") or recommendation.get("visual_direction") or "").strip()
    slides = []

    for slide in blueprint.get("slides", []):
        asset_intent = slide.get("asset_intent", {})
        primary_route = choose_primary_route(asset_intent, critical_visual=bool(slide.get("critical_visual", False)))
        research_tags = _dedupe_texts(
            list(asset_intent.get("visual_cues") or [])
            + list(asset_direction.get("visual_cues") or [])
            + list(asset_intent.get("generation_cues") or [])
            + list(asset_direction.get("generation_cues") or [])
            + list(asset_intent.get("must_show") or [])
            + list(asset_direction.get("image_mood") or [])
            + list(visual_language.get("image_mood") or [])
        )
        reject_if = _dedupe_texts(list(asset_intent.get("must_avoid") or []) + ["generic enterprise stock pose", "equal-width card-grid energy"])
        desired_composition = str(asset_intent.get("composition_hint") or slide.get("layout_pattern") or "").strip()
        desired_mood = ", ".join(_dedupe_texts(list(asset_direction.get("image_mood") or []) + list(visual_language.get("image_mood") or [])))
        slides.append(
            {
                "slide": slide["slide"],
                "title": slide.get("title", f"Slide {slide['slide']}"),
                "primary_route": primary_route,
                "research_query": _asset_query(slide, asset_intent),
                "research_tags": research_tags,
                "visual_motif": str(asset_intent.get("visual_role") or "").strip(),
                "desired_composition": desired_composition,
                "desired_mood": desired_mood,
                "reject_if": reject_if,
                "sourcing_guidance": _dedupe_texts(
                    [
                        str(asset_intent.get("asset_goal") or "").strip(),
                        str(asset_direction.get("icon_style") or "").strip(),
                        str(asset_direction.get("diagram_style") or "").strip(),
                    ]
                ),
            }
        )

    payload = {
        "project_id": workspace.project_id,
        "deck_visual_strategy": deck_visual_strategy,
        "slides": slides,
    }
    _write_json(workspace.visual_asset_research_path, payload)
    return payload


def build_asset_plan_entry(slide: int, critical_visual: bool, asset_intent: dict, research_entry: dict | None = None) -> dict:
    primary_route = choose_primary_route(asset_intent, critical_visual=critical_visual)
    fallback_routes = [route for route in _normalized_candidate_routes(asset_intent) if route != primary_route]
    research_entry = research_entry or {}
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
                "research_query": research_entry.get("research_query", ""),
                "research_tags": research_entry.get("research_tags", []),
                "selection_criteria": _selection_criteria(primary_route, critical_visual),
                "placement_contract": _placement_contract(primary_route, asset_intent, critical_visual),
                "fallback_strategy": _fallback_strategy(primary_route, fallback_routes, asset_intent),
                "premium_fallback_required": primary_route in REMOTE_ROUTES,
            }
        ],
    }


def load_slide_blueprint(workspace) -> dict:
    if not workspace.slide_blueprint_path.exists():
        raise FileNotFoundError(f"missing slide blueprint: {workspace.slide_blueprint_path}")
    return _load_json(workspace.slide_blueprint_path)


def build_visual_asset_plan(workspace) -> dict:
    blueprint = load_slide_blueprint(workspace)
    research = (
        _load_json(workspace.visual_asset_research_path)
        if workspace.visual_asset_research_path.exists()
        else build_visual_asset_research(workspace)
    )
    research_by_slide = {entry["slide"]: entry for entry in research.get("slides", [])}
    slides = []
    for slide in blueprint.get("slides", []):
        entry = build_asset_plan_entry(
            slide=slide["slide"],
            critical_visual=bool(slide.get("critical_visual", False)),
            asset_intent=slide.get("asset_intent", {}),
            research_entry=research_by_slide.get(slide["slide"], {}),
        )
        entry["title"] = slide.get("title", f"Slide {slide['slide']}")
        entry["visual_goal"] = slide.get("visual_goal", "")
        entry["wow_goal"] = slide.get("wow_goal") or slide.get("asset_intent", {}).get("wow_goal", "")
        entry["rollback_scope_default"] = slide.get("rollback_scope_default", "slide_local")
        entry["shared_visual_dependencies"] = slide.get("shared_visual_dependencies", [])
        slides.append(entry)

    payload = {
        "project_id": workspace.project_id,
        "research_artifact": workspace.visual_asset_research_path.name,
        "slides": slides,
    }
    _write_json(workspace.visual_asset_plan_path, payload)
    return payload


def _route_to_source(route: str) -> tuple[str, str]:
    if route == "diagram/svg":
        return ("diagram/svg", "local_svg_renderer")
    if route == "chart":
        return ("chart", "local_chart_renderer")
    if route == "image_generation":
        return ("image_generation", _first_configured_provider(IMAGE_GENERATION_PROVIDER_ENV) or "unconfigured")
    return ("none", "none")


def _first_configured_provider(provider_map: dict[str, str]) -> str | None:
    for provider, env_names in provider_map.items():
        if isinstance(env_names, str):
            env_names = (env_names,)
        if any(os.getenv(env_name) for env_name in env_names):
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


def _normalize_candidate_paths(workspace, candidates: list[dict]) -> list[dict]:
    normalized = []
    for candidate in candidates:
        entry = dict(candidate)
        local_path = entry.get("local_path")
        if local_path:
            entry["path"] = _relative_asset_path(workspace, Path(local_path))
            entry.pop("local_path", None)
        normalized.append(entry)
    return normalized


def _rank_candidate_assets(candidates: list[dict], route: str, asset_intent: dict, critical_visual: bool) -> list[dict]:
    rankings = []
    must_show_bonus = min(len(_must_show_list(asset_intent)) * 0.15, 0.6)
    route_bonus = 0.3 if route in REMOTE_ROUTES and critical_visual else 0.15 if route in {"diagram/svg", "chart"} else 0.0
    for index, candidate in enumerate(candidates, start=1):
        base_score = float(candidate.get("score", 0.0) or 0.0)
        status = str(candidate.get("status", "ready"))
        implementation_confidence = 9.2 if status in {"ready", "provider_ready"} else 4.0 if status == "pending" else 2.0
        composition_fit = min(base_score + (0.25 if critical_visual else 0.0), 10.0)
        goal_match = min(base_score + must_show_bonus, 10.0)
        distinctiveness = min(base_score + route_bonus, 10.0)
        total_score = round((goal_match * 0.38) + (composition_fit * 0.27) + (distinctiveness * 0.2) + (implementation_confidence * 0.15), 2)
        rankings.append(
            {
                "candidate_id": candidate.get("candidate_id", f"candidate-{index}"),
                "rank": index,
                "total_score": total_score,
                "criteria_scores": {
                    "goal_match": round(goal_match, 2),
                    "composition_fit": round(composition_fit, 2),
                    "distinctiveness": round(distinctiveness, 2),
                    "implementation_confidence": round(implementation_confidence, 2),
                },
                "notes": f"Route {route} ranking based on asset goal, composition fit, and implementation confidence.",
            }
        )
    rankings.sort(key=lambda item: item["total_score"], reverse=True)
    for rank, item in enumerate(rankings, start=1):
        item["rank"] = rank
    return rankings


def _selected_candidate_from_rankings(candidates: list[dict], rankings: list[dict]) -> dict:
    if not candidates:
        return {"status": "not_required"}
    candidate_by_id = {candidate.get("candidate_id"): candidate for candidate in candidates}
    top_candidate = rankings[0] if rankings else None
    if top_candidate and top_candidate.get("candidate_id") in candidate_by_id:
        return candidate_by_id[top_candidate["candidate_id"]]
    return _select_best_candidate(candidates)


def _build_remote_candidates(
    workspace,
    slide_entry: dict,
    slide_meta: dict,
    slot: dict,
    route: str,
    asset_intent: dict,
    research_entry: dict | None = None,
) -> tuple[list[dict], dict, str, str]:
    query = _asset_query(slide_meta, asset_intent)
    asset_prefix = f"slide_{slide_entry['slide']:02d}_{slot['slot']}_generated"
    try:
        candidates = generate_image_candidates(
            prompt=query,
            candidate_count=slot["candidate_count"],
            workspace_root=workspace.assets_dir,
            asset_prefix=asset_prefix,
        )
    except (ProviderUnavailableError, ProviderRequestError) as exc:
        blocked = {
            "candidate_id": f"{slide_entry['slide']}-{slot['slot']}-{route}-unavailable",
            "status": "unavailable",
            "reason": str(exc),
            "query": query,
        }
        return [], blocked, "blocked", str(exc)

    normalized_candidates = _normalize_candidate_paths(workspace, candidates)
    selected = _select_best_candidate(normalized_candidates)
    rationale = f"Selected the highest-scoring generated image candidate for slide {slide_entry['slide']}."
    return normalized_candidates, selected, "approved", rationale


def _materialize_asset_route(
    workspace,
    slide_entry: dict,
    slide_meta: dict,
    slot: dict,
    route: str,
    asset_intent: dict,
    research_entry: dict | None = None,
) -> tuple[str, str, list[dict], dict, str, str]:
    source_type, source_provider = _route_to_source(route)
    if route == "diagram/svg":
        candidate_assets = _build_diagram_candidates(workspace, slide_meta, slot, asset_intent)
        selected_asset = _select_best_candidate(candidate_assets)
        return source_type, source_provider, candidate_assets, selected_asset, "approved", f"Selected the strongest diagram candidate for slide {slide_entry['slide']}."
    if route == "chart":
        candidate_assets = _build_chart_candidates(workspace, slide_meta, slot, asset_intent)
        selected_asset = _select_best_candidate(candidate_assets)
        return source_type, source_provider, candidate_assets, selected_asset, "approved", f"Selected the clearest chart candidate for slide {slide_entry['slide']}."
    if route == "image_generation":
        candidate_assets, selected_asset, review_status, selection_rationale = _build_remote_candidates(
            workspace,
            slide_entry,
            slide_meta,
            slot,
            route,
            asset_intent,
            research_entry=research_entry,
        )
        return source_type, source_provider, candidate_assets, selected_asset, review_status, selection_rationale
    return source_type, source_provider, [], {"status": "not_required"}, "approved", "No visual asset is required for this slide."


def build_visual_asset_manifest(workspace) -> dict:
    plan = _load_json(workspace.visual_asset_plan_path) if workspace.visual_asset_plan_path.exists() else build_visual_asset_plan(workspace)
    research = (
        _load_json(workspace.visual_asset_research_path)
        if workspace.visual_asset_research_path.exists()
        else build_visual_asset_research(workspace)
    )
    blueprint = load_slide_blueprint(workspace)
    blueprint_by_slide = {entry["slide"]: entry for entry in blueprint.get("slides", [])}
    research_by_slide = {entry["slide"]: entry for entry in research.get("slides", [])}
    assets = []

    for slide_entry in plan.get("slides", []):
        slide_meta = blueprint_by_slide.get(slide_entry["slide"], {"slide": slide_entry["slide"], "title": slide_entry.get("title", "")})
        asset_intent = slide_meta.get("asset_intent", {})
        research_entry = research_by_slide.get(slide_entry["slide"], {})
        for slot in slide_entry.get("asset_slots", []):
            requested_route = str(slot["primary_route"]).strip()
            route_attempts = []
            for route in [requested_route, *slot.get("fallback_routes", [])]:
                normalized_route = str(route or "").strip()
                if normalized_route and normalized_route in SUPPORTED_ASSET_ROUTES and normalized_route not in route_attempts:
                    route_attempts.append(normalized_route)
            asset_id = f"slide-{slide_entry['slide']}-{slot['slot']}"
            resolved_route = requested_route
            fallback_applied = {"used": False, "from_route": requested_route, "to_route": requested_route, "reason": ""}
            source_type = "none"
            source_provider = "none"
            candidate_assets: list[dict] = []
            selected_asset: dict = {"status": "not_required"}
            review_status = "approved"
            selection_rationale = f"Selected the highest-scoring {requested_route} candidate for slide {slide_entry['slide']}."

            for attempt_index, route in enumerate(route_attempts):
                source_type, source_provider, candidate_assets, selected_asset, review_status, selection_rationale = _materialize_asset_route(
                    workspace,
                    slide_entry,
                    slide_meta,
                    slot,
                    route,
                    asset_intent,
                    research_entry=research_entry,
                )
                resolved_route = route
                if review_status != "blocked":
                    if route != requested_route:
                        fallback_applied = {
                            "used": True,
                            "from_route": requested_route,
                            "to_route": route,
                            "reason": f"Primary route was blocked; using fallback route {route}.",
                        }
                    break
                if attempt_index == len(route_attempts) - 1:
                    fallback_applied = {
                        "used": requested_route != route,
                        "from_route": requested_route,
                        "to_route": route,
                        "reason": selected_asset.get("reason", "All configured routes failed."),
                    }

            candidate_ranking = _rank_candidate_assets(
                candidate_assets,
                resolved_route,
                asset_intent,
                bool(slot.get("critical_visual", False)),
            )
            if candidate_ranking:
                selected_asset = _selected_candidate_from_rankings(candidate_assets, candidate_ranking)
                if fallback_applied["used"]:
                    selection_rationale = (
                        f"Primary route {requested_route} was unavailable; "
                        f"selected the best-ranked {resolved_route} fallback candidate for slide {slide_entry['slide']}."
                    )
                else:
                    selection_rationale = f"Selected the best-ranked {resolved_route} candidate for slide {slide_entry['slide']}."

            asset = {
                "asset_id": asset_id,
                "slide": slide_entry["slide"],
                "slot": slot["slot"],
                "asset_type": resolved_route,
                "source_type": source_type,
                "source_provider": selected_asset.get("source_provider", source_provider),
                "prompt_or_query": _asset_query(slide_meta, asset_intent),
                "candidate_assets": candidate_assets,
                "selected_asset": selected_asset,
                "candidate_ranking": candidate_ranking,
                "selection_rationale": selection_rationale,
                "review_status": review_status,
                "research_summary": {
                    "research_query": research_entry.get("research_query", ""),
                    "research_tags": research_entry.get("research_tags", []),
                    "desired_composition": research_entry.get("desired_composition", ""),
                    "reject_if": research_entry.get("reject_if", []),
                },
                "placement_decision": {
                    **dict(slot.get("placement_contract") or {}),
                    "resolved_route": resolved_route,
                    "critical_visual": bool(slot.get("critical_visual", False)),
                },
                "fallback_applied": fallback_applied,
                "license_metadata": selected_asset.get("license_metadata", {}),
                "resolution_metadata": {"candidate_count": len(candidate_assets), **selected_asset.get("resolution_metadata", {})},
                "rollback_scope": slide_meta.get("rollback_scope_default", "slide_local"),
            }
            assets.append(asset)

    payload = {"project_id": workspace.project_id, "assets": assets}
    _write_json(workspace.visual_asset_manifest_path, payload)
    return payload
