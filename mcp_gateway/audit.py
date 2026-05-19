from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Protocol


@dataclass(frozen=True)
class ToolAuditRecord:
    request_id: str
    tool_name: str
    status: str
    tool_input_hash: str
    started_at: datetime
    finished_at: datetime
    cache_hit: bool
    output_count: int
    citations_count: int
    error_code: str | None = None

    def __post_init__(self) -> None:
        if not self.request_id.strip():
            raise ValueError("request_id must be a non-empty string")
        if not self.tool_name.strip():
            raise ValueError("tool_name must be a non-empty string")
        if self.status not in {"succeeded", "failed"}:
            raise ValueError("status must be succeeded or failed")
        if not self.tool_input_hash.strip():
            raise ValueError("tool_input_hash must be a non-empty string")
        if self.started_at.tzinfo is None or self.finished_at.tzinfo is None:
            raise ValueError("started_at and finished_at must be timezone-aware")

    @property
    def latency_ms(self) -> int:
        delta = self.finished_at - self.started_at
        return max(0, int(delta.total_seconds() * 1000))


class AuditSink(Protocol):
    def record_tool_call(self, record: ToolAuditRecord) -> None:
        ...


@dataclass
class InMemoryAuditSink:
    records: list[ToolAuditRecord]

    def record_tool_call(self, record: ToolAuditRecord) -> None:
        self.records.append(record)


def utc_now() -> datetime:
    return datetime.now(timezone.utc)
