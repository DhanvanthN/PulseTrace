from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUID_PK, new_uuid

if TYPE_CHECKING:
    from app.models.incident import IncidentEvidence
    from app.models.log import Log
    from app.models.project import Project


class LogCluster(TimestampMixin, Base):
    __tablename__ = "log_clusters"
    __table_args__ = (
        UniqueConstraint("project_id", "cluster_label", name="uq_log_clusters_project_label"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID_PK, primary_key=True, default=new_uuid)
    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID_PK,
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    cluster_label: Mapped[str] = mapped_column(String(32), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    representative_message: Mapped[str] = mapped_column(Text, nullable=False)
    algorithm: Mapped[str] = mapped_column(String(64), nullable=False, default="dbscan_tfidf")
    log_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    first_seen: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_seen: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    project: Mapped[Project] = relationship("Project", back_populates="log_clusters")
    memberships: Mapped[list[LogClusterMembership]] = relationship(
        "LogClusterMembership",
        back_populates="cluster",
        cascade="all, delete-orphan",
    )
    incident_evidence: Mapped[list[IncidentEvidence]] = relationship(
        "IncidentEvidence",
        back_populates="cluster",
    )


class LogClusterMembership(Base):
    __tablename__ = "log_cluster_memberships"
    __table_args__ = (
        UniqueConstraint("log_id", "cluster_id", name="uq_cluster_membership_log_cluster"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID_PK, primary_key=True, default=new_uuid)
    cluster_id: Mapped[uuid.UUID] = mapped_column(
        UUID_PK,
        ForeignKey("log_clusters.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    log_id: Mapped[uuid.UUID] = mapped_column(
        UUID_PK,
        ForeignKey("logs.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    cluster: Mapped[LogCluster] = relationship("LogCluster", back_populates="memberships")
    log: Mapped[Log] = relationship("Log", back_populates="cluster_memberships")