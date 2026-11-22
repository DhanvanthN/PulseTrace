"""Cross-user and IDOR regression tests."""

from fastapi.testclient import TestClient

from test_analysis import _recent_jsonl_spike
from test_logs import _create_project, _register_and_login, _upload


def _second_user(client: TestClient) -> dict[str, str]:
    return _register_and_login(client)


def test_cross_user_logs_upload_and_search(client: TestClient) -> None:
    owner_headers = _register_and_login(client)
    project_id = _create_project(client, owner_headers)
    other = _second_user(client)

    assert (
        client.post(
            f"/api/v1/projects/{project_id}/logs/upload",
            headers=other,
            files={"file": ("x.jsonl", _recent_jsonl_spike(), "application/octet-stream")},
        ).status_code
        == 404
    )
    assert client.get(f"/api/v1/projects/{project_id}/logs", headers=other).status_code == 404


def test_cross_user_incidents_and_rca(client: TestClient) -> None:
    owner_headers = _register_and_login(client)
    project_id = _create_project(client, owner_headers)
    _upload(client, owner_headers, project_id, "spike.jsonl", _recent_jsonl_spike())
    client.post(f"/api/v1/projects/{project_id}/analysis/run", headers=owner_headers, json={})
    client.post(f"/api/v1/projects/{project_id}/incidents/correlate", headers=owner_headers)
    incident_id = client.get(f"/api/v1/projects/{project_id}/incidents", headers=owner_headers).json()["items"][0]["id"]

    other = _second_user(client)
    for path in (
        f"/api/v1/projects/{project_id}/incidents",
        f"/api/v1/projects/{project_id}/incidents/{incident_id}",
        f"/api/v1/projects/{project_id}/incidents/{incident_id}/timeline",
        f"/api/v1/projects/{project_id}/incidents/{incident_id}/evidence",
        f"/api/v1/projects/{project_id}/incidents/{incident_id}/root-causes",
    ):
        assert client.get(path, headers=other).status_code == 404, path

    assert (
        client.post(
            f"/api/v1/projects/{project_id}/incidents/{incident_id}/investigate",
            headers=other,
            json={},
        ).status_code
        == 404
    )


def test_cross_user_analysis_and_clusters(client: TestClient) -> None:
    owner_headers = _register_and_login(client)
    project_id = _create_project(client, owner_headers)
    _upload(client, owner_headers, project_id, "spike.jsonl", _recent_jsonl_spike())
    client.post(f"/api/v1/projects/{project_id}/analysis/run", headers=owner_headers, json={})
    other = _second_user(client)

    assert client.post(f"/api/v1/projects/{project_id}/analysis/run", headers=other, json={}).status_code == 404
    assert client.get(f"/api/v1/projects/{project_id}/anomalies", headers=other).status_code == 404
    assert client.get(f"/api/v1/projects/{project_id}/clusters", headers=other).status_code == 404


def test_resolve_stored_upload_path_rejects_traversal() -> None:
    from fastapi import HTTPException

    from app.modules.logs.storage import resolve_stored_upload_path

    try:
        resolve_stored_upload_path("../../etc/passwd")
        raised = False
    except HTTPException as exc:
        raised = True
        assert exc.status_code == 400
    assert raised