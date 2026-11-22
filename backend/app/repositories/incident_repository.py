from datetime import datetime
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.models.incident import Incident, IncidentEvent, IncidentEvidence


class IncidentFilters:
    def __init__(
        self,
        *,
        status: str | None = None,
        severity: str | None = None,
        service_id: UUID | None = None,
        search: str | None = None,
        start_time: datetime | None = None,
        end_time: datetime | None = None,
    ) -> None:
        self.status = status
        self.severity = severity
        self.service_id = service_id
        self.search = search
        self.start_time = start_time
        self.end_time = end_time


class IncidentRepository:
    def __init__(self, db: Session) -> None:
        self._db = db

    def _apply(self, stmt, project_id: UUID, filters: IncidentFilters):
        stmt = stmt.where(Incident.project_id == project_id)
        if filters.status:
            stmt = stmt.where(Incident.status == filters.status.upper())
        if filters.severity:
            stmt = stmt.where(Incident.severity == filters.severity.upper())
        if filters.service_id:
            stmt = stmt.where(Incident.primary_service_id == filters.service_id)
        if filters.search:
            escaped = filters.search.replace("%", "\\%")
            stmt = stmt.where(
                Incident.title.ilike(f"%{escaped}%", escape="\\")
                | Incident.description.ilike(f"%{escaped}%", escape="\\")
            )
        if filters.start_time:
            stmt = stmt.where(Incident.started_at >= filters.start_time)
        if filters.end_time:
            stmt = stmt.where(Incident.last_activity_at <= filters.end_time)
        return stmt

    def search(
        self,
        project_id: UUID,
        filters: IncidentFilters,
        *,
        skip: int,
        limit: int,
    ) -> tuple[list[Incident], int, dict[str, int], dict[str, int]]:
        base = self._apply(select(Incident), project_id, filters)
        total = self._db.scalar(select(func.count()).select_from(base.subquery())) or 0
        items = list(
            self._db.scalars(
                base.order_by(Incident.last_activity_at.desc()).offset(skip).limit(limit)
            ).all()
        )

        status_stmt = (
            select(Incident.status, func.count())
            .where(Incident.project_id == project_id)
            .group_by(Incident.status)
        )
        severity_stmt = (
            select(Incident.severity, func.count())
            .where(Incident.project_id == project_id)
            .group_by(Incident.severity)
        )
        status_counts = {row[0]: int(row[1]) for row in self._db.execute(status_stmt).all()}
        severity_counts = {row[0]: int(row[1]) for row in self._db.execute(severity_stmt).all()}
        return items, int(total), status_counts, severity_counts

    def get_in_project(self, incident_id: UUID, project_id: UUID) -> Incident | None:
        stmt = (
            select(Incident)
            .where(Incident.id == incident_id, Incident.project_id == project_id)
            .options(
                selectinload(Incident.events),
                selectinload(Incident.evidence_items),
            )
        )
        return self._db.scalars(stmt).first()

    def timeline(self, incident_id: UUID) -> list[IncidentEvent]:
        stmt = (
            select(IncidentEvent)
            .where(IncidentEvent.incident_id == incident_id)
            .order_by(IncidentEvent.event_timestamp.asc(), IncidentEvent.created_at.asc())
        )
        return list(self._db.scalars(stmt).all())

    def evidence(self, incident_id: UUID) -> list[IncidentEvidence]:
        stmt = select(IncidentEvidence).where(IncidentEvidence.incident_id == incident_id)
        return list(self._db.scalars(stmt).all())