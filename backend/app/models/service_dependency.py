from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUID_PK, new_uuid

if TYPE_CHECKING:
    from app.models.service import Service


class ServiceDependency(TimestampMixin, Base):
    __tablename__ = "service_dependencies"
    __table_args__ = (
        UniqueConstraint(
            "upstream_service_id",
            "downstream_service_id",
            name="uq_service_dependencies_pair",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID_PK, primary_key=True, default=new_uuid)
    upstream_service_id: Mapped[uuid.UUID] = mapped_column(
        UUID_PK,
        ForeignKey("services.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    downstream_service_id: Mapped[uuid.UUID] = mapped_column(
        UUID_PK,
        ForeignKey("services.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    upstream_service: Mapped[Service] = relationship(
        "Service",
        foreign_keys=[upstream_service_id],
        back_populates="downstream_dependencies",
    )
    downstream_service: Mapped[Service] = relationship(
        "Service",
        foreign_keys=[downstream_service_id],
        back_populates="upstream_dependencies",
    )