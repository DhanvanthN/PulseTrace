from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.api.deps import get_owned_project
from app.db.session import get_db
from app.models.project import Project
from app.models.service import Service
from app.models.service_dependency import ServiceDependency
from app.repositories.service_repository import ServiceRepository
from app.schemas.service import (
    ServiceCreateRequest,
    ServiceDependencyCreateRequest,
    ServiceDependencyResponse,
    ServiceListResponse,
    ServiceResponse,
)

router = APIRouter(prefix="/projects/{project_id}/services", tags=["services"])


@router.get("", response_model=ServiceListResponse)
def list_services(
    project_id: UUID,
    project: Project = Depends(get_owned_project),
    db: Session = Depends(get_db),
) -> ServiceListResponse:
    if project.id != project_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")

    from sqlalchemy import select

    items = db.scalars(select(Service).where(Service.project_id == project.id).order_by(Service.name)).all()
    return ServiceListResponse(items=[ServiceResponse.model_validate(item) for item in items])


@router.post("", response_model=ServiceResponse, status_code=status.HTTP_201_CREATED)
def create_service(
    project_id: UUID,
    payload: ServiceCreateRequest,
    project: Project = Depends(get_owned_project),
    db: Session = Depends(get_db),
) -> ServiceResponse:
    if project.id != project_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")

    service = Service(
        project_id=project.id,
        name=payload.name.strip(),
        service_type=payload.service_type,
        environment=payload.environment,
        description=payload.description,
    )
    db.add(service)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Service name already exists in this project",
        ) from exc
    db.refresh(service)
    return ServiceResponse.model_validate(service)


@router.post("/dependencies", response_model=ServiceDependencyResponse, status_code=status.HTTP_201_CREATED)
def create_service_dependency(
    project_id: UUID,
    payload: ServiceDependencyCreateRequest,
    project: Project = Depends(get_owned_project),
    db: Session = Depends(get_db),
) -> ServiceDependencyResponse:
    if project.id != project_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    repo = ServiceRepository(db)
    upstream = repo.get_in_project(payload.upstream_service_id, project.id)
    downstream = repo.get_in_project(payload.downstream_service_id, project.id)
    if upstream is None or downstream is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid service scope")
    if payload.upstream_service_id == payload.downstream_service_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Service cannot depend on itself")

    row = ServiceDependency(
        upstream_service_id=payload.upstream_service_id,
        downstream_service_id=payload.downstream_service_id,
    )
    db.add(row)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Dependency already exists") from exc
    db.refresh(row)
    return ServiceDependencyResponse.model_validate(row)