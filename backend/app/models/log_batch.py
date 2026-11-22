from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUID_PK, new_uuid

if TYPE_CHECKING:
    from app.models.log import Log
    from app.models.project import Project
    from app.models.user import User


class LogBatch(TimestampMixin, Base):
    __tablename__ = "log_batches"

    id: Mapped[uuid.UUID] = mapped_column(UUID_PK, primary_key=True, default=new_uuid)
    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID_PK,
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    uploaded_by: Mapped[uuid.UUID] = mapped_column(
        UUID_PK,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    file_format: Mapped[str] = mapped_column(String(16), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="pending", index=True)
    storage_path: Mapped[str] = mapped_column(String(512), nullable=False)
    total_records: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    processed_records: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    failed_records: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    error_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    project: Mapped[Project] = relationship("Project", back_populates="log_batches")
    uploader: Mapped[User | None] = relationship("User")
    logs: Mapped[list[Log]] = relationship("Log", back_populates="batch", cascade="all, delete-orphan")