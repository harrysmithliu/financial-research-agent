from __future__ import annotations

from dataclasses import dataclass

from fastapi.testclient import TestClient

from agents.research_workflow import ResearchWorkflow
from api.main import create_app
from config.settings import Settings
from mcp_gateway.factory import create_gateway
from retrieval.postgres import RetrievedChunk


@dataclass
class FakeRetrievalService:
    calls: list[tuple[str, int]]

    def search(self, query: str, *, top_k: int | None = None) -> tuple[RetrievedChunk, ...]:
        if top_k is None:
            raise AssertionError("top_k should be forwarded through MCP tool contract")
        self.calls.append((query, top_k))
        return (
            RetrievedChunk(
                chunk_id="chunk_doc_a_000",
                document_id="doc_a",
                chunk_index=0,
                source_uri="data/sample_documents/fund_a_factsheet.md",
                text="Fund A evidence",
                metadata={"dataset_name": "synthetic_fund_seed"},
                distance=0.08,
            ),
            RetrievedChunk(
                chunk_id="chunk_doc_b_000",
                document_id="doc_b",
                chunk_index=0,
                source_uri="data/sample_documents/fund_b_factsheet.md",
                text="Fund B evidence",
                metadata={"dataset_name": "synthetic_fund_seed"},
                distance=0.13,
            ),
        )


def test_research_api_runs_through_mcp_gateway_document_retrieval() -> None:
    retrieval_service = FakeRetrievalService(calls=[])
    gateway = create_gateway(retrieval_service=retrieval_service)
    workflow = ResearchWorkflow(gateway=gateway)
    app = create_app(Settings(environment="test"), research_workflow=workflow)

    response = TestClient(app).post(
        "/research",
        headers={"x-request-id": "req-e2e-001"},
        json={
            "question": "Compare Fund A and Fund B by expense ratio",
            "task_type": "fund_comparison",
            "top_k": 2,
        },
    )

    assert response.status_code == 200
    assert response.headers["x-request-id"] == "req-e2e-001"
    body = response.json()
    assert body["request_id"] == "req-e2e-001"
    assert body["tool_trace"][0]["tool_name"] == "document_retrieval"
    assert len(body["citations"]) == 2
    assert body["citations"][0]["chunk_id"] == "chunk_doc_a_000"
    assert body["citations"][0]["source_uri"] == "data/sample_documents/fund_a_factsheet.md"
    assert retrieval_service.calls == [("Compare Fund A and Fund B by expense ratio", 2)]

    assert len(gateway.audit_sink.records) == 1
    audit_record = gateway.audit_sink.records[0]
    assert audit_record.request_id == "req-e2e-001"
    assert audit_record.tool_name == "document_retrieval"
    assert audit_record.status == "succeeded"
    assert audit_record.output_count == 2
    assert audit_record.citations_count == 2
