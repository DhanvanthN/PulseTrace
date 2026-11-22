from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


class LogBatchResponse(BaseModel):
    id: UUID
    project_id: UUID
    uploaded_by: UUID | None
    filename: str
    file_format: str
    status: str
    total_records: int
    processed_records: int
    failed_records: int
    error_summary: str | None
    created_at: datetime
    completed_at: datetime | None

    model_config = {"from_attributes": True}


class LogBatchListResponse(BaseModel):
    items: list[LogBatchResponse]
    total: int
    skip: int
    limit: int


class LogResponse(BaseModel):
    id: UUID
    project_id: UUID
    service_id: UUID | None
    service_name: str | None = None
    batch_id: UUID
    timestamp: datetime
    level: str
    message: str
    trace_id: str | None
    request_id: str | None
    metadata: dict[str, Any] = Field(default_factory=dict)
    fingerprint: str
    created_at: datetime

    model_config = {"from_attributes": True}


class LogListResponse(BaseModel):
    items: list[LogResponse]
    total: int
    skip: int
    limit: int


def log_to_response(log) -> LogResponse:  # noqa: ANN001
    service_name = log.service.name if getattr(log, "service", None) else None
    if not service_name and isinstance(log.log_metadata, dict):
        service_name = log.log_metadata.get("original_service_name")

    return LogResponse(
        id=log.id,
        project_id=log.project_id,
        service_id=log.service_id,
        service_name=service_name,
        batch_id=log.batch_id,
        timestamp=log.timestamp,
        level=log.level,
        message=log.message,
        trace_id=log.trace_id,
        request_id=log.request_id,
        metadata=log.log_metadata or {},
        fingerprint=log.fingerprint,
        created_at=log.created_at,
    )