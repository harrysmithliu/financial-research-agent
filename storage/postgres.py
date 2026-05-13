from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol

from storage.models import Document, EvalCase, IngestionJobRecord, StructuredRecord

DEFAULT_MIGRATIONS_DIR = Path(__file__).resolve().parent / "migrations"


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
                    _jsonb_param(document.metadata),
                    document.created_at,
                    document.updated_at,
                    _jsonb_param(payload),
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
                    _jsonb_param(record.metadata),
                    _jsonb_param(payload),
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
                    _jsonb_param(eval_case.metadata),
                    _jsonb_param(payload),
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
                _jsonb_param(list(job_record.source_ids)),
                job_record.status,
                job_record.document_count,
                job_record.structured_record_count,
                job_record.eval_case_count,
                job_record.started_at,
                job_record.finished_at,
                job_record.error_message,
                _jsonb_param(payload),
            ),
        )


def connect_postgres_repository(database_url: str) -> PostgresStorageRepository:
    try:
        import psycopg
    except ModuleNotFoundError as exc:
        raise RuntimeError(
            "psycopg is required to create a PostgreSQL storage repository"
        ) from exc

    return PostgresStorageRepository(psycopg.connect(database_url))


def migration_paths(migrations_dir: Path = DEFAULT_MIGRATIONS_DIR) -> tuple[Path, ...]:
    return tuple(sorted(migrations_dir.glob("*.sql")))


def run_ingestion_storage_migrations(
    connection: PostgresConnection,
    migrations_dir: Path = DEFAULT_MIGRATIONS_DIR,
) -> None:
    for migration_path in migration_paths(migrations_dir):
        connection.execute(migration_path.read_text(encoding="utf-8"), ())


def _structured_record_key(record: StructuredRecord, fallback_index: int) -> str:
    for field_name in ("fund_id", "issue_id", "case_id"):
        value = record.values.get(field_name)
        if isinstance(value, str) and value.strip():
            return f"{record.record_type}:{value}"
    return f"{record.record_type}:{record.source_uri or 'unknown'}:{fallback_index}"


def _jsonb_param(value: Any) -> Any:
    try:
        from psycopg.types.json import Jsonb
    except ModuleNotFoundError:
        return value

    return Jsonb(value)
