from datetime import datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient

from app.modules.incidents.severity import aggregate_incident_severity
from app.modules.incidents.sanitize import sanitize_configuration_diff
from test_analysis import _recent_jsonl_spike
from test_logs import _create_project, _register_and_login, _upload


def _auth_project(client: TestClient) -> tuple[dict[str, str], str]:
    headers = _register_and_login(client)
    project_id = _create_project(client, headers)
    return headers, project_id


def test_severity_aggregation_rules() -> None:
    assert aggregate_incident_severity(["CRITICAL", "LOW"]) == "CRITICAL"
    assert aggregate_incident_severity(["HIGH", "HIGH"]) == "HIGH"
    assert aggregate_incident_severity(["HIGH", "MEDIUM", "MEDIUM"]) == "HIGH"
    assert aggregate_incident_severity(["MEDIUM", "MEDIUM", "MEDIUM"]) == "HIGH"
    assert aggregate_incident_severity(["LOW"]) == "LOW"


def test_sanitize_configuration_diff_strips_secrets() -> None:
    payload = {"api_key": "x", "timeout": 5, "nested": {"auth_token": "y"}}
    cleaned = sanitize_configuration_diff(payload)
    assert "api_key" not in cleaned
    assert cleaned["timeout"] == 5
    assert "auth_token" not in cleaned["nested"]


@pytest.fixture
def incident_project(client: TestClient) -> tuple[dict[str, str], str]:
    headers, project_id = _auth_project(client)
    _upload(client, headers, project_id, "spike.jsonl", _recent_jsonl_spike())
    client.post(f"/api/v1/projects/{project_id}/analysis/run", headers=headers, json={})
    return headers, project_id


def test_manual_incident_create(incident_project, client: TestClient) -> None:
    headers, project_id = incident_project
    response = client.post(
        f"/api/v1/projects/{project_id}/incidents",
        headers=headers,
        json={"title": "Manual outage", "description": "Investigating", "severity": "HIGH"},
    )
    assert response.status_code == 201
    body = response.json()
    assert body["status"] == "OPEN"
    assert body["severity"] == "HIGH"


def test_correlate_creates_incidents(incident_project, client: TestClient) -> None:
    headers, project_id = incident_project
    correlate = client.post(f"/api/v1/projects/{project_id}/incidents/correlate", headers=headers)
    assert correlate.status_code == 200
    assert correlate.json()["incidents_created"] >= 1

    listing = client.get(f"/api/v1/projects/{project_id}/incidents", headers=headers)
    assert listing.status_code == 200
    assert listing.json()["total"] >= 1

    incident_id = listing.json()["items"][0]["id"]
    timeline = client.get(f"/api/v1/projects/{project_id}/incidents/{incident_id}/timeline", headers=headers)
    assert timeline.status_code == 200
    events = timeline.json()["items"]
    assert events == sorted(events, key=lambda item: item["event_timestamp"])
    assert any(event["event_type"] == "ANOMALY_DETECTED" for event in events)

    evidence = client.get(f"/api/v1/projects/{project_id}/incidents/{incident_id}/evidence", headers=headers)
    assert evidence.status_code == 200
    assert len(evidence.json()["items"]) >= 1
    assert any(row["anomaly_id"] for row in evidence.json()["items"])


def test_duplicate_correlation_idempotent(incident_project, client: TestClient) -> None:
    headers, project_id = incident_project
    first = client.post(f"/api/v1/projects/{project_id}/incidents/correlate", headers=headers)
    second = client.post(f"/api/v1/projects/{project_id}/incidents/correlate", headers=headers)
    assert first.status_code == 200
    assert second.status_code == 200
    assert second.json()["incidents_created"] == 0
    assert second.json()["anomalies_processed"] == 0


def test_incident_resolve_and_reopen(incident_project, client: TestClient) -> None:
    headers, project_id = incident_project
    client.post(f"/api/v1/projects/{project_id}/incidents/correlate", headers=headers)
    incident_id = client.get(f"/api/v1/projects/{project_id}/incidents", headers=headers).json()["items"][0]["id"]

    resolved = client.patch(
        f"/api/v1/projects/{project_id}/incidents/{incident_id}",
        headers=headers,
        json={"status": "RESOLVED"},
    )
    assert resolved.status_code == 200
    assert resolved.json()["resolved_at"] is not None

    reopened = client.patch(
        f"/api/v1/projects/{project_id}/incidents/{incident_id}",
        headers=headers,
        json={"status": "OPEN"},
    )
    assert reopened.status_code == 200
    assert reopened.json()["resolved_at"] is None


def test_investigation_note(incident_project, client: TestClient) -> None:
    headers, project_id = incident_project
    client.post(f"/api/v1/projects/{project_id}/incidents/correlate", headers=headers)
    incident_id = client.get(f"/api/v1/projects/{project_id}/incidents", headers=headers).json()["items"][0]["id"]

    note = client.post(
        f"/api/v1/projects/{project_id}/incidents/{incident_id}/notes",
        headers=headers,
        json={"content": "Checked dashboards; errors still elevated."},
    )
    assert note.status_code == 200
    assert note.json()["event_type"] == "INVESTIGATION_NOTE"


def test_deployment_registration_and_correlation_event(incident_project, client: TestClient) -> None:
    headers, project_id = incident_project
    deployed_at = datetime.now(timezone.utc) - timedelta(minutes=30)
    deployment = client.post(
        f"/api/v1/projects/{project_id}/deployments",
        headers=headers,
        json={
            "version": "2.4.1",
            "change_type": "release",
            "description": "Payments rollout",
            "deployed_at": deployed_at.isoformat().replace("+00:00", "Z"),
            "configuration_diff": {"timeout_ms": 5000, "api_key": "redacted-should-drop"},
        },
    )
    assert deployment.status_code == 201
    assert "api_key" not in deployment.json()["configuration_diff"]

    client.post(f"/api/v1/projects/{project_id}/incidents/correlate", headers=headers)
    incident_id = client.get(f"/api/v1/projects/{project_id}/incidents", headers=headers).json()["items"][0]["id"]
    timeline = client.get(f"/api/v1/projects/{project_id}/incidents/{incident_id}/timeline", headers=headers).json()
    deployment_events = [item for item in timeline["items"] if item["event_type"] == "DEPLOYMENT"]
    if deployment_events:
        assert "correlation only" in deployment_events[0]["description"].lower()


def test_incident_project_isolation(client: TestClient) -> None:
    headers_a, project_a = _auth_project(client)
    headers_b = _register_and_login(client)
    response = client.get(f"/api/v1/projects/{project_a}/incidents", headers=headers_b)
    assert response.status_code == 404


def test_service_dependency_correlation(client: TestClient, incident_project) -> None:
    headers, project_id = incident_project
    service_a = client.post(
        f"/api/v1/projects/{project_id}/services",
        headers=headers,
        json={"name": "api-gateway", "service_type": "api", "environment": "staging"},
    ).json()
    service_b = client.post(
        f"/api/v1/projects/{project_id}/services",
        headers=headers,
        json={"name": "payments", "service_type": "api", "environment": "staging"},
    ).json()
    dep = client.post(
        f"/api/v1/projects/{project_id}/services/dependencies",
        headers=headers,
        json={
            "upstream_service_id": service_a["id"],
            "downstream_service_id": service_b["id"],
        },
    )
    assert dep.status_code == 201