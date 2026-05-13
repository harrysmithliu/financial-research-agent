from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

from ingestion.jobs import load_seed_dataset
from storage.models import IngestionJobRecord
from storage.repository import InMemoryStorageRepository


REPO_ROOT = Path(__file__).resolve().parents[1]
NOW = datetime(2026, 5, 12, tzinfo=UTC)


def test_in_memory_repository_saves_canonical_ingestion_outputs() -> None:
    ingestion_result = load_seed_dataset(REPO_ROOT)
    repository = InMemoryStorageRepository()

    repository.save_structured_records(ingestion_result.structured_records)
    repository.save_documents(ingestion_result.documents)
    repository.save_eval_cases(ingestion_result.eval_cases)

    assert len(repository.list_structured_records()) == 7
    assert len(repository.list_documents()) == 13
    assert len(repository.list_eval_cases()) == 10


def test_in_memory_repository_preserves_citation_and_audit_metadata() -> None:
    ingestion_result = load_seed_dataset(REPO_ROOT)
    repository = InMemoryStorageRepository()

    repository.save_structured_records(ingestion_result.structured_records)
    repository.save_documents(ingestion_result.documents)
    repository.save_eval_cases(ingestion_result.eval_cases)

    fact_sheet = next(
        document
        for document in repository.list_documents()
        if document.document_id == "doc_fund_a_factsheet"
    )
    issue_record = next(
        record
        for record in repository.list_structured_records()
        if record.record_type == "github_issue"
        and record.values["issue_id"] == "issue_openbb_like_001"
    )
    finagent_case = next(
        eval_case
        for eval_case in repository.list_eval_cases()
        if eval_case.case_id == "finagent_FE_001"
    )

    assert fact_sheet.source_uri == "data/sample_documents/fund_a_factsheet.md"
    assert fact_sheet.metadata["dataset_name"] == "synthetic_fund_seed"
    assert fact_sheet.metadata["fund_id"] == "FUND_A"
    assert issue_record.source_uri == "data/sample_issues/issues.json"
    assert issue_record.metadata["dataset_name"] == "synthetic_fund_seed"
    assert finagent_case.expected_citations[0]["source_uri"].startswith(
        "hf://Guen/finagent-benchmark/"
    )
    assert (
        finagent_case.metadata["source_metadata"]["dataset_url"]
        == "https://huggingface.co/datasets/Guen/finagent-benchmark"
    )


def test_in_memory_repository_saves_ingestion_job_records() -> None:
    repository = InMemoryStorageRepository()
    job_record = IngestionJobRecord(
        job_id="ingest_synthetic_fund_seed_001",
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

    assert repository.list_ingestion_job_records() == (job_record,)
