import os

import pytest

from app.core.config import Settings
from app.core.production import production_error_message, validate_production_settings


def test_production_rejects_short_jwt() -> None:
    settings = Settings(
        APP_ENV="production",
        JWT_SECRET_KEY="too-short",
        DATABASE_URL="postgresql+psycopg://u:p@localhost/db",
    )
    with pytest.raises(RuntimeError, match="JWT_SECRET_KEY"):
        validate_production_settings(settings)


def test_production_rejects_placeholder_jwt() -> None:
    settings = Settings(
        APP_ENV="production",
        JWT_SECRET_KEY="replace_with_a_long_random_secret_value_12345",
        DATABASE_URL="postgresql+psycopg://u:secret@localhost/db",
    )
    with pytest.raises(RuntimeError, match="placeholder"):
        validate_production_settings(settings)


def test_production_error_message_hides_details() -> None:
    assert "internal" in production_error_message(500).lower()


def test_app_starts_in_test_env(client) -> None:
    response = client.get("/api/v1/health")
    assert response.status_code == 200