from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy import DateTime, ForeignKey, Index, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUID_PK, new_uuid

if TYPE_CHECKING:
    from app.models.incident import IncidentEvidence
    from app.models.log_batch import LogBatch
    from app.models.log_cluster import LogClusterMembership
    from app.models.project import Project
    from app.models.service import Service


class Log(TimestampMixin, Base):
    __tablename__ = "logs"
    __table_args__ = (
        Index("ix_logs_project_timestamp", "project_id", "timestamp"),
        Index("ix_logs_project_level", "project_id", "level"),
        Index("ix_logs_trace_id", "trace_id"),
        Index("ix_logs_fingerprint", "fingerprint"),
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
    batch_id: Mapped[uuid.UUID] = mapped_column(
        UUID_PK,
        ForeignKey("log_batches.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    level: Mapped[str] = mapped_column(String(16), nullable=False, index=True)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    trace_id: Mapped[str | None] = mapped_column(String(128), nullable=True, index=True)
    request_id: Mapped[str | None] = mapped_column(String(128), nullable=True, index=True)
    log_metadata: Mapped[dict[str, Any]] = mapped_column("metadata", JSONB, nullable=False, default=dict)
    fingerprint: Mapped[str] = mapped_column(String(64), nullable=False, index=True)

    project: Mapped[Project] = relationship("Project", back_populates="logs")
    service: Mapped[Service | None] = relationship("Service", back_populates="logs")
    batch: Mapped[LogBatch] = relationship("LogBatch", back_populates="logs")
    cluster_memberships: Mapped[list[LogClusterMembership]] = relationship(
        "LogClusterMembership",
        back_populates="log",
        cascade="all, delete-orphan",
    )
    incident_evidence: Mapped[list[IncidentEvidence]] = relationship(
        "IncidentEvidence",
        back_populates="log",
    )