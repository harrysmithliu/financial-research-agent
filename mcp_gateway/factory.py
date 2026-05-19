from __future__ import annotations

from mcp_gateway.gateway import McpGateway
from mcp_gateway.tools.document_retrieval import (
    TOOL_NAME as DOCUMENT_RETRIEVAL_TOOL_NAME,
)
from mcp_gateway.tools.document_retrieval import handle_document_retrieval


def create_gateway() -> McpGateway:
    gateway = McpGateway()
    gateway.register_tool(DOCUMENT_RETRIEVAL_TOOL_NAME, handle_document_retrieval)
    return gateway
