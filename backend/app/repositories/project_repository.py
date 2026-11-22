from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.project import Project


class ProjectRepository:
    def __init__(self, db: Session) -> None:
        self._db = db

    def get_owned(self, project_id: UUID, owner_id: UUID) -> Project | None:
        stmt = select(Project).where(Project.id == project_id, Project.owner_id == owner_id)
        return self._db.scalars(stmt).first()

    def list_owned(
        self,
        owner_id: UUID,
        *,
        skip: int = 0,
        limit: int = 20,
    ) -> tuple[list[Project], int]:
        total = (
            self._db.scalar(
                select(func.count()).select_from(Project).where(Project.owner_id == owner_id)
            )
            or 0
        )
        base = select(Project).where(Project.owner_id == owner_id)
        items = self._db.scalars(
            base.order_by(Project.created_at.desc()).offset(skip).limit(limit)
        ).all()
        return list(items), int(total)

    def create(
        self,
        *,
        owner_id: UUID,
        name: str,
        description: str | None,
        environment: str,
    ) -> Project:
        project = Project(
            owner_id=owner_id,
            name=name.strip(),
            description=description,
            environment=environment,
        )
        self._db.add(project)
        self._db.flush()
        return project

    def update(
        self,
        project: Project,
        *,
        name: str | None = None,
        description: str | None = None,
        environment: str | None = None,
    ) -> Project:
        if name is not None:
            project.name = name.strip()
        if description is not None:
            project.description = description
        if environment is not None:
            project.environment = environment
        self._db.flush()
        return project

    def delete(self, project: Project) -> None:
        self._db.delete(project)
        self._db.flush()