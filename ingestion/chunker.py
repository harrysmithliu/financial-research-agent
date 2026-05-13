from __future__ import annotations

from storage.models import Document, DocumentChunk

DEFAULT_MAX_CHARS = 1200
DEFAULT_OVERLAP_CHARS = 120


def chunk_documents(
    documents: tuple[Document, ...],
    *,
    max_chars: int = DEFAULT_MAX_CHARS,
    overlap_chars: int = DEFAULT_OVERLAP_CHARS,
) -> tuple[DocumentChunk, ...]:
    if max_chars <= 0:
        raise ValueError("max_chars must be positive")
    if overlap_chars < 0 or overlap_chars >= max_chars:
        raise ValueError(
            "overlap_chars must be non-negative and smaller than max_chars"
        )

    chunks: list[DocumentChunk] = []
    for document in documents:
        chunks.extend(
            _chunk_document(
                document,
                max_chars=max_chars,
                overlap_chars=overlap_chars,
            )
        )
    return tuple(chunks)


def _chunk_document(
    document: Document,
    *,
    max_chars: int,
    overlap_chars: int,
) -> tuple[DocumentChunk, ...]:
    segments = _split_text(
        document.body,
        max_chars=max_chars,
        overlap_chars=overlap_chars,
    )
    chunk_count = len(segments)

    return tuple(
        DocumentChunk(
            chunk_id=f"chunk_{document.document_id}_{index:03d}",
            document_id=document.document_id,
            chunk_index=index,
            text=segment,
            metadata={
                **document.metadata,
                "document_id": document.document_id,
                "document_title": document.title,
                "source_type": document.source_type,
                "chunk_count": chunk_count,
            },
            source_uri=document.source_uri,
        )
        for index, segment in enumerate(segments)
    )


def _split_text(text: str, *, max_chars: int, overlap_chars: int) -> tuple[str, ...]:
    cleaned_text = text.strip()
    if len(cleaned_text) <= max_chars:
        return (cleaned_text,)

    segments: list[str] = []
    start = 0
    while start < len(cleaned_text):
        end = min(start + max_chars, len(cleaned_text))
        if end < len(cleaned_text):
            boundary = cleaned_text.rfind(" ", start, end)
            if boundary > start:
                end = boundary
        segment = cleaned_text[start:end].strip()
        if segment:
            segments.append(segment)
        if end == len(cleaned_text):
            break
        next_start = _overlap_start(cleaned_text, start, end, overlap_chars)
        start = next_start if next_start > start else end

    return tuple(segments)


def _overlap_start(
    text: str,
    current_start: int,
    current_end: int,
    overlap_chars: int,
) -> int:
    if overlap_chars == 0:
        return current_end

    candidate = max(current_end - overlap_chars, 0)
    while candidate > current_start and text[candidate - 1] != " ":
        candidate -= 1
    return candidate
