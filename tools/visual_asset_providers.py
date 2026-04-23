from __future__ import annotations

import base64
import json
import mimetypes
import os
from pathlib import Path
from urllib.parse import urlencode, urlparse
from urllib.request import Request, urlopen


SEARCH_PROVIDER_ENV = {
    "unsplash": "UNSPLASH_ACCESS_KEY",
    "pexels": "PEXELS_API_KEY",
    "pixabay": "PIXABAY_API_KEY",
}

IMAGE_GENERATION_PROVIDER_ENV = {
    "gemini": "GEMINI_API_KEY",
    "qwen": "QWEN_IMAGE_API_KEY",
    "wanx": "WANX_API_KEY",
}


class ProviderUnavailableError(RuntimeError):
    pass


class ProviderRequestError(RuntimeError):
    pass


def _request_json(url, *, headers=None, params=None, method="GET", payload=None):
    headers = dict(headers or {})
    if params:
        query = urlencode(params, doseq=True)
        separator = "&" if "?" in url else "?"
        url = f"{url}{separator}{query}"

    body = None
    if payload is not None:
        body = json.dumps(payload).encode("utf-8")
        headers.setdefault("Content-Type", "application/json")

    request = Request(url, data=body, method=method, headers=headers)
    with urlopen(request) as response:
        return json.loads(response.read().decode("utf-8"))


def _download_binary(url, destination, *, headers=None):
    destination.parent.mkdir(parents=True, exist_ok=True)
    request = Request(url, headers=headers or {})
    with urlopen(request) as response:
        destination.write_bytes(response.read())
    return destination


def _choose_provider(provider_env_map: dict[str, str], selector_env: str) -> str:
    selected = os.getenv(selector_env, "").strip().lower()
    if selected:
        if selected not in provider_env_map:
            raise ProviderUnavailableError(f"Unsupported provider '{selected}' for {selector_env}.")
        env_name = provider_env_map[selected]
        if not os.getenv(env_name):
            raise ProviderUnavailableError(f"{selected} selected but missing {env_name}.")
        return selected

    for provider, env_name in provider_env_map.items():
        if os.getenv(env_name):
            return provider
    raise ProviderUnavailableError(f"No configured provider. Expected one of: {', '.join(provider_env_map.values())}")


def _extension_from_url_or_type(url: str, mime_type: str | None = None) -> str:
    if mime_type:
        guessed = mimetypes.guess_extension(mime_type)
        if guessed:
            return guessed
    path = urlparse(url).path
    suffix = Path(path).suffix.lower()
    return suffix if suffix else ".bin"


def _candidate_score(index: int, width: int = 0, height: int = 0) -> float:
    megapixels = (width * height) / 1_000_000 if width and height else 0
    return round(9.2 - index * 0.12 + min(megapixels * 0.02, 0.35), 2)


def _save_remote_file(remote_url: str, workspace_root: Path, filename: str, *, headers=None) -> Path:
    extension = _extension_from_url_or_type(remote_url)
    destination = workspace_root / f"{filename}{extension}"
    return _download_binary(remote_url, destination, headers=headers)


def _relative_path(root: Path, path: Path) -> str:
    return path.relative_to(root).as_posix()


def _normalize_unsplash_result(item: dict, index: int, workspace_root: Path, asset_prefix: str, api_key: str) -> dict:
    headers = {
        "Authorization": f"Client-ID {api_key}",
        "Accept-Version": "v1",
    }
    tracked = {}
    download_location = item.get("links", {}).get("download_location")
    if download_location:
        tracked = _request_json(download_location, headers=headers)
    download_url = tracked.get("url") or item.get("urls", {}).get("regular")
    if not download_url:
        raise ProviderRequestError("Unsplash result missing downloadable URL.")
    saved = _save_remote_file(download_url, workspace_root, f"{asset_prefix}_{index:02d}")
    user = item.get("user", {})
    return {
        "candidate_id": item.get("id", f"unsplash-{index}"),
        "path": _relative_path(workspace_root, saved),
        "local_path": str(saved),
        "status": "ready",
        "score": _candidate_score(index, item.get("width", 0), item.get("height", 0)),
        "source_provider": "unsplash",
        "remote_url": download_url,
        "license_metadata": {
            "provider": "unsplash",
            "author": user.get("name", ""),
            "author_url": user.get("links", {}).get("html", ""),
            "asset_url": item.get("links", {}).get("html", ""),
        },
        "resolution_metadata": {
            "width": item.get("width"),
            "height": item.get("height"),
            "color": item.get("color"),
        },
    }


def _normalize_pexels_result(item: dict, index: int, workspace_root: Path, asset_prefix: str) -> dict:
    download_url = item.get("src", {}).get("large2x") or item.get("src", {}).get("original")
    if not download_url:
        raise ProviderRequestError("Pexels result missing downloadable URL.")
    saved = _save_remote_file(download_url, workspace_root, f"{asset_prefix}_{index:02d}")
    return {
        "candidate_id": str(item.get("id", f"pexels-{index}")),
        "path": _relative_path(workspace_root, saved),
        "local_path": str(saved),
        "status": "ready",
        "score": _candidate_score(index, item.get("width", 0), item.get("height", 0)),
        "source_provider": "pexels",
        "remote_url": download_url,
        "license_metadata": {
            "provider": "pexels",
            "author": item.get("photographer", ""),
            "author_url": item.get("photographer_url", ""),
            "asset_url": item.get("url", ""),
        },
        "resolution_metadata": {
            "width": item.get("width"),
            "height": item.get("height"),
            "color": item.get("avg_color"),
        },
    }


def _normalize_pixabay_result(item: dict, index: int, workspace_root: Path, asset_prefix: str) -> dict:
    download_url = item.get("largeImageURL") or item.get("webformatURL")
    if not download_url:
        raise ProviderRequestError("Pixabay result missing downloadable URL.")
    saved = _save_remote_file(download_url, workspace_root, f"{asset_prefix}_{index:02d}")
    return {
        "candidate_id": str(item.get("id", f"pixabay-{index}")),
        "path": _relative_path(workspace_root, saved),
        "local_path": str(saved),
        "status": "ready",
        "score": _candidate_score(index, item.get("imageWidth", 0), item.get("imageHeight", 0)),
        "source_provider": "pixabay",
        "remote_url": download_url,
        "license_metadata": {
            "provider": "pixabay",
            "author": item.get("user", ""),
            "asset_url": item.get("pageURL", ""),
            "tags": item.get("tags", ""),
        },
        "resolution_metadata": {
            "width": item.get("imageWidth"),
            "height": item.get("imageHeight"),
        },
    }


def _search_unsplash(query: str, candidate_count: int, workspace_root: Path, asset_prefix: str) -> list[dict]:
    api_key = os.getenv("UNSPLASH_ACCESS_KEY")
    if not api_key:
        raise ProviderUnavailableError("Missing UNSPLASH_ACCESS_KEY.")
    payload = _request_json(
        "https://api.unsplash.com/search/photos",
        headers={
            "Authorization": f"Client-ID {api_key}",
            "Accept-Version": "v1",
        },
        params={
            "query": query,
            "page": 1,
            "per_page": candidate_count,
            "orientation": "landscape",
        },
    )
    return [
        _normalize_unsplash_result(item, index + 1, workspace_root, asset_prefix, api_key)
        for index, item in enumerate(payload.get("results", [])[:candidate_count])
    ]


def _search_pexels(query: str, candidate_count: int, workspace_root: Path, asset_prefix: str) -> list[dict]:
    api_key = os.getenv("PEXELS_API_KEY")
    if not api_key:
        raise ProviderUnavailableError("Missing PEXELS_API_KEY.")
    payload = _request_json(
        "https://api.pexels.com/v1/search",
        headers={"Authorization": api_key},
        params={
            "query": query,
            "per_page": candidate_count,
            "page": 1,
            "orientation": "landscape",
        },
    )
    return [
        _normalize_pexels_result(item, index + 1, workspace_root, asset_prefix)
        for index, item in enumerate(payload.get("photos", [])[:candidate_count])
    ]


def _search_pixabay(query: str, candidate_count: int, workspace_root: Path, asset_prefix: str) -> list[dict]:
    api_key = os.getenv("PIXABAY_API_KEY")
    if not api_key:
        raise ProviderUnavailableError("Missing PIXABAY_API_KEY.")
    payload = _request_json(
        "https://pixabay.com/api/",
        params={
            "key": api_key,
            "q": query,
            "image_type": "photo",
            "safesearch": "true",
            "per_page": candidate_count,
            "page": 1,
        },
    )
    return [
        _normalize_pixabay_result(item, index + 1, workspace_root, asset_prefix)
        for index, item in enumerate(payload.get("hits", [])[:candidate_count])
    ]


def search_image_candidates(*, query: str, candidate_count: int, workspace_root: Path, asset_prefix: str) -> list[dict]:
    provider = _choose_provider(SEARCH_PROVIDER_ENV, "VISUAL_ASSET_SEARCH_PROVIDER")
    if provider == "unsplash":
        return _search_unsplash(query, candidate_count, workspace_root, asset_prefix)
    if provider == "pexels":
        return _search_pexels(query, candidate_count, workspace_root, asset_prefix)
    if provider == "pixabay":
        return _search_pixabay(query, candidate_count, workspace_root, asset_prefix)
    raise ProviderUnavailableError(f"Unsupported image-search provider '{provider}'.")


def _candidate_prompt(prompt: str, variant: int) -> str:
    if variant == 1:
        return prompt
    return f"{prompt}\nVariation {variant}: keep the slide intent, but explore a distinct composition and focal balance."


def _extract_gemini_inline_data(response: dict) -> tuple[str, bytes]:
    for candidate in response.get("candidates", []):
        content = candidate.get("content", {})
        for part in content.get("parts", []):
            inline_data = part.get("inlineData")
            if inline_data and inline_data.get("data"):
                mime_type = inline_data.get("mimeType", "image/png")
                return mime_type, base64.b64decode(inline_data["data"])
    raise ProviderRequestError("Gemini response did not contain generated image data.")


def _generate_with_gemini(prompt: str, candidate_count: int, workspace_root: Path, asset_prefix: str) -> list[dict]:
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ProviderUnavailableError("Missing GEMINI_API_KEY.")
    model = os.getenv("GEMINI_IMAGE_MODEL", "gemini-2.5-flash-image")
    candidates = []
    for variant in range(1, candidate_count + 1):
        response = _request_json(
            f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent",
            params={"key": api_key},
            method="POST",
            payload={
                "contents": [{"parts": [{"text": _candidate_prompt(prompt, variant)}]}],
            },
        )
        mime_type, image_bytes = _extract_gemini_inline_data(response)
        extension = _extension_from_url_or_type("", mime_type)
        destination = workspace_root / f"{asset_prefix}_{variant:02d}{extension}"
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(image_bytes)
        candidates.append(
            {
                "candidate_id": f"gemini-{variant}",
                "path": _relative_path(workspace_root, destination),
                "local_path": str(destination),
                "status": "ready",
                "score": round(9.15 - (variant - 1) * 0.08, 2),
                "source_provider": "gemini",
                "license_metadata": {
                    "provider": "gemini",
                    "model": model,
                    "watermark": "SynthID",
                },
                "resolution_metadata": {"mime_type": mime_type},
            }
        )
    return candidates


def generate_image_candidates(*, prompt: str, candidate_count: int, workspace_root: Path, asset_prefix: str) -> list[dict]:
    provider = _choose_provider(IMAGE_GENERATION_PROVIDER_ENV, "VISUAL_ASSET_IMAGE_PROVIDER")
    if provider == "gemini":
        return _generate_with_gemini(prompt, candidate_count, workspace_root, asset_prefix)
    raise ProviderUnavailableError(
        f"Configured image-generation provider '{provider}' does not have an implemented adapter yet."
    )
