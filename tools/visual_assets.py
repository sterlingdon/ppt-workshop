from __future__ import annotations


CRITICAL_REVIEW_CANDIDATE_COUNT = 5
DEFAULT_CANDIDATE_COUNT = 3
ROUTE_PRIORITY = [
    "diagram/svg",
    "chart",
    "image_search",
    "image_generation",
    "none",
]


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
