from __future__ import annotations

from typing import Any, Callable

from mcp_gateway.errors import McpToolError, ToolErrorCode
from mcp_gateway.hooks import ToolContext
from mcp_gateway.schemas import DocumentRetrievalRequest
from retrieval.service import RetrievalService

TOOL_NAME = "document_retrieval"


def handle_document_retrieval_unavailable(
    context: ToolContext,
    payload: dict[str, Any],
) -> dict[str, Any]:
    _parse_request_payload(payload, context)
    raise McpToolError(
        code=ToolErrorCode.TOOL_UNAVAILABLE,
        message="document_retrieval is not wired to retrieval service yet",
        tool_name=TOOL_NAME,
        request_id=context.request_id,
    )


def build_document_retrieval_handler(
    retrieval_service: RetrievalService,
) -> Callable[[ToolContext, dict[str, Any]], dict[str, Any]]:
    def handle_document_retrieval(
        context: ToolContext,
        payload: dict[str, Any],
    ) -> dict[str, Any]:
        request = _parse_request_payload(payload, context)
        try:
            chunks = retrieval_service.search(request.query, top_k=request.top_k)
        except ValueError as exc:
            raise McpToolError(
                code=ToolErrorCode.VALIDATION_ERROR,
                message=str(exc),
                tool_name=TOOL_NAME,
                request_id=context.request_id,
                details={"query": request.query, "top_k": request.top_k},
            ) from exc
        except Exception as exc:
            raise McpToolError(
                code=ToolErrorCode.TOOL_UNAVAILABLE,
                message="document_retrieval retrieval backend unavailable",
                tool_name=TOOL_NAME,
                request_id=context.request_id,
                retryable=True,
            ) from exc

        citations = [
            {
                "chunk_id": chunk.chunk_id,
                "document_id": chunk.document_id,
                "source_uri": chunk.source_uri,
                "chunk_index": chunk.chunk_index,
                "text": chunk.text,
                "metadata": dict(chunk.metadata),
                "distance": float(chunk.distance),
            }
            for chunk in chunks
        ]
        retrieved_documents = _ordered_document_ids(citations)
        return {
            "request_id": context.request_id,
            "tool_name": TOOL_NAME,
            "query": request.query,
            "top_k": request.top_k,
            "cache_hit": False,
            "retrieved_documents": retrieved_documents,
            "citations": citations,
        }

    return handle_document_retrieval


def _parse_request_payload(
    payload: dict[str, Any],
    context: ToolContext,
) -> DocumentRetrievalRequest:
    query = payload.get("query", "")
    top_k_raw = payload.get("top_k", 5)
    try:
        top_k = int(top_k_raw)
    except (TypeError, ValueError) as exc:
        raise McpToolError(
            code=ToolErrorCode.VALIDATION_ERROR,
            message="top_k must be an integer",
            tool_name=TOOL_NAME,
            request_id=context.request_id,
            details={"top_k": top_k_raw},
        ) from exc

    try:
        return DocumentRetrievalRequest(
            query=str(query),
            top_k=top_k,
        )
    except ValueError as exc:
        raise McpToolError(
            code=ToolErrorCode.VALIDATION_ERROR,
            message=str(exc),
            tool_name=TOOL_NAME,
            request_id=context.request_id,
            details={"query": query, "top_k": top_k},
        ) from exc


def _ordered_document_ids(citations: list[dict[str, Any]]) -> list[str]:
    document_ids: list[str] = []
    seen: set[str] = set()
    for citation in citations:
        document_id = str(citation["document_id"])
        if document_id in seen:
            continue
        seen.add(document_id)
        document_ids.append(document_id)
    return document_ids
