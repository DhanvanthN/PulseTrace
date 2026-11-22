import os
from collections.abc import Generator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

# Test defaults before app import loads settings cache.
os.environ.setdefault("APP_ENV", "test")
os.environ.setdefault("LOG_LEVEL", "WARNING")
os.environ.setdefault("JWT_SECRET_KEY", "test-jwt-secret-key-do-not-use-in-production")
os.environ.setdefault("LOG_STORAGE_PATH", str(Path(__file__).resolve().parents[1] / "data" / "test_uploads"))

from app.core.config import get_settings
from app.main import create_app


@pytest.fixture(scope="session")
def database_url() -> str:
    return os.environ.get(
        "DATABASE_URL",
        "postgresql+psycopg://pulsetrace:change_me_in_local_env@localhost:5433/pulsetrace",
    )


@pytest.fixture(scope="session", autouse=True)
def configure_test_settings(database_url: str) -> Generator[None, None, None]:
    os.environ["DATABASE_URL"] = database_url
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


@pytest.fixture
def client() -> Generator[TestClient, None, None]:
    application = create_app()
    with TestClient(application) as test_client:
        yield test_client