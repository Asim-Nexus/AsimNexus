#!/usr/bin/env python3
"""
STATUS: REAL — FastAPI HTTP middleware
ASIMNEXUS Observability Middleware
==================================
Hooks into every incoming request to track latency, correlate request contexts,
and record request execution telemetry metrics.

Integrates with AsimNexus Gateway for request-level authorization.
"""

import time
import uuid
import logging
from starlette.middleware.base import BaseHTTPMiddleware
from fastapi import Request
from core.context import new_request_context, bind_request_context, clear_request_context
from core.observability import get_collector
from core.audit_bus import emit_audit

logger = logging.getLogger(__name__)

# ── AsimNexus Gateway integration ─────────────────────────────────
try:
    from gateway_middleware import AsimNexusGatewayMiddleware
    HAS_GATEWAY = True
except ImportError:
    HAS_GATEWAY = False
    AsimNexusGatewayMiddleware = None
    logger.info("AsimNexus Gateway middleware not available")


class ObservabilityMiddleware(BaseHTTPMiddleware):
    """Intercepts requests to populate ContextVar, track latencies, and append to telemetry."""

    async def dispatch(self, request: Request, call_next):
        # Read header or generate request correlation IDs
        req_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
        trace_id = request.headers.get("X-Trace-ID") or str(uuid.uuid4())
        
        # Initialize thread-local context variables
        ctx = new_request_context(req_id)
        bind_request_context(
            trace_id=trace_id,
            user_id=request.headers.get("X-User-ID") or "anonymous",
            device_id=request.headers.get("X-Device-ID") or "unknown",
            session_id=request.headers.get("X-Session-ID") or "ephemeral"
        )
        
        # Track start time
        start_time = time.time()
        
        try:
            response = await call_next(request)
            duration_ms = (time.time() - start_time) * 1000
            
            # Record telemetry metric log
            collector = get_collector()
            ref_event = collector.record_request(
                request_id=req_id,
                path=request.url.path,
                method=request.method,
                status_code=response.status_code,
                latency_ms=duration_ms,
                context=ctx
            )
            
            # Emit safety audit bus trace
            emit_audit(ref_event)
            
            # Append headers to output
            response.headers["X-Request-ID"] = req_id
            response.headers["X-Trace-ID"] = trace_id
            
            return response
            
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            collector = get_collector()
            
            # Record error event
            err_event = collector.record_error(
                error_type=e.__class__.__name__,
                message=str(e),
                context=ctx
            )
            emit_audit(err_event)
            raise e
            
        finally:
            # Clean up task context thread state to prevent memory leaks
            clear_request_context()
