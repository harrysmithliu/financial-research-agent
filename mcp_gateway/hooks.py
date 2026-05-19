from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol


@dataclass(frozen=True)
class ToolContext:
    request_id: str
    tool_name: str


class PermissionChecker(Protocol):
    def check(self, context: ToolContext, payload: dict[str, Any]) -> None:
        ...


class RateLimiter(Protocol):
    def check(self, context: ToolContext) -> None:
        ...


class CacheHook(Protocol):
    def get(self, context: ToolContext, key: str) -> dict[str, Any] | None:
        ...

    def set(self, context: ToolContext, key: str, value: dict[str, Any]) -> None:
        ...


class AllowAllPermissionChecker:
    def check(self, context: ToolContext, payload: dict[str, Any]) -> None:
        del context, payload


class NoopRateLimiter:
    def check(self, context: ToolContext) -> None:
        del context


class NoopCacheHook:
    def get(self, context: ToolContext, key: str) -> dict[str, Any] | None:
        del context, key
        return None

    def set(self, context: ToolContext, key: str, value: dict[str, Any]) -> None:
        del context, key, value
