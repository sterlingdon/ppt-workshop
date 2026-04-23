from __future__ import annotations

import json
import re


STAGE_ARTIFACTS = {
    "visual_review": ["visual_review_report.json", "review/full_deck.png", "review/slides"],
    "visual_asset_plan": ["visual_asset_plan.json"],
    "visual_asset_manifest": ["visual_asset_manifest.json", "assets"],
    "slide_blueprint": ["slide_blueprint.json"],
    "design_dna": ["design_dna.json", "outline.json", "slide_blueprint.json"],
}

STAGE_KEYWORDS = [
    ("design_dna", ("design dna", "design_dna")),
    ("slide_blueprint", ("blueprint", "visual anchor", "asset intent")),
    ("visual_asset_manifest", ("asset manifest", "asset system", "assets", "搜图", "出图", "chart", "diagram")),
    ("visual_review", ("visual review", "review", "screenshots")),
]


def _extract_slide_targets(message: str) -> list[str]:
    numbers = re.findall(r"slide\s*[_-]?(\d+)", message, flags=re.IGNORECASE)
    seen: set[str] = set()
    targets: list[str] = []
    for number in numbers:
        target = f"Slide_{int(number)}"
        if target not in seen:
            seen.add(target)
            targets.append(target)
    return targets


def _infer_restart_stage(message: str, default_stage: str) -> str:
    lowered = message.lower()
    for stage, keywords in STAGE_KEYWORDS:
        if any(keyword in lowered for keyword in keywords):
            return stage
    return default_stage


def _infer_expected_change(message: str, targets: list[str], restart_stage: str) -> str:
    lowered = message.lower()
    if targets and any(keyword in lowered for keyword in ("triangle", "三角")):
        return f"rebuild the triangle diagram on {targets[0]}"
    if restart_stage == "design_dna":
        return "rework the deck visual contract"
    if targets:
        return f"rework the visual composition on {targets[0]}"
    return "rework the affected visual system"


def _infer_rollback_level(message: str, targets: list[str], restart_stage: str) -> str:
    lowered = message.lower()
    if restart_stage == "design_dna":
        return "deck_global"
    if any(keyword in lowered for keyword in ("shared", "system", "整套", "全局", "pattern")):
        return "pattern_shared"
    if targets:
        return "slide_local"
    return "pattern_shared"


def _invalidated_artifacts(targets: list[str], restart_stage: str, rollback_level: str) -> list[str]:
    artifacts = list(STAGE_ARTIFACTS.get(restart_stage, []))
    if rollback_level == "slide_local":
        for target in targets:
            artifacts.extend(
                [
                    f"slides/{target}.tsx",
                    f"review/{target}.png",
                    f"assets/{target}",
                ]
            )
    return sorted(set(artifacts))


def normalize_feedback(message: str, default_stage: str) -> dict:
    restart_stage = _infer_restart_stage(message, default_stage)
    targets = _extract_slide_targets(message)
    rollback_level = _infer_rollback_level(message, targets, restart_stage)
    invalidated_artifacts = _invalidated_artifacts(targets, restart_stage, rollback_level)

    return {
        "feedback_scope": "human_async",
        "targets": targets,
        "reason": message,
        "expected_change": _infer_expected_change(message, targets, restart_stage),
        "rollback_level": rollback_level,
        "restart_stage": restart_stage,
        "invalidated_artifacts": invalidated_artifacts,
        "agent_acknowledgement": "",
        "status": "open",
    }


def apply_feedback(workspace, message: str, default_stage: str) -> dict:
    payload = normalize_feedback(message, default_stage=default_stage)
    if not payload["agent_acknowledgement"]:
        payload["agent_acknowledgement"] = (
            f"Captured feedback for {', '.join(payload['targets']) or payload['restart_stage']}; "
            f"rollback level is {payload['rollback_level']} and restart stage is {payload['restart_stage']}."
        )

    items: list[dict] = []
    if workspace.human_feedback_log_path.exists():
        existing = json.loads(workspace.human_feedback_log_path.read_text(encoding="utf-8"))
        items = list(existing.get("items", []))
    items.append(payload)

    workspace.human_feedback_log_path.write_text(
        json.dumps({"items": items}, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    return payload
