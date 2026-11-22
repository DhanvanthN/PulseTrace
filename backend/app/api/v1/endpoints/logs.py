import logging
from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_owned_project
from app.core.config import get_settings
from app.db.session import get_db
from app.models.project import Project
from app.models.user import User
from app.modules.logs.processor import process_log_batch
from app.modules.logs.storage import detect_format, resolve_storage_root, sanitize_filename, save_upload_stream
from app.repositories.log_batch_repository import LogBatchRepository
from app.repositories.log_repository import LogRepository, LogSearchFilters
from app.repositories.service_repository import ServiceRepository
from app.schemas.log import (
    LogBatchListResponse,
    LogBatchResponse,
    LogListResponse,
    LogResponse,
    log_to_response,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/projects/{project_id}/logs", tags=["logs"])


@router.post("/upload", response_model=LogBatchResponse, status_code=status.HTTP_201_CREATED)
async def upload_logs(
    project_id: UUID,
    file: UploadFile = File(...),
    service_id: UUID | None = Form(default=None),
    db: Session = Depends(get_db),
    project: Project = Depends(get_owned_project),
    current_user: User = Depends(get_current_user),
) -> LogBatchResponse:
    if project.id != project_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")

    if service_id is not None:
        service = ServiceRepository(db).get_in_project(service_id, project.id)
        if service is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="service_id does not belong to this project",
            )

    batch_repo = LogBatchRepository(db)
    original_name = sanitize_filename(file.filename or "upload.log")
    batch = batch_repo.create(
        project_id=project.id,
        uploaded_by=current_user.id,
        filename=original_name,
        file_format=detect_format(original_name),
        storage_path="",
    )

    try:
        file_path, file_format, _size = await save_upload_stream(
            file,
            project_id=project.id,
            batch_id=batch.id,
        )
        batch.file_format = file_format
        batch.storage_path = str(
            file_path.relative_to(resolve_storage_root()).as_posix()
        )
        db.flush()

        process_log_batch(
            db,
            batch=batch,
            file_path=file_path,
            forced_service_id=service_id,
        )
        db.commit()
    except HTTPException:
        db.rollback()
        raise
    except Exception as exc:
        db.rollback()
        logger.exception("Upload processing failed project_id=%s", project.id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Log processing failed",
        ) from exc

    db.refresh(batch)
    return LogBatchResponse.model_validate(batch)


@router.get("", response_model=LogListResponse)
def search_logs(
    project_id: UUID,
    start_time: datetime | None = Query(default=None),
    end_time: datetime | None = Query(default=None),
    level: str | None = Query(default=None),
    service_id: UUID | None = Query(default=None),
    trace_id: str | None = Query(default=None),
    request_id: str | None = Query(default=None),
    keyword: str | None = Query(default=None, max_length=200),
    batch_id: UUID | None = Query(default=None),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=200),
    project: Project = Depends(get_owned_project),
    db: Session = Depends(get_db),
) -> LogListResponse:
    if project.id != project_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")

    filters = LogSearchFilters(
        start_time=start_time,
        end_time=end_time,
        level=level,
        service_id=service_id,
        trace_id=trace_id,
        request_id=request_id,
        keyword=keyword,
        batch_id=batch_id,
    )
    items, total = LogRepository(db).search(project.id, filters, skip=skip, limit=limit)
    return LogListResponse(
        items=[log_to_response(item) for item in items],
        total=total,
        skip=skip,
        limit=limit,
    )


@router.get("/batches", response_model=LogBatchListResponse)
def list_batches(
    project_id: UUID,
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=100),
    project: Project = Depends(get_owned_project),
    db: Session = Depends(get_db),
) -> LogBatchListResponse:
    if project.id != project_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")

    items, total = LogBatchRepository(db).list_for_project(project.id, skip=skip, limit=limit)
    return LogBatchListResponse(
        items=[LogBatchResponse.model_validate(item) for item in items],
        total=total,
        skip=skip,
        limit=limit,
    )


@router.get("/batches/{batch_id}", response_model=LogBatchResponse)
def get_batch(
    project_id: UUID,
    batch_id: UUID,
    project: Project = Depends(get_owned_project),
    db: Session = Depends(get_db),
) -> LogBatchResponse:
    if project.id != project_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")

    batch = LogBatchRepository(db).get_in_project(batch_id, project.id)
    if batch is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Batch not found")
    return LogBatchResponse.model_validate(batch)


@router.get("/{log_id}", response_model=LogResponse)
def get_log(
    project_id: UUID,
    log_id: UUID,
    project: Project = Depends(get_owned_project),
    db: Session = Depends(get_db),
) -> LogResponse:
    if project.id != project_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")

    log = LogRepository(db).get_in_project(log_id, project.id)
    if log is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Log not found")
    return log_to_response(log)