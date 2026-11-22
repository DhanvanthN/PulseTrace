import logging

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.v1.router import api_v1_router
from app.core.config import get_settings
from app.core.logging import setup_logging
from app.core.production import production_error_message, validate_production_settings
from app.middleware.csrf import CsrfOriginMiddleware
from app.middleware.rate_limit import RateLimitMiddleware
from app.middleware.security_headers import SecurityHeadersMiddleware
from app.schemas.health import HealthResponse

logger = logging.getLogger(__name__)


def create_app() -> FastAPI:
    setup_logging()
    settings = get_settings()
    validate_production_settings(settings)

    application = FastAPI(
        title=settings.app_name,
        version="0.1.0",
        docs_url="/docs" if settings.app_env != "production" else None,
        redoc_url="/redoc" if settings.app_env != "production" else None,
    )

    application.add_middleware(SecurityHeadersMiddleware)
    application.add_middleware(CsrfOriginMiddleware)
    application.add_middleware(RateLimitMiddleware)
    application.add_middleware(
        CORSMiddleware,
        allow_origins=settings.backend_cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @application.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        return JSONResponse(status_code=422, content={"detail": exc.errors()})

    @application.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        if isinstance(exc, HTTPException):
            return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})
        logger.exception("Unhandled error path=%s", request.url.path)
        detail = (
            production_error_message(500)
            if settings.is_production
            else str(exc)
        )
        return JSONResponse(status_code=500, content={"detail": detail})

    @application.get("/health", response_model=HealthResponse, tags=["health"])
    def root_health() -> HealthResponse:
        return HealthResponse(status="ok", service=settings.app_name)

    application.include_router(api_v1_router, prefix="/api/v1")

    logger.info("PulseTrace API initialized (env=%s)", settings.app_env)
    return application


app = create_app()