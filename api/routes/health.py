from __future__ import annotations

from fastapi import APIRouter, Request

from observability.request_context import get_request_id

router = APIRouter(tags=["health"])


@router.get("/health")
def health(request: Request) -> dict[str, str]:
    settings = request.app.state.settings
    return {
        "status": "ok",
        "service": settings.app_name,
        "environment": settings.environment,
        "request_id": get_request_id(),
    }
