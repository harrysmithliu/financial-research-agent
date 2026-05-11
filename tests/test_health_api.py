from __future__ import annotations

from fastapi.testclient import TestClient

from api.main import create_app
from config.settings import Settings


def test_health_endpoint_returns_service_status_and_request_id() -> None:
    app = create_app(
        Settings(
            app_name="financial-research-agent-test",
            environment="test",
        )
    )

    response = TestClient(app).get(
        "/health",
        headers={"x-request-id": "req-test-001"},
    )

    assert response.status_code == 200
    assert response.headers["x-request-id"] == "req-test-001"
    assert response.json() == {
        "status": "ok",
        "service": "financial-research-agent-test",
        "environment": "test",
        "request_id": "req-test-001",
    }


def test_health_endpoint_generates_request_id_when_missing() -> None:
    app = create_app(Settings(environment="test"))

    response = TestClient(app).get("/health")

    assert response.status_code == 200
    assert response.headers["x-request-id"]
    assert response.json()["request_id"] == response.headers["x-request-id"]
