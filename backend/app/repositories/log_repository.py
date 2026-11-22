from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.models.log import Log


class LogSearchFilters:
    def __init__(
        self,
        *,
        start_time: datetime | None = None,
        end_time: datetime | None = None,
        level: str | None = None,
        service_id: UUID | None = None,
        trace_id: str | None = None,
        request_id: str | None = None,
        keyword: str | None = None,
        batch_id: UUID | None = None,
    ) -> None:
        self.start_time = start_time
        self.end_time = end_time
        self.level = level
        self.service_id = service_id
        self.trace_id = trace_id
        self.request_id = request_id
        self.keyword = keyword
        self.batch_id = batch_id


class LogRepository:
    def __init__(self, db: Session) -> None:
        self._db = db

    def _apply_filters(self, stmt, project_id: UUID, filters: LogSearchFilters):
        stmt = stmt.where(Log.project_id == project_id)
        if filters.start_time is not None:
            stmt = stmt.where(Log.timestamp >= filters.start_time)
        if filters.end_time is not None:
            stmt = stmt.where(Log.timestamp <= filters.end_time)
        if filters.level is not None:
            stmt = stmt.where(Log.level == filters.level.upper())
        if filters.service_id is not None:
            stmt = stmt.where(Log.service_id == filters.service_id)
        if filters.trace_id is not None:
            stmt = stmt.where(Log.trace_id == filters.trace_id)
        if filters.request_id is not None:
            stmt = stmt.where(Log.request_id == filters.request_id)
        if filters.batch_id is not None:
            stmt = stmt.where(Log.batch_id == filters.batch_id)
        if filters.keyword:
            escaped = filters.keyword.replace("%", "\\%").replace("_", "\\_")
            stmt = stmt.where(Log.message.ilike(f"%{escaped}%", escape="\\"))
        return stmt

    def search(
        self,
        project_id: UUID,
        filters: LogSearchFilters,
        *,
        skip: int = 0,
        limit: int = 50,
    ) -> tuple[list[Log], int]:
        count_stmt = self._apply_filters(select(func.count()).select_from(Log), project_id, filters)
        total = self._db.scalar(count_stmt) or 0

        rows_stmt = (
            self._apply_filters(select(Log), project_id, filters)
            .options(selectinload(Log.service))
            .order_by(Log.timestamp.desc(), Log.id.desc())
            .offset(skip)
            .limit(limit)
        )
        items = list(self._db.scalars(rows_stmt).all())
        return items, int(total)

    def get_in_project(self, log_id: UUID, project_id: UUID) -> Log | None:
        stmt = (
            select(Log)
            .where(Log.id == log_id, Log.project_id == project_id)
            .options(selectinload(Log.service))
        )
        return self._db.scalars(stmt).first()