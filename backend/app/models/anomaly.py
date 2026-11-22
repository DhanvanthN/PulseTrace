from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy import DateTime, Float, ForeignKey, Index, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUID_PK, new_uuid

if TYPE_CHECKING:
    from app.models.incident import IncidentEvidence
    from app.models.project import Project
    from app.models.service import Service


class Anomaly(TimestampMixin, Base):
    __tablename__ = "anomalies"
    __table_args__ = (
        UniqueConstraint("project_id", "dedupe_key", name="uq_anomalies_project_dedupe"),
        Index("ix_anomalies_project_severity", "project_id", "severity"),
        Index("ix_anomalies_project_type", "project_id", "anomaly_type"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID_PK, primary_key=True, default=new_uuid)
    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID_PK,
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    service_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID_PK,
        ForeignKey("services.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    anomaly_type: Mapped[str] = mapped_column(String(64), nullable=False)
    severity: Mapped[str] = mapped_column(String(16), nullable=False, index=True)
    score: Mapped[float] = mapped_column(Float, nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    start_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    end_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    detection_method: Mapped[str] = mapped_column(String(64), nullable=False)
    evidence: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    dedupe_key: Mapped[str] = mapped_column(String(128), nullable=False)

    project: Mapped[Project] = relationship("Project", back_populates="anomalies")
    service: Mapped[Service | None] = relationship("Service", back_populates="anomalies")
    incident_evidence: Mapped[list[IncidentEvidence]] = relationship(
        "IncidentEvidence",
        back_populates="anomaly",
    )