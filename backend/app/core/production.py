"""Production startup checks — fail fast on unsafe configuration."""

from __future__ import annotations

import logging
import re

from app.core.config import Settings

logger = logging.getLogger(__name__)

_INSECURE_JWT_MARKERS = (
    "dev-only",
    "change_me",
    "replace_with",
    "test-jwt",
    "your-secret",
    "secret-key",
)


def validate_production_settings(settings: Settings) -> None:
    if not settings.is_production:
        return

    secret = settings.jwt_secret_key.strip()
    lowered = secret.lower()
    if len(secret) < 32:
        raise RuntimeError("JWT_SECRET_KEY must be at least 32 characters in production")
    if any(marker in lowered for marker in _INSECURE_JWT_MARKERS):
        raise RuntimeError("JWT_SECRET_KEY appears to be a development placeholder")

    if not settings.auth_cookie_secure:
        logger.warning("AUTH_COOKIE_SECURE=false in production — enable for HTTPS deployments")

    if "localhost" in settings.cors_origins_env and len(settings.backend_cors_origins) <= 2:
        logger.warning(
            "BACKEND_CORS_ORIGINS still includes localhost-only origins in production"
        )

    db_url = settings.database_url
    if re.search(r"://[^:]+:change_me", db_url, re.IGNORECASE):
        raise RuntimeError("DATABASE_URL uses a placeholder password in production")


def production_error_message(status_code: int) -> str:
    if status_code >= 500:
        return "An internal error occurred"
    return "Request could not be completed"