from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pytest

from config.settings import Settings
from ingestion.postgres_runner import run_seed_ingestion_to_postgres


REPO_ROOT = Path(__file__).resolve().parents[1]
NOW = datetime(2026, 5, 13, tzinfo=UTC)


@dataclass
class FakePostgresConnection:
    events: list[str] = field(default_factory=list)
    calls: list[tuple[str, tuple[Any, ...]]] = field(default_factory=list)

    def execute(self, query: str, params: tuple[Any, ...]) -> None:
        self.events.append("execute")
        self.calls.append((query, params))

    def commit(self) -> None:
        self.events.append("commit")

    def rollback(self) -> None:
        self.events.append("rollback")

    def close(self) -> None:
        self.events.append("close")


def test_run_seed_ingestion_to_postgres_runs_migrations_before_writes(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    connection = FakePostgresConnection()
    database_urls: list[str] = []

    def fake_connect_postgres(database_url: str) -> FakePostgresConnection:
        database_urls.append(database_url)
        return connection

    monkeypatch.setattr(
        "ingestion.postgres_runner.connect_postgres",
        fake_connect_postgres,
    )

    run_result = run_seed_ingestion_to_postgres(
        REPO_ROOT,
        settings=Settings(database_url="postgresql://user:pass@db:5432/app"),
        started_at=NOW,
    )

    assert database_urls == ["postgresql://user:pass@db:5432/app"]
    assert run_result.job_record.status == "completed"
    assert run_result.job_record.started_at == NOW
    assert "CREATE TABLE IF NOT EXISTS ingestion_job_records" in connection.calls[0][0]
    assert any("INSERT INTO document_chunks" in call[0] for call in connection.calls)
    assert connection.events[-2:] == ["commit", "close"]
    assert "rollback" not in connection.events


def test_run_seed_ingestion_to_postgres_allows_database_url_override(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    connection = FakePostgresConnection()
    database_urls: list[str] = []

    def fake_connect_postgres(database_url: str) -> FakePostgresConnection:
        database_urls.append(database_url)
        return connection

    monkeypatch.setattr(
        "ingestion.postgres_runner.connect_postgres",
        fake_connect_postgres,
    )

    run_seed_ingestion_to_postgres(
        REPO_ROOT,
        settings=Settings(database_url="postgresql://settings/db"),
        database_url="postgresql://override/db",
        started_at=NOW,
    )

    assert database_urls == ["postgresql://override/db"]


def test_run_seed_ingestion_to_postgres_rolls_back_and_closes_on_failure(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    connection = FakePostgresConnection()

    monkeypatch.setattr(
        "ingestion.postgres_runner.connect_postgres",
        lambda _: connection,
    )

    with pytest.raises(FileNotFoundError):
        run_seed_ingestion_to_postgres(tmp_path, database_url="postgresql://db")

    assert connection.events[-2:] == ["rollback", "close"]
    assert "commit" not in connection.events
    assert any(
        "INSERT INTO ingestion_job_records" in call[0]
        for call in connection.calls
    )
