from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

import pytest

from ingestion.normalizers import (
    NormalizationError,
    normalize_markdown_document,
    normalize_markdown_document_file,
)


REPO_ROOT = Path(__file__).resolve().parents[1]
FIXED_TIME = datetime(2026, 5, 11, tzinfo=UTC)


def test_normalize_factsheet_file_returns_canonical_document() -> None:
    document = normalize_markdown_document_file(
        REPO_ROOT / "data/sample_documents/fund_a_factsheet.md",
        source_id="fund_a_factsheet",
        source_type="fund_fact_sheet",
        source_uri="data/sample_documents/fund_a_factsheet.md",
        dataset_name="synthetic_fund_seed",
        fund_id="FUND_A",
        created_at=FIXED_TIME,
        updated_at=FIXED_TIME,
    )

    assert document.document_id == "doc_fund_a_factsheet"
    assert document.source_type == "fund_fact_sheet"
    assert document.source_uri == "data/sample_documents/fund_a_factsheet.md"
    assert document.title == "Northstar Growth Fund Factsheet"
    assert "## Strategy" in document.body
    assert document.metadata == {
        "dataset_name": "synthetic_fund_seed",
        "source_id": "fund_a_factsheet",
        "source_type": "fund_fact_sheet",
        "fund_id": "FUND_A",
        "as_of": "2026-03-31",
    }


def test_normalize_all_sample_factsheets_returns_four_documents() -> None:
    documents = [
        normalize_markdown_document_file(
            REPO_ROOT / f"data/sample_documents/fund_{fund_letter}_factsheet.md",
            source_id=f"fund_{fund_letter}_factsheet",
            source_type="fund_fact_sheet",
            source_uri=f"data/sample_documents/fund_{fund_letter}_factsheet.md",
            dataset_name="synthetic_fund_seed",
            fund_id=f"FUND_{fund_letter.upper()}",
            created_at=FIXED_TIME,
            updated_at=FIXED_TIME,
        )
        for fund_letter in ("a", "b", "c", "d")
    ]

    assert len(documents) == 4
    assert {document.document_id for document in documents} == {
        "doc_fund_a_factsheet",
        "doc_fund_b_factsheet",
        "doc_fund_c_factsheet",
        "doc_fund_d_factsheet",
    }
    assert {document.metadata["fund_id"] for document in documents} == {
        "FUND_A",
        "FUND_B",
        "FUND_C",
        "FUND_D",
    }


def test_document_normalization_can_infer_fund_id_from_header() -> None:
    document = normalize_markdown_document(
        "# Example Fund Factsheet\n\nFund ID: FUND_X\nAs of: 2026-03-31\n\n## Strategy\nText.",
        source_id="example_factsheet",
        source_type="fund_fact_sheet",
        source_uri="memory://example",
        dataset_name="synthetic_fund_seed",
        created_at=FIXED_TIME,
        updated_at=FIXED_TIME,
    )

    assert document.metadata["fund_id"] == "FUND_X"
    assert document.metadata["as_of"] == "2026-03-31"


def test_document_normalization_rejects_empty_document() -> None:
    with pytest.raises(NormalizationError, match="empty"):
        normalize_markdown_document(
            "   ",
            source_id="empty",
            source_type="fund_fact_sheet",
            source_uri="memory://empty",
            dataset_name="synthetic_fund_seed",
        )


def test_document_normalization_rejects_missing_h1_title() -> None:
    with pytest.raises(NormalizationError, match="missing an H1 title"):
        normalize_markdown_document(
            "Fund ID: FUND_X\n\n## Strategy\nText.",
            source_id="missing_title",
            source_type="fund_fact_sheet",
            source_uri="memory://missing-title",
            dataset_name="synthetic_fund_seed",
        )

