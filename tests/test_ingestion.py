from pathlib import Path

import pytest

from app.ingestion.loaders import clean_html, format_nusmods_module, load_source
from app.ingestion.splitter import recursive_character_split


def test_clean_html_removes_non_content_elements() -> None:
    title, text = clean_html(
        "<html><head><title>Course page</title></head><body>"
        "<nav>Navigation</nav><main><h1>Programme</h1><p>Course details.</p>"
        "<script>ignore this</script></main></body></html>",
        "fallback",
    )

    assert title == "Course page"
    assert "Programme" in text
    assert "Course details." in text
    assert "Navigation" not in text
    assert "ignore this" not in text


def test_recursive_character_split_respects_size_and_overlap() -> None:
    text = "Alpha section. " * 100

    chunks = recursive_character_split(text, chunk_size=120, chunk_overlap=20)

    assert len(chunks) > 1
    assert all(len(chunk) <= 120 for chunk in chunks)
    assert all(first[-10:] in second for first, second in zip(chunks, chunks[1:]))


def test_load_local_html_source(tmp_path: Path) -> None:
    source_path = tmp_path / "sample.html"
    source_path.write_text(
        "<html><title>Sample</title><main><p>Admissions information.</p></main></html>",
        encoding="utf-8",
    )

    document = load_source({"id": "sample", "path": "sample.html"}, tmp_path)

    assert document.source_id == "sample"
    assert document.title == "Sample"
    assert document.text == "Admissions information."

def test_format_nusmods_module() -> None:
    title, text = format_nusmods_module(
        {
            "acadYear": "2026/2027",
            "moduleCode": "CS2040",
            "title": "Data Structures and Algorithms",
            "faculty": "Computing",
            "department": "Computer Science",
            "moduleCredit": "4",
            "workload": [3, 0, 1, 3, 3],
            "prerequisite": "must have completed 1 of CS1010/CS1101S",
            "description": "Fundamental data structures and algorithms.",
            "semesterData": [{"semester": 1}, {"semester": 2}],
        }
    )

    assert title == "CS2040 Data Structures and Algorithms"
    assert "Units: 4" in text
    assert "Offered in: Semester 1, Semester 2" in text
    assert "(total 10h)" in text
    assert "Prerequisite: must have completed 1 of CS1010/CS1101S" in text
    assert "Preclusion" not in text
    assert text.endswith("Description: Fundamental data structures and algorithms.")


def test_load_source_rejects_multiple_locations() -> None:
    with pytest.raises(ValueError, match="exactly one"):
        load_source({"id": "bad", "url": "https://example.com", "nusmods_module": "CS2040"}, Path("."))


def test_recursive_character_split_always_advances_past_previous_chunk() -> None:
    # A paragraph break just after the overlap window used to make every
    # following chunk end at the same position, advancing one character at a time.
    text = "a" * 150 + "\n\n" + "b" * 300

    chunks = recursive_character_split(text, chunk_size=200, chunk_overlap=100)

    assert len(chunks) <= 4
    assert chunks[-1].endswith("b")
