from datetime import datetime
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.anomaly import Anomaly


class AnomalyFilters:
    def __init__(
        self,
        *,
        severity: str | None = None,
        service_id: UUID | None = None,
        anomaly_type: str | None = None,
        start_time: datetime | None = None,
        end_time: datetime | None = None,
    ) -> None:
        self.severity = severity
        self.service_id = service_id
        self.anomaly_type = anomaly_type
        self.start_time = start_time
        self.end_time = end_time


class AnomalyRepository:
    def __init__(self, db: Session) -> None:
        self._db = db

    def _apply(self, stmt, project_id: UUID, filters: AnomalyFilters):
        stmt = stmt.where(Anomaly.project_id == project_id)
        if filters.severity:
            stmt = stmt.where(Anomaly.severity == filters.severity.upper())
        if filters.service_id:
            stmt = stmt.where(Anomaly.service_id == filters.service_id)
        if filters.anomaly_type:
            stmt = stmt.where(Anomaly.anomaly_type == filters.anomaly_type)
        if filters.start_time:
            stmt = stmt.where(Anomaly.start_time >= filters.start_time)
        if filters.end_time:
            stmt = stmt.where(Anomaly.end_time <= filters.end_time)
        return stmt

    def search(
        self,
        project_id: UUID,
        filters: AnomalyFilters,
        *,
        skip: int,
        limit: int,
    ) -> tuple[list[Anomaly], int, dict[str, int]]:
        count_stmt = self._apply(select(func.count()).select_from(Anomaly), project_id, filters)
        total = self._db.scalar(count_stmt) or 0

        rows_stmt = (
            self._apply(select(Anomaly), project_id, filters)
            .order_by(Anomaly.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        items = list(self._db.scalars(rows_stmt).all())

        severity_stmt = (
            select(Anomaly.severity, func.count())
            .where(Anomaly.project_id == project_id)
            .group_by(Anomaly.severity)
        )
        severity_counts = {row[0]: int(row[1]) for row in self._db.execute(severity_stmt).all()}
        return items, int(total), severity_counts

    def get_in_project(self, anomaly_id: UUID, project_id: UUID) -> Anomaly | None:
        stmt = select(Anomaly).where(Anomaly.id == anomaly_id, Anomaly.project_id == project_id)
        return self._db.scalars(stmt).first()