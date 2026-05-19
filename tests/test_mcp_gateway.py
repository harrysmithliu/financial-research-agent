from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from mcp_gateway.errors import McpToolError, ToolErrorCode
from mcp_gateway.factory import create_gateway
from mcp_gateway.gateway import McpGateway
from mcp_gateway.hooks import ToolContext
from observability.request_context import request_id_context


@dataclass
class RecordingPermissionChecker:
    calls: list[tuple[ToolContext, dict[str, Any]]] = field(default_factory=list)

    def check(self, context: ToolContext, payload: dict[str, Any]) -> None:
        self.calls.append((context, payload))


@dataclass
class RecordingRateLimiter:
    calls: list[ToolContext] = field(default_factory=list)

    def check(self, context: ToolContext) -> None:
        self.calls.append(context)


@dataclass
class DictCache:
    values: dict[str, dict[str, Any]] = field(default_factory=dict)
    get_calls: list[str] = field(default_factory=list)
    set_calls: list[str] = field(default_factory=list)

    def get(self, context: ToolContext, key: str) -> dict[str, Any] | None:
        del context
        self.get_calls.append(key)
        return self.values.get(key)

    def set(self, context: ToolContext, key: str, value: dict[str, Any]) -> None:
        del context
        self.set_calls.append(key)
        self.values[key] = value


def test_gateway_invokes_registered_tool_with_hooks_and_audit() -> None:
    checker = RecordingPermissionChecker()
    limiter = RecordingRateLimiter()
    cache = DictCache()
    gateway = McpGateway(
        permission_checker=checker,
        rate_limiter=limiter,
        cache_hook=cache,
    )

    gateway.register_tool(
        "document_retrieval",
        lambda context, payload: {
            "request_id": context.request_id,
            "tool_name": context.tool_name,
            "query": payload["query"],
            "top_k": payload["top_k"],
            "cache_hit": False,
            "retrieved_documents": ["doc_a"],
            "citations": [
                {
                    "chunk_id": "chunk_001",
                    "document_id": "doc_a",
                    "source_uri": "data/sample_documents/fund_a_factsheet.md",
                    "chunk_index": 0,
                    "text": "Fund A summary",
                    "metadata": {"dataset_name": "synthetic_fund_seed"},
                    "distance": 0.2,
                }
            ],
        },
    )

    token = request_id_context.set("req-gateway-001")
    try:
        result = gateway.invoke_tool(
            "document_retrieval",
            {"query": "Compare funds", "top_k": 3},
        )
    finally:
        request_id_context.reset(token)

    assert result["request_id"] == "req-gateway-001"
    assert checker.calls[0][0].request_id == "req-gateway-001"
    assert limiter.calls[0].tool_name == "document_retrieval"
    assert cache.get_calls
    assert cache.set_calls
    assert len(gateway.audit_sink.records) == 1
    assert gateway.audit_sink.records[0].status == "succeeded"


def test_gateway_returns_tool_unavailable_error_for_unregistered_tool() -> None:
    gateway = McpGateway()
    token = request_id_context.set("req-gateway-002")
    try:
        try:
            gateway.invoke_tool("missing_tool", {"query": "Q", "top_k": 1})
        except McpToolError as exc:
            assert exc.code is ToolErrorCode.TOOL_UNAVAILABLE
            assert exc.request_id == "req-gateway-002"
        else:
            raise AssertionError("Expected McpToolError")
    finally:
        request_id_context.reset(token)

    assert len(gateway.audit_sink.records) == 1
    assert gateway.audit_sink.records[0].status == "failed"
    assert gateway.audit_sink.records[0].error_code == "tool_unavailable"


def test_create_gateway_registers_document_retrieval_stub() -> None:
    gateway = create_gateway()
    token = request_id_context.set("req-gateway-003")
    try:
        try:
            gateway.invoke_tool(
                "document_retrieval",
                {"query": "Compare risk", "top_k": 2},
            )
        except McpToolError as exc:
            assert exc.code is ToolErrorCode.TOOL_UNAVAILABLE
            assert "not wired to retrieval service yet" in exc.message
        else:
            raise AssertionError("Expected McpToolError from stub")
    finally:
        request_id_context.reset(token)
