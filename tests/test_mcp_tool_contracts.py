from __future__ import annotations

from mcp_gateway.errors import McpToolError, ToolErrorCode
from mcp_gateway.schemas import (
    CitationChunk,
    DocumentRetrievalRequest,
    DocumentRetrievalResponse,
)


def test_document_retrieval_request_validates_query_and_top_k() -> None:
    request = DocumentRetrievalRequest(query="Compare fund fees", top_k=3)
    assert request.to_mapping() == {"query": "Compare fund fees", "top_k": 3}

    try:
        DocumentRetrievalRequest(query="", top_k=3)
    except ValueError as exc:
        assert str(exc) == "query must be a non-empty string"
    else:
        raise AssertionError("Expected ValueError for empty query")

    try:
        DocumentRetrievalRequest(query="ok", top_k=0)
    except ValueError as exc:
        assert str(exc) == "top_k must be a positive integer"
    else:
        raise AssertionError("Expected ValueError for non-positive top_k")


def test_document_retrieval_response_exposes_citations_and_document_ids() -> None:
    first_chunk = CitationChunk(
        chunk_id="chunk_001",
        document_id="doc_a",
        source_uri="data/sample_documents/fund_a_factsheet.md",
        chunk_index=0,
        text="Fund A has a 0.72% expense ratio.",
        metadata={"dataset_name": "synthetic_fund_seed"},
        distance=0.10,
    )
    second_chunk = CitationChunk(
        chunk_id="chunk_002",
        document_id="doc_b",
        source_uri="data/sample_documents/fund_b_factsheet.md",
        chunk_index=0,
        text="Fund B has a 0.45% expense ratio.",
        metadata={"dataset_name": "synthetic_fund_seed"},
        distance=0.14,
    )
    response = DocumentRetrievalResponse(
        request_id="req-001",
        tool_name="document_retrieval",
        query="Compare expense ratios",
        top_k=2,
        chunks=(first_chunk, second_chunk, first_chunk),
    )

    assert response.retrieved_documents == ("doc_a", "doc_b")
    assert len(response.citations) == 3
    assert response.to_mapping()["request_id"] == "req-001"


def test_mcp_tool_error_serializes_to_mapping() -> None:
    error = McpToolError(
        code=ToolErrorCode.VALIDATION_ERROR,
        message="query must be a non-empty string",
        tool_name="document_retrieval",
        request_id="req-002",
        details={"field": "query"},
    )

    assert str(error) == "document_retrieval:validation_error:query must be a non-empty string"
    assert error.to_mapping() == {
        "code": "validation_error",
        "message": "query must be a non-empty string",
        "tool_name": "document_retrieval",
        "request_id": "req-002",
        "retryable": False,
        "details": {"field": "query"},
    }
