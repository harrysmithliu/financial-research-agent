from __future__ import annotations

from dataclasses import dataclass

from mcp_gateway.errors import McpToolError, ToolErrorCode
from mcp_gateway.hooks import ToolContext
from mcp_gateway.tools.document_retrieval import build_document_retrieval_handler
from retrieval.postgres import RetrievedChunk


@dataclass
class FakeRetrievalService:
    calls: list[tuple[str, int]]
    chunks: tuple[RetrievedChunk, ...]
    should_fail: bool = False

    def search(self, query: str, *, top_k: int | None = None) -> tuple[RetrievedChunk, ...]:
        if top_k is None:
            raise AssertionError("top_k should be provided by tool handler")
        self.calls.append((query, top_k))
        if self.should_fail:
            raise RuntimeError("backend unavailable")
        return self.chunks


def test_document_retrieval_handler_returns_retrieval_payload() -> None:
    service = FakeRetrievalService(
        calls=[],
        chunks=(
            RetrievedChunk(
                chunk_id="chunk_001",
                document_id="doc_a",
                chunk_index=0,
                source_uri="data/sample_documents/fund_a_factsheet.md",
                text="Fund A overview",
                metadata={"dataset_name": "synthetic_fund_seed"},
                distance=0.11,
            ),
            RetrievedChunk(
                chunk_id="chunk_002",
                document_id="doc_b",
                chunk_index=0,
                source_uri="data/sample_documents/fund_b_factsheet.md",
                text="Fund B overview",
                metadata={"dataset_name": "synthetic_fund_seed"},
                distance=0.17,
            ),
        ),
    )
    handler = build_document_retrieval_handler(service)
    context = ToolContext(request_id="req-tool-001", tool_name="document_retrieval")

    payload = handler(context, {"query": "Compare Fund A and Fund B", "top_k": 2})

    assert service.calls == [("Compare Fund A and Fund B", 2)]
    assert payload["request_id"] == "req-tool-001"
    assert payload["retrieved_documents"] == ["doc_a", "doc_b"]
    assert len(payload["citations"]) == 2


def test_document_retrieval_handler_returns_validation_error() -> None:
    service = FakeRetrievalService(calls=[], chunks=())
    handler = build_document_retrieval_handler(service)
    context = ToolContext(request_id="req-tool-002", tool_name="document_retrieval")

    try:
        handler(context, {"query": "", "top_k": 2})
    except McpToolError as exc:
        assert exc.code is ToolErrorCode.VALIDATION_ERROR
        assert exc.request_id == "req-tool-002"
    else:
        raise AssertionError("Expected validation error")


def test_document_retrieval_handler_maps_backend_failure() -> None:
    service = FakeRetrievalService(calls=[], chunks=(), should_fail=True)
    handler = build_document_retrieval_handler(service)
    context = ToolContext(request_id="req-tool-003", tool_name="document_retrieval")

    try:
        handler(context, {"query": "Compare risk", "top_k": 1})
    except McpToolError as exc:
        assert exc.code is ToolErrorCode.TOOL_UNAVAILABLE
        assert exc.retryable is True
    else:
        raise AssertionError("Expected backend failure mapping")
