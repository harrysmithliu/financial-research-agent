from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any


class ToolErrorCode(StrEnum):
    VALIDATION_ERROR = "validation_error"
    PERMISSION_DENIED = "permission_denied"
    RATE_LIMITED = "rate_limited"
    TOOL_UNAVAILABLE = "tool_unavailable"
    INTERNAL_ERROR = "internal_error"


@dataclass(frozen=True)
class McpToolError(Exception):
    code: ToolErrorCode
    message: str
    tool_name: str
    request_id: str
    retryable: bool = False
    details: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.message.strip():
            raise ValueError("message must be a non-empty string")
        if not self.tool_name.strip():
            raise ValueError("tool_name must be a non-empty string")
        if not self.request_id.strip():
            raise ValueError("request_id must be a non-empty string")

    def __str__(self) -> str:
        return f"{self.tool_name}:{self.code}:{self.message}"

    def to_mapping(self) -> dict[str, Any]:
        return {
            "code": self.code.value,
            "message": self.message,
            "tool_name": self.tool_name,
            "request_id": self.request_id,
            "retryable": self.retryable,
            "details": dict(self.details),
        }
