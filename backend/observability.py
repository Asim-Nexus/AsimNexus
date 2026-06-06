#!/usr/bin/env python3
"""
STATUS: REAL — FastAPI routes setup
ASIMNEXUS Observability Routes
==============================
Exposes telemetry, posture assessment scores, logs, and traces API endpoints.
"""

from typing import Dict, Any, Optional
from pydantic import BaseModel
from fastapi import APIRouter, Request, HTTPException, status
from fastapi.responses import JSONResponse
from core.observability import get_collector
from core.audit_bus import fetch_audit, audit_summary


class ExternalEvent(BaseModel):
    component: str
    action: str
    severity: str
    message: str
    latency_ms: Optional[float] = 0.0
    status: Optional[str] = "ok"


def setup_observability_routes(app):
    """Registers observability APIs into the FastAPI instance."""
    
    @app.get("/api/observability/telemetry")
    async def get_telemetry_endpoint(limit: Optional[int] = 100):
        collector = get_collector()
        return JSONResponse(collector.get_telemetry(limit))

    @app.get("/api/observability/posture")
    async def get_posture_endpoint():
        collector = get_collector()
        return JSONResponse(collector.get_posture())

    @app.get("/api/observability/metrics")
    async def get_metrics_endpoint():
        # Aggregated execution metrics summary
        collector = get_collector()
        telemetry = collector.get_telemetry(1000)
        
        total_requests = len([e for e in telemetry if e.get("action") == "request"])
        errors = len([e for e in telemetry if e.get("action") == "error" or e.get("status") == "failed"])
        avg_latency = 0.0
        
        request_latencies = [e.get("latency_ms", 0.0) for e in telemetry if e.get("action") == "request"]
        if request_latencies:
            avg_latency = sum(request_latencies) / len(request_latencies)

        return JSONResponse({
            "total_requests": total_requests,
            "error_rate": errors / max(1, total_requests),
            "average_latency_ms": round(avg_latency, 2),
            "total_events_buffered": len(telemetry)
        })

    @app.get("/api/observability/traces")
    async def get_traces_endpoint(trace_id: Optional[str] = None):
        collector = get_collector()
        events = collector.get_telemetry(1000)
        if trace_id:
            filtered = [e for e in events if e.get("trace_id") == trace_id]
        else:
            filtered = [e for e in events if e.get("trace_id") is not None]
        return JSONResponse(filtered)

    @app.get("/api/observability/audit")
    async def get_audit_endpoint(limit: Optional[int] = 50, cursor: Optional[str] = None):
        return JSONResponse(fetch_audit(limit, cursor))

    @app.post("/api/observability/event")
    async def post_event_endpoint(event: ExternalEvent):
        collector = get_collector()
        payload = {
            "component": event.component,
            "action": event.action,
            "severity": event.severity,
            "message": event.message,
            "latency_ms": event.latency_ms,
            "status": event.status
        }
        try:
            res = collector._append_event(payload)
            return JSONResponse({"status": "recorded", "event": res})
        except ValueError as ve:
            return JSONResponse({"status": "error", "detail": str(ve)}, status_code=422)

    @app.get("/api/observability/health")
    async def get_health_endpoint():
        return JSONResponse({"status": "healthy", "subsystem": "observability"})

    @app.get("/api/observability/status")
    async def get_status_endpoint():
        collector = get_collector()
        summary = audit_summary()
        return JSONResponse({
            "active_mode": collector.mode,
            "policy_score": collector.policy_score,
            "audit_bus": summary,
            "buffered_events_count": len(collector.events_buffer)
        })
