from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUID_PK, new_uuid

if TYPE_CHECKING:
    from app.models.anomaly import Anomaly
    from app.models.deployment import Deployment
    from app.models.incident import Incident
    from app.models.rca import RootCauseCandidate
    from app.models.log import Log
    from app.models.project import Project
    from app.models.service_dependency import ServiceDependency


class Service(TimestampMixin, Base):
    __tablename__ = "services"
    __table_args__ = (UniqueConstraint("project_id", "name", name="uq_services_project_name"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID_PK, primary_key=True, default=new_uuid)
    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID_PK,
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    service_type: Mapped[str] = mapped_column(String(64), nullable=False, default="api")
    environment: Mapped[str] = mapped_column(String(64), nullable=False, default="production")
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    project: Mapped[Project] = relationship("Project", back_populates="services")
    logs: Mapped[list[Log]] = relationship("Log", back_populates="service")
    anomalies: Mapped[list[Anomaly]] = relationship("Anomaly", back_populates="service")
    incidents: Mapped[list[Incident]] = relationship("Incident", back_populates="primary_service")
    deployments: Mapped[list[Deployment]] = relationship("Deployment", back_populates="service")
    downstream_dependencies: Mapped[list[ServiceDependency]] = relationship(
        "ServiceDependency",
        foreign_keys="ServiceDependency.upstream_service_id",
        back_populates="upstream_service",
        cascade="all, delete-orphan",
    )
    upstream_dependencies: Mapped[list[ServiceDependency]] = relationship(
        "ServiceDependency",
        foreign_keys="ServiceDependency.downstream_service_id",
        back_populates="downstream_service",
        cascade="all, delete-orphan",
    )
    root_cause_candidates: Mapped[list[RootCauseCandidate]] = relationship(
        "RootCauseCandidate",
        back_populates="service",
    )