import uuid

from fastapi.testclient import TestClient


def _unique_email() -> str:
    return f"proj-{uuid.uuid4().hex[:12]}@example.com"


def _auth_headers(client: TestClient) -> dict[str, str]:
    email = _unique_email()
    password = "SecurePass1"
    client.post(
        "/api/v1/auth/register",
        json={"full_name": "Owner", "email": email, "password": password},
    )
    login = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": password},
    )
    token = login.json()["access_token"]
    return {"Authorization": f"Bearer {token}", "X-Test-User": email}


def test_project_create_list_update_delete(client: TestClient) -> None:
    headers = _auth_headers(client)
    create = client.post(
        "/api/v1/projects",
        json={
            "name": "Payments Core",
            "description": "Primary payment platform",
            "environment": "staging",
        },
        headers=headers,
    )
    assert create.status_code == 201
    project = create.json()
    project_id = project["id"]
    assert project["name"] == "Payments Core"

    listing = client.get("/api/v1/projects", headers=headers)
    assert listing.status_code == 200
    body = listing.json()
    assert body["total"] >= 1
    assert any(item["id"] == project_id for item in body["items"])

    detail = client.get(f"/api/v1/projects/{project_id}", headers=headers)
    assert detail.status_code == 200

    updated = client.patch(
        f"/api/v1/projects/{project_id}",
        json={"name": "Payments Core v2"},
        headers=headers,
    )
    assert updated.status_code == 200
    assert updated.json()["name"] == "Payments Core v2"

    deleted = client.delete(f"/api/v1/projects/{project_id}", headers=headers)
    assert deleted.status_code == 204
    assert client.get(f"/api/v1/projects/{project_id}", headers=headers).status_code == 404


def test_cross_user_project_access_rejected(client: TestClient) -> None:
    owner_headers = _auth_headers(client)
    create = client.post(
        "/api/v1/projects",
        json={"name": "Private", "environment": "production"},
        headers=owner_headers,
    )
    project_id = create.json()["id"]

    other_headers = _auth_headers(client)
    assert client.get(f"/api/v1/projects/{project_id}", headers=other_headers).status_code == 404
    assert (
        client.patch(
            f"/api/v1/projects/{project_id}",
            json={"name": "Hijacked"},
            headers=other_headers,
        ).status_code
        == 404
    )
    assert client.delete(f"/api/v1/projects/{project_id}", headers=other_headers).status_code == 404