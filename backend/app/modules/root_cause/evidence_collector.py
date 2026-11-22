from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.core.config import get_settings
from app.models.anomaly import Anomaly
from app.models.deployment import Deployment
from app.models.incident import Incident, IncidentEvent, IncidentEvidence
from app.models.log import Log
from app.models.log_cluster import LogCluster, LogClusterMembership
from app.models.service import Service
from app.models.service_dependency import ServiceDependency


@dataclass
class TraceEvidence:
    evidence_key: str
    source_type: str
    source_id: str
    timestamp: datetime | None
    service_id: UUID | None
    explanation: str
    stance: str  # supporting | contradicting
    weight_category: str = "general"


@dataclass
class InvestigationContext:
    project_id: UUID
    incident: Incident
    events: list[IncidentEvent]
    incident_evidence: list[IncidentEvidence]
    anomalies: list[Anomaly]
    logs: list[Log]
    clusters: list[LogCluster]
    deployments: list[Deployment]
    services: dict[UUID, Service]
    dependencies: list[ServiceDependency]
    window_start: datetime
    window_end: datetime
    anomalies_by_service: dict[UUID | None, list[Anomaly]] = field(default_factory=dict)


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def collect_investigation_context(db: Session, *, project_id: UUID, incident_id: UUID) -> InvestigationContext | None:
    settings = get_settings()
    incident = db.scalars(
        select(Incident)
        .where(Incident.id == incident_id, Incident.project_id == project_id)
        .options(
            selectinload(Incident.events),
            selectinload(Incident.evidence_items),
        )
    ).first()
    if incident is None:
        return None

    window_end = incident.last_activity_at
    window_start = min(incident.started_at, window_end) - timedelta(hours=settings.rca_lookback_hours)

    anomaly_ids = {
        row.anomaly_id for row in incident.evidence_items if row.anomaly_id is not None
    }
    cluster_ids = {row.cluster_id for row in incident.evidence_items if row.cluster_id is not None}
    log_ids = {row.log_id for row in incident.evidence_items if row.log_id is not None}

    anomalies = []
    if anomaly_ids:
        anomalies = list(db.scalars(select(Anomaly).where(Anomaly.id.in_(anomaly_ids))).all())
    if not anomalies:
        anomalies = list(
            db.scalars(
                select(Anomaly).where(
                    Anomaly.project_id == project_id,
                    Anomaly.start_time >= window_start,
                    Anomaly.start_time <= window_end,
                )
            ).all()
        )

    clusters: list[LogCluster] = []
    if cluster_ids:
        clusters = list(db.scalars(select(LogCluster).where(LogCluster.id.in_(cluster_ids))).all())
    elif anomalies:
        clusters = list(db.scalars(select(LogCluster).where(LogCluster.project_id == project_id)).all())

    logs: list[Log] = []
    if log_ids:
        logs = list(db.scalars(select(Log).where(Log.id.in_(log_ids))).all())
    else:
        stmt = (
            select(Log)
            .where(
                Log.project_id == project_id,
                Log.timestamp >= window_start,
                Log.timestamp <= window_end,
                Log.level.in_(("ERROR", "CRITICAL", "WARNING")),
            )
            .order_by(Log.timestamp.desc())
            .limit(settings.rca_max_logs)
        )
        logs = list(db.scalars(stmt).all())

    if cluster_ids:
        membership_logs = db.scalars(
            select(Log)
            .join(LogClusterMembership, LogClusterMembership.log_id == Log.id)
            .where(LogClusterMembership.cluster_id.in_(cluster_ids))
            .limit(settings.rca_max_logs)
        ).all()
        known = {log.id for log in logs}
        logs.extend([row for row in membership_logs if row.id not in known])

    deployments = list(
        db.scalars(
            select(Deployment).where(
                Deployment.project_id == project_id,
                Deployment.deployed_at >= window_start - timedelta(hours=settings.rca_lookback_hours),
                Deployment.deployed_at <= window_end,
            )
        ).all()
    )

    services = {
        row.id: row
        for row in db.scalars(select(Service).where(Service.project_id == project_id)).all()
    }
    service_ids = select(Service.id).where(Service.project_id == project_id)
    dependencies = list(
        db.scalars(
            select(ServiceDependency).where(
                ServiceDependency.upstream_service_id.in_(service_ids),
                ServiceDependency.downstream_service_id.in_(service_ids),
            )
        ).all()
    )

    by_service: dict[UUID | None, list[Anomaly]] = {}
    for item in anomalies:
        by_service.setdefault(item.service_id, []).append(item)

    return InvestigationContext(
        project_id=project_id,
        incident=incident,
        events=sorted(incident.events, key=lambda e: e.event_timestamp),
        incident_evidence=list(incident.evidence_items),
        anomalies=anomalies,
        logs=logs,
        clusters=clusters,
        deployments=deployments,
        services=services,
        dependencies=dependencies,
        window_start=window_start,
        window_end=window_end,
        anomalies_by_service=by_service,
    )