from __future__ import annotations

from dataclasses import dataclass

from agents.research_workflow import ResearchWorkflow, ResearchWorkflowRequest
from mcp_gateway.schemas import (
    CitationChunk,
    DocumentRetrievalRequest,
    DocumentRetrievalResponse,
)
from observability.request_context import request_id_context


@dataclass
class FakeGateway:
    calls: list[DocumentRetrievalRequest]

    def invoke_document_retrieval(
        self,
        request: DocumentRetrievalRequest,
    ) -> DocumentRetrievalResponse:
        self.calls.append(request)
        return DocumentRetrievalResponse(
            request_id="req-workflow-gateway-001",
            tool_name="document_retrieval",
            query=request.query,
            top_k=request.top_k,
            chunks=(
                CitationChunk(
                    chunk_id="chunk_001",
                    document_id="doc_fund_a",
                    source_uri="data/sample_documents/fund_a_factsheet.md",
                    chunk_index=0,
                    text="Fund A overview",
                    metadata={"dataset_name": "synthetic_fund_seed"},
                    distance=0.12,
                ),
            ),
            cache_hit=False,
        )


def test_research_workflow_uses_gateway_document_retrieval_tool() -> None:
    gateway = FakeGateway(calls=[])
    workflow = ResearchWorkflow(gateway=gateway)
    token = request_id_context.set("req-workflow-001")
    try:
        result = workflow.run(
            ResearchWorkflowRequest(
                question="Compare Fund A and Fund B by risk",
                task_type="fund_comparison",
                top_k=2,
            )
        )
    finally:
        request_id_context.reset(token)

    assert result.request_id == "req-workflow-001"
    assert result.task_type == "fund_comparison"
    assert len(gateway.calls) == 1
    assert gateway.calls[0].query == "Compare Fund A and Fund B by risk"
    assert result.tool_trace[0]["tool_name"] == "document_retrieval"
    assert "Top evidence source" in result.summary


def test_research_workflow_request_rejects_empty_question() -> None:
    try:
        ResearchWorkflowRequest(
            question="",
            task_type="financial_qa",
            top_k=2,
        )
    except ValueError as exc:
        assert str(exc) == "question must be a non-empty string"
    else:
        raise AssertionError("Expected ValueError for empty question")
