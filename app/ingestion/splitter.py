DEFAULT_CHUNK_SIZE = 2_000
DEFAULT_CHUNK_OVERLAP = 200
SEPARATORS = ("\n\n", "\n", ". ", " ")


def recursive_character_split(
    text: str,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    chunk_overlap: int = DEFAULT_CHUNK_OVERLAP,
) -> list[str]:
    if chunk_size <= 0:
        raise ValueError("chunk_size must be greater than zero.")
    if chunk_overlap < 0 or chunk_overlap >= chunk_size:
        raise ValueError("chunk_overlap must be non-negative and smaller than chunk_size.")

    text = text.strip()
    if not text:
        return []

    chunks: list[str] = []
    start = 0
    while start < len(text):
        limit = min(start + chunk_size, len(text))
        end = limit

        if limit < len(text):
            for separator in SEPARATORS:
                boundary = text.rfind(separator, start, limit - len(separator) + 1)
                if boundary > start:
                    end = boundary + len(separator)
                    break

        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        if end == len(text):
            break

        next_start = max(start + 1, end - chunk_overlap)
        while next_start < end and text[next_start].isspace():
            next_start += 1
        start = next_start

    return chunks