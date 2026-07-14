"""
Unified API Response Model
==========================
Standard response format for all AsimNexus API endpoints.

Usage:
    from routes.response import ApiResponse, ok, error

    @router.get("/api/example")
    async def example():
        return ok(data={"key": "value"})
        # → {"status": "ok", "data": {"key": "value"}, "timestamp": "..."}

    @router.get("/api/example")
    async def example_fail():
        return error("Something went wrong", status_code=400)
        # → {"status": "error", "detail": "Something went wrong", "code": 400, "timestamp": "..."}
"""

import time
from typing import Any, Dict, List, Optional, Union
from datetime import datetime, timezone


def _timestamp() -> str:
    return datetime.now(timezone.utc).isoformat()


def ok(
    data: Any = None,
    note: Optional[str] = None,
    meta: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Build a standard success response.

    Args:
        data: The primary payload (dict, list, str, etc.)
        note: Optional human-readable note (e.g. "service unavailable")
        meta: Optional metadata dict (pagination, counts, etc.)

    Returns:
        Dict with keys: status, data, timestamp [, note, meta]
    """
    result: Dict[str, Any] = {
        "status": "ok",
        "timestamp": _timestamp(),
    }
    if data is not None:
        result["data"] = data
    if note is not None:
        result["note"] = note
    if meta is not None:
        result["meta"] = meta
    return result


def error(
    detail: str,
    status_code: int = 500,
    data: Any = None,
) -> Dict[str, Any]:
    """
    Build a standard error response.

    Args:
        detail: Human-readable error description
        status_code: HTTP status code (default 500)
        data: Optional additional error data

    Returns:
        Dict with keys: status, detail, code, timestamp [, data]
    """
    result: Dict[str, Any] = {
        "status": "error",
        "detail": detail,
        "code": status_code,
        "timestamp": _timestamp(),
    }
    if data is not None:
        result["data"] = data
    return result


def paginated(
    items: List[Any],
    total: int,
    page: int,
    limit: int,
    note: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Build a paginated success response.

    Args:
        items: List of items for the current page
        total: Total number of items across all pages
        page: Current page number (1-based)
        limit: Items per page

    Returns:
        Dict with status, data (items), meta (pagination info)
    """
    total_pages = max(1, (total + limit - 1) // limit) if limit > 0 else 1
    return ok(
        data=items,
        note=note,
        meta={
            "page": page,
            "limit": limit,
            "total": total,
            "total_pages": total_pages,
            "has_next": page < total_pages,
            "has_prev": page > 1,
        },
    )


def created(data: Any = None, note: Optional[str] = None) -> Dict[str, Any]:
    """Build a 'created' success response (HTTP 201)."""
    return ok(data=data, note=note)


def deleted(note: Optional[str] = None) -> Dict[str, Any]:
    """Build a 'deleted' success response."""
    return ok(note=note or "Resource deleted")


def unavailable(service: str) -> Dict[str, Any]:
    """Build a response indicating a backend service is unavailable."""
    return ok(note=f"{service} unavailable")
