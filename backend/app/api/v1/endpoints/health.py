from fastapi import APIRouter

from app.core.config import get_settings
from app.db.session import check_database_connectivity
from app.schemas.health import DatabaseHealthResponse, HealthResponse

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
def api_health() -> HealthResponse:
    settings = get_settings()
    return HealthResponse(status="ok", service=settings.app_name)


@router.get("/health/database", response_model=DatabaseHealthResponse)
def database_health() -> DatabaseHealthResponse:
    connected, detail = check_database_connectivity()
    if connected:
        return DatabaseHealthResponse(
            status="ok",
            database="connected",
            detail=detail,
        )
    return DatabaseHealthResponse(
        status="error",
        database="disconnected",
        detail=detail,
    )