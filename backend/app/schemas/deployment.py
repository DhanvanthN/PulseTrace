from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


class DeploymentCreateRequest(BaseModel):
    service_id: UUID | None = None
    version: str = Field(min_length=1, max_length=128)
    change_type: str = Field(default="release", max_length=64)
    description: str = ""
    configuration_diff: dict[str, Any] = Field(default_factory=dict)
    deployed_at: datetime | None = None


class DeploymentResponse(BaseModel):
    id: UUID
    project_id: UUID
    service_id: UUID | None
    version: str
    change_type: str
    description: str
    configuration_diff: dict[str, Any]
    deployed_at: datetime
    created_at: datetime

    model_config = {"from_attributes": True}


class DeploymentListResponse(BaseModel):
    items: list[DeploymentResponse]
    total: int
    skip: int
    limit: int