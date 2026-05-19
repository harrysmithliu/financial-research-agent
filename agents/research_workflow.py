from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal, Protocol
from uuid import uuid4

from mcp_gateway.schemas import DocumentRetrievalRequest, DocumentRetrievalResponse
from observability.request_context import get_request_id

TaskType = Literal[
    "fund_comparison",
    "due_diligence_brief",
    "financial_qa",
    "platform_issue_research",
]


class DocumentRetrievalGateway(Protocol):
    def invoke_document_retrieval(
        self,
        request: DocumentRetrievalRequest,
        ) -> DocumentRetrievalResponse:
        ...


class ResearchWorkflowRunner(Protocol):
    def run(self, request: ResearchWorkflowRequest) -> ResearchWorkflowResult:
        ...


@dataclass(frozen=True)
class ResearchWorkflowRequest:
    question: str
    task_type: TaskType
    top_k: int = 5

    def __post_init__(self) -> None:
        if not self.question.strip():
            raise ValueError("question must be a non-empty string")
        if self.top_k <= 0:
            raise ValueError("top_k must be a positive integer")


@dataclass(frozen=True)
class ResearchWorkflowResult:
    run_id: str
    request_id: str
    task_type: TaskType
    question: str
    summary: str
    citations: tuple[dict[str, Any], ...]
    tool_trace: tuple[dict[str, Any], ...]


@dataclass(frozen=True)
class ResearchWorkflow:
    gateway: DocumentRetrievalGateway

    def run(self, request: ResearchWorkflowRequest) -> ResearchWorkflowResult:
        retrieval_request = DocumentRetrievalRequest(
            query=request.question,
            top_k=request.top_k,
        )
        retrieval_response = self.gateway.invoke_document_retrieval(retrieval_request)
        citations = retrieval_response.citations
        summary = _build_summary(request.question, citations)
        return ResearchWorkflowResult(
            run_id=f"run_{uuid4().hex[:12]}",
            request_id=get_request_id().strip() or retrieval_response.request_id,
            task_type=request.task_type,
            question=request.question,
            summary=summary,
            citations=citations,
            tool_trace=(
                {
                    "tool_name": retrieval_response.tool_name,
                    "query": retrieval_response.query,
                    "top_k": retrieval_response.top_k,
                    "citation_count": len(retrieval_response.citations),
                    "cache_hit": retrieval_response.cache_hit,
                },
            ),
        )


def _build_summary(question: str, citations: tuple[dict[str, Any], ...]) -> str:
    if not citations:
        return (
            "No supporting evidence was retrieved for the question. "
            "Human review is required before any conclusion."
        )
    top_source_uri = str(citations[0]["source_uri"])
    return (
        f"Retrieved {len(citations)} evidence chunks for: {question}. "
        f"Top evidence source: {top_source_uri}."
    )
