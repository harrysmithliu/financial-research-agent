from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from typing import Any, Callable

from mcp_gateway.audit import AuditSink, InMemoryAuditSink, ToolAuditRecord, utc_now
from mcp_gateway.errors import McpToolError, ToolErrorCode
from mcp_gateway.hooks import (
    AllowAllPermissionChecker,
    CacheHook,
    NoopCacheHook,
    NoopRateLimiter,
    PermissionChecker,
    RateLimiter,
    ToolContext,
)
from mcp_gateway.schemas import (
    CitationChunk,
    DocumentRetrievalRequest,
    DocumentRetrievalResponse,
)
from observability.logging import get_logger
from observability.request_context import get_request_id

ToolHandler = Callable[[ToolContext, dict[str, Any]], dict[str, Any]]


@dataclass
class McpGateway:
    handlers: dict[str, ToolHandler] = field(default_factory=dict)
    permission_checker: PermissionChecker = field(default_factory=AllowAllPermissionChecker)
    rate_limiter: RateLimiter = field(default_factory=NoopRateLimiter)
    cache_hook: CacheHook = field(default_factory=NoopCacheHook)
    audit_sink: AuditSink = field(default_factory=lambda: InMemoryAuditSink(records=[]))

    def __post_init__(self) -> None:
        self.logger = get_logger(__name__)

    def register_tool(self, tool_name: str, handler: ToolHandler) -> None:
        if not tool_name.strip():
            raise ValueError("tool_name must be a non-empty string")
        self.handlers[tool_name] = handler

    def invoke_tool(self, tool_name: str, payload: dict[str, Any]) -> dict[str, Any]:
        request_id = get_request_id().strip() or "unknown-request"
        context = ToolContext(request_id=request_id, tool_name=tool_name)
        started_at = utc_now()
        serialized_payload = _stable_json(payload)
        payload_hash = hashlib.sha256(serialized_payload.encode("utf-8")).hexdigest()
        cache_key = f"{tool_name}:{payload_hash}"
        cache_hit = False
        output_count = 0
        citations_count = 0
        status = "succeeded"
        error_code: str | None = None

        try:
            self.permission_checker.check(context, payload)
            self.rate_limiter.check(context)

            cached_result = self.cache_hook.get(context, cache_key)
            if cached_result is not None:
                cache_hit = True
                output_count = len(cached_result.get("retrieved_documents", []))
                citations_count = len(cached_result.get("citations", []))
                return cached_result

            handler = self.handlers.get(tool_name)
            if handler is None:
                raise McpToolError(
                    code=ToolErrorCode.TOOL_UNAVAILABLE,
                    message=f"tool not registered: {tool_name}",
                    tool_name=tool_name,
                    request_id=context.request_id,
                )

            response = handler(context, payload)
            output_count = len(response.get("retrieved_documents", []))
            citations_count = len(response.get("citations", []))
            self.cache_hook.set(context, cache_key, response)
            return response
        except McpToolError as exc:
            status = "failed"
            error_code = exc.code.value
            self.logger.warning(
                "mcp_tool_call_failed",
                extra={
                    "request_id": context.request_id,
                    "tool_name": tool_name,
                    "error_code": exc.code.value,
                    "retryable": exc.retryable,
                },
            )
            raise
        except Exception:
            status = "failed"
            error_code = ToolErrorCode.INTERNAL_ERROR.value
            raise
        finally:
            finished_at = utc_now()
            self.audit_sink.record_tool_call(
                ToolAuditRecord(
                    request_id=context.request_id,
                    tool_name=tool_name,
                    status=status,
                    tool_input_hash=payload_hash,
                    started_at=started_at,
                    finished_at=finished_at,
                    cache_hit=cache_hit,
                    output_count=output_count,
                    citations_count=citations_count,
                    error_code=error_code,
                )
            )

    def invoke_document_retrieval(
        self,
        request: DocumentRetrievalRequest,
    ) -> DocumentRetrievalResponse:
        response_payload = self.invoke_tool("document_retrieval", request.to_mapping())
        chunks = tuple(
            CitationChunk(
                chunk_id=citation["chunk_id"],
                document_id=citation["document_id"],
                source_uri=citation["source_uri"],
                chunk_index=int(citation["chunk_index"]),
                text=citation["text"],
                metadata=dict(citation["metadata"]),
                distance=float(citation["distance"]),
            )
            for citation in response_payload.get("citations", [])
        )
        return DocumentRetrievalResponse(
            request_id=response_payload["request_id"],
            tool_name=response_payload["tool_name"],
            query=response_payload["query"],
            top_k=response_payload["top_k"],
            chunks=chunks,
            cache_hit=bool(response_payload.get("cache_hit", False)),
        )


def _stable_json(payload: dict[str, Any]) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"))
