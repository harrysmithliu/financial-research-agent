from __future__ import annotations

from datetime import UTC, datetime

import pytest

from ingestion.chunker import chunk_documents
from storage.models import Document


NOW = datetime(2026, 5, 13, tzinfo=UTC)


def _document(body: str) -> Document:
    return Document(
        document_id="doc_fund_a_factsheet",
        source_type="fund_fact_sheet",
        source_uri="data/sample_documents/fund_a_factsheet.md",
        title="Northstar Growth Fund Factsheet",
        body=body,
        metadata={"dataset_name": "synthetic_fund_seed", "fund_id": "FUND_A"},
        created_at=NOW,
        updated_at=NOW,
    )


def test_chunk_documents_creates_citation_ready_chunk_for_short_document() -> None:
    document = _document("Northstar Growth Fund seeks long-term capital appreciation.")

    chunks = chunk_documents((document,))

    assert len(chunks) == 1
    assert chunks[0].chunk_id == "chunk_doc_fund_a_factsheet_000"
    assert chunks[0].document_id == "doc_fund_a_factsheet"
    assert chunks[0].chunk_index == 0
    assert chunks[0].text == document.body
    assert chunks[0].embedding is None
    assert chunks[0].source_uri == document.source_uri
    assert chunks[0].metadata["dataset_name"] == "synthetic_fund_seed"
    assert chunks[0].metadata["fund_id"] == "FUND_A"
    assert chunks[0].metadata["document_title"] == document.title
    assert chunks[0].metadata["chunk_count"] == 1


def test_chunk_documents_splits_long_document_with_stable_overlap() -> None:
    document = _document("alpha beta gamma delta epsilon zeta eta theta")

    chunks = chunk_documents((document,), max_chars=17, overlap_chars=5)

    assert [chunk.chunk_id for chunk in chunks] == [
        "chunk_doc_fund_a_factsheet_000",
        "chunk_doc_fund_a_factsheet_001",
        "chunk_doc_fund_a_factsheet_002",
        "chunk_doc_fund_a_factsheet_003",
        "chunk_doc_fund_a_factsheet_004",
    ]
    assert [chunk.text for chunk in chunks] == [
        "alpha beta gamma",
        "gamma delta",
        "delta epsilon",
        "epsilon zeta eta",
        "zeta eta theta",
    ]
    assert all(chunk.metadata["chunk_count"] == 5 for chunk in chunks)


def test_chunk_documents_validates_window_settings() -> None:
    document = _document("Northstar Growth Fund seeks long-term capital appreciation.")

    with pytest.raises(ValueError, match="max_chars"):
        chunk_documents((document,), max_chars=0)

    with pytest.raises(ValueError, match="overlap_chars"):
        chunk_documents((document,), max_chars=10, overlap_chars=10)
