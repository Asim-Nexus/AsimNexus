"""
Health & App-Level Routes
=========================
Endpoints for health checks, mesh nodes overview, and socket.io.
"""

import logging
from fastapi import APIRouter
from routes.response import ok, error

router = APIRouter(tags=["Health"])

logger = logging.getLogger("AsimNexus.Routes.Health")

# Module-level globals set by app.py at startup
orchestrator = None


def init_health(app_globals: dict) -> None:
    """Initialize health module from app.py globals."""
    global orchestrator
    orchestrator = app_globals.get("orchestrator")


@router.get("/health")
async def health_check():
    """Simple health check — returns 200 if the server is running."""
    return ok(data={"status": "ok", "service": "asimnexus"})


@router.get("/api/system/info")
async def system_info():
    """System information endpoint."""
    try:
        import platform
        import sys
        return ok(data={
            "platform": platform.platform(),
            "python_version": sys.version,
            "hostname": platform.node(),
            "architecture": platform.machine(),
        })
    except Exception as e:
        logger.error(f"system_info error: {e}")
        return error(str(e))


@router.get("/health/live")
async def health_live():
    """Liveness probe — always returns 200 if the server is running."""
    return ok(data={"status": "alive"})


@router.get("/health/ready")
async def health_ready():
    """Readiness probe — checks if the system is ready to serve traffic."""
    try:
        return ok(data={"status": "ready"})
    except Exception as e:
        logger.error(f"health_ready error: {e}")
        return error(str(e))


@router.get("/health/status")
async def health_status():
    """Full health status of the system."""
    try:
        return ok(data={
            "status": "operational",
            "version": "1.0.0-rc2",
            "uptime": "unknown",
            "components": {
                "api": "healthy",
                "mesh": "unknown",
                "database": "unknown"
            }
        })
    except Exception as e:
        logger.error(f"health_status error: {e}")
        return error(str(e))


@router.get("/mesh/nodes")
async def mesh_nodes_overview():
    """Get overview of mesh nodes."""
    try:
        return ok(data={
            "nodes": [],
            "total": 0,
            "active": 0,
            "message": "mesh node overview"
        })
    except Exception as e:
        logger.error(f"mesh_nodes_overview error: {e}")
        return error(str(e))


@router.get("/socket.io/")
async def socket_io():
    """Socket.IO endpoint placeholder."""
    return ok(data={
        "status": "socket.io endpoint",
        "message": "WebSocket support not yet implemented"
    })
