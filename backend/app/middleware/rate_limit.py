"""Simple in-process rate limiting (single-instance; not distributed)."""

from __future__ import annotations

import time
from collections import defaultdict, deque
from threading import Lock

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from app.core.config import get_settings

_lock = Lock()
_hits: dict[str, deque[float]] = defaultdict(deque)

_EXPENSIVE_SUFFIXES = (
    "/analysis/run",
    "/incidents/correlate",
    "/investigate",
)

_AUTH_PATHS = ("/api/v1/auth/login", "/api/v1/auth/register")


class RateLimitMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        settings = get_settings()
        if settings.app_env == "test":
            return await call_next(request)

        limit, window = _limits_for_path(request.url.path, settings)
        if limit <= 0:
            return await call_next(request)

        client = request.client.host if request.client else "unknown"
        key = f"{client}:{request.url.path}"
        now = time.monotonic()

        with _lock:
            bucket = _hits[key]
            while bucket and now - bucket[0] > window:
                bucket.popleft()
            if len(bucket) >= limit:
                return JSONResponse(
                    status_code=429,
                    content={"detail": "Too many requests. Try again shortly."},
                )
            bucket.append(now)

        return await call_next(request)


def _limits_for_path(path: str, settings) -> tuple[int, float]:
    if any(path.endswith(suffix) for suffix in _EXPENSIVE_SUFFIXES):
        return settings.rate_limit_expensive_per_minute, 60.0
    if any(path.startswith(prefix) for prefix in _AUTH_PATHS):
        return settings.rate_limit_auth_per_minute, 60.0
    return 0, 60.0