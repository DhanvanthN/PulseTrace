from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampUpdateMixin, UUID_PK, new_uuid

if TYPE_CHECKING:
    from app.models.anomaly import Anomaly
    from app.models.deployment import Deployment
    from app.models.incident import Incident
    from app.models.log import Log
    from app.models.log_batch import LogBatch
    from app.models.log_cluster import LogCluster
    from app.models.service import Service
    from app.models.user import User


class Project(TimestampUpdateMixin, Base):
    __tablename__ = "projects"
    __table_args__ = (UniqueConstraint("owner_id", "name", name="uq_projects_owner_name"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID_PK, primary_key=True, default=new_uuid)
    owner_id: Mapped[uuid.UUID] = mapped_column(
        UUID_PK,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    environment: Mapped[str] = mapped_column(String(64), nullable=False, default="development")

    owner: Mapped[User] = relationship("User", back_populates="projects")
    services: Mapped[list[Service]] = relationship(
        "Service",
        back_populates="project",
        cascade="all, delete-orphan",
    )
    log_batches: Mapped[list[LogBatch]] = relationship(
        "LogBatch",
        back_populates="project",
        cascade="all, delete-orphan",
    )
    logs: Mapped[list[Log]] = relationship(
        "Log",
        back_populates="project",
        cascade="all, delete-orphan",
    )
    anomalies: Mapped[list[Anomaly]] = relationship(
        "Anomaly",
        back_populates="project",
        cascade="all, delete-orphan",
    )
    log_clusters: Mapped[list[LogCluster]] = relationship(
        "LogCluster",
        back_populates="project",
        cascade="all, delete-orphan",
    )
    incidents: Mapped[list[Incident]] = relationship(
        "Incident",
        back_populates="project",
        cascade="all, delete-orphan",
    )
    deployments: Mapped[list[Deployment]] = relationship(
        "Deployment",
        back_populates="project",
        cascade="all, delete-orphan",
    )