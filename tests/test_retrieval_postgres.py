from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from retrieval.embeddings import DeterministicEmbeddingProvider
from retrieval.postgres import (
    backfill_document_chunk_vectors,
    ensure_document_chunk_vector_index,
    search_document_chunks_by_vector,
)
from retrieval.service import RetrievalService


@dataclass
class FakeCursor:
    rows: list[Any] = field(default_factory=list)
    rowcount: int = 0

    def fetchall(self) -> list[Any]:
        return self.rows


@dataclass
class FakeConnection:
    calls: list[tuple[str, tuple[Any, ...]]] = field(default_factory=list)
    responses: list[FakeCursor] = field(default_factory=list)
    fail_on_hnsw: bool = False

    def execute(self, query: str, params: tuple[Any, ...]) -> FakeCursor:
        self.calls.append((query, params))
        if self.fail_on_hnsw and "USING hnsw" in query:
            raise RuntimeError("hnsw not available")
        if self.responses:
            return self.responses.pop(0)
        return FakeCursor()


def test_ensure_document_chunk_vector_index_uses_hnsw_when_available() -> None:
    connection = FakeConnection()

    index_method = ensure_document_chunk_vector_index(connection)

    assert index_method == "hnsw"
    assert "USING hnsw" in connection.calls[0][0]


def test_ensure_document_chunk_vector_index_falls_back_to_ivfflat() -> None:
    connection = FakeConnection(fail_on_hnsw=True)

    index_method = ensure_document_chunk_vector_index(connection)

    assert index_method == "ivfflat"
    assert "USING hnsw" in connection.calls[0][0]
    assert "USING ivfflat" in connection.calls[1][0]


def test_backfill_document_chunk_vectors_updates_matching_rows() -> None:
    connection = FakeConnection(responses=[FakeCursor(rowcount=3)])

    updated = backfill_document_chunk_vectors(connection, embedding_dimensions=512)

    assert updated == 3
    assert "UPDATE document_chunks" in connection.calls[0][0]
    assert connection.calls[0][1] == (512,)


def test_search_document_chunks_by_vector_preserves_citation_fields() -> None:
    connection = FakeConnection(
        responses=[
            FakeCursor(
                rows=[
                    (
                        "chunk_doc_fund_a_factsheet_000",
                        "doc_fund_a_factsheet",
                        0,
                        "data/sample_documents/fund_a_factsheet.md",
                        "Northstar Growth Fund seeks long-term capital appreciation.",
                        {
                            "dataset_name": "synthetic_fund_seed",
                            "source_id": "fund_a_factsheet",
                        },
                        0.12,
                    )
                ]
            )
        ]
    )

    results = search_document_chunks_by_vector(
        connection,
        query_embedding=[0.1, 0.2, 0.3],
        top_k=5,
    )

    assert len(results) == 1
    first = results[0]
    assert first.chunk_id == "chunk_doc_fund_a_factsheet_000"
    assert first.document_id == "doc_fund_a_factsheet"
    assert first.source_uri == "data/sample_documents/fund_a_factsheet.md"
    assert first.metadata["dataset_name"] == "synthetic_fund_seed"


def test_retrieval_service_search_embeds_query_and_calls_vector_search() -> None:
    connection = FakeConnection(
        responses=[
            FakeCursor(
                rows=[
                    {
                        "chunk_id": "chunk_doc_fund_b_factsheet_000",
                        "document_id": "doc_fund_b_factsheet",
                        "chunk_index": 0,
                        "source_uri": "data/sample_documents/fund_b_factsheet.md",
                        "text": "BlueRiver Income Fund emphasizes lower volatility.",
                        "metadata": {"dataset_name": "synthetic_fund_seed"},
                        "distance": 0.09,
                    }
                ]
            )
        ]
    )
    provider = DeterministicEmbeddingProvider(dimensions=8)
    service = RetrievalService(
        connection=connection,
        embedding_provider=provider,
        embedding_dimensions=8,
        default_top_k=5,
    )

    results = service.search("Compare Fund A and Fund B")

    assert len(results) == 1
    assert results[0].chunk_id == "chunk_doc_fund_b_factsheet_000"
    assert "ORDER BY embedding_vector <=>" in connection.calls[0][0]
    assert connection.calls[0][1][2] == 5


def test_search_document_chunks_by_vector_rejects_invalid_input() -> None:
    connection = FakeConnection()

    try:
        search_document_chunks_by_vector(connection, query_embedding=[], top_k=5)
    except ValueError as exc:
        assert str(exc) == "query_embedding must not be empty"
    else:
        raise AssertionError("Expected ValueError for empty query embedding")

    try:
        search_document_chunks_by_vector(connection, query_embedding=[0.1], top_k=0)
    except ValueError as exc:
        assert str(exc) == "top_k must be positive"
    else:
        raise AssertionError("Expected ValueError for non-positive top_k")
