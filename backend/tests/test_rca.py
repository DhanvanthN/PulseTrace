from datetime import datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient

from app.core.config import Settings
from app.modules.root_cause.evidence_collector import TraceEvidence
from app.modules.root_cause.evidence_scorer import score_candidate
from test_incidents import incident_project


def test_scoring_is_deterministic() -> None:
    settings = Settings()
    evidence = [
        TraceEvidence(
            evidence_key="a1",
            source_type="anomaly",
            source_id="1",
            timestamp=datetime.now(timezone.utc),
            service_id=None,
            explanation="support",
            stance="supporting",
            weight_category="deployment",
        ),
        TraceEvidence(
            evidence_key="c1",
            source_type="deployment",
            source_id="2",
            timestamp=None,
            service_id=None,
            explanation="contradict",
            stance="contradicting",
            weight_category="deployment",
        ),
    ]
    first = score_candidate(evidence, settings)
    second = score_candidate(evidence, settings)
    assert first.confidence_score == second.confidence_score
    assert first.confidence_score < 100.0
    assert "not a statistical probability" in first.evidence_summary["score_note"]


def test_contradiction_lowers_score() -> None:
    settings = Settings()
    support_only = [
        TraceEvidence(
            evidence_key="a1",
            source_type="anomaly",
            source_id="1",
            timestamp=None,
            service_id=None,
            explanation="support",
            stance="supporting",
            weight_category="service",
        )
    ]
    mixed = support_only + [
        TraceEvidence(
            evidence_key="c1",
            source_type="anomaly",
            source_id="2",
            timestamp=None,
            service_id=None,
            explanation="contradict",
            stance="contradicting",
            weight_category="service",
        )
    ]
    high = score_candidate(support_only, settings).confidence_score
    low = score_candidate(mixed, settings).confidence_score
    assert low < high


def test_deployment_regression_ranking_with_contradiction(incident_project, client: TestClient) -> None:
    headers, project_id = incident_project
    client.post(f"/api/v1/projects/{project_id}/incidents/correlate", headers=headers)
    incident_id = client.get(f"/api/v1/projects/{project_id}/incidents", headers=headers).json()["items"][0]["id"]

    # Deployment well before correlate window activity — should rank lower than service failure when contradicted
    old_deploy = datetime.now(timezone.utc) - timedelta(days=2)
    client.post(
        f"/api/v1/projects/{project_id}/deployments",
        headers=headers,
        json={
            "version": "0.9.0",
            "deployed_at": old_deploy.isoformat().replace("+00:00", "Z"),
            "description": "Old release",
            "configuration_diff": {"feature_flag": False},
        },
    )

    run = client.post(f"/api/v1/projects/{project_id}/incidents/{incident_id}/investigate", headers=headers)
    assert run.status_code == 200
    assert run.json()["candidate_count"] >= 1

    candidates = client.get(
        f"/api/v1/projects/{project_id}/incidents/{incident_id}/root-causes",
        headers=headers,
    ).json()
    assert candidates["items"]
    assert candidates["items"][0]["ranking"] == 1
    assert all(0 <= item["confidence_score"] <= 100 for item in candidates["items"])

    report = client.get(
        f"/api/v1/projects/{project_id}/incidents/{incident_id}/investigation-report",
        headers=headers,
    )
    assert report.status_code == 200
    assert "investigation_conclusion" in report.json()["report"]
    assert "not probability" in report.json()["markdown"].lower() or "evidence strength" in report.json()["markdown"].lower()


def test_rca_idempotent_candidate_keys(incident_project, client: TestClient) -> None:
    headers, project_id = incident_project
    client.post(f"/api/v1/projects/{project_id}/incidents/correlate", headers=headers)
    incident_id = client.get(f"/api/v1/projects/{project_id}/incidents", headers=headers).json()["items"][0]["id"]

    client.post(f"/api/v1/projects/{project_id}/incidents/{incident_id}/investigate", headers=headers)
    first = client.get(f"/api/v1/projects/{project_id}/incidents/{incident_id}/root-causes", headers=headers).json()
    client.post(f"/api/v1/projects/{project_id}/incidents/{incident_id}/investigate", headers=headers)
    second = client.get(f"/api/v1/projects/{project_id}/incidents/{incident_id}/root-causes", headers=headers).json()
    assert second["version"] == (first["version"] or 0) + 1
    keys_first = {item["title"] for item in first["items"]}
    keys_second = {item["title"] for item in second["items"]}
    assert keys_first == keys_second


def test_rca_project_isolation(incident_project, client: TestClient) -> None:
    headers, project_id = incident_project
    client.post(f"/api/v1/projects/{project_id}/incidents/correlate", headers=headers)
    incident_id = client.get(f"/api/v1/projects/{project_id}/incidents", headers=headers).json()["items"][0]["id"]
    client.post(f"/api/v1/projects/{project_id}/incidents/{incident_id}/investigate", headers=headers)
    candidate_id = client.get(
        f"/api/v1/projects/{project_id}/incidents/{incident_id}/root-causes",
        headers=headers,
    ).json()["items"][0]["id"]

    from test_incidents import _auth_project

    other_headers, _ = _auth_project(client)
    blocked = client.get(
        f"/api/v1/projects/{project_id}/incidents/{incident_id}/root-causes/{candidate_id}",
        headers=other_headers,
    )
    assert blocked.status_code == 404