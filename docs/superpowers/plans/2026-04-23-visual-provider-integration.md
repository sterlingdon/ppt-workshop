# Visual Provider Integration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add real remote image-search and image-generation provider support to the visual asset system so `asset-manifest` can fetch, cache, and select usable remote assets.

**Architecture:** Keep `tools/visual_assets.py` as the orchestration layer and move remote-provider logic into a new focused module. Implement real HTTP-backed adapters for Unsplash, Pexels, Pixabay, and Gemini image generation. Preserve the existing local SVG/chart pipeline, and degrade cleanly to blocked manifest entries when credentials are missing or provider calls fail.

**Tech Stack:** Python 3 standard library (`urllib`, `base64`, `json`), pytest, existing project CLI in `tools/ppt_workflow.py`, JSON artifact workflow, Markdown reference docs

---

## File Structure

### Existing files to modify

- `tools/visual_assets.py`  
  Keep route selection and manifest orchestration here, but replace remote placeholders with provider-backed candidate generation and local caching.

- `tests/test_visual_assets.py`  
  Extend orchestration tests to cover configured remote search and configured remote image generation.

- `references/workflow.md`  
  Document that `asset-manifest` can now fetch remote assets and which environment variables enable the providers.

### New files to create

- `tools/visual_asset_providers.py`  
  HTTP helpers, provider registry, normalized search candidate extraction, Gemini image generation, and local asset download helpers.

- `tests/test_visual_asset_providers.py`  
  Unit tests for provider normalization and Gemini response parsing with HTTP mocked at the helper boundary.

## Task 1: Add Provider Adapters And Normalized Remote Asset Records

**Files:**
- Create: `tools/visual_asset_providers.py`
- Test: `tests/test_visual_asset_providers.py`

- [ ] **Step 1: Write failing provider tests**

```python
def test_unsplash_search_normalizes_results(monkeypatch, tmp_path):
    monkeypatch.setenv("UNSPLASH_ACCESS_KEY", "test-key")
    responses = [
        {
            "results": [
                {
                    "id": "photo-1",
                    "alt_description": "Teacher with students",
                    "urls": {"regular": "https://images.example/teacher.jpg"},
                    "width": 1600,
                    "height": 900,
                    "color": "#ccddee",
                    "links": {
                        "html": "https://unsplash.com/photos/photo-1",
                        "download_location": "https://api.unsplash.com/photos/photo-1/download",
                    },
                    "user": {
                        "name": "Jane Doe",
                        "links": {"html": "https://unsplash.com/@jane"},
                    },
                }
            ]
        },
        {"url": "https://images.example/teacher.jpg?tracked=1"},
    ]
    calls = []

    def fake_request_json(url, *, headers=None, params=None, method="GET", payload=None):
        calls.append((url, headers, params, method, payload))
        return responses.pop(0)

    def fake_download_binary(url, destination, *, headers=None):
        destination.write_bytes(b"img")
        return destination

    monkeypatch.setattr(providers, "_request_json", fake_request_json)
    monkeypatch.setattr(providers, "_download_binary", fake_download_binary)

    items = providers.search_image_candidates(
        route="image_search",
        query="teacher student classroom",
        candidate_count=1,
        workspace_root=tmp_path,
        asset_prefix="slide_01_primary",
    )

    assert items[0]["path"].endswith(".jpg")
    assert items[0]["source_provider"] == "unsplash"
    assert items[0]["license_metadata"]["author"] == "Jane Doe"
    assert any("download" in call[0] for call in calls)


def test_gemini_generation_writes_png_candidate(monkeypatch, tmp_path):
    monkeypatch.setenv("GEMINI_API_KEY", "gem-key")
    monkeypatch.setenv("GEMINI_IMAGE_MODEL", "gemini-2.5-flash-image-preview")
    image_bytes = base64.b64encode(b"png-bytes").decode("ascii")

    def fake_request_json(url, *, headers=None, params=None, method="GET", payload=None):
        return {
            "candidates": [
                {
                    "content": {
                        "parts": [
                            {"inlineData": {"mimeType": "image/png", "data": image_bytes}}
                        ]
                    }
                }
            ]
        }

    monkeypatch.setattr(providers, "_request_json", fake_request_json)

    items = providers.generate_image_candidates(
        prompt="Create a premium classroom hero image",
        candidate_count=1,
        workspace_root=tmp_path,
        asset_prefix="slide_02_primary",
    )

    assert items[0]["path"].endswith(".png")
    assert (tmp_path / items[0]["path"]).is_file()
    assert items[0]["source_provider"] == "gemini"
```

- [ ] **Step 2: Run the provider tests to verify they fail**

Run: `pytest tests/test_visual_asset_providers.py -v`

Expected: FAIL with `ModuleNotFoundError` for `tools.visual_asset_providers`.

- [ ] **Step 3: Implement provider adapters**

```python
def search_image_candidates(route: str, query: str, candidate_count: int, workspace_root: Path, asset_prefix: str) -> list[dict]:
    provider = _choose_search_provider()
    if provider == "unsplash":
        return _search_unsplash(query, candidate_count, workspace_root, asset_prefix)
    if provider == "pexels":
        return _search_pexels(query, candidate_count, workspace_root, asset_prefix)
    if provider == "pixabay":
        return _search_pixabay(query, candidate_count, workspace_root, asset_prefix)
    raise ProviderUnavailableError("No configured search provider")


def generate_image_candidates(prompt: str, candidate_count: int, workspace_root: Path, asset_prefix: str) -> list[dict]:
    provider = _choose_generation_provider()
    if provider == "gemini":
        return _generate_with_gemini(prompt, candidate_count, workspace_root, asset_prefix)
    raise ProviderUnavailableError("No configured image-generation provider")
```

- [ ] **Step 4: Run the provider tests**

Run: `pytest tests/test_visual_asset_providers.py -v`

Expected: PASS for both provider tests.

- [ ] **Step 5: Commit**

```bash
git add tools/visual_asset_providers.py tests/test_visual_asset_providers.py
git commit -m "feat(ppt): add remote visual asset providers"
```

## Task 2: Wire Remote Providers Into Manifest Generation

**Files:**
- Modify: `tools/visual_assets.py`
- Modify: `tests/test_visual_assets.py`

- [ ] **Step 1: Write failing orchestration tests**

```python
def test_build_visual_asset_manifest_fetches_configured_image_search_candidates(tmp_path, monkeypatch):
    workspace = create_project_workspace("Search Deck", root_dir=tmp_path, project_id="search-deck")
    write_blueprint(
        workspace,
        [
            {
                "slide": 1,
                "title": "Real Classroom",
                "critical_visual": False,
                "asset_intent": {
                    "visual_role": "supporting_evidence",
                    "asset_goal": "Show a real classroom context.",
                    "candidate_asset_types": ["image_search"],
                    "must_show": ["teacher", "student"],
                    "must_avoid": ["diagram"],
                    "wow_goal": "photo credibility",
                },
            }
        ],
    )
    build_visual_asset_plan(workspace)

    def fake_search(*, query, candidate_count, workspace_root, asset_prefix):
        path = workspace_root / f"{asset_prefix}.jpg"
        path.write_bytes(b"img")
        return [
            {
                "candidate_id": "search-1",
                "path": path.relative_to(workspace.project_dir).as_posix(),
                "status": "ready",
                "score": 8.9,
                "source_provider": "unsplash",
                "license_metadata": {"provider": "unsplash"},
                "resolution_metadata": {"width": 1600, "height": 900},
            }
        ]

    monkeypatch.setattr("tools.visual_assets.search_image_candidates", fake_search)

    manifest = build_visual_asset_manifest(workspace)

    asset = manifest["assets"][0]
    assert asset["review_status"] == "approved"
    assert asset["selected_asset"]["source_provider"] == "unsplash"


def test_build_visual_asset_manifest_fetches_configured_generated_images(tmp_path, monkeypatch):
    workspace = create_project_workspace("Hero Deck", root_dir=tmp_path, project_id="hero-deck")
    write_blueprint(
        workspace,
        [
            {
                "slide": 1,
                "title": "AI Teaching Future",
                "critical_visual": True,
                "asset_intent": {
                    "visual_role": "hero_anchor",
                    "asset_goal": "Create a premium hero visual for future teaching.",
                    "candidate_asset_types": ["image_generation"],
                    "must_show": ["teacher", "AI", "classroom"],
                    "must_avoid": ["stock-photo look"],
                    "wow_goal": "hero atmosphere",
                },
            }
        ],
    )
    build_visual_asset_plan(workspace)

    def fake_generate(*, prompt, candidate_count, workspace_root, asset_prefix):
        path = workspace_root / f"{asset_prefix}.png"
        path.write_bytes(b"png")
        return [
            {
                "candidate_id": "gen-1",
                "path": path.relative_to(workspace.project_dir).as_posix(),
                "status": "ready",
                "score": 9.1,
                "source_provider": "gemini",
                "license_metadata": {"provider": "gemini"},
                "resolution_metadata": {"width": 1024, "height": 1024},
            }
        ]

    monkeypatch.setattr("tools.visual_assets.generate_image_candidates", fake_generate)

    manifest = build_visual_asset_manifest(workspace)

    asset = manifest["assets"][0]
    assert asset["review_status"] == "approved"
    assert asset["selected_asset"]["source_provider"] == "gemini"
```

- [ ] **Step 2: Run the orchestration tests to verify they fail**

Run: `pytest tests/test_visual_assets.py -k "configured_image_search_candidates or configured_generated_images" -v`

Expected: FAIL because `tools.visual_assets` still returns blocked placeholders for remote routes.

- [ ] **Step 3: Replace remote placeholders with provider-backed generation**

```python
elif route == "image_search":
    candidate_assets = search_image_candidates(
        query=_asset_query(slide_meta, asset_intent),
        candidate_count=slot["candidate_count"],
        workspace_root=workspace.assets_dir,
        asset_prefix=f"slide_{slide_entry['slide']:02d}_{slot['slot']}_search",
    )
    selected_asset = _select_best_candidate(candidate_assets)
elif route == "image_generation":
    candidate_assets = generate_image_candidates(
        prompt=_asset_query(slide_meta, asset_intent),
        candidate_count=slot["candidate_count"],
        workspace_root=workspace.assets_dir,
        asset_prefix=f"slide_{slide_entry['slide']:02d}_{slot['slot']}_generated",
    )
    selected_asset = _select_best_candidate(candidate_assets)
```

- [ ] **Step 4: Run the visual asset tests**

Run: `pytest tests/test_visual_assets.py -v`

Expected: PASS for local SVG tests, blocked-provider tests, and the new configured-provider tests.

- [ ] **Step 5: Commit**

```bash
git add tools/visual_assets.py tests/test_visual_assets.py
git commit -m "feat(ppt): wire remote providers into asset manifests"
```

## Task 3: Document Provider Configuration And Verify Full Suite

**Files:**
- Modify: `references/workflow.md`

- [ ] **Step 1: Update workflow docs**

```md
- `asset-manifest`: writes `visual_asset_manifest.json`, emits local SVG/chart assets, and can fetch remote search or generated images when provider credentials are configured.

### Provider Environment Variables

- Search providers: `UNSPLASH_ACCESS_KEY`, `PEXELS_API_KEY`, `PIXABAY_API_KEY`
- Image generation providers: `GEMINI_API_KEY` with optional `GEMINI_IMAGE_MODEL`
```

- [ ] **Step 2: Run targeted provider tests**

Run: `pytest tests/test_visual_asset_providers.py tests/test_visual_assets.py -v`

Expected: PASS

- [ ] **Step 3: Run the full test suite**

Run: `pytest -q`

Expected: PASS with the existing warning count only.

- [ ] **Step 4: Commit**

```bash
git add references/workflow.md
git commit -m "docs(ppt): document visual asset provider configuration"
```
