from __future__ import annotations

from pathlib import Path

import pytest

from ingestion.normalizers import (
    NormalizationError,
    normalize_eval_cases,
    normalize_eval_cases_file,
    normalize_issue_records,
    normalize_issue_records_file,
)


REPO_ROOT = Path(__file__).resolve().parents[1]
ISSUES_SOURCE_URI = "data/sample_issues/issues.json"
ISSUES_PATH = REPO_ROOT / ISSUES_SOURCE_URI
EVAL_SOURCE_URI = "data/eval_cases/fund_eval_cases.json"
EVAL_PATH = REPO_ROOT / EVAL_SOURCE_URI


def test_normalize_sample_issues_returns_metadata_records_and_documents() -> None:
    result = normalize_issue_records_file(
        ISSUES_PATH,
        source_uri=ISSUES_SOURCE_URI,
        dataset_name="synthetic_fund_seed",
    )

    assert len(result.issue_records) == 3
    assert len(result.documents) == 9
    assert {record.record_type for record in result.issue_records} == {"github_issue"}
    assert {document.source_type for document in result.documents} == {
        "github_issue",
        "github_issue_comment",
    }


def test_issue_metadata_record_preserves_queryable_fields() -> None:
    result = normalize_issue_records_file(
        ISSUES_PATH,
        source_uri=ISSUES_SOURCE_URI,
        dataset_name="synthetic_fund_seed",
    )

    first_record = result.issue_records[0].to_mapping()

    assert first_record["record_type"] == "github_issue"
    assert first_record["issue_id"] == "issue_openbb_like_001"
    assert first_record["repo"] == "synthetic-finance/openbb-like-platform"
    assert first_record["number"] == 101
    assert first_record["labels"] == ["bug", "options", "data-quality"]
    assert first_record["state"] == "open"
    assert first_record["comment_count"] == 2
    assert first_record["source_uri"] == ISSUES_SOURCE_URI
    assert first_record["metadata"] == {
        "dataset_name": "synthetic_fund_seed",
        "source_record_index": 0,
    }


def test_issue_documents_preserve_body_and_comment_parentage() -> None:
    result = normalize_issue_records_file(
        ISSUES_PATH,
        source_uri=ISSUES_SOURCE_URI,
        dataset_name="synthetic_fund_seed",
    )

    issue_document = result.documents[0]
    comment_document = result.documents[1]

    assert issue_document.document_id == "doc_issue_openbb_like_001"
    assert issue_document.source_type == "github_issue"
    assert issue_document.title == (
        "Options chain response drops implied volatility for weekly expirations"
    )
    assert "implied_volatility field is null" in issue_document.body
    assert issue_document.metadata["document_kind"] == "issue_body"

    assert comment_document.document_id == "doc_issue_openbb_like_001_comment_001"
    assert comment_document.source_type == "github_issue_comment"
    assert comment_document.metadata["issue_id"] == "issue_openbb_like_001"
    assert comment_document.metadata["comment_id"] == "issue_openbb_like_001_comment_001"
    assert comment_document.metadata["parent_source_uri"] == issue_document.source_uri
    assert "#comment-issue_openbb_like_001_comment_001" in comment_document.source_uri


def test_issue_normalization_rejects_missing_comment_body() -> None:
    raw_issues = [
        {
            "issue_id": "issue_001",
            "repo": "example/repo",
            "number": 1,
            "title": "Example issue",
            "body": "Issue body",
            "labels": ["bug"],
            "state": "open",
            "source_uri": "https://github.com/example/repo/issues/1",
            "created_at": "2026-04-02T14:12:00Z",
            "updated_at": "2026-04-05T09:30:00Z",
            "comments": [
                {
                    "comment_id": "comment_001",
                    "author": "maintainer",
                    "created_at": "2026-04-03T10:18:00Z",
                }
            ],
        }
    ]

    with pytest.raises(NormalizationError, match="body"):
        normalize_issue_records(
            raw_issues,
            source_uri=ISSUES_SOURCE_URI,
            dataset_name="synthetic_fund_seed",
        )


def test_normalize_sample_eval_cases_returns_five_eval_cases() -> None:
    cases = normalize_eval_cases_file(
        EVAL_PATH,
        source_uri=EVAL_SOURCE_URI,
        dataset_name="synthetic_fund_seed",
    )

    assert len(cases) == 5
    assert {case.case_id for case in cases} == {
        "fund_compare_001",
        "fund_brief_001",
        "fund_qa_001",
        "fund_qa_002",
        "fund_compare_002",
    }
    assert all(
        case.safety_expectations["dataset_name"] == "synthetic_fund_seed"
        for case in cases
    )


def test_eval_case_preserves_expected_citations_and_safety_expectations() -> None:
    cases = normalize_eval_cases_file(
        EVAL_PATH,
        source_uri=EVAL_SOURCE_URI,
        dataset_name="synthetic_fund_seed",
    )

    first_case = cases[0].to_mapping()

    assert first_case["case_id"] == "fund_compare_001"
    assert first_case["task_type"] == "fund_comparison"
    assert first_case["entities"] == [
        {"entity_type": "fund", "entity_id": "FUND_A"},
        {"entity_type": "fund", "entity_id": "FUND_B"},
    ]
    assert first_case["expected_citations"] == [
        {"source_uri": "data/sample_documents/fund_a_factsheet.md"},
        {"source_uri": "data/sample_documents/fund_b_factsheet.md"},
    ]
    assert first_case["safety_expectations"]["requires_disclaimer"] is True
    assert first_case["safety_expectations"]["source_uri"] == EVAL_SOURCE_URI


def test_eval_case_normalization_rejects_missing_question() -> None:
    raw_cases = [
        {
            "case_id": "case_001",
            "task_type": "financial_qa",
            "entities": [],
            "expected_citations": [],
            "evaluation_tags": ["financial_qa"],
            "safety_expectations": {"should_refuse": False},
        }
    ]

    with pytest.raises(NormalizationError, match="question"):
        normalize_eval_cases(
            raw_cases,
            source_uri=EVAL_SOURCE_URI,
            dataset_name="synthetic_fund_seed",
        )

