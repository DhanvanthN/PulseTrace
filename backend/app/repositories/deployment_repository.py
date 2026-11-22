from datetime import datetime
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.deployment import Deployment


class DeploymentRepository:
    def __init__(self, db: Session) -> None:
        self._db = db

    def create(self, deployment: Deployment) -> Deployment:
        self._db.add(deployment)
        return deployment

    def list_project(
        self,
        project_id: UUID,
        *,
        service_id: UUID | None,
        start_time: datetime | None,
        end_time: datetime | None,
        skip: int,
        limit: int,
    ) -> tuple[list[Deployment], int]:
        stmt = select(Deployment).where(Deployment.project_id == project_id)
        if service_id:
            stmt = stmt.where(Deployment.service_id == service_id)
        if start_time:
            stmt = stmt.where(Deployment.deployed_at >= start_time)
        if end_time:
            stmt = stmt.where(Deployment.deployed_at <= end_time)

        total = self._db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
        items = list(
            self._db.scalars(
                stmt.order_by(Deployment.deployed_at.desc()).offset(skip).limit(limit)
            ).all()
        )
        return items, int(total)

    def get_in_project(self, deployment_id: UUID, project_id: UUID) -> Deployment | None:
        stmt = select(Deployment).where(Deployment.id == deployment_id, Deployment.project_id == project_id)
        return self._db.scalars(stmt).first()