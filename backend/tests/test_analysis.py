import json
import uuid
from datetime import datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient

from app.core.config import get_settings
from app.modules.anomaly_detection.features import BucketFeatures, build_hourly_buckets, logs_to_dataframe
from app.modules.anomaly_detection.statistical import detect_statistical_anomalies
from app.modules.clustering.engine import cluster_log_messages
from app.modules.clustering.text_normalize import normalize_message_for_clustering

from test_logs import _create_project, _register_and_login, _upload


def _auth_project(client: TestClient) -> tuple[dict[str, str], str]:
    headers = _register_and_login(client)
    project_id = _create_project(client, headers)
    return headers, project_id


def _bucket_series() -> list[BucketFeatures]:
    start = datetime(2026, 1, 1, tzinfo=timezone.utc)
    buckets: list[BucketFeatures] = []
    for hour in range(8):
        buckets.append(
            BucketFeatures(
                bucket_start=start + timedelta(hours=hour),
                bucket_end=start + timedelta(hours=hour + 1),
                service_id=None,
                total_count=20,
                error_count=0 if hour % 2 == 0 else 1,
                critical_count=0,
                warning_count=2,
                unique_fingerprints=10,
                request_count=5,
            )
        )
    buckets.append(
        BucketFeatures(
            bucket_start=start + timedelta(hours=8),
            bucket_end=start + timedelta(hours=9),
            service_id=None,
            total_count=120,
            error_count=80,
            critical_count=6,
            warning_count=3,
            unique_fingerprints=40,
            request_count=30,
        )
    )
    return buckets


def test_statistical_error_spike_detection() -> None:
    detected = detect_statistical_anomalies(_bucket_series(), min_samples=5, z_threshold=2.5)
    types = {item.anomaly_type for item in detected}
    assert "error_spike" in types
    error = next(item for item in detected if item.anomaly_type == "error_spike")
    assert error.severity in {"HIGH", "CRITICAL", "MEDIUM"}
    assert error.evidence["z_score"] >= 2.5
    assert "probability" in error.evidence["score_note"].lower()


def test_statistical_insufficient_buckets() -> None:
    short = _bucket_series()[:3]
    assert detect_statistical_anomalies(short, min_samples=5, z_threshold=2.5) == []


def test_text_normalization_groups_variable_tokens() -> None:
    a = normalize_message_for_clustering(
        "Connection failed for user 192.168.1.10 req=a1b2c3d4-e5f6-7890-abcd-ef1234567890"
    )
    b = normalize_message_for_clustering(
        "Connection failed for user 10.0.0.5 req=00000000-0000-4000-8000-000000000099"
    )
    assert a == b


def test_dbscan_clusters_similar_messages() -> None:
    now = datetime.now(timezone.utc)
    template = "Payment timeout for order <uuid>"
    records = []
    for idx in range(6):
        records.append(
            {
                "log_id": uuid.uuid4(),
                "timestamp": now,
                "message": template.replace("<uuid>", str(uuid.uuid4())),
            }
        )
    records.append(
        {
            "log_id": uuid.uuid4(),
            "timestamp": now,
            "message": "Unrelated healthcheck ok",
        }
    )
    clusters, noise = cluster_log_messages(records, eps=0.35, min_samples=3, max_clusters=10)
    assert len(clusters) >= 1
    assert clusters[0].log_count >= 3
    assert "text-similarity" in clusters[0].description.lower()
    assert noise >= 0


def test_build_hourly_buckets_from_frame() -> None:
    now = datetime.now(timezone.utc)
    rows = [
        {"timestamp": now, "level": "ERROR", "service_id": None, "fingerprint": "a", "request_id": None, "log_id": 1, "message": "e1"},
        {"timestamp": now, "level": "INFO", "service_id": None, "fingerprint": "b", "request_id": "r1", "log_id": 2, "message": "i1"},
    ]
    buckets = build_hourly_buckets(logs_to_dataframe(rows), 60)
    assert len(buckets) == 1
    assert buckets[0].error_count == 1
    assert buckets[0].total_count == 2


def _recent_jsonl_spike() -> bytes:
    now = datetime.now(timezone.utc)
    lines: list[str] = []
    for hour in range(1, 8):
        ts = (now - timedelta(hours=hour)).isoformat().replace("+00:00", "Z")
        for _ in range(15):
            lines.append(json.dumps({"timestamp": ts, "level": "INFO", "message": "steady traffic"}))
        lines.append(json.dumps({"timestamp": ts, "level": "ERROR", "message": "baseline error"}))
    latest = now.isoformat().replace("+00:00", "Z")
    for _ in range(30):
        lines.append(json.dumps({"timestamp": latest, "level": "ERROR", "message": "database connection reset"}))
    for _ in range(5):
        lines.append(json.dumps({"timestamp": latest, "level": "CRITICAL", "message": "database unavailable"}))
    return "\n".join(lines).encode()


@pytest.fixture
def analysis_project(client: TestClient) -> tuple[dict[str, str], str]:
    headers, project_id = _auth_project(client)
    upload = _upload(client, headers, project_id, "spike.jsonl", _recent_jsonl_spike())
    assert upload.status_code == 201
    assert upload.json()["processed_records"] > 0
    return headers, project_id


def test_analysis_run_and_list(analysis_project, client: TestClient) -> None:
    headers, project_id = analysis_project
    run = client.post(f"/api/v1/projects/{project_id}/analysis/run", headers=headers, json={})
    assert run.status_code == 200
    body = run.json()
    assert body["status"] == "completed"
    assert body["anomalies_detected"] >= 1
    assert body["clusters_created"] >= 0

    listing = client.get(f"/api/v1/projects/{project_id}/anomalies", headers=headers)
    assert listing.status_code == 200
    payload = listing.json()
    assert payload["total"] >= 1
    assert payload["items"][0]["evidence"]

    detail = client.get(
        f"/api/v1/projects/{project_id}/anomalies/{payload['items'][0]['id']}",
        headers=headers,
    )
    assert detail.status_code == 200
    assert detail.json()["detection_method"] in {"statistical_zscore", "isolation_forest"}


def test_duplicate_analysis_prevention(analysis_project, client: TestClient) -> None:
    headers, project_id = analysis_project
    first = client.post(f"/api/v1/projects/{project_id}/analysis/run", headers=headers, json={})
    assert first.status_code == 200
    created_first = first.json()["anomalies_created"]

    second = client.post(f"/api/v1/projects/{project_id}/analysis/run", headers=headers, json={})
    assert second.status_code == 200
    assert second.json()["anomalies_created"] == 0
    assert second.json()["anomalies_detected"] >= created_first


def test_cluster_api(analysis_project, client: TestClient) -> None:
    headers, project_id = analysis_project
    client.post(f"/api/v1/projects/{project_id}/analysis/run", headers=headers, json={})
    clusters = client.get(f"/api/v1/projects/{project_id}/clusters?min_log_count=2", headers=headers)
    assert clusters.status_code == 200
    data = clusters.json()
    if data["total"] > 0:
        cluster_id = data["items"][0]["id"]
        detail = client.get(f"/api/v1/projects/{project_id}/clusters/{cluster_id}", headers=headers)
        assert detail.status_code == 200
        assert "representative_message" in detail.json()


def test_analysis_project_isolation(client: TestClient) -> None:
    headers_a, project_a = _auth_project(client)
    _upload(client, headers_a, project_a, "spike.jsonl", _recent_jsonl_spike())

    headers_b = _register_and_login(client)
    response = client.post(f"/api/v1/projects/{project_a}/analysis/run", headers=headers_b, json={})
    assert response.status_code == 404


def test_analysis_no_logs(client: TestClient) -> None:
    headers, project_id = _auth_project(client)
    response = client.post(f"/api/v1/projects/{project_id}/analysis/run", headers=headers, json={})
    assert response.status_code == 200
    assert response.json()["status"] == "no_data"


def test_isolation_forest_min_rows(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    headers, project_id = _auth_project(client)
    now = datetime.now(timezone.utc)
    lines = [
        json.dumps({"timestamp": now.isoformat().replace("+00:00", "Z"), "level": "INFO", "message": "only one"})
    ]
    _upload(client, headers, project_id, "tiny.jsonl", "\n".join(lines).encode())
    monkeypatch.setenv("ANALYSIS_IF_MIN_ROWS", "50")
    get_settings.cache_clear()
    run = client.post(f"/api/v1/projects/{project_id}/analysis/run", headers=headers, json={})
    get_settings.cache_clear()
    assert run.status_code == 200
    assert run.json()["status"] in {"completed", "no_data"}