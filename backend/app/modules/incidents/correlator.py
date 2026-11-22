from __future__ import annotations

import hashlib
import logging
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.core.config import get_settings
from app.models.anomaly import Anomaly
from app.models.deployment import Deployment
from app.models.incident import Incident, IncidentEvent, IncidentEvidence
from app.models.log import Log
from app.models.log_cluster import LogCluster
from app.models.service import Service
from app.models.service_dependency import ServiceDependency
from app.modules.incidents.severity import aggregate_incident_severity

logger = logging.getLogger(__name__)

ACTIVE_STATUSES = frozenset({"OPEN", "INVESTIGATING"})


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


class UnionFind:
    def __init__(self, ids: list[UUID]) -> None:
        self.parent = {node: node for node in ids}

    def find(self, node: UUID) -> UUID:
        while self.parent[node] != node:
            self.parent[node] = self.parent[self.parent[node]]
            node = self.parent[node]
        return node

    def union(self, a: UUID, b: UUID) -> None:
        root_a = self.find(a)
        root_b = self.find(b)
        if root_a != root_b:
            self.parent[root_b] = root_a

    def groups(self) -> dict[UUID, list[UUID]]:
        buckets: dict[UUID, list[UUID]] = defaultdict(list)
        for node in self.parent:
            buckets[self.find(node)].append(node)
        return dict(buckets)


def _load_dependency_map(db: Session, project_id: UUID) -> dict[UUID, set[UUID]]:
    service_ids_subq = select(Service.id).where(Service.project_id == project_id)
    stmt = select(ServiceDependency).where(
        ServiceDependency.upstream_service_id.in_(service_ids_subq),
        ServiceDependency.downstream_service_id.in_(service_ids_subq),
    )
    edges = db.scalars(stmt).all()
    related: dict[UUID, set[UUID]] = defaultdict(set)
    for edge in edges:
        related[edge.upstream_service_id].add(edge.downstream_service_id)
        related[edge.downstream_service_id].add(edge.upstream_service_id)
    return related


def _services_related(a: UUID | None, b: UUID | None, related: dict[UUID, set[UUID]]) -> bool:
    if a is None and b is None:
        return True
    if a is None or b is None:
        return False
    if a == b:
        return True
    return b in related.get(a, set()) or a in related.get(b, set())


def _anomalies_related(
    left: Anomaly,
    right: Anomaly,
    *,
    temporal: timedelta,
    related_services: dict[UUID, set[UUID]],
) -> bool:
    time_gap = abs((left.start_time - right.start_time).total_seconds())
    max_gap = temporal.total_seconds()
    if time_gap > max_gap * 2:
        return False
    if left.service_id is None and right.service_id is None:
        return time_gap <= max_gap
    if not _services_related(left.service_id, right.service_id, related_services):
        return False
    if time_gap > max_gap:
        return left.service_id == right.service_id and left.service_id is not None
    return True


def _cluster_related_to_anomaly(cluster: LogCluster, anomaly: Anomaly, *, temporal: timedelta) -> bool:
    if cluster.first_seen is None or cluster.last_seen is None:
        return False
    if cluster.first_seen > anomaly.end_time + temporal:
        return False
    if cluster.last_seen < anomaly.start_time - temporal:
        return False
    return True


def _correlation_key(anomaly_ids: list[UUID]) -> str:
    payload = ",".join(sorted(str(value) for value in anomaly_ids))
    return hashlib.sha256(payload.encode()).hexdigest()


def _build_incident_title(anomalies: list[Anomaly], service_names: dict[UUID, str]) -> str:
    primary = max(anomalies, key=lambda item: (item.severity, item.start_time))
    service = ""
    if primary.service_id and primary.service_id in service_names:
        service = f" ({service_names[primary.service_id]})"
    return f"{primary.anomaly_type.replace('_', ' ').title()}{service}"


def _event_exists(db: Session, incident_id: UUID, dedupe_key: str) -> bool:
    return (
        db.scalar(
            select(IncidentEvent.id).where(
                IncidentEvent.incident_id == incident_id,
                IncidentEvent.dedupe_key == dedupe_key,
            )
        )
        is not None
    )


def _evidence_exists(db: Session, incident_id: UUID, **filters) -> bool:
    stmt = select(IncidentEvidence.id).where(IncidentEvidence.incident_id == incident_id)
    for key, value in filters.items():
        if value is not None:
            stmt = stmt.where(getattr(IncidentEvidence, key) == value)
    return db.scalar(stmt) is not None


def _append_anomaly_evidence(
    db: Session,
    incident: Incident,
    anomaly: Anomaly,
) -> None:
    if _evidence_exists(db, incident.id, anomaly_id=anomaly.id):
        return
    db.add(
        IncidentEvidence(
            incident_id=incident.id,
            anomaly_id=anomaly.id,
            evidence_type="anomaly",
            explanation=(
                f"Anomaly {anomaly.anomaly_type} ({anomaly.severity}) observed; "
                "correlation based on temporal and service signals, not proven root cause."
            ),
        )
    )
    dedupe = f"anomaly:{anomaly.id}"
    if not _event_exists(db, incident.id, dedupe):
        db.add(
            IncidentEvent(
                incident_id=incident.id,
                event_type="ANOMALY_DETECTED",
                description=anomaly.description,
                event_timestamp=anomaly.start_time,
                event_metadata={
                    "anomaly_id": str(anomaly.id),
                    "anomaly_type": anomaly.anomaly_type,
                    "severity": anomaly.severity,
                    "detection_method": anomaly.detection_method,
                },
                dedupe_key=dedupe,
            )
        )
        if "error" in anomaly.anomaly_type:
            spike_dedupe = f"error_spike:{anomaly.id}"
            if not _event_exists(db, incident.id, spike_dedupe):
                db.add(
                    IncidentEvent(
                        incident_id=incident.id,
                        event_type="ERROR_SPIKE",
                        description=f"Error-related signal: {anomaly.anomaly_type}",
                        event_timestamp=anomaly.start_time,
                        event_metadata={"anomaly_id": str(anomaly.id)},
                        dedupe_key=spike_dedupe,
                    )
                )


def _link_cluster(
    db: Session,
    incident: Incident,
    cluster: LogCluster,
    *,
    reason: str,
) -> None:
    if _evidence_exists(db, incident.id, cluster_id=cluster.id):
        return
    db.add(
        IncidentEvidence(
            incident_id=incident.id,
            cluster_id=cluster.id,
            evidence_type="log_cluster",
            explanation=reason,
        )
    )
    dedupe = f"cluster:{cluster.id}"
    if not _event_exists(db, incident.id, dedupe):
        db.add(
            IncidentEvent(
                incident_id=incident.id,
                event_type="LOG_PATTERN_DETECTED",
                description=cluster.representative_message[:500],
                event_timestamp=cluster.last_seen or cluster.first_seen or _utc_now(),
                event_metadata={
                    "cluster_id": str(cluster.id),
                    "cluster_label": cluster.cluster_label,
                    "log_count": cluster.log_count,
                },
                dedupe_key=dedupe,
            )
        )


def _link_sample_logs(db: Session, incident: Incident, anomaly: Anomaly, *, limit: int = 3) -> None:
    stmt = (
        select(Log)
        .where(
            Log.project_id == incident.project_id,
            Log.level.in_(("ERROR", "CRITICAL")),
            Log.timestamp >= anomaly.start_time,
            Log.timestamp <= anomaly.end_time,
        )
        .order_by(Log.timestamp.desc())
        .limit(limit)
    )
    if anomaly.service_id:
        stmt = stmt.where(Log.service_id == anomaly.service_id)
    for log in db.scalars(stmt).all():
        if _evidence_exists(db, incident.id, log_id=log.id):
            continue
        db.add(
            IncidentEvidence(
                incident_id=incident.id,
                log_id=log.id,
                evidence_type="supporting_log",
                explanation=(
                    "Sample log record within the anomaly window (observed data, not inferred causation)."
                ),
            )
        )
        dedupe = f"log:{log.id}"
        if not _event_exists(db, incident.id, dedupe):
            db.add(
                IncidentEvent(
                    incident_id=incident.id,
                    event_type="SERVICE_IMPACT",
                    description=log.message[:400],
                    event_timestamp=log.timestamp,
                    event_metadata={
                        "log_id": str(log.id),
                        "level": log.level,
                        "service_id": str(log.service_id) if log.service_id else None,
                    },
                    dedupe_key=dedupe,
                )
            )


def _link_deployments(
    db: Session,
    incident: Incident,
    anomalies: list[Anomaly],
    *,
    deploy_window: timedelta,
) -> None:
    if not anomalies:
        return
    window_start = min(item.start_time for item in anomalies) - deploy_window
    window_end = max(item.end_time for item in anomalies)
    service_ids = {item.service_id for item in anomalies if item.service_id}

    stmt = select(Deployment).where(
        Deployment.project_id == incident.project_id,
        Deployment.deployed_at >= window_start,
        Deployment.deployed_at <= window_end,
    )
    deployments = db.scalars(stmt).all()
    for deployment in deployments:
        for anomaly in anomalies:
            if anomaly.start_time < deployment.deployed_at:
                continue
            delta = anomaly.start_time - deployment.deployed_at
            if delta > deploy_window:
                continue
            if deployment.service_id and anomaly.service_id and deployment.service_id != anomaly.service_id:
                continue
            if deployment.service_id and anomaly.service_id and deployment.service_id in service_ids:
                pass
            dedupe = f"deployment:{deployment.id}:{anomaly.id}"
            if _event_exists(db, incident.id, dedupe):
                continue
            db.add(
                IncidentEvent(
                    incident_id=incident.id,
                    event_type="DEPLOYMENT",
                    description=(
                        f"Deployment v{deployment.version} recorded {int(delta.total_seconds())}s "
                        f"before anomaly window (correlation only, not causation)."
                    ),
                    event_timestamp=deployment.deployed_at,
                    event_metadata={
                        "deployment_id": str(deployment.id),
                        "version": deployment.version,
                        "service_id": str(deployment.service_id) if deployment.service_id else None,
                        "seconds_before_anomaly": int(delta.total_seconds()),
                        "anomaly_id": str(anomaly.id),
                    },
                    dedupe_key=dedupe,
                )
            )


def _find_matching_active_incident(
    db: Session,
    project_id: UUID,
    anomalies: list[Anomaly],
    *,
    temporal: timedelta,
) -> Incident | None:
    if not anomalies:
        return None
    start = min(item.start_time for item in anomalies)
    end = max(item.end_time for item in anomalies)
    service_ids = {item.service_id for item in anomalies if item.service_id}

    stmt = (
        select(Incident)
        .where(
            Incident.project_id == project_id,
            Incident.status.in_(tuple(ACTIVE_STATUSES)),
            Incident.started_at <= end + temporal,
            Incident.last_activity_at >= start - temporal,
        )
        .options(selectinload(Incident.evidence_items))
    )
    candidates = db.scalars(stmt).all()
    anomaly_ids = {item.id for item in anomalies}
    for incident in candidates:
        linked_anomalies = {
            row.anomaly_id for row in incident.evidence_items if row.anomaly_id is not None
        }
        if linked_anomalies & anomaly_ids:
            return incident
        if incident.primary_service_id and incident.primary_service_id in service_ids:
            return incident
    return None


def _refresh_incident_fields(incident: Incident, anomalies: list[Anomaly]) -> None:
    if not anomalies:
        return
    incident.severity = aggregate_incident_severity([item.severity for item in anomalies])
    incident.last_activity_at = max(item.end_time for item in anomalies)
    if incident.primary_service_id is None:
        for item in sorted(anomalies, key=lambda row: row.start_time):
            if item.service_id:
                incident.primary_service_id = item.service_id
                break
    incident.description = (
        f"Correlated incident grouping {len(anomalies)} anomaly signal(s). "
        "Relationships reflect observed proximity, not confirmed root cause."
    )


def correlate_project_incidents(db: Session, project_id: UUID) -> dict:
    settings = get_settings()
    lookback = timedelta(hours=settings.incident_correlation_lookback_hours)
    temporal = timedelta(minutes=settings.incident_correlation_window_minutes)
    deploy_window = timedelta(minutes=settings.incident_deployment_window_minutes)
    now = _utc_now()
    since = now - lookback

    anomalies = list(
        db.scalars(
            select(Anomaly)
            .where(Anomaly.project_id == project_id, Anomaly.start_time >= since)
            .order_by(Anomaly.start_time.asc())
        ).all()
    )
    if not anomalies:
        return {
            "status": "no_data",
            "message": "No anomalies in lookback window to correlate.",
            "incidents_created": 0,
            "incidents_updated": 0,
            "anomalies_processed": 0,
        }

    linked_ids = set(
        db.scalars(
            select(IncidentEvidence.anomaly_id).where(
                IncidentEvidence.anomaly_id.is_not(None),
                IncidentEvidence.incident.has(project_id=project_id),
            )
        ).all()
    )
    unlinked = [item for item in anomalies if item.id not in linked_ids]
    if not unlinked:
        return {
            "status": "completed",
            "message": "All recent anomalies already linked to incidents.",
            "incidents_created": 0,
            "incidents_updated": 0,
            "anomalies_processed": 0,
        }

    related_services = _load_dependency_map(db, project_id)
    uf = UnionFind([item.id for item in unlinked])
    by_id = {item.id: item for item in unlinked}

    for idx, left in enumerate(unlinked):
        for right in unlinked[idx + 1 :]:
            if _anomalies_related(left, right, temporal=temporal, related_services=related_services):
                uf.union(left.id, right.id)

    clusters = list(
        db.scalars(select(LogCluster).where(LogCluster.project_id == project_id)).all()
    )
    for cluster in clusters:
        related_anomalies = [
            item
            for item in unlinked
            if _cluster_related_to_anomaly(cluster, item, temporal=temporal)
        ]
        if len(related_anomalies) < 2:
            continue
        anchor = related_anomalies[0]
        for other in related_anomalies[1:]:
            uf.union(anchor.id, other.id)

    service_names: dict[UUID, str] = {}
    for svc in db.scalars(select(Service).where(Service.project_id == project_id)).all():
        service_names[svc.id] = svc.name

    incidents_created = 0
    incidents_updated = 0
    processed = 0

    for members in uf.groups().values():
        group = [by_id[node] for node in members]
        processed += len(group)

        incident = _find_matching_active_incident(db, project_id, group, temporal=temporal)
        if incident is None:
            key = _correlation_key([item.id for item in group])
            existing = db.scalar(
                select(Incident.id).where(
                    Incident.project_id == project_id,
                    Incident.correlation_key == key,
                    Incident.status.in_(tuple(ACTIVE_STATUSES)),
                )
            )
            if existing:
                incident = db.get(Incident, existing)
            else:
                started = min(item.start_time for item in group)
                incident = Incident(
                    project_id=project_id,
                    title=_build_incident_title(group, service_names),
                    description="",
                    severity=aggregate_incident_severity([item.severity for item in group]),
                    status="OPEN",
                    started_at=started,
                    last_activity_at=max(item.end_time for item in group),
                    correlation_key=key,
                    primary_service_id=next(
                        (item.service_id for item in group if item.service_id),
                        None,
                    ),
                )
                db.add(incident)
                db.flush()
                incidents_created += 1
                dedupe = f"incident_open:{incident.id}"
                db.add(
                    IncidentEvent(
                        incident_id=incident.id,
                        event_type="STATUS_CHANGED",
                        description="Incident opened from automated correlation.",
                        event_timestamp=started,
                        event_metadata={"status": "OPEN", "source": "correlation"},
                        dedupe_key=dedupe,
                    )
                )
        else:
            incidents_updated += 1

        for item in group:
            _append_anomaly_evidence(db, incident, item)
            _link_sample_logs(db, incident, item)

        for cluster in clusters:
            if any(_cluster_related_to_anomaly(cluster, item, temporal=temporal) for item in group):
                _link_cluster(
                    db,
                    incident,
                    cluster,
                    reason=(
                        "Log cluster overlaps anomaly time window (text-similarity grouping; "
                        "not semantic root cause)."
                    ),
                )

        _link_deployments(db, incident, group, deploy_window=deploy_window)

        anomaly_ids = list(
            db.scalars(
                select(IncidentEvidence.anomaly_id).where(
                    IncidentEvidence.incident_id == incident.id,
                    IncidentEvidence.anomaly_id.is_not(None),
                )
            ).all()
        )
        linked_anomalies: list[Anomaly] = []
        if anomaly_ids:
            linked_anomalies = list(
                db.scalars(select(Anomaly).where(Anomaly.id.in_(anomaly_ids))).all()
            )
        _refresh_incident_fields(incident, linked_anomalies or group)

    db.commit()
    return {
        "status": "completed",
        "message": "Incident correlation completed.",
        "incidents_created": incidents_created,
        "incidents_updated": incidents_updated,
        "anomalies_processed": processed,
    }