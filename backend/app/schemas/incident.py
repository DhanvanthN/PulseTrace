from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field, field_validator

from app.models.incident import INCIDENT_SEVERITIES, INCIDENT_STATUSES


class IncidentCreateRequest(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    description: str = Field(default="")
    severity: str = "MEDIUM"
    status: str = "OPEN"
    primary_service_id: UUID | None = None
    started_at: datetime | None = None

    @field_validator("severity")
    @classmethod
    def validate_severity(cls, value: str) -> str:
        upper = value.upper()
        if upper not in INCIDENT_SEVERITIES:
            raise ValueError("Invalid severity")
        return upper

    @field_validator("status")
    @classmethod
    def validate_status(cls, value: str) -> str:
        upper = value.upper()
        if upper not in INCIDENT_STATUSES:
            raise ValueError("Invalid status")
        return upper


class IncidentUpdateRequest(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = None
    severity: str | None = None
    status: str | None = None
    primary_service_id: UUID | None = None

    @field_validator("severity")
    @classmethod
    def validate_severity(cls, value: str | None) -> str | None:
        if value is None:
            return None
        upper = value.upper()
        if upper not in INCIDENT_SEVERITIES:
            raise ValueError("Invalid severity")
        return upper

    @field_validator("status")
    @classmethod
    def validate_status(cls, value: str | None) -> str | None:
        if value is None:
            return None
        upper = value.upper()
        if upper not in INCIDENT_STATUSES:
            raise ValueError("Invalid status")
        return upper


class IncidentResponse(BaseModel):
    id: UUID
    project_id: UUID
    primary_service_id: UUID | None
    title: str
    description: str
    severity: str
    status: str
    started_at: datetime
    last_activity_at: datetime
    resolved_at: datetime | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class IncidentListResponse(BaseModel):
    items: list[IncidentResponse]
    total: int
    skip: int
    limit: int
    status_counts: dict[str, int]
    severity_counts: dict[str, int]


class IncidentEventResponse(BaseModel):
    id: UUID
    incident_id: UUID
    event_type: str
    description: str
    event_timestamp: datetime
    metadata: dict[str, Any]
    created_at: datetime

    model_config = {"from_attributes": True}

    @classmethod
    def from_model(cls, event) -> "IncidentEventResponse":
        return cls(
            id=event.id,
            incident_id=event.incident_id,
            event_type=event.event_type,
            description=event.description,
            event_timestamp=event.event_timestamp,
            metadata=event.event_metadata,
            created_at=event.created_at,
        )


class IncidentEvidenceResponse(BaseModel):
    id: UUID
    incident_id: UUID
    log_id: UUID | None
    anomaly_id: UUID | None
    cluster_id: UUID | None
    evidence_type: str
    explanation: str
    created_at: datetime

    model_config = {"from_attributes": True}


class IncidentTimelineResponse(BaseModel):
    items: list[IncidentEventResponse]


class IncidentEvidenceListResponse(BaseModel):
    items: list[IncidentEvidenceResponse]


class IncidentNoteRequest(BaseModel):
    content: str = Field(min_length=1, max_length=4000)


class IncidentCorrelateResponse(BaseModel):
    status: str
    message: str
    incidents_created: int = 0
    incidents_updated: int = 0
    anomalies_processed: int = 0


class IncidentDetailResponse(IncidentResponse):
    events_count: int = 0
    evidence_count: int = 0