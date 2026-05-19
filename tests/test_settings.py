from __future__ import annotations

from config.settings import DEFAULT_DATABASE_URL, DEFAULT_REDIS_URL, Settings


def test_settings_defaults_are_local_development_safe() -> None:
    settings = Settings()

    assert settings.app_name == "financial-research-agent"
    assert settings.environment == "local"
    assert settings.log_level == "INFO"
    assert settings.api_host == "0.0.0.0"
    assert settings.api_port == 8000
    assert settings.database_url == DEFAULT_DATABASE_URL
    assert settings.redis_url == DEFAULT_REDIS_URL
    assert settings.request_id_header == "x-request-id"
    assert settings.retrieval_embedding_dimension == 512
    assert settings.retrieval_top_k == 5


def test_settings_load_from_environment(monkeypatch) -> None:
    monkeypatch.setenv("APP_NAME", "financial-research-agent-test")
    monkeypatch.setenv("APP_ENV", "test")
    monkeypatch.setenv("LOG_LEVEL", "debug")
    monkeypatch.setenv("API_HOST", "127.0.0.1")
    monkeypatch.setenv("API_PORT", "8080")
    monkeypatch.setenv("DATABASE_URL", "postgresql://user:pass@db:5432/app")
    monkeypatch.setenv("REDIS_URL", "redis://redis:6379/1")
    monkeypatch.setenv("REQUEST_ID_HEADER", "X-Correlation-ID")
    monkeypatch.setenv("RETRIEVAL_EMBEDDING_DIMENSION", "768")
    monkeypatch.setenv("RETRIEVAL_TOP_K", "8")

    settings = Settings.from_env()

    assert settings.app_name == "financial-research-agent-test"
    assert settings.environment == "test"
    assert settings.log_level == "DEBUG"
    assert settings.api_host == "127.0.0.1"
    assert settings.api_port == 8080
    assert settings.database_url == "postgresql://user:pass@db:5432/app"
    assert settings.redis_url == "redis://redis:6379/1"
    assert settings.request_id_header == "x-correlation-id"
    assert settings.retrieval_embedding_dimension == 768
    assert settings.retrieval_top_k == 8
