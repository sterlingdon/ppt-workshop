from __future__ import annotations

import json
import mimetypes
import re
from pathlib import Path
from urllib.parse import urlparse
from urllib.request import Request, urlopen

try:
    from .presentation_workspace import PresentationWorkspace
except ImportError:
    from presentation_workspace import PresentationWorkspace


FONT_REGISTRY: dict[str, dict] = {
    "Space Grotesk": {
        "google_family": "Space+Grotesk:wght@400;500;700",
        "fallback_chain": ["Arial", "sans-serif"],
    },
    "DM Sans": {
        "google_family": "DM+Sans:wght@400;500;700",
        "fallback_chain": ["Arial", "sans-serif"],
    },
    "Manrope": {
        "google_family": "Manrope:wght@400;500;700;800",
        "fallback_chain": ["Arial", "sans-serif"],
    },
    "Plus Jakarta Sans": {
        "google_family": "Plus+Jakarta+Sans:wght@400;500;700;800",
        "fallback_chain": ["Arial", "sans-serif"],
    },
    "IBM Plex Sans": {
        "google_family": "IBM+Plex+Sans:wght@400;500;700",
        "fallback_chain": ["Arial", "sans-serif"],
    },
    "Newsreader": {
        "google_family": "Newsreader:opsz,wght@6..72,400;6..72,600;6..72,700",
        "fallback_chain": ["Georgia", "serif"],
    },
    "Noto Sans SC": {
        "google_family": "Noto+Sans+SC:wght@400;500;700",
        "fallback_chain": ["Microsoft YaHei", "PingFang SC", "sans-serif"],
    },
    "Noto Serif SC": {
        "google_family": "Noto+Serif+SC:wght@400;600;700",
        "fallback_chain": ["Songti SC", "STSong", "serif"],
    },
}

FONT_PRESET_REGISTRY: dict[str, dict] = {
    "editorial_publishing": {
        "roles": {
            "display": {"family": "Newsreader", "source": "download", "fallback_chain": ["Georgia", "serif"]},
            "body": {"family": "Noto Sans SC", "source": "download", "fallback_chain": ["PingFang SC", "sans-serif"]},
            "number": {"family": "Space Grotesk", "source": "download", "fallback_chain": ["Arial", "sans-serif"]},
        }
    },
    "business_strategy": {
        "roles": {
            "display": {"family": "IBM Plex Sans", "source": "download", "fallback_chain": ["Arial", "sans-serif"]},
            "body": {"family": "Noto Sans SC", "source": "download", "fallback_chain": ["PingFang SC", "sans-serif"]},
            "number": {"family": "IBM Plex Sans", "source": "download", "fallback_chain": ["Arial", "sans-serif"]},
        }
    },
    "education_family": {
        "roles": {
            "display": {"family": "Noto Serif SC", "source": "download", "fallback_chain": ["Songti SC", "serif"]},
            "body": {"family": "Noto Sans SC", "source": "download", "fallback_chain": ["PingFang SC", "sans-serif"]},
            "number": {"family": "Space Grotesk", "source": "download", "fallback_chain": ["Arial", "sans-serif"]},
        }
    },
    "tech_future": {
        "roles": {
            "display": {"family": "Plus Jakarta Sans", "source": "download", "fallback_chain": ["Arial", "sans-serif"]},
            "body": {"family": "Noto Sans SC", "source": "download", "fallback_chain": ["PingFang SC", "sans-serif"]},
            "number": {"family": "Space Grotesk", "source": "download", "fallback_chain": ["Arial", "sans-serif"]},
        }
    },
}

GOOGLE_FONTS_CSS_URL = "https://fonts.googleapis.com/css2"
GOOGLE_FONTS_USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
)


def _read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


def _request_text(url: str, *, headers: dict[str, str] | None = None, params: dict | None = None) -> str:
    request = Request(url, headers=headers or {})
    with urlopen(request) as response:
        return response.read().decode("utf-8")


def _download_binary(url: str, destination: Path, *, headers: dict[str, str] | None = None) -> Path:
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.is_file() and destination.stat().st_size > 0:
        return destination
    request = Request(url, headers=headers or {})
    with urlopen(request) as response:
        destination.write_bytes(response.read())
    return destination


def _slug(value: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", value.strip().lower()).strip("-")
    return slug or "font"


def _canonical_family(value: str) -> str:
    return re.sub(r"\s+", " ", value.strip())


def _lookup_registry(family: str) -> dict:
    canonical = _canonical_family(family)
    for name, config in FONT_REGISTRY.items():
        if name.lower() == canonical.lower():
            return {"family": name, **config}
    return {"family": canonical}


def _merge_font_role(base: dict, override: dict) -> dict:
    merged = dict(base)
    for key, value in override.items():
        if value not in (None, "", []):
            merged[key] = value
    return merged


def _infer_font_preset(design_dna: dict) -> str | None:
    explicit = str(design_dna.get("font_preset") or "").strip()
    if explicit:
        return explicit
    keyword_blob = " ".join(
        [
            str(design_dna.get("visual_direction") or ""),
            str(design_dna.get("recommendation_summary") or ""),
        ]
    ).lower()
    if any(term in keyword_blob for term in ("editorial", "magazine", "publishing", "poster")):
        return "editorial_publishing"
    if any(term in keyword_blob for term in ("strategy", "business", "board", "investor")):
        return "business_strategy"
    if any(term in keyword_blob for term in ("education", "family", "parent", "school")):
        return "education_family"
    if any(term in keyword_blob for term in ("tech", "future", "ai", "product")):
        return "tech_future"
    return None


def _extension_from_url(url: str) -> str:
    path = urlparse(url).path
    suffix = Path(path).suffix.lower()
    if suffix:
        return suffix
    guessed = mimetypes.guess_extension("font/ttf")
    return guessed or ".bin"


def _first_font_asset(css_text: str) -> tuple[str, str]:
    match = re.search(r"url\((https://[^)]+)\)\s+format\(['\"]([^'\"]+)['\"]\)", css_text)
    if match:
        return match.group(1), match.group(2)
    match = re.search(r"url\((https://[^)]+)\)", css_text)
    if match:
        return match.group(1), "truetype"
    raise ValueError("Google Fonts CSS did not contain a downloadable URL.")


def resolve_font_strategy(design_dna: dict) -> tuple[str | None, dict]:
    preset_name = _infer_font_preset(design_dna)
    preset_roles = dict(FONT_PRESET_REGISTRY.get(preset_name, {}).get("roles") or {})
    strategy = dict(design_dna.get("font_strategy") or {})
    resolved: dict[str, dict] = {}
    for role in ("display", "body", "number"):
        resolved[role] = _merge_font_role(preset_roles.get(role, {}), dict(strategy.get(role) or {}))
    return preset_name, resolved


def _font_roles(design_dna: dict) -> tuple[str | None, list[tuple[str, dict]]]:
    preset_name, strategy = resolve_font_strategy(design_dna)
    roles: list[tuple[str, dict]] = []
    for role in ("display", "body", "number"):
        config = dict(strategy.get(role) or {})
        if not config.get("family"):
            if role == "display" and design_dna.get("font_display"):
                config["family"] = design_dna["font_display"]
            elif role == "body" and design_dna.get("font_body"):
                config["family"] = design_dna["font_body"]
            elif role == "number" and design_dna.get("font_display"):
                config["family"] = design_dna["font_display"]
        if config.get("family"):
            roles.append((role, config))
    return preset_name, roles


def _download_google_font(entry: dict, destination_dir: Path, role: str) -> tuple[Path, str, str]:
    family_query = entry.get("google_family")
    if not family_query:
        raise ValueError(f"No google_family configured for {entry['family']}.")
    url = f"{GOOGLE_FONTS_CSS_URL}?family={family_query}&display=swap"
    css_text = _request_text(
        url,
        headers={"User-Agent": GOOGLE_FONTS_USER_AGENT},
    )
    remote_url, font_format = _first_font_asset(css_text)
    extension = _extension_from_url(remote_url)
    destination = destination_dir / f"{_slug(role)}-{_slug(entry['family'])}{extension}"
    saved = _download_binary(remote_url, destination, headers={"User-Agent": GOOGLE_FONTS_USER_AGENT})
    return saved, remote_url, font_format


def _copy_bundled_font(source_path: str, destination: Path) -> Path:
    source = Path(source_path)
    if not source.is_file():
        raise FileNotFoundError(f"Bundled font not found: {source}")
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_bytes(source.read_bytes())
    return destination


def build_font_asset_manifest(workspace: PresentationWorkspace) -> dict:
    if not workspace.metadata_path.exists():
        raise FileNotFoundError(f"missing project metadata: {workspace.metadata_path}")

    if not (workspace.project_dir / "design_dna.json").exists():
        payload = {"project_id": workspace.project_id, "fonts": []}
        workspace.font_css_path.write_text("/* no project font assets */\n", encoding="utf-8")
        _write_json(workspace.font_manifest_path, payload)
        return payload

    design_dna = _read_json(workspace.project_dir / "design_dna.json")
    preset_name, font_roles = _font_roles(design_dna)
    fonts = []
    css_blocks: list[str] = []
    written_faces: set[tuple[str, str]] = set()

    for role, config in font_roles:
        family = _canonical_family(str(config.get("family", "")))
        entry = _lookup_registry(family)
        source = str(config.get("source") or ("download" if entry.get("google_family") else "local"))
        fallback_chain = list(config.get("fallback_chain") or entry.get("fallback_chain") or [])
        status = "local_only"
        local_path = None
        remote_url = None
        font_format = None
        error = None

        try:
            if source == "download":
                if config.get("download_url"):
                    remote_url = str(config["download_url"])
                    extension = _extension_from_url(remote_url)
                    destination = workspace.fonts_dir / f"{_slug(role)}-{_slug(family)}{extension}"
                    saved = _download_binary(remote_url, destination)
                    font_format = extension.lstrip(".") or "truetype"
                else:
                    saved, remote_url, font_format = _download_google_font(entry, workspace.fonts_dir, role)
                local_path = saved
                status = "ready"
            elif source == "bundled":
                asset_path = str(config.get("asset_path", ""))
                if not asset_path:
                    raise ValueError(f"Bundled font for {family} requires asset_path.")
                extension = Path(asset_path).suffix or ".ttf"
                destination = workspace.fonts_dir / f"{_slug(role)}-{_slug(family)}{extension}"
                saved = _copy_bundled_font(asset_path, destination)
                local_path = saved
                status = "ready"
                font_format = extension.lstrip(".") or "truetype"
            elif source == "local":
                status = "local_only"
            else:
                raise ValueError(f"Unsupported font source '{source}' for {family}.")
        except Exception as exc:  # pragma: no cover - error path exercised via tests
            status = "blocked"
            error = str(exc)

        if local_path:
            rel_path = local_path.relative_to(workspace.project_dir).as_posix()
            face_key = (family, rel_path)
            if face_key not in written_faces:
                css_blocks.append(
                    "\n".join(
                        [
                            "@font-face {",
                            f"  font-family: '{family}';",
                            f"  src: url('./fonts/{local_path.name}') format('{font_format or 'truetype'}');",
                            "  font-style: normal;",
                            "  font-weight: 100 900;",
                            "  font-display: swap;",
                            "}",
                        ]
                    )
                )
                written_faces.add(face_key)
        else:
            rel_path = None

        css_family = ", ".join([f"'{family}'", *[f"'{item}'" if " " in item else item for item in fallback_chain]]) if fallback_chain else f"'{family}'"
        fonts.append(
            {
                "role": role,
                "family": family,
                "source": source,
                "status": status,
                "fallback_chain": fallback_chain,
                "css_family": css_family,
                "local_path": rel_path,
                "remote_url": remote_url,
                "font_format": font_format,
                "coverage_notes": config.get("coverage_notes", ""),
                "ppt_fidelity_mode": config.get("ppt_fidelity_mode", "native"),
                "error": error,
            }
        )

    css_content = "/* generated project font faces */\n"
    if css_blocks:
        css_content += "\n\n".join(css_blocks) + "\n"
    workspace.font_css_path.write_text(css_content, encoding="utf-8")
    payload = {"project_id": workspace.project_id, "preset": preset_name, "fonts": fonts}
    _write_json(workspace.font_manifest_path, payload)
    return payload
