# Visual Review And Engineering Validation

This workflow has two separate gates:

- **AI Lens Review**: the agent judges and repairs visual quality.
- **Engineering Browser Gate**: Python checks visibility, clipping, coverage, and overflow.

Do not confuse them. The Python validator cannot decide whether a slide is beautiful, persuasive, premium, on-brand, or strategically useful.

## AI Lens Review

Run this before final export and after every meaningful slide redesign.

Input context:

- rendered browser preview with full-deck `?extract=1`
- `review/full_deck.png`
- `review/slides/*.png`
- `references/ppt-visual-design.md`
- `analysis.json`
- `content_quality_report.json`
- `design_dna.json`
- `outline.json`
- `slide_blueprint.json`

The agent must inspect the slides like a visual director, not a DOM validator.

The review screenshots are required inputs. Generate them after the final slide source change and before writing `visual_review_report.json`.

Judge each slide on:

- focal point: what grabs attention in the first 3 seconds
- hierarchy: whether title, anchor, evidence, and detail have clear priority
- type scale: whether title, body, labels, and metrics have presentation-appropriate sizes and weights
- composition: balance, whitespace, grid discipline, and scan path
- information density: enough substance without becoming a wall of text
- visual rhythm: slide-to-slide variation without breaking the visual system
- brand consistency: strict adherence to `design_dna.json`
- audience usefulness: whether the slide helps the reader decide, believe, or remember something
- craft: typography, contrast, alignment, color restraint, icon/chart quality, and overall finish

Reject slides that feel generic, template-like, preset-looking, article-like, empty, cluttered, off-theme, or merely decorative. Also reject slides where text is technically visible but visibly too small, too uniform in weight, poorly spaced, or not integrated into a clear composition.

Write `visual_review_report.json` as an AI audit artifact:

```json
{
  "project_id": "<project-id>",
  "review_type": "ai_lens_visual_review",
  "gate_type": "ai_visual_quality_review",
  "status": "pass",
  "review_assets": {
    "full_deck_screenshot": "review/full_deck.png",
    "slide_screenshots_dir": "review/slides"
  },
  "blocking_findings": 0,
  "repair_log": [],
  "slides": [
    {
      "slide": 1,
      "passed": true,
      "visual_score": 9,
      "findings": [],
      "repairs": []
    }
  ]
}
```

If a slide fails, set `status` to `"blocked"`, repair the React source directly, regenerate review screenshots, and review it again. Do not move to export with unresolved blocking findings.

## Engineering Browser Gate

Run:

```bash
python3 tools/ppt_workflow.py visual-validate --project <project-id>
```

The tool activates the project slides, opens the React preview at `?extract=1`, and writes `visual_validation_report.json`.

It checks:

- expected text is present in the browser preview
- `data-ppt-text` nodes are not hidden
- text is not clipped outside the slide
- text is not covered by another element
- slide content does not overflow the 1920x1080 frame

Pass condition:

```text
visual_validation_report.json.summary.failed == 0
```

## Agent Design Review

The automated gate does not know whether a slide is strategically useful or visually excellent. If the engineering gate passes but the AI Lens Review finds issues, the deck is still not done.

Common false passes:

- A slide is readable but has no strong focal point.
- A slide has visible text but looks generic or low-end.
- Font sizes technically fit but the hierarchy is flat or too small for a real presentation.
- A slide has no overflow but is too dense for presentation use.
- A chart is visible but visually weak or not decision-oriented.
- A deck is technically consistent but monotonous.

## Required Repair Loop

1. Open the full-deck browser preview with `?extract=1`.
2. Capture review screenshots with `python3 tools/ppt_workflow.py review-screenshots --project <project-id>`.
3. Perform AI Lens Review and write/update `visual_review_report.json`.
4. Repair React slides for visual-quality findings.
5. Regenerate `review/full_deck.png` and `review/slides/*.png` after every slide-source repair.
6. Run `visual-validate` and repair engineering findings.
7. If an engineering repair changes any slide source, regenerate review screenshots and repeat AI Lens Review before trusting the engineering pass.
8. Rebuild only when `visual_review_report.json.status == "pass"`, `visual_review_report.json.blocking_findings == 0`, every slide has `passed: true`, every `repair_log` item is `resolved`, and `visual_validation_report.json.summary.failed == 0`.

## Repair Log Contract

For every blocked visual finding, the execution agent must record the repair before asking for re-review:

```json
{
  "id": "V1",
  "source_slide": 3,
  "finding": "Weak focal point and inconsistent accent color.",
  "status": "resolved",
  "changed_artifacts": ["slides/Slide_3.tsx", "review/slides/slide_03.png"],
  "evidence": "Rebuilt the slide around a larger decision matrix, applied --ppt-accent consistently, and regenerated screenshots."
}
```

Do not clear failed slide findings by deleting them without a resolved repair log entry.

## Preview Rules

- Inspect the browser preview, not the PPTX alone.
- Use `?extract=1` for full-deck stacked inspection.
- Do not hide essential human-visible content just to satisfy export behavior.
- A clean automated report is necessary, not sufficient.
