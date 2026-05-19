from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from fastapi.testclient import TestClient

from agents.research_workflow import (
    ResearchWorkflowRequest,
    ResearchWorkflowResult,
)
from api.main import create_app
from config.settings import Settings
from mcp_gateway.errors import McpToolError, ToolErrorCode
from observability.request_context import get_request_id


@dataclass
class FakeResearchWorkflow:
    should_fail: bool = False
    calls: list[ResearchWorkflowRequest] | None = None

    def run(self, request: ResearchWorkflowRequest) -> ResearchWorkflowResult:
        if self.calls is not None:
            self.calls.append(request)
        if self.should_fail:
            raise McpToolError(
                code=ToolErrorCode.TOOL_UNAVAILABLE,
                message="retrieval backend unavailable",
                tool_name="document_retrieval",
                request_id=get_request_id(),
                retryable=True,
            )
        return ResearchWorkflowResult(
            run_id="run_test_001",
            request_id=get_request_id(),
            task_type=request.task_type,
            question=request.question,
            summary="Retrieved 1 evidence chunk for the question.",
            citations=(
                {
                    "chunk_id": "chunk_001",
                    "document_id": "doc_a",
                    "source_uri": "data/sample_documents/fund_a_factsheet.md",
                    "chunk_index": 0,
                    "text": "Fund A overview",
                    "metadata": {"dataset_name": "synthetic_fund_seed"},
                    "distance": 0.18,
                },
            ),
            tool_trace=(
                {
                    "tool_name": "document_retrieval",
                    "query": request.question,
                    "top_k": request.top_k,
                    "citation_count": 1,
                    "cache_hit": False,
                },
            ),
        )


def test_research_endpoint_returns_workflow_result() -> None:
    workflow = FakeResearchWorkflow(calls=[])
    app = create_app(
        Settings(environment="test", retrieval_top_k=7),
        research_workflow=workflow,
    )

    response = TestClient(app).post(
        "/research",
        headers={"x-request-id": "req-api-001"},
        json={
            "question": "Compare Fund A and Fund B",
            "task_type": "fund_comparison",
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert response.headers["x-request-id"] == "req-api-001"
    assert body["request_id"] == "req-api-001"
    assert body["task_type"] == "fund_comparison"
    assert body["status"] == "completed"
    assert workflow.calls is not None
    assert workflow.calls[0].top_k == 7


def test_research_endpoint_maps_tool_error_to_http_error() -> None:
    app = create_app(
        Settings(environment="test"),
        research_workflow=FakeResearchWorkflow(should_fail=True),
    )

    response = TestClient(app).post(
        "/research",
        headers={"x-request-id": "req-api-002"},
        json={
            "question": "Compare risk",
            "task_type": "financial_qa",
            "top_k": 3,
        },
    )

    assert response.status_code == 503
    detail = response.json()["detail"]
    assert detail["error"]["code"] == "tool_unavailable"
    assert detail["error"]["request_id"] == "req-api-002"


def test_research_endpoint_validates_payload() -> None:
    app = create_app(
        Settings(environment="test"),
        research_workflow=FakeResearchWorkflow(),
    )

    response = TestClient(app).post(
        "/research",
        json={
            "question": "Compare fees",
            "task_type": "fund_comparison",
            "top_k": 0,
            "extra_field": "not_allowed",
        },
    )

    assert response.status_code == 422
    detail = response.json()["detail"]
    detail_text = str(detail)
    assert "top_k" in detail_text
    assert "extra_field" in detail_text
