from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

from ingestion.jobs import load_seed_dataset, run_seed_ingestion
from storage.models import DocumentChunk, IngestionJobRecord
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


def test_in_memory_repository_saves_document_chunks() -> None:
    repository = InMemoryStorageRepository()
    chunk = DocumentChunk(
        chunk_id="chunk_doc_fund_a_factsheet_000",
        document_id="doc_fund_a_factsheet",
        chunk_index=0,
        text="Northstar Growth Fund seeks long-term capital appreciation.",
        metadata={"dataset_name": "synthetic_fund_seed"},
        source_uri="data/sample_documents/fund_a_factsheet.md",
    )

    repository.save_document_chunks((chunk,))

    assert repository.list_document_chunks() == (chunk,)


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


def test_repository_retains_fund_record_fields_needed_for_structured_lookup() -> None:
    repository = InMemoryStorageRepository()

    run_seed_ingestion(REPO_ROOT, repository, started_at=NOW)

    fund_record = next(
        record
        for record in repository.list_structured_records()
        if record.record_type == "fund" and record.values["fund_id"] == "FUND_A"
    )

    assert fund_record.source_uri == "data/sample_funds/funds.json"
    assert fund_record.metadata == {
        "dataset_name": "synthetic_fund_seed",
        "source_record_index": 0,
    }
    assert fund_record.values["name"] == "Northstar Growth Fund"
    assert fund_record.values["category"] == "US Equity"
    assert fund_record.values["expense_ratio"] == 0.65
    assert fund_record.values["volatility"] == 15.2


def test_repository_retains_issue_comment_document_parentage_for_citations() -> None:
    repository = InMemoryStorageRepository()

    run_seed_ingestion(REPO_ROOT, repository, started_at=NOW)

    comment_document = next(
        document
        for document in repository.list_documents()
        if document.document_id == "doc_issue_openbb_like_001_comment_001"
    )

    assert comment_document.source_type == "github_issue_comment"
    assert comment_document.source_uri.endswith(
        "#comment-issue_openbb_like_001_comment_001"
    )
    assert comment_document.metadata["dataset_name"] == "synthetic_fund_seed"
    assert comment_document.metadata["issue_id"] == "issue_openbb_like_001"
    assert comment_document.metadata["comment_id"] == (
        "issue_openbb_like_001_comment_001"
    )
    assert comment_document.metadata["parent_source_uri"] == (
        "https://github.com/synthetic-finance/openbb-like-platform/issues/101"
    )


def test_repository_retains_finagent_eval_metadata_for_replay() -> None:
    repository = InMemoryStorageRepository()

    run_seed_ingestion(REPO_ROOT, repository, started_at=NOW)

    eval_case = next(
        case
        for case in repository.list_eval_cases()
        if case.case_id == "finagent_ADV_001"
    )

    assert eval_case.expected_answer == "NOT_AVAILABLE"
    assert eval_case.metadata["dataset_name"] == "synthetic_fund_seed"
    assert eval_case.metadata["source_uri"] == (
        "data/external/finagent_benchmark_sample.json"
    )
    assert eval_case.metadata["source_metadata"]["source_record_id"] == "ADV_001"
    assert eval_case.metadata["source_metadata"]["source_type"] == "adversarial"
    assert eval_case.metadata["source_metadata"]["verification_note"] == (
        "HUMAN_VERIFIED_ORIGINAL_CONFIRMED"
    )


def test_repository_retains_ingestion_job_source_ids_for_audit() -> None:
    repository = InMemoryStorageRepository()

    run_seed_ingestion(REPO_ROOT, repository, started_at=NOW)

    job_record = repository.list_ingestion_job_records()[0]

    assert job_record.job_id == "ingest_synthetic_fund_seed_0.1.0"
    assert job_record.source_ids == (
        "synthetic_fund_records",
        "fund_a_factsheet",
        "fund_b_factsheet",
        "fund_c_factsheet",
        "fund_d_factsheet",
        "synthetic_platform_issues",
        "fund_eval_cases",
        "finagent_benchmark_sample",
    )
