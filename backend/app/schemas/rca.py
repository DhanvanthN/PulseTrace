from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


class RCAInvestigateResponse(BaseModel):
    status: str
    message: str
    investigation_id: str | None = None
    version: int = 0
    candidate_count: int = 0
    top_candidate_title: str | None = None
    top_confidence_score: float = 0.0


class RootCauseCandidateResponse(BaseModel):
    id: UUID
    investigation_id: UUID
    incident_id: UUID
    service_id: UUID | None
    deployment_id: UUID | None
    cause_type: str
    title: str
    explanation: str
    confidence_score: float
    ranking: int
    evidence_summary: dict[str, Any]
    supporting_evidence_count: int
    contradicting_evidence_count: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class RootCauseListResponse(BaseModel):
    investigation_id: UUID | None
    version: int | None
    status: str | None
    items: list[RootCauseCandidateResponse]
    score_note: str = Field(
        default="Confidence scores are evidence strength (0–100), not calibrated probabilities."
    )


class InvestigationReportResponse(BaseModel):
    report: dict[str, Any]
    markdown: str