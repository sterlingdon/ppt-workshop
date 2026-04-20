import pytest
from unittest.mock import patch, MagicMock
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))
from tools.ingest import extract_from_url, extract_from_text, extract_from_pdf, IngestResult

def test_extract_from_text_basic():
    text = "# AI的未来\n\n这是一篇关于人工智能的文章。" * 10
    result = extract_from_text(text)
    assert isinstance(result, IngestResult)
    assert len(result.text) > 0
    assert result.source_type == "text"

def test_extract_from_text_cleans_whitespace():
    text = "标题\n\n\n\n\n正文   内容"
    result = extract_from_text(text)
    assert "\n\n\n" not in result.text

def test_extract_from_url_uses_trafilatura():
    with patch("tools.ingest.trafilatura.fetch_url") as mock_fetch:
        with patch("tools.ingest.trafilatura.extract") as mock_extract:
            mock_fetch.return_value = b"<html><body><article>Test content</article></body></html>"
            mock_extract.return_value = "Test content"
            result = extract_from_url("https://example.com/article")
            assert result.text == "Test content"
            assert result.source_type == "url"
            assert result.source_url == "https://example.com/article"

def test_extract_from_url_raises_on_empty():
    with patch("tools.ingest.trafilatura.fetch_url") as mock_fetch:
        with patch("tools.ingest.trafilatura.extract") as mock_extract:
            mock_fetch.return_value = b""
            mock_extract.return_value = None
            with pytest.raises(ValueError, match="无法提取"):
                extract_from_url("https://example.com/empty")

def test_extract_from_pdf_requires_file(tmp_path):
    fake_pdf = tmp_path / "fake.pdf"
    fake_pdf.write_bytes(b"not a real pdf")
    with pytest.raises(Exception):
        extract_from_pdf(str(fake_pdf))
