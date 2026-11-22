import uuid
from datetime import datetime, timedelta, timezone

import jwt
import pytest
from fastapi.testclient import TestClient

from app.core.config import get_settings
from app.core.security import hash_password, verify_password


def _unique_email() -> str:
    return f"user-{uuid.uuid4().hex[:12]}@example.com"


def _register(client: TestClient, email: str | None = None, password: str = "SecurePass1") -> dict:
    email = email or _unique_email()
    response = client.post(
        "/api/v1/auth/register",
        json={"full_name": "Pulse Operator", "email": email, "password": password},
    )
    assert response.status_code == 201
    return {"email": email, "password": password, "user": response.json()}


def _login(client: TestClient, email: str, password: str) -> dict:
    response = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": password},
    )
    assert response.status_code == 200
    return response.json()


def test_user_registration(client: TestClient) -> None:
    payload = _register(client)
    assert payload["user"]["email"] == payload["email"]
    assert "password_hash" not in payload["user"]
    assert payload["user"]["is_active"] is True


def test_duplicate_registration_rejected(client: TestClient) -> None:
    email = _unique_email()
    _register(client, email=email)
    response = client.post(
        "/api/v1/auth/register",
        json={"full_name": "Dup User", "email": email, "password": "SecurePass1"},
    )
    assert response.status_code == 409


def test_password_hashing_roundtrip() -> None:
    raw = "AnotherPass9"
    hashed = hash_password(raw)
    assert hashed != raw
    assert verify_password(raw, hashed) is True
    assert verify_password("wrong", hashed) is False


def test_login_success(client: TestClient) -> None:
    creds = _register(client)
    token_payload = _login(client, creds["email"], creds["password"])
    assert token_payload["token_type"] == "bearer"
    assert token_payload["access_token"]
    assert token_payload["user"]["email"] == creds["email"]


def test_login_failure(client: TestClient) -> None:
    creds = _register(client)
    response = client.post(
        "/api/v1/auth/login",
        json={"email": creds["email"], "password": "WrongPass9"},
    )
    assert response.status_code == 401


def test_current_user_with_bearer(client: TestClient) -> None:
    creds = _register(client)
    token_payload = _login(client, creds["email"], creds["password"])
    response = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token_payload['access_token']}"},
    )
    assert response.status_code == 200
    assert response.json()["email"] == creds["email"]


def test_expired_token_rejected(client: TestClient) -> None:
    creds = _register(client)
    settings = get_settings()
    token = jwt.encode(
        {
            "sub": creds["user"]["id"],
            "exp": datetime.now(timezone.utc) - timedelta(minutes=1),
            "iat": datetime.now(timezone.utc) - timedelta(minutes=5),
            "type": "access",
        },
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
    )
    response = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 401


def test_invalid_token_rejected(client: TestClient) -> None:
    response = client.get("/api/v1/auth/me", headers={"Authorization": "Bearer not-a-jwt"})
    assert response.status_code == 401


def test_logout_clears_session_cookie(client: TestClient) -> None:
    creds = _register(client)
    login = client.post(
        "/api/v1/auth/login",
        json={"email": creds["email"], "password": creds["password"]},
    )
    assert login.status_code == 200
    assert client.cookies.get("pulsetrace_access_token")

    logout = client.post("/api/v1/auth/logout")
    assert logout.status_code == 204
    assert client.cookies.get("pulsetrace_access_token") is None

    set_cookie_headers = [
        value.decode() if isinstance(value, bytes) else value
        for key, value in logout.headers.multi_items()
        if key.lower() == "set-cookie"
    ]
    assert any("pulsetrace_access_token=" in header for header in set_cookie_headers)
    assert any("httponly" in header.lower() for header in set_cookie_headers)