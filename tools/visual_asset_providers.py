from __future__ import annotations

import base64
import importlib
import json
import mimetypes
import os
from pathlib import Path
from urllib.parse import urlencode, urlsplit
from urllib.request import Request, urlopen

IMAGE_GENERATION_PROVIDER_ENV = {
    "gemini": "GEMINI_API_KEY",
    "qwen": ("QWEN_IMAGE_API_KEY", "DASHSCOPE_API_KEY"),
    "wanx": ("WANX_API_KEY", "DASHSCOPE_API_KEY"),
}

DEFAULT_REQUEST_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
    ),
    "Accept": "application/json, text/plain, */*",
}


class ProviderUnavailableError(RuntimeError):
    pass


class ProviderRequestError(RuntimeError):
    pass


def _request_json(url, *, headers=None, params=None, method="GET", payload=None):
    headers = {**DEFAULT_REQUEST_HEADERS, **dict(headers or {})}
    if params:
        query = urlencode(params, doseq=True)
        separator = "&" if "?" in url else "?"
        url = f"{url}{separator}{query}"

    body = None
    if payload is not None:
        body = json.dumps(payload).encode("utf-8")
        headers.setdefault("Content-Type", "application/json")

    request = Request(url, data=body, method=method, headers=headers)
    try:
        with urlopen(request) as response:
            return json.loads(response.read().decode("utf-8"))
    except Exception as exc:
        raise ProviderRequestError(f"Request failed for {url}: {exc}") from exc


def _download_binary(url, destination, *, headers=None):
    destination.parent.mkdir(parents=True, exist_ok=True)
    request = Request(url, headers={**DEFAULT_REQUEST_HEADERS, **dict(headers or {})})
    try:
        with urlopen(request) as response:
            destination.write_bytes(response.read())
    except Exception as exc:
        raise ProviderRequestError(f"Download failed for {url}: {exc}") from exc
    return destination


def _choose_provider(provider_env_map: dict[str, str], selector_env: str) -> str:
    selected = os.getenv(selector_env, "").strip().lower()
    if selected:
        if selected not in provider_env_map:
            raise ProviderUnavailableError(f"Unsupported provider '{selected}' for {selector_env}.")
        env_names = provider_env_map[selected]
        if isinstance(env_names, str):
            env_names = (env_names,)
        if env_names and not any(os.getenv(env_name) for env_name in env_names):
            raise ProviderUnavailableError(f"{selected} selected but missing one of: {', '.join(env_names)}.")
        return selected

    public_provider = None
    for provider, env_names in provider_env_map.items():
        if isinstance(env_names, str):
            env_names = (env_names,)
        if not env_names:
            public_provider = public_provider or provider
            continue
        if any(os.getenv(env_name) for env_name in env_names):
            return provider
    if public_provider:
        return public_provider
    expected = []
    for env_names in provider_env_map.values():
        if isinstance(env_names, str):
            expected.append(env_names)
        else:
            expected.extend(env_names)
    if expected:
        raise ProviderUnavailableError(f"No configured provider. Expected one of: {', '.join(sorted(set(expected)))}")
    raise ProviderUnavailableError("No configured provider.")


def _provider_api_key(provider: str) -> str:
    env_names = IMAGE_GENERATION_PROVIDER_ENV[provider]
    if isinstance(env_names, str):
        env_names = (env_names,)
    for env_name in env_names:
        value = os.getenv(env_name)
        if value:
            return value
    raise ProviderUnavailableError(f"Missing API key for {provider}.")


def _extension_from_url_or_type(url: str, mime_type: str | None = None) -> str:
    if mime_type:
        guessed = mimetypes.guess_extension(mime_type)
        if guessed:
            return guessed
    suffix = Path(urlsplit(url).path).suffix.lower()
    return suffix if suffix else ".bin"


def _save_remote_file(remote_url: str, workspace_root: Path, filename: str, *, headers=None) -> Path:
    extension = _extension_from_url_or_type(remote_url)
    destination = workspace_root / f"{filename}{extension}"
    return _download_binary(remote_url, destination, headers=headers)


def _relative_path(root: Path, path: Path) -> str:
    return path.relative_to(root).as_posix()


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
    api_key = _provider_api_key("gemini")
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


def _dashscope_response_to_dict(response) -> dict:
    if isinstance(response, dict):
        return response
    return json.loads(str(response))


def _extract_qwen_image_url(response) -> str:
    resp_dict = _dashscope_response_to_dict(response)
    content = (
        resp_dict.get("output", {})
        .get("choices", [{}])[0]
        .get("message", {})
        .get("content", [])
    )
    for item in content:
        image_url = item.get("image")
        if image_url:
            return image_url
    raise ProviderRequestError("Qwen response did not contain an image URL.")


def _extract_wanx_image_url(response) -> str:
    resp_dict = _dashscope_response_to_dict(response)
    content = (
        resp_dict.get("output", {})
        .get("choices", [{}])[0]
        .get("message", {})
        .get("content", [])
    )
    for item in content:
        image_url = item.get("image")
        if image_url:
            return image_url

    results = resp_dict.get("output", {}).get("results", [])
    if results:
        image_url = results[0].get("url")
        if image_url:
            return image_url
    raise ProviderRequestError("Wanx response did not contain an image URL.")


def _generate_with_qwen(prompt: str, candidate_count: int, workspace_root: Path, asset_prefix: str) -> list[dict]:
    dashscope = importlib.import_module("dashscope")
    api_key = _provider_api_key("qwen")
    dashscope.api_key = api_key
    dashscope.base_http_api_url = os.getenv("QWEN_IMAGE_BASE_URL", "https://dashscope.aliyuncs.com/api/v1")
    multimodal = getattr(dashscope, "MultiModalConversation", None)
    if multimodal is None:
        raise ProviderRequestError("dashscope.MultiModalConversation is unavailable.")

    model = os.getenv("QWEN_IMAGE_MODEL", "qwen-image-2.0-pro")
    size = os.getenv("QWEN_IMAGE_SIZE", "1024*1024")
    negative_prompt = (
        "透明格子背景，伪透明背景，噪点，杂质，杂色，颗粒感，地面阴影，投影，光影伪造，边框，网格线，"
        "白色边框，黑色边框，分割线，画框，低分辨率，低画质，肢体畸形，手指畸形，画面过饱和，蜡像感，"
        "人脸无细节，过度光滑，画面具有 AI 感，构图混乱，文字模糊，扭曲，背景污染，渐变背景，花纹背景，"
        "阴影效果，发光效果"
    )
    candidates = []
    for variant in range(1, candidate_count + 1):
        response = multimodal.call(
            model=model,
            messages=[{"role": "user", "content": [{"text": _candidate_prompt(prompt, variant)}]}],
            stream=False,
            watermark=False,
            prompt_extend=True,
            negative_prompt=negative_prompt,
            size=size,
        )
        if getattr(response, "status_code", 200) != 200:
            raise ProviderRequestError(f"Qwen API failed: {getattr(response, 'message', 'unknown error')}")
        image_url = _extract_qwen_image_url(response)
        saved = _save_remote_file(image_url, workspace_root, f"{asset_prefix}_{variant:02d}")
        candidates.append(
            {
                "candidate_id": f"qwen-{variant}",
                "path": _relative_path(workspace_root, saved),
                "local_path": str(saved),
                "status": "ready",
                "score": round(9.12 - (variant - 1) * 0.08, 2),
                "source_provider": "qwen",
                "license_metadata": {"provider": "qwen", "model": model},
                "resolution_metadata": {"size": size},
            }
        )
    return candidates


def _generate_with_wanx(prompt: str, candidate_count: int, workspace_root: Path, asset_prefix: str) -> list[dict]:
    dashscope = importlib.import_module("dashscope")
    dashscope.api_key = _provider_api_key("wanx")
    if hasattr(dashscope, "base_url"):
        dashscope.base_url = os.getenv("WANX_IMAGE_BASE_URL", getattr(dashscope, "base_url", ""))
    model = os.getenv("WANX_IMAGE_MODEL", "wan2.6-t2i")
    size = os.getenv("WANX_IMAGE_SIZE", "1024*1024")
    candidates = []

    if model.strip().lower().startswith("wan2."):
        image_generation_module = importlib.import_module("dashscope.aigc.image_generation")
        response_module = importlib.import_module("dashscope.api_entities.dashscope_response")
        image_generation = getattr(image_generation_module, "ImageGeneration")
        message_cls = getattr(response_module, "Message")
        for variant in range(1, candidate_count + 1):
            response = image_generation.call(
                model=model,
                api_key=dashscope.api_key,
                messages=[message_cls(role="user", content=[{"text": _candidate_prompt(prompt, variant)}])],
                negative_prompt="",
                prompt_extend=True,
                watermark=False,
                n=1,
                size=size,
            )
            if getattr(response, "status_code", 200) != 200:
                raise ProviderRequestError(f"Wanx API failed: {getattr(response, 'message', 'unknown error')}")
            image_url = _extract_wanx_image_url(response)
            saved = _save_remote_file(image_url, workspace_root, f"{asset_prefix}_{variant:02d}")
            candidates.append(
                {
                    "candidate_id": f"wanx-{variant}",
                    "path": _relative_path(workspace_root, saved),
                    "local_path": str(saved),
                    "status": "ready",
                    "score": round(9.1 - (variant - 1) * 0.08, 2),
                    "source_provider": "wanx",
                    "license_metadata": {"provider": "wanx", "model": model},
                    "resolution_metadata": {"size": size},
                }
            )
        return candidates

    image_synthesis = getattr(dashscope, "ImageSynthesis", None)
    if image_synthesis is None:
        raise ProviderRequestError("dashscope.ImageSynthesis is unavailable.")
    for variant in range(1, candidate_count + 1):
        response = image_synthesis.call(
            model=model,
            prompt=_candidate_prompt(prompt, variant),
            n=1,
            size=size,
        )
        if getattr(response, "status_code", 200) != 200:
            raise ProviderRequestError(f"Wanx API failed: {getattr(response, 'message', 'unknown error')}")
        image_url = _extract_wanx_image_url(response)
        saved = _save_remote_file(image_url, workspace_root, f"{asset_prefix}_{variant:02d}")
        candidates.append(
            {
                "candidate_id": f"wanx-{variant}",
                "path": _relative_path(workspace_root, saved),
                "local_path": str(saved),
                "status": "ready",
                "score": round(9.1 - (variant - 1) * 0.08, 2),
                "source_provider": "wanx",
                "license_metadata": {"provider": "wanx", "model": model},
                "resolution_metadata": {"size": size},
            }
        )
    return candidates


def generate_image_candidates(*, prompt: str, candidate_count: int, workspace_root: Path, asset_prefix: str) -> list[dict]:
    provider = _choose_provider(IMAGE_GENERATION_PROVIDER_ENV, "VISUAL_ASSET_IMAGE_PROVIDER")
    if provider == "gemini":
        return _generate_with_gemini(prompt, candidate_count, workspace_root, asset_prefix)
    if provider == "qwen":
        return _generate_with_qwen(prompt, candidate_count, workspace_root, asset_prefix)
    if provider == "wanx":
        return _generate_with_wanx(prompt, candidate_count, workspace_root, asset_prefix)
    raise ProviderUnavailableError(
        f"Configured image-generation provider '{provider}' does not have an implemented adapter yet."
    )
