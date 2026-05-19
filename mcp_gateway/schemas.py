from __future__ import annotations

from dataclasses import dataclass
from typing import Any


def _require_non_empty_string(field_name: str, value: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field_name} must be a non-empty string")


def _require_mapping(field_name: str, value: dict[str, Any]) -> None:
    if not isinstance(value, dict):
        raise ValueError(f"{field_name} must be a mapping")


@dataclass(frozen=True)
class CitationChunk:
    chunk_id: str
    document_id: str
    source_uri: str
    chunk_index: int
    text: str
    metadata: dict[str, Any]
    distance: float

    def __post_init__(self) -> None:
        _require_non_empty_string("chunk_id", self.chunk_id)
        _require_non_empty_string("document_id", self.document_id)
        _require_non_empty_string("source_uri", self.source_uri)
        _require_non_empty_string("text", self.text)
        _require_mapping("metadata", self.metadata)
        if not isinstance(self.chunk_index, int) or self.chunk_index < 0:
            raise ValueError("chunk_index must be a non-negative integer")
        if not isinstance(self.distance, int | float):
            raise ValueError("distance must be numeric")

    def to_mapping(self) -> dict[str, Any]:
        return {
            "chunk_id": self.chunk_id,
            "document_id": self.document_id,
            "source_uri": self.source_uri,
            "chunk_index": self.chunk_index,
            "text": self.text,
            "metadata": dict(self.metadata),
            "distance": float(self.distance),
        }


@dataclass(frozen=True)
class DocumentRetrievalRequest:
    query: str
    top_k: int = 5

    def __post_init__(self) -> None:
        _require_non_empty_string("query", self.query)
        if not isinstance(self.top_k, int) or self.top_k <= 0:
            raise ValueError("top_k must be a positive integer")
        if self.top_k > 50:
            raise ValueError("top_k must be less than or equal to 50")

    def to_mapping(self) -> dict[str, Any]:
        return {
            "query": self.query,
            "top_k": self.top_k,
        }


@dataclass(frozen=True)
class DocumentRetrievalResponse:
    request_id: str
    tool_name: str
    query: str
    top_k: int
    chunks: tuple[CitationChunk, ...]
    cache_hit: bool = False

    def __post_init__(self) -> None:
        _require_non_empty_string("request_id", self.request_id)
        _require_non_empty_string("tool_name", self.tool_name)
        _require_non_empty_string("query", self.query)
        if not isinstance(self.top_k, int) or self.top_k <= 0:
            raise ValueError("top_k must be a positive integer")
        if not isinstance(self.chunks, tuple):
            raise ValueError("chunks must be a tuple")

    @property
    def citations(self) -> tuple[dict[str, Any], ...]:
        return tuple(chunk.to_mapping() for chunk in self.chunks)

    @property
    def retrieved_documents(self) -> tuple[str, ...]:
        seen_document_ids: set[str] = set()
        ordered_document_ids: list[str] = []
        for chunk in self.chunks:
            if chunk.document_id in seen_document_ids:
                continue
            seen_document_ids.add(chunk.document_id)
            ordered_document_ids.append(chunk.document_id)
        return tuple(ordered_document_ids)

    def to_mapping(self) -> dict[str, Any]:
        return {
            "request_id": self.request_id,
            "tool_name": self.tool_name,
            "query": self.query,
            "top_k": self.top_k,
            "cache_hit": self.cache_hit,
            "retrieved_documents": list(self.retrieved_documents),
            "citations": list(self.citations),
        }
