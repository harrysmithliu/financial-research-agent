from __future__ import annotations

import sys
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from ingestion.jobs import load_seed_dataset
from storage.models import DocumentChunk, IngestionJobRecord
from storage.postgres import (
    PostgresStorageRepository,
    connect_postgres_repository,
    migration_paths,
    run_ingestion_storage_migrations,
)


REPO_ROOT = Path(__file__).resolve().parents[1]
NOW = datetime(2026, 5, 13, tzinfo=UTC)


@dataclass
class FakeConnection:
    calls: list[tuple[str, tuple[Any, ...]]] = field(default_factory=list)

    def execute(self, query: str, params: tuple[Any, ...]) -> None:
        self.calls.append((query, params))


@dataclass
class FakeCursor:
    rows: list[Any]

    def fetchall(self) -> list[Any]:
        return self.rows


@dataclass
class FakeReadConnection:
    responses: list[list[Any]]
    calls: list[tuple[str, tuple[Any, ...]]] = field(default_factory=list)

    def execute(self, query: str, params: tuple[Any, ...]) -> FakeCursor:
        self.calls.append((query, params))
        return FakeCursor(self.responses.pop(0))


def _jsonb_value(value: Any) -> Any:
    return getattr(value, "obj", value)


def test_postgres_repository_writes_documents_with_payload() -> None:
    ingestion_result = load_seed_dataset(REPO_ROOT)
    connection = FakeConnection()
    repository = PostgresStorageRepository(connection)

    repository.save_documents((ingestion_result.documents[0],))

    query, params = connection.calls[0]

    assert "INSERT INTO documents" in query
    assert params[0] == "doc_fund_a_factsheet"
    assert params[1] == "fund_fact_sheet"
    assert params[2] == "data/sample_documents/fund_a_factsheet.md"
    assert _jsonb_value(params[5])["dataset_name"] == "synthetic_fund_seed"
    assert _jsonb_value(params[8])["document_id"] == "doc_fund_a_factsheet"


def test_postgres_repository_writes_document_chunks_with_payload() -> None:
    connection = FakeConnection()
    repository = PostgresStorageRepository(connection)
    chunk = DocumentChunk(
        chunk_id="chunk_doc_fund_a_factsheet_000",
        document_id="doc_fund_a_factsheet",
        chunk_index=0,
        text="Northstar Growth Fund seeks long-term capital appreciation.",
        metadata={"dataset_name": "synthetic_fund_seed"},
        source_uri="data/sample_documents/fund_a_factsheet.md",
    )

    repository.save_document_chunks((chunk,))

    query, params = connection.calls[0]

    assert "INSERT INTO document_chunks" in query
    assert params[0] == "chunk_doc_fund_a_factsheet_000"
    assert params[1] == "doc_fund_a_factsheet"
    assert params[2] == 0
    assert params[5] is None
    assert params[6] is None
    assert params[7] is None
    assert _jsonb_value(params[8])["dataset_name"] == "synthetic_fund_seed"
    assert _jsonb_value(params[9])["chunk_id"] == "chunk_doc_fund_a_factsheet_000"


def test_postgres_repository_writes_document_chunk_embedding_as_jsonb() -> None:
    connection = FakeConnection()
    repository = PostgresStorageRepository(connection)
    chunk = DocumentChunk(
        chunk_id="chunk_doc_fund_a_factsheet_001",
        document_id="doc_fund_a_factsheet",
        chunk_index=1,
        text="Expense ratio is 0.65%.",
        embedding=[0.1, 0.2, 0.3],
        metadata={"dataset_name": "synthetic_fund_seed"},
        source_uri="data/sample_documents/fund_a_factsheet.md",
    )

    repository.save_document_chunks((chunk,))

    _, params = connection.calls[0]

    assert _jsonb_value(params[5]) == [0.1, 0.2, 0.3]
    assert params[6] == "[0.1,0.2,0.3]"
    assert params[7] == "[0.1,0.2,0.3]"
    assert _jsonb_value(params[9])["embedding"] == [0.1, 0.2, 0.3]


def test_postgres_repository_writes_structured_records_with_stable_key() -> None:
    ingestion_result = load_seed_dataset(REPO_ROOT)
    connection = FakeConnection()
    repository = PostgresStorageRepository(connection)

    repository.save_structured_records((ingestion_result.fund_records[0],))

    query, params = connection.calls[0]

    assert "INSERT INTO structured_records" in query
    assert params[0] == "fund:FUND_A"
    assert params[1] == "fund"
    assert params[2] == "data/sample_funds/funds.json"
    assert _jsonb_value(params[3])["dataset_name"] == "synthetic_fund_seed"
    assert _jsonb_value(params[4])["fund_id"] == "FUND_A"


def test_postgres_repository_writes_eval_cases_with_metadata() -> None:
    ingestion_result = load_seed_dataset(REPO_ROOT)
    connection = FakeConnection()
    repository = PostgresStorageRepository(connection)
    eval_case = next(
        case
        for case in ingestion_result.eval_cases
        if case.case_id == "finagent_ADV_001"
    )

    repository.save_eval_cases((eval_case,))

    query, params = connection.calls[0]

    assert "INSERT INTO evaluation_cases" in query
    assert params[0] == "finagent_ADV_001"
    assert params[1] == "financial_qa"
    assert _jsonb_value(params[3])["source_metadata"]["source_type"] == "adversarial"
    assert _jsonb_value(params[4])["expected_answer"] == "NOT_AVAILABLE"


def test_postgres_repository_writes_ingestion_job_records() -> None:
    connection = FakeConnection()
    repository = PostgresStorageRepository(connection)
    job_record = IngestionJobRecord(
        job_id="ingest_synthetic_fund_seed_0.1.0",
        dataset_name="synthetic_fund_seed",
        source_ids=("synthetic_fund_records", "finagent_benchmark_sample"),
        status="completed",
        document_count=13,
        structured_record_count=7,
        eval_case_count=10,
        started_at=NOW,
        finished_at=NOW,
    )

    repository.save_ingestion_job_record(job_record)

    query, params = connection.calls[0]

    assert "INSERT INTO ingestion_job_records" in query
    assert params[0] == "ingest_synthetic_fund_seed_0.1.0"
    assert params[1] == "synthetic_fund_seed"
    assert _jsonb_value(params[2]) == [
        "synthetic_fund_records",
        "finagent_benchmark_sample",
    ]
    assert params[3] == "completed"
    assert _jsonb_value(params[10])["status"] == "completed"


def test_connect_postgres_repository_uses_psycopg_connect(monkeypatch: Any) -> None:
    connection = FakeConnection()
    calls: list[str] = []

    class FakePsycopg:
        def connect(self, database_url: str) -> FakeConnection:
            calls.append(database_url)
            return connection

    monkeypatch.setitem(sys.modules, "psycopg", FakePsycopg())

    repository = connect_postgres_repository("postgresql://user:pass@db:5432/app")

    assert repository.connection is connection
    assert calls == ["postgresql://user:pass@db:5432/app"]


def test_migration_paths_are_sorted(tmp_path: Path) -> None:
    later = tmp_path / "010_later.sql"
    earlier = tmp_path / "001_earlier.sql"
    later.write_text("SELECT 2;", encoding="utf-8")
    earlier.write_text("SELECT 1;", encoding="utf-8")

    assert migration_paths(tmp_path) == (earlier, later)


def test_run_ingestion_storage_migrations_executes_files_in_order(
    tmp_path: Path,
) -> None:
    (tmp_path / "002_second.sql").write_text("SELECT 2;", encoding="utf-8")
    (tmp_path / "001_first.sql").write_text("SELECT 1;", encoding="utf-8")
    connection = FakeConnection()

    run_ingestion_storage_migrations(connection, tmp_path)

    assert connection.calls == [
        ("SELECT 1;", ()),
        ("SELECT 2;", ()),
    ]


def test_postgres_repository_lists_documents_from_payload_rows() -> None:
    ingestion_result = load_seed_dataset(REPO_ROOT)
    document = ingestion_result.documents[0]
    connection = FakeReadConnection(responses=[[(document.to_mapping(),)]])
    repository = PostgresStorageRepository(connection)

    assert repository.list_documents() == (document,)
    assert "FROM documents" in connection.calls[0][0]
    assert "ORDER BY document_id" in connection.calls[0][0]


def test_postgres_repository_lists_document_chunks_from_payload_rows() -> None:
    chunk = DocumentChunk(
        chunk_id="chunk_doc_fund_a_factsheet_001",
        document_id="doc_fund_a_factsheet",
        chunk_index=1,
        text="Expense ratio is 0.65%.",
        embedding=[0.1, 0.2, 0.3],
        metadata={"dataset_name": "synthetic_fund_seed"},
        source_uri="data/sample_documents/fund_a_factsheet.md",
    )
    connection = FakeReadConnection(responses=[[(chunk.to_mapping(),)]])
    repository = PostgresStorageRepository(connection)

    assert repository.list_document_chunks() == (chunk,)
    assert "FROM document_chunks" in connection.calls[0][0]
    assert "ORDER BY document_id, chunk_index, chunk_id" in connection.calls[0][0]


def test_postgres_repository_lists_structured_records_from_payload_rows() -> None:
    ingestion_result = load_seed_dataset(REPO_ROOT)
    fund_record = ingestion_result.fund_records[0]
    connection = FakeReadConnection(responses=[[(fund_record.to_mapping(),)]])
    repository = PostgresStorageRepository(connection)

    assert repository.list_structured_records() == (fund_record,)
    assert "FROM structured_records" in connection.calls[0][0]
    assert "ORDER BY record_type, record_key" in connection.calls[0][0]


def test_postgres_repository_lists_eval_cases_from_dict_payload_rows() -> None:
    ingestion_result = load_seed_dataset(REPO_ROOT)
    eval_case = next(
        case
        for case in ingestion_result.eval_cases
        if case.case_id == "finagent_FE_001"
    )
    connection = FakeReadConnection(responses=[[{"payload": eval_case.to_mapping()}]])
    repository = PostgresStorageRepository(connection)

    assert repository.list_eval_cases() == (eval_case,)
    assert "FROM evaluation_cases" in connection.calls[0][0]
    assert "ORDER BY case_id" in connection.calls[0][0]


def test_postgres_repository_lists_ingestion_job_records_from_payload_rows() -> None:
    job_record = IngestionJobRecord(
        job_id="ingest_synthetic_fund_seed_0.1.0",
        dataset_name="synthetic_fund_seed",
        source_ids=("synthetic_fund_records", "finagent_benchmark_sample"),
        status="completed",
        document_count=13,
        structured_record_count=7,
        eval_case_count=10,
        started_at=NOW,
        finished_at=NOW,
    )
    connection = FakeReadConnection(responses=[[(job_record.to_mapping(),)]])
    repository = PostgresStorageRepository(connection)

    assert repository.list_ingestion_job_records() == (job_record,)
    assert "FROM ingestion_job_records" in connection.calls[0][0]
    assert "ORDER BY started_at, job_id" in connection.calls[0][0]


def test_ingestion_storage_schema_declares_expected_tables() -> None:
    schema = (
        REPO_ROOT / "storage/migrations/001_ingestion_storage.sql"
    ).read_text(encoding="utf-8")
    vector_migration = (
        REPO_ROOT / "storage/migrations/002_document_chunk_embedding_vector.sql"
    ).read_text(encoding="utf-8")

    assert "CREATE TABLE IF NOT EXISTS ingestion_job_records" in schema
    assert "CREATE TABLE IF NOT EXISTS documents" in schema
    assert "CREATE TABLE IF NOT EXISTS document_chunks" in schema
    assert "CREATE TABLE IF NOT EXISTS structured_records" in schema
    assert "CREATE TABLE IF NOT EXISTS evaluation_cases" in schema
    assert "JSONB" in schema
    assert "ADD COLUMN IF NOT EXISTS embedding_vector vector(512)" in vector_migration
