from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

import pytest

from ingestion.jobs import load_seed_dataset, run_seed_ingestion
from storage.repository import InMemoryStorageRepository


REPO_ROOT = Path(__file__).resolve().parents[1]
NOW = datetime(2026, 5, 12, tzinfo=UTC)


def test_load_seed_dataset_runs_end_to_end_without_external_services() -> None:
    result = load_seed_dataset(REPO_ROOT)

    assert result.manifest.dataset_name == "synthetic_fund_seed"
    assert len(result.resolved_sources) == 8
    assert len(result.fund_records) == 4
    assert len(result.issue_records) == 3
    assert len(result.documents) == 13
    assert len(result.eval_cases) == 10
    assert len(result.structured_records) == 7


def test_load_seed_dataset_preserves_expected_entity_identifiers() -> None:
    result = load_seed_dataset(REPO_ROOT)

    assert {record.values["fund_id"] for record in result.fund_records} == {
        "FUND_A",
        "FUND_B",
        "FUND_C",
        "FUND_D",
    }
    assert {record.values["issue_id"] for record in result.issue_records} == {
        "issue_openbb_like_001",
        "issue_openbb_like_002",
        "issue_openbb_like_003",
    }
    assert {case.case_id for case in result.eval_cases} == {
        "fund_compare_001",
        "fund_brief_001",
        "fund_qa_001",
        "fund_qa_002",
        "fund_compare_002",
        "finagent_FE_001",
        "finagent_NR_001",
        "finagent_TR_001",
        "finagent_MH_001",
        "finagent_ADV_001",
    }


def test_load_seed_dataset_preserves_citation_source_uris() -> None:
    result = load_seed_dataset(REPO_ROOT)

    document_source_uris = {document.source_uri for document in result.documents}

    assert "data/sample_documents/fund_a_factsheet.md" in document_source_uris
    assert "data/sample_documents/fund_d_factsheet.md" in document_source_uris
    assert (
        "https://github.com/synthetic-finance/openbb-like-platform/issues/101"
        in document_source_uris
    )
    assert any(
        "#comment-issue_openbb_like_001_comment_001" in source_uri
        for source_uri in document_source_uris
    )
    assert all(
        citation["source_uri"]
        for eval_case in result.eval_cases
        for citation in eval_case.expected_citations
    )


def test_run_seed_ingestion_persists_outputs_and_completed_job_record() -> None:
    repository = InMemoryStorageRepository()

    run_result = run_seed_ingestion(REPO_ROOT, repository, started_at=NOW)

    assert len(repository.list_structured_records()) == 7
    assert len(repository.list_documents()) == 13
    assert len(repository.list_eval_cases()) == 10
    assert repository.list_ingestion_job_records() == (run_result.job_record,)
    assert run_result.job_record.status == "completed"
    assert run_result.job_record.dataset_name == "synthetic_fund_seed"
    assert run_result.job_record.source_ids == tuple(
        resolved_source.source.source_id
        for resolved_source in run_result.ingestion_result.resolved_sources
    )
    assert run_result.job_record.document_count == 13
    assert run_result.job_record.structured_record_count == 7
    assert run_result.job_record.eval_case_count == 10
    assert run_result.job_record.started_at == NOW
    assert run_result.job_record.finished_at is not None


def test_run_seed_ingestion_records_failed_job_before_reraising(tmp_path: Path) -> None:
    repository = InMemoryStorageRepository()

    with pytest.raises(FileNotFoundError):
        run_seed_ingestion(tmp_path, repository, started_at=NOW)

    failed_record = repository.list_ingestion_job_records()[0]

    assert failed_record.status == "failed"
    assert failed_record.started_at == NOW
    assert failed_record.finished_at is not None
    assert failed_record.document_count == 0
    assert failed_record.structured_record_count == 0
    assert failed_record.eval_case_count == 0
    assert failed_record.error_message is not None
