from pathlib import Path

from app.ingestion.loaders import clean_html, load_source
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