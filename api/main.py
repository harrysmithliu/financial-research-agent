from __future__ import annotations

from fastapi import FastAPI

from api.middleware import RequestIdMiddleware
from api.routes.health import router as health_router
from config.settings import Settings, get_settings
from observability.logging import configure_logging, get_logger


def create_app(settings: Settings | None = None) -> FastAPI:
    resolved_settings = settings or get_settings()
    configure_logging(resolved_settings)

    app = FastAPI(
        title="Financial Research Agent",
        version="0.1.0",
    )
    app.state.settings = resolved_settings
    app.add_middleware(
        RequestIdMiddleware,
        request_id_header=resolved_settings.request_id_header,
    )
    app.include_router(health_router)

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
