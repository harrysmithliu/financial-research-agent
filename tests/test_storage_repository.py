from __future__ import annotations

from pathlib import Path

from ingestion.jobs import load_seed_dataset
from storage.repository import InMemoryStorageRepository


REPO_ROOT = Path(__file__).resolve().parents[1]


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

