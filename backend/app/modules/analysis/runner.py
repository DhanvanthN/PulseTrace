from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.anomaly import Anomaly
from app.models.log import Log
from app.models.log_cluster import LogCluster, LogClusterMembership
from app.modules.anomaly_detection.features import build_hourly_buckets, logs_to_dataframe
from app.modules.anomaly_detection.isolation_forest import detect_isolation_forest_anomalies
from app.modules.anomaly_detection.statistical import DetectedAnomaly, detect_statistical_anomalies
from app.modules.clustering.engine import cluster_log_messages

logger = logging.getLogger(__name__)


def _fetch_logs(db: Session, project_id: UUID, service_id: UUID | None, limit: int) -> list[dict]:
    stmt = (
        select(
            Log.id,
            Log.timestamp,
            Log.level,
            Log.service_id,
            Log.fingerprint,
            Log.request_id,
            Log.message,
        )
        .where(Log.project_id == project_id)
        .order_by(Log.timestamp.desc())
        .limit(limit)
    )
    if service_id is not None:
        stmt = stmt.where(Log.service_id == service_id)

    rows = db.execute(stmt).mappings().all()
    records = []
    for row in reversed(rows):
        records.append(
            {
                "log_id": row["id"],
                "timestamp": row["timestamp"],
                "level": row["level"],
                "service_id": row["service_id"],
                "fingerprint": row["fingerprint"],
                "request_id": row["request_id"],
                "message": row["message"],
            }
        )
    return records


def _persist_anomalies(
    db: Session,
    project_id: UUID,
    detected: list[DetectedAnomaly],
) -> int:
    created = 0
    for item in detected:
        exists = db.scalar(
            select(Anomaly.id).where(
                Anomaly.project_id == project_id,
                Anomaly.dedupe_key == item.dedupe_key,
            )
        )
        if exists:
            continue
        db.add(
            Anomaly(
                project_id=project_id,
                service_id=item.service_id,
                anomaly_type=item.anomaly_type,
                severity=item.severity,
                score=item.score,
                description=item.description,
                start_time=item.start_time,
                end_time=item.end_time,
                detection_method=item.detection_method,
                evidence=item.evidence,
                dedupe_key=item.dedupe_key,
            )
        )
        created += 1
    return created


def _replace_clusters(db: Session, project_id: UUID, clusters) -> int:
    db.execute(delete(LogCluster).where(LogCluster.project_id == project_id))
    db.flush()
    total_memberships = 0
    for cluster in clusters:
        row = LogCluster(
            project_id=project_id,
            cluster_label=cluster.cluster_label,
            description=cluster.description,
            representative_message=cluster.representative_message,
            algorithm="dbscan_tfidf",
            log_count=cluster.log_count,
            first_seen=cluster.first_seen,
            last_seen=cluster.last_seen,
        )
        db.add(row)
        db.flush()
        for log_id in cluster.log_ids:
            db.add(LogClusterMembership(cluster_id=row.id, log_id=log_id))
            total_memberships += 1
    return total_memberships


def run_project_analysis(
    db: Session,
    *,
    project_id: UUID,
    service_id: UUID | None = None,
) -> dict:
    settings = get_settings()
    now = datetime.now(timezone.utc)
    window_start = now - timedelta(hours=settings.analysis_window_hours)

    records = _fetch_logs(db, project_id, service_id, settings.analysis_max_logs)
    if not records:
        return {
            "status": "no_data",
            "message": "No logs available for analysis in the selected scope.",
            "anomalies_created": 0,
            "clusters_created": 0,
            "logs_analyzed": 0,
            "window_start": window_start.isoformat(),
            "window_end": now.isoformat(),
        }

    records = [row for row in records if row["timestamp"] >= window_start]
    frame = logs_to_dataframe(records)
    buckets = build_hourly_buckets(frame, settings.analysis_bucket_minutes)

    statistical = detect_statistical_anomalies(
        buckets,
        min_samples=settings.analysis_min_samples,
        z_threshold=settings.analysis_zscore_threshold,
    )
    isolation = detect_isolation_forest_anomalies(
        buckets,
        contamination=settings.analysis_if_contamination,
        min_rows=settings.analysis_if_min_rows,
        random_state=settings.analysis_random_seed,
    )

    detected = statistical + isolation
    anomalies_created = _persist_anomalies(db, project_id, detected)

    cluster_records = records[: settings.cluster_max_logs]
    clusters, noise_count = cluster_log_messages(
        cluster_records,
        eps=settings.cluster_dbscan_eps,
        min_samples=settings.cluster_min_samples,
        max_clusters=settings.cluster_max_clusters,
    )
    memberships = _replace_clusters(db, project_id, clusters)

    db.commit()
    logger.info(
        "Analysis complete project_id=%s anomalies_created=%s clusters=%s",
        project_id,
        anomalies_created,
        len(clusters),
    )

    return {
        "status": "completed",
        "message": "Analysis completed successfully.",
        "anomalies_created": anomalies_created,
        "anomalies_detected": len(detected),
        "clusters_created": len(clusters),
        "cluster_memberships": memberships,
        "noise_logs": noise_count,
        "logs_analyzed": len(records),
        "window_start": window_start.isoformat(),
        "window_end": now.isoformat(),
        "methods": ["statistical_zscore", "isolation_forest", "dbscan_tfidf"],
    }