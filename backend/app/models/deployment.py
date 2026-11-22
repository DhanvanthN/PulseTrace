from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy import DateTime, ForeignKey, Index, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUID_PK, new_uuid

if TYPE_CHECKING:
    from app.models.project import Project
    from app.models.rca import RootCauseCandidate
    from app.models.service import Service


class Deployment(TimestampMixin, Base):
    __tablename__ = "deployments"
    __table_args__ = (Index("ix_deployments_project_deployed", "project_id", "deployed_at"),)

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
    version: Mapped[str] = mapped_column(String(128), nullable=False)
    change_type: Mapped[str] = mapped_column(String(64), nullable=False, default="release")
    description: Mapped[str] = mapped_column(Text, nullable=False, default="")
    configuration_diff: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    deployed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)

    project: Mapped[Project] = relationship("Project", back_populates="deployments")
    service: Mapped[Service | None] = relationship("Service", back_populates="deployments")
    root_cause_candidates: Mapped[list[RootCauseCandidate]] = relationship(
        "RootCauseCandidate",
        back_populates="deployment",
    )