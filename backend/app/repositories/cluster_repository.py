from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.models.log import Log
from app.models.log_cluster import LogCluster, LogClusterMembership


class ClusterRepository:
    def __init__(self, db: Session) -> None:
        self._db = db

    def search(
        self,
        project_id: UUID,
        *,
        search: str | None,
        min_log_count: int,
        skip: int,
        limit: int,
    ) -> tuple[list[LogCluster], int]:
        stmt = select(LogCluster).where(
            LogCluster.project_id == project_id,
            LogCluster.log_count >= min_log_count,
        )
        if search:
            escaped = search.replace("%", "\\%")
            stmt = stmt.where(LogCluster.representative_message.ilike(f"%{escaped}%", escape="\\"))

        count_stmt = select(func.count()).select_from(LogCluster).where(
            LogCluster.project_id == project_id,
            LogCluster.log_count >= min_log_count,
        )
        if search:
            escaped = search.replace("%", "\\%")
            count_stmt = count_stmt.where(
                LogCluster.representative_message.ilike(f"%{escaped}%", escape="\\")
            )
        total = self._db.scalar(count_stmt) or 0
        items = self._db.scalars(
            stmt.order_by(LogCluster.log_count.desc(), LogCluster.created_at.desc())
            .offset(skip)
            .limit(limit)
        ).all()
        return list(items), int(total)

    def get_in_project(self, cluster_id: UUID, project_id: UUID) -> LogCluster | None:
        stmt = (
            select(LogCluster)
            .where(LogCluster.id == cluster_id, LogCluster.project_id == project_id)
            .options(selectinload(LogCluster.memberships).selectinload(LogClusterMembership.log))
        )
        return self._db.scalars(stmt).first()

    def cluster_logs(self, cluster: LogCluster, *, limit: int = 50) -> list[Log]:
        stmt = (
            select(Log)
            .join(LogClusterMembership, LogClusterMembership.log_id == Log.id)
            .where(LogClusterMembership.cluster_id == cluster.id)
            .order_by(Log.timestamp.desc())
            .limit(limit)
        )
        return list(self._db.scalars(stmt).all())