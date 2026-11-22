from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy import DateTime, Float, ForeignKey, Index, Integer, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, TimestampUpdateMixin, UUID_PK, new_uuid

if TYPE_CHECKING:
    from app.models.deployment import Deployment
    from app.models.incident import Incident
    from app.models.service import Service

CAUSE_TYPES = frozenset(
    {
        "DEPLOYMENT_REGRESSION",
        "SERVICE_FAILURE",
        "DEPENDENCY_FAILURE",
        "ERROR_PATTERN",
        "TRAFFIC_ANOMALY",
        "CONFIGURATION_CHANGE",
        "UNKNOWN",
    }
)
INVESTIGATION_STATUSES = frozenset({"pending", "running", "completed", "insufficient_data"})


class RCAInvestigation(TimestampUpdateMixin, Base):
    __tablename__ = "rca_investigations"
    __table_args__ = (
        Index("ix_rca_investigations_incident", "incident_id", "version"),
        UniqueConstraint("incident_id", "version", name="uq_rca_investigations_incident_version"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID_PK, primary_key=True, default=new_uuid)
    incident_id: Mapped[uuid.UUID] = mapped_column(
        UUID_PK,
        ForeignKey("incidents.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="pending")
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    candidate_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    investigation_summary: Mapped[str] = mapped_column(Text, nullable=False, default="")
    limitations: Mapped[str] = mapped_column(Text, nullable=False, default="")

    incident: Mapped[Incident] = relationship("Incident", back_populates="rca_investigations")
    candidates: Mapped[list[RootCauseCandidate]] = relationship(
        "RootCauseCandidate",
        back_populates="investigation",
        cascade="all, delete-orphan",
    )


class RootCauseCandidate(TimestampUpdateMixin, Base):
    __tablename__ = "root_cause_candidates"
    __table_args__ = (
        UniqueConstraint("investigation_id", "candidate_key", name="uq_rca_candidate_investigation_key"),
        Index("ix_root_cause_candidates_incident_rank", "incident_id", "ranking"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID_PK, primary_key=True, default=new_uuid)
    investigation_id: Mapped[uuid.UUID] = mapped_column(
        UUID_PK,
        ForeignKey("rca_investigations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    incident_id: Mapped[uuid.UUID] = mapped_column(
        UUID_PK,
        ForeignKey("incidents.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    service_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID_PK,
        ForeignKey("services.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    deployment_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID_PK,
        ForeignKey("deployments.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    cause_type: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    explanation: Mapped[str] = mapped_column(Text, nullable=False)
    confidence_score: Mapped[float] = mapped_column(Float, nullable=False)
    ranking: Mapped[int] = mapped_column(Integer, nullable=False)
    evidence_summary: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    supporting_evidence_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    contradicting_evidence_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    candidate_key: Mapped[str] = mapped_column(String(192), nullable=False)

    investigation: Mapped[RCAInvestigation] = relationship("RCAInvestigation", back_populates="candidates")
    incident: Mapped[Incident] = relationship("Incident", back_populates="root_cause_candidates")
    service: Mapped[Service | None] = relationship("Service", back_populates="root_cause_candidates")
    deployment: Mapped[Deployment | None] = relationship("Deployment", back_populates="root_cause_candidates")