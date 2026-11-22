from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


class AnalysisRunRequest(BaseModel):
    service_id: UUID | None = None


class AnalysisRunResponse(BaseModel):
    status: str
    message: str
    anomalies_created: int = 0
    anomalies_detected: int = 0
    clusters_created: int = 0
    cluster_memberships: int = 0
    noise_logs: int = 0
    logs_analyzed: int = 0
    window_start: str | None = None
    window_end: str | None = None
    methods: list[str] = Field(default_factory=list)


class AnomalyResponse(BaseModel):
    id: UUID
    project_id: UUID
    service_id: UUID | None
    anomaly_type: str
    severity: str
    score: float
    description: str
    start_time: datetime
    end_time: datetime
    detection_method: str
    evidence: dict[str, Any]
    created_at: datetime

    model_config = {"from_attributes": True}


class AnomalyListResponse(BaseModel):
    items: list[AnomalyResponse]
    total: int
    skip: int
    limit: int
    severity_counts: dict[str, int]


class LogClusterResponse(BaseModel):
    id: UUID
    project_id: UUID
    cluster_label: str
    description: str
    representative_message: str
    algorithm: str
    log_count: int
    first_seen: datetime | None
    last_seen: datetime | None
    created_at: datetime

    model_config = {"from_attributes": True}


class LogClusterDetailResponse(LogClusterResponse):
    logs: list[dict[str, Any]] = Field(default_factory=list)


class LogClusterListResponse(BaseModel):
    items: list[LogClusterResponse]
    total: int
    skip: int
    limit: int