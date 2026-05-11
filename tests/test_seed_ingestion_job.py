from __future__ import annotations

from pathlib import Path

from ingestion.jobs import load_seed_dataset


REPO_ROOT = Path(__file__).resolve().parents[1]


def test_load_seed_dataset_runs_end_to_end_without_external_services() -> None:
    result = load_seed_dataset(REPO_ROOT)

    assert result.manifest.dataset_name == "synthetic_fund_seed"
    assert len(result.resolved_sources) == 7
    assert len(result.fund_records) == 4
    assert len(result.issue_records) == 3
    assert len(result.documents) == 13
    assert len(result.eval_cases) == 5
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
