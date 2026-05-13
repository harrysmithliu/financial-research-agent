from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol

from storage.models import Document, EvalCase, IngestionJobRecord, StructuredRecord


class StorageRepository(Protocol):
    """Boundary for durable storage implementations."""

    def save_documents(self, documents: tuple[Document, ...]) -> None:
        ...

    def save_structured_records(self, records: tuple[StructuredRecord, ...]) -> None:
        ...

    def save_eval_cases(self, eval_cases: tuple[EvalCase, ...]) -> None:
        ...

    def save_ingestion_job_record(self, job_record: IngestionJobRecord) -> None:
        ...

    def list_documents(self) -> tuple[Document, ...]:
        ...

    def list_structured_records(self) -> tuple[StructuredRecord, ...]:
        ...

    def list_eval_cases(self) -> tuple[EvalCase, ...]:
        ...

    def list_ingestion_job_records(self) -> tuple[IngestionJobRecord, ...]:
        ...


@dataclass
class InMemoryStorageRepository:
    """Test repository that preserves the production storage boundary without a DB."""

    _documents: list[Document] = field(default_factory=list)
    _structured_records: list[StructuredRecord] = field(default_factory=list)
    _eval_cases: list[EvalCase] = field(default_factory=list)
    _ingestion_job_records: list[IngestionJobRecord] = field(default_factory=list)

    def save_documents(self, documents: tuple[Document, ...]) -> None:
        self._documents.extend(documents)

    def save_structured_records(self, records: tuple[StructuredRecord, ...]) -> None:
        self._structured_records.extend(records)

    def save_eval_cases(self, eval_cases: tuple[EvalCase, ...]) -> None:
        self._eval_cases.extend(eval_cases)

    def save_ingestion_job_record(self, job_record: IngestionJobRecord) -> None:
        self._ingestion_job_records.append(job_record)

    def list_documents(self) -> tuple[Document, ...]:
        return tuple(self._documents)

    def list_structured_records(self) -> tuple[StructuredRecord, ...]:
        return tuple(self._structured_records)

    def list_eval_cases(self) -> tuple[EvalCase, ...]:
        return tuple(self._eval_cases)

    def list_ingestion_job_records(self) -> tuple[IngestionJobRecord, ...]:
        return tuple(self._ingestion_job_records)
