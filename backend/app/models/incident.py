from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, TimestampUpdateMixin, UUID_PK, new_uuid

if TYPE_CHECKING:
    from app.models.anomaly import Anomaly
    from app.models.log import Log
    from app.models.log_cluster import LogCluster
    from app.models.project import Project
    from app.models.rca import RCAInvestigation, RootCauseCandidate
    from app.models.service import Service


INCIDENT_STATUSES = frozenset({"OPEN", "INVESTIGATING", "RESOLVED", "IGNORED"})
INCIDENT_SEVERITIES = frozenset({"LOW", "MEDIUM", "HIGH", "CRITICAL"})


class Incident(TimestampUpdateMixin, Base):
    __tablename__ = "incidents"
    __table_args__ = (
        Index("ix_incidents_project_status", "project_id", "status"),
        Index("ix_incidents_project_severity", "project_id", "severity"),
        Index("ix_incidents_last_activity", "project_id", "last_activity_at"),
        UniqueConstraint("project_id", "correlation_key", name="uq_incidents_project_correlation_key"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID_PK, primary_key=True, default=new_uuid)
    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID_PK,
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    primary_service_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID_PK,
        ForeignKey("services.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False, default="")
    severity: Mapped[str] = mapped_column(String(16), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="OPEN", index=True)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    last_activity_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    correlation_key: Mapped[str | None] = mapped_column(String(128), nullable=True)

    project: Mapped[Project] = relationship("Project", back_populates="incidents")
    primary_service: Mapped[Service | None] = relationship("Service", back_populates="incidents")
    events: Mapped[list[IncidentEvent]] = relationship(
        "IncidentEvent",
        back_populates="incident",
        cascade="all, delete-orphan",
        order_by="IncidentEvent.event_timestamp",
    )
    evidence_items: Mapped[list[IncidentEvidence]] = relationship(
        "IncidentEvidence",
        back_populates="incident",
        cascade="all, delete-orphan",
    )
    rca_investigations: Mapped[list[RCAInvestigation]] = relationship(
        "RCAInvestigation",
        back_populates="incident",
        cascade="all, delete-orphan",
    )
    root_cause_candidates: Mapped[list[RootCauseCandidate]] = relationship(
        "RootCauseCandidate",
        back_populates="incident",
        cascade="all, delete-orphan",
    )


class IncidentEvent(TimestampMixin, Base):
    __tablename__ = "incident_events"
    __table_args__ = (
        Index("ix_incident_events_incident_time", "incident_id", "event_timestamp"),
        UniqueConstraint("incident_id", "dedupe_key", name="uq_incident_events_incident_dedupe"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID_PK, primary_key=True, default=new_uuid)
    incident_id: Mapped[uuid.UUID] = mapped_column(
        UUID_PK,
        ForeignKey("incidents.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    event_type: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    event_timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    event_metadata: Mapped[dict[str, Any]] = mapped_column("metadata", JSONB, nullable=False, default=dict)
    dedupe_key: Mapped[str] = mapped_column(String(128), nullable=False)

    incident: Mapped[Incident] = relationship("Incident", back_populates="events")


class IncidentEvidence(TimestampMixin, Base):
    __tablename__ = "incident_evidence"
    __table_args__ = (
        CheckConstraint(
            "(CASE WHEN log_id IS NOT NULL THEN 1 ELSE 0 END + "
            "CASE WHEN anomaly_id IS NOT NULL THEN 1 ELSE 0 END + "
            "CASE WHEN cluster_id IS NOT NULL THEN 1 ELSE 0 END) >= 1",
            name="ck_incident_evidence_at_least_one_ref",
        ),
        Index("ix_incident_evidence_incident", "incident_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID_PK, primary_key=True, default=new_uuid)
    incident_id: Mapped[uuid.UUID] = mapped_column(
        UUID_PK,
        ForeignKey("incidents.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    log_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID_PK,
        ForeignKey("logs.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    anomaly_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID_PK,
        ForeignKey("anomalies.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    cluster_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID_PK,
        ForeignKey("log_clusters.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    evidence_type: Mapped[str] = mapped_column(String(64), nullable=False)
    explanation: Mapped[str] = mapped_column(Text, nullable=False)

    incident: Mapped[Incident] = relationship("Incident", back_populates="evidence_items")
    log: Mapped[Log | None] = relationship("Log", back_populates="incident_evidence")
    anomaly: Mapped[Anomaly | None] = relationship("Anomaly", back_populates="incident_evidence")
    cluster: Mapped[LogCluster | None] = relationship("LogCluster", back_populates="incident_evidence")