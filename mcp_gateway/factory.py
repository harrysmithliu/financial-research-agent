from __future__ import annotations

from mcp_gateway.gateway import McpGateway
from mcp_gateway.tools.document_retrieval import (
    RetrievalSearchService,
    TOOL_NAME as DOCUMENT_RETRIEVAL_TOOL_NAME,
)
from mcp_gateway.tools.document_retrieval import (
    build_document_retrieval_handler,
    handle_document_retrieval_unavailable,
)


def create_gateway(retrieval_service: RetrievalSearchService | None = None) -> McpGateway:
    gateway = McpGateway()
    if retrieval_service is None:
        handler = handle_document_retrieval_unavailable
    else:
        handler = build_document_retrieval_handler(retrieval_service)
    gateway.register_tool(DOCUMENT_RETRIEVAL_TOOL_NAME, handler)
    return gateway
