from __future__ import annotations

from typing import Any

from mcp_gateway.errors import McpToolError, ToolErrorCode
from mcp_gateway.hooks import ToolContext
from mcp_gateway.schemas import DocumentRetrievalRequest

TOOL_NAME = "document_retrieval"


def handle_document_retrieval(
    context: ToolContext,
    payload: dict[str, Any],
) -> dict[str, Any]:
    request = DocumentRetrievalRequest(
        query=str(payload.get("query", "")),
        top_k=int(payload.get("top_k", 5)),
    )
    del request
    raise McpToolError(
        code=ToolErrorCode.TOOL_UNAVAILABLE,
        message="document_retrieval is not wired to retrieval service yet",
        tool_name=TOOL_NAME,
        request_id=context.request_id,
    )
