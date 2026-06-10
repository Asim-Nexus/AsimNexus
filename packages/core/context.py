#!/usr/bin/env python3
"""
STATUS: REAL — Production-grade request context tracking
ASIMNEXUS Request Context Subsystem
===================================
Tracks correlation metadata (request_id, trace_id, user_id, session_id)
across asynchronous task execution boundaries using contextvars.
"""

import uuid
from contextvars import ContextVar
from typing import Dict, Any, Optional

# Context variable containing request metadata dict
_request_context: ContextVar[Dict[str, Any]] = ContextVar("request_context", default={})


def new_request_context(request_id: Optional[str] = None) -> Dict[str, Any]:
    """Initialize a brand new request context with correlation IDs."""
    req_id = request_id or str(uuid.uuid4())
    trace_id = str(uuid.uuid4())
    initial_ctx = {
        "request_id": req_id,
        "trace_id": trace_id,
        "span_id": str(uuid.uuid4()),
        "user_id": None,
        "device_id": None,
        "session_id": None,
        "mode": "personal",
        "privacy_level": "public"
    }
    _request_context.set(initial_ctx)
    return initial_ctx


def bind_request_context(**fields) -> None:
    """Bind key-value pairs into the current active context."""
    ctx = _request_context.get()
    # Create copy to prevent mutating shared references across coroutines
    new_ctx = ctx.copy()
    new_ctx.update(fields)
    _request_context.set(new_ctx)


def get_request_context() -> Dict[str, Any]:
    """Retrieve the current active request context."""
    return _request_context.get()


def clear_request_context() -> None:
    """Clear and reset request context to default state."""
    _request_context.set({})
