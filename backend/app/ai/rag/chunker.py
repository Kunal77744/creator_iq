def chunk_text(text: str, chunk_size: int = 400, overlap: int = 50) -> list[str]:
    """Split text into overlapping character chunks preserving word boundaries where possible."""
    cleaned = " ".join((text or "").split())
    if not cleaned:
        return []
    if len(cleaned) <= chunk_size:
        return [cleaned]

    chunks: list[str] = []
    start = 0
    step = max(1, chunk_size - overlap)
    while start < len(cleaned):
        end = start + chunk_size
        chunks.append(cleaned[start:end].strip())
        if end >= len(cleaned):
            break
        start += step
    return chunks
