from dataclasses import dataclass
from io import BytesIO
from pathlib import Path
from typing import Any, Mapping

import httpx
from bs4 import BeautifulSoup
from pypdf import PdfReader

USER_AGENT = "UniversityKnowledgeAgent/0.1 (public information ingestion)"
DEFAULT_NUSMODS_ACAD_YEAR = "2026-2027"
NUSMODS_API_URL = "https://api.nusmods.com/v2/{acad_year}/modules/{module_code}.json"
NUSMODS_PAGE_URL = "https://nusmods.com/courses/{module_code}"
NUSMODS_SEMESTERS = {1: "Semester 1", 2: "Semester 2", 3: "Special Term I", 4: "Special Term II"}
NUSMODS_WORKLOAD_PARTS = ("lecture", "tutorial", "laboratory", "project", "preparation")


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


def format_nusmods_module(module: Mapping[str, Any]) -> tuple[str, str]:
    """Render a NUSMods module JSON record as a readable plain-text document."""
    code = module["moduleCode"]
    title = f"{code} {module['title']}"
    lines = [
        title,
        "University: National University of Singapore (NUS)",
        f"Academic year: {module.get('acadYear', '')}",
        f"Faculty: {module.get('faculty', '')}",
        f"Department: {module.get('department', '')}",
        f"Units: {module.get('moduleCredit', '')}",
    ]

    semesters = [
        NUSMODS_SEMESTERS.get(entry.get("semester"), f"Semester {entry.get('semester')}")
        for entry in module.get("semesterData", [])
    ]
    lines.append(f"Offered in: {', '.join(semesters) if semesters else 'Not offered this year'}")

    workload = module.get("workload")
    if isinstance(workload, list) and len(workload) == len(NUSMODS_WORKLOAD_PARTS):
        hours = ", ".join(f"{part} {h}h" for part, h in zip(NUSMODS_WORKLOAD_PARTS, workload))
        lines.append(f"Weekly workload: {hours} (total {sum(workload)}h)")

    if module.get("gradingBasisDescription"):
        lines.append(f"Grading basis: {module['gradingBasisDescription']}")

    for key, label in (
        ("prerequisite", "Prerequisite"),
        ("corequisite", "Corequisite"),
        ("preclusion", "Preclusion"),
    ):
        value = module.get(key)
        if value:
            lines.append(f"{label}: {' '.join(str(value).replace('THEN(', ' THEN (').split())}")

    lines.append("")
    lines.append(f"Description: {module.get('description', '').strip()}")
    return title, "\n".join(lines)


def _load_nusmods_module(module_code: str, acad_year: str, source_id: str) -> SourceDocument:
    response = httpx.get(
        NUSMODS_API_URL.format(acad_year=acad_year, module_code=module_code),
        timeout=30,
        headers={"User-Agent": USER_AGENT},
    )
    response.raise_for_status()
    title, text = format_nusmods_module(response.json())
    return SourceDocument(source_id, NUSMODS_PAGE_URL.format(module_code=module_code), title, text)


def load_source(source: Mapping[str, Any], base_dir: Path) -> SourceDocument:
    source_id = str(source.get("id", "")).strip()
    if not source_id:
        raise ValueError("Each source must have a non-empty 'id'.")

    url = source.get("url")
    local_path = source.get("path")
    nusmods_module = source.get("nusmods_module")
    if sum(bool(value) for value in (url, local_path, nusmods_module)) != 1:
        raise ValueError(
            f"Source '{source_id}' must have exactly one of 'url', 'path' or 'nusmods_module'."
        )

    if nusmods_module:
        acad_year = str(source.get("acad_year") or DEFAULT_NUSMODS_ACAD_YEAR)
        return _load_nusmods_module(str(nusmods_module), acad_year, source_id)

    if local_path:
        path = (base_dir / str(local_path)).resolve()
        if not path.is_file():
            raise FileNotFoundError(f"Source file for '{source_id}' not found: {path}")
        return _load_path(path, source_id)

    response = httpx.get(
        str(url),
        follow_redirects=True,
        timeout=30,
        headers={"User-Agent": USER_AGENT},
    )
    response.raise_for_status()
    content_type = response.headers.get("content-type", "").lower()
    if "application/pdf" in content_type or str(response.url).lower().endswith(".pdf"):
        text = _read_pdf(response.content)
        title = str(source.get("title") or source_id)
    else:
        title, text = clean_html(response.text, str(source.get("title") or source_id))

    return SourceDocument(source_id, str(response.url), title, text)