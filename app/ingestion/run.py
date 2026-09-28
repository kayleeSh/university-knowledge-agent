import argparse
import json
from pathlib import Path
from typing import Any

from app.ingestion.loaders import load_source
from app.ingestion.splitter import (
    DEFAULT_CHUNK_OVERLAP,
    DEFAULT_CHUNK_SIZE,
    recursive_character_split,
)

PROJECT_ROOT = Path(__file__).resolve().parents[2]


def ingest_manifest(
    manifest_path: Path,
    output_path: Path,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    chunk_overlap: int = DEFAULT_CHUNK_OVERLAP,
) -> list[dict[str, Any]]:
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    sources = manifest.get("sources")
    if not isinstance(sources, list):
        raise ValueError("Manifest must contain a 'sources' list.")

    records: list[dict[str, Any]] = []
    for source_config in sources:
        document = load_source(source_config, manifest_path.parent)
        for chunk_index, text in enumerate(
            recursive_character_split(document.text, chunk_size, chunk_overlap)
        ):
            records.append(
                {
                    "id": f"{document.source_id}:{chunk_index}",
                    "source_id": document.source_id,
                    "source": document.source,
                    "title": document.title,
                    "chunk_index": chunk_index,
                    "text": text,
                }
            )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(records, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return records


def main() -> None:
    parser = argparse.ArgumentParser(description="Ingest public university pages into JSON chunks.")
    parser.add_argument(
        "--manifest",
        type=Path,
        default=PROJECT_ROOT / "data" / "sources.json",
        help="JSON source manifest (default: data/sources.json)",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=PROJECT_ROOT / "data" / "processed" / "chunks.json",
        help="JSON output path (default: data/processed/chunks.json)",
    )
    parser.add_argument("--chunk-size", type=int, default=DEFAULT_CHUNK_SIZE)
    parser.add_argument("--chunk-overlap", type=int, default=DEFAULT_CHUNK_OVERLAP)
    args = parser.parse_args()

    records = ingest_manifest(args.manifest, args.output, args.chunk_size, args.chunk_overlap)
    print(f"Wrote {len(records)} chunks from {args.manifest} to {args.output}")


if __name__ == "__main__":
    main()