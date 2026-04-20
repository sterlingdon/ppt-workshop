"""Agent 1 辅助工具：从 URL / 文本 / PDF 提取文章内容"""
from __future__ import annotations
import re
from dataclasses import dataclass
from pathlib import Path

import trafilatura


@dataclass
class IngestResult:
    text: str
    source_type: str          # "url" | "text" | "pdf"
    source_url: str = ""
    title: str = ""
    word_count: int = 0


def extract_from_url(url: str) -> IngestResult:
    """通过 trafilatura 提取 URL 文章正文"""
    downloaded = trafilatura.fetch_url(url)
    text = trafilatura.extract(
        downloaded,
        include_comments=False,
        include_tables=True,
        no_fallback=False,
    ) if downloaded else None

    if not text:
        raise ValueError(f"无法提取文章内容：{url}")

    text = _clean_text(text)
    return IngestResult(
        text=text,
        source_type="url",
        source_url=url,
        word_count=len(text.split()),
    )


def extract_from_text(raw: str) -> IngestResult:
    """直接使用用户提供的文本"""
    text = _clean_text(raw)
    return IngestResult(
        text=text,
        source_type="text",
        word_count=len(text.split()),
    )


def extract_from_pdf(path: str) -> IngestResult:
    """通过 pymupdf4llm 提取 PDF 内容（保留标题结构）"""
    try:
        import pymupdf4llm
    except ImportError:
        raise ImportError("请安装 pymupdf4llm: pip install pymupdf4llm")

    md_text = pymupdf4llm.to_markdown(path)
    if not md_text or len(md_text.strip()) < 50:
        raise ValueError(f"PDF 内容提取失败或内容过少：{path}")

    text = _clean_text(md_text)
    return IngestResult(
        text=text,
        source_type="pdf",
        source_url=str(Path(path).resolve()),
        word_count=len(text.split()),
    )


def _clean_text(text: str) -> str:
    """清理多余空白行和乱码"""
    text = re.sub(r'\n{3,}', '\n\n', text)
    text = re.sub(r' {3,}', '  ', text)
    return text.strip()


if __name__ == "__main__":
    import sys, json
    mode = sys.argv[1]  # url | text | pdf
    source = sys.argv[2]

    if mode == "url":
        result = extract_from_url(source)
    elif mode == "pdf":
        result = extract_from_pdf(source)
    else:
        result = extract_from_text(Path(source).read_text(encoding="utf-8"))

    print(json.dumps({
        "text": result.text,
        "source_type": result.source_type,
        "source_url": result.source_url,
        "word_count": result.word_count,
    }, ensure_ascii=False, indent=2))
