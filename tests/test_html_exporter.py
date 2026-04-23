from pathlib import Path
import subprocess
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

from tools import html_exporter


def test_collect_static_asset_references_reads_vite_index(tmp_path):
    index = tmp_path / "index.html"
    index.write_text(
        '<script type="module" src="./assets/index.js"></script>'
        '<link rel="stylesheet" href="./assets/index.css">'
        '<link rel="icon" href="/absolute.svg">'
        '<script src="https://example.com/remote.js"></script>',
        encoding="utf-8",
    )

    assert html_exporter.collect_static_asset_references(index) == {
        Path("assets/index.css"),
        Path("assets/index.js"),
    }


def test_build_html_presentation_runs_vite_build_with_static_base(tmp_path, monkeypatch):
    web_dir = tmp_path / "web"
    web_dir.mkdir()
    output_dir = tmp_path / "project" / "presentation-html"
    calls = []

    def fake_run(command, cwd, text, stdout, stderr):
        calls.append((command, cwd, text, stdout, stderr))
        (output_dir / "assets").mkdir(parents=True)
        (output_dir / "index.html").write_text(
            '<!doctype html><script type="module" src="./assets/index.js"></script>',
            encoding="utf-8",
        )
        (output_dir / "assets" / "index.js").write_text("console.log('deck')", encoding="utf-8")
        return subprocess.CompletedProcess(command, 0, stdout="ok")

    monkeypatch.setattr(html_exporter.subprocess, "run", fake_run)

    result = html_exporter.build_html_presentation(web_dir, output_dir)

    assert result == output_dir
    command, cwd, text, stdout, stderr = calls[0]
    assert command[:3] == ["npm", "run", "build"]
    assert "--outDir" in command
    assert str(output_dir.resolve()) in command
    assert "--base" in command
    assert "./" in command
    assert cwd == str(web_dir)
    assert text is True
    assert stdout == subprocess.PIPE
    assert stderr == subprocess.STDOUT


def test_inline_local_static_assets_keeps_dist_files_and_makes_index_standalone(tmp_path):
    output_dir = tmp_path / "presentation-html"
    assets_dir = output_dir / "assets"
    assets_dir.mkdir(parents=True)
    (output_dir / "index.html").write_text(
        '<!doctype html><html><head>'
        '<script type="module" crossorigin src="./assets/index.js"></script>'
        '<link rel="stylesheet" crossorigin href="./assets/index.css">'
        '</head><body></body></html>',
        encoding="utf-8",
    )
    (assets_dir / "index.js").write_text("console.log('deck')", encoding="utf-8")
    (assets_dir / "index.css").write_text("body{margin:0}", encoding="utf-8")

    html_exporter.inline_local_static_assets(output_dir)

    html = (output_dir / "index.html").read_text(encoding="utf-8")
    assert 'src="./assets/index.js"' not in html
    assert 'href="./assets/index.css"' not in html
    assert 'data-inline-origin="./assets/index.js"' in html
    assert 'data-inline-origin="./assets/index.css"' in html
    assert "console.log('deck')" in html
    assert "body{margin:0}" in html
    assert (assets_dir / "index.js").is_file()
    assert (assets_dir / "index.css").is_file()


def test_build_html_presentation_raises_when_build_fails(tmp_path, monkeypatch):
    web_dir = tmp_path / "web"
    web_dir.mkdir()

    def fake_run(command, cwd, text, stdout, stderr):
        return subprocess.CompletedProcess(command, 1, stdout="vite failed")

    monkeypatch.setattr(html_exporter.subprocess, "run", fake_run)

    try:
        html_exporter.build_html_presentation(web_dir, tmp_path / "presentation-html")
    except RuntimeError as exc:
        assert "vite failed" in str(exc)
    else:
        raise AssertionError("expected failed HTML export to raise")


def test_build_html_presentation_raises_when_referenced_asset_is_missing(tmp_path, monkeypatch):
    web_dir = tmp_path / "web"
    web_dir.mkdir()
    output_dir = tmp_path / "presentation-html"

    def fake_run(command, cwd, text, stdout, stderr):
        output_dir.mkdir()
        (output_dir / "index.html").write_text(
            '<!doctype html><script type="module" src="./assets/missing.js"></script>',
            encoding="utf-8",
        )
        return subprocess.CompletedProcess(command, 0, stdout="ok")

    monkeypatch.setattr(html_exporter.subprocess, "run", fake_run)

    try:
        html_exporter.build_html_presentation(web_dir, output_dir)
    except RuntimeError as exc:
        assert "missing files referenced by index.html" in str(exc)
        assert "assets/missing.js" in str(exc)
    else:
        raise AssertionError("expected missing asset to raise")
