from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache


DEFAULT_DATABASE_URL = (
    "postgresql://financial_research:financial_research@localhost:5432/"
    "financial_research"
)
DEFAULT_REDIS_URL = "redis://localhost:6379/0"


def _read_env(name: str, default: str) -> str:
    value = os.getenv(name)
    if value is None or not value.strip():
        return default
    return value.strip()


@dataclass(frozen=True)
class Settings:
    app_name: str = "financial-research-agent"
    environment: str = "local"
    log_level: str = "INFO"
    database_url: str = DEFAULT_DATABASE_URL
    redis_url: str = DEFAULT_REDIS_URL
    request_id_header: str = "x-request-id"

    @classmethod
    def from_env(cls) -> Settings:
        return cls(
            app_name=_read_env("APP_NAME", cls.app_name),
            environment=_read_env("APP_ENV", cls.environment),
            log_level=_read_env("LOG_LEVEL", cls.log_level).upper(),
            database_url=_read_env("DATABASE_URL", cls.database_url),
            redis_url=_read_env("REDIS_URL", cls.redis_url),
            request_id_header=_read_env(
                "REQUEST_ID_HEADER",
                cls.request_id_header,
            ).lower(),
        )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings.from_env()
