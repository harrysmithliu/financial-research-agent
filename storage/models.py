from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


class ModelValidationError(ValueError):
    """Raised when a canonical model is missing required data."""


def _require_non_empty_string(field_name: str, value: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise ModelValidationError(f"{field_name} must be a non-empty string")


def _require_mapping(field_name: str, value: dict[str, Any]) -> None:
    if not isinstance(value, dict):
        raise ModelValidationError(f"{field_name} must be a mapping")


def _require_list(field_name: str, value: list[Any]) -> None:
    if not isinstance(value, list):
        raise ModelValidationError(f"{field_name} must be a list")


@dataclass(frozen=True)
class Document:
    document_id: str
    source_type: str
    source_uri: str
    title: str
    body: str
    metadata: dict[str, Any]
    created_at: datetime
    updated_at: datetime

    def __post_init__(self) -> None:
        _require_non_empty_string("document_id", self.document_id)
        _require_non_empty_string("source_type", self.source_type)
        _require_non_empty_string("source_uri", self.source_uri)
        _require_non_empty_string("title", self.title)
        _require_non_empty_string("body", self.body)
        _require_mapping("metadata", self.metadata)
        if not isinstance(self.created_at, datetime):
            raise ModelValidationError("created_at must be a datetime")
        if not isinstance(self.updated_at, datetime):
            raise ModelValidationError("updated_at must be a datetime")

    def to_mapping(self) -> dict[str, Any]:
        return {
            "document_id": self.document_id,
            "source_type": self.source_type,
            "source_uri": self.source_uri,
            "title": self.title,
            "body": self.body,
            "metadata": dict(self.metadata),
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }


@dataclass(frozen=True)
class DocumentChunk:
    chunk_id: str
    document_id: str
    chunk_index: int
    text: str
    metadata: dict[str, Any]
    source_uri: str
    embedding: list[float] | None = None

    def __post_init__(self) -> None:
        _require_non_empty_string("chunk_id", self.chunk_id)
        _require_non_empty_string("document_id", self.document_id)
        if not isinstance(self.chunk_index, int) or self.chunk_index < 0:
            raise ModelValidationError("chunk_index must be a non-negative integer")
        _require_non_empty_string("text", self.text)
        _require_mapping("metadata", self.metadata)
        _require_non_empty_string("source_uri", self.source_uri)
        if self.embedding is not None:
            _require_list("embedding", self.embedding)
            if not all(isinstance(value, int | float) for value in self.embedding):
                raise ModelValidationError("embedding must contain only numbers")

    def to_mapping(self) -> dict[str, Any]:
        return {
            "chunk_id": self.chunk_id,
            "document_id": self.document_id,
            "chunk_index": self.chunk_index,
            "text": self.text,
            "embedding": list(self.embedding) if self.embedding is not None else None,
            "metadata": dict(self.metadata),
            "source_uri": self.source_uri,
        }


@dataclass(frozen=True)
class StructuredRecord:
    record_type: str
    source_uri: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    values: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        _require_non_empty_string("record_type", self.record_type)
        if self.source_uri is not None:
            _require_non_empty_string("source_uri", self.source_uri)
        _require_mapping("metadata", self.metadata)
        _require_mapping("values", self.values)

    def to_mapping(self) -> dict[str, Any]:
        record = {
            "record_type": self.record_type,
            **self.values,
        }
        if self.source_uri is not None:
            record["source_uri"] = self.source_uri
        if self.metadata:
            record["metadata"] = dict(self.metadata)
        return record


@dataclass(frozen=True)
class EvalCase:
    case_id: str
    task_type: str
    question: str
    entities: list[dict[str, Any]]
    expected_citations: list[dict[str, Any]]
    evaluation_tags: list[str]
    safety_expectations: dict[str, Any]
    expected_answer: str | None = None

    def __post_init__(self) -> None:
        _require_non_empty_string("case_id", self.case_id)
        _require_non_empty_string("task_type", self.task_type)
        _require_non_empty_string("question", self.question)
        _require_list("entities", self.entities)
        _require_list("expected_citations", self.expected_citations)
        _require_list("evaluation_tags", self.evaluation_tags)
        if not all(isinstance(tag, str) and tag.strip() for tag in self.evaluation_tags):
            raise ModelValidationError("evaluation_tags must contain non-empty strings")
        _require_mapping("safety_expectations", self.safety_expectations)
        if self.expected_answer is not None:
            _require_non_empty_string("expected_answer", self.expected_answer)

    def to_mapping(self) -> dict[str, Any]:
        return {
            "case_id": self.case_id,
            "task_type": self.task_type,
            "question": self.question,
            "entities": list(self.entities),
            "expected_answer": self.expected_answer,
            "expected_citations": list(self.expected_citations),
            "evaluation_tags": list(self.evaluation_tags),
            "safety_expectations": dict(self.safety_expectations),
        }

