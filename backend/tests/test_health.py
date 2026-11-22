import pytest
from fastapi.testclient import TestClient

from app.db.session import check_database_connectivity, get_engine


def test_root_health_endpoint(client: TestClient) -> None:
    response = client.get("/health")
    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "ok"
    assert payload["service"] == "PulseTrace"


def test_api_v1_health_endpoint(client: TestClient) -> None:
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_application_starts() -> None:
    from app.main import app

    assert app.title == "PulseTrace"


def test_database_health_endpoint(client: TestClient) -> None:
    connected, _ = check_database_connectivity()
    if not connected:
        pytest.skip("PostgreSQL is not reachable; start Docker Compose to run this test.")

    response = client.get("/api/v1/health/database")
    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "ok"
    assert payload["database"] == "connected"


def test_database_connectivity_check() -> None:
    connected, detail = check_database_connectivity()
    if not connected:
        pytest.skip(f"PostgreSQL is not reachable: {detail}")

    assert connected is True
    assert detail == "connected"
    get_engine().dispose()