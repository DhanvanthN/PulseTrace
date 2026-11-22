from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.anomaly import Anomaly
from app.models.log import Log
from app.models.log_cluster import LogCluster
from app.models.service import Service


def assert_service_in_project(db: Session, service_id: UUID | None, project_id: UUID) -> None:
    if service_id is None:
        return
    found = db.scalar(
        select(Service.id).where(Service.id == service_id, Service.project_id == project_id)
    )
    if not found:
        raise ValueError("service_id does not belong to this project")


def assert_anomaly_in_project(db: Session, anomaly_id: UUID, project_id: UUID) -> Anomaly:
    row = db.scalar(select(Anomaly).where(Anomaly.id == anomaly_id, Anomaly.project_id == project_id))
    if row is None:
        raise ValueError("anomaly does not belong to this project")
    return row


def assert_log_in_project(db: Session, log_id: UUID, project_id: UUID) -> Log:
    row = db.scalar(select(Log).where(Log.id == log_id, Log.project_id == project_id))
    if row is None:
        raise ValueError("log does not belong to this project")
    return row


def assert_cluster_in_project(db: Session, cluster_id: UUID, project_id: UUID) -> LogCluster:
    row = db.scalar(select(LogCluster).where(LogCluster.id == cluster_id, LogCluster.project_id == project_id))
    if row is None:
        raise ValueError("cluster does not belong to this project")
    return row