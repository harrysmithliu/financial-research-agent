"""MCP gateway package."""

from mcp_gateway.factory import create_gateway
from mcp_gateway.gateway import McpGateway

__all__ = ["McpGateway", "create_gateway"]
