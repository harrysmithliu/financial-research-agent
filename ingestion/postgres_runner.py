from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any

from config.settings import Settings, get_settings
from ingestion.jobs import IngestionRunResult, run_seed_ingestion
from storage.postgres import (
    PostgresStorageRepository,
    connect_postgres,
    run_ingestion_storage_migrations,
)


def run_seed_ingestion_to_postgres(
    repo_root: str | Path,
    *,
    settings: Settings | None = None,
    database_url: str | None = None,
    started_at: datetime | None = None,
) -> IngestionRunResult:
    resolved_database_url = database_url or (settings or get_settings()).database_url
    connection = connect_postgres(resolved_database_url)
    try:
        run_ingestion_storage_migrations(connection)
        run_result = run_seed_ingestion(
            repo_root,
            PostgresStorageRepository(connection),
            started_at=started_at,
        )
        _call_if_available(connection, "commit")
        return run_result
    except Exception:
        _call_if_available(connection, "rollback")
        raise
    finally:
        _call_if_available(connection, "close")


def _call_if_available(target: Any, method_name: str) -> None:
    method = getattr(target, method_name, None)
    if method is not None:
        method()
