from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.log_batch import LogBatch


class LogBatchRepository:
    def __init__(self, db: Session) -> None:
        self._db = db

    def create(
        self,
        *,
        project_id: UUID,
        uploaded_by: UUID,
        filename: str,
        file_format: str,
        storage_path: str,
    ) -> LogBatch:
        batch = LogBatch(
            project_id=project_id,
            uploaded_by=uploaded_by,
            filename=filename,
            file_format=file_format,
            storage_path=storage_path,
            status="pending",
        )
        self._db.add(batch)
        self._db.flush()
        return batch

    def get_in_project(self, batch_id: UUID, project_id: UUID) -> LogBatch | None:
        stmt = select(LogBatch).where(LogBatch.id == batch_id, LogBatch.project_id == project_id)
        return self._db.scalars(stmt).first()

    def list_for_project(
        self,
        project_id: UUID,
        *,
        skip: int = 0,
        limit: int = 20,
    ) -> tuple[list[LogBatch], int]:
        count = self._db.scalar(
            select(func.count()).select_from(LogBatch).where(LogBatch.project_id == project_id)
        ) or 0
        stmt = (
            select(LogBatch)
            .where(LogBatch.project_id == project_id)
            .order_by(LogBatch.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        return list(self._db.scalars(stmt).all()), int(count)