import os
import time
import logging
from collections import defaultdict
from typing import Dict, List, Tuple, Optional

from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger("AsimNexus.RateLimiter")

DEFAULT_LIMIT = int(os.getenv("ASIM_RATE_LIMIT_DEFAULT", "100"))
DEFAULT_WINDOW = int(os.getenv("ASIM_RATE_LIMIT_WINDOW", "60"))

ROUTE_LIMITS: List[Tuple[str, int, int]] = [
    ("/auth/register", 5, 60),
    ("/auth/login", 10, 60),
    ("/api/identity/create", 10, 60),
    ("/api/did/create", 20, 60),
    ("/api/credits/transfer", 10, 60),
    ("/chat", 30, 60),
    ("/api/chat", 30, 60),
    ("/llm/chat", 30, 60),
    ("/health", 120, 60),
    ("/api/status", 120, 60),
    ("/healthz", 120, 60),
    ("/status", 120, 60),
]


def _get_route_limit(path: str) -> Tuple[int, int]:
    for prefix, limit, window in ROUTE_LIMITS:
        if path.startswith(prefix):
            return limit, window
    return DEFAULT_LIMIT, DEFAULT_WINDOW


class RateLimiterMiddleware(BaseHTTPMiddleware):
    def __init__(self, app):
        super().__init__(app)
        self._windows: Dict[str, List[float]] = defaultdict(list)
        self._cleanup_interval = 300
        self._last_cleanup = time.monotonic()

    async def dispatch(self, request: Request, call_next):
        client_ip = request.client.host if request.client else "unknown"
        path = request.url.path

        limit, window = _get_route_limit(path)
        now = time.monotonic()

        key = f"{client_ip}:{path}"
        self._cleanup(now)

        window_start = now - window
        timestamps = self._windows.get(key, [])
        timestamps[:] = [t for t in timestamps if t > window_start]

        if len(timestamps) >= limit:
            retry_after = int(timestamps[0] + window - now) if timestamps else window
            logger.warning(
                f"Rate limit exceeded: {client_ip} -> {path} "
                f"({len(timestamps)}/{limit} in {window}s)"
            )
            return JSONResponse(
                status_code=429,
                content={
                    "detail": "Rate limit exceeded",
                    "retry_after_seconds": max(1, retry_after),
                    "limit": limit,
                    "window_seconds": window,
                },
                headers={"Retry-After": str(max(1, retry_after))},
            )

        timestamps.append(now)
        return await call_next(request)

    def _cleanup(self, now: float):
        if now - self._last_cleanup < self._cleanup_interval:
            return
        self._last_cleanup = now
        cutoff = now - max(w for _, _, w in ROUTE_LIMITS + [("", DEFAULT_LIMIT, DEFAULT_WINDOW)])
        self._windows = {
            k: [t for t in v if t > cutoff]
            for k, v in self._windows.items()
        }
