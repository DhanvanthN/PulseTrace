import logging
from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_owned_project
from app.db.session import get_db
from app.models.project import Project
from app.models.user import User
from app.modules.analysis.runner import run_project_analysis
from app.repositories.anomaly_repository import AnomalyFilters, AnomalyRepository
from app.repositories.cluster_repository import ClusterRepository
from app.repositories.service_repository import ServiceRepository
from app.schemas.analysis import (
    AnalysisRunRequest,
    AnalysisRunResponse,
    AnomalyListResponse,
    AnomalyResponse,
    LogClusterDetailResponse,
    LogClusterListResponse,
    LogClusterResponse,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/projects/{project_id}", tags=["analysis"])


@router.post("/analysis/run", response_model=AnalysisRunResponse)
def run_analysis(
    project_id: UUID,
    payload: AnalysisRunRequest,
    project: Project = Depends(get_owned_project),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> AnalysisRunResponse:
    if project.id != project_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")

    if payload.service_id is not None:
        service = ServiceRepository(db).get_in_project(payload.service_id, project.id)
        if service is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="service_id does not belong to this project",
            )

    try:
        result = run_project_analysis(
            db,
            project_id=project.id,
            service_id=payload.service_id,
        )
    except Exception as exc:
        logger.exception("Analysis failed project_id=%s user_id=%s", project.id, current_user.id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Analysis execution failed",
        ) from exc

    return AnalysisRunResponse.model_validate(result)


@router.get("/anomalies", response_model=AnomalyListResponse)
def list_anomalies(
    project_id: UUID,
    severity: str | None = Query(default=None),
    service_id: UUID | None = Query(default=None),
    anomaly_type: str | None = Query(default=None),
    start_time: datetime | None = Query(default=None),
    end_time: datetime | None = Query(default=None),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=100),
    project: Project = Depends(get_owned_project),
    db: Session = Depends(get_db),
) -> AnomalyListResponse:
    if project.id != project_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")

    filters = AnomalyFilters(
        severity=severity,
        service_id=service_id,
        anomaly_type=anomaly_type,
        start_time=start_time,
        end_time=end_time,
    )
    items, total, severity_counts = AnomalyRepository(db).search(
        project.id,
        filters,
        skip=skip,
        limit=limit,
    )
    return AnomalyListResponse(
        items=[AnomalyResponse.model_validate(item) for item in items],
        total=total,
        skip=skip,
        limit=limit,
        severity_counts=severity_counts,
    )


@router.get("/anomalies/{anomaly_id}", response_model=AnomalyResponse)
def get_anomaly(
    project_id: UUID,
    anomaly_id: UUID,
    project: Project = Depends(get_owned_project),
    db: Session = Depends(get_db),
) -> AnomalyResponse:
    if project.id != project_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")

    anomaly = AnomalyRepository(db).get_in_project(anomaly_id, project.id)
    if anomaly is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Anomaly not found")
    return AnomalyResponse.model_validate(anomaly)


@router.get("/clusters", response_model=LogClusterListResponse)
def list_clusters(
    project_id: UUID,
    search: str | None = Query(default=None, max_length=200),
    min_log_count: int = Query(default=1, ge=1),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=100),
    project: Project = Depends(get_owned_project),
    db: Session = Depends(get_db),
) -> LogClusterListResponse:
    if project.id != project_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")

    items, total = ClusterRepository(db).search(
        project.id,
        search=search,
        min_log_count=min_log_count,
        skip=skip,
        limit=limit,
    )
    return LogClusterListResponse(
        items=[LogClusterResponse.model_validate(item) for item in items],
        total=total,
        skip=skip,
        limit=limit,
    )


@router.get("/clusters/{cluster_id}", response_model=LogClusterDetailResponse)
def get_cluster(
    project_id: UUID,
    cluster_id: UUID,
    project: Project = Depends(get_owned_project),
    db: Session = Depends(get_db),
) -> LogClusterDetailResponse:
    if project.id != project_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")

    cluster = ClusterRepository(db).get_in_project(cluster_id, project.id)
    if cluster is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cluster not found")

    logs = ClusterRepository(db).cluster_logs(cluster, limit=50)
    payload = LogClusterDetailResponse.model_validate(cluster)
    payload.logs = [
        {
            "id": str(log.id),
            "timestamp": log.timestamp.isoformat(),
            "level": log.level,
            "message": log.message,
            "service_id": str(log.service_id) if log.service_id else None,
        }
        for log in logs
    ]
    return payload