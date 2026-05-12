from __future__ import annotations

from dataclasses import FrozenInstanceError
from datetime import UTC, datetime

import pytest

from storage.models import (
    Document,
    DocumentChunk,
    EvalCase,
    ModelValidationError,
    StructuredRecord,
)


NOW = datetime(2026, 5, 11, tzinfo=UTC)


def test_document_matches_canonical_shape() -> None:
    document = Document(
        document_id="doc_fund_a_factsheet",
        source_type="fund_fact_sheet",
        source_uri="data/sample_documents/fund_a_factsheet.md",
        title="Northstar Growth Fund Factsheet",
        body="Northstar Growth Fund seeks long-term capital appreciation.",
        metadata={"dataset_name": "synthetic_fund_seed", "fund_id": "FUND_A"},
        created_at=NOW,
        updated_at=NOW,
    )

    assert document.to_mapping() == {
        "document_id": "doc_fund_a_factsheet",
        "source_type": "fund_fact_sheet",
        "source_uri": "data/sample_documents/fund_a_factsheet.md",
        "title": "Northstar Growth Fund Factsheet",
        "body": "Northstar Growth Fund seeks long-term capital appreciation.",
        "metadata": {"dataset_name": "synthetic_fund_seed", "fund_id": "FUND_A"},
        "created_at": "2026-05-11T00:00:00+00:00",
        "updated_at": "2026-05-11T00:00:00+00:00",
    }


def test_document_requires_non_empty_required_fields() -> None:
    with pytest.raises(ModelValidationError, match="document_id"):
        Document(
            document_id="",
            source_type="fund_fact_sheet",
            source_uri="data/sample_documents/fund_a_factsheet.md",
            title="Northstar Growth Fund Factsheet",
            body="Northstar Growth Fund seeks long-term capital appreciation.",
            metadata={},
            created_at=NOW,
            updated_at=NOW,
        )


def test_document_chunk_accepts_missing_embedding_until_embedding_stage() -> None:
    chunk = DocumentChunk(
        chunk_id="chunk_doc_fund_a_factsheet_000",
        document_id="doc_fund_a_factsheet",
        chunk_index=0,
        text="Northstar Growth Fund seeks long-term capital appreciation.",
        metadata={"fund_id": "FUND_A", "source_type": "fund_fact_sheet"},
        source_uri="data/sample_documents/fund_a_factsheet.md",
    )

    assert chunk.embedding is None
    assert chunk.to_mapping()["embedding"] is None


def test_document_chunk_rejects_negative_index() -> None:
    with pytest.raises(ModelValidationError, match="chunk_index"):
        DocumentChunk(
            chunk_id="chunk_doc_fund_a_factsheet_000",
            document_id="doc_fund_a_factsheet",
            chunk_index=-1,
            text="Northstar Growth Fund seeks long-term capital appreciation.",
            metadata={},
            source_uri="data/sample_documents/fund_a_factsheet.md",
        )


def test_structured_record_flattens_type_specific_values() -> None:
    record = StructuredRecord(
        record_type="fund",
        source_uri="data/sample_funds/funds.json",
        metadata={"dataset_name": "synthetic_fund_seed"},
        values={
            "fund_id": "FUND_A",
            "name": "Northstar Growth Fund",
            "category": "US Equity",
            "investment_style": "growth",
            "expense_ratio": 0.65,
            "return_1y": 12.4,
            "return_3y": 8.9,
            "volatility": 15.2,
            "sharpe": 0.71,
            "aum_millions": 1840,
            "inception_year": 2016,
        },
    )

    assert record.to_mapping()["record_type"] == "fund"
    assert record.to_mapping()["fund_id"] == "FUND_A"
    assert record.to_mapping()["metadata"] == {"dataset_name": "synthetic_fund_seed"}


def test_eval_case_matches_canonical_shape() -> None:
    eval_case = EvalCase(
        case_id="fund_compare_001",
        task_type="fund_comparison",
        question="Compare FUND_A and FUND_B.",
        entities=[
            {"entity_type": "fund", "entity_id": "FUND_A"},
            {"entity_type": "fund", "entity_id": "FUND_B"},
        ],
        expected_answer=None,
        expected_citations=[
            {"source_uri": "data/sample_documents/fund_a_factsheet.md"},
            {"source_uri": "data/sample_documents/fund_b_factsheet.md"},
        ],
        evaluation_tags=["fund_comparison", "citation_required"],
        safety_expectations={"should_refuse": False, "requires_disclaimer": True},
        metadata={
            "dataset_name": "synthetic_fund_seed",
            "source_uri": "data/eval_cases/fund_eval_cases.json",
        },
    )

    assert eval_case.to_mapping()["case_id"] == "fund_compare_001"
    assert len(eval_case.to_mapping()["expected_citations"]) == 2
    assert eval_case.to_mapping()["metadata"] == {
        "dataset_name": "synthetic_fund_seed",
        "source_uri": "data/eval_cases/fund_eval_cases.json",
    }


def test_models_are_frozen_after_creation() -> None:
    record = StructuredRecord(record_type="fund")

    with pytest.raises(FrozenInstanceError):
        record.record_type = "github_issue"
