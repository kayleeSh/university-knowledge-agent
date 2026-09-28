from dataclasses import dataclass
from io import BytesIO
from pathlib import Path
from typing import Any, Mapping

import httpx
from bs4 import BeautifulSoup
from pypdf import PdfReader


@dataclass(frozen=True)
class SourceDocument:
    source_id: str
    source: str
    title: str
    text: str


def clean_html(html: str, fallback_title: str) -> tuple[str, str]:
    soup = BeautifulSoup(html, "html.parser")
    title = soup.title.get_text(" ", strip=True) if soup.title else fallback_title

    for element in soup.select("script, style, noscript, svg, nav, header, footer"):
        element.decompose()

    content = soup.find("main") or soup.find("article") or soup.body or soup
    text = content.get_text("\n", strip=True)
    return title, text


def _read_pdf(content: bytes) -> str:
    reader = PdfReader(BytesIO(content))
    return "\n\n".join(page.extract_text() or "" for page in reader.pages).strip()


def _load_path(path: Path, source_id: str) -> SourceDocument:
    suffix = path.suffix.lower()
    if suffix == ".pdf":
        text = _read_pdf(path.read_bytes())
        return SourceDocument(source_id, str(path), path.stem, text)

    if suffix in {".html", ".htm"}:
        title, text = clean_html(path.read_text(encoding="utf-8"), path.stem)
        return SourceDocument(source_id, str(path), title, text)

    raise ValueError(f"Unsupported local source type: {path}")


def load_source(source: Mapping[str, Any], base_dir: Path) -> SourceDocument:
    source_id = str(source.get("id", "")).strip()
    if not source_id:
        raise ValueError("Each source must have a non-empty 'id'.")

    url = source.get("url")
    local_path = source.get("path")
    if bool(url) == bool(local_path):
        raise ValueError(f"Source '{source_id}' must have exactly one of 'url' or 'path'.")

    if local_path:
        path = (base_dir / str(local_path)).resolve()
        if not path.is_file():
            raise FileNotFoundError(f"Source file for '{source_id}' not found: {path}")
        return _load_path(path, source_id)

    response = httpx.get(
        str(url),
        follow_redirects=True,
        timeout=30,
        headers={"User-Agent": "UniversityKnowledgeAgent/0.1 (public information ingestion)"},
    )
    response.raise_for_status()
    content_type = response.headers.get("content-type", "").lower()
    if "application/pdf" in content_type or str(response.url).lower().endswith(".pdf"):
        text = _read_pdf(response.content)
        title = str(source.get("title") or source_id)
    else:
        title, text = clean_html(response.text, str(source.get("title") or source_id))

    return SourceDocument(source_id, str(response.url), title, text)