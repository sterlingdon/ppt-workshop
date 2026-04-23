from __future__ import annotations


STAGE_ARTIFACTS = {
    "visual_review": ["visual_review_report.json", "review/full_deck.png", "review/slides"],
    "design_dna": ["design_dna.json", "outline.json", "slide_blueprint.json"],
}


def normalize_feedback(message: str, default_stage: str) -> dict:
    rollback_level = "slide_local"
    targets: list[str] = []
    invalidated_artifacts = list(STAGE_ARTIFACTS.get(default_stage, []))

    lowered = message.lower()
    if "slide 7" in lowered:
        targets.append("Slide_7")
    if "design dna" in lowered:
        rollback_level = "deck_global"
        invalidated_artifacts.extend(["design_dna.json", "outline.json", "slide_blueprint.json"])

    return {
        "feedback_scope": "human_async",
        "targets": targets,
        "reason": message,
        "expected_change": "rebuild the triangle diagram on Slide_7" if targets == ["Slide_7"] else "rework the deck visual contract",
        "rollback_level": rollback_level,
        "invalidated_artifacts": sorted(set(invalidated_artifacts)),
        "agent_acknowledgement": "",
        "status": "open",
    }
