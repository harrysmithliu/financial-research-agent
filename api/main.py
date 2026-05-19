from __future__ import annotations

from fastapi import FastAPI

from agents.research_workflow import ResearchWorkflow, ResearchWorkflowRunner
from api.middleware import RequestIdMiddleware
from api.routes.health import router as health_router
from api.routes.research import router as research_router
from config.settings import Settings, get_settings
from mcp_gateway.factory import create_gateway
from observability.logging import configure_logging, get_logger


def create_app(
    settings: Settings | None = None,
    research_workflow: ResearchWorkflowRunner | None = None,
) -> FastAPI:
    resolved_settings = settings or get_settings()
    configure_logging(resolved_settings)
    resolved_research_workflow = research_workflow or ResearchWorkflow(
        gateway=create_gateway()
    )

    app = FastAPI(
        title="Financial Research Agent",
        version="0.1.0",
    )
    app.state.settings = resolved_settings
    app.state.research_workflow = resolved_research_workflow
    app.add_middleware(
        RequestIdMiddleware,
        request_id_header=resolved_settings.request_id_header,
    )
    app.include_router(health_router)
    app.include_router(research_router)

    logger = get_logger(__name__)
    logger.info(
        "api_app_created",
        extra={
            "service": resolved_settings.app_name,
            "environment": resolved_settings.environment,
        },
    )

    return app


app = create_app()
