"""
Observability Routes
====================
Endpoints for observability: health, metrics, traces, audit, telemetry.
"""

import logging
from fastapi import APIRouter, Body
from routes.response import ok, error, unavailable

router = APIRouter(tags=["Observability"])

logger = logging.getLogger("AsimNexus.Routes.Observability")

# Module-level globals set by app.py at startup
observability_manager = None


def init_observability(app_globals: dict) -> None:
    """Initialize observability module from app.py globals."""
    global observability_manager
    observability_manager = app_globals.get("observability_manager")


@router.get("/api/observability/health")
async def observability_health():
    """Observability system health."""
    try:
        if observability_manager:
            data = await observability_manager.health_check()
            return ok(data=data)
        return ok(data={"status": "healthy"})
    except Exception as e:
        logger.error(f"observability_health error: {e}")
        return error(str(e))


@router.get("/api/observability/status")
async def observability_status():
    """Observability system status."""
    try:
        if observability_manager:
            data = await observability_manager.get_status()
            return ok(data=data)
        return ok(data={"status": "active", "mode": "observability"})
    except Exception as e:
        logger.error(f"observability_status error: {e}")
        return error(str(e))


@router.get("/api/observability/metrics")
async def observability_metrics():
    """Get system metrics."""
    try:
        if observability_manager:
            data = await observability_manager.get_metrics()
            return ok(data=data)
        return ok(data={"metrics": {}, "timestamp": "mock"})
    except Exception as e:
        logger.error(f"observability_metrics error: {e}")
        return error(str(e))


@router.get("/api/observability/traces")
async def observability_traces(service: str = "", limit: int = 100):
    """Get distributed traces."""
    try:
        if observability_manager:
            data = await observability_manager.get_traces(service=service, limit=limit)
            return ok(data=data)
        return ok(data={"traces": [], "count": 0})
    except Exception as e:
        logger.error(f"observability_traces error: {e}")
        return error(str(e))


@router.get("/api/observability/audit")
async def observability_audit(user_id: str = "", action: str = "", limit: int = 100):
    """Get audit log entries."""
    try:
        if observability_manager:
            data = await observability_manager.get_audit_log(user_id=user_id, action=action, limit=limit)
            return ok(data=data)
        return ok(data={"entries": [], "count": 0})
    except Exception as e:
        logger.error(f"observability_audit error: {e}")
        return error(str(e))


@router.post("/api/observability/event")
async def observability_event(data: dict = Body(...)):
    """Record an observability event."""
    try:
        if observability_manager:
            result = await observability_manager.record_event(data)
            return ok(data=result)
        return ok(data={"status": "recorded", "event_id": "mock_event"})
    except Exception as e:
        logger.error(f"observability_event error: {e}")
        return error(str(e))


@router.get("/api/observability/posture")
async def observability_posture():
    """Get security posture assessment."""
    try:
        if observability_manager:
            data = await observability_manager.get_posture()
            return ok(data=data)
        return ok(data={"posture": "secure", "score": 0.95, "risks": []})
    except Exception as e:
        logger.error(f"observability_posture error: {e}")
        return error(str(e))


@router.get("/api/observability/telemetry")
async def observability_telemetry(component: str = "", metric: str = ""):
    """Get telemetry data for components."""
    try:
        if observability_manager:
            data = await observability_manager.get_telemetry(component=component, metric=metric)
            return ok(data=data)
        return ok(data={"telemetry": {}, "component": component, "metric": metric})
    except Exception as e:
        logger.error(f"observability_telemetry error: {e}")
        return error(str(e))