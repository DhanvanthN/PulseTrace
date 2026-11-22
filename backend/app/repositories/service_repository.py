from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.service import Service


class ServiceRepository:
    def __init__(self, db: Session) -> None:
        self._db = db

    def get_in_project(self, service_id: UUID, project_id: UUID) -> Service | None:
        stmt = select(Service).where(Service.id == service_id, Service.project_id == project_id)
        return self._db.scalars(stmt).first()

    def name_map_for_project(self, project_id: UUID) -> dict[str, UUID]:
        stmt = select(Service).where(Service.project_id == project_id)
        services = self._db.scalars(stmt).all()
        return {service.name.strip().lower(): service.id for service in services}