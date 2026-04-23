"""Export the active React deck as a Vite static-site directory."""
from __future__ import annotations

from html.parser import HTMLParser
from pathlib import Path
import subprocess
from urllib.parse import urlparse


class StaticAssetTag:
    def __init__(self, tag: str, attrs: list[tuple[str, str | None]], raw_tag: str) -> None:
        self.tag = tag
        self.attrs = attrs
        self.raw_tag = raw_tag

    @property
    def attr_map(self) -> dict[str, str | None]:
        return {name: value for name, value in self.attrs}

    @property
    def reference(self) -> str | None:
        attr_map = self.attr_map
        return attr_map.get("src") or attr_map.get("href")


class StaticAssetParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.references: set[str] = set()
        self.asset_tags: list[StaticAssetTag] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attr_map = {name: value for name, value in attrs}
        for key in ("src", "href"):
            value = attr_map.get(key)
            if value:
                self.references.add(value)
                self.asset_tags.append(StaticAssetTag(tag, attrs, self.get_starttag_text()))


def collect_static_asset_references(index_path: Path) -> set[Path]:
    parser = StaticAssetParser()
    parser.feed(index_path.read_text(encoding="utf-8"))

    references: set[Path] = set()
    for raw_reference in parser.references:
        parsed = urlparse(raw_reference)
        if parsed.scheme or parsed.netloc or parsed.path.startswith(("/", "#")):
            continue
        references.add(Path(parsed.path))
    return references


def _is_local_reference(raw_reference: str) -> bool:
    parsed = urlparse(raw_reference)
    return not parsed.scheme and not parsed.netloc and not parsed.path.startswith(("/", "#"))


def _html_attr_text(attrs: list[tuple[str, str | None]]) -> str:
    parts: list[str] = []
    for name, value in attrs:
        if name in {"src", "href", "crossorigin"}:
            continue
        if value is None:
            parts.append(name)
        else:
            escaped = value.replace("&", "&amp;").replace('"', "&quot;")
            parts.append(f'{name}="{escaped}"')
    return (" " + " ".join(parts)) if parts else ""


def inline_local_static_assets(output_dir: str | Path) -> None:
    """Inline local JS/CSS into index.html so the deck also works from file://."""
    out_path = Path(output_dir)
    index_path = out_path / "index.html"
    html = index_path.read_text(encoding="utf-8")

    parser = StaticAssetParser()
    parser.feed(html)

    for asset_tag in parser.asset_tags:
        raw_reference = asset_tag.reference
        if not raw_reference or not _is_local_reference(raw_reference):
            continue

        asset_path = out_path / Path(urlparse(raw_reference).path)
        if not asset_path.is_file():
            continue

        if asset_tag.tag == "link" and asset_tag.attr_map.get("rel") == "stylesheet":
            css = asset_path.read_text(encoding="utf-8")
            replacement = f'<style data-inline-origin="{raw_reference}">\n{css}\n</style>'
            html = html.replace(asset_tag.raw_tag, replacement, 1)
        elif asset_tag.tag == "script" and asset_tag.attr_map.get("src"):
            js = asset_path.read_text(encoding="utf-8")
            attrs = _html_attr_text(asset_tag.attrs)
            replacement = f"<script{attrs} data-inline-origin=\"{raw_reference}\">\n{js}\n</script>"
            script_block = f"{asset_tag.raw_tag}</script>"
            if script_block in html:
                html = html.replace(script_block, replacement, 1)
            else:
                html = html.replace(asset_tag.raw_tag, replacement, 1)

    index_path.write_text(html, encoding="utf-8")


def validate_static_html_output(output_dir: str | Path) -> None:
    out_path = Path(output_dir)
    index_path = out_path / "index.html"
    if not index_path.is_file() or index_path.stat().st_size == 0:
        raise RuntimeError(f"HTML presentation export did not create a non-empty index.html: {index_path}")

    missing = [
        str(reference)
        for reference in sorted(collect_static_asset_references(index_path))
        if not (out_path / reference).is_file()
    ]
    if missing:
        raise RuntimeError(
            "HTML presentation export is missing files referenced by index.html: "
            + ", ".join(missing)
        )


def build_html_presentation(web_dir: str | Path, output_dir: str | Path) -> Path:
    """Run Vite against the active generated slides and write a static deck."""
    web_path = Path(web_dir)
    out_path = Path(output_dir)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    command = [
        "npm",
        "run",
        "build",
        "--",
        "--outDir",
        str(out_path.resolve()),
        "--emptyOutDir",
        "--base",
        "./",
    ]
    result = subprocess.run(
        command,
        cwd=str(web_path),
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    if result.returncode != 0:
        raise RuntimeError(f"HTML presentation export failed:\n{result.stdout}")

    validate_static_html_output(out_path)
    inline_local_static_assets(out_path)
    return out_path
