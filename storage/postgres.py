from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol

from storage.models import Document, EvalCase, IngestionJobRecord, StructuredRecord


class PostgresConnection(Protocol):
    def execute(self, query: str, params: tuple[Any, ...]) -> Any:
        ...


@dataclass(frozen=True)
class PostgresStorageRepository:
    connection: PostgresConnection

    def save_documents(self, documents: tuple[Document, ...]) -> None:
        for document in documents:
            payload = document.to_mapping()
            self.connection.execute(
                """
                INSERT INTO documents (
                    document_id,
                    source_type,
                    source_uri,
                    title,
                    body,
                    metadata,
                    created_at,
                    updated_at,
                    payload
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (document_id) DO UPDATE SET
                    source_type = EXCLUDED.source_type,
                    source_uri = EXCLUDED.source_uri,
                    title = EXCLUDED.title,
                    body = EXCLUDED.body,
                    metadata = EXCLUDED.metadata,
                    updated_at = EXCLUDED.updated_at,
                    payload = EXCLUDED.payload
                """,
                (
                    document.document_id,
                    document.source_type,
                    document.source_uri,
                    document.title,
                    document.body,
                    document.metadata,
                    document.created_at,
                    document.updated_at,
                    payload,
                ),
            )

    def save_structured_records(self, records: tuple[StructuredRecord, ...]) -> None:
        for index, record in enumerate(records):
            payload = record.to_mapping()
            record_key = _structured_record_key(record, index)
            self.connection.execute(
                """
                INSERT INTO structured_records (
                    record_key,
                    record_type,
                    source_uri,
                    metadata,
                    payload
                )
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (record_key) DO UPDATE SET
                    record_type = EXCLUDED.record_type,
                    source_uri = EXCLUDED.source_uri,
                    metadata = EXCLUDED.metadata,
                    payload = EXCLUDED.payload
                """,
                (
                    record_key,
                    record.record_type,
                    record.source_uri,
                    record.metadata,
                    payload,
                ),
            )

    def save_eval_cases(self, eval_cases: tuple[EvalCase, ...]) -> None:
        for eval_case in eval_cases:
            payload = eval_case.to_mapping()
            self.connection.execute(
                """
                INSERT INTO evaluation_cases (
                    case_id,
                    task_type,
                    question,
                    metadata,
                    payload
                )
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (case_id) DO UPDATE SET
                    task_type = EXCLUDED.task_type,
                    question = EXCLUDED.question,
                    metadata = EXCLUDED.metadata,
                    payload = EXCLUDED.payload
                """,
                (
                    eval_case.case_id,
                    eval_case.task_type,
                    eval_case.question,
                    eval_case.metadata,
                    payload,
                ),
            )

    def save_ingestion_job_record(self, job_record: IngestionJobRecord) -> None:
        payload = job_record.to_mapping()
        self.connection.execute(
            """
            INSERT INTO ingestion_job_records (
                job_id,
                dataset_name,
                source_ids,
                status,
                document_count,
                structured_record_count,
                eval_case_count,
                started_at,
                finished_at,
                error_message,
                payload
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (job_id) DO UPDATE SET
                dataset_name = EXCLUDED.dataset_name,
                source_ids = EXCLUDED.source_ids,
                status = EXCLUDED.status,
                document_count = EXCLUDED.document_count,
                structured_record_count = EXCLUDED.structured_record_count,
                eval_case_count = EXCLUDED.eval_case_count,
                finished_at = EXCLUDED.finished_at,
                error_message = EXCLUDED.error_message,
                payload = EXCLUDED.payload
            """,
            (
                job_record.job_id,
                job_record.dataset_name,
                list(job_record.source_ids),
                job_record.status,
                job_record.document_count,
                job_record.structured_record_count,
                job_record.eval_case_count,
                job_record.started_at,
                job_record.finished_at,
                job_record.error_message,
                payload,
            ),
        )


def _structured_record_key(record: StructuredRecord, fallback_index: int) -> str:
    for field_name in ("fund_id", "issue_id", "case_id"):
        value = record.values.get(field_name)
        if isinstance(value, str) and value.strip():
            return f"{record.record_type}:{value}"
    return f"{record.record_type}:{record.source_uri or 'unknown'}:{fallback_index}"

