import io
import uuid
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.core.config import get_settings
from app.modules.logs.fingerprint import build_fingerprint
from app.modules.logs.normalizer import normalize_level, parse_timestamp

FIXTURES = Path(__file__).parent / "fixtures"


def _unique_email() -> str:
    return f"log-{uuid.uuid4().hex[:10]}@example.com"


def _register_and_login(client: TestClient) -> dict[str, str]:
    email = _unique_email()
    password = "SecurePass1"
    client.post(
        "/api/v1/auth/register",
        json={"full_name": "Log Tester", "email": email, "password": password},
    )
    login = client.post("/api/v1/auth/login", json={"email": email, "password": password})
    token = login.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def _create_project(client: TestClient, headers: dict[str, str]) -> str:
    response = client.post(
        "/api/v1/projects",
        json={"name": f"Logs-{uuid.uuid4().hex[:6]}", "environment": "staging"},
        headers=headers,
    )
    assert response.status_code == 201
    return response.json()["id"]


def _upload(client: TestClient, headers: dict[str, str], project_id: str, name: str, content: bytes):
    return client.post(
        f"/api/v1/projects/{project_id}/logs/upload",
        headers=headers,
        files={"file": (name, io.BytesIO(content), "application/octet-stream")},
    )


@pytest.fixture
def auth_project(client: TestClient) -> tuple[dict[str, str], str]:
    headers = _register_and_login(client)
    project_id = _create_project(client, headers)
    return headers, project_id


def test_csv_upload_and_search(auth_project, client: TestClient) -> None:
    headers, project_id = auth_project
    content = (FIXTURES / "sample.csv").read_bytes()
    upload = _upload(client, headers, project_id, "sample.csv", content)
    assert upload.status_code == 201
    body = upload.json()
    assert body["processed_records"] >= 2
    assert body["failed_records"] >= 1
    assert body["status"] in {"partially_completed", "completed"}

    search = client.get(f"/api/v1/projects/{project_id}/logs?level=ERROR", headers=headers)
    assert search.status_code == 200
    items = search.json()["items"]
    assert any("timeout" in item["message"].lower() for item in items)


def test_json_upload(auth_project, client: TestClient) -> None:
    headers, project_id = auth_project
    upload = _upload(client, headers, project_id, "sample.json", (FIXTURES / "sample.json").read_bytes())
    assert upload.status_code == 201
    assert upload.json()["processed_records"] == 2


def test_jsonl_upload(auth_project, client: TestClient) -> None:
    headers, project_id = auth_project
    upload = _upload(client, headers, project_id, "sample.jsonl", (FIXTURES / "sample.jsonl").read_bytes())
    assert upload.status_code == 201
    assert upload.json()["processed_records"] == 2
    assert upload.json()["failed_records"] >= 1


def test_txt_upload(auth_project, client: TestClient) -> None:
    headers, project_id = auth_project
    upload = _upload(client, headers, project_id, "sample.txt", (FIXTURES / "sample.txt").read_bytes())
    assert upload.status_code == 201
    assert upload.json()["processed_records"] >= 2


def test_invalid_extension(auth_project, client: TestClient) -> None:
    headers, project_id = auth_project
    upload = _upload(client, headers, project_id, "sample.exe", b"data")
    assert upload.status_code == 400


def test_empty_file(auth_project, client: TestClient) -> None:
    headers, project_id = auth_project
    upload = _upload(client, headers, project_id, "empty.jsonl", b"")
    assert upload.status_code == 400


def test_oversized_file(auth_project, client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    headers, project_id = auth_project
    settings = get_settings()
    monkeypatch.setenv("LOG_UPLOAD_MAX_BYTES", "32")
    get_settings.cache_clear()
    payload = b"x" * 64
    upload = _upload(client, headers, project_id, "big.jsonl", payload)
    get_settings.cache_clear()
    assert upload.status_code == 413


def test_service_association(auth_project, client: TestClient) -> None:
    headers, project_id = auth_project
    create_service = client.post(
        f"/api/v1/projects/{project_id}/services",
        headers=headers,
        json={"name": "payments-api", "service_type": "api", "environment": "staging"},
    )
    assert create_service.status_code == 201
    service_id = create_service.json()["id"]

    csv = b"timestamp,level,service,message\n2024-06-01T12:00:00Z,INFO,payments-api,Matched service\n"
    upload = _upload(client, headers, project_id, "svc.csv", csv)
    assert upload.status_code == 201

    search = client.get(
        f"/api/v1/projects/{project_id}/logs?service_id={service_id}",
        headers=headers,
    )
    assert search.status_code == 200
    assert search.json()["total"] >= 1


def test_unknown_service_metadata(auth_project, client: TestClient) -> None:
    headers, project_id = auth_project
    csv = b"timestamp,level,service,message\n2024-06-01T12:00:00Z,INFO,unknown-svc,Something happened\n"
    _upload(client, headers, project_id, "unknown.csv", csv)
    search = client.get(f"/api/v1/projects/{project_id}/logs?keyword=Something", headers=headers)
    item = search.json()["items"][0]
    assert item["service_id"] is None
    assert item["metadata"].get("original_service_name") == "unknown-svc"


def test_fingerprint_consistency() -> None:
    first = build_fingerprint(level="ERROR", message="Timeout", service_name="api", trace_id="t1")
    second = build_fingerprint(level="ERROR", message="Timeout", service_name="api", trace_id="t1")
    assert first == second


def test_timestamp_and_level_normalization() -> None:
    ts = parse_timestamp("2024-01-15T10:00:00Z")
    assert ts is not None
    assert normalize_level("warn") == "WARNING"


def test_batch_list_and_detail(auth_project, client: TestClient) -> None:
    headers, project_id = auth_project
    _upload(client, headers, project_id, "sample.json", (FIXTURES / "sample.json").read_bytes())
    listing = client.get(f"/api/v1/projects/{project_id}/logs/batches", headers=headers)
    assert listing.status_code == 200
    batch_id = listing.json()["items"][0]["id"]
    detail = client.get(f"/api/v1/projects/{project_id}/logs/batches/{batch_id}", headers=headers)
    assert detail.status_code == 200


def test_project_isolation(client: TestClient) -> None:
    headers_a = _register_and_login(client)
    project_a = _create_project(client, headers_a)
    headers_b = _register_and_login(client)
    project_b = _create_project(client, headers_b)
    _upload(client, headers_a, project_a, "sample.json", (FIXTURES / "sample.json").read_bytes())
    search_b = client.get(f"/api/v1/projects/{project_b}/logs", headers=headers_b)
    assert search_b.json()["total"] == 0
    search_cross = client.get(f"/api/v1/projects/{project_b}/logs", headers=headers_a)
    assert search_cross.status_code == 404

def test_unauthorized_upload(client: TestClient, auth_project) -> None:
    _, project_id = auth_project
    client.cookies.clear()
    upload = _upload(client, {}, project_id, "sample.json", b"{}")
    assert upload.status_code == 401