"""Origin check for cookie-authenticated state-changing requests."""

from __future__ import annotations

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from app.core.config import get_settings

_UNSAFE_METHODS = frozenset({"POST", "PUT", "PATCH", "DELETE"})


class CsrfOriginMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        settings = get_settings()
        if settings.app_env == "test":
            return await call_next(request)

        if request.method not in _UNSAFE_METHODS:
            return await call_next(request)

        auth_header = request.headers.get("authorization", "")
        if auth_header.lower().startswith("bearer "):
            return await call_next(request)

        cookie_name = settings.auth_cookie_name
        if cookie_name not in request.cookies:
            return await call_next(request)

        origin = request.headers.get("origin") or request.headers.get("referer", "")
        if not origin:
            return JSONResponse(status_code=403, content={"detail": "Origin header required"})

        allowed = settings.backend_cors_origins
        if not any(origin.startswith(allowed_origin) for allowed_origin in allowed):
            return JSONResponse(status_code=403, content={"detail": "Cross-site request blocked"})

        return await call_next(request)