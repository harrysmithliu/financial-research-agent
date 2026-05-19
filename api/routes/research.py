from __future__ import annotations

from enum import StrEnum
from typing import Any

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, ConfigDict, Field

from agents.research_workflow import (
    ResearchWorkflowRunner,
    ResearchWorkflowRequest,
    ResearchWorkflowResult,
)
from mcp_gateway.errors import McpToolError, ToolErrorCode

router = APIRouter(tags=["research"])


class ResearchTaskType(StrEnum):
    FUND_COMPARISON = "fund_comparison"
    DUE_DILIGENCE_BRIEF = "due_diligence_brief"
    FINANCIAL_QA = "financial_qa"
    PLATFORM_ISSUE_RESEARCH = "platform_issue_research"


class ResearchRequestBody(BaseModel):
    model_config = ConfigDict(extra="forbid")

    question: str = Field(min_length=1)
    task_type: ResearchTaskType
    top_k: int | None = Field(default=None, ge=1, le=50)


class ResearchResponseBody(BaseModel):
    model_config = ConfigDict(extra="forbid")

    run_id: str
    request_id: str
    task_type: str
    question: str
    summary: str
    citations: list[dict[str, Any]]
    tool_trace: list[dict[str, Any]]
    status: str = "completed"


@router.post("/research", response_model=ResearchResponseBody)
def run_research(request: Request, body: ResearchRequestBody) -> ResearchResponseBody:
    workflow: ResearchWorkflowRunner = request.app.state.research_workflow
    settings = request.app.state.settings
    top_k = settings.retrieval_top_k if body.top_k is None else body.top_k

    workflow_request = ResearchWorkflowRequest(
        question=body.question.strip(),
        task_type=body.task_type.value,
        top_k=top_k,
    )

    try:
        result = workflow.run(workflow_request)
    except McpToolError as exc:
        status_code = _tool_error_status_code(exc.code)
        raise HTTPException(
            status_code=status_code,
            detail={
                "error": exc.to_mapping(),
            },
        ) from exc
    return _to_response_model(result)


def _to_response_model(result: ResearchWorkflowResult) -> ResearchResponseBody:
    return ResearchResponseBody(
        run_id=result.run_id,
        request_id=result.request_id,
        task_type=result.task_type,
        question=result.question,
        summary=result.summary,
        citations=list(result.citations),
        tool_trace=list(result.tool_trace),
    )


def _tool_error_status_code(code: ToolErrorCode) -> int:
    if code is ToolErrorCode.VALIDATION_ERROR:
        return 422
    if code is ToolErrorCode.PERMISSION_DENIED:
        return 403
    if code is ToolErrorCode.RATE_LIMITED:
        return 429
    if code is ToolErrorCode.TOOL_UNAVAILABLE:
        return 503
    return 500
