# Content Quality Auditor

The Content Quality Auditor is the first hard gate after article extraction. Its job is to make sure the deck is worth building for a specific audience before Design DNA, outline, or slide coding starts.

## Inputs

- `article_text.md`
- `deck_state.json`
- user request and any audience/goal hints

## Outputs

- `analysis.json`
- `content_quality_report.json`
- updated `deck_state.json`

## Core Checks

- Audience: the deck names a real reader or decision-maker.
- Goal: the deck states what the reader should believe, decide, or remember.
- Thesis: the deck has one clear conclusion, not just a summary of the article.
- Evidence: key claims are backed by extracted facts, statistics, examples, or quotes.
- Emphasis: the strongest article points and data are elevated, not buried.
- Cutting: weak, redundant, or audience-irrelevant material is explicitly excluded.
- Narrative angle: the planned deck has a point of view, not an article-order summary.
- Slide-worthiness: each proposed argument can become a useful presentation page.

## `content_quality_report.json`

Write a compact report before PPT generation:

```json
{
  "project_id": "<project-id>",
  "review_type": "content_quality_audit",
  "status": "pass",
  "audience": "...",
  "goal": "...",
  "core_thesis": "...",
  "must_emphasize": ["..."],
  "must_cut": ["..."],
  "key_data_points": ["..."],
  "slide_worthy_arguments": [
    {
      "argument": "...",
      "why_it_matters_to_audience": "...",
      "supporting_evidence": "..."
    }
  ],
  "deck_angle": "...",
  "blocking_findings": 0,
  "required_revisions": [],
  "resolution_log": [],
  "resolution_notes": "",
  "findings": []
}
```

Blocking findings include:

- unknown or generic audience
- no clear deck goal
- weak or missing thesis
- unverified or invented data
- key article point omitted
- deck angle does not serve the audience
- outline would merely summarize the article

## Repair Rules

- If the source is too thin, narrow the deck scope instead of padding.
- If the audience is unclear, infer the most likely audience from the user request and source; if inference is risky, ask.
- If the article has too many points, rank them by audience value.
- If data is weak, mark it as weak; do not invent stronger data.
- If the article order is poor for presentation, define a better narrative order in the report.

## Pass Rule

Proceed to Design DNA and PPT generation only when:

- `analysis.json` captures the audience, thesis, and strongest evidence.
- `content_quality_report.json.status == "pass"`.
- `content_quality_report.json.blocking_findings == 0`.
- `content_quality_report.json.required_revisions == []`.
- Every `content_quality_report.json.resolution_log` item has `status: "resolved"`.
- The deck reads like a purposeful presentation, not an article transcript.

If the report has `status: "needs_revision"` or any blocking findings, the Content Quality Auditor must revise `analysis.json`, `deck_state.json`, and the report before handing off. Do not treat unresolved findings as advice for a later agent.

## Revision Loop

1. Auditor identifies blocking issues and writes `status: "needs_revision"`.
2. Auditor lists concrete `required_revisions`; each item must name the affected artifact and expected fix.
3. Execution agent updates the affected artifacts and records each fix in `resolution_log` with `status: "resolved"`, `changed_artifacts`, and evidence.
4. Auditor re-reads the updated artifacts, clears `required_revisions`, sets `status: "pass"`, and keeps resolved log entries.

Do not proceed to Design DNA while `required_revisions` is non-empty or any `resolution_log` item is not `resolved`.
