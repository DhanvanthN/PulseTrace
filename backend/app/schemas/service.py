from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class ServiceCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    service_type: str = Field(default="api", max_length=64)
    environment: str = Field(default="production", max_length=64)
    description: str | None = Field(default=None, max_length=2000)


class ServiceResponse(BaseModel):
    id: UUID
    project_id: UUID
    name: str
    service_type: str
    environment: str
    description: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


class ServiceListResponse(BaseModel):
    items: list[ServiceResponse]


class ServiceDependencyCreateRequest(BaseModel):
    upstream_service_id: UUID
    downstream_service_id: UUID


class ServiceDependencyResponse(BaseModel):
    id: UUID
    upstream_service_id: UUID
    downstream_service_id: UUID
    created_at: datetime

    model_config = {"from_attributes": True}